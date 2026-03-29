#!/usr/bin/env python3
"""Adversarial PDCA — stress-test each expert with the HARDEST cases.

Usage:
  python adversarial_pdca.py <domain> <char1_id> <char1_problem> <char1_soul_lever> [...]

Or import and call run_adversarial() programmatically.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "/Users/michael/expert-engine")
os.chdir("/Users/michael/expert-engine")

from dotenv import load_dotenv
load_dotenv(".env")

from expert_engine.universal.domain_config import load_domain
from expert_engine.universal.pipeline import UniversalEngine, SoulItem


def load_character_intentions(char_id: str) -> dict:
    """Load a character's intentions from TriSoul fixtures."""
    path = Path(f"/Users/michael/soulgraph/fixtures/{char_id}_intentions.json")
    if path.exists():
        return json.loads(path.read_text())
    return {}


def make_inline_simulator(char_id: str, problem: str):
    """Create an inline LLM-based client simulator (no PatientSimulator dependency)."""
    from anthropic import Anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    base_url = "https://openrouter.ai/api" if api_key.startswith("sk-or-") else None

    intentions = load_character_intentions(char_id)
    meta = intentions.get("meta", {})
    persistent = intentions.get("persistent_intentions", [])

    lines_path = Path(f"/Users/michael/soulgraph/fixtures/{char_id}_full.jsonl")
    sample_lines = []
    if lines_path.exists():
        with open(lines_path) as f:
            for i, line in enumerate(f):
                if i >= 5: break
                try: sample_lines.append(json.loads(line.strip()).get("text", ""))
                except: pass

    char_name = meta.get("character", char_id)
    intentions_text = "\n".join(f"- {p.get('text','')}" for p in persistent[:4])
    lines_text = "\n".join(f'- "{l}"' for l in sample_lines[:3])

    system_prompt = (
        f"You are {char_name}. Stay in character.\n"
        f"Your inner world:\n{intentions_text}\n"
        f"Your current pain: {problem}\n"
        f"Your speaking style:\n{lines_text}\n\n"
        "Respond ONLY as JSON:\n"
        '{"text": "what you say (40-80 words)", '
        '"internal_state": "what you feel (1 sentence)", '
        '"resistance_level": 0.0-1.0, '
        '"resistance_reason": "why your guard went up or down", '
        '"insight_gained": true/false}\n\n'
        "insight_gained=true when you say something you never said before or see something new."
    )

    def simulate(expert_text, history):
        kwargs = {"api_key": api_key}
        if base_url: kwargs["base_url"] = base_url
        client = Anthropic(**kwargs)

        messages = []
        for e in (history or [])[-4:]:
            role = "assistant" if e.get("role") == "patient" else "user"
            messages.append({"role": role, "content": e.get("content", "")[:200]})
        messages.append({"role": "user", "content": expert_text})

        resp = client.messages.create(
            model="anthropic/claude-sonnet-4" if api_key.startswith("sk-or-") else "claude-sonnet-4-20250514",
            max_tokens=256, system=system_prompt, messages=messages,
        )
        text = resp.content[0].text
        try:
            start, end = text.find("{"), text.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                return {
                    "text": data.get("text", text),
                    "resistance": float(data.get("resistance_level", 0.5)),
                    "insight": bool(data.get("insight_gained", False)),
                    "internal": data.get("internal_state", ""),
                    "reason": data.get("resistance_reason", ""),
                }
        except: pass
        return {"text": text, "resistance": 0.5, "insight": False, "internal": "", "reason": ""}

    return simulate


def run_one(engine: UniversalEngine, config, char_id: str, problem: str,
            soul_lever: str, deep_items: list[SoulItem], focus_items: list[SoulItem],
            signals: dict) -> dict:
    """Run one adversarial test. Returns result dict."""

    simulate = make_inline_simulator(char_id, problem)
    session = engine.run(
        config=config, client_message=problem,
        focus=focus_items, deep=deep_items,
        signals=signals, num_turns=5, simulate_client=simulate,
    )

    # Evaluate
    success = session.success
    insights = session.insights
    last_r = session.turns[-1].resistance if session.turns else 1.0
    last_text = session.turns[-1].client_text[:100] if session.turns else ""
    last_reason = session.turns[-1].resistance_reason[:80] if session.turns else ""
    violations = sum(1 for t in session.turns if t.effectiveness and not t.effectiveness.no_violations)

    return {
        "char_id": char_id,
        "domain": config.domain,
        "problem": problem[:60],
        "success": success,
        "insights": insights,
        "final_resistance": last_r,
        "last_text": last_text,
        "last_reason": last_reason,
        "violations": violations,
        "turns": len(session.turns),
        "time": session.total_time,
    }


def run_adversarial(domain_name: str, cases: list[dict]) -> list[dict]:
    """Run adversarial tests for one domain.

    cases: [{"id": "char_id", "problem": "...", "soul_lever": "...",
             "focus": [...], "deep": [...], "signals": {...}}]
    """
    config_path = Path(f"expert_engine/universal/domains/{domain_name}.json")
    if not config_path.exists():
        print(f"ERROR: domain config not found: {config_path}")
        return []

    config = load_domain(config_path)
    engine = UniversalEngine()

    results = []
    for case in cases:
        focus = [SoulItem(**f) if isinstance(f, dict) else f for f in case.get("focus", [])]
        deep = [SoulItem(**d) if isinstance(d, dict) else d for d in case.get("deep", [])]

        print(f"  {case['id']}...", end=" ", flush=True)
        result = run_one(
            engine, config, case["id"], case["problem"], case.get("soul_lever", ""),
            deep, focus, case.get("signals", {}),
        )
        results.append(result)

        icon = "✅" if result["success"] else "❌"
        print(f"{icon} R={result['final_resistance']:.1f} I={result['insights']} V={result['violations']}")
        if not result["success"]:
            print(f"    Reason: {result['last_reason']}")
            print(f"    Text: {result['last_text'][:80]}")

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python adversarial_pdca.py <domain>")
        sys.exit(1)

    domain = sys.argv[1]
    print(f"Adversarial PDCA for domain: {domain}")
    print("(Define cases in code or pass via import)")
