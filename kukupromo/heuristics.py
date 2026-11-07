from __future__ import annotations

import re
from collections import Counter

from .models import Episode, Event, PromoCandidate

HOOK_TERMS = {
    "betray", "secret", "marry", "marriage", "murder", "kill", "dead", "death",
    "pregnant", "stole", "stolen", "arrest", "arrested", "threat", "threaten",
    "truth", "lie", "lying", "never", "impossible", "why", "what", "who",
    "how", "stop", "help", "no", "wait", "run", "leave", "choice", "father",
    "husband", "wife", "duke", "queen", "king", "prince", "secretly", "revenge",
    "betrayed", "abandon", "abandoned", "refuse", "refused", "confess", "confession",
}
CLIFF_TERMS = {
    "who", "what", "where", "why", "how", "wait", "unless", "secret",
    "truth", "not yet", "you don't know", "you do not know", "what if", "what happened",
    "who is", "who was", "tell me", "knock", "knocking", "door", "arrive", "arrives",
    "arrival", "suddenly", "shocked", "gasp", "gasps", "stares", "reveals", "reveal",
    "interrupt", "interrupted", "threat", "threatens", "kill", "dead", "arrest",
    "evidence", "proof", "one thing", "come back", "not over",
}
EMOTION_TERMS = {
    "furious", "angry", "screaming", "shouting", "weeping", "sobbing", "tearful",
    "heartbroken", "devastated", "shocked", "horrified", "terrified", "desperate",
    "betrayed", "venomous", "menacing", "threatening", "gloating", "smug",
    "outraged", "panic", "panicked", "fear", "crying", "pleading", "revenge",
    "murder", "kill", "threat", "confront", "accuse", "accusing", "secret",
}
WORD_RE = re.compile(r"[a-zA-Z']+")


def _words(text: str) -> list[str]:
    return [word.lower() for word in WORD_RE.findall(text)]


def _term_hits(text: str, terms: set[str]) -> int:
    lower = text.lower()
    words = set(_words(lower))
    hits = len(words & terms)
    hits += sum(1 for phrase in terms if " " in phrase and phrase in lower)
    return hits


def _clamp(value: float) -> int:
    return max(1, min(5, int(round(value))))


def _event_text(event: Event) -> str:
    return f"{event.label}: {event.text}".strip()


def _best_event(events: list[Event], terms: set[str]) -> Event | None:
    if not events:
        return None
    return max(
        events,
        key=lambda event: (
            _term_hits(_event_text(event) + " " + event.label, terms),
            1 if event.kind in {"dialogue", "action"} else 0,
            len(event.text),
        ),
    )


