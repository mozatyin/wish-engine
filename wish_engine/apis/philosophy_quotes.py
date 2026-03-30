"""Philosophy & wisdom quotes API.

Primary source: api.quotable.io (free, no auth, 220 req/3s rate limit)
Fallback:       zenquotes.io    (free, no auth, 50 quotes/batch)
Static fallback: embedded curated quotes (zero network dependency)

Usage:
    from wish_engine.apis.philosophy_quotes import get_quote, get_quotes_by_tradition

    q = get_quote()
    # -> {"author": "Marcus Aurelius", "text": "...", "tradition": "Stoic"}

    qs = get_quotes_by_tradition("Buddhist", limit=5)
"""

from __future__ import annotations

import json
import random
import ssl
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError

_SSL_CTX = ssl._create_unverified_context()

# ---------------------------------------------------------------------------
# Tradition mapping: quotable.io author slugs -> tradition label
# Built from verified author list (api.quotable.io/authors, 2026-03-31)
# ---------------------------------------------------------------------------
_AUTHOR_TRADITION: dict[str, str] = {
    # Stoic
    "marcus-aurelius":     "Stoic",
    "epictetus":           "Stoic",
    "seneca-the-younger":  "Stoic",
    "cicero":              "Stoic",
    "heraclitus":          "Stoic",
    # Buddhist
    "the-buddha":          "Buddhist",
    "thich-nhat-hanh":     "Buddhist",
    "dalai-lama":          "Buddhist",
    "pema-chodron":        "Buddhist",
    "daisaku-ikeda":       "Buddhist",
    # Taoist / Chinese
    "laozi":               "Taoist",
    "confucius":           "Confucian",
    "sun-tzu":             "Chinese",
    "chanakya":            "Indian",
    # Greek / Western Classical
    "socrates":            "Greek",
    "plato":               "Greek",
    "aristotle":           "Greek",
    "plutarch":            "Greek",
    "isocrates":           "Greek",
    "aesop":               "Greek",
    "sophocles":           "Greek",
    "euripides":           "Greek",
    "aeschylus":           "Greek",
    # Sufi / Islamic mysticism
    "rumi":                "Sufi",
    "kahlil-gibran":       "Sufi",
    # Modern / Perennial
    "alan-watts":          "Perennial",
    "eckhart-tolle":       "Perennial",
    "richard-bach":        "Perennial",
    "ralph-waldo-emerson": "Transcendentalist",
    "henry-david-thoreau": "Transcendentalist",
    # Western philosophy
    "friedrich-nietzsche": "Philosophy",
    "albert-camus":        "Philosophy",
    "jean-paul-sartre":    "Philosophy",
    "soren-kierkegaard":   "Philosophy",
    "blaise-pascal":       "Philosophy",
    "francis-bacon":       "Philosophy",
    "john-locke":          "Philosophy",
    "john-dewey":          "Philosophy",
    "william-james":       "Philosophy",
    "voltaire":            "Philosophy",
    "michel-de-montaigne": "Philosophy",
    "henri-frederic-amiel":"Philosophy",
    "augustine-of-hippo":  "Philosophy",
    "albert-schweitzer":   "Philosophy",
}

# Grouped slugs per tradition for batch queries
_TRADITION_AUTHORS: dict[str, list[str]] = {}
for _slug, _trad in _AUTHOR_TRADITION.items():
    _TRADITION_AUTHORS.setdefault(_trad, []).append(_slug)

