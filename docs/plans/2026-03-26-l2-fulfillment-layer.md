# L2 Fulfillment Layer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement L2 (Internet Services) fulfillment layer — local-compute recommendation engine with personality-based filtering across 5 wish types, zero LLM calls.

**Architecture:** Adapter pattern with `L2Fulfiller` ABC. Each wish type has a concrete fulfiller with curated knowledge base + personality filter. Router dispatches by WishType. Engine integrates L2 fulfillment into the existing pipeline alongside L1.

**Tech Stack:** Python 3.12+, Pydantic v2 models, pytest, zero external API calls (curated catalogs only).

---

### Task 1: Add L2 output models to models.py

**Files:**
- Modify: `wish_engine/models.py:125-140`
- Test: `tests/test_l2_models.py` (create)

**Step 1: Write the failing test**

Create `tests/test_l2_models.py`:

```python
"""Tests for L2 output models."""

import pytest
from wish_engine.models import (
    L2FulfillmentResult,
    Recommendation,
    MapData,
    ReminderOption,
)


class TestRecommendation:
    def test_create_minimal(self):
        r = Recommendation(
            title="Calm Yoga Studio",
            description="Quiet yoga studio with small classes",
            category="yoga_studio",
            relevance_reason="Matches your introversion preference",
            score=0.85,
        )
        assert r.title == "Calm Yoga Studio"
        assert r.score == 0.85
        assert r.action_url is None
        assert r.tags == []

    def test_create_full(self):
        r = Recommendation(
            title="Mindfulness in Plain English",
            description="Classic meditation guide",
            category="book",
            relevance_reason="Aligns with your values: tradition",
            score=0.92,
            action_url="https://example.com/book/123",
            tags=["meditation", "beginner", "tradition"],
        )
        assert r.action_url == "https://example.com/book/123"
        assert len(r.tags) == 3

    def test_score_bounds(self):
        with pytest.raises(Exception):
            Recommendation(
                title="Bad", description="x", category="x",
                relevance_reason="x", score=1.5,
            )
        with pytest.raises(Exception):
            Recommendation(
                title="Bad", description="x", category="x",
                relevance_reason="x", score=-0.1,
            )


class TestMapData:
    def test_create(self):
        m = MapData(place_type="meditation_center", radius_km=5.0)
        assert m.place_type == "meditation_center"
        assert m.radius_km == 5.0


class TestReminderOption:
    def test_create(self):
        r = ReminderOption(text="Want a reminder this Saturday?", delay_hours=72)
        assert r.delay_hours == 72


class TestL2FulfillmentResult:
    def test_minimal(self):
        rec = Recommendation(
            title="Park", description="Quiet park",
            category="park", relevance_reason="calm", score=0.8,
        )
        result = L2FulfillmentResult(recommendations=[rec])
        assert len(result.recommendations) == 1
        assert result.map_data is None
        assert result.reminder_option is None

    def test_full_with_map_and_reminder(self):
        rec = Recommendation(
            title="Zen Garden", description="Traditional meditation space",
            category="meditation_center", relevance_reason="values: tradition",
            score=0.9, tags=["meditation", "quiet"],
        )
        result = L2FulfillmentResult(
            recommendations=[rec],
            map_data=MapData(place_type="meditation_center", radius_km=3.0),
            reminder_option=ReminderOption(
                text="Want a reminder this Saturday?", delay_hours=48,
            ),
        )
        assert result.map_data.radius_km == 3.0
        assert result.reminder_option.delay_hours == 48

    def test_empty_recommendations_rejected(self):
        with pytest.raises(Exception):
            L2FulfillmentResult(recommendations=[])
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_models.py -v`
Expected: FAIL — `ImportError: cannot import name 'L2FulfillmentResult'`

**Step 3: Write minimal implementation**

Add to `wish_engine/models.py` after `L1FulfillmentResult` (after line 131):

```python
class Recommendation(BaseModel):
    """A single L2 recommendation item."""

    title: str
    description: str
    category: str
    relevance_reason: str
    score: float = Field(ge=0.0, le=1.0)
    action_url: str | None = None
    tags: list[str] = Field(default_factory=list)


class MapData(BaseModel):
    """Map display data for place-based wishes."""

    place_type: str
    radius_km: float = Field(gt=0.0)


class ReminderOption(BaseModel):
    """Reminder suggestion for the user."""

    text: str
    delay_hours: int = Field(gt=0)


class L2FulfillmentResult(BaseModel):
    """Output of L2 fulfiller — personalized recommendations."""

    recommendations: list[Recommendation] = Field(min_length=1)
    map_data: MapData | None = None
    reminder_option: ReminderOption | None = None
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_models.py -v`
Expected: All 8 tests PASS

**Step 5: Commit**

```bash
git add wish_engine/models.py tests/test_l2_models.py
git commit -m "feat: add L2 output models (Recommendation, MapData, ReminderOption, L2FulfillmentResult)"
```

---

### Task 2: L2Fulfiller base class + personality filter + router

**Files:**
- Create: `wish_engine/l2_fulfiller.py`
- Test: `tests/test_l2_fulfiller.py` (create)

**Step 1: Write the failing test**

Create `tests/test_l2_fulfiller.py`:

```python
"""Tests for L2Fulfiller base class, personality filter, and router."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    Recommendation,
    WishLevel,
    WishType,
)
from wish_engine.l2_fulfiller import (
    L2Fulfiller,
    PersonalityFilter,
    fulfill_l2,
)


# ── PersonalityFilter ─────────────────────────────────────────────────────


class TestPersonalityFilter:
    """Test personality-based filtering of recommendation candidates."""

    def _make_candidate(self, **overrides) -> dict:
        base = {
            "title": "Test Place",
            "description": "A test",
            "category": "park",
            "tags": [],
            "noise": "quiet",
            "social": "low",
            "mood": "calming",
            "cognitive_style": "any",
        }
        base.update(overrides)
        return base

    def test_introvert_excludes_noisy(self):
        """MBTI(I) + introversion > 0.6 → exclude noisy places."""
        pf = PersonalityFilter(DetectorResults(
            mbti={"type": "INFJ", "dimensions": {"E_I": 0.3}},  # I = 0.7
        ))
        candidates = [
            self._make_candidate(title="Loud Bar", noise="loud", social="high"),
            self._make_candidate(title="Quiet Park", noise="quiet", social="low"),
        ]
        filtered = pf.apply(candidates)
        titles = [c["title"] for c in filtered]
        assert "Quiet Park" in titles
        assert "Loud Bar" not in titles

    def test_extrovert_keeps_noisy(self):
        """MBTI(E) → noisy places not excluded."""
        pf = PersonalityFilter(DetectorResults(
            mbti={"type": "ENFP", "dimensions": {"E_I": 0.8}},  # E = 0.8
        ))
        candidates = [
            self._make_candidate(title="Loud Bar", noise="loud", social="high"),
            self._make_candidate(title="Quiet Park", noise="quiet", social="low"),
        ]
        filtered = pf.apply(candidates)
        assert len(filtered) == 2

    def test_anxiety_excludes_high_stimulation(self):
        """emotion(anxiety) > 0.5 → exclude high-stimulation."""
        pf = PersonalityFilter(DetectorResults(
            emotion={"emotions": {"anxiety": 0.7}},
        ))
        candidates = [
            self._make_candidate(title="Intense Bootcamp", mood="intense"),
            self._make_candidate(title="Gentle Yoga", mood="calming"),
        ]
        filtered = pf.apply(candidates)
        titles = [c["title"] for c in filtered]
        assert "Gentle Yoga" in titles
        assert "Intense Bootcamp" not in titles

    def test_no_anxiety_keeps_intense(self):
        pf = PersonalityFilter(DetectorResults(
            emotion={"emotions": {"joy": 0.8}},
        ))
        candidates = [
            self._make_candidate(title="Intense Bootcamp", mood="intense"),
        ]
        assert len(pf.apply(candidates)) == 1

    def test_tradition_boosts_traditional(self):
        """values(tradition) → boost traditional items."""
        pf = PersonalityFilter(DetectorResults(
            values={"top_values": ["tradition", "conformity"]},
        ))
        candidates = [
            self._make_candidate(title="Traditional Meditation", tags=["traditional"]),
            self._make_candidate(title="Modern Mindfulness App", tags=["modern"]),
        ]
        scored = pf.score(candidates)
        trad = next(s for s in scored if s["title"] == "Traditional Meditation")
        modern = next(s for s in scored if s["title"] == "Modern Mindfulness App")
        assert trad["_personality_score"] > modern["_personality_score"]

    def test_self_direction_boosts_autonomous(self):
        """values(self-direction) → boost autonomous/independent items."""
        pf = PersonalityFilter(DetectorResults(
            values={"top_values": ["self-direction", "stimulation"]},
        ))
        candidates = [
            self._make_candidate(title="Self-Paced Course", tags=["self-paced", "autonomous"]),
            self._make_candidate(title="Structured Classroom", tags=["structured", "group"]),
        ]
        scored = pf.score(candidates)
        sp = next(s for s in scored if s["title"] == "Self-Paced Course")
        sc = next(s for s in scored if s["title"] == "Structured Classroom")
        assert sp["_personality_score"] > sc["_personality_score"]

    def test_empty_detector_results_passes_all(self):
        """No detector data → no filtering, no scoring changes."""
        pf = PersonalityFilter(DetectorResults())
        candidates = [self._make_candidate(), self._make_candidate(title="Another")]
        assert len(pf.apply(candidates)) == 2

    def test_defensive_fragility_excludes_confrontational(self):
        """fragility(defensive) → exclude confrontational recommendations."""
        pf = PersonalityFilter(DetectorResults(
            fragility={"pattern": "defensive"},
        ))
        candidates = [
            self._make_candidate(title="Assertiveness Workshop", mood="confrontational"),
            self._make_candidate(title="Gentle Journaling", mood="calming"),
        ]
        filtered = pf.apply(candidates)
        titles = [c["title"] for c in filtered]
        assert "Assertiveness Workshop" not in titles
        assert "Gentle Journaling" in titles


# ── Router ──────────────────────────────────────────────────────────────────


class TestFulfillL2Router:
    """Test that fulfill_l2 routes to the correct fulfiller."""

    def _make_wish(self, wish_type: WishType) -> ClassifiedWish:
        return ClassifiedWish(
            wish_text="test wish",
            wish_type=wish_type,
            level=WishLevel.L2,
            fulfillment_strategy="test",
        )

    def test_find_place_returns_result_with_map(self):
        wish = self._make_wish(WishType.FIND_PLACE)
        result = fulfill_l2(wish, DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert result.map_data is not None
        assert len(result.recommendations) >= 1

    def test_find_resource_returns_books(self):
        wish = self._make_wish(WishType.FIND_RESOURCE)
        result = fulfill_l2(wish, DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert any("book" in r.category or "resource" in r.category for r in result.recommendations)

    def test_learn_skill_returns_courses(self):
        wish = self._make_wish(WishType.LEARN_SKILL)
        result = fulfill_l2(wish, DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_career_direction_returns_result(self):
        wish = self._make_wish(WishType.CAREER_DIRECTION)
        result = fulfill_l2(wish, DetectorResults())
        assert isinstance(result, L2FulfillmentResult)

    def test_health_wellness_returns_result(self):
        wish = self._make_wish(WishType.HEALTH_WELLNESS)
        result = fulfill_l2(wish, DetectorResults())
        assert isinstance(result, L2FulfillmentResult)

    def test_l1_wish_raises(self):
        wish = ClassifiedWish(
            wish_text="test", wish_type=WishType.SELF_UNDERSTANDING,
            level=WishLevel.L1, fulfillment_strategy="test",
        )
        with pytest.raises(ValueError, match="L2"):
            fulfill_l2(wish, DetectorResults())

    def test_recommendations_are_personalized(self):
        """Introvert wish for place → quiet recommendations score higher."""
        wish = self._make_wish(WishType.FIND_PLACE)
        det = DetectorResults(
            mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}},
        )
        result = fulfill_l2(wish, det)
        # All returned recommendations should be introvert-friendly
        for rec in result.recommendations:
            assert "noisy" not in rec.tags

    def test_max_3_recommendations(self):
        wish = self._make_wish(WishType.FIND_PLACE)
        result = fulfill_l2(wish, DetectorResults())
        assert len(result.recommendations) <= 3

    def test_reminder_option_present_for_places(self):
        wish = self._make_wish(WishType.FIND_PLACE)
        result = fulfill_l2(wish, DetectorResults())
        assert result.reminder_option is not None
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_fulfiller.py -v`
Expected: FAIL — `ImportError: cannot import name 'L2Fulfiller'`

