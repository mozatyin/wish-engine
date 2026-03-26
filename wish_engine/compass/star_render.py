"""Star rendering — visual states for compass shells."""

from __future__ import annotations

from pydantic import BaseModel

from wish_engine.compass.models import Shell, ShellStage


class CompassStarOutput(BaseModel):
    shell_id: str
    stage: ShellStage
    color: str
    animation: str
    animation_duration_ms: int


_STAGE_CONFIG: dict[ShellStage, tuple[str, str, int]] = {
    ShellStage.SPROUT: ("#2A2035", "flicker_rare", 10000),
    ShellStage.BUD: ("#5B4A8A", "pulse_slow", 4000),
    ShellStage.BLOOM: ("#E8A0BF", "glow_warm", 2000),
}


def render_shell_star(shell: Shell) -> CompassStarOutput | None:
    """Return visual star output for a shell. Seed shells are invisible (None)."""
    if shell.stage == ShellStage.SEED:
        return None

    color, animation, duration = _STAGE_CONFIG[shell.stage]
    return CompassStarOutput(
        shell_id=shell.id,
        stage=shell.stage,
        color=color,
        animation=animation,
        animation_duration_ms=duration,
    )
