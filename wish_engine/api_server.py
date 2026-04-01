"""
wish_engine.api_server
~~~~~~~~~~~~~~~~~~~~~~
Minimal FastAPI HTTP service exposing the executor as a REST API.

Start:
    uvicorn wish_engine.api_server:app --reload --port 8000

Endpoints:
    POST /recommend          — signal + location → results
    POST /pipeline           — utterances + location → signals + results
    GET  /signals            — list all known signals
    GET  /health             — liveness check
"""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from wish_engine.executor import execute, execute_pipeline
from wish_engine.soul_api_bridge import SOUL_API_MAP

app = FastAPI(
    title="Wish Engine",
    description="Surface-layer wish detection and API recommendation service.",
    version="1.0.0",
)


# ── request / response models ─────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    signal: str = Field(..., examples=["sad"], description="Attention signal key")
    lat: Optional[float] = Field(None, examples=[25.2048], description="User latitude")
    lng: Optional[float] = Field(None, examples=[55.2708], description="User longitude")
    limit: int = Field(3, ge=1, le=10, description="Max results to return")
    cat: Optional[str] = Field(None, examples=["healing"], description="Category filter")


class RecommendResult(BaseModel):
    api:      str
    fn:       str
    cat:      str
    star:     str
    rendered: str
    raw:      object


class RecommendResponse(BaseModel):
    signal:  str
    results: list[RecommendResult]


class PipelineRequest(BaseModel):
    utterances:       list[str] = Field(..., min_length=1, examples=[["I feel lonely and bored"]])
    lat:              Optional[float] = None
    lng:              Optional[float] = None
    limit_per_signal: int = Field(2, ge=1, le=10)
    max_signals:      int = Field(3, ge=1, le=10)


class PipelineResponse(BaseModel):
    signals: list[str]
    results: dict[str, list[RecommendResult]]


# ── endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "signals": len(SOUL_API_MAP)}


@app.get("/signals")
def list_signals():
    return {
        "count": len(SOUL_API_MAP),
        "signals": sorted(SOUL_API_MAP.keys()),
    }


@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    if req.signal not in SOUL_API_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown signal: {req.signal!r}")

    results = execute(
        signal=req.signal,
        user_lat=req.lat,
        user_lng=req.lng,
        limit=req.limit,
        cat=req.cat,
    )
    return RecommendResponse(signal=req.signal, results=results)


@app.post("/pipeline", response_model=PipelineResponse)
def pipeline(req: PipelineRequest):
    out = execute_pipeline(
        utterances=req.utterances,
        user_lat=req.lat,
        user_lng=req.lng,
        limit_per_signal=req.limit_per_signal,
        max_signals=req.max_signals,
    )
    return PipelineResponse(
        signals=out["signals"],
        results=out["results"],
    )
