"""Tests for the verification framework — validates the validation system itself."""

from __future__ import annotations

import pytest
from wish_engine.verification.character_map import (
    CHARACTER_FILES,
    FULFILLER_CHARACTER_MAP,
    get_characters_for_fulfiller,
    get_unmapped_fulfillers,
)
from wish_engine.verification.validator import (
    ValidationResult,
    ValidationReport,
    validate_single,
    validate_fulfiller,
    validate_all,
)


class TestCharacterMap:
    def test_has_characters(self):
        assert len(CHARACTER_FILES) >= 20

    def test_has_fulfiller_mappings(self):
        assert len(FULFILLER_CHARACTER_MAP) >= 15

    def test_each_mapping_has_characters(self):
        for name, chars in FULFILLER_CHARACTER_MAP.items():
            assert len(chars) >= 1, f"{name} has no characters"

    def test_each_character_has_required_fields(self):
        for name, chars in FULFILLER_CHARACTER_MAP.items():
            for c in chars:
                assert "character" in c, f"{name} missing character"
                assert "reason" in c, f"{name} missing reason"
                assert "expected_tags" in c, f"{name} missing expected_tags"

    def test_get_characters_for_known_fulfiller(self):
        chars = get_characters_for_fulfiller("l2_suicide_prevention")
        assert len(chars) >= 2

    def test_get_characters_for_unknown_returns_empty(self):
        assert get_characters_for_fulfiller("l2_nonexistent") == []

    def test_unmapped_fulfillers_exist(self):
        unmapped = get_unmapped_fulfillers()
        assert isinstance(unmapped, list)


class TestValidateSingle:
    def test_food_xu_sanguan(self):
        spec = {"character": "xu_sanguan", "reason": "Hunger drives everything", "expected_tags": ["comfort"]}
        result = validate_single("l2_food", spec)
        assert isinstance(result, ValidationResult)
        assert result.fulfiller == "l2_food"
        assert result.character == "xu_sanguan"
        assert len(result.recommendations) >= 1

    def test_nature_healing_jane(self):
        spec = {"character": "jane", "reason": "Moors heal her", "expected_tags": ["nature"]}
        result = validate_single("l2_nature_healing", spec)
        assert isinstance(result, ValidationResult)
        assert len(result.recommendations) >= 1

    def test_confidence_celie(self):
        spec = {"character": "celie", "reason": "Zero to hero journey", "expected_tags": ["confidence"]}
        result = validate_single("l2_confidence", spec)
        assert result.character == "celie"


class TestValidateFulfiller:
    def test_validate_food(self):
        results = validate_fulfiller("l2_food")
        assert len(results) >= 2
        assert all(isinstance(r, ValidationResult) for r in results)

    def test_validate_suicide_prevention(self):
        results = validate_fulfiller("l2_suicide_prevention")
        assert len(results) >= 2


class TestValidateAll:
    def test_full_validation_runs(self):
        report = validate_all()
        assert isinstance(report, ValidationReport)
        assert report.total >= 30
        assert report.passed >= 1

    def test_report_has_pass_rate(self):
        report = validate_all()
        assert 0.0 <= report.pass_rate <= 1.0

    def test_report_counts_consistent(self):
        report = validate_all()
        assert report.passed + report.failed + report.errors == report.total
