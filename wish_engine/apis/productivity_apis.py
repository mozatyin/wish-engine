"""Productivity APIs. Local compute."""
from __future__ import annotations
import random


# 96. Pomodoro timer calculator (local)
def pomodoro_schedule(
    total_hours: float = 4,
    focus_min: int = 25,
    break_min: int = 5,
    long_break_min: int = 15,
) -> list[dict]:
    schedule = []
    total_min = int(total_hours * 60)
    elapsed = 0
    session = 1
    while elapsed < total_min:
        schedule.append(
            {"type": "focus", "session": session, "start_min": elapsed, "duration": focus_min}
        )
        elapsed += focus_min
        if session % 4 == 0:
            schedule.append(
                {"type": "long_break", "start_min": elapsed, "duration": long_break_min}
            )
            elapsed += long_break_min
        else:
            schedule.append({"type": "break", "start_min": elapsed, "duration": break_min})
            elapsed += break_min
        session += 1
    return schedule


# 97. Eisenhower matrix sorter (local)
def eisenhower_sort(tasks: list[dict]) -> dict:
    """tasks: [{"name": "...", "urgent": True/False, "important": True/False}]"""
    matrix: dict[str, list[str]] = {
        "do_first": [],
        "schedule": [],
        "delegate": [],
        "eliminate": [],
    }
    for t in tasks:
        if t.get("urgent") and t.get("important"):
            matrix["do_first"].append(t["name"])
        elif not t.get("urgent") and t.get("important"):
            matrix["schedule"].append(t["name"])
        elif t.get("urgent") and not t.get("important"):
            matrix["delegate"].append(t["name"])
        else:
            matrix["eliminate"].append(t["name"])
    return matrix


# 98. Goal SMART checker (local)
def check_smart_goal(goal: str) -> dict:
    feedback = []
    if len(goal) < 20:
        feedback.append("Too vague -- be more Specific")
    if not any(c.isdigit() for c in goal):
        feedback.append("Not Measurable -- add a number or metric")
    if (
        "by" not in goal.lower()
        and "before" not in goal.lower()
        and "within" not in goal.lower()
    ):
        feedback.append("Not Time-bound -- add a deadline")
    is_smart = len(feedback) == 0
    return {
        "goal": goal,
        "is_smart": is_smart,
        "feedback": feedback if feedback else ["This goal looks SMART!"],
    }


# 99. Decision helper (local)
def decision_helper(option_a: str, option_b: str) -> dict:
    questions = [
        "Which option aligns more with your values?",
        "Which would you regret NOT choosing in 5 years?",
        "If money weren't an issue, which would you pick?",
        "What would the bravest version of you choose?",
        "Which option scares you more? (That might be the right one.)",
    ]
    return {
        "option_a": option_a,
        "option_b": option_b,
        "guiding_question": random.choice(questions),
        "coin_flip": random.choice([option_a, option_b]),
        "note": "The coin flip doesn't decide -- your reaction to the result does.",
    }


# 100. Weekly reflection prompts (local)
def weekly_reflection() -> list[str]:
    return [
        "What went well this week?",
        "What was the hardest moment? How did you handle it?",
        "Who did you connect with this week?",
        "What did you learn?",
        "What do you want to do differently next week?",
        "What are you grateful for?",
        "Rate your energy this week: 1-10. Why?",
    ]


def is_available() -> bool:
    return True
