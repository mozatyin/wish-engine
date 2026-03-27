"""Tests for DialogueScanner — topic extraction from dialogue text."""

import pytest
from wish_engine.compass.scanner import DialogueScanner


class TestEntityDetection:
    def test_detects_named_entity(self):
        scanner = DialogueScanner({"Rhett": ["rhett", "butler"]})
        topics = scanner.scan_dialogue("Rhett Butler is a fool!")
        assert len(topics) == 1
        assert topics[0]["entity"] == "Rhett"

    def test_no_match_returns_empty(self):
        scanner = DialogueScanner({"Rhett": ["rhett"]})
        topics = scanner.scan_dialogue("The weather is nice today")
        assert len(topics) == 0

    def test_multiple_entities(self):
        scanner = DialogueScanner({
            "Rhett": ["rhett"],
            "Ashley": ["ashley"],
        })
        topics = scanner.scan_dialogue("Rhett and Ashley were both there")
        assert len(topics) == 2

    def test_case_insensitive(self):
        scanner = DialogueScanner({"Rhett": ["rhett"]})
        topics = scanner.scan_dialogue("RHETT is impossible")
        assert len(topics) == 1


class TestSentiment:
    def test_negative_sentiment(self):
        scanner = DialogueScanner({"X": ["x"]})
        topics = scanner.scan_dialogue("I hate X, he is horrible")
        assert topics[0]["sentiment"] == "negative"

    def test_positive_sentiment(self):
        scanner = DialogueScanner({"X": ["x"]})
        topics = scanner.scan_dialogue("I love X, he is wonderful")
        assert topics[0]["sentiment"] == "positive"

    def test_denial_sentiment(self):
        scanner = DialogueScanner({"X": ["x"]})
        topics = scanner.scan_dialogue("I don't care about X anymore")
        assert topics[0]["sentiment"] == "denial"


class TestArousal:
    def test_high_arousal_negative(self):
        scanner = DialogueScanner({"X": ["x"]})
        topics = scanner.scan_dialogue("I hate X! That fool makes me furious!")
        assert topics[0]["arousal"] >= 0.6

    def test_low_arousal_neutral(self):
        scanner = DialogueScanner({"X": ["x"]})
        topics = scanner.scan_dialogue("X was there too")
        assert topics[0]["arousal"] <= 0.4

    def test_high_arousal_words_boost(self):
        scanner = DialogueScanner({"X": ["x"]})
        topics = scanner.scan_dialogue("X is extraordinary, I cannot stop thinking about it, my heart races")
        assert topics[0]["arousal"] >= 0.7


class TestBatchScan:
    def test_aggregates_mentions(self):
        scanner = DialogueScanner({"Rhett": ["rhett"]})
        dialogues = [
            {"text": "Rhett was there"},
            {"text": "Rhett spoke to me"},
            {"text": "I saw Rhett again"},
        ]
        topics = scanner.scan_batch(dialogues)
        assert len(topics) == 1
        assert topics[0]["mentions"] >= 3

    def test_max_arousal_kept(self):
        scanner = DialogueScanner({"Rhett": ["rhett"]})
        dialogues = [
            {"text": "Rhett was there"},  # low arousal
            {"text": "I hate Rhett! That horrible fool!"},  # high arousal
        ]
        topics = scanner.scan_batch(dialogues)
        assert topics[0]["arousal"] >= 0.5
