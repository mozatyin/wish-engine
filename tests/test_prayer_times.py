"""Tests for Prayer Times Calculator — astronomical local computation."""

import pytest
from datetime import datetime, timezone

from wish_engine.apis.prayer_times import (
    get_prayer_times,
    get_next_prayer,
    is_available,
    METHODS,
)


class TestIsAvailable:
    def test_always_true(self):
        assert is_available() is True


class TestPrayerTimesMakkah:
    """Makkah (21.4225°N, 39.8262°E) — well-known reference location."""

    LAT, LNG = 21.4225, 39.8262

    def test_returns_all_six_prayers(self):
        times = get_prayer_times(self.LAT, self.LNG, method="MWL")
        assert set(times.keys()) == {"Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"}

    def test_times_are_hh_mm_format(self):
        times = get_prayer_times(self.LAT, self.LNG)
        for name, t in times.items():
            parts = t.split(":")
            assert len(parts) == 2, f"{name}: {t}"
            assert 0 <= int(parts[0]) <= 23, f"{name} hour out of range: {t}"
            assert 0 <= int(parts[1]) <= 59, f"{name} minute out of range: {t}"

    def test_prayer_order_chronological(self):
        times = get_prayer_times(self.LAT, self.LNG)
        order = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]
        minutes = []
        for name in order:
            h, m = map(int, times[name].split(":"))
            minutes.append(h * 60 + m)
        for i in range(len(minutes) - 1):
            assert minutes[i] < minutes[i + 1], (
                f"{order[i]} ({minutes[i]}) should be before {order[i+1]} ({minutes[i+1]})"
            )

    def test_dhuhr_around_noon(self):
        """Dhuhr (solar noon) should be roughly 11:30-12:30 local time."""
        times = get_prayer_times(self.LAT, self.LNG)
        h, _ = map(int, times["Dhuhr"].split(":"))
        assert 11 <= h <= 13, f"Dhuhr at {times['Dhuhr']} seems wrong for Makkah"


class TestPrayerTimesDubai:
    """Dubai (25.2048°N, 55.2708°E)."""

    LAT, LNG = 25.2048, 55.2708

    def test_returns_valid_times(self):
        times = get_prayer_times(self.LAT, self.LNG, method="MWL")
        assert len(times) == 6
        for name, t in times.items():
            h, m = map(int, t.split(":"))
            assert 0 <= h <= 23


class TestDifferentMethods:
    LAT, LNG = 21.4225, 39.8262  # Makkah

    def test_all_methods_produce_results(self):
        for method in METHODS:
            times = get_prayer_times(self.LAT, self.LNG, method=method)
            assert len(times) == 6, f"Method {method} failed"

    def test_different_fajr_angles_give_different_fajr(self):
        """MWL (18°) and ISNA (15°) have different Fajr angles."""
        mwl = get_prayer_times(self.LAT, self.LNG, method="MWL")
        isna = get_prayer_times(self.LAT, self.LNG, method="ISNA")
        # ISNA has smaller angle → later Fajr
        assert mwl["Fajr"] != isna["Fajr"]

    def test_invalid_method_raises(self):
        with pytest.raises(ValueError, match="Unknown method"):
            get_prayer_times(self.LAT, self.LNG, method="INVALID")

    def test_makkah_method_isha_after_maghrib(self):
        """Makkah method: Isha = 90 min after Maghrib."""
        times = get_prayer_times(self.LAT, self.LNG, method="Makkah")
        mh, mm = map(int, times["Maghrib"].split(":"))
        ih, im = map(int, times["Isha"].split(":"))
        diff = (ih * 60 + im) - (mh * 60 + mm)
        assert 85 <= diff <= 95, f"Isha should be ~90min after Maghrib, got {diff}min"


class TestGetNextPrayer:
    def test_returns_valid_tuple(self):
        name, time_str, minutes_until = get_next_prayer(21.4225, 39.8262)
        assert name in {"Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"}
        assert ":" in time_str
        assert minutes_until > 0