# ---------------------------------------------------------------------------
# Static fallback quotes — used when both APIs are unreachable
# ---------------------------------------------------------------------------
_STATIC_QUOTES: list[dict] = [
    {"author": "Marcus Aurelius",    "text": "You have power over your mind, not outside events. Realize this, and you will find strength.",          "tradition": "Stoic"},
    {"author": "Epictetus",          "text": "Make the best use of what is in your power, and take the rest as it happens.",                          "tradition": "Stoic"},
    {"author": "Seneca",             "text": "Luck is what happens when preparation meets opportunity.",                                               "tradition": "Stoic"},
    {"author": "Marcus Aurelius",    "text": "Waste no more time arguing about what a good man should be. Be one.",                                   "tradition": "Stoic"},
    {"author": "The Buddha",         "text": "A disciplined mind brings happiness.",                                                                  "tradition": "Buddhist"},
    {"author": "The Buddha",         "text": "Peace comes from within. Do not seek it without.",                                                      "tradition": "Buddhist"},
    {"author": "Thích Nhất Hạnh",    "text": "The present moment is the only moment available to us, and it is the door to all moments.",             "tradition": "Buddhist"},
    {"author": "Dalai Lama",         "text": "Be kind whenever possible. It is always possible.",                                                     "tradition": "Buddhist"},
    {"author": "Laozi",              "text": "He who talks more is sooner exhausted.",                                                                "tradition": "Taoist"},
    {"author": "Laozi",              "text": "A journey of a thousand miles begins with a single step.",                                              "tradition": "Taoist"},
    {"author": "Laozi",              "text": "Nature does not hurry, yet everything is accomplished.",                                                "tradition": "Taoist"},
    {"author": "Confucius",          "text": "It does not matter how slowly you go as long as you do not stop.",                                      "tradition": "Confucian"},
    {"author": "Confucius",          "text": "He who learns but does not think is lost. He who thinks but does not learn is in great danger.",         "tradition": "Confucian"},
    {"author": "Rumi",               "text": "Out beyond ideas of wrongdoing and rightdoing, there is a field. I'll meet you there.",                 "tradition": "Sufi"},
    {"author": "Rumi",               "text": "Don't grieve. Anything you lose comes around in another form.",                                         "tradition": "Sufi"},
    {"author": "Socrates",           "text": "The unexamined life is not worth living.",                                                              "tradition": "Greek"},
    {"author": "Aristotle",          "text": "We are what we repeatedly do. Excellence, then, is not an act but a habit.",                            "tradition": "Greek"},
    {"author": "Alan Watts",         "text": "The only way to make sense out of change is to plunge into it, move with it, and join the dance.",      "tradition": "Perennial"},
    {"author": "Kahlil Gibran",      "text": "Your pain is the breaking of the shell that encloses your understanding.",                              "tradition": "Sufi"},
    {"author": "Marcus Aurelius",    "text": "The impediment to action advances action. What stands in the way becomes the way.",                     "tradition": "Stoic"},
]


def _http_get(url: str, timeout: int = 8) -> dict | list | None:
    """Fetch JSON from url, return parsed object or None on error."""
    try:
        req = Request(url, headers={"User-Agent": "WishEngine/1.0 (+https://soulmap.app)"})
        with urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            return json.loads(resp.read().decode())
    except (URLError, json.JSONDecodeError, Exception):
        return None


# ---------------------------------------------------------------------------
# Source 1: quotable.io
# ---------------------------------------------------------------------------
def _from_quotable_random(tags: str = "philosophy|wisdom") -> dict | None:
    """
    GET https://api.quotable.io/random?tags=philosophy|wisdom
    Response: {_id, content, author, authorSlug, tags, length}
    No auth required. Rate limit: 220 req per 3-second window.
    Supports: ?tags=<tag1|tag2>, ?author=<slug1|slug2>
    """
    data = _http_get(f"https://api.quotable.io/random?tags={tags}")
    if not data or "content" not in data:
        return None
    slug = data.get("authorSlug", "")
    return {
        "author":    data["author"],
        "text":      data["content"],
        "tradition": _AUTHOR_TRADITION.get(slug, "Wisdom"),
        "_source":   "quotable",
        "_id":       data.get("_id"),
    }


def _from_quotable_author(author_slugs: list[str]) -> dict | None:
    """
    GET https://api.quotable.io/random?author=slug1|slug2|...
    Returns one random quote from those authors.
    """
    if not author_slugs:
        return None
    slug_str = "|".join(author_slugs)
    data = _http_get(f"https://api.quotable.io/random?author={slug_str}")
    if not data or "content" not in data:
        return None
    slug = data.get("authorSlug", "")
    return {
        "author":    data["author"],
        "text":      data["content"],
        "tradition": _AUTHOR_TRADITION.get(slug, "Wisdom"),
        "_source":   "quotable",
        "_id":       data.get("_id"),
    }


