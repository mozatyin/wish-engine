"""Free dictionary. No key. dictionaryapi.dev"""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def define(word: str) -> dict | None:
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data and isinstance(data, list):
                entry = data[0]
                meanings = entry.get("meanings", [])
                defs = []
                for m in meanings[:3]:
                    for d in m.get("definitions", [])[:2]:
                        defs.append({"partOfSpeech": m.get("partOfSpeech", ""), "definition": d.get("definition", ""), "example": d.get("example", "")})
                return {"word": entry.get("word", ""), "phonetic": entry.get("phonetic", ""), "definitions": defs}
    except: pass
    return None

def is_available() -> bool: return True
