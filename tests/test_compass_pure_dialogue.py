import json
import re
import pytest
from collections import defaultdict
from wish_engine.models import DetectorResults
from wish_engine.compass.compass import WishCompass

FIXTURE = "/Users/michael/soulgraph/fixtures/scarlett_full.jsonl"


@pytest.mark.skipif(not __import__("pathlib").Path(FIXTURE).exists(), reason="fixture missing")
class TestCompassPureDialogue:
    def _run_pure_dialogue(self):
        with open(FIXTURE) as f:
            all_d = [json.loads(l) for l in f]
        compass = WishCompass()
        for i, d in enumerate(all_d):
            text = d["text"]
            names = set(re.findall(r'\b[A-Z][a-z]{2,}\b', text)) - {
                'The', 'And', 'But', 'What', 'How', 'Why', 'God', 'Not', 'After',
            }
            emotion_words = [
                'hate', 'love', 'furious', 'scared', 'cry', 'want', 'need',
                'angry', 'miss', 'dead', 'died',
            ]
            has_emotion = any(w in text.lower() for w in emotion_words)
            for name in names:
                if has_emotion:
                    arousal = 0.5 if any(
                        w in text.lower() for w in ['hate', 'furious', 'love', 'cry', 'dead']
                    ) else 0.35
                    sentiment = 'negative' if any(
                        w in text.lower() for w in ['hate', 'furious', 'angry']
                    ) else 'mixed'
                    compass.scan(
                        topics=[{
                            'entity': name,
                            'sentiment': sentiment,
                            'arousal': arousal,
                            'mentions': 1,
                        }],
                        detector_results=DetectorResults(),
                        session_id=f's_{i}',
                    )
        return compass

    def test_rhett_detected(self):
        compass = self._run_pure_dialogue()
        rhett = compass.vault.get_by_topic("Rhett")
        assert len(rhett) >= 1, "Compass should detect Rhett in pure dialogue"

    def test_ashley_detected(self):
        compass = self._run_pure_dialogue()
        ashley = compass.vault.get_by_topic("Ashley")
        assert len(ashley) >= 1, "Compass should detect Ashley in pure dialogue"

    def test_multiple_entities_detected(self):
        compass = self._run_pure_dialogue()
        shells = compass.vault.all_shells
        topics = [s.topic for s in shells]
        assert len(topics) >= 3, f"Should detect 3+ entities, got {topics}"
