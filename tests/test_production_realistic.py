"""Tests with production-realistic inputs (short, terse, non-English).

These tests verify that rule-based components (case_formulator,
schema_detector, technique_selector, tone_adapter) handle minimal,
terse, and non-English inputs without crashing or hallucinating.
No LLM calls — all components tested here are zero-LLM.
"""

import pytest

from expert_engine.case_formulator import CaseFormulator
from expert_engine.schema_detector import SchemaDetector
from expert_engine.technique_selector import TechniqueSelector
from expert_engine.tone_adapter import ToneAdapter, ToneDirective
from expert_engine.models import (
    CaseFormulation,
    SchemaProfile,
    SchemaType,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _minimal_signals(**overrides) -> dict:
    """Bare minimum signals — simulates sparse production data."""
    base = {
        "attachment_style": "",
        "attachment_confidence": 0.0,
        "conflict_style": "",
        "conflict_confidence": 0.0,
        "fragility_pattern": "",
        "fragility_confidence": 0.0,
        "humor_style": "",
        "humor_confidence": 0.0,
        "eq_score": 0.5,
        "emotion_dominant": "",
        "emotion_intensity": 0.0,
        "crisis_level": 0.0,
        "user_id": "prod_user",
    }
    base.update(overrides)
    return base


def _terse_signals(**overrides) -> dict:
    """Signals from a user who gave very short answers — only 2-3 dimensions."""
    base = _minimal_signals()
    base.update({
        "emotion_dominant": "neutral",
        "emotion_intensity": 0.3,
        "eq_score": 0.4,
    })
    base.update(overrides)
    return base


# ── Test: Terse Input Handling ───────────────────────────────────────────────


class TestTerseInputHandling:
    """Expert components should handle 'idk' and 'ok' style sparse data."""

    def test_case_formulator_with_empty_signals(self):
        """CaseFormulator with near-empty signals should not crash."""
        cf = CaseFormulator()
        result = cf.formulate(
            detector_signals=_minimal_signals(),
            deep_soul_items=[],
            surface_facts=[],
            cross_detector_patterns=[],
        )
        assert isinstance(result, CaseFormulation)
        # With minimal signals, predisposing should be empty (no vulnerabilities detected)
        assert isinstance(result.predisposing, list)

    def test_case_formulator_with_only_emotion(self):
        """Only emotion data available — should not hallucinate other factors."""
        cf = CaseFormulator()
        result = cf.formulate(
            detector_signals=_minimal_signals(
                emotion_dominant="sadness",
                emotion_intensity=0.7,
            ),
            deep_soul_items=[],
            surface_facts=[],
            cross_detector_patterns=[],
        )
        assert isinstance(result, CaseFormulation)
        # Should detect precipitating sadness but NOT predisposing factors
        # (we have no attachment, conflict, fragility data)
        precip_factors = [f.factor for f in result.precipitating]
        assert any("sadness" in f for f in precip_factors), (
            "Should detect elevated sadness as precipitating factor"
        )
        # Predisposing should be empty since we have no trait data
        assert len(result.predisposing) == 0, (
            f"Should not hallucinate predisposing factors from emotion alone, got: "
            f"{[f.factor for f in result.predisposing]}"
        )

    def test_tone_adapter_with_minimal_signals(self):
        """ToneAdapter should return a valid directive even with no signals."""
        ta = ToneAdapter()
        directive = ta.adapt(_minimal_signals())
        assert isinstance(directive, ToneDirective)
        assert directive.style in ("warm", "direct", "gentle", "intellectual", "challenging")
        assert len(directive.dos) > 0, "Should always have at least some dos"

    def test_tone_adapter_with_only_eq(self):
        """Only EQ score — should pick a reasonable style."""
        ta = ToneAdapter()
        directive = ta.adapt(_minimal_signals(eq_score=0.3))
        assert isinstance(directive, ToneDirective)
        # Low EQ alone should not crash
        assert directive.style is not None


class TestSchemaDetectionMinimalData:
    """Schema detector with only 2 data points should not hallucinate."""

    def test_two_signals_only(self):
        """With only attachment + emotion, should detect limited schemas."""
        sd = SchemaDetector()
        signals = _minimal_signals(
            attachment_style="anxious",
            attachment_confidence=0.7,
        )
        profile = sd.detect(signals)
        assert isinstance(profile, SchemaProfile)
        # Should detect something related to anxious attachment
        if profile.schemas:
            schema_types = [s.schema_type for s in profile.schemas]
            # Anxious attachment should trigger abandonment-related schemas
            assert SchemaType.ABANDONMENT in schema_types, (
                f"Anxious attachment should trigger abandonment, got: {schema_types}"
            )

    def test_no_signals_at_all(self):
        """Completely empty signals should not crash."""
        sd = SchemaDetector()
        profile = sd.detect(_minimal_signals())
        assert isinstance(profile, SchemaProfile)
        # May detect nothing or trace-level schemas — both are valid
        assert isinstance(profile.schemas, list)

    def test_only_crisis_signal(self):
        """Only crisis level — should not hallucinate personality schemas."""
        sd = SchemaDetector()
        profile = sd.detect(_minimal_signals(crisis_level=0.8))
        assert isinstance(profile, SchemaProfile)
        # Crisis alone should not trigger personality schemas at high confidence
        for s in profile.schemas:
            assert s.confidence < 0.8, (
                f"Schema {s.schema_type} at {s.confidence:.2f} from crisis alone — hallucination"
            )


class TestShortArabicInput:
    """Expert components should work with Arabic user input contexts."""

    def test_case_formulator_arabic_deep_soul(self):
        """Arabic deep soul items should be processed without crash."""
        cf = CaseFormulator()
        result = cf.formulate(
            detector_signals=_terse_signals(
                attachment_style="anxious",
                attachment_confidence=0.6,
            ),
            deep_soul_items=[
                {"text": "ما حدا بيحبني", "confidence": 0.7},  # "Nobody loves me"
                {"text": "خايف من المستقبل", "confidence": 0.6},  # "Afraid of the future"
            ],
            surface_facts=[],
            cross_detector_patterns=[],
        )
        assert isinstance(result, CaseFormulation)
        # The absolute language detector should catch Arabic items with confidence >= 0.6
        # even though the regex is English — the item still gets processed

    def test_tone_adapter_arabic_context(self):
        """ToneAdapter should work when signals come from Arabic conversation."""
        ta = ToneAdapter()
        directive = ta.adapt(_terse_signals(
            attachment_style="anxious",
            fragility_pattern="reactive",
            fragility_confidence=0.7,
            emotion_dominant="sadness",  # Non-neutral to avoid "direct" path
            emotion_intensity=0.6,
            eq_score=0.35,  # Low EQ so intellectual path is skipped
        ))
        assert isinstance(directive, ToneDirective)
        assert directive.style == "gentle", (
            f"Anxious+reactive (non-neutral emotion, low EQ) should get gentle style, "
            f"got: {directive.style}"
        )


class TestCareerOneSentence:
    """Career expert components should work with just 'I hate my job'."""

    def test_case_formulator_career_frustration(self):
        """Minimal career frustration signals should produce valid formulation."""
        cf = CaseFormulator()
        result = cf.formulate(
            detector_signals=_terse_signals(
                emotion_dominant="frustration",
                emotion_intensity=0.8,
            ),
            deep_soul_items=[
                {"text": "I hate my job", "confidence": 0.9},
            ],
            surface_facts=[
                {"text": "career dissatisfaction", "emotional_valence": "aroused", "recency": "recent"},
            ],
            cross_detector_patterns=[],
        )
        assert isinstance(result, CaseFormulation)
        # Should have precipitating factor from frustration
        precip_factors = [f.factor for f in result.precipitating]
        assert len(precip_factors) > 0, "Should detect career frustration as precipitating"

    def test_schema_detector_career_failure(self):
        """Career frustration + self-criticism should detect failure schema."""
        sd = SchemaDetector()
        signals = _terse_signals(
            emotion_dominant="frustration",
            emotion_intensity=0.7,
            self_criticism_score=0.7,
            values_achievement=0.8,
        )
        profile = sd.detect(signals)
        schema_types = [s.schema_type for s in profile.schemas]
        # High achievement + self-criticism should trigger failure or unrelenting_standards
        assert (SchemaType.FAILURE in schema_types
                or SchemaType.UNRELENTING_STANDARDS in schema_types), (
            f"Career frustration with self-criticism should detect failure/standards, "
            f"got: {schema_types}"
        )

    def test_tone_for_frustrated_career_seeker(self):
        """Frustrated but not fragile person should get warm or direct style."""
        ta = ToneAdapter()
        directive = ta.adapt(_terse_signals(
            emotion_dominant="frustration",
            emotion_intensity=0.7,
            fragility_pattern="resilient",
            eq_score=0.6,
        ))
        assert directive.style in ("warm", "direct"), (
            f"Frustrated resilient person should get warm/direct, got: {directive.style}"
        )


class TestTechniqueSelectionSparseData:
    """Technique selection with sparse case formulation should not crash."""

    def test_select_with_empty_formulation(self):
        """Empty formulation should still return techniques (fallback)."""
        ts = TechniqueSelector()
        cf = CaseFormulator()
        signals = _minimal_signals()
        formulation = cf.formulate(
            detector_signals=signals,
            deep_soul_items=[],
            surface_facts=[],
            cross_detector_patterns=[],
        )
        sd = SchemaDetector()
        schema_profile = sd.detect(signals)

        result = ts.select(
            case_formulation=formulation,
            schema_profile=schema_profile,
            signals=signals,
        )
        # Should not crash — may return empty or fallback techniques
        assert isinstance(result, list) or hasattr(result, 'recommendations'), (
            "TechniqueSelector.select should return a valid result type"
        )