**Step 3: Write minimal implementation**

Create `wish_engine/l2_fulfiller.py`:

```python
"""L2 Fulfiller — local-compute recommendation engine with personality filtering.

Routes L2 wishes to domain-specific fulfillers. Each fulfiller has a curated
knowledge base and applies personality-based filtering. Zero LLM.

5 fulfillment types:
  a) Place search (parks, cafés, meditation centers, gyms)
  b) Book recommendation (values + MBTI matching)
  c) Course recommendation (cognitive style matching)
  d) Career direction (values + MBTI career mapping)
  e) Wellness recommendation (emotion + fragility matching)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    Recommendation,
    ReminderOption,
    WishLevel,
    WishType,
)


# ── Personality Filter (local-compute, zero LLM) ────────────────────────────


class PersonalityFilter:
    """Applies personality-based filtering and scoring to recommendation candidates.

    Hard filters (exclude):
      - MBTI I + introversion > 0.6 → exclude noisy/crowded
      - emotion anxiety > 0.5 → exclude high-stimulation
      - fragility defensive → exclude confrontational

    Soft filters (score boost):
      - values tradition → boost traditional
      - values self-direction → boost autonomous
      - attachment anxious → boost calming/structured
      - MBTI N → boost theory-heavy
      - MBTI S → boost practical/hands-on
    """

    def __init__(self, detector_results: DetectorResults):
        self._det = detector_results

    # ── Extracted traits ──────────────────────────────────────────────────

    @property
    def _is_introvert(self) -> bool:
        mbti = self._det.mbti
        if not mbti.get("type"):
            return False
        ei = mbti.get("dimensions", {}).get("E_I", 0.5)
        return ei < 0.4  # low E_I = introverted

    @property
    def _anxiety_level(self) -> float:
        return self._det.emotion.get("emotions", {}).get("anxiety", 0.0)

    @property
    def _fragility_pattern(self) -> str:
        return self._det.fragility.get("pattern", "")

    @property
    def _top_values(self) -> list[str]:
        return self._det.values.get("top_values", [])

    @property
    def _mbti_type(self) -> str:
        return self._det.mbti.get("type", "")

    @property
    def _attachment_style(self) -> str:
        return self._det.attachment.get("style", "")

    # ── Hard filters ──────────────────────────────────────────────────────

    def apply(self, candidates: list[dict]) -> list[dict]:
        """Apply hard exclusion filters. Returns surviving candidates."""
        result = []
        for c in candidates:
            if self._is_introvert and c.get("noise") == "loud" and c.get("social") == "high":
                continue
            if self._anxiety_level > 0.5 and c.get("mood") == "intense":
                continue
            if self._fragility_pattern == "defensive" and c.get("mood") == "confrontational":
                continue
            result.append(c)
        return result

    # ── Soft scoring ──────────────────────────────────────────────────────

    def score(self, candidates: list[dict]) -> list[dict]:
        """Add _personality_score to each candidate based on trait alignment."""
        for c in candidates:
            s = 0.5  # base score
            tags = set(c.get("tags", []))

            # Values boosts
            if "tradition" in self._top_values and "traditional" in tags:
                s += 0.15
            if "self-direction" in self._top_values and ("self-paced" in tags or "autonomous" in tags):
                s += 0.15
            if "benevolence" in self._top_values and "helping" in tags:
                s += 0.10

            # MBTI cognitive style
            if len(self._mbti_type) == 4:
                if self._mbti_type[1] == "N" and "theory" in tags:
                    s += 0.10
                if self._mbti_type[1] == "S" and "practical" in tags:
                    s += 0.10
                if self._mbti_type[0] == "I" and "quiet" in tags:
                    s += 0.10
                if self._mbti_type[0] == "E" and "social" in tags:
                    s += 0.10

            # Attachment
            if self._attachment_style == "anxious" and "calming" in tags:
                s += 0.10

            # Calming bonus for anxious users
            if self._anxiety_level > 0.5 and "calming" in tags:
                s += 0.10

            c["_personality_score"] = min(s, 1.0)
        return candidates

    def filter_and_rank(self, candidates: list[dict], max_results: int = 3) -> list[dict]:
        """Apply hard filter, score, sort descending, return top N."""
        filtered = self.apply(candidates)
        scored = self.score(filtered)
        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        return scored[:max_results]


# ── L2Fulfiller ABC ──────────────────────────────────────────────────────────


class L2Fulfiller(ABC):
    """Base class for L2 domain-specific fulfillers."""

    @abstractmethod
    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        """Generate personalized recommendations for the wish."""
        ...

    def _build_recommendations(
        self,
        candidates: list[dict],
        detector_results: DetectorResults,
        max_results: int = 3,
    ) -> list[Recommendation]:
        """Filter, score, and convert candidates to Recommendation models."""
        pf = PersonalityFilter(detector_results)
        ranked = pf.filter_and_rank(candidates, max_results=max_results)
        return [
            Recommendation(
                title=c["title"],
                description=c["description"],
                category=c["category"],
                relevance_reason=c.get("relevance_reason", "Matches your profile"),
                score=c.get("_personality_score", 0.5),
                action_url=c.get("action_url"),
                tags=c.get("tags", []),
            )
            for c in ranked
        ]


# ── Lazy imports for concrete fulfillers (avoid circular) ────────────────────


def _get_fulfiller(wish_type: WishType) -> L2Fulfiller:
    """Get the fulfiller instance for a wish type."""
    from wish_engine.l2_places import PlaceFulfiller
    from wish_engine.l2_books import BookFulfiller
    from wish_engine.l2_courses import CourseFulfiller
    from wish_engine.l2_career import CareerFulfiller
    from wish_engine.l2_wellness import WellnessFulfiller

    _FULFILLER_MAP: dict[WishType, L2Fulfiller] = {
        WishType.FIND_PLACE: PlaceFulfiller(),
        WishType.FIND_RESOURCE: BookFulfiller(),
        WishType.LEARN_SKILL: CourseFulfiller(),
        WishType.CAREER_DIRECTION: CareerFulfiller(),
        WishType.HEALTH_WELLNESS: WellnessFulfiller(),
    }
    fulfiller = _FULFILLER_MAP.get(wish_type)
    if not fulfiller:
        raise ValueError(f"No L2 fulfiller for wish type: {wish_type}")
    return fulfiller


# ── Public router ────────────────────────────────────────────────────────────


def fulfill_l2(
    wish: ClassifiedWish,
    detector_results: DetectorResults,
) -> L2FulfillmentResult:
    """Route an L2 wish to the appropriate fulfiller and return recommendations.

    Zero LLM — all local-compute with curated knowledge bases.

    Args:
        wish: Classified wish (must be L2 level).
        detector_results: All 16 detector results for personality filtering.

    Returns:
        L2FulfillmentResult with personalized recommendations.

    Raises:
        ValueError: If wish is not L2 level.
    """
    if wish.level != WishLevel.L2:
        raise ValueError(f"L2Fulfiller only handles L2 wishes, got {wish.level}")

    fulfiller = _get_fulfiller(wish.wish_type)
    return fulfiller.fulfill(wish, detector_results)
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_fulfiller.py -v`
Expected: FAIL — concrete fulfillers don't exist yet. Tests for PersonalityFilter and router-error should pass. Other router tests will fail.

> **Note:** This task creates the base + filter + router. Tests for routing will pass after Tasks 3-7. For now, run only filter tests:
> `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_fulfiller.py::TestPersonalityFilter -v`
> Expected: 9 PASS

**Step 5: Commit**

