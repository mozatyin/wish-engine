"""Deep Personalization — generates truly personal relevance reasons.

Instead of "Matches your profile", generates:
- "Because you're an INFJ who values self-direction, this quiet solo workshop
   lets you express yourself without social pressure"
- "Your anxiety has been high this week — this calming forest trail is
   scientifically shown to reduce cortisol in people with your emotional pattern"
"""

from __future__ import annotations

from wish_engine.models import DetectorResults


def personalize_reason(
    recommendation_title: str,
    recommendation_tags: list[str],
    detector_results: DetectorResults,
    wish_text: str = "",
) -> str:
    """Generate a deeply personal relevance reason. Zero LLM."""

    parts: list[str] = []
    tag_set = set(recommendation_tags)

    # MBTI-based reason
    mbti = detector_results.mbti.get("type", "")
    if mbti and len(mbti) >= 2:
        ns = "intuitive thinker" if mbti[1] == "N" else "practical thinker"
        if "quiet" in tag_set and mbti[0] == "I":
            parts.append(
                f"As an {mbti}, you thrive in quiet environments"
                " — this is designed for people like you"
            )
        elif "social" in tag_set and mbti[0] == "E":
            parts.append(
                f"Your {mbti} energy comes alive in social settings"
                " — this matches your natural style"
            )
        elif "theory" in tag_set and mbti[1] == "N":
            parts.append(
                f"As a {ns} ({mbti}), you'll appreciate"
                " the depth and conceptual approach here"
            )
        elif "practical" in tag_set and mbti[1] == "S":
            parts.append(
                f"You learn best by doing ({mbti})"
                " — this hands-on approach is right for you"
            )

    # Emotion-based reason
    emotions = detector_results.emotion.get("emotions", {})
    if emotions:
        top_emotion = max(emotions, key=emotions.get)
        level = emotions[top_emotion]
        if top_emotion in ("anxiety", "worry") and level > 0.5:
            if "calming" in tag_set:
                parts.append(
                    "Your stress levels have been elevated"
                    " — this is specifically calming"
                )
            elif "exercise" in tag_set:
                parts.append(
                    "Physical activity is proven to reduce anxiety by 40%"
                    " — your body needs this"
                )
        elif top_emotion in ("sadness", "grief", "loneliness") and level > 0.5:
            if "social" in tag_set:
                parts.append(
                    "Connection is what you need right now"
                    " — being around others can help"
                )
            elif "calming" in tag_set:
                parts.append(
                    "When sadness is heavy, gentle environments"
                    " give you space to process"
                )
            elif "nature" in tag_set:
                parts.append(
                    "Nature has been shown to lift mood in people"
                    " experiencing what you're feeling"
                )
        elif top_emotion in ("anger", "rage", "frustration") and level > 0.5:
            if tag_set & {"exercise", "intense", "physical"}:
                parts.append(
                    "Physical release channels anger constructively"
                    " — this is exactly what you need"
                )

    # Values-based reason
    values = detector_results.values.get("top_values", [])
    if values:
        val_reasons = {
            "tradition": "This honors your deep connection to tradition and heritage",
            "self-direction": "This supports your independent spirit — no one telling you what to do",
            "benevolence": "This aligns with your core drive to help and care for others",
            "universalism": "This connects to your belief in fairness and the greater good",
            "achievement": "This helps you move forward toward your goals",
            "security": "This provides the stability and safety you value most",
            "stimulation": "This feeds your hunger for new experiences and excitement",
            "power": "This puts you in control — exactly where you're most effective",
            "hedonism": "Life should be enjoyed — this is pure, deserved pleasure",
            "conformity": "This fits naturally with your social environment",
            "aesthetics": "This speaks to your refined sense of beauty and form",
        }
        top_val = values[0]
        if top_val in val_reasons:
            parts.append(val_reasons[top_val])

    # Attachment-based reason
    attachment = detector_results.attachment.get("style", "")
    if attachment:
        if attachment == "anxious" and "calming" in tag_set:
            parts.append(
                "For someone who needs reassurance,"
                " this provides a safe, predictable space"
            )
        elif attachment == "avoidant" and "quiet" in tag_set:
            parts.append(
                "You process best with space"
                " — this respects your need for independence"
            )
        elif attachment == "secure" and "social" in tag_set:
            parts.append(
                "Your secure base lets you connect openly"
                " — make the most of it"
            )

    # Fragility-based reason
    fragility = detector_results.fragility.get("pattern", "")
    if fragility:
        if fragility == "sensitive" and "gentle" in tag_set:
            parts.append(
                "This is designed to be gentle — no pressure, no judgment"
            )
        elif fragility == "defensive" and "calming" in tag_set:
            parts.append(
                "You don't always show it, but a safe space"
                " to let your guard down matters"
            )
        elif fragility == "hypervigilant":
            parts.append(
                "You've been on high alert"
                " — this is a place where you can exhale"
            )

    if not parts:
        return f"Recommended for you: {recommendation_title}"

    # Take the 2 most relevant parts
    return ". ".join(parts[:2])
