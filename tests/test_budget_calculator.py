"""Tests for budget_calculator — pure local computation."""
import pytest

from wish_engine.apis.budget_calculator import (
    fifty_thirty_twenty,
    emergency_fund_target,
    debt_snowball,
    debt_avalanche,
    savings_goal,
    calorie_budget,
)


class TestFiftyThirtyTwenty:
    def test_splits_income_correctly(self):
        result = fifty_thirty_twenty(3000)
        assert result["needs"] == pytest.approx(1500, rel=1e-3)
        assert result["wants"] == pytest.approx(900, rel=1e-3)
        assert result["savings"] == pytest.approx(600, rel=1e-3)

    def test_percentages_present(self):
        result = fifty_thirty_twenty(1000)
        assert result["pct_needs"] == 50
        assert result["pct_wants"] == 30
        assert result["pct_savings"] == 20

    def test_parts_sum_to_income(self):
        income = 4567.89
        result = fifty_thirty_twenty(income)
        total = result["needs"] + result["wants"] + result["savings"]
        assert total == pytest.approx(income, abs=0.02)

    def test_zero_income(self):
        result = fifty_thirty_twenty(0)
        assert result["needs"] == 0
        assert result["wants"] == 0
        assert result["savings"] == 0


class TestEmergencyFundTarget:
    def test_default_six_months(self):
        assert emergency_fund_target(2000) == pytest.approx(12000)

    def test_custom_months(self):
        assert emergency_fund_target(1000, months=3) == pytest.approx(3000)

    def test_clamps_months_to_max_12(self):
        r12 = emergency_fund_target(1000, months=12)
        r99 = emergency_fund_target(1000, months=99)
        assert r12 == r99

    def test_clamps_months_to_min_1(self):
        r0 = emergency_fund_target(1000, months=0)
        r1 = emergency_fund_target(1000, months=1)
        assert r0 == r1 == pytest.approx(1000)


class TestDebtSnowball:
    def test_sorts_smallest_balance_first(self):
        debts = [
            {"name": "C", "balance": 500, "rate": 5.0},
            {"name": "A", "balance": 100, "rate": 20.0},
            {"name": "B", "balance": 2000, "rate": 3.0},
        ]
        result = debt_snowball(debts)
        assert result[0]["name"] == "A"
        assert result[1]["name"] == "C"
        assert result[2]["name"] == "B"

    def test_empty_list(self):
        assert debt_snowball([]) == []

    def test_does_not_mutate_input(self):
        debts = [{"name": "X", "balance": 100}]
        debt_snowball(debts)
        assert len(debts) == 1


class TestDebtAvalanche:
    def test_sorts_highest_rate_first(self):
        debts = [
            {"name": "C", "balance": 500, "rate": 5.0},
            {"name": "A", "balance": 100, "rate": 20.0},
            {"name": "B", "balance": 2000, "rate": 3.0},
        ]
        result = debt_avalanche(debts)
        assert result[0]["name"] == "A"
        assert result[1]["name"] == "C"
        assert result[2]["name"] == "B"

    def test_empty_list(self):
        assert debt_avalanche([]) == []


class TestSavingsGoal:
    def test_basic_calculation(self):
        result = savings_goal(target=12000, monthly_save=1000)
        assert result["months"] == 12
        assert result["years"] == pytest.approx(1.0)

    def test_non_round_number(self):
        result = savings_goal(target=1000, monthly_save=300)
        assert result["months"] == 4  # ceil(1000/300) = 4

    def test_zero_monthly_save_returns_impossible(self):
        result = savings_goal(target=1000, monthly_save=0)
        assert result["months"] == -1
        assert result["years"] == -1.0

    def test_negative_monthly_save_returns_impossible(self):
        result = savings_goal(target=1000, monthly_save=-100)
        assert result["months"] == -1

    def test_result_contains_target_and_monthly_save(self):
        result = savings_goal(5000, 500)
        assert result["target"] == 5000
        assert result["monthly_save"] == 500


class TestCalorieBudget:
    def test_male_sedentary(self):
        result = calorie_budget(70, 175, 30, "male", "sedentary")
        assert result["bmr"] > 0
        assert result["tdee"] > result["bmr"]
        assert result["deficit_500"] == pytest.approx(result["tdee"] - 500)
        assert result["surplus_250"] == pytest.approx(result["tdee"] + 250)

    def test_female_active(self):
        result = calorie_budget(60, 165, 25, "female", "active")
        assert result["activity_factor"] == pytest.approx(1.725)
        assert result["tdee"] > 2000

    def test_activity_factor_stored(self):
        r = calorie_budget(70, 175, 30, "male", "moderate")
        assert r["activity_factor"] == pytest.approx(1.55)
        assert r["activity"] == "moderate"

    def test_unknown_activity_defaults_to_sedentary(self):
        r_sedentary = calorie_budget(70, 175, 30, "male", "sedentary")
        r_unknown   = calorie_budget(70, 175, 30, "male", "unknown")
        assert r_sedentary["tdee"] == r_unknown["tdee"]

    def test_female_lower_bmr_than_male_same_stats(self):
        male   = calorie_budget(70, 175, 30, "male",   "sedentary")
        female = calorie_budget(70, 175, 30, "female", "sedentary")
        assert male["bmr"] > female["bmr"]
