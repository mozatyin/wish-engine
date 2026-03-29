"""Datamuse API — word associations and related words. Free, no key."""
from __future__ import annotations
import json
from typing import Any
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError

def related_words(word: str, max_results: int = 10) -> list[str]:
    """Find words triggered by / associated with the input word."""
    url = f"https://api.datamuse.com/words?rel_trg={word}&max={max_results}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        return [d["word"] for d in data if "word" in d]
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return []

def similar_meaning(word: str, max_results: int = 10) -> list[str]:
    """Find words with similar meaning (synonyms)."""
    url = f"https://api.datamuse.com/words?ml={word}&max={max_results}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        return [d["word"] for d in data if "word" in d]
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return []

def is_available() -> bool:
    return True
