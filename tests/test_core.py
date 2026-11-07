import unittest
import os
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from kukupromo.heuristics import generate_heuristic_candidates
from kukupromo.prompts import build_prompt, parse_model_response
from kukupromo.groq import GroqPromoModel
from kukupromo.models import Episode, Event, format_timestamp, parse_timestamp
from kukupromo.parser import parse_episode


SAMPLE = """EPISODE NUMBER: Episode 1
EPISODE LOGLINE: A bride discovers betrayal at the altar.
CONTINUITY NOTES: First episode.

--- SCRIPT START ---

SCENE 01
Scene heading: INT. CHURCH - DAY
Scene start: 00:00.00
Scene end: 01:00.00

Actions and dialogue:

**ACTION:**
Start: (00:00.00) | End: (00:04.00)
A bride enters and sees the groom with another woman.

**LADY JULIANA (Shocked):**
Start: (00:04.00) | End: (00:08.00)
"Why are you holding her hand?"

**CAMERA:**
Start: (00:08.00) | End: (00:10.00)
Close up on the groom.

**GERALD (Cold):**
Start: (00:30.00) | End: (00:35.00)
"Because I am marrying her."

**ACTION:**
Start: (00:55.00) | End: (01:00.00)
A stranger suddenly enters and everyone turns in shock.
"""


class CoreTests(unittest.TestCase):
    def test_timestamp_roundtrip(self):
        self.assertEqual(parse_timestamp("01:10.50"), 70.5)
        self.assertEqual(format_timestamp(70.5), "01:10.50")

    def test_parser_extracts_metadata_scenes_and_timed_blocks(self):
        episode = parse_episode(SAMPLE, "episode-001.txt")
        self.assertEqual(episode.episode_id, 1)
        self.assertIn("bride", episode.logline)
        self.assertEqual(len(episode.scenes), 1)
        self.assertEqual(len(episode.events), 5)
        self.assertEqual(episode.duration_seconds, 60.0)
        self.assertEqual(episode.events[0].kind, "action")
        self.assertEqual(episode.events[1].kind, "dialogue")

    def test_heuristic_only_returns_valid_clip_lengths(self):
        episode = Episode(
            episode_id=2,
            source_name="sample.txt",
            logline="A character discovers a secret and faces a threat.",
            continuity_notes="A dramatic confrontation begins.",
            duration_seconds=90.0,
            events=[
                Event("ACTION", "action", 0, 4, "A woman discovers a secret letter."),
                Event("WOMAN (Shocked)", "dialogue", 4, 8, "What is this?"),
                Event("MAN (Threatening)", "dialogue", 24, 30, "You were never supposed to know!"),
                Event("ACTION", "action", 55, 60, "The door opens and a stranger enters."),
                Event("CAMERA", "camera", 60, 65, "Everyone turns in shock."),
            ],
        )
        candidates = generate_heuristic_candidates(episode, limit=3)
        self.assertTrue(candidates)
        for candidate in candidates:
            self.assertGreaterEqual(candidate.duration_seconds, 20)
            self.assertLessEqual(candidate.duration_seconds, 60)
            self.assertEqual(candidate.method, "heuristic_offline")

    def test_ai_response_parser_and_time_evidence_validation(self):
        episode = parse_episode(SAMPLE, "episode-001.txt")
        raw = """{
          "candidates": [{
            "start_time": "00:00.00",
            "end_time": "00:30.00",
            "hook": "A bride sees betrayal immediately.",
            "cliffhanger": "The groom reveals he is marrying another woman.",
            "why_it_works": "It opens with betrayal and closes on a reveal.",
            "hook_evidence": "A bride enters and sees the groom with another woman.",
            "cliffhanger_evidence": "Because I am marrying her.",
            "scores": {"hook": 5, "cliffhanger": 4, "standalone_clarity": 4, "emotional_intensity": 5}
          }]
        }"""
        candidates = parse_model_response(raw, episode)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].duration_seconds, 30.0)
        self.assertTrue(any("cliffhanger evidence does not occur near the end" in warning.lower() for warning in candidates[0].validation_warnings))
        prompt = build_prompt(episode)
        self.assertIn("SCENE LIST", prompt)
        self.assertIn("FIRST 3 SECONDS", prompt)


    def test_groq_adapter_uses_json_request(self):
        episode = parse_episode(SAMPLE, "episode-001.txt")
        raw = """{
          "candidates": [{
            "start_time": "00:00.00",
            "end_time": "00:30.00",
            "hook": "A bride sees betrayal immediately.",
            "cliffhanger": "The groom reveals he is marrying another woman.",
            "why_it_works": "It opens with betrayal and closes on a reveal.",
            "hook_evidence": "A bride enters and sees the groom with another woman.",
            "cliffhanger_evidence": "Because I am marrying her.",
            "scores": {"hook": 5, "cliffhanger": 4, "standalone_clarity": 4, "emotional_intensity": 5}
          }]
        }"""
        captured = {}

        class FakeOpenAI:
            def __init__(self, **kwargs):
                captured["client_kwargs"] = kwargs
                completions = SimpleNamespace(create=self.create)
                self.chat = SimpleNamespace(completions=completions)

            def create(self, **kwargs):
                captured["request_kwargs"] = kwargs
                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(content=raw)
                        )
                    ]
                )

        with patch("kukupromo.groq.OpenAI", FakeOpenAI):
            with patch.dict(
                os.environ,
                {
                    "GROQ_API_KEY": "test-key",
                    "GROQ_MODEL": "qwen/qwen3.8-27b",
                }
            ):
                model = GroqPromoModel()
                returned_raw, candidates = model.analyze_episode(episode)

        self.assertEqual(returned_raw, raw)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].method, "groq_llm")
        self.assertEqual(
            captured["client_kwargs"]["base_url"],
            "https://api.groq.com/openai/v1"
        )
        self.assertEqual(
            captured["request_kwargs"]["response_format"],
            {"type": "json_object"}
        )
        self.assertEqual(
            captured["request_kwargs"]["reasoning_effort"],
            "none"
        )


if __name__ == "__main__":
    unittest.main()