```bash
git add wish_engine/l2_fulfiller.py tests/test_l2_fulfiller.py
git commit -m "feat: add L2Fulfiller base class, PersonalityFilter, and router"
```

---

### Task 3: PlaceFulfiller — find places (meditation, parks, cafés, gyms)

**Files:**
- Create: `wish_engine/l2_places.py`
- Test: `tests/test_l2_places.py` (create)

**Step 1: Write the failing test**

Create `tests/test_l2_places.py`:

```python
"""Tests for PlaceFulfiller — place search with personality filtering."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_places import PlaceFulfiller, PLACE_CATALOG


class TestPlaceCatalog:
    def test_catalog_not_empty(self):
        assert len(PLACE_CATALOG) >= 20

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for place in PLACE_CATALOG:
            missing = required - set(place.keys())
            assert not missing, f"{place['title']} missing: {missing}"

    def test_noise_values_valid(self):
        for place in PLACE_CATALOG:
            assert place["noise"] in ("quiet", "moderate", "loud"), place["title"]

    def test_social_values_valid(self):
        for place in PLACE_CATALOG:
            assert place["social"] in ("low", "medium", "high"), place["title"]


class TestPlaceFulfiller:
    def _make_wish(self, text="想找个安静的地方") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="place_search",
        )

    def test_returns_l2_result(self):
        f = PlaceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1
        assert len(result.recommendations) <= 3

    def test_has_map_data(self):
        f = PlaceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.radius_km > 0

    def test_has_reminder(self):
        f = PlaceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_introvert_no_noisy_places(self):
        f = PlaceFulfiller()
        det = DetectorResults(mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        for rec in result.recommendations:
            assert "noisy" not in rec.tags
            assert "loud" not in rec.tags

    def test_anxiety_no_intense_places(self):
        f = PlaceFulfiller()
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.8}})
        result = f.fulfill(self._make_wish(), det)
        for rec in result.recommendations:
            assert "intense" not in rec.tags

    def test_meditation_wish_finds_meditation(self):
        f = PlaceFulfiller()
        result = f.fulfill(self._make_wish("想学冥想"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert any("meditation" in c for c in categories)

    def test_exercise_wish_finds_fitness(self):
        f = PlaceFulfiller()
        result = f.fulfill(self._make_wish("想多运动"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert any(c in ("gym", "fitness_studio", "park", "swimming_pool") for c in categories)

    def test_quiet_wish_finds_quiet_places(self):
        f = PlaceFulfiller()
        result = f.fulfill(self._make_wish("想找个安静地方待会儿"), DetectorResults())
        for rec in result.recommendations:
            assert any(t in rec.tags for t in ["quiet", "peaceful", "calming"])
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_places.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'wish_engine.l2_places'`

**Step 3: Write minimal implementation**

Create `wish_engine/l2_places.py`:

```python
"""PlaceFulfiller — finds places matching user wishes with personality filtering.

Curated catalog of ~30 place types. Keyword matching on wish text to select
relevant place categories, then personality filter ranks results.
Zero LLM.
"""

from __future__ import annotations

import re
from typing import Any

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    ReminderOption,
)

# ── Place catalog ────────────────────────────────────────────────────────────

PLACE_CATALOG: list[dict[str, Any]] = [
    # Meditation & mindfulness
    {"title": "Meditation Center", "description": "Guided meditation sessions in a peaceful environment", "category": "meditation_center", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["meditation", "quiet", "calming", "traditional", "mindfulness"]},
    {"title": "Zen Garden", "description": "Traditional Japanese garden for contemplation", "category": "meditation_center", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["meditation", "quiet", "calming", "traditional", "nature"]},
    {"title": "Mindfulness Studio", "description": "Modern mindfulness and breathing workshops", "category": "meditation_center", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["meditation", "quiet", "calming", "modern", "mindfulness"]},
    # Parks & nature
    {"title": "City Park", "description": "Green space with walking trails and benches", "category": "park", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["nature", "quiet", "peaceful", "walking", "calming"]},
    {"title": "Botanical Garden", "description": "Curated gardens with quiet pathways", "category": "park", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["nature", "quiet", "peaceful", "calming", "beautiful"]},
    {"title": "Riverside Trail", "description": "Scenic trail along the river, ideal for reflective walks", "category": "park", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["nature", "quiet", "walking", "peaceful", "calming"]},
    {"title": "Community Garden", "description": "Shared garden space for planting and relaxation", "category": "park", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["nature", "quiet", "calming", "social", "hands-on"]},
    # Cafés & quiet spaces
    {"title": "Quiet Café", "description": "Low-noise café with comfortable seating and books", "category": "cafe", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "calming", "reading", "coffee"]},
    {"title": "Library Reading Room", "description": "Silent reading space with natural light", "category": "library", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "reading", "peaceful", "calming", "study"]},
    {"title": "Bookshop Café", "description": "Bookshop with attached café area", "category": "cafe", "noise": "moderate", "social": "low", "mood": "calming", "tags": ["quiet", "reading", "coffee", "calming"]},
    {"title": "Co-working Space", "description": "Quiet workspace with focus zones", "category": "coworking", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["quiet", "productive", "work", "social"]},
    # Fitness & exercise
    {"title": "Yoga Studio", "description": "Small group yoga classes in calm environment", "category": "yoga_studio", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["exercise", "quiet", "calming", "yoga", "small-group"]},
    {"title": "Fitness Gym", "description": "Full-service gym with equipment and classes", "category": "gym", "noise": "loud", "social": "high", "mood": "intense", "tags": ["exercise", "noisy", "intense", "equipment", "social"]},
    {"title": "Swimming Pool", "description": "Indoor pool for lap swimming", "category": "swimming_pool", "noise": "moderate", "social": "low", "mood": "calming", "tags": ["exercise", "swimming", "quiet", "calming", "solo"]},
    {"title": "Running Track", "description": "Outdoor track for jogging and running", "category": "park", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["exercise", "running", "outdoor", "quiet", "solo", "calming"]},
    {"title": "Rock Climbing Gym", "description": "Indoor climbing with beginner to advanced routes", "category": "gym", "noise": "moderate", "social": "medium", "mood": "intense", "tags": ["exercise", "climbing", "practical", "challenging"]},
    {"title": "Dance Studio", "description": "Group dance classes in various styles", "category": "fitness_studio", "noise": "loud", "social": "high", "mood": "intense", "tags": ["exercise", "noisy", "social", "dance", "fun"]},
    {"title": "Pilates Studio", "description": "Small-group pilates with personal attention", "category": "fitness_studio", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["exercise", "quiet", "calming", "small-group", "gentle"]},
    # Art & creative
    {"title": "Art Studio Workshop", "description": "Open studio with painting and drawing supplies", "category": "art_studio", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["creative", "quiet", "painting", "hands-on", "calming"]},
    {"title": "Pottery Workshop", "description": "Hands-on ceramics classes", "category": "art_studio", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["creative", "quiet", "pottery", "hands-on", "practical", "calming"]},
    {"title": "Music Practice Room", "description": "Soundproof rooms for instrument practice", "category": "music_studio", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["music", "quiet", "solo", "practice", "calming"]},
    # Therapy & healing
    {"title": "Counseling Center", "description": "Professional counselors and therapists", "category": "therapy_center", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["therapy", "quiet", "calming", "professional", "healing"]},
    {"title": "Art Therapy Studio", "description": "Therapeutic art sessions guided by professionals", "category": "therapy_center", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["therapy", "creative", "quiet", "calming", "healing"]},
    {"title": "Spa & Wellness Center", "description": "Massage, sauna, and relaxation treatments", "category": "spa", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["relaxation", "quiet", "calming", "self-care"]},
    # Social & community
    {"title": "Community Center", "description": "Local community events and meetups", "category": "community_center", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["social", "community", "events", "group"]},
    {"title": "Board Game Café", "description": "Café with board games for groups", "category": "cafe", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["social", "fun", "games", "group"]},
    {"title": "Dog Park", "description": "Off-leash area for dogs and their owners", "category": "park", "noise": "moderate", "social": "medium", "mood": "calming", "tags": ["nature", "pets", "social", "outdoor", "calming"]},
    # Dining
    {"title": "Quiet Restaurant", "description": "Intimate dining with low noise", "category": "restaurant", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["dining", "quiet", "calming", "date"]},
    {"title": "Lively Restaurant", "description": "Energetic atmosphere with live music", "category": "restaurant", "noise": "loud", "social": "high", "mood": "intense", "tags": ["dining", "noisy", "social", "fun", "loud"]},
]

# ── Keyword → category mapping for wish text matching ────────────────────────

_WISH_KEYWORDS: dict[str, list[str]] = {
    "meditation": ["meditation_center"],
    "冥想": ["meditation_center"],
    "تأمل": ["meditation_center"],
    "mindfulness": ["meditation_center"],
    "正念": ["meditation_center"],
    "yoga": ["yoga_studio", "fitness_studio"],
    "瑜伽": ["yoga_studio", "fitness_studio"],
    "exercise": ["gym", "fitness_studio", "park", "swimming_pool"],
    "运动": ["gym", "fitness_studio", "park", "swimming_pool"],
    "رياضة": ["gym", "fitness_studio", "park", "swimming_pool"],
    "gym": ["gym", "fitness_studio"],
    "健身": ["gym", "fitness_studio"],
    "swim": ["swimming_pool"],
    "游泳": ["swimming_pool"],
    "run": ["park"],
    "跑步": ["park"],
    "quiet": ["park", "cafe", "library"],
    "安静": ["park", "cafe", "library"],
    "هادئ": ["park", "cafe", "library"],
    "park": ["park"],
    "公园": ["park"],
    "café": ["cafe"],
    "咖啡": ["cafe"],
    "book": ["library", "cafe"],
    "library": ["library"],
    "图书馆": ["library"],
    "art": ["art_studio"],
    "画画": ["art_studio"],
    "pottery": ["art_studio"],
    "therapy": ["therapy_center"],
    "咨询": ["therapy_center"],
    "spa": ["spa"],
    "massage": ["spa"],
    "restaurant": ["restaurant"],
    "吃饭": ["restaurant"],
    "dining": ["restaurant"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract target categories from wish text via keyword matching."""
    text_lower = wish_text.lower()
    matched: set[str] = set()
    for keyword, categories in _WISH_KEYWORDS.items():
        if keyword in text_lower:
            matched.update(categories)
    return list(matched) if matched else []  # empty = all categories


class PlaceFulfiller(L2Fulfiller):
    """Finds places matching user wishes with personality-based filtering."""

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # Match categories from wish text
        target_cats = _match_categories(wish.wish_text)

        # Filter catalog by category
        if target_cats:
            candidates = [p for p in PLACE_CATALOG if p["category"] in target_cats]
        else:
            candidates = list(PLACE_CATALOG)

        # If no matches found for specific categories, fall back to full catalog
        if not candidates:
            candidates = list(PLACE_CATALOG)

        # Personality filter + rank
        recs = self._build_recommendations(candidates, detector_results, max_results=3)

        # Determine primary place type for map
        primary_category = recs[0].category if recs else "park"

        return L2FulfillmentResult(
            recommendations=recs,
            map_data=MapData(place_type=primary_category, radius_km=5.0),
            reminder_option=ReminderOption(
                text="Want a reminder to visit this weekend?",
                delay_hours=48,
            ),
        )
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_places.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add wish_engine/l2_places.py tests/test_l2_places.py
git commit -m "feat: add PlaceFulfiller with 28-place catalog and keyword matching"
```

