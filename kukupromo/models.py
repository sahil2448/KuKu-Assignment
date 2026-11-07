from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Scene:
    number: int
    heading: str
    start_seconds: float
    end_seconds: float


@dataclass
class Event:
    label: str
    kind: str
    start_seconds: float
    end_seconds: float
    text: str
    scene_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Episode:
    episode_id: int
    source_name: str
    logline: str
    continuity_notes: str
    duration_seconds: float
    scenes: list[Scene] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "source_name": self.source_name,
            "logline": self.logline,
            "continuity_notes": self.continuity_notes,
            "duration_seconds": self.duration_seconds,
            "scenes": [asdict(x) for x in self.scenes],
            "events": [x.to_dict() for x in self.events],
        }


@dataclass
class PromoCandidate:
    episode_id: int
    start_seconds: float
    end_seconds: float
    hook: str
    cliffhanger: str
    why_it_works: str
    scores: dict[str, int]
    method: str
    hook_evidence: str = ""
    cliffhanger_evidence: str = ""
    validation_warnings: list[str] = field(default_factory=list)
    human_review_required: bool = True

    @property
    def duration_seconds(self) -> float:
        return round(self.end_seconds - self.start_seconds, 2)

    @property
    def final_score(self) -> float:
        weights = {"hook": 30, "cliffhanger": 30, "standalone_clarity": 25, "emotional_intensity": 15}
        weighted = sum(self.scores.get(key, 0) * weight for key, weight in weights.items())
        return round(weighted / 5, 1)

    def to_dict(self, rank: int | None = None, promo_id: str | None = None) -> dict[str, Any]:
        return {
            "rank": rank,
            "promo_id": promo_id,
            "episode_id": self.episode_id,
            "segments": [
                {
                    "episode_id": self.episode_id,
                    "start": format_timestamp(self.start_seconds),
                    "end": format_timestamp(self.end_seconds),
                    "duration_seconds": self.duration_seconds,
                }
            ],
            "total_duration_seconds": self.duration_seconds,
            "hook": self.hook,
            "cliffhanger": self.cliffhanger,
            "why_it_works": self.why_it_works,
            "scores": self.scores,
            "final_score": self.final_score,
            "method": self.method,
            "evidence": {
                "hook": self.hook_evidence,
                "cliffhanger": self.cliffhanger_evidence,
            },
            "validation_warnings": self.validation_warnings,
            "human_review_required": self.human_review_required,
        }


def parse_timestamp(value: str | float | int) -> float:
    """Parse MM:SS[.fraction] or a numeric second value."""
    if isinstance(value, (int, float)):
        return float(value)
    value = str(value).strip()
    if ":" not in value:
        return float(value)
    minutes, seconds = value.split(":", 1)
    return int(minutes) * 60 + float(seconds)


def format_timestamp(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    minutes = int(seconds // 60)
    remainder = seconds - minutes * 60
    return f"{minutes:02d}:{remainder:05.2f}"
