"""Tests for deep personalization engine."""

from wish_engine.models import DetectorResults
from wish_engine.personalization import personalize_reason


def _det(**kwargs) -> DetectorResults:
    """Helper to build DetectorResults with specific fields."""
    return DetectorResults(**kwargs)


# ── MBTI-based reasons ──────────────────────────────────────────────────────


def test_infj_quiet_environment():
    dr = _det(mbti={"type": "INFJ"})
    reason = personalize_reason("Solo Workshop", ["quiet", "creative"], dr)
    assert "INFJ" in reason
    assert "quiet environments" in reason


def test_estp_social_setting():
    dr = _det(mbti={"type": "ESTP"})
    reason = personalize_reason("Group Hike", ["social", "exercise"], dr)
    assert "ESTP" in reason
    assert "social settings" in reason


def test_intj_theory_match():
    dr = _det(mbti={"type": "INTJ"})
    reason = personalize_reason("Philosophy Course", ["theory", "deep"], dr)
    assert "intuitive thinker" in reason
    assert "INTJ" in reason


def test_isfp_practical_match():
    dr = _det(mbti={"type": "ISFP"})
    reason = personalize_reason("Pottery Class", ["practical", "creative"], dr)
    assert "hands-on" in reason
    assert "ISFP" in reason


# ── Emotion-based reasons ───────────────────────────────────────────────────


def test_high_anxiety_calming():
    dr = _det(emotion={"emotions": {"anxiety": 0.8}})
    reason = personalize_reason("Forest Walk", ["calming", "nature"], dr)
    assert "stress levels" in reason


def test_high_anxiety_exercise():
    dr = _det(emotion={"emotions": {"anxiety": 0.7}})
    reason = personalize_reason("Boxing Class", ["exercise", "intense"], dr)
    assert "reduce anxiety" in reason


def test_sadness_nature():
    dr = _det(emotion={"emotions": {"sadness": 0.6}})
    reason = personalize_reason("Garden Trail", ["nature"], dr)
    assert "lift mood" in reason


def test_sadness_social():
    dr = _det(emotion={"emotions": {"loneliness": 0.7}})
    reason = personalize_reason("Community Event", ["social"], dr)
    assert "Connection" in reason


def test_anger_physical():
    dr = _det(emotion={"emotions": {"anger": 0.8}})
    reason = personalize_reason("Kickboxing", ["exercise", "physical"], dr)
    assert "Physical release" in reason


# ── Values-based reasons ────────────────────────────────────────────────────


def test_values_self_direction():
    dr = _det(values={"top_values": ["self-direction"]})
    reason = personalize_reason("Solo Retreat", [], dr)
    assert "independent spirit" in reason


def test_values_benevolence():
    dr = _det(values={"top_values": ["benevolence"]})
    reason = personalize_reason("Volunteer Day", [], dr)
    assert "help and care" in reason


# ── Attachment-based reasons ────────────────────────────────────────────────


def test_anxious_attachment_calming():
    dr = _det(attachment={"style": "anxious"})
    reason = personalize_reason("Meditation Room", ["calming"], dr)
    assert "safe, predictable" in reason


def test_avoidant_attachment_quiet():
    dr = _det(attachment={"style": "avoidant"})
    reason = personalize_reason("Solo Studio", ["quiet"], dr)
    assert "independence" in reason


# ── Fragility-based reasons ─────────────────────────────────────────────────


def test_hypervigilant_fragility():
    dr = _det(fragility={"pattern": "hypervigilant"})
    reason = personalize_reason("Zen Garden", ["calming"], dr)
    assert "exhale" in reason


# ── Fallback ────────────────────────────────────────────────────────────────


def test_generic_fallback_no_dimensions():
    dr = _det()
    reason = personalize_reason("Calming Acoustic", [], dr)
    assert reason == "Recommended for you: Calming Acoustic"


# ── Combined dimensions (max 2 parts) ──────────────────────────────────────


def test_combined_mbti_and_values():
    dr = _det(
        mbti={"type": "INFJ"},
        values={"top_values": ["self-direction"]},
    )
    reason = personalize_reason("Quiet Studio", ["quiet"], dr)
    # Should mention either MBTI or values (hash selects one)
    assert "INFJ" in reason or "independent" in reason
    assert "Quiet Studio" in reason  # title prefix


def test_combined_caps_at_two_parts():
    dr = _det(
        mbti={"type": "INFJ"},
        values={"top_values": ["self-direction"]},
        attachment={"style": "avoidant"},
        fragility={"pattern": "hypervigilant"},
    )
    reason = personalize_reason("Quiet Retreat", ["quiet"], dr)
    # Should not have more than 2 sentences joined
    assert reason.count(". ") <= 1