---

### Task 4: BookFulfiller — book recommendations based on values + MBTI

**Files:**
- Create: `wish_engine/l2_books.py`
- Test: `tests/test_l2_books.py` (create)

**Step 1: Write the failing test**

Create `tests/test_l2_books.py`:

```python
"""Tests for BookFulfiller — book recommendations with personality matching."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_books import BookFulfiller, BOOK_CATALOG


class TestBookCatalog:
    def test_catalog_not_empty(self):
        assert len(BOOK_CATALOG) >= 30

    def test_each_entry_has_required_fields(self):
        required = {"title", "author", "description", "category", "topic", "tags"}
        for book in BOOK_CATALOG:
            missing = required - set(book.keys())
            assert not missing, f"{book['title']} missing: {missing}"


class TestBookFulfiller:
    def _make_wish(self, text="想读一本关于心理学的书") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="resource_recommendation",
        )

    def test_returns_l2_result(self):
        f = BookFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_no_map_data(self):
        """Books don't need map data."""
        f = BookFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None

    def test_attachment_wish_finds_attachment_books(self):
        f = BookFulfiller()
        result = f.fulfill(self._make_wish("想了解依恋理论"), DetectorResults())
        topics = []
        for r in result.recommendations:
            topics.extend(r.tags)
        assert any("attachment" in t for t in topics)

    def test_meditation_wish_finds_mindfulness_books(self):
        f = BookFulfiller()
        result = f.fulfill(self._make_wish("想学冥想"), DetectorResults())
        topics = []
        for r in result.recommendations:
            topics.extend(r.tags)
        assert any(t in ("meditation", "mindfulness") for t in topics)

    def test_tradition_values_boost_traditional_books(self):
        f = BookFulfiller()
        det = DetectorResults(values={"top_values": ["tradition"]})
        result = f.fulfill(self._make_wish("想了解冥想"), det)
        # Traditional books should score higher
        assert any("traditional" in r.tags for r in result.recommendations)

    def test_max_3_recommendations(self):
        f = BookFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_reminder(self):
        f = BookFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_mentions_profile(self):
        f = BookFulfiller()
        det = DetectorResults(attachment={"style": "anxious"})
        result = f.fulfill(self._make_wish("想了解依恋"), det)
        # At least one recommendation should have a profile-based reason
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any(len(r) > 10 for r in reasons)
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_books.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `wish_engine/l2_books.py`:

```python
"""BookFulfiller — book recommendations based on values, MBTI, and wish topic.

Curated catalog of ~40 books spanning psychology, self-help, mindfulness,
relationships, career, and wellness. Keyword matching + personality filter.
Zero LLM.
"""

from __future__ import annotations

from typing import Any

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Book catalog ─────────────────────────────────────────────────────────────

BOOK_CATALOG: list[dict[str, Any]] = [
    # Attachment theory
    {"title": "Attached", "author": "Amir Levine & Rachel Heller", "description": "Understand your attachment style and how it affects your relationships", "category": "book", "topic": "attachment", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["attachment", "relationships", "psychology", "practical", "self-help"]},
    {"title": "Hold Me Tight", "author": "Sue Johnson", "description": "Emotionally focused therapy for couples", "category": "book", "topic": "attachment", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["attachment", "relationships", "couples", "therapy", "practical"]},
    {"title": "Wired for Love", "author": "Stan Tatkin", "description": "Create a thriving relationship using neuroscience", "category": "book", "topic": "attachment", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["attachment", "neuroscience", "relationships", "practical"]},
    # Mindfulness & meditation
    {"title": "Mindfulness in Plain English", "author": "Bhante Gunaratana", "description": "Classic guide to Vipassana meditation", "category": "book", "topic": "meditation", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["meditation", "mindfulness", "traditional", "beginner", "calming"]},
    {"title": "The Miracle of Mindfulness", "author": "Thich Nhat Hanh", "description": "Gentle introduction to mindfulness practice", "category": "book", "topic": "meditation", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["meditation", "mindfulness", "traditional", "gentle", "calming"]},
    {"title": "Wherever You Go, There You Are", "author": "Jon Kabat-Zinn", "description": "Mindfulness meditation in everyday life", "category": "book", "topic": "meditation", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["meditation", "mindfulness", "modern", "practical", "calming"]},
    {"title": "10% Happier", "author": "Dan Harris", "description": "A skeptic's journey into meditation", "category": "book", "topic": "meditation", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["meditation", "mindfulness", "modern", "humor", "beginner"]},
    # Psychology & self-understanding
    {"title": "Thinking, Fast and Slow", "author": "Daniel Kahneman", "description": "How two systems in your mind drive the way you think", "category": "book", "topic": "psychology", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["psychology", "cognitive", "theory", "science"]},
    {"title": "The Body Keeps the Score", "author": "Bessel van der Kolk", "description": "How trauma reshapes body and brain", "category": "book", "topic": "psychology", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["psychology", "trauma", "healing", "neuroscience", "therapy"]},
    {"title": "Quiet", "author": "Susan Cain", "description": "The power of introverts in a world that can't stop talking", "category": "book", "topic": "psychology", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["psychology", "introvert", "quiet", "self-understanding"]},
    {"title": "Gifts Differing", "author": "Isabel Briggs Myers", "description": "Understanding personality types through MBTI", "category": "book", "topic": "psychology", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["psychology", "mbti", "personality", "theory", "self-understanding"]},
    {"title": "Emotional Intelligence", "author": "Daniel Goleman", "description": "Why EQ matters more than IQ", "category": "book", "topic": "psychology", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["psychology", "eq", "emotions", "self-understanding", "practical"]},
    # Relationships & conflict
    {"title": "Nonviolent Communication", "author": "Marshall Rosenberg", "description": "A language of compassion for resolving conflicts", "category": "book", "topic": "conflict", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["conflict", "communication", "relationships", "practical", "calming"]},
    {"title": "Crucial Conversations", "author": "Patterson et al.", "description": "Tools for talking when stakes are high", "category": "book", "topic": "conflict", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["conflict", "communication", "practical", "assertive"]},
    {"title": "The Seven Principles for Making Marriage Work", "author": "John Gottman", "description": "Research-based guide to a successful relationship", "category": "book", "topic": "relationships", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["relationships", "couples", "practical", "research"]},
    {"title": "The Five Love Languages", "author": "Gary Chapman", "description": "Understand how you and your partner express love", "category": "book", "topic": "relationships", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["relationships", "love-language", "practical", "couples"]},
    # Self-help & growth
    {"title": "Atomic Habits", "author": "James Clear", "description": "Tiny changes, remarkable results", "category": "book", "topic": "growth", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["habits", "growth", "practical", "self-help", "autonomous"]},
    {"title": "The Subtle Art of Not Giving a F*ck", "author": "Mark Manson", "description": "A counterintuitive approach to living a good life", "category": "book", "topic": "growth", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["growth", "values", "modern", "humor", "self-direction"]},
    {"title": "Man's Search for Meaning", "author": "Viktor Frankl", "description": "Finding purpose through suffering", "category": "book", "topic": "growth", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["meaning", "growth", "philosophy", "traditional", "deep"]},
    {"title": "Daring Greatly", "author": "Brené Brown", "description": "The power of vulnerability", "category": "book", "topic": "growth", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["vulnerability", "growth", "courage", "self-understanding", "calming"]},
    {"title": "The Gifts of Imperfection", "author": "Brené Brown", "description": "Letting go of who you think you should be", "category": "book", "topic": "growth", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["self-acceptance", "growth", "gentle", "calming"]},
    # Career & purpose
    {"title": "Designing Your Life", "author": "Bill Burnett & Dave Evans", "description": "Design thinking for building a joyful life", "category": "book", "topic": "career", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["career", "purpose", "practical", "design-thinking", "self-direction"]},
    {"title": "So Good They Can't Ignore You", "author": "Cal Newport", "description": "Why skills trump passion in the quest for work you love", "category": "book", "topic": "career", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["career", "skills", "practical", "theory"]},
    {"title": "Range", "author": "David Epstein", "description": "Why generalists triumph in a specialized world", "category": "book", "topic": "career", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["career", "growth", "theory", "exploration"]},
    # Anxiety & emotional regulation
    {"title": "The Anxiety and Phobia Workbook", "author": "Edmund Bourne", "description": "Step-by-step program for managing anxiety", "category": "book", "topic": "anxiety", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["anxiety", "therapy", "practical", "workbook", "calming"]},
    {"title": "Feeling Good", "author": "David Burns", "description": "CBT techniques for mood management", "category": "book", "topic": "anxiety", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["anxiety", "depression", "cbt", "practical", "therapy", "calming"]},
    {"title": "Self-Compassion", "author": "Kristin Neff", "description": "The proven power of being kind to yourself", "category": "book", "topic": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["self-compassion", "wellness", "gentle", "calming", "healing"]},
    # Creativity
    {"title": "The Artist's Way", "author": "Julia Cameron", "description": "A spiritual path to higher creativity", "category": "book", "topic": "creativity", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["creativity", "art", "self-expression", "self-paced", "autonomous"]},
    {"title": "Big Magic", "author": "Elizabeth Gilbert", "description": "Creative living beyond fear", "category": "book", "topic": "creativity", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["creativity", "courage", "growth", "inspiring"]},
    # Philosophy & meaning
    {"title": "Meditations", "author": "Marcus Aurelius", "description": "Stoic philosophy for daily life", "category": "book", "topic": "philosophy", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["philosophy", "stoic", "traditional", "meaning", "deep"]},
    {"title": "The Tao of Pooh", "author": "Benjamin Hoff", "description": "Taoism explained through Winnie the Pooh", "category": "book", "topic": "philosophy", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["philosophy", "taoism", "traditional", "gentle", "humor", "calming"]},
    {"title": "When Things Fall Apart", "author": "Pema Chödrön", "description": "Heart advice for difficult times", "category": "book", "topic": "philosophy", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["philosophy", "buddhism", "traditional", "healing", "calming", "gentle"]},
]

