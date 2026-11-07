from __future__ import annotations

import re
import zipfile
from pathlib import Path

from .models import Episode, Event, Scene

TIMESTAMP = r"\d{2}:\d{2}(?:\.\d+)?"
SCENE_RE = re.compile(
    rf"^SCENE\s+(?P<number>\d+)\s*\n"
    rf"Scene heading:\s*(?P<heading>.*?)\s*\n"
    rf"Scene start:\s*(?P<start>{TIMESTAMP})\s*\n"
    rf"Scene end:\s*(?P<end>{TIMESTAMP})\s*$",
    re.MULTILINE | re.IGNORECASE,
)
BLOCK_RE = re.compile(
    rf"^\*\*(?P<label>.+?):\*\*\s*\n"
    rf"Start:\s*\((?P<start>{TIMESTAMP})\)\s*\|\s*"
    rf"End:\s*\((?P<end>{TIMESTAMP})\)\s*\n"
    rf"(?P<body>.*?)(?=^\*\*.+?:\*\*\s*$|\Z)",
    re.MULTILINE | re.DOTALL,
)


def _seconds(value: str) -> float:
    minutes, seconds = value.split(":", 1)
    return int(minutes) * 60 + float(seconds)


def _header_value(text: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}:\s*(.*?)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def parse_episode(text: str, source_name: str) -> Episode:
    episode_label = _header_value(text, "EPISODE NUMBER")
    episode_match = re.search(r"(\d+)", episode_label or source_name)
    if not episode_match:
        raise ValueError(f"Could not determine episode number from {source_name}")
    episode_id = int(episode_match.group(1))

    scenes: list[Scene] = []
    for match in SCENE_RE.finditer(text):
        scenes.append(
            Scene(
                number=int(match.group("number")),
                heading=match.group("heading").strip(),
                start_seconds=_seconds(match.group("start")),
                end_seconds=_seconds(match.group("end")),
            )
        )

    events: list[Event] = []
    for match in BLOCK_RE.finditer(text):
        label = match.group("label").strip()
        label_upper = label.upper()
        if label_upper == "CAMERA":
            kind = "camera"
        elif label_upper == "ACTION":
            kind = "action"
        elif label_upper in {"SOUND FX", "SOUND", "MUSIC"}:
            kind = "sound"
        else:
            kind = "dialogue"
        start = _seconds(match.group("start"))
        end = _seconds(match.group("end"))
        body = re.sub(r"\s+", " ", match.group("body")).strip()
        scene_number = None
        for scene in scenes:
            if scene.start_seconds - 0.05 <= start <= scene.end_seconds + 0.05:
                scene_number = scene.number
                break
        events.append(
            Event(
                label=label,
                kind=kind,
                start_seconds=start,
                end_seconds=end,
                text=body,
                scene_number=scene_number,
            )
        )

    scenes.sort(key=lambda item: (item.start_seconds, item.number))
    events.sort(key=lambda item: (item.start_seconds, item.end_seconds, item.kind))
    if not scenes:
        raise ValueError(f"No scene blocks found in {source_name}")
    if not events:
        raise ValueError(f"No timed screenplay blocks found in {source_name}")

    duration = max(
        [scene.end_seconds for scene in scenes]
        + [event.end_seconds for event in events]
    )
    return Episode(
        episode_id=episode_id,
        source_name=source_name,
        logline=_header_value(text, "EPISODE LOGLINE"),
        continuity_notes=_header_value(text, "CONTINUITY NOTES"),
        duration_seconds=round(duration, 2),
        scenes=scenes,
        events=events,
    )


def read_input(source: str | Path) -> list[Episode]:
    """Read .txt screenplays from a ZIP archive or a directory."""
    source_path = Path(source).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {source_path}")

    file_items: list[tuple[str, bytes]] = []
    if source_path.is_file() and source_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(source_path, "r") as archive:
            for item in archive.infolist():
                if item.is_dir() or not item.filename.lower().endswith(".txt"):
                    continue
                # Read files directly from the archive; never extract untrusted paths.
                file_items.append((Path(item.filename).name, archive.read(item)))
    elif source_path.is_dir():
        for item in sorted(source_path.rglob("*.txt")):
            file_items.append((item.name, item.read_bytes()))
    else:
        raise ValueError("Input must be a .zip archive or a folder containing .txt files")

    if not file_items:
        raise ValueError("No .txt screenplay files were found in the input")

    episodes: list[Episode] = []
    for name, data in file_items:
        text = data.decode("utf-8-sig", errors="replace")
        episodes.append(parse_episode(text, name))

    episodes.sort(key=lambda episode: episode.episode_id)
    ids = [episode.episode_id for episode in episodes]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate episode numbers found in the input")
    return episodes
