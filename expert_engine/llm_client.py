"""Shared LLM Client — cached client instances, auto-detect OpenRouter, retry with backoff.

Fixes:
- #16: One client per (api_key, base_url) combo, not per call
- #23: Retry with exponential backoff (3 attempts)
- #24: No more time.sleep(0.3) in callers
- #25: JSON parse with fallback + logging on malformed response
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Cache: (api_key, base_url) -> Anthropic client
_client_cache: dict[tuple[str, str | None], Anthropic] = {}


def get_client(api_key: str | None = None, base_url: str | None = None) -> Anthropic:
    """Return a cached Anthropic client for the given credentials.

    Auto-detects OpenRouter keys (sk-or-*) and sets the base_url accordingly.
    """
    resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    resolved_base = base_url or os.environ.get("ANTHROPIC_BASE_URL")

    # Auto-detect OpenRouter
    if resolved_key.startswith("sk-or-") and not resolved_base:
        resolved_base = "https://openrouter.ai/api"

    cache_key = (resolved_key, resolved_base)
    if cache_key not in _client_cache:
        kwargs: dict[str, Any] = {"api_key": resolved_key}
        if resolved_base:
            kwargs["base_url"] = resolved_base
        _client_cache[cache_key] = Anthropic(**kwargs)
        logger.debug("Created new Anthropic client (base_url=%s)", resolved_base)

    return _client_cache[cache_key]


def call_llm_with_retry(
    client: Anthropic,
    *,
    model: str,
    max_tokens: int,
    system: str,
    messages: list[dict],
    max_attempts: int = 3,
) -> Any:
    """Call LLM with exponential backoff retry.

    Retries on transient errors (rate limits, server errors).
    Raises on permanent errors (auth, bad request).
    """
    delays = [1.0, 2.0, 4.0]  # seconds between retries
    last_exc: Exception | None = None

    for attempt in range(max_attempts):
        try:
            return client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
        except Exception as e:
            last_exc = e
            err_str = str(e).lower()
            # Don't retry auth errors or bad requests
            if any(term in err_str for term in ("authentication", "401", "403", "invalid_api_key", "400")):
                logger.error("Permanent LLM error (attempt %d/%d): %s", attempt + 1, max_attempts, e)
                raise

            logger.warning(
                "Transient LLM error (attempt %d/%d): %s — retrying in %.1fs",
                attempt + 1, max_attempts, e, delays[min(attempt, len(delays) - 1)],
            )
            if attempt < max_attempts - 1:
                time.sleep(delays[attempt])

    raise last_exc  # type: ignore[misc]


def parse_json_response(text: str) -> dict:
    """Parse JSON from LLM response text with fallback.

    Tries direct parse first, then looks for embedded JSON object.
    Logs a warning on malformed responses and returns a fallback dict.
    """
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find embedded JSON
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            logger.warning(
                "Malformed JSON in LLM response (embedded parse failed). "
                "First 200 chars: %s",
                text[:200],
            )
    else:
        logger.warning(
            "No JSON object found in LLM response. First 200 chars: %s",
            text[:200],
        )

    # Fallback: treat entire text as reply
    return {
        "reply": text,
        "homework_instruction": "",
        "session_summary": "",
        "progress_note": "",
    }
