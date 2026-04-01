"""Teleport API — real-time city quality-of-life data.

Zero auth. Returns urban area scores (cost of living, safety, startups, culture, etc.)
Great for: new_place, need_housing, career_change, immigration_stress.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import quote


TELEPORT_BASE = "https://api.teleport.org/api"


def get_urban_area(city_name: str) -> dict[str, Any]:
    """Get quality-of-life scores for a city.

    Returns dict with: name, summary, scores (dict category→score), teleport_city_url.
    Falls back to {} on failure.
    """
    # Step 1: Search for the city slug
    search_url = f"{TELEPORT_BASE}/cities/?search={quote(city_name)}&embed=city:search-results/city:item/city:urban_area"
    try:
        req = Request(search_url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        results = (
            data.get("_embedded", {})
                .get("city:search-results", [])
        )
        if not results:
            return {}

        # Get urban_area link from first result
        first = results[0]
        ua_link = (
            first.get("_embedded", {})
                 .get("city:item", {})
                 .get("_links", {})
                 .get("city:urban_area", {})
                 .get("href", "")
        )
        if not ua_link:
            # City found but no urban area data
            city_name_resolved = first.get("matching_full_name", city_name)
            return {"name": city_name_resolved, "scores": {}, "summary": ""}

        # Step 2: Get urban area scores
        scores_url = ua_link.rstrip("/") + "/scores/"
        req2 = Request(scores_url, headers={"Accept": "application/json"})
        with urlopen(req2, timeout=10) as resp2:
            scores_data = json.loads(resp2.read().decode())

        # Extract categories
        scores = {}
        for cat in scores_data.get("categories", []):
            name = cat.get("name", "")
            score = cat.get("score_out_of_10")
            if name and score is not None:
                scores[name] = round(score, 1)

        summary = scores_data.get("summary", "").replace("<p>", "").replace("</p>", "").replace("<b>", "").replace("</b>", "").strip()
        # Trim summary to 200 chars
        if len(summary) > 200:
            summary = summary[:200] + "..."

        # Get city name from urban area
        ua_name = scores_data.get("_links", {}).get("ua:cities", {})
        if isinstance(ua_name, list) and ua_name:
            ua_name = ua_name[0].get("name", city_name)
        elif isinstance(ua_name, dict):
            ua_name = ua_name.get("name", city_name)
        else:
            ua_name = city_name

        # Pick top highlights
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        highlights = ", ".join(f"{k} {v}/10" for k, v in top)

        return {
            "name": str(ua_name),
            "summary": summary,
            "scores": scores,
            "highlights": highlights,
            "result": f"{ua_name}: {highlights}" if highlights else str(ua_name),
        }

    except (URLError, json.JSONDecodeError, OSError, TimeoutError, KeyError, TypeError):
        return {}


def get_city_salaries(city_name: str, job_title: str = "software-engineer") -> dict[str, Any]:
    """Get salary data for a job title in a city.

    Returns dict with: job, city, salary_percentile_25, salary_median, salary_percentile_75.
    """
    # First get urban area slug
    search_url = f"{TELEPORT_BASE}/cities/?search={quote(city_name)}&embed=city:search-results/city:item/city:urban_area"
    try:
        req = Request(search_url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        results = data.get("_embedded", {}).get("city:search-results", [])
        if not results:
            return {}

        ua_link = (
            results[0].get("_embedded", {})
                      .get("city:item", {})
                      .get("_links", {})
                      .get("city:urban_area", {})
                      .get("href", "")
        )
        if not ua_link:
            return {}

        # Get salaries
        slug = ua_link.rstrip("/").split("/")[-1]
        salaries_url = f"{TELEPORT_BASE}/urban_areas/slug:{slug}/salaries/"
        req2 = Request(salaries_url, headers={"Accept": "application/json"})
        with urlopen(req2, timeout=10) as resp2:
            sal_data = json.loads(resp2.read().decode())

        job_title_lower = job_title.lower().replace("-", " ")
        for entry in sal_data.get("salaries", []):
            if job_title_lower in entry.get("job", {}).get("title", "").lower():
                p = entry.get("salary_percentiles", {})
                return {
                    "job": entry["job"]["title"],
                    "city": city_name,
                    "salary_p25": p.get("percentile_25", 0),
                    "salary_median": p.get("percentile_50", 0),
                    "salary_p75": p.get("percentile_75", 0),
                    "result": f"{entry['job']['title']} in {city_name}: median ${p.get('percentile_50', 0):,.0f}/yr",
                }

        return {}

    except (URLError, json.JSONDecodeError, OSError, TimeoutError, KeyError, TypeError):
        return {}
