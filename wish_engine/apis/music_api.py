"""Spotify API client — playlist search and track recommendations.

Requires SPOTIFY_CLIENT_ID + SPOTIFY_CLIENT_SECRET environment variables.
Falls back gracefully when credentials are not available.
Zero LLM.
"""

from __future__ import annotations

import base64
import json
import os
from typing import Any
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError


SPOTIFY_CLIENT_ID_ENV = "SPOTIFY_CLIENT_ID"
SPOTIFY_CLIENT_SECRET_ENV = "SPOTIFY_CLIENT_SECRET"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"
SPOTIFY_RECOMMENDATIONS_URL = "https://api.spotify.com/v1/recommendations"


def _get_credentials() -> tuple[str | None, str | None]:
    return (
        os.environ.get(SPOTIFY_CLIENT_ID_ENV),
        os.environ.get(SPOTIFY_CLIENT_SECRET_ENV),
    )


def is_available() -> bool:
    """Check if Spotify API credentials are configured."""
    client_id, client_secret = _get_credentials()
    return client_id is not None and client_secret is not None


def _get_access_token() -> str | None:
    """Get Spotify access token via client credentials flow."""
    client_id, client_secret = _get_credentials()
    if not client_id or not client_secret:
        return None

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = urlencode({"grant_type": "client_credentials"}).encode()

    try:
        req = Request(
            SPOTIFY_TOKEN_URL,
            data=data,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        with urlopen(req, timeout=10) as resp:
            token_data = json.loads(resp.read().decode())
        return token_data.get("access_token")
    except (URLError, json.JSONDecodeError, OSError):
        return None


def search_playlists(
    mood: str,
    genre: str | None = None,
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """Search Spotify for playlists matching a mood/genre.

    Args:
        mood: Mood keyword (e.g. "calming", "upbeat", "intense")
        genre: Optional genre filter (e.g. "acoustic", "rock")
        max_results: Max playlists to return

    Returns:
        List of playlist dicts with: name, description, url, image_url, tracks_total
    """
    token = _get_access_token()
    if not token:
        return []

    query = f"{mood} {genre}" if genre else mood
    params = {
        "q": query,
        "type": "playlist",
        "limit": max_results,
    }
    url = f"{SPOTIFY_SEARCH_URL}?{urlencode(params)}"

    try:
        req = Request(url, headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        })
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        playlists = data.get("playlists", {}).get("items", [])
        return [
            {
                "name": p.get("name", ""),
                "description": (p.get("description") or "")[:200],
                "url": (p.get("external_urls") or {}).get("spotify", ""),
                "image_url": p["images"][0]["url"] if p.get("images") else "",
                "tracks_total": (p.get("tracks") or {}).get("total", 0),
            }
            for p in playlists
            if p is not None
        ]
    except (URLError, json.JSONDecodeError, OSError, IndexError, KeyError):
        return []


def get_recommendations(
    seed_genres: list[str],
    target_valence: float = 0.5,
    target_energy: float = 0.5,
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """Get Spotify track recommendations based on audio features.

    Args:
        seed_genres: Up to 5 genre seeds (e.g. ["acoustic", "ambient"])
        target_valence: 0.0 (sad) to 1.0 (happy)
        target_energy: 0.0 (calm) to 1.0 (energetic)
        max_results: Max tracks to return

    Returns:
        List of track dicts with: name, artist, album, url, duration_ms
    """
    token = _get_access_token()
    if not token:
        return []

    params: dict[str, Any] = {
        "seed_genres": ",".join(seed_genres[:5]),
        "target_valence": target_valence,
        "target_energy": target_energy,
        "limit": max_results,
    }
    url = f"{SPOTIFY_RECOMMENDATIONS_URL}?{urlencode(params)}"

    try:
        req = Request(url, headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        })
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        tracks = data.get("tracks", [])
        return [
            {
                "name": t.get("name", ""),
                "artist": t["artists"][0]["name"] if t.get("artists") else "",
                "album": (t.get("album") or {}).get("name", ""),
                "url": (t.get("external_urls") or {}).get("spotify", ""),
                "duration_ms": t.get("duration_ms", 0),
            }
            for t in tracks
        ]
    except (URLError, json.JSONDecodeError, OSError, IndexError, KeyError):
        return []
