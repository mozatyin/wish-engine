import pytest, json
from unittest.mock import patch, MagicMock

def _mock_resp(data):
    m = MagicMock()
    m.read.return_value = json.dumps(data).encode() if isinstance(data, (dict, list)) else data.encode()
    m.__enter__ = lambda s: s; m.__exit__ = MagicMock(return_value=False)
    return m

class TestAffirmations:
    @patch("wish_engine.apis.affirmations_api.urlopen")
    def test_get(self, mock):
        mock.return_value = _mock_resp({"affirmation": "You are brave"})
        from wish_engine.apis.affirmations_api import get_affirmation
        assert "brave" in get_affirmation()

class TestBored:
    @patch("wish_engine.apis.bored_api.urlopen")
    def test_get(self, mock):
        mock.return_value = _mock_resp({"activity": "Learn origami", "type": "education", "participants": 1})
        from wish_engine.apis.bored_api import get_activity
        assert get_activity()["activity"] == "Learn origami"

class TestJoke:
    @patch("wish_engine.apis.joke_api.urlopen")
    def test_get(self, mock):
        mock.return_value = _mock_resp({"type": "single", "joke": "Why do programmers...", "category": "Programming"})
        from wish_engine.apis.joke_api import get_joke
        assert get_joke()["joke"]

class TestMeal:
    @patch("wish_engine.apis.meal_api.urlopen")
    def test_search(self, mock):
        mock.return_value = _mock_resp({"meals": [{"strMeal": "Pasta", "strCategory": "Italian", "strArea": "Italy", "strInstructions": "Boil water"}]})
        from wish_engine.apis.meal_api import search_meal
        assert search_meal("pasta")[0]["name"] == "Pasta"

class TestExercise:
    def test_available(self):
        from wish_engine.apis.exercise_api import is_available
        assert is_available()

class TestCurrency:
    @patch("wish_engine.apis.currency_api.urlopen")
    def test_rate(self, mock):
        mock.return_value = _mock_resp({"rates": {"EUR": 0.92}})
        from wish_engine.apis.currency_api import get_rate
        assert get_rate("USD", "EUR") == 0.92

class TestDog:
    @patch("wish_engine.apis.dog_api.urlopen")
    def test_image(self, mock):
        mock.return_value = _mock_resp({"message": "https://images.dog.ceo/breeds/retriever-golden/n02099601_1.jpg"})
        from wish_engine.apis.dog_api import random_dog_image
        assert "dog.ceo" in random_dog_image()

class TestAdvice:
    @patch("wish_engine.apis.advice_api.urlopen")
    def test_get(self, mock):
        mock.return_value = _mock_resp({"slip": {"advice": "Take small steps."}})
        from wish_engine.apis.advice_api import get_advice
        assert "steps" in get_advice()

class TestQuran:
    @patch("wish_engine.apis.quran_api.urlopen")
    def test_ayah(self, mock):
        mock.return_value = _mock_resp({"data": {"text": "In the name of God", "surah": {"englishName": "Al-Fatiha"}, "numberInSurah": 1}})
        from wish_engine.apis.quran_api import get_ayah
        a = get_ayah("1:1")
        assert "God" in a["text"]

class TestBible:
    @patch("wish_engine.apis.bible_api.urlopen")
    def test_verse(self, mock):
        mock.return_value = _mock_resp({"reference": "John 3:16", "text": "For God so loved the world", "verse_count": 1})
        from wish_engine.apis.bible_api import get_verse
        v = get_verse("John 3:16")
        assert "loved" in v["text"]

class TestAllAvailable:
    def test_all_12_available(self):
        from wish_engine.apis import affirmations_api, bored_api, joke_api, numbers_api, tarot_api, meal_api, exercise_api, currency_api, dog_api, advice_api, quran_api, bible_api
        apis = [affirmations_api, bored_api, joke_api, numbers_api, tarot_api, meal_api, exercise_api, currency_api, dog_api, advice_api, quran_api, bible_api]
        assert all(a.is_available() for a in apis)
