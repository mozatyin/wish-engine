"""Adzuna Job Search API.

Requires ADZUNA_APP_ID and ADZUNA_API_KEY env vars.
Free tier: 250 req/day.
Docs: https://api.adzuna.com/v1/api/jobs/{country}/search/1
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def is_available() -> bool:
    """Returns True if both ADZUNA_APP_ID and ADZUNA_API_KEY are set."""
    return bool(os.environ.get("ADZUNA_APP_ID") and os.environ.get("ADZUNA_API_KEY"))


def search_jobs(
    query: str = "software",
    location: str = "",
    country: str = "gb",
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """Search jobs via Adzuna. Returns [] when keys not set or API fails."""
    app_id = os.environ.get("ADZUNA_APP_ID", "")
    api_key = os.environ.get("ADZUNA_API_KEY", "")
    if not app_id or not api_key:
        return []

    params: dict[str, Any] = {
        "app_id": app_id,
        "app_key": api_key,
        "what": query,
        "results_per_page": min(max_results, 50),
    }
    if location:
        params["where"] = location

    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1?{urlencode(params)}"
    try:
        req = Request(url, headers={"Accept": "application/json", "User-Agent": "wish-engine/1.0"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        results = []
        for job in data.get("results", [])[:max_results]:
            results.append({
                "title": job.get("title", ""),
                "company": job.get("company", {}).get("display_name", ""),
                "location": job.get("location", {}).get("display_name", ""),
                "url": job.get("redirect_url", ""),
                "salary": _format_salary(job),
                "description": job.get("description", "")[:200],
            })
        return results
    except (URLError, json.JSONDecodeError, OSError, KeyError, TypeError):
        return []


def search_visa_jobs(
    location: str = "",
    country: str = "gb",
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """Search for jobs with visa sponsorship on Adzuna."""
    return search_jobs(
        query="visa sponsorship",
        location=location,
        country=country,
        max_results=max_results,
    )


def _format_salary(job: dict) -> str:
    """Format salary range from Adzuna job dict."""
    min_sal = job.get("salary_min")
    max_sal = job.get("salary_max")
    if min_sal and max_sal:
        return f"{int(min_sal):,}–{int(max_sal):,}"
    if min_sal:
        return f"{int(min_sal):,}+"
    return ""
