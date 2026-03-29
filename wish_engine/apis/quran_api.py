"""Quran text, translations, audio. Free, no key."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def get_ayah(reference: str = "random", edition: str = "en.asad") -> dict | None:
    """Get a Quran ayah. reference: 'random', '2:255' (Al-Baqarah 255), etc."""
    if reference == "random":
        import random
        surah = random.randint(1, 114)
        url = f"https://api.alquran.cloud/v1/surah/{surah}/{edition}"
    else:
        url = f"https://api.alquran.cloud/v1/ayah/{reference}/{edition}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            d = data.get("data", {})
            if isinstance(d, dict) and "ayahs" in d:
                ayah = d["ayahs"][0] if d["ayahs"] else {}
                return {"text": ayah.get("text", ""), "surah": d.get("englishName", ""), "number": ayah.get("numberInSurah", 0)}
            elif isinstance(d, dict):
                return {"text": d.get("text", ""), "surah": d.get("surah", {}).get("englishName", ""), "number": d.get("numberInSurah", 0)}
    except: pass
    return None

def is_available() -> bool: return True
