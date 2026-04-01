"""
wish_engine.executor
~~~~~~~~~~~~~~~~~~~~
Runtime execution layer: translate a signal + user context into real API results.

Usage::

    from wish_engine.executor import execute, execute_pipeline

    # Single signal
    results = execute("sad", user_lat=25.2, user_lng=55.3, limit=3)
    for r in results:
        print(r["rendered"])   # best-effort formatted string
        print(r["raw"])        # original API response dict

    # Full pipeline: text → signals → results
    out = execute_pipeline(
        ["feeling lonely, nothing to do"],
        user_lat=25.2, user_lng=55.3,
    )
    print(out["signals"])   # ["lonely", "bored"]
    print(out["results"])   # {"lonely": [...], "bored": [...]}
"""
from __future__ import annotations

import importlib
import inspect
from typing import Optional


class _SafeDict(dict):
    """Return empty string for missing keys so str.format_map never raises KeyError."""

    def __missing__(self, key: str) -> str:
        return ""


def execute(
    signal: str,
    user_lat: Optional[float] = None,
    user_lng: Optional[float] = None,
    limit: int = 3,
    cat: Optional[str] = None,
) -> list[dict]:
    """
    Execute a signal and return real recommendation results.

    Parameters
    ----------
    signal    : attention signal key, e.g. "sad" or "want_learn"
    user_lat  : user latitude  — enables location-aware APIs when provided
    user_lng  : user longitude — enables location-aware APIs when provided
    limit     : max number of *successful* results to return
    cat       : optional category filter, e.g. "healing", "place"

    Returns
    -------
    List of result dicts, each with keys:

        api      — module path, e.g. "wish_engine.apis.joke_api"
        fn       — function name called
        cat      — category tag
        star     — urgency tier: "meteor" | "star" | "earth"
        rendered — best-effort formatted string using the action template
        raw      — original API response (dict | list | str)

    Failed API calls are silently skipped; the list may be shorter than *limit*.
    """
    from wish_engine.soul_api_bridge import get_api_actions

    actions = get_api_actions(signal)
    if cat is not None:
        actions = [a for a in actions if a.get("cat") == cat]

    results: list[dict] = []
    for action in actions:
        if len(results) >= limit:
            break
        result = _call_action(action, user_lat, user_lng)
        if result is not None:
            results.append(result)

    return results


def execute_pipeline(
    utterances: list[str],
    user_lat: Optional[float] = None,
    user_lng: Optional[float] = None,
    limit_per_signal: int = 2,
    max_signals: int = 3,
) -> dict:
    """
    Full pipeline: raw utterances → detected signals → executed results.

    Parameters
    ----------
    utterances        : list of user text strings
    user_lat / lng    : user location (optional)
    limit_per_signal  : max API results per signal
    max_signals       : cap on how many signals to act on

    Returns
    -------
    {
        "signals": ["sad", "lonely"],
        "results": {
            "sad":    [<result>, ...],
            "lonely": [<result>, ...]
        }
    }
    """
    from wish_engine.soul_recommender import detect_surface_attention

    signals = list(detect_surface_attention(utterances))[:max_signals]
    results: dict[str, list] = {}
    for signal in signals:
        results[signal] = execute(
            signal,
            user_lat=user_lat,
            user_lng=user_lng,
            limit=limit_per_signal,
        )
    return {"signals": signals, "results": results}


# ── internal helpers ──────────────────────────────────────────────────────────

def _call_action(
    action: dict,
    lat: Optional[float],
    lng: Optional[float],
) -> Optional[dict]:
    """
    Import the API module, call the function, return a structured result.

    Returns None on any failure (import error, exception, empty/None response).
    """
    try:
        module = importlib.import_module(action["api"])
        fn = getattr(module, action["fn"])
        kwargs = _build_kwargs(fn, action.get("params", {}), lat, lng)
        raw = fn(**kwargs)

        if raw is None:
            return None
        if isinstance(raw, list) and len(raw) == 0:
            return None

        return {
            "api":      action["api"],
            "fn":       action["fn"],
            "cat":      action.get("cat", ""),
            "star":     action.get("star", "meteor"),
            "rendered": _render(action.get("template", ""), raw),
            "raw":      raw,
        }
    except Exception:
        return None


def _build_kwargs(
    fn,
    params: dict,
    lat: Optional[float],
    lng: Optional[float],
) -> dict:
    """
    Merge static action params with runtime lat/lng.

    lat and lng are only injected if the target function's signature declares
    those parameter names, preventing TypeError on non-location APIs.
    """
    kwargs = dict(params)
    try:
        param_names = set(inspect.signature(fn).parameters.keys())
        if "lat" in param_names and lat is not None:
            kwargs["lat"] = lat
        if "lng" in param_names and lng is not None:
            kwargs["lng"] = lng
    except (ValueError, TypeError):
        pass
    return kwargs


def _render(template: str, raw) -> str:
    """
    Best-effort template rendering via str.format_map.

    Context rules:
    - dict  → used directly
    - list  → first item used (if it's a dict), else bound to {result}
    - str   → bound to {result}
    - other → str(raw) bound to {result}

    Missing keys return empty string. Any rendering error returns the
    template unchanged (visible as unrendered placeholders).
    """
    if not template:
        return ""

    if isinstance(raw, list) and raw:
        ctx: dict = raw[0] if isinstance(raw[0], dict) else {"result": raw[0]}
    elif isinstance(raw, dict):
        ctx = raw
    elif isinstance(raw, str):
        ctx = {"result": raw}
    else:
        ctx = {"result": str(raw)}

    ctx = dict(ctx)
    ctx.setdefault("result", raw)

    try:
        return template.format_map(_SafeDict(ctx))
    except Exception:
        return template