# ── Keyword → topic mapping ──────────────────────────────────────────────────

_BOOK_KEYWORDS: dict[str, list[str]] = {
    "attachment": ["attachment"],
    "依恋": ["attachment"],
    "تعلق": ["attachment"],
    "meditation": ["meditation"],
    "冥想": ["meditation"],
    "تأمل": ["meditation"],
    "mindfulness": ["meditation"],
    "正念": ["meditation"],
    "anxiety": ["anxiety"],
    "焦虑": ["anxiety"],
    "قلق": ["anxiety"],
    "conflict": ["conflict"],
    "冲突": ["conflict"],
    "relationship": ["relationships", "attachment"],
    "关系": ["relationships", "attachment"],
    "career": ["career"],
    "职业": ["career"],
    "工作": ["career"],
    "psychology": ["psychology"],
    "心理": ["psychology", "anxiety"],
    "growth": ["growth"],
    "成长": ["growth"],
    "emotion": ["psychology", "anxiety"],
    "情绪": ["psychology", "anxiety"],
    "creativity": ["creativity"],
    "创造": ["creativity"],
    "art": ["creativity"],
    "philosophy": ["philosophy"],
    "哲学": ["philosophy"],
    "meaning": ["philosophy", "growth"],
    "意义": ["philosophy", "growth"],
    "book": [],  # generic — return all
    "书": [],
    "read": [],
    "读": [],
}


def _match_topics(wish_text: str) -> list[str]:
    """Extract target book topics from wish text via keyword matching."""
    text_lower = wish_text.lower()
    matched: set[str] = set()
    for keyword, topics in _BOOK_KEYWORDS.items():
        if keyword in text_lower:
            matched.update(topics)
    return list(matched)


class BookFulfiller(L2Fulfiller):
    """Recommends books based on wish topic and personality profile."""

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        target_topics = _match_topics(wish.wish_text)

        if target_topics:
            candidates = [b for b in BOOK_CATALOG if b["topic"] in target_topics]
        else:
            candidates = list(BOOK_CATALOG)

        if not candidates:
            candidates = list(BOOK_CATALOG)

        # Add relevance_reason based on profile
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, detector_results)

        recs = self._build_recommendations(candidates, detector_results, max_results=3)

        return L2FulfillmentResult(
            recommendations=recs,
            map_data=None,  # books don't need a map
            reminder_option=ReminderOption(
                text="Want a reminder to start reading this week?",
                delay_hours=24,
            ),
        )


def _build_relevance_reason(book: dict, det: DetectorResults) -> str:
    """Build a personalized relevance reason based on detector results."""
    reasons: list[str] = []

    attachment = det.attachment.get("style", "")
    if attachment and "attachment" in book.get("tags", []):
        reasons.append(f"Relevant to your {attachment} attachment style")

    top_values = det.values.get("top_values", [])
    book_tags = set(book.get("tags", []))
    for v in top_values:
        if v in book_tags or v.replace("-", "_") in book_tags:
            reasons.append(f"Aligns with your values: {v}")
            break

    mbti = det.mbti.get("type", "")
    if mbti and "introvert" in book_tags and mbti.startswith("I"):
        reasons.append("Written for introverts like you")

    if not reasons:
        reasons.append(f"Recommended for {book.get('topic', 'personal growth')}")

    return ". ".join(reasons)
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_books.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add wish_engine/l2_books.py tests/test_l2_books.py
git commit -m "feat: add BookFulfiller with 32-book catalog and topic matching"
```

---

### Task 5: CourseFulfiller — course recommendations based on cognitive style

**Files:**
- Create: `wish_engine/l2_courses.py`
- Test: `tests/test_l2_courses.py` (create)

**Step 1: Write the failing test**

Create `tests/test_l2_courses.py`:

```python
"""Tests for CourseFulfiller — course recommendations with cognitive style matching."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_courses import CourseFulfiller, COURSE_CATALOG


class TestCourseCatalog:
    def test_catalog_not_empty(self):
        assert len(COURSE_CATALOG) >= 25

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "topic", "format", "tags"}
        for course in COURSE_CATALOG:
            missing = required - set(course.keys())
            assert not missing, f"{course['title']} missing: {missing}"


class TestCourseFulfiller:
    def _make_wish(self, text="想学心理学") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.LEARN_SKILL,
            level=WishLevel.L2, fulfillment_strategy="course_recommendation",
        )

    def test_returns_l2_result(self):
        f = CourseFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_intuitive_gets_theory_courses(self):
        """MBTI N type → theory-heavy courses boosted."""
        f = CourseFulfiller()
        det = DetectorResults(mbti={"type": "INTJ", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        assert any("theory" in r.tags for r in result.recommendations)

    def test_sensing_gets_practical_courses(self):
        """MBTI S type → practical courses boosted."""
        f = CourseFulfiller()
        det = DetectorResults(mbti={"type": "ISTJ", "dimensions": {"E_I": 0.3}})
        result = f.fulfill(self._make_wish(), det)
        assert any("practical" in r.tags for r in result.recommendations)

    def test_introvert_prefers_self_paced(self):
        f = CourseFulfiller()
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        assert any("self-paced" in r.tags for r in result.recommendations)

    def test_programming_wish(self):
        f = CourseFulfiller()
        result = f.fulfill(self._make_wish("想学编程"), DetectorResults())
        topics = []
        for r in result.recommendations:
            topics.extend(r.tags)
        assert any(t in ("programming", "coding", "tech") for t in topics)

    def test_max_3(self):
        f = CourseFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_reminder(self):
        f = CourseFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_courses.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `wish_engine/l2_courses.py`:

```python
"""CourseFulfiller — course recommendations based on cognitive style and interests.

