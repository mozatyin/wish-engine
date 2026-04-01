"""Jobs API — real-time job listings from RemoteOK and Arbeitnow.

Zero auth required. Returns live job postings for job seekers.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError


def remoteok_jobs(
    keywords: list[str] | None = None,
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """Fetch live remote jobs from RemoteOK (no auth).

    Returns list of dicts with: title, company, tags, url, salary, date.
    """
    url = "https://remoteok.com/api"
    try:
        req = Request(url, headers={"User-Agent": "wish-engine/1.0 (life-needs matcher)"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        # First element is a legal disclaimer dict, skip it
        jobs = [j for j in data if isinstance(j, dict) and j.get("position")]

        # Filter by keywords if provided
        if keywords:
            kw_lower = [k.lower() for k in keywords]
            filtered = []
            for j in jobs:
                text = f"{j.get('position','')} {' '.join(j.get('tags', []))}".lower()
                if any(k in text for k in kw_lower):
                    filtered.append(j)
            jobs = filtered if filtered else jobs  # fallback to all if no match

        results = []
        for j in jobs[:max_results]:
            results.append({
                "title": j.get("position", "Remote Job"),
                "company": j.get("company", ""),
                "tags": j.get("tags", []),
                "url": j.get("url", ""),
                "salary": j.get("salary", ""),
                "location": "Remote",
                "date": j.get("date", ""),
            })
        return results

    except (URLError, json.JSONDecodeError, OSError, TimeoutError, KeyError):
        return []


def arbeitnow_jobs(
    keywords: str = "",
    location: str = "",
    visa_sponsorship: bool = False,
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """Fetch live jobs from Arbeitnow (no auth, EU + remote focused).

    Args:
        keywords: Search keywords
        location: City or country filter
        visa_sponsorship: Filter for visa-sponsoring jobs
        max_results: Max results

    Returns list of dicts with: title, company, location, url, tags, remote, visa.
    """
    from urllib.parse import urlencode

    params: dict[str, Any] = {"page": 1}
    if keywords:
        params["search"] = keywords
    if location:
        params["location"] = location
    if visa_sponsorship:
        params["visa_sponsorship"] = "true"

    url = f"https://www.arbeitnow.com/api/job-board-api?{urlencode(params)}"
    try:
        req = Request(url, headers={"Accept": "application/json", "User-Agent": "wish-engine/1.0"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        jobs = data.get("data", [])
        results = []
        for j in jobs[:max_results]:
            results.append({
                "title": j.get("title", "Job Opening"),
                "company": j.get("company_name", ""),
                "location": j.get("location", ""),
                "url": j.get("url", ""),
                "tags": j.get("tags", []),
                "remote": j.get("remote", False),
                "visa": j.get("visa_sponsorship", False),
                "date": j.get("created_at", ""),
            })
        return results

    except (URLError, json.JSONDecodeError, OSError, TimeoutError, KeyError):
        return []


def search_jobs(
    keywords: list[str] | None = None,
    location: str = "",
    max_results: int = 5,
) -> dict[str, Any]:
    """Search both RemoteOK and Arbeitnow, return best combined results.

    Returns a dict with: title, company, location, url, tags, source.
    Falls back gracefully if either API fails.
    """
    kw_str = " ".join(keywords) if keywords else ""

    remote = remoteok_jobs(keywords=keywords, max_results=max_results)
    local = arbeitnow_jobs(keywords=kw_str, location=location, max_results=max_results)

    # Merge and deduplicate by title+company
    seen = set()
    combined = []
    for j in remote + local:
        key = (j.get("title", "").lower(), j.get("company", "").lower())
        if key not in seen:
            seen.add(key)
            combined.append(j)

    if not combined:
        return {}

    best = combined[0]
    return {
        "title": best.get("title", ""),
        "company": best.get("company", ""),
        "location": best.get("location") or "Remote",
        "url": best.get("url", ""),
        "tags": best.get("tags", []),
        "result": f"{best.get('title','')} at {best.get('company','')} — {best.get('location') or 'Remote'}",
    }
