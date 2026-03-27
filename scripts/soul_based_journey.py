#!/usr/bin/env python3
"""Soul-Based Journey: Scarlett from Chapter 1 to the End.

NOT MBTI-based. Based on THREE LAYERS of Soul:
  - Focus (当下): What is she thinking about RIGHT NOW in this chapter?
  - Memory (历史): What themes keep recurring across chapters?
  - Deep (底层): What does she want but doesn't know? (Compass)

At each chapter, the system recommends based on all three layers.
"""

import sys, json
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from wish_engine.models import ClassifiedWish, DetectorResults, WishLevel, WishType
from wish_engine.universal_fulfiller import universal_fulfill
from wish_engine.l2_router import route
from wish_engine.compass.compass import WishCompass
from wish_engine.compass.scanner import DialogueScanner

FIXTURES = Path("/Users/michael/soulgraph/fixtures")


# ── Soul State Tracker ───────────────────────────────────────────────────────

class SoulState:
    """Tracks the three layers of a character's Soul across chapters."""

    def __init__(self):
        # Focus layer: what's on their mind RIGHT NOW
        self.current_topics: list[str] = []
        self.current_emotions: dict[str, float] = {}
        self.current_concerns: list[str] = []

        # Memory layer: recurring themes across chapters
        self.topic_history: Counter = Counter()
        self.emotion_history: defaultdict = defaultdict(list)
        self.recurring_concerns: Counter = Counter()

        # Scarlett's base personality (doesn't change)
        self.base_mbti = "ESTJ"
        self.base_values = ["power", "achievement", "security"]
        self.base_attachment = "fearful"

        # Deep layer: Compass
        self.compass = WishCompass()
        self.scanner = DialogueScanner({
            "Rhett": ["rhett", "butler", "captain butler"],
            "Ashley": ["ashley", "wilkes"],
            "Melanie": ["melanie", "melly"],
            "Tara": ["tara"],
            "Money": ["money", "dollars", "taxes", "poverty", "hungry", "starving"],
            "War": ["war", "yankees", "confederate", "soldiers", "battle"],
            "Mother": ["mother", "ellen", "mama"],
            "Children": ["bonnie", "wade", "ella", "baby", "child"],
        })

    def process_chapter(self, dialogues: list[dict], phase: int, session_prefix: str):
        """Process all dialogues in a chapter, updating all three Soul layers."""

        # ── Focus layer: extract what's on her mind NOW ──────────────
        self.current_topics = []
        self.current_emotions = {}
        self.current_concerns = []

        emotion_words = {
            "anger": ["furious", "hate", "damn", "rage", "angry", "fury"],
            "fear": ["scared", "afraid", "terrified", "horror", "panic", "dread"],
            "sadness": ["cry", "crying", "tears", "grief", "mourn", "miss", "lost", "dead", "died"],
            "loneliness": ["alone", "lonely", "no one", "nobody", "isolated"],
            "anxiety": ["worried", "nervous", "can't sleep", "thinking about", "what if"],
            "pride": ["I am", "I will", "never again", "I'll show", "I can"],
            "desire": ["want", "need", "wish", "dream", "long for", "yearn"],
            "love": ["love", "heart", "dear", "darling", "beloved"],
            "guilt": ["shouldn't", "wrong", "forgive", "sorry", "fault"],
            "determination": ["must", "have to", "will not", "swear", "promise", "tomorrow"],
        }

        concern_patterns = {
            "survival": ["hungry", "starving", "food", "taxes", "money", "dollars", "poverty", "Tara"],
            "love_triangle": ["ashley", "rhett", "love", "marry", "husband", "wife"],
            "war": ["war", "yankees", "soldiers", "battle", "confederate", "burning"],
            "motherhood": ["bonnie", "baby", "child", "mother", "children"],
            "social_status": ["lady", "reputation", "scandal", "society", "gossip"],
            "loss": ["dead", "died", "gone", "lost", "never again", "funeral"],
            "independence": ["my own", "myself", "I don't need", "I'll do it", "mill", "business"],
            "identity": ["who am I", "what kind of", "Ellen's daughter", "not a lady"],
        }

        for d in dialogues:
            text = d["text"].lower()

            # Extract emotions
            for emotion, words in emotion_words.items():
                hits = sum(1 for w in words if w in text)
                if hits > 0:
                    self.current_emotions[emotion] = self.current_emotions.get(emotion, 0) + hits * 0.1

            # Extract concerns
            for concern, patterns in concern_patterns.items():
                if any(p in text for p in patterns):
                    self.current_concerns.append(concern)

            # Feed to Compass
            topics = self.scanner.scan_dialogue(d["text"])
            if topics:
                self.compass.scan(
                    topics=topics,
                    detector_results=DetectorResults(),
                    session_id=f"{session_prefix}_p{phase}_{dialogues.index(d)}",
                )

        # Normalize emotions
        for e in self.current_emotions:
            self.current_emotions[e] = min(self.current_emotions[e], 1.0)

        # Current topics = top concerns this chapter
        concern_counts = Counter(self.current_concerns)
        self.current_topics = [c for c, _ in concern_counts.most_common(3)]

        # ── Memory layer: update history ─────────────────────────────
        for concern, count in concern_counts.items():
            self.recurring_concerns[concern] += count
        for emotion, level in self.current_emotions.items():
            self.emotion_history[emotion].append(level)
            self.topic_history[emotion] += 1

    def get_detector_results(self) -> DetectorResults:
        """Build DetectorResults from current Soul state — this is what fulfillers use."""
        # Values shift based on life phase
        current_values = list(self.base_values)
        if "survival" in self.current_topics:
            current_values = ["security", "achievement", "power"]
        if "independence" in self.current_topics:
            current_values = ["self-direction", "achievement", "power"]
        if "loss" in self.current_topics:
            current_values = ["benevolence", "security", "tradition"]

        return DetectorResults(
            mbti={"type": self.base_mbti, "dimensions": {"E_I": 0.7}},
            emotion={"emotions": dict(self.current_emotions), "distress": self.current_emotions.get("sadness", 0) + self.current_emotions.get("fear", 0)},
            values={"top_values": current_values},
            attachment={"style": self.base_attachment},
            conflict={"style": "competing"},
            fragility={"pattern": "defensive" if self.current_emotions.get("anger", 0) > 0.3 else "sensitive"},
        )

    def get_focus_wishes(self) -> list[str]:
        """What she needs RIGHT NOW based on current chapter."""
        wishes = []
        concerns = self.current_topics

        if "survival" in concerns:
            wishes.append("I need help with money and financial planning")
        if "love_triangle" in concerns:
            wishes.append("I need to understand my feelings about the people in my life")
        if "war" in concerns:
            wishes.append("I'm dealing with trauma and fear from the war around me")
        if "motherhood" in concerns:
            wishes.append("I need support as a mother dealing with family challenges")
        if "loss" in concerns:
            wishes.append("I just lost someone important and I need grief support")
        if "independence" in concerns:
            wishes.append("I want to build my business and career on my own terms")
        if "social_status" in concerns:
            wishes.append("I'm dealing with social pressure and reputation concerns")
        if "identity" in concerns:
            wishes.append("I need to explore who I really am beyond what others expect")

        # Emotion-based wishes
        if self.current_emotions.get("fear", 0) > 0.5:
            wishes.append("I'm scared and I need a safe place to feel protected")
        if self.current_emotions.get("loneliness", 0) > 0.3:
            wishes.append("I feel so alone, I need someone to talk to")
        if self.current_emotions.get("anger", 0) > 0.5:
            wishes.append("I'm furious and need to release this anger somewhere")
        if self.current_emotions.get("anxiety", 0) > 0.3:
            wishes.append("I can't stop worrying, I need to calm my mind")
        if self.current_emotions.get("guilt", 0) > 0.3:
            wishes.append("I feel guilty about what I've done, I want to process this")

        return wishes[:3]  # Top 3 focus wishes

    def get_memory_wishes(self) -> list[str]:
        """What she's been needing CONSISTENTLY across chapters."""
        wishes = []
        top_recurring = self.recurring_concerns.most_common(3)

        for concern, count in top_recurring:
            if count >= 3:  # Only if it's truly recurring
                if concern == "survival":
                    wishes.append("I keep worrying about money — I need long-term financial stability")
                elif concern == "love_triangle":
                    wishes.append("My relationship confusion has been going on for a long time — I need clarity")
                elif concern == "independence":
                    wishes.append("I've been fighting for independence — I need resources to sustain it")
                elif concern == "loss":
                    wishes.append("I've experienced multiple losses — I need ongoing grief support")
                elif concern == "social_status":
                    wishes.append("Social pressure has been constant — I need to build inner confidence")

        return wishes[:2]  # Top 2 memory wishes

    def get_deep_wishes(self) -> list[str]:
        """What Compass detected she doesn't know she wants."""
        wishes = []
        for shell in self.compass.vault.all_shells:
            if shell.confidence > 0.2:
                wishes.append(f"Hidden: your feelings about {shell.topic} are stronger than you admit (confidence: {shell.confidence:.2f})")
        blooms = self.compass.harvest_blooms()
        for b in blooms:
            wishes.append(f"MATURE HIDDEN WISH: {b['wish_text']}")
        return wishes