Curated catalog of ~30 courses. MBTI cognitive style determines whether to
recommend theory-heavy or practical courses. Introversion prefers self-paced.
Zero LLM.
"""

from __future__ import annotations

from typing import Any

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Course catalog ───────────────────────────────────────────────────────────

COURSE_CATALOG: list[dict[str, Any]] = [
    # Psychology
    {"title": "Introduction to Psychology", "description": "Comprehensive overview of psychology fundamentals", "category": "course", "topic": "psychology", "format": "video", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["psychology", "theory", "self-paced", "beginner"]},
    {"title": "Practical Psychology for Everyday Life", "description": "Apply psychology concepts to daily situations", "category": "course", "topic": "psychology", "format": "interactive", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["psychology", "practical", "self-paced", "applied"]},
    {"title": "Understanding Emotions", "description": "Science of emotions and emotional regulation", "category": "course", "topic": "psychology", "format": "video", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["psychology", "emotions", "theory", "self-paced", "calming"]},
    {"title": "Group Psychology Workshop", "description": "Interactive group sessions exploring human behavior", "category": "course", "topic": "psychology", "format": "group", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["psychology", "practical", "social", "group", "interactive"]},
    # Meditation & mindfulness
    {"title": "Mindfulness-Based Stress Reduction (MBSR)", "description": "8-week MBSR program with daily practice", "category": "course", "topic": "meditation", "format": "guided", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["meditation", "mindfulness", "traditional", "self-paced", "calming", "practical"]},
    {"title": "Science of Meditation", "description": "Neuroscience behind meditation practices", "category": "course", "topic": "meditation", "format": "video", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["meditation", "theory", "neuroscience", "self-paced"]},
    {"title": "Group Meditation Circle", "description": "Weekly guided meditation with community", "category": "course", "topic": "meditation", "format": "group", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["meditation", "social", "group", "calming", "traditional"]},
    # Programming & tech
    {"title": "Python for Beginners", "description": "Learn Python programming from scratch", "category": "course", "topic": "programming", "format": "interactive", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["programming", "coding", "tech", "practical", "self-paced", "beginner"]},
    {"title": "Computer Science Theory", "description": "Algorithms, data structures, and computational thinking", "category": "course", "topic": "programming", "format": "video", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["programming", "coding", "tech", "theory", "self-paced"]},
    {"title": "Web Development Bootcamp", "description": "Intensive full-stack web development", "category": "course", "topic": "programming", "format": "bootcamp", "noise": "moderate", "social": "high", "mood": "intense", "tags": ["programming", "coding", "tech", "practical", "social", "intensive"]},
    # Art & creativity
    {"title": "Drawing Fundamentals", "description": "Learn to draw from observation", "category": "course", "topic": "art", "format": "video", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["art", "drawing", "practical", "self-paced", "creative", "calming"]},
    {"title": "Watercolor Painting", "description": "Watercolor techniques for beginners", "category": "course", "topic": "art", "format": "video", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["art", "painting", "practical", "self-paced", "creative", "calming"]},
    {"title": "Art History Survey", "description": "Journey through art movements and masterpieces", "category": "course", "topic": "art", "format": "video", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["art", "theory", "history", "self-paced"]},
    {"title": "Community Art Workshop", "description": "Create art together in group sessions", "category": "course", "topic": "art", "format": "group", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["art", "creative", "social", "group", "hands-on"]},
    # Language
    {"title": "Arabic for Beginners", "description": "Learn conversational Arabic with structured lessons", "category": "course", "topic": "language", "format": "interactive", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["language", "arabic", "practical", "self-paced", "beginner"]},
    {"title": "Japanese Language & Culture", "description": "Learn Japanese with cultural context", "category": "course", "topic": "language", "format": "video", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["language", "japanese", "theory", "culture", "self-paced"]},
    {"title": "Language Exchange Group", "description": "Practice languages with native speakers", "category": "course", "topic": "language", "format": "group", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["language", "social", "group", "practical", "interactive"]},
    # Business
    {"title": "Entrepreneurship Foundations", "description": "From idea to business plan", "category": "course", "topic": "business", "format": "video", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["business", "entrepreneurship", "practical", "self-paced", "self-direction", "autonomous"]},
    {"title": "Business Strategy Theory", "description": "Strategic frameworks and competitive analysis", "category": "course", "topic": "business", "format": "video", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["business", "strategy", "theory", "self-paced"]},
    {"title": "Startup Incubator Program", "description": "Intensive startup building with mentors", "category": "course", "topic": "business", "format": "bootcamp", "noise": "moderate", "social": "high", "mood": "intense", "tags": ["business", "entrepreneurship", "social", "intensive", "practical"]},
    # Wellness
    {"title": "CBT Self-Help Course", "description": "Cognitive behavioral therapy techniques for daily life", "category": "course", "topic": "wellness", "format": "interactive", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["wellness", "cbt", "therapy", "practical", "self-paced", "calming"]},
    {"title": "Stress Management Workshop", "description": "Learn evidence-based stress reduction techniques", "category": "course", "topic": "wellness", "format": "group", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["wellness", "stress", "practical", "calming", "gentle"]},
    {"title": "Nutrition & Mental Health", "description": "How diet affects your mood and cognition", "category": "course", "topic": "wellness", "format": "video", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["wellness", "nutrition", "theory", "self-paced", "health"]},
    # Music
    {"title": "Guitar for Beginners", "description": "Learn guitar from first chord to first song", "category": "course", "topic": "music", "format": "video", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["music", "guitar", "practical", "self-paced", "creative", "beginner"]},
    {"title": "Music Theory Fundamentals", "description": "Understand harmony, rhythm, and structure", "category": "course", "topic": "music", "format": "video", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["music", "theory", "self-paced"]},
    # Cooking
    {"title": "Home Cooking Basics", "description": "Essential cooking techniques and recipes", "category": "course", "topic": "cooking", "format": "video", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["cooking", "practical", "self-paced", "hands-on", "beginner"]},
    {"title": "Cooking Class Group", "description": "Learn to cook together in a social setting", "category": "course", "topic": "cooking", "format": "group", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["cooking", "practical", "social", "group", "hands-on", "fun"]},
]

# ── Keyword → topic mapping ──────────────────────────────────────────────────

_COURSE_KEYWORDS: dict[str, list[str]] = {
    "psychology": ["psychology"],
    "心理": ["psychology"],
    "meditation": ["meditation"],
    "冥想": ["meditation"],
    "تأمل": ["meditation"],
    "mindfulness": ["meditation"],
    "programming": ["programming"],
    "编程": ["programming"],
    "coding": ["programming"],
    "代码": ["programming"],
    "art": ["art"],
    "画画": ["art"],
    "drawing": ["art"],
    "painting": ["art"],
    "书法": ["art"],
    "language": ["language"],
    "语言": ["language"],
    "arabic": ["language"],
    "阿拉伯语": ["language"],
    "japanese": ["language"],
    "日语": ["language"],
    "business": ["business"],
    "商业": ["business"],
    "创业": ["business"],
    "wellness": ["wellness"],
    "健康": ["wellness"],
    "cooking": ["cooking"],
    "烹饪": ["cooking"],
    "做饭": ["cooking"],
    "music": ["music"],
    "音乐": ["music"],
    "guitar": ["music"],
    "吉他": ["music"],
    "skill": [],  # generic
    "学": [],
    "learn": [],
}


def _match_topics(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: set[str] = set()
    for keyword, topics in _COURSE_KEYWORDS.items():
        if keyword in text_lower:
            matched.update(topics)
    return list(matched)


class CourseFulfiller(L2Fulfiller):
    """Recommends courses based on wish topic and cognitive style (MBTI)."""

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        target_topics = _match_topics(wish.wish_text)

        if target_topics:
            candidates = [c for c in COURSE_CATALOG if c["topic"] in target_topics]
        else:
            candidates = list(COURSE_CATALOG)

        if not candidates:
            candidates = list(COURSE_CATALOG)

        recs = self._build_recommendations(candidates, detector_results, max_results=3)

        return L2FulfillmentResult(
            recommendations=recs,
            map_data=None,
            reminder_option=ReminderOption(
                text="Want a reminder to start this course?",
                delay_hours=24,
            ),
        )
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_courses.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add wish_engine/l2_courses.py tests/test_l2_courses.py
git commit -m "feat: add CourseFulfiller with 27-course catalog and cognitive style matching"
```

---

### Task 6: CareerFulfiller — career direction based on values + MBTI

**Files:**
- Create: `wish_engine/l2_career.py`
- Test: `tests/test_l2_career.py` (create)

**Step 1: Write the failing test**

Create `tests/test_l2_career.py`:

```python
"""Tests for CareerFulfiller — career direction with values + MBTI matching."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_career import CareerFulfiller, CAREER_CATALOG


class TestCareerCatalog:
    def test_catalog_not_empty(self):
        assert len(CAREER_CATALOG) >= 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in CAREER_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestCareerFulfiller:
    def _make_wish(self, text="想换个工作") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.CAREER_DIRECTION,
            level=WishLevel.L2, fulfillment_strategy="career_guidance",
        )

    def test_returns_l2_result(self):
        f = CareerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_self_direction_values(self):
        """values(self-direction) → entrepreneurial/independent career paths."""
        f = CareerFulfiller()
        det = DetectorResults(values={"top_values": ["self-direction", "stimulation"]})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("self-direction", "autonomous", "entrepreneurship") for t in tags)

    def test_benevolence_values(self):
        """values(benevolence) → helping-oriented careers."""
        f = CareerFulfiller()
        det = DetectorResults(values={"top_values": ["benevolence", "universalism"]})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("helping", "social-impact", "benevolence") for t in tags)

    def test_max_3(self):
        f = CareerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_reminder(self):
        f = CareerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_career.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `wish_engine/l2_career.py`:

```python
"""CareerFulfiller — career direction recommendations based on values + MBTI.

Maps value profiles and MBTI types to career directions.
Zero LLM.
"""

from __future__ import annotations

from typing import Any

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Career direction catalog ─────────────────────────────────────────────────

CAREER_CATALOG: list[dict[str, Any]] = [
    # Independent / self-direction
    {"title": "Freelance & Independent Work", "description": "Build your own practice in your area of expertise", "category": "career_direction", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["self-direction", "autonomous", "freelance", "independence"]},
    {"title": "Entrepreneurship", "description": "Start and grow your own business", "category": "career_direction", "noise": "moderate", "social": "medium", "mood": "calming", "tags": ["self-direction", "autonomous", "entrepreneurship", "leadership"]},
    {"title": "Creative Industries", "description": "Design, writing, art, media — work driven by creativity", "category": "career_direction", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["self-direction", "creativity", "autonomous", "art"]},
    # Helping / benevolence
    {"title": "Counseling & Therapy", "description": "Help others through mental health support", "category": "career_direction", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["benevolence", "helping", "therapy", "social-impact", "calming"]},
    {"title": "Education & Teaching", "description": "Shape minds and inspire learning", "category": "career_direction", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["benevolence", "helping", "education", "social", "teaching"]},
    {"title": "Non-Profit & Social Impact", "description": "Drive change through mission-driven organizations", "category": "career_direction", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["benevolence", "social-impact", "helping", "universalism"]},
    {"title": "Healthcare", "description": "Care for people's physical and mental wellbeing", "category": "career_direction", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["benevolence", "helping", "health", "practical"]},
    # Achievement / power
    {"title": "Management & Leadership", "description": "Lead teams and drive organizational success", "category": "career_direction", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["achievement", "leadership", "social", "power"]},
    {"title": "Finance & Investment", "description": "Analyze markets and manage capital", "category": "career_direction", "noise": "moderate", "social": "medium", "mood": "calming", "tags": ["achievement", "analytical", "theory", "security"]},
    {"title": "Consulting", "description": "Solve complex business problems for organizations", "category": "career_direction", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["achievement", "analytical", "practical", "social"]},
    # Security / stability
    {"title": "Government & Public Service", "description": "Stable career serving the public interest", "category": "career_direction", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["security", "stability", "traditional", "structured"]},
    {"title": "Engineering", "description": "Build and maintain systems and infrastructure", "category": "career_direction", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["security", "practical", "analytical", "structured"]},
    # Universalism / exploration
    {"title": "Research & Academia", "description": "Pursue knowledge and advance understanding", "category": "career_direction", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["universalism", "theory", "research", "quiet", "autonomous", "self-paced"]},
    {"title": "International Development", "description": "Work across cultures to improve lives globally", "category": "career_direction", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["universalism", "social-impact", "global", "helping"]},
    # Tech
    {"title": "Software Development", "description": "Build products and solve problems through code", "category": "career_direction", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["tech", "practical", "autonomous", "quiet", "self-paced", "self-direction"]},
    {"title": "Data Science & AI", "description": "Extract insights from data and build intelligent systems", "category": "career_direction", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["tech", "analytical", "theory", "autonomous", "quiet"]},
    # Volunteer-adjacent
    {"title": "Volunteering & Community Service", "description": "Contribute your time and skills to causes you care about", "category": "career_direction", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["benevolence", "helping", "community", "social-impact", "volunteer"]},
]


class CareerFulfiller(L2Fulfiller):
    """Recommends career directions based on values and MBTI profile."""

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = list(CAREER_CATALOG)

        # Add relevance reason based on values
        top_values = detector_results.values.get("top_values", [])
        for c in candidates:
            c["relevance_reason"] = _build_career_reason(c, top_values)

        recs = self._build_recommendations(candidates, detector_results, max_results=3)

        return L2FulfillmentResult(
            recommendations=recs,
            map_data=None,
            reminder_option=ReminderOption(
                text="Want to explore this direction further this week?",
                delay_hours=48,
            ),
        )


def _build_career_reason(career: dict, top_values: list[str]) -> str:
    tags = set(career.get("tags", []))
    for v in top_values:
        if v in tags:
            return f"Aligns with your core value: {v}"
    return f"Recommended direction: {career['title']}"
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_career.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add wish_engine/l2_career.py tests/test_l2_career.py
git commit -m "feat: add CareerFulfiller with 17-direction catalog and values matching"
```

