"""Backward-compatible imports for prompt parsing; API calls use the Groq adapter."""
from .prompts import PROMPT_TEMPLATE, build_prompt, parse_model_response

__all__ = ["PROMPT_TEMPLATE", "build_prompt", "parse_model_response"]