def _from_quotable_list(author_slugs: list[str], limit: int = 10) -> list[dict]:
    """
    GET https://api.quotable.io/quotes?author=slug1|slug2&limit=N
    Returns up to `limit` quotes for the given authors.
    """
    if not author_slugs:
        return []
    slug_str = "|".join(author_slugs)
    data = _http_get(f"https://api.quotable.io/quotes?author={slug_str}&limit={limit}")
    if not data or "results" not in data:
        return []
    results = []
    for item in data["results"]:
        slug = item.get("authorSlug", "")
        results.append({
            "author":    item["author"],
            "text":      item["content"],
            "tradition": _AUTHOR_TRADITION.get(slug, "Wisdom"),
            "_source":   "quotable",
            "_id":       item.get("_id"),
        })
    return results


# ---------------------------------------------------------------------------
# Source 2: zenquotes.io
# ---------------------------------------------------------------------------
def _from_zenquotes_random() -> dict | None:
    """
    GET https://zenquotes.io/api/random
    Response: [{"q": "...", "a": "author", "c": "chars", "h": "html"}]
    No auth. Returns general wisdom; no category filter available.
    Useful as generic fallback only.
    """
    data = _http_get("https://zenquotes.io/api/random")
    if not data or not isinstance(data, list) or not data:
        return None
    item = data[0]
    q, a = item.get("q", ""), item.get("a", "")
    if not q or q.startswith("Unrecognized"):
        return None
    return {
        "author":    a,
        "text":      q,
        "tradition": "Wisdom",
        "_source":   "zenquotes",
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_quote(tradition: Optional[str] = None) -> dict:
    """Return one philosophy/wisdom quote.

    Args:
        tradition: Optional filter. One of "Stoic", "Buddhist", "Taoist",
                   "Confucian", "Sufi", "Greek", "Perennial",
                   "Transcendentalist", "Philosophy", "Chinese", "Indian".
                   If None, returns any philosophy/wisdom quote.

    Returns:
        {
          "author":    str,   # e.g. "Marcus Aurelius"
          "text":      str,   # quote body
          "tradition": str,   # e.g. "Stoic"
        }
    """
    # 1. Try tradition-specific authors on quotable.io
    if tradition:
        slugs = _TRADITION_AUTHORS.get(tradition, [])
        if slugs:
            q = _from_quotable_author(slugs)
            if q:
                return {k: v for k, v in q.items() if not k.startswith("_")}

    # 2. Try generic philosophy/wisdom tag on quotable.io
    q = _from_quotable_random("philosophy|wisdom|religion|spirituality")
    if q:
        return {k: v for k, v in q.items() if not k.startswith("_")}

    # 3. Zenquotes fallback
    q = _from_zenquotes_random()
    if q:
        return {k: v for k, v in q.items() if not k.startswith("_")}

    # 4. Static embedded fallback
    pool = [s for s in _STATIC_QUOTES if not tradition or s["tradition"] == tradition]
    if not pool:
        pool = _STATIC_QUOTES
    return dict(random.choice(pool))


def get_quotes_by_tradition(tradition: str, limit: int = 5) -> list[dict]:
    """Return up to `limit` quotes for a specific tradition.

    Args:
        tradition: One of "Stoic", "Buddhist", "Taoist", "Confucian",
                   "Sufi", "Greek", "Perennial", "Transcendentalist",
                   "Philosophy", "Chinese", "Indian".
        limit:     Max number of quotes to return (1-20).

    Returns:
        List of {"author", "text", "tradition"} dicts.
    """
    limit = max(1, min(20, limit))
    slugs = _TRADITION_AUTHORS.get(tradition, [])

    if slugs:
        results = _from_quotable_list(slugs, limit=limit)
        if results:
            return [{k: v for k, v in r.items() if not k.startswith("_")} for r in results]

    # Fallback to static quotes for this tradition
    pool = [s for s in _STATIC_QUOTES if s["tradition"] == tradition]
    if not pool:
        pool = _STATIC_QUOTES
    random.shuffle(pool)
    return [dict(q) for q in pool[:limit]]


def list_traditions() -> list[str]:
    """Return all supported tradition labels."""
    return sorted(set(_AUTHOR_TRADITION.values()))
