from __future__ import annotations

import json
import re
from typing import Any

from .models import Episode, PromoCandidate, parse_timestamp


PROMPT_TEMPLATE = """You are a senior short-form drama promo editor. Analyze ONE episode screenplay and recommend up to {limit} promotional clips.

A usable promo is 20 to 60 seconds long. It should:
1) hook a scrolling viewer within its FIRST 3 SECONDS;
2) stop at an unresolved or curiosity-building moment (not after the conflict has been fully resolved);
3) make enough sense to a person who has never watched the series;
4) use only events and timestamps actually present in the supplied screenplay.

Important constraints:
- Recommend continuous segments from THIS episode only. The system combines results from all episodes into one ranked list. Multi-episode montages are outside this first version's scope.
- Use MM:SS.ss timestamp format. Start and end must be between 20 and 60 seconds apart and inside this episode's duration.
- Do not invent dialogue, actions, character relationships, timestamps, or plot facts.
- Do not confuse a camera direction with a story event. Camera descriptions may help explain visual context, but prioritize dialogue and action.
- A dramatic scene is not automatically a good promo. Explain why it works as an advertisement for a new viewer.
- Be honest: give low scores when the episode has no strong promo moment. Do not force a high score.
- Evidence fields must contain short exact phrases copied from screenplay dialogue/action. If there is no evidence for a hook or cliffhanger, use an empty string and explain the uncertainty.
- Scores must be integers from 1 (weak) to 5 (excellent).

Episode number: {episode_id}
Episode duration: {duration}
Episode logline: {logline}
Continuity notes: {continuity}
{neighbor_context}

SCENE LIST:
{scenes}

SCREENPLAY EVENTS (chronological; each has exact time range and type):
{events}

Return ONLY valid JSON in this exact shape:
{{
  "candidates": [
    {{
      "start_time": "00:20.00",
      "end_time": "00:48.00",
      "hook": "Plain-language description of what grabs attention immediately.",
      "cliffhanger": "Plain-language description of the unresolved ending.",
      "why_it_works": "One or two sentences explaining standalone ad value.",
      "hook_evidence": "Exact short excerpt from an action/dialogue event.",
      "cliffhanger_evidence": "Exact short excerpt from an action/dialogue event.",
      "scores": {{
        "hook": 1,
        "cliffhanger": 1,
        "standalone_clarity": 1,
        "emotional_intensity": 1
      }}
    }}
  ]
}}
"""


def _format_events(episode: Episode) -> str:
    lines = []
    for event in episode.events:
        # Keep timed camera/action/dialogue/sound blocks, but cap individual text for prompt size.
        lines.append(
            f"[{event.start_seconds:06.2f}-{event.end_seconds:06.2f}] "
            f"[{event.kind.upper()} | {event.label}] {event.text[:650]}"
        )
    return "\n".join(lines)


def build_prompt(episode: Episode, limit: int = 3, neighbor_context: str = "") -> str:
    return PROMPT_TEMPLATE.format(
        limit=limit,
        episode_id=episode.episode_id,
        duration=f"{episode.duration_seconds:.2f} seconds",
        logline=episode.logline or "Not supplied",
        continuity=episode.continuity_notes or "Not supplied",
        neighbor_context=neighbor_context or "Series context: no additional adjacent-episode summary supplied.",
        scenes="\n".join(
            f"Scene {scene.number} [{scene.start_seconds:06.2f}-{scene.end_seconds:06.2f}]: {scene.heading}"
            for scene in episode.scenes
        ) or "No scene headings supplied.",
        events=_format_events(episode),
    )


