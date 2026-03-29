"""Collection of micro APIs — single-function, free, no key."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def kanye_quote() -> str:
    try:
        with urlopen(Request("https://api.kanye.rest/"), timeout=3) as r:
            return json.loads(r.read().decode()).get("quote", "")
    except: return ""

def chuck_norris_joke() -> str:
    try:
        with urlopen(Request("https://api.chucknorris.io/jokes/random", headers={"Accept": "application/json"}), timeout=3) as r:
            return json.loads(r.read().decode()).get("value", "")
    except: return ""

def random_trivia() -> dict | None:
    try:
        with urlopen(Request("https://opentdb.com/api.php?amount=1"), timeout=5) as r:
            data = json.loads(r.read().decode())
            results = data.get("results", [])
            if results:
                q = results[0]
                return {"question": q.get("question", ""), "answer": q.get("correct_answer", ""), "category": q.get("category", "")}
    except: pass
    return None

def spacex_latest_launch() -> dict | None:
    try:
        with urlopen(Request("https://api.spacexdata.com/v4/launches/latest", headers={"Accept": "application/json"}), timeout=5) as r:
            data = json.loads(r.read().decode())
            return {"name": data.get("name", ""), "date": data.get("date_utc", ""), "success": data.get("success"), "details": (data.get("details") or "")[:200]}
    except: return None

def zen_quote() -> str:
    try:
        with urlopen(Request("https://zenquotes.io/api/random"), timeout=3) as r:
            data = json.loads(r.read().decode())
            if data: return f"{data[0].get('q', '')} — {data[0].get('a', '')}"
    except: pass
    return ""

def my_public_ip() -> str:
    try:
        with urlopen(Request("https://api.ipify.org?format=json"), timeout=3) as r:
            return json.loads(r.read().decode()).get("ip", "")
    except: return ""

def placeholder_image(width: int = 200, height: int = 200) -> str:
    return f"https://picsum.photos/{width}/{height}"

def estimate_age(name: str) -> int:
    try:
        with urlopen(Request(f"https://api.agify.io?name={name}"), timeout=3) as r:
            return json.loads(r.read().decode()).get("age", 0)
    except: return 0

def http_cat(status_code: int) -> str:
    return f"https://http.cat/{status_code}"

def is_available() -> bool: return True
