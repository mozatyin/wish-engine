"""IP geolocation. Free, no key, 45 req/min. ip-api.com"""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def get_location_from_ip(ip: str = "") -> dict | None:
    url = f"http://ip-api.com/json/{ip}" if ip else "http://ip-api.com/json/"
    try:
        req = Request(url)
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get("status") == "success":
                return {"city": data.get("city", ""), "country": data.get("country", ""), "country_code": data.get("countryCode", ""), "lat": data.get("lat"), "lng": data.get("lon"), "timezone": data.get("timezone", ""), "isp": data.get("isp", "")}
    except: pass
    return None

def is_available() -> bool: return True
