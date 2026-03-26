"""Revelation Renderer — generates insight text for shells."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from wish_engine.compass.models import ContradictionPattern, Shell, ShellStage


class RevelationStyle(str, Enum):
    METAPHOR = "metaphor"
    QUESTION = "question"
    GENTLE_STATEMENT = "gentle_statement"


class Revelation(BaseModel):
    shell_id: str
    style: RevelationStyle
    text: str


# ---------------------------------------------------------------------------
# Template banks — keyed by ContradictionPattern
# ---------------------------------------------------------------------------

_METAPHOR_TEMPLATES: dict[ContradictionPattern, list[str]] = {
    ContradictionPattern.MOUTH_HARD_HEART_SOFT: [
        "A river runs beneath the stone.",
        "The armor hums a quiet lullaby.",
    ],
    ContradictionPattern.SAY_ONE_DO_OTHER: [
        "Two paths diverge in a single step.",
        "The compass needle trembles between poles.",
    ],
    ContradictionPattern.REPEATED_PROBING: [
        "A moth circles the same lantern again.",
        "The tide keeps returning to the same shore.",
    ],
    ContradictionPattern.VALUE_CONFLICT: [
        "Two stars share one sky, pulling in opposite ways.",
        "The roots grow toward two different waters.",
    ],
    ContradictionPattern.EMOTION_ANOMALY: [
        "A color appears where the palette says none should be.",
        "The melody shifts to an unexpected key.",
    ],
    ContradictionPattern.AVOIDANCE_SIGNAL: [
        "A door left ajar, never entered.",
        "Footprints circle around, never crossing the threshold.",
    ],
    ContradictionPattern.GROWTH_GAP: [
        "A seed dreams of sunlight it hasn't yet reached.",
        "The cocoon trembles, not yet ready to open.",
    ],
}

_QUESTION_TEMPLATES: dict[ContradictionPattern, list[str]] = {
    ContradictionPattern.MOUTH_HARD_HEART_SOFT: [
        "Could it be that your firmness about {topic} protects something tender?",
    ],
    ContradictionPattern.SAY_ONE_DO_OTHER: [
        "Have you noticed your actions around {topic} tell a different story?",
    ],
    ContradictionPattern.REPEATED_PROBING: [
        "What keeps drawing you back to {topic}?",
    ],
    ContradictionPattern.VALUE_CONFLICT: [
        "Do you feel pulled in two directions when it comes to {topic}?",
    ],
    ContradictionPattern.EMOTION_ANOMALY: [
        "Does {topic} stir something unexpected in you?",
    ],
    ContradictionPattern.AVOIDANCE_SIGNAL: [
        "Is there a reason you tend to step around {topic}?",
    ],
    ContradictionPattern.GROWTH_GAP: [
        "Are you ready to explore what {topic} could become?",
    ],
}

_GENTLE_STATEMENT_TEMPLATES: dict[ContradictionPattern, list[str]] = {
    ContradictionPattern.MOUTH_HARD_HEART_SOFT: [
        "It seems your toughness around {topic} might be guarding a softer truth.",
    ],
    ContradictionPattern.SAY_ONE_DO_OTHER: [
        "Your words and actions around {topic} seem to be having a quiet conversation.",
    ],
    ContradictionPattern.REPEATED_PROBING: [
        "You keep circling back to {topic} — it clearly matters to you.",
    ],
    ContradictionPattern.VALUE_CONFLICT: [
        "There may be two honest voices inside you about {topic}.",
    ],
    ContradictionPattern.EMOTION_ANOMALY: [
        "Your feelings about {topic} carry a shade that surprised even you.",
    ],
    ContradictionPattern.AVOIDANCE_SIGNAL: [
        "You seem to give {topic} a wide berth — and that says something too.",
    ],
    ContradictionPattern.GROWTH_GAP: [
        "There is a version of you that is already reaching toward {topic}.",
    ],
}

# ---------------------------------------------------------------------------
# Style selection logic
# ---------------------------------------------------------------------------

_STAGE_TO_STYLE: dict[ShellStage, RevelationStyle] = {
    ShellStage.SPROUT: RevelationStyle.METAPHOR,
    ShellStage.BUD: RevelationStyle.QUESTION,
    ShellStage.BLOOM: RevelationStyle.GENTLE_STATEMENT,
}

_STYLE_ORDER = [RevelationStyle.METAPHOR, RevelationStyle.QUESTION, RevelationStyle.GENTLE_STATEMENT]


def _cap_style(style: RevelationStyle, sensitivity: str) -> RevelationStyle:
    """High sensitivity caps the style at QUESTION (never gentle_statement)."""
    if sensitivity == "high" and style == RevelationStyle.GENTLE_STATEMENT:
        return RevelationStyle.QUESTION
    return style


def _pick_template(pattern: ContradictionPattern, style: RevelationStyle, topic: str) -> str:
    if style == RevelationStyle.METAPHOR:
        templates = _METAPHOR_TEMPLATES[pattern]
    elif style == RevelationStyle.QUESTION:
        templates = _QUESTION_TEMPLATES[pattern]
    else:
        templates = _GENTLE_STATEMENT_TEMPLATES[pattern]

    text = templates[0]
    if "{topic}" in text:
        text = text.replace("{topic}", topic)
    return text


class RevelationRenderer:
    """Renders a Revelation for a given Shell."""

    def render(self, shell: Shell, sensitivity: str = "medium") -> Revelation:
        base_style = _STAGE_TO_STYLE.get(shell.stage)
        if base_style is None:
            # seed shells shouldn't be rendered, but fall back to metaphor
            base_style = RevelationStyle.METAPHOR

        style = _cap_style(base_style, sensitivity)
        text = _pick_template(shell.pattern, style, shell.topic)

        return Revelation(shell_id=shell.id, style=style, text=text)