---

### Task 7: WellnessFulfiller — wellness recommendations based on emotion + fragility

**Files:**
- Create: `wish_engine/l2_wellness.py`
- Test: `tests/test_l2_wellness.py` (create)

**Step 1: Write the failing test**

Create `tests/test_l2_wellness.py`:

```python
"""Tests for WellnessFulfiller — wellness with emotion + fragility matching."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_wellness import WellnessFulfiller, WELLNESS_CATALOG


class TestWellnessCatalog:
    def test_catalog_not_empty(self):
        assert len(WELLNESS_CATALOG) >= 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "mood"}
        for item in WELLNESS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestWellnessFulfiller:
    def _make_wish(self, text="最近总失眠") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="wellness_recommendation",
        )

    def test_returns_l2_result(self):
        f = WellnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_anxiety_gets_calming(self):
        f = WellnessFulfiller()
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.8}})
        result = f.fulfill(self._make_wish("想减轻焦虑"), det)
        for rec in result.recommendations:
            assert "intense" not in rec.tags

    def test_sleep_wish_finds_sleep_items(self):
        f = WellnessFulfiller()
        result = f.fulfill(self._make_wish("最近总失眠"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("sleep", "relaxation", "calming") for t in tags)

    def test_exercise_wish(self):
        f = WellnessFulfiller()
        result = f.fulfill(self._make_wish("想多运动"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("exercise", "movement", "fitness") for t in tags)

    def test_max_3(self):
        f = WellnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_map_for_physical_activities(self):
        f = WellnessFulfiller()
        result = f.fulfill(self._make_wish("想多运动"), DetectorResults())
        # Wellness with physical component may have map data
        assert isinstance(result, L2FulfillmentResult)

    def test_has_reminder(self):
        f = WellnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_wellness.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `wish_engine/l2_wellness.py`:

```python
"""WellnessFulfiller — wellness recommendations based on emotion + fragility.

Maps emotional state and fragility patterns to appropriate wellness activities.
Anxiety → calming; agitation → movement; depression → gentle activation.
Zero LLM.
"""

from __future__ import annotations

from typing import Any

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    ReminderOption,
)

# ── Wellness catalog ─────────────────────────────────────────────────────────

WELLNESS_CATALOG: list[dict[str, Any]] = [
    # Sleep
    {"title": "Sleep Hygiene Program", "description": "Evidence-based routines for better sleep", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["sleep", "relaxation", "calming", "self-paced", "practical"]},
    {"title": "Guided Sleep Meditation", "description": "Audio-guided meditation designed for falling asleep", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["sleep", "meditation", "calming", "relaxation", "gentle"]},
    {"title": "CBT for Insomnia (CBT-I)", "description": "Structured program to address chronic insomnia", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["sleep", "cbt", "therapy", "practical", "calming"]},
    # Anxiety management
    {"title": "Breathing Exercises", "description": "Simple breathing techniques for anxiety relief", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["anxiety", "breathing", "calming", "practical", "quick"]},
    {"title": "Progressive Muscle Relaxation", "description": "Systematic tension-release practice for stress", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["anxiety", "relaxation", "calming", "practical", "gentle"]},
    {"title": "Anxiety Journaling", "description": "Structured journaling to process anxious thoughts", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["anxiety", "journaling", "calming", "self-paced", "writing"]},
    # Exercise & movement
    {"title": "Gentle Yoga Routine", "description": "Low-intensity yoga for relaxation and flexibility", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["exercise", "yoga", "calming", "gentle", "movement", "quiet"]},
    {"title": "Walking Meditation", "description": "Mindful walking practice combining movement and awareness", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["exercise", "meditation", "movement", "calming", "nature", "quiet"]},
    {"title": "Swimming for Wellbeing", "description": "Rhythmic swimming as moving meditation", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["exercise", "swimming", "movement", "calming", "solo"]},
    {"title": "Outdoor Running", "description": "Running in nature for mood elevation", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["exercise", "running", "movement", "nature", "fitness", "solo"]},
    {"title": "Group Fitness Class", "description": "Energetic group exercise with music", "category": "wellness", "noise": "loud", "social": "high", "mood": "intense", "tags": ["exercise", "fitness", "social", "movement", "intense", "noisy"]},
    # Nutrition
    {"title": "Mood-Boosting Nutrition Guide", "description": "Foods that support mental health", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["nutrition", "health", "practical", "calming", "self-paced"]},
    # Relaxation
    {"title": "Nature Therapy (Shinrin-yoku)", "description": "Forest bathing for stress reduction", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["relaxation", "nature", "calming", "gentle", "quiet"]},
    {"title": "Aromatherapy Basics", "description": "Using essential oils for relaxation and focus", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["relaxation", "calming", "practical", "self-care"]},
    {"title": "Digital Detox Plan", "description": "Structured plan to reduce screen time", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["relaxation", "digital", "practical", "self-paced", "calming"]},
    # Emotional regulation
    {"title": "Emotional Freedom Technique (EFT)", "description": "Tapping technique for emotional relief", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["emotions", "calming", "practical", "gentle", "self-paced"]},
    {"title": "Gratitude Practice", "description": "Daily gratitude journaling for positive mood shift", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["emotions", "journaling", "calming", "gentle", "positive"]},
    {"title": "Art as Self-Care", "description": "Expressive art for emotional processing", "category": "wellness", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["emotions", "creative", "calming", "self-expression", "healing"]},
]

# ── Keyword → wellness category mapping ──────────────────────────────────────