def fulfill_wish(wish_text, soul_det=None):
    """Route and fulfill a single wish with the user's current Soul state."""
    module_path, _ = route(wish_text)
    catalog_id = module_path.replace("wish_engine.l2_", "").replace("wish_engine.", "")
    wish = ClassifiedWish(
        wish_text=wish_text, wish_type=WishType.FIND_RESOURCE,
        level=WishLevel.L2, fulfillment_strategy="soul",
    )
    det = soul_det or DetectorResults()
    result = universal_fulfill(catalog_id, wish, det)
    if result.recommendations:
        r = result.recommendations[0]
        return {"title": r.title, "category": r.category, "reason": r.relevance_reason[:100], "desc": r.description[:80]}
    return {"title": "No match", "category": "", "reason": "", "desc": ""}


def main():
    # Load Scarlett's dialogues
    with open(FIXTURES / "scarlett_full.jsonl") as f:
        all_dialogues = [json.loads(l) for l in f]

    # Group by phase
    phases = defaultdict(list)
    for d in all_dialogues:
        phases[d.get("chapter_phase", 0)].append(d)

    soul = SoulState()

    print("=" * 80)
    print("SCARLETT O'HARA: SOUL-BASED JOURNEY")
    print("From first line to final 'Tomorrow is another day'")
    print("=" * 80)

    for phase_num in sorted(phases.keys()):
        chapter_dialogues = phases[phase_num]
        first_line = chapter_dialogues[0]["text"][:70]

        print(f"\n{'━' * 80}")
        print(f"📖 PHASE {phase_num}: \"{first_line}...\"")
        print(f"   ({len(chapter_dialogues)} dialogues)")
        print(f"{'━' * 80}")

        # Process this chapter through Soul
        soul.process_chapter(chapter_dialogues, phase_num, "scarlett")

        # ── FOCUS (当下) ──────────────────────────────────────────
        focus_wishes = soul.get_focus_wishes()
        if focus_wishes:
            print(f"\n  🔴 FOCUS (当下她在想什么):")
            print(f"     Topics: {soul.current_topics}")
            print(f"     Emotions: {dict((k, round(v,2)) for k,v in sorted(soul.current_emotions.items(), key=lambda x:-x[1])[:3])}")
            for w in focus_wishes:
                rec = fulfill_wish(w, soul.get_detector_results())
                print(f"\n     Need: \"{w}\"")
                print(f"     → {rec['title']} [{rec['category']}]")

        # ── MEMORY (历史) ─────────────────────────────────────────
        memory_wishes = soul.get_memory_wishes()
        if memory_wishes:
            print(f"\n  🟡 MEMORY (一直在重复的主题):")
            print(f"     Recurring: {dict(soul.recurring_concerns.most_common(3))}")
            for w in memory_wishes:
                rec = fulfill_wish(w, soul.get_detector_results())
                print(f"\n     Pattern: \"{w}\"")
                print(f"     → {rec['title']} [{rec['category']}]")

        # ── DEEP (底层/Compass) ───────────────────────────────────
        deep_wishes = soul.get_deep_wishes()
        if deep_wishes:
            print(f"\n  🟣 DEEP (她自己不知道的):")
            for w in deep_wishes:
                print(f"     {w}")
                if w.startswith("MATURE"):
                    rec = fulfill_wish(w, soul.get_detector_results())
                    print(f"     → {rec['title']} [{rec['category']}]")

        # Compass summary
        shells = soul.compass.vault.all_shells
        if shells:
            print(f"\n  🔮 Compass: {len(shells)} shells")
            for s in shells:
                print(f"     {s.topic}: {s.stage.value} (conf={s.confidence:.2f}, signals={len(s.raw_signals)})")

    # ── FINAL SUMMARY ────────────────────────────────────────────────
    print(f"\n{'=' * 80}")
    print("SCARLETT'S COMPLETE SOUL JOURNEY")
    print(f"{'=' * 80}")
    print(f"\nRecurring life themes: {dict(soul.recurring_concerns.most_common(5))}")
    print(f"Emotional patterns: {dict((k, round(sum(v)/len(v), 2)) for k,v in soul.emotion_history.items() if v)}")
    print(f"Compass shells: {[(s.topic, s.stage.value, round(s.confidence,2)) for s in soul.compass.vault.all_shells]}")


if __name__ == "__main__":
    main()