def _strip_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def parse_model_response(text: str, episode: Episode) -> list[PromoCandidate]:
    try:
        payload: dict[str, Any] = json.loads(_strip_json(text))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model response was not valid JSON: {exc}") from exc
    items = payload.get("candidates", [])
    if not isinstance(items, list):
        raise ValueError("Model JSON field 'candidates' must be a list")

    results: list[PromoCandidate] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        try:
            start = parse_timestamp(item["start_time"])
            end = parse_timestamp(item["end_time"])
            scores_raw = item["scores"]
            scores = {
                key: int(scores_raw[key])
                for key in ("hook", "cliffhanger", "standalone_clarity", "emotional_intensity")
            }
        except (KeyError, TypeError, ValueError) as exc:
            continue
        warnings: list[str] = []
        fatal_warnings: list[str] = []
        if start < 0 or end <= start:
            fatal_warnings.append("Invalid time order or negative timestamp.")
        boundaries = [value for event in episode.events for value in (event.start_seconds, event.end_seconds)]
        boundaries.extend(value for scene in episode.scenes for value in (scene.start_seconds, scene.end_seconds))
        if boundaries and min(abs(start - value) for value in boundaries) > 0.10:
            warnings.append("Start timestamp does not align closely with a screenplay event/scene boundary.")
        if boundaries and min(abs(end - value) for value in boundaries) > 0.10:
            warnings.append("End timestamp does not align closely with a screenplay event/scene boundary.")
        if end - start < 20 or end - start > 60:
            fatal_warnings.append("Clip duration is outside the required 20-60 second range.")
        if end > episode.duration_seconds + 0.05 or start > episode.duration_seconds:
            fatal_warnings.append("Candidate timestamp exceeds the episode duration.")
        if any(score < 1 or score > 5 for score in scores.values()):
            fatal_warnings.append("One or more scores are outside the 1-5 scale.")
        if set(scores) != {"hook", "cliffhanger", "standalone_clarity", "emotional_intensity"}:
            fatal_warnings.append("Score dimensions are incomplete.")
        if fatal_warnings:
            continue

        hook = str(item.get("hook", "")).strip()
        cliffhanger = str(item.get("cliffhanger", "")).strip()
        why = str(item.get("why_it_works", "")).strip()
        hook_evidence = str(item.get("hook_evidence", "")).strip()
        cliff_evidence = str(item.get("cliffhanger_evidence", "")).strip()
        if not hook or not cliffhanger or not why:
            continue
        source_text = " ".join(event.text.lower() for event in episode.events if event.kind in {"action", "dialogue"})
        if hook_evidence and hook_evidence.lower() not in source_text:
            warnings.append("Hook evidence was not found as an exact substring; verify it manually.")
        if cliff_evidence and cliff_evidence.lower() not in source_text:
            warnings.append("Cliffhanger evidence was not found as an exact substring; verify it manually.")
        if hook_evidence:
            hook_event = next(
                (event for event in episode.events
                 if event.kind in {"action", "dialogue"}
                 and hook_evidence.lower() in event.text.lower()),
                None,
            )
            if hook_event and not (hook_event.start_seconds < start + 3 and hook_event.end_seconds > start):
                warnings.append("Hook evidence does not occur within the first 3 seconds of the suggested clip.")
        else:
            warnings.append("No hook evidence was supplied.")
        if cliff_evidence:
            cliff_event = next(
                (event for event in episode.events
                 if event.kind in {"action", "dialogue"}
                 and cliff_evidence.lower() in event.text.lower()),
                None,
            )
            if cliff_event and not (cliff_event.end_seconds > end - 8 and cliff_event.start_seconds < end):
                warnings.append("Cliffhanger evidence does not occur near the end of the suggested clip.")
        else:
            warnings.append("No cliffhanger evidence was supplied.")
        results.append(
            PromoCandidate(
                episode_id=episode.episode_id,
                start_seconds=round(start, 2),
                end_seconds=round(end, 2),
                hook=hook,
                cliffhanger=cliffhanger,
                why_it_works=why,
                scores=scores,
                method="groq_llm",
                hook_evidence=hook_evidence,
                cliffhanger_evidence=cliff_evidence,
                validation_warnings=warnings,
                human_review_required=True,
            )
        )
    return results

