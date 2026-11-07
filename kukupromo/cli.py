from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from .groq import GroqPromoModel
from .heuristics import generate_heuristic_candidates
from .models import Episode, PromoCandidate
from .output import write_json, write_outputs
from .parser import read_input


def load_dotenv(path: Path = Path(".env")) -> None:
    """Minimal .env loader; does not overwrite variables already in the shell."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _neighbors(episodes: list[Episode], index: int) -> str:
    parts = []
    if index > 0:
        prev = episodes[index - 1]
        parts.append(f"Previous episode {prev.episode_id} logline: {prev.logline}")
    if index + 1 < len(episodes):
        nxt = episodes[index + 1]
        parts.append(f"Next episode {nxt.episode_id} logline: {nxt.logline}")
    return "Adjacent episode summaries for context only (do not use their timestamps in this episode):\n" + "\n".join(parts) if parts else ""


def _candidate_from_dict(row: dict[str, Any]) -> PromoCandidate:
    return PromoCandidate(
        episode_id=int(row["episode_id"]),
        start_seconds=float(row["start_seconds"]),
        end_seconds=float(row["end_seconds"]),
        hook=str(row["hook"]),
        cliffhanger=str(row["cliffhanger"]),
        why_it_works=str(row["why_it_works"]),
        scores={key: int(value) for key, value in row["scores"].items()},
        method=str(row["method"]),
        hook_evidence=str(row.get("hook_evidence", "")),
        cliffhanger_evidence=str(row.get("cliffhanger_evidence", "")),
        validation_warnings=list(row.get("validation_warnings", [])),
        human_review_required=bool(row.get("human_review_required", True)),
    )


def _checkpoint_path(out_dir: Path, episode_id: int) -> Path:
    return out_dir / "checkpoints" / f"episode_{episode_id:03d}.json"


def _load_checkpoint(path: Path) -> tuple[list[PromoCandidate], dict[str, Any]] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        status = payload.get("status", {})
        if status.get("status") != "processed":
            return None
        candidates = [_candidate_from_dict(item) for item in payload.get("candidates", [])]
        return candidates, status
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def _save_checkpoint(path: Path, candidates: list[PromoCandidate], status: dict[str, Any]) -> None:
    write_json(path, {
        "status": status,
        "candidates": [
            {
                "episode_id": item.episode_id,
                "start_seconds": item.start_seconds,
                "end_seconds": item.end_seconds,
                "hook": item.hook,
                "cliffhanger": item.cliffhanger,
                "why_it_works": item.why_it_works,
                "scores": item.scores,
                "method": item.method,
                "hook_evidence": item.hook_evidence,
                "cliffhanger_evidence": item.cliffhanger_evidence,
                "validation_warnings": item.validation_warnings,
                "human_review_required": item.human_review_required,
            }
            for item in candidates
        ],
    })


def _deduplicate(candidates: list[PromoCandidate], limit_per_episode: int) -> list[PromoCandidate]:
    selected: list[PromoCandidate] = []
    by_episode: dict[int, list[PromoCandidate]] = {}
    for candidate in sorted(candidates, key=lambda item: item.final_score, reverse=True):
        group = by_episode.setdefault(candidate.episode_id, [])
        overlap_duplicate = False
        for chosen in group:
            overlap = max(0.0, min(candidate.end_seconds, chosen.end_seconds) - max(candidate.start_seconds, chosen.start_seconds))
            shorter = min(candidate.duration_seconds, chosen.duration_seconds)
            if shorter > 0 and overlap / shorter >= 0.82:
                overlap_duplicate = True
                break
        if overlap_duplicate or len(group) >= limit_per_episode:
            continue
        group.append(candidate)
        selected.append(candidate)
    return selected


def run(args: argparse.Namespace) -> int:
    load_dotenv(Path(args.env_file))
    try:
        episodes = read_input(args.input)
    except Exception as exc:
        print(f"ERROR: Could not read input: {exc}", file=sys.stderr)
        return 2

    if args.limit is not None:
        episodes = episodes[: max(0, args.limit)]
    if not episodes:
        print("ERROR: No episodes selected.", file=sys.stderr)
        return 2

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    ai_model = None
    if args.mode in {"ai", "auto"}:
        has_key = bool(os.getenv("GROQ_API_KEY"))
        if args.mode == "ai" or has_key:
            try:
                ai_model = GroqPromoModel(model_name=args.model or None)
            except Exception as exc:
                if args.mode == "ai":
                    print(f"ERROR: {exc}", file=sys.stderr)
                    return 2
                print(f"WARNING: AI unavailable ({exc}); using offline heuristic mode.")
        elif args.mode == "auto":
            print("INFO: GROQ_API_KEY not found; using offline heuristic mode.")

    all_candidates: list[PromoCandidate] = []
    statuses: dict[int, dict[str, Any]] = {}
    for index, episode in enumerate(episodes):
        checkpoint = _checkpoint_path(out_dir, episode.episode_id)
        if args.resume:
            cached = _load_checkpoint(checkpoint)
            if cached:
                cached_candidates, status = cached
                all_candidates.extend(cached_candidates)
                statuses[episode.episode_id] = status | {"note": "Loaded from checkpoint"}
                print(f"[{index + 1}/{len(episodes)}] Episode {episode.episode_id}: resumed ({len(cached_candidates)} candidates)")
                continue

        print(f"[{index + 1}/{len(episodes)}] Processing Episode {episode.episode_id}...", flush=True)
        candidates: list[PromoCandidate] = []
        method = "heuristic_offline"
        note = ""
        if ai_model is not None:
            try:
                raw_text, candidates = ai_model.analyze_episode(
                    episode,
                    limit=args.top_per_episode,
                    neighbor_context=_neighbors(episodes, index),
                )
                method = "groq_llm"
                raw_dir = out_dir / "raw_responses"
                raw_dir.mkdir(parents=True, exist_ok=True)
                (raw_dir / f"episode_{episode.episode_id:03d}.txt").write_text(raw_text, encoding="utf-8")
                parse_error = getattr(ai_model, "last_parse_error", None)
                if parse_error:
                    note = parse_error
                    (out_dir / "errors").mkdir(exist_ok=True)
                    (out_dir / "errors" / f"episode_{episode.episode_id:03d}.txt").write_text(note, encoding="utf-8")
                    if args.mode == "auto":
                        print(f"  WARNING: {note}; using heuristic fallback for this episode.")
                        candidates = generate_heuristic_candidates(episode, limit=args.top_per_episode)
                        method = "heuristic_offline"
                    else:
                        method = "groq_error"
                elif not candidates:
                    note = "Groq returned no valid candidates after validation."
            except Exception as exc:
                note = f"Groq error: {exc}"
                (out_dir / "errors").mkdir(exist_ok=True)
                (out_dir / "errors" / f"episode_{episode.episode_id:03d}.txt").write_text(note, encoding="utf-8")
                if args.mode == "ai":
                    method = "groq_error"
                    print(f"  WARNING: {note}; no heuristic fallback in --mode ai.")
                else:
                    print(f"  WARNING: {note}; using heuristic fallback for this episode.")
                    candidates = generate_heuristic_candidates(episode, limit=args.top_per_episode)
                    method = "heuristic_offline"
        else:
            candidates = generate_heuristic_candidates(episode, limit=args.top_per_episode)

        status = {
            "status": "error" if method == "groq_error" else "processed",
            "method": method,
            "candidate_count": len(candidates),
            "note": note,
        }
        statuses[episode.episode_id] = status
        _save_checkpoint(checkpoint, candidates, status)
        if method == "heuristic_offline":
            heuristic_dir = out_dir / "heuristic_outputs"
            heuristic_dir.mkdir(parents=True, exist_ok=True)
            write_json(heuristic_dir / f"episode_{episode.episode_id:03d}.json", {
                "notice": "This is a program-generated heuristic baseline, not a raw LLM response.",
                "candidates": [
                    {
                        "start_time": item.start_seconds,
                        "end_time": item.end_seconds,
                        "hook": item.hook,
                        "cliffhanger": item.cliffhanger,
                        "why_it_works": item.why_it_works,
                        "scores": item.scores,
                    }
                    for item in candidates
                ],
            })
        all_candidates.extend(candidates)
        if ai_model is not None and index < len(episodes) - 1:
            time.sleep(max(0.0, args.delay))

    final_candidates = _deduplicate(all_candidates, limit_per_episode=args.top_per_episode)
    report = write_outputs(
        out_dir,
        episodes,
        final_candidates,
        mode_requested=args.mode,
        model_name=ai_model.model_name if ai_model else None,
        per_episode_status=statuses,
        input_name=Path(args.input).name,
    )

    print("\nCompleted.")
    print(f"Episodes processed: {report['episodes_processed']}/{len(episodes)}")
    print(f"Promotional candidates: {report['candidate_count']}")
    print(f"Top results: {out_dir / 'promos.csv'}")
    print(f"Full JSON: {out_dir / 'promos.json'}")
    print(f"Run report: {out_dir / 'run_report.md'}")
    if report["heuristic_candidate_count"]:
        print("NOTE: Heuristic candidates are only an offline baseline; they are not LLM judgments.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kuku-promo-finder",
        description="Find and rank 20-60 second promo candidates in timestamped screenplays using Groq or local heuristics.",
    )
    parser.add_argument("--input", required=True, help="Path to Kuku screenplay .zip file or folder of .txt scripts")
    parser.add_argument("--out", default="outputs/latest", help="Output folder (default: outputs/latest)")
    parser.add_argument("--mode", choices=["auto", "ai", "heuristic"], default="auto", help="auto uses Groq if configured; otherwise offline heuristics")
    parser.add_argument("--model", default=None, help="Groq model ID; defaults to GROQ_MODEL or qwen/qwen3.8-27b")
    parser.add_argument("--top-per-episode", type=int, default=3, help="Maximum candidates retained per episode (default: 3)")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N episodes (useful for a quick test)")
    parser.add_argument("--delay", type=float, default=3.2, help="Seconds between Groq requests (default: 3.2; keeps below free-tier request/minute limits)")
    parser.add_argument("--resume", action="store_true", help="Reuse episode checkpoints already present in the output folder")
    parser.add_argument("--env-file", default=".env", help="Path to .env file (default: .env)")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.top_per_episode < 1:
        print("ERROR: --top-per-episode must be at least 1", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
