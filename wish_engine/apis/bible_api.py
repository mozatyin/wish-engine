"""Bible verses. Free, no key."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def get_verse(reference: str = "John 3:16") -> dict | None:
    url = f"https://bible-api.com/{reference.replace(' ', '+')}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return {"reference": data.get("reference", ""), "text": data.get("text", "").strip(), "verses": data.get("verse_count", 0)}
    except: return None

def random_verse() -> dict | None:
    import random
    popular = ["Psalm 23:1-6", "Philippians 4:13", "Romans 8:28", "Jeremiah 29:11", "Isaiah 41:10", "Proverbs 3:5-6", "Matthew 11:28-30", "John 14:27", "Psalm 46:1", "2 Timothy 1:7"]
    return get_verse(random.choice(popular))

def is_available() -> bool: return True
