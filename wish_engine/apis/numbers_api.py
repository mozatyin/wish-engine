"""Fun number facts. Free, no key. numbersapi.com"""
from __future__ import annotations
from urllib.request import urlopen, Request
from urllib.error import URLError

def get_fact(number: int = 0, fact_type: str = "trivia") -> str:
    """fact_type: trivia, math, date, year"""
    url = f"http://numbersapi.com/{number}/{fact_type}"
    try:
        req = Request(url)
        with urlopen(req, timeout=5) as resp:
            return resp.read().decode().strip()
    except: return ""

def random_fact() -> str:
    try:
        req = Request("http://numbersapi.com/random/trivia")
        with urlopen(req, timeout=5) as resp:
            return resp.read().decode().strip()
    except: return ""

def is_available() -> bool: return True
