"""Budget calculator — pure local computation, zero network dependency.

All functions take raw numbers and return structured dicts.
No external calls, no env vars, no auth.

Usage:
    from wish_engine.apis.budget_calculator import (
        fifty_thirty_twenty, emergency_fund_target,
        debt_snowball, debt_avalanche, savings_goal, calorie_budget,
    )
"""

from __future__ import annotations

import math


def fifty_thirty_twenty(income: float) -> dict:
    """Split income using the 50/30/20 budgeting rule.

    Args:
        income: Monthly take-home income (any currency).

    Returns:
        {"needs": float, "wants": float, "savings": float,
         "pct_needs": 50, "pct_wants": 30, "pct_savings": 20}
    """
    return {
        "needs":       round(income * 0.50, 2),
        "wants":       round(income * 0.30, 2),
        "savings":     round(income * 0.20, 2),
        "pct_needs":   50,
        "pct_wants":   30,
        "pct_savings": 20,
    }


def emergency_fund_target(monthly_expenses: float, months: int = 6) -> float:
    """Calculate recommended emergency fund size.

    Args:
        monthly_expenses: Total monthly spending (rent + food + bills + etc).
        months: How many months to cover (default 6, range 3-12).

    Returns:
        Target savings amount.
    """
    months = max(1, min(12, months))
    return round(monthly_expenses * months, 2)


def debt_snowball(debts: list[dict]) -> list[dict]:
    """Sort debts for the snowball method: smallest balance first.

    Each debt dict should have: {"name": str, "balance": float, "min_payment": float, ...}
    Debts with equal balances are sorted by name.

    Args:
        debts: List of debt dicts.

    Returns:
        Sorted list — attack smallest balance first to build momentum.
    """
    return sorted(debts, key=lambda d: (d.get("balance", 0), d.get("name", "")))


def debt_avalanche(debts: list[dict]) -> list[dict]:
    """Sort debts for the avalanche method: highest interest rate first.

    Each debt dict should have: {"name": str, "balance": float, "rate": float, ...}
    Debts with equal rates are sorted by balance descending.

    Args:
        debts: List of debt dicts.

    Returns:
        Sorted list — attack highest rate first to minimise total interest paid.
    """
    return sorted(debts, key=lambda d: (-d.get("rate", 0), -d.get("balance", 0)))


def savings_goal(target: float, monthly_save: float) -> dict:
    """Calculate how long to reach a savings target.

    Args:
        target:       Amount to save.
        monthly_save: Amount saved each month.

    Returns:
        {"months": int, "years": float, "monthly_save": float, "target": float}
        If monthly_save <= 0 returns {"months": -1, "years": -1, ...} (impossible).
    """
    if monthly_save <= 0:
        return {"months": -1, "years": -1.0, "monthly_save": monthly_save, "target": target}
    months = math.ceil(target / monthly_save)
    return {
        "months":       months,
        "years":        round(months / 12, 1),
        "monthly_save": monthly_save,
        "target":       target,
    }


def calorie_budget(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: str = "male",
    activity: str = "sedentary",
) -> dict:
    """Estimate daily calorie needs using the Mifflin-St Jeor equation.

    Args:
        weight_kg: Body weight in kg.
        height_cm: Height in cm.
        age:       Age in years.
        sex:       "male" or "female".
        activity:  One of "sedentary", "light", "moderate", "active", "very_active".

    Returns:
        {"bmr": float, "tdee": float, "deficit_500": float, "surplus_250": float,
         "activity_factor": float, "activity": str}

        bmr        = basal metabolic rate (at rest).
        tdee       = total daily energy expenditure (with activity).
        deficit_500 = tdee - 500 (mild weight loss, ~0.5 kg/week).
        surplus_250 = tdee + 250 (mild muscle gain).
    """
    _ACTIVITY = {
        "sedentary":   1.2,
        "light":       1.375,
        "moderate":    1.55,
        "active":      1.725,
        "very_active": 1.9,
    }
    factor = _ACTIVITY.get(activity.lower(), 1.2)

    # Mifflin-St Jeor
    if sex.lower() in ("male", "m"):
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    tdee = bmr * factor
    return {
        "bmr":             round(bmr, 0),
        "tdee":            round(tdee, 0),
        "deficit_500":     round(tdee - 500, 0),
        "surplus_250":     round(tdee + 250, 0),
        "activity_factor": factor,
        "activity":        activity,
    }
