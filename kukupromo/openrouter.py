
from __future__ import annotations

import os
from pathlib import Path

from openai import OpenAI

from .models import Episode, PromoCandidate
from .prompts import build_prompt, parse_model_response


DEFAULT_MODEL = "qwen/qwen3.8-27b"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def load_project_env():
    """Load variables from the project's .env file."""
    env_path = Path(__file__).resolve().parents[1] / ".env"

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


class GroqPromoModel:
    """Groq adapter compatible with the original Kuku CLI."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
    ):
        load_project_env()

        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY is missing. Configure it in the project .env file."
            )

        self.model_name = (
            model_name
            or os.getenv("GROQ_MODEL")
            or DEFAULT_MODEL
        )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=GROQ_BASE_URL,
            timeout=150.0,
            max_retries=0,
        )

        self.last_parse_error = None

    def analyze_episode(
        self,
        episode: Episode,
        limit: int = 3,
        neighbor_context: str = "",
    ) -> tuple[str, list[PromoCandidate]]:

        # Preserve the original project's prompt-generation logic.
        prompt = build_prompt(
            episode,
            limit=limit,
            neighbor_context=neighbor_context,
        )

        self.last_parse_error = None

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=5000,
                reasoning_effort="none",
                temperature=0.4,
            )

        except Exception as exc:
            raise RuntimeError(
                f"Groq request failed: {exc}"
            ) from exc

        try:
            choice = response.choices[0]
            raw_text = choice.message.content or ""

        except (AttributeError, IndexError, TypeError) as exc:
            raise RuntimeError(
                "Groq returned an unexpected response structure."
            ) from exc

        if not raw_text.strip():
            raise RuntimeError(
                "Groq returned an empty response. "
                "Check the model response and token limits."
            )

        try:
            candidates = parse_model_response(raw_text, episode)

        except Exception as exc:
            self.last_parse_error = (
                f"Could not parse Groq response: {exc}"
            )
            candidates = []

        return raw_text, candidates


# Keep the old import name so the existing CLI does not need rewriting.
OpenRouterPromoModel = GroqPromoModel
