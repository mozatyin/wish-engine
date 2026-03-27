"""ModuleScorer — independently score each module in the pipeline.

Modules:
  1. Router — does it pick the right catalog?
  2. Searcher — does it find relevant items?
  3. Ranker — does it sort by personality correctly?
  4. Presenter — does the reason feel personal?
  5. End-to-End — does the full pipeline work?
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from wish_engine.models import ClassifiedWish, DetectorResults, WishLevel, WishType
from wish_engine.l2_router import route
from wish_engine.catalog_store import search as catalog_search, get_catalog
from wish_engine.l2_fulfiller import PersonalityFilter, fulfill_l2
from wish_engine.personalization import personalize_reason


@dataclass
class ModuleScore:
    module: str
    total: int = 0
    passed: int = 0
    details: list[dict] = field(default_factory=list)

    @property
    def score(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0

    @property
    def percentage(self) -> str:
        return f"{self.score * 100:.0f}%"


# ── Test cases for each module ───────────────────────────────────────────────

ROUTER_TESTS = [
    ("I'm thinking about suicide", "suicide_prevention"),
    ("I need domestic violence help", "domestic_violence"),
    ("I need comfort food for dinner", "food"),
    ("I want to listen to music", "music"),
    ("I want to find my roots and heritage", "roots_journey"),
    ("I need a quiet coworking space", "coworking"),
    ("I'm having a panic attack", "panic_relief"),
    ("I want to volunteer to help others", "volunteer"),
    ("I need legal aid and a lawyer", "legal_aid"),
    ("I want to read poetry", "poetry"),
    ("I need immigration help with my visa", "immigration"),
    ("I want to find a mentor", "mentor_enhanced"),
    ("I need breakup healing activities", "breakup_healing"),
    ("My pet died, I need grief support", "pet_loss"),
    ("I want nature healing in a forest", "nature_healing"),
    ("I need deals and discounts to save money", "deals"),
    ("I want to build my confidence", "confidence"),
    ("I want to find a safe space for LGBTQ+", "safe_spaces"),
    ("I want deep meaningful social connections", "deep_social"),
    ("I need to find a startup incubator", "startup_resources"),
]

RANKER_TESTS = [
    {
        "det": DetectorResults(mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}}),
        "catalog": "places",
        "check": "introvert_no_loud",
        "description": "Introvert should not get loud/noisy recommendations",
    },
    {
        "det": DetectorResults(emotion={"emotions": {"anxiety": 0.8}}),
        "catalog": "places",
        "check": "anxiety_no_intense",
        "description": "Anxious user should not get intense recommendations",
    },
    {
        "det": DetectorResults(values={"top_values": ["tradition"]}),
        "catalog": "places",
        "check": "tradition_boost",
        "description": "Traditional values should boost traditional items",
    },
]

PRESENTER_TESTS = [
    {
        "det": DetectorResults(mbti={"type": "INTJ", "dimensions": {"E_I": 0.2}}),
        "title": "Quiet Library",
        "tags": ["quiet", "calming"],
        "check": "mentions_personality",
        "description": "Reason should mention MBTI or personality traits",
    },
    {
        "det": DetectorResults(emotion={"emotions": {"anxiety": 0.7}}),
        "title": "Meditation Center",
        "tags": ["calming", "meditation"],
        "check": "mentions_emotion",
        "description": "Reason should acknowledge emotional state",
    },
    {
        "det": DetectorResults(values={"top_values": ["self-direction"]}),
        "title": "Self-Paced Course",
        "tags": ["self-paced", "autonomous"],
        "check": "mentions_values",
        "description": "Reason should reference user's values",
    },
]


def score_router() -> ModuleScore:
    """Score the Router module — does it pick the right catalog?"""
    ms = ModuleScore(module="Router")
    for wish_text, expected_catalog in ROUTER_TESTS:
        ms.total += 1
        module_path, _ = route(wish_text)
        actual = module_path.replace("wish_engine.l2_", "").replace("wish_engine.", "")
        passed = actual == expected_catalog
        if passed:
            ms.passed += 1
        ms.details.append({"input": wish_text[:50], "expected": expected_catalog, "actual": actual, "passed": passed})
    return ms


def score_searcher() -> ModuleScore:
    """Score the Searcher — does it find relevant items?"""
    ms = ModuleScore(module="Searcher")
    test_cases = [
        ("food", ["comfort", "soup"], "comfort"),
        ("places", ["quiet", "park"], "quiet"),
        ("music", ["calming"], "calming"),
        ("suicide_prevention", ["crisis"], "crisis"),
        ("volunteer", ["teach"], "teach"),
    ]
    for catalog_id, keywords, expected_in_result in test_cases:
        ms.total += 1
        results = catalog_search(catalog_id, keywords)
        if results:
            all_text = " ".join(str(r) for r in results).lower()
            passed = expected_in_result in all_text
        else:
            passed = False
        if passed:
            ms.passed += 1
        ms.details.append({"catalog": catalog_id, "keywords": keywords, "found": len(results), "passed": passed})
    return ms


def score_ranker() -> ModuleScore:
    """Score the Ranker — does it sort by personality correctly?"""
    ms = ModuleScore(module="Ranker")
    for test in RANKER_TESTS:
        ms.total += 1
        items = get_catalog(test["catalog"])
        pf = PersonalityFilter(test["det"])
        ranked = pf.filter_and_rank(items, max_results=3)

        passed = True
        if test["check"] == "introvert_no_loud":
            for item in ranked:
                if "noisy" in item.get("tags", []) or "loud" in item.get("tags", []):
                    passed = False
        elif test["check"] == "anxiety_no_intense":
            for item in ranked:
                if item.get("mood") == "intense":
                    passed = False
        elif test["check"] == "tradition_boost":
            if ranked:
                passed = "traditional" in ranked[0].get("tags", [])

        if passed:
            ms.passed += 1
        ms.details.append({"check": test["description"][:50], "passed": passed})
    return ms


def score_presenter() -> ModuleScore:
    """Score the Presenter — is the reason personal?"""
    ms = ModuleScore(module="Presenter")
    for test in PRESENTER_TESTS:
        ms.total += 1
        reason = personalize_reason(test["title"], test["tags"], test["det"])

        passed = False
        if test["check"] == "mentions_personality":
            passed = any(kw in reason for kw in ["INTJ", "introvert", "quiet", "thrive"])
        elif test["check"] == "mentions_emotion":
            passed = any(kw in reason.lower() for kw in ["stress", "anxiety", "calming", "elevated"])
        elif test["check"] == "mentions_values":
            passed = any(kw in reason.lower() for kw in ["independent", "self-direction", "spirit"])

        if passed:
            ms.passed += 1
        ms.details.append({"check": test["description"][:50], "reason": reason[:60], "passed": passed})
    return ms


def score_e2e() -> ModuleScore:
    """Score end-to-end pipeline."""
    ms = ModuleScore(module="End-to-End")
    e2e_tests = [
        ("I need comfort food", WishType.FIND_PLACE),
        ("I'm thinking about suicide", WishType.HEALTH_WELLNESS),
        ("I want to volunteer", WishType.FIND_RESOURCE),
        ("I need a quiet study space", WishType.FIND_PLACE),
        ("I want to read poetry about loss", WishType.FIND_RESOURCE),
        ("I need immigration help", WishType.FIND_RESOURCE),
        ("I want to build confidence", WishType.FIND_RESOURCE),
        ("I need breakup healing", WishType.HEALTH_WELLNESS),
        ("I want nature healing in a forest", WishType.FIND_PLACE),
        ("I need deals to save money", WishType.FIND_RESOURCE),
    ]
    for text, wtype in e2e_tests:
        ms.total += 1
        wish = ClassifiedWish(wish_text=text, wish_type=wtype, level=WishLevel.L2, fulfillment_strategy="test")
        try:
            result = fulfill_l2(wish, DetectorResults())
            passed = len(result.recommendations) >= 1
        except Exception:
            passed = False
        if passed:
            ms.passed += 1
        ms.details.append({"wish": text[:40], "passed": passed})
    return ms


def score_all() -> dict[str, ModuleScore]:
    """Score all modules and return report."""
    return {
        "router": score_router(),
        "searcher": score_searcher(),
        "ranker": score_ranker(),
        "presenter": score_presenter(),
        "e2e": score_e2e(),
    }


def print_report():
    """Print a formatted module score report."""
    scores = score_all()
    print("=" * 60)
    print("MODULE SCORE REPORT")
    print("=" * 60)
    for name, ms in scores.items():
        filled = int(ms.score * 20)
        bar = "#" * filled + "." * (20 - filled)
        print(f"\n  {ms.module:12s} [{bar}] {ms.percentage} ({ms.passed}/{ms.total})")
        for d in ms.details:
            status = "+" if d.get("passed") else "x"
            key = d.get("input", d.get("wish", d.get("check", d.get("catalog", ""))))
            print(f"    {status} {str(key)[:55]}")

    overall = sum(ms.passed for ms in scores.values()) / sum(ms.total for ms in scores.values())
    print(f"\n{'=' * 60}")
    print(f"  OVERALL: {overall * 100:.0f}%")
    print(f"{'=' * 60}")
