from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import Episode, PromoCandidate, format_timestamp


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_outputs(
    out_dir: Path,
    episodes: list[Episode],
    candidates: list[PromoCandidate],
    *,
    mode_requested: str,
    model_name: str | None,
    per_episode_status: dict[int, dict[str, Any]],
    input_name: str,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates = sorted(candidates, key=lambda item: item.final_score, reverse=True)

    promo_rows = []
    for rank, candidate in enumerate(candidates, start=1):
        promo_rows.append(candidate.to_dict(rank=rank, promo_id=f"EP{candidate.episode_id:03d}-P{rank:03d}"))

    methods = sorted({candidate.method for candidate in candidates})
    ai_count = sum(1 for candidate in candidates if candidate.method == "groq_llm")
    ai_episode_count = sum(
        1 for status in per_episode_status.values()
        if str(status.get("method", "")).startswith("groq")
    )
    ai_used = ai_episode_count > 0
    heuristic_count = sum(1 for candidate in candidates if candidate.method == "heuristic_offline")
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    report = {
        "project": "Kuku AI Promo Finder",
        "generated_at_utc": generated_at,
        "input_name": input_name,
        "mode_requested": mode_requested,
        "llm_provider": "Groq" if ai_used else None,
        "llm_model": model_name if ai_used else None,
        "episodes_found": len(episodes),
        "episodes_processed": sum(1 for status in per_episode_status.values() if status.get("status") == "processed"),
        "episodes_with_errors": sum(1 for status in per_episode_status.values() if status.get("status") == "error"),
        "candidate_count": len(candidates),
        "llm_candidate_count": ai_count,
        "llm_episode_count": ai_episode_count,
        "heuristic_candidate_count": heuristic_count,
        "methods_present": methods,
        "score_weights": {
            "hook": 30,
            "cliffhanger": 30,
            "standalone_clarity": 25,
            "emotional_intensity": 15,
        },
        "important_limitations": [
            "The screenplay is text, not the finished video. Visual performance, acting, edit rhythm, music, and actual shot quality cannot be verified from the script alone.",
            "The first version recommends one continuous segment per promo. It does not compose multi-segment or cross-episode montages.",
            "The weighted score is a transparent prioritization aid, not a measured prediction of social-media conversion.",
            "Every recommendation requires human editorial review before publication.",
            "Heuristic mode is an offline baseline and must not be presented as an LLM result.",
        ],
        "episode_status": {str(key): value for key, value in sorted(per_episode_status.items())},
    }
    write_json(out_dir / "promos.json", {"run": report, "promos": promo_rows})
    write_json(out_dir / "run_report.json", report)

    csv_path = out_dir / "promos.csv"
    fields = [
        "rank", "promo_id", "episode_id", "start", "end", "duration_seconds",
        "hook", "cliffhanger", "why_it_works", "hook_score", "cliffhanger_score",
        "standalone_clarity_score", "emotional_intensity_score", "final_score",
        "method", "human_review_required", "validation_warnings",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in promo_rows:
            scores = row["scores"]
            segment = row["segments"][0]
            writer.writerow({
                "rank": row["rank"],
                "promo_id": row["promo_id"],
                "episode_id": row["episode_id"],
                "start": segment["start"],
                "end": segment["end"],
                "duration_seconds": row["total_duration_seconds"],
                "hook": row["hook"],
                "cliffhanger": row["cliffhanger"],
                "why_it_works": row["why_it_works"],
                "hook_score": scores["hook"],
                "cliffhanger_score": scores["cliffhanger"],
                "standalone_clarity_score": scores["standalone_clarity"],
                "emotional_intensity_score": scores["emotional_intensity"],
                "final_score": row["final_score"],
                "method": row["method"],
                "human_review_required": row["human_review_required"],
                "validation_warnings": " | ".join(row["validation_warnings"]),
            })

    review_path = out_dir / "quality_review_template.csv"
    with review_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "rank", "promo_id", "episode_id", "start", "end", "final_score",
            "human_approved (yes/no)", "failure_reason", "reviewer_notes",
        ])
        for row in promo_rows[:30]:
            seg = row["segments"][0]
            writer.writerow([
                row["rank"], row["promo_id"], row["episode_id"], seg["start"], seg["end"],
                row["final_score"], "", "", "",
            ])

    report_lines = [
        "# Kuku AI Promo Finder - Run Report",
        "",
        f"- Input: `{input_name}`",
        f"- Generated (UTC): {generated_at}",
        f"- Episodes found: {len(episodes)}",
        f"- Episodes processed: {report['episodes_processed']}",
        f"- Episodes with errors: {report['episodes_with_errors']}",
        f"- Promos produced: {len(candidates)}",
        f"- Methods: {', '.join(methods) if methods else 'none'}",
        f"- AI provider: {'Groq' if ai_used else 'not used'}",
        f"- AI model: {model_name if ai_used else 'not used'}",
        "",
        "## How to read this output",
        "The ranked list is a shortlist for an editor. The 100-point score is calculated from four 1-5 ratings using the weights in `run_report.json`.",
        "Every candidate includes the original episode timestamp range and must be checked against the actual episode video.",
        "",
        "## Quality and limitations",
    ]
    report_lines.extend(f"- {item}" for item in report["important_limitations"])
    report_lines.extend(["", "## Per-episode processing", "", "| Episode | Status | Method | Candidates | Note |", "|---:|---|---|---:|---|"])
    for episode_id, status in sorted(per_episode_status.items()):
        report_lines.append(
            f"| {episode_id} | {status.get('status', '')} | {status.get('method', '')} | "
            f"{status.get('candidate_count', 0)} | {str(status.get('note', '')).replace('|', '/')} |"
        )
    report_lines.append("")
    (out_dir / "run_report.md").write_text("\n".join(report_lines), encoding="utf-8")
    return report