def _score_window(episode: Episode, start: float, end: float) -> tuple[dict[str, int], str, str, str, str]:
    events = [event for event in episode.events if event.end_seconds > start and event.start_seconds < end]
    opening = [event for event in events if event.start_seconds < start + 3 and event.end_seconds > start]
    ending = [event for event in events if event.end_seconds > end - 8 and event.start_seconds < end]
    dialogue_events = [event for event in events if event.kind == "dialogue"]
    action_events = [event for event in events if event.kind == "action"]

    hook_event = _best_event(opening, HOOK_TERMS) or _best_event(opening, EMOTION_TERMS) or _best_event(opening, set())
    cliff_event = _best_event(ending, CLIFF_TERMS) or _best_event(ending, EMOTION_TERMS) or _best_event(ending, set())

    opening_text = " ".join(_event_text(event) for event in opening)
    ending_text = " ".join(_event_text(event) for event in ending)
    all_text = " ".join(_event_text(event) for event in events)
    hook_hits = _term_hits(opening_text, HOOK_TERMS)
    hook_emotion = _term_hits(opening_text, EMOTION_TERMS)
    cliff_hits = _term_hits(ending_text, CLIFF_TERMS)
    ending_question = "?" in ending_text
    unresolved_action = any(term in ending_text.lower() for term in ("turns", "opens", "enters", "arrives", "reveals", "stares", "gasps", "knocks"))
    emotion_hits = _term_hits(all_text, EMOTION_TERMS)

    hook_score = _clamp(1.1 + hook_hits * 1.15 + hook_emotion * 0.45 + (0.4 if any(e.kind == "dialogue" for e in opening) else 0))
    cliff_score = _clamp(1.2 + cliff_hits * 0.85 + (0.9 if ending_question else 0) + (0.65 if unresolved_action else 0))
    clarity_score = _clamp(1.0 + min(2.2, len(dialogue_events) / 3.0) + min(1.2, len(action_events) / 5.0) + (0.5 if episode.logline else 0))
    intensity_score = _clamp(1.0 + min(3.5, emotion_hits * 0.55 + sum(1 for e in events if e.kind == "dialogue" and ("!" in e.text or "?" in e.text)) * 0.35))

    hook = f"Opening moment: {_event_text(hook_event)}" if hook_event else "No clearly identifiable hook in the first 3 seconds."
    cliffhanger = f"Ending moment: {_event_text(cliff_event)}" if cliff_event else "No clearly identifiable unresolved ending moment."
    evidence_hook = hook_event.text[:260] if hook_event else ""
    evidence_cliff = cliff_event.text[:260] if cliff_event else ""
    why = (
        "Offline heuristic estimate based on opening-event language, ending-event cues, "
        "dialogue/action density, and emotional wording. Treat this as a shortlist, not an AI editorial verdict."
    )
    return (
        {
            "hook": hook_score,
            "cliffhanger": cliff_score,
            "standalone_clarity": clarity_score,
            "emotional_intensity": intensity_score,
        },
        hook,
        cliffhanger,
        why,
        evidence_hook + " || " + evidence_cliff,
    )


def _overlap_ratio(a: PromoCandidate, b: PromoCandidate) -> float:
    overlap = max(0.0, min(a.end_seconds, b.end_seconds) - max(a.start_seconds, b.start_seconds))
    shorter = min(a.duration_seconds, b.duration_seconds)
    return overlap / shorter if shorter > 0 else 0.0


def generate_heuristic_candidates(episode: Episode, limit: int = 3) -> list[PromoCandidate]:
    """Create a transparent offline baseline from timed screenplay events."""
    starts = sorted({round(event.start_seconds, 2) for event in episode.events})
    ends = sorted({round(event.end_seconds, 2) for event in episode.events})
    candidates: list[PromoCandidate] = []

    # Only use event boundaries, so suggestions are traceable to screenplay timing.
    for start in starts:
        for end in ends:
            duration = end - start
            if duration < 20 or duration > 60 or end > episode.duration_seconds + 0.05:
                continue
            scores, hook, cliffhanger, why, evidence = _score_window(episode, start, end)
            candidates.append(
                PromoCandidate(
                    episode_id=episode.episode_id,
                    start_seconds=start,
                    end_seconds=end,
                    hook=hook,
                    cliffhanger=cliffhanger,
                    why_it_works=why,
                    scores=scores,
                    method="heuristic_offline",
                    hook_evidence=evidence.split(" || ", 1)[0],
                    cliffhanger_evidence=evidence.split(" || ", 1)[1],
                    validation_warnings=[
                        "Generated by keyword/density heuristics, not an LLM.",
                        "Needs human editorial review for actual story meaning and visual context.",
                    ],
                    human_review_required=True,
                )
            )

    candidates.sort(key=lambda item: (item.final_score, item.scores["hook"], item.scores["cliffhanger"], -item.start_seconds), reverse=True)
    selected: list[PromoCandidate] = []
    for candidate in candidates:
        if any(_overlap_ratio(candidate, chosen) >= 0.82 for chosen in selected):
            continue
        selected.append(candidate)
        if len(selected) >= limit:
            break
    return selected
