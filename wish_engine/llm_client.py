"""Shared LLM client with caching, OpenRouter detection, retry, and error handling."""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

_clients: dict[str, anthropic.Anthropic] = {}


def get_client(api_key: str | None = None) -> anthropic.Anthropic:
    """Get or create a cached Anthropic client with OpenRouter auto-detection."""
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key in _clients:
        return _clients[api_key]

    kwargs: dict[str, Any] = {"api_key": api_key}
    if api_key.startswith("sk-or-"):
        kwargs["base_url"] = "https://openrouter.ai/api"

    client = anthropic.Anthropic(**kwargs)
    _clients[api_key] = client
    return client


def resolve_model(base_model: str, api_key: str | None = None) -> str:
    """Resolve model name based on API key type (OpenRouter vs direct)."""
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if key.startswith("sk-or-"):
        # OpenRouter needs vendor prefix
        if not base_model.startswith("anthropic/"):
            return f"anthropic/{base_model}"
        return base_model
    else:
        # Direct Anthropic API — strip vendor prefix
        if base_model.startswith("anthropic/"):
            return base_model.removeprefix("anthropic/")
        return base_model


def call_llm(
    model: str,
    prompt: str,
    api_key: str | None = None,
    max_tokens: int = 256,
    temperature: float = 0.3,
    max_retries: int = 3,
    parse_json: bool = False,
    messages: list[dict[str, str]] | None = None,
) -> str | dict[str, Any]:
    """Call LLM with retry and optional JSON parsing.

    Args:
        model: Base model name (e.g. "claude-haiku-4-5-20251001").
            OpenRouter prefix is added automatically based on api_key.
        prompt: User prompt (ignored if messages is provided).
        api_key: API key. If None, reads from ANTHROPIC_API_KEY env.
        max_tokens: Max tokens for response.
        temperature: Sampling temperature.
        max_retries: Number of retry attempts.
        parse_json: If True, parse response as JSON with fallback extraction.
        messages: Optional pre-built messages list (overrides prompt).

    Returns:
        Raw text string, or parsed dict if parse_json=True.
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    client = get_client(key)
    resolved_model = resolve_model(model, key)
    msgs = messages or [{"role": "user", "content": prompt}]

    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=resolved_model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=msgs,
            )
            if not response.content:
                logger.warning("Empty LLM response on attempt %d", attempt + 1)
                continue

            raw = response.content[0].text

            if not parse_json:
                return raw

            # JSON parsing with fallback
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                start = raw.find("{")
                end = raw.rfind("}") + 1
                if start >= 0 and end > start:
                    try:
                        return json.loads(raw[start:end])
                    except json.JSONDecodeError:
                        logger.warning("Truncated JSON on attempt %d: %s", attempt + 1, raw[:100])
                        if attempt < max_retries - 1:
                            continue
                        return {}
                else:
                    logger.warning("No JSON found on attempt %d: %s", attempt + 1, raw[:100])
                    if attempt < max_retries - 1:
                        continue
                    return {}

        except Exception as e:
            logger.warning("LLM call failed (attempt %d/%d): %s", attempt + 1, max_retries, e)
            if attempt < max_retries - 1:
                time.sleep(1.0 * (2 ** attempt))  # 1s, 2s, 4s
                continue
            raise

    return "" if not parse_json else {}
