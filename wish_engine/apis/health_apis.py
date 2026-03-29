"""Health & body APIs. All free, no key or local compute."""
from __future__ import annotations


# 81. BMI calculator (local)
def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    return {"bmi": round(bmi, 1), "category": category}


# 82. Water intake calculator (local)
def daily_water_ml(weight_kg: float, exercise_minutes: int = 0, hot_weather: bool = False) -> int:
    base = weight_kg * 33  # 33ml per kg
    base += exercise_minutes * 12  # 12ml per minute of exercise
    if hot_weather:
        base += 500
    return int(base)


# 83. Sleep calculator (local)
def sleep_times(wake_time_hour: int, wake_time_minute: int = 0) -> list[str]:
    """Calculate optimal bedtimes based on 90-minute sleep cycles."""
    results = []
    for cycles in [6, 5, 4, 3]:  # 9h, 7.5h, 6h, 4.5h
        minutes_before = cycles * 90 + 15  # 15 min to fall asleep
        total_minutes = wake_time_hour * 60 + wake_time_minute - minutes_before
        if total_minutes < 0:
            total_minutes += 24 * 60
        h = (total_minutes // 60) % 24
        m = total_minutes % 60
        results.append(f"{h:02d}:{m:02d} ({cycles} cycles, {cycles * 1.5:.1f}h)")
    return results


# 84. Heart rate zones (local)
def heart_rate_zones(age: int, resting_hr: int = 70) -> dict:
    max_hr = 220 - age
    return {
        "max_hr": max_hr,
        "zone_1_recovery": f"{int(max_hr * 0.5)}-{int(max_hr * 0.6)} bpm",
        "zone_2_fat_burn": f"{int(max_hr * 0.6)}-{int(max_hr * 0.7)} bpm",
        "zone_3_cardio": f"{int(max_hr * 0.7)}-{int(max_hr * 0.8)} bpm",
        "zone_4_hard": f"{int(max_hr * 0.8)}-{int(max_hr * 0.9)} bpm",
        "zone_5_max": f"{int(max_hr * 0.9)}-{max_hr} bpm",
    }


# 85. Calorie estimation (local, rough)
def estimate_calories(activity: str, weight_kg: float, minutes: int) -> int:
    """Rough calorie burn estimation."""
    met_values = {
        "walking": 3.5,
        "running": 8.0,
        "cycling": 6.0,
        "swimming": 7.0,
        "yoga": 2.5,
        "weight_training": 5.0,
        "dancing": 4.5,
        "meditation": 1.2,
        "cooking": 2.5,
        "cleaning": 3.0,
        "sleeping": 0.9,
        "reading": 1.0,
    }
    met = met_values.get(activity.lower(), 3.0)
    return int(met * weight_kg * minutes / 60)


def is_available() -> bool:
    return True
