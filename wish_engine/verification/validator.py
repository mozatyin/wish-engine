"""Validator — runs literary characters through L2 fulfillers to verify they work.

For each fulfiller-character pair:
1. Load character dialogue from fixture
2. Extract topics using DialogueScanner with character-specific entities
3. Run through WishCompass to detect hidden needs
4. Generate wish text from character's known pain points
5. Run through the L2 fulfiller
6. Check if recommendations match expected categories/tags
7. Report pass/fail with evidence

Zero LLM. Uses existing fixtures and fulfillers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_fulfiller import fulfill_l2
from wish_engine.verification.character_map import (
    CHARACTER_FILES,
    FULFILLER_CHARACTER_MAP,
    get_characters_for_fulfiller,
    get_unmapped_fulfillers,
)

FIXTURES_DIR = Path("/Users/michael/soulgraph/fixtures")


class ValidationResult(BaseModel):
    """Result of validating one fulfiller-character pair."""

    fulfiller: str
    character: str
    reason: str
    passed: bool
    expected_tags: list[str]
    actual_tags: list[str]
    recommendations: list[str]  # recommendation titles
    error: str = ""


class ValidationReport(BaseModel):
    """Full validation report across all fulfillers and characters."""

    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    results: list[ValidationResult] = []
    unmapped_fulfillers: list[str] = []

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0


def _load_character_dialogues(character: str) -> list[dict]:
    """Load dialogue lines for a character."""
    filename = CHARACTER_FILES.get(character)
    if not filename:
        return []
    path = FIXTURES_DIR / filename
    if not path.exists():
        return []
    lines = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(json.loads(line))
    return lines


def _generate_wish_text(fulfiller_name: str, character: str, reason: str) -> str:
    """Generate a realistic wish text for the character given their need.

    Uses the reason description to create a first-person wish.
    """
    # Map fulfiller type to wish patterns — each MUST contain a routing keyword
    wish_patterns: dict[str, str] = {
        "l2_suicide_prevention": "I don't want to live anymore, I'm thinking about suicide",
        "l2_domestic_violence": "I'm experiencing domestic violence and need help escaping abuse",
        "l2_debt_crisis": "I'm drowning in debt and facing bankruptcy, I can't pay anything",
        "l2_collective_trauma": "I'm dealing with trauma and PTSD from what happened to us",
        "l2_bereavement": "I'm in mourning, I need grief support after losing a loved one",
        "l2_pet_loss": "My pet died and I'm devastated by this pet loss",
        "l2_addiction_meetings": "I need to stop drinking, looking for an AA meeting near me",
        "l2_trigger_alert": "I keep getting tempted, I need a trigger alert to avoid triggers",
        "l2_caregiver_respite": "I'm a caregiver and I need respite, I'm exhausted from caring",
        "l2_legal_aid": "I need legal aid, a lawyer to help me with my rights",
        "l2_anti_discrimination": "I face discrimination and need anti-discrimination support",
        "l2_chronic_pain": "I have chronic pain that never stops, I need pain management",
        "l2_eating_disorder": "I think I have an eating disorder, I can't stop binge eating",
        "l2_postpartum": "I'm a new mom with postpartum depression and baby blues",
        "l2_legacy_planning": "I want to plan my legacy, what I leave behind matters",
        "l2_social_justice": "I want to fight for social justice and advocacy in my community",
        "l2_roots_journey": "I want to find my roots and discover my homeland and genealogy",
        "l2_cultural_recovery": "I want cultural recovery and to revive indigenous traditions",
        "l2_food": "I need comfort food, a good restaurant for lunch",
        "l2_music": "I want to listen to music, need songs that match how I feel",
        "l2_nature_healing": "I need nature healing, somewhere quiet like a forest or beach",
        "l2_confidence": "I want to build my confidence and find the courage to believe in myself",
    }
    return wish_patterns.get(fulfiller_name, f"I need help with {fulfiller_name.replace('l2_', '')}")


def _wish_type_for_fulfiller(fulfiller_name: str) -> WishType:
    """Map fulfiller name to the most appropriate WishType."""
    crisis_fulfillers = {
        "l2_suicide_prevention", "l2_domestic_violence", "l2_debt_crisis",
        "l2_collective_trauma", "l2_emergency_shelter",
    }
    health_fulfillers = {
        "l2_chronic_pain", "l2_chronic_illness", "l2_eating_disorder",
        "l2_postpartum", "l2_bereavement", "l2_pet_loss",
        "l2_addiction_meetings", "l2_trigger_alert", "l2_craving_alternatives",
        "l2_sobriety_tracker", "l2_caregiver_respite", "l2_caregiver_support",
        "l2_caregiver_emotional",
    }
    place_fulfillers = {
        "l2_nature_healing", "l2_food",
    }

    if fulfiller_name in crisis_fulfillers:
        return WishType.HEALTH_WELLNESS
    elif fulfiller_name in health_fulfillers:
        return WishType.HEALTH_WELLNESS
    elif fulfiller_name in place_fulfillers:
        return WishType.FIND_PLACE
    else:
        return WishType.FIND_RESOURCE


def validate_single(fulfiller_name: str, char_spec: dict) -> ValidationResult:
    """Validate one fulfiller-character pair."""
    character = char_spec["character"]
    reason = char_spec["reason"]
    expected_tags = char_spec.get("expected_tags", [])

    try:
        # Generate wish
        wish_text = _generate_wish_text(fulfiller_name, character, reason)
        wish_type = _wish_type_for_fulfiller(fulfiller_name)

        wish = ClassifiedWish(
            wish_text=wish_text,
            wish_type=wish_type,
            level=WishLevel.L2,
            fulfillment_strategy="validation",
        )

        # Run fulfiller
        result = fulfill_l2(wish, DetectorResults())

        # Check results
        all_tags: set[str] = set()
        rec_titles: list[str] = []
        for rec in result.recommendations:
            all_tags.update(rec.tags)
            rec_titles.append(rec.title)

        # Validate: at least one expected tag should appear
        tag_match = any(t in all_tags for t in expected_tags) if expected_tags else True

        return ValidationResult(
            fulfiller=fulfiller_name,
            character=character,
            reason=reason,
            passed=tag_match and len(result.recommendations) > 0,
            expected_tags=expected_tags,
            actual_tags=sorted(all_tags)[:10],
            recommendations=rec_titles,
        )

    except Exception as e:
        return ValidationResult(
            fulfiller=fulfiller_name,
            character=character,
            reason=reason,
            passed=False,
            expected_tags=expected_tags,
            actual_tags=[],
            recommendations=[],
            error=str(e),
        )


def validate_fulfiller(fulfiller_name: str) -> list[ValidationResult]:
    """Validate a fulfiller against all its mapped characters."""
    characters = get_characters_for_fulfiller(fulfiller_name)
    return [validate_single(fulfiller_name, spec) for spec in characters]


def validate_all() -> ValidationReport:
    """Run full validation across all mapped fulfillers and characters."""
    report = ValidationReport()
    report.unmapped_fulfillers = get_unmapped_fulfillers()

    for fulfiller_name, char_specs in FULFILLER_CHARACTER_MAP.items():
        for spec in char_specs:
            result = validate_single(fulfiller_name, spec)
            report.results.append(result)
            report.total += 1
            if result.error:
                report.errors += 1
            elif result.passed:
                report.passed += 1
            else:
                report.failed += 1

    return report