_WELLNESS_KEYWORDS: dict[str, list[str]] = {
    "sleep": ["sleep"],
    "失眠": ["sleep"],
    "نوم": ["sleep"],
    "insomnia": ["sleep"],
    "anxiety": ["anxiety"],
    "焦虑": ["anxiety"],
    "قلق": ["anxiety"],
    "stress": ["anxiety", "relaxation"],
    "压力": ["anxiety", "relaxation"],
    "exercise": ["exercise"],
    "运动": ["exercise"],
    "رياضة": ["exercise"],
    "yoga": ["exercise"],
    "瑜伽": ["exercise"],
    "relax": ["relaxation"],
    "放松": ["relaxation"],
    "nutrition": ["nutrition"],
    "diet": ["nutrition"],
    "emotion": ["emotions"],
    "情绪": ["emotions"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: set[str] = set()
    for keyword, cats in _WELLNESS_KEYWORDS.items():
        if keyword in text_lower:
            matched.update(cats)
    return list(matched)


class WellnessFulfiller(L2Fulfiller):
    """Recommends wellness activities based on emotion state and fragility."""

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        target_cats = _match_categories(wish.wish_text)

        if target_cats:
            candidates = [
                w for w in WELLNESS_CATALOG
                if any(cat in w.get("tags", []) for cat in target_cats)
            ]
        else:
            candidates = list(WELLNESS_CATALOG)

        if not candidates:
            candidates = list(WELLNESS_CATALOG)

        recs = self._build_recommendations(candidates, detector_results, max_results=3)

        # Map data only for physical activities
        has_physical = any(
            any(t in ("exercise", "yoga", "nature") for t in r.tags)
            for r in recs
        )
        map_data = MapData(place_type="wellness_center", radius_km=5.0) if has_physical else None

        return L2FulfillmentResult(
            recommendations=recs,
            map_data=map_data,
            reminder_option=ReminderOption(
                text="Want a daily reminder for this practice?",
                delay_hours=12,
            ),
        )
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_wellness.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add wish_engine/l2_wellness.py tests/test_l2_wellness.py
git commit -m "feat: add WellnessFulfiller with 18-activity catalog and emotion matching"
```

---

### Task 8: Wire L2 into engine + update queue + renderer + exports

**Files:**
- Modify: `wish_engine/engine.py:309-319` (L2 block)
- Modify: `wish_engine/queue.py:55` (fulfillment type)
- Modify: `wish_engine/renderer.py:81-146` (L2 card_data)
- Modify: `wish_engine/__init__.py` (exports)
- Test: `tests/test_l2_engine_integration.py` (create)

**Step 1: Write the failing test**

Create `tests/test_l2_engine_integration.py`:

```python
"""Integration tests — L2 wishes flow through the full engine pipeline."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    EmotionState,
    L2FulfillmentResult,
    WishLevel,
    WishState,
    WishType,
)
from wish_engine.engine import WishEngine


class TestL2EngineIntegration:
    """Test L2 wishes through the full WishEngine pipeline."""

    def test_l2_wish_gets_fulfilled(self):
        """L2 wish text → detection → classification → fulfillment → render."""
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        result = engine.process(
            raw_wishes=["想找个安静的地方"],
            detector_results=DetectorResults(
                mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}},
            ),
            session_id="s1",
            user_id="u1",
        )
        assert len(result.l2_wishes) >= 1
        # L2 wishes should be fulfilled now (not just queued)
        assert len(result.l2_fulfillments) >= 1

    def test_l2_render_blue_star(self):
        """L2 fulfilled wish → blue star with pulse_blue_wave animation."""
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        result = engine.process(
            raw_wishes=["想学冥想"],
            detector_results=DetectorResults(),
            session_id="s1",
            user_id="u1",
        )
        l2_renders = [
            r for r in result.renders
            if r.star_state == WishState.FOUND and r.color == "#4A90D9"
        ]
        assert len(l2_renders) >= 1
        assert l2_renders[0].animation == "pulse_blue_wave"

    def test_l2_card_data_has_recommendations(self):
        """L2 card_data includes recommendations list."""
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        result = engine.process(
            raw_wishes=["想读一本关于心理学的书"],
            detector_results=DetectorResults(),
            session_id="s1",
            user_id="u1",
        )
        found_renders = [r for r in result.renders if r.star_state == WishState.FOUND]
        if found_renders:
            card = found_renders[0].card_data
            assert "recommendations" in card
            assert len(card["recommendations"]) >= 1

    def test_l2_queue_state_found(self):
        """L2 wishes transition to FOUND state in the queue."""
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        result = engine.process(
            raw_wishes=["想学画画"],
            detector_results=DetectorResults(),
            session_id="s1",
            user_id="u1",
        )
        l2_queued = [q for q in result.queued if q.wish.level == WishLevel.L2]
        assert len(l2_queued) >= 1
        assert l2_queued[0].state == WishState.FOUND

    def test_l2_with_personality_filtering(self):
        """Introvert profile → L2 place recommendations filtered for noise."""
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        result = engine.process(
            raw_wishes=["想找个地方运动"],
            detector_results=DetectorResults(
                mbti={"type": "INFP", "dimensions": {"E_I": 0.15}},
            ),
            session_id="s1",
            user_id="u1",
        )
        if result.l2_fulfillments:
            for key, ful in result.l2_fulfillments.items():
                for rec in ful.recommendations:
                    assert "noisy" not in rec.tags

    def test_l2_summary_counts(self):
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        result = engine.process(
            raw_wishes=["想找个安静地方"],
            detector_results=DetectorResults(),
            session_id="s1",
            user_id="u1",
        )
        summary = result.summary()
        assert summary["l2"] >= 1
        assert summary["l2_fulfilled"] >= 1

    def test_mixed_l1_l2_wishes(self):
        """Both L1 and L2 wishes in same session work independently."""
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        result = engine.process(
            raw_wishes=["想理解自己", "想找个安静的地方"],
            detector_results=DetectorResults(),
            session_id="s1",
            user_id="u1",
        )
        assert len(result.l1_wishes) >= 1 or len(result.l2_wishes) >= 1

    def test_l2_chocolate_moment_timing(self):
        """L2 wishes have reveal_after set (not immediate)."""
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        result = engine.process(
            raw_wishes=["想找个安静地方"],
            detector_results=DetectorResults(),
            session_id="s1",
            user_id="u1",
        )
        l2_queued = [q for q in result.queued if q.wish.level == WishLevel.L2]
        if l2_queued:
            assert l2_queued[0].reveal_after > 0
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_engine_integration.py -v`
Expected: FAIL — `AttributeError: 'WishEngineResult' object has no attribute 'l2_fulfillments'`

**Step 3: Apply changes**

**3a. Update `wish_engine/queue.py` line 55** — generalize fulfillment type:

Change:
```python
    fulfillment: L1FulfillmentResult | None = None
```
To:
```python
    fulfillment: Any = None  # L1FulfillmentResult or L2FulfillmentResult
```

And update imports at top of queue.py — add `Any`:
```python
from typing import Any
```

Remove unused import `L1FulfillmentResult` from line 23 of queue.py.

Also update `mark_found` signature (line 163-166):
```python
    def mark_found(
        self,
        wish_id: str,
        fulfillment: Any,
        delay_seconds: float = 0,
    ) -> QueuedWish:
```

**3b. Update `wish_engine/engine.py`** — add L2 fulfillment:

Add import at top (after line 47):
```python
from wish_engine.l2_fulfiller import fulfill_l2
```

Add `l2_fulfillments` to `WishEngineResult.__init__` (after line 62):
```python
        self.l2_fulfillments: dict[str, L2FulfillmentResult] = {}
```

Add import of L2FulfillmentResult at top:
```python
from wish_engine.models import (
    ...
    L2FulfillmentResult,
    ...
)
```

Replace L2 block (lines 309-319) with:
```python
        # L2: Fulfill with local-compute adapters
        for wish in result.l2_wishes:
            try:
                qw = self._queue.enqueue(
                    wish, session_id=session_id, user_id=user_id, distress=distress,
                )
                result.queued.append(qw)
                self._queue.mark_searching(qw.wish_id)

                # L2 fulfillment (zero LLM, local-compute)
                l2_result = fulfill_l2(wish, det_results)
                result.l2_fulfillments[wish.wish_text] = l2_result

                delay = self._queue.compute_delay(qw.priority)
                self._queue.mark_found(qw.wish_id, l2_result, delay_seconds=delay)

                found_render = render(WishState.FOUND, wish=wish, l2_fulfillment=l2_result)
                result.renders.append(found_render)
            except Exception as e:
                result.errors.append(f"L2 fulfillment error: {e}")
                born_render = render(WishState.BORN, wish=wish)
                result.renders.append(born_render)
```

Update `summary()` method to include `l2_fulfilled`:
```python
            "l2_fulfilled": len(self.l2_fulfillments),
```

**3c. Update `wish_engine/renderer.py`** — accept L2 fulfillment data:

Update `_build_card_data` signature to accept L2 data:
```python
def _build_card_data(
    wish: ClassifiedWish | None,
    fulfillment: L1FulfillmentResult | None,
    state: WishState,
    l2_fulfillment: L2FulfillmentResult | None = None,
) -> dict[str, Any]:
```

Add L2 card data section after the L1 fulfillment block (after line 97):
```python
    if l2_fulfillment:
        card["recommendations"] = [
            {
                "title": r.title,
                "description": r.description,
                "category": r.category,
                "relevance_reason": r.relevance_reason,
                "score": r.score,
                "tags": r.tags,
            }
            for r in l2_fulfillment.recommendations
        ]
        if l2_fulfillment.map_data:
            card["map_data"] = {
                "place_type": l2_fulfillment.map_data.place_type,
                "radius_km": l2_fulfillment.map_data.radius_km,
            }
        if l2_fulfillment.reminder_option:
            card["reminder"] = {
                "text": l2_fulfillment.reminder_option.text,
                "delay_hours": l2_fulfillment.reminder_option.delay_hours,
            }
```

Update `render()` function signature:
```python
def render(
    state: WishState,
    wish: ClassifiedWish | None = None,
    fulfillment: L1FulfillmentResult | None = None,
    l2_fulfillment: L2FulfillmentResult | None = None,
) -> RenderOutput:
```

Update `render()` body to pass l2_fulfillment:
```python
    card_data = _build_card_data(wish, fulfillment, state, l2_fulfillment=l2_fulfillment)
```

Add import of L2FulfillmentResult at top of renderer.py:
```python
from wish_engine.models import (
    ...
    L2FulfillmentResult,
    ...
)
```

**3d. Update `wish_engine/__init__.py`** — add L2 exports:

Add to imports:
```python
from wish_engine.l2_fulfiller import fulfill_l2, L2Fulfiller, PersonalityFilter
from wish_engine.l2_places import PlaceFulfiller
from wish_engine.l2_books import BookFulfiller
from wish_engine.l2_courses import CourseFulfiller
from wish_engine.l2_career import CareerFulfiller
from wish_engine.l2_wellness import WellnessFulfiller
from wish_engine.models import L2FulfillmentResult, Recommendation, MapData, ReminderOption
```

Add to `__all__`:
```python
    # L2 Fulfillment
    "fulfill_l2",
    "L2Fulfiller",
    "PersonalityFilter",
    "PlaceFulfiller",
    "BookFulfiller",
    "CourseFulfiller",
    "CareerFulfiller",
    "WellnessFulfiller",
    "L2FulfillmentResult",
    "Recommendation",
    "MapData",
    "ReminderOption",
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_engine_integration.py -v`
Expected: All tests PASS

**Step 5: Run full test suite**

Run: `cd /Users/michael/wish-engine && python -m pytest -v`
Expected: All existing tests + all new tests PASS. No regressions.

**Step 6: Commit**

```bash
git add wish_engine/engine.py wish_engine/queue.py wish_engine/renderer.py wish_engine/__init__.py tests/test_l2_engine_integration.py
git commit -m "feat: wire L2 fulfillment into engine pipeline with queue, renderer, and exports"
```

---

### Task 9: Run full test suite + verify all router tests pass

**Files:**
- Modify: None (verification only)

**Step 1: Run all tests**

Run: `cd /Users/michael/wish-engine && python -m pytest -v --tb=short`
Expected: All tests PASS including `tests/test_l2_fulfiller.py::TestFulfillL2Router`

**Step 2: Count total tests**

Run: `cd /Users/michael/wish-engine && python -m pytest --co -q | tail -1`
Expected: ~580+ tests (513 existing + ~70 new)

**Step 3: Spot-check personality filtering end-to-end**

Run: `cd /Users/michael/wish-engine && python -m pytest tests/test_l2_fulfiller.py tests/test_l2_places.py tests/test_l2_books.py tests/test_l2_courses.py tests/test_l2_career.py tests/test_l2_wellness.py tests/test_l2_engine_integration.py -v`
Expected: All L2 tests PASS

**Step 4: Commit (if any fixes needed)**

---

## Summary

| Task | What | New Tests | Files |
|------|------|-----------|-------|
| 1 | L2 output models | 8 | models.py, test_l2_models.py |
| 2 | L2Fulfiller base + PersonalityFilter + router | 19 | l2_fulfiller.py, test_l2_fulfiller.py |
| 3 | PlaceFulfiller (28 places) | 9 | l2_places.py, test_l2_places.py |
| 4 | BookFulfiller (32 books) | 9 | l2_books.py, test_l2_books.py |
| 5 | CourseFulfiller (27 courses) | 7 | l2_courses.py, test_l2_courses.py |
| 6 | CareerFulfiller (17 directions) | 5 | l2_career.py, test_l2_career.py |
| 7 | WellnessFulfiller (18 activities) | 7 | l2_wellness.py, test_l2_wellness.py |
| 8 | Engine + queue + renderer + exports | 8 | engine.py, queue.py, renderer.py, __init__.py, test_l2_engine_integration.py |
| 9 | Full suite verification | 0 | — |
| **Total** | | **~72** | **17 files** |

**Zero LLM calls. All local-compute. Curated catalogs. Personality filter on every recommendation.**
