#!/usr/bin/env python3
"""Sleep Consultant Trial — Can the Sleep Consultant help 10 literary characters find peace at night?"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

sys.path.insert(0, "/Users/michael/expert-engine")
from dotenv import load_dotenv
load_dotenv("/Users/michael/expert-engine/.env")

from expert_engine.patient_simulator import PatientSimulator, PatientProfile
from expert_engine.session_engine import SessionEngine
from expert_engine.sleep_consultant.sleep_advisor import SleepPatternDetector, SleepEngine
from expert_engine.goal_generator import SoulItem

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CHARACTERS = [
    {"id": "hamlet_sleep", "name": "Hamlet", "source": "Hamlet", "age": 30, "complaint": "To sleep, perchance to dream — ay, there's the rub. I fear what comes in sleep.",
     "sample_lines": ["To be or not to be.", "To die, to sleep — to sleep, perchance to dream.", "What dreams may come when we have shuffled off this mortal coil."],
     "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "frozen"},
     "focus": [SoulItem(id="f1", text="I fear sleep because in dreams the truth arrives — my father's ghost, my uncle's guilt, my own paralysis", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="Awake I can pretend to be mad. Asleep I am truly mad — the dreams are real.", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="My father's ghost appeared at night — sleep became the gateway to horror", activation=0.2, emotional_valence="negative", tags=["trauma"]), SoulItem(id="d2", text="The players — when art imitates truth I feel awake for the first time", activation=0.15, emotional_valence="positive", tags=["clarity"]), SoulItem(id="d3", text="Horatio watches over me — having someone you trust near makes the night less infinite", activation=0.1, emotional_valence="positive", tags=["anchor"])],
     "expected_pattern": "nightmare_dread"},
    {"id": "lady_macbeth_sleep", "name": "Lady Macbeth", "source": "Macbeth", "age": 35, "complaint": "Out, damned spot! I walk in my sleep and try to wash blood that isn't there.",
     "sample_lines": ["Out, damned spot!", "What's done cannot be undone.", "All the perfumes of Arabia will not sweeten this little hand."],
     "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I sleepwalk trying to wash blood from my hands — awake I was fearless, asleep I am haunted", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="I told Macbeth 'a little water clears us of this deed' — I was wrong. Nothing clears it.", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="I was the strong one — 'unsex me here' — I became ruthless so he could be king", activation=0.2, emotional_valence="negative", tags=["sacrifice"]), SoulItem(id="d2", text="Before the murder, our love was real — we were partners in everything", activation=0.15, emotional_valence="positive", tags=["before"]), SoulItem(id="d3", text="The doctor watches me sleep — someone finally sees what the crown cost me", activation=0.1, emotional_valence="positive", tags=["seen"])],
     "expected_pattern": "guilt_insomnia"},
    {"id": "anna_k_sleep", "name": "Anna Karenina", "source": "Anna Karenina", "age": 28, "complaint": "I take morphine to sleep. Without it the jealousy eats me alive all night.",
     "sample_lines": ["I am guilty.", "All happy families are alike; every unhappy family is unhappy in its own way.", "I think I shall die."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "escalating", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="At night my mind races — is Vronsky with someone else? does he still love me? the morphine stops the questions", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="I left everything for love and now love won't let me sleep", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="I abandoned my son Seryozha — the guilt visits me every night at 3am", activation=0.2, emotional_valence="negative", tags=["guilt"]), SoulItem(id="d2", text="When Vronsky holds me I can sleep — his arms are the only medicine that works", activation=0.15, emotional_valence="positive", tags=["dependency"]), SoulItem(id="d3", text="I dream of trains — the same dream, over and over", activation=0.1, emotional_valence="negative", tags=["premonition"])],
     "expected_pattern": "anxiety_vigilance"},
    {"id": "raskolnikov_sleep", "name": "Raskolnikov", "source": "Crime and Punishment", "age": 23, "complaint": "I killed her and now I can't sleep. The ceiling of my room is a courtroom.",
     "sample_lines": ["Am I a Napoleon or a louse?", "Pain and suffering are always inevitable for a large intelligence.", "I wanted to prove I was not a louse."],
     "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="Every night I see the old woman's eyes — they're open and they're looking at me", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="My tiny room is a coffin — the walls close in at night and I can't breathe", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="I was a brilliant student — now I'm a murderer who can't sleep in a room the size of a closet", activation=0.2, emotional_valence="negative", tags=["fall"]), SoulItem(id="d2", text="Sonya reads to me — her voice is the only thing that quiets the noise in my head", activation=0.15, emotional_valence="positive", tags=["peace"]), SoulItem(id="d3", text="Confession might bring sleep — but confession means prison. Is prison worse than this?", activation=0.1, emotional_valence="negative", tags=["choice"])],
     "expected_pattern": "guilt_insomnia"},
    {"id": "holden_sleep", "name": "Holden Caulfield", "source": "The Catcher in the Rye", "age": 16, "complaint": "I can't sleep in hotel rooms. Or dorms. Or anywhere that's not home. And I don't have a home.",
     "sample_lines": ["Don't ever tell anybody anything. If you do, you start missing everybody.", "I'm the most terrific liar you ever saw.", "People never notice anything."],
     "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I lie in bed in this crummy hotel and I can't sleep because everyone is a phony and I'm alone", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="Allie died and I can't stop thinking about his baseball mitt — at 3am everything comes back to Allie", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="Allie's red hair — my brother died and nobody talks about him. Night is when he visits.", activation=0.2, emotional_valence="negative", tags=["grief"]), SoulItem(id="d2", text="Phoebe's face when she's sleeping — she looks so peaceful. I want to protect that.", activation=0.15, emotional_valence="positive", tags=["love"]), SoulItem(id="d3", text="The ducks in Central Park — where do they go in winter? If they survive, maybe I can too.", activation=0.1, emotional_valence="positive", tags=["hope"])],
     "expected_pattern": "loneliness_insomnia"},
    {"id": "lin_daiyu_sleep", "name": "林黛玉", "source": "红楼梦", "age": 16, "complaint": "夜里咳嗽到天明。不是只有病 — 是心事太重了。",
     "sample_lines": ["一朝春尽红颜老", "质本洁来还洁去", "风刀霜剑严相逼"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="夜里咳嗽不止 — 身体的病和心里的病混在一起分不清", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="宝玉在不在想我？宝钗是不是在他身边？这些问题让我整夜睡不着", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="父母双亡 — 寄人篱下的孩子夜里醒来不知道自己在哪", activation=0.2, emotional_valence="negative", tags=["orphan"]), SoulItem(id="d2", text="写诗的夜晚是最好的 — 把心事变成文字我就能睡一会儿", activation=0.15, emotional_valence="positive", tags=["release"]), SoulItem(id="d3", text="紫鹃陪着我 — 她是我夜里唯一的温暖", activation=0.1, emotional_valence="positive", tags=["companion"])],
     "expected_pattern": "anxiety_vigilance"},
    {"id": "werther_sleep", "name": "Werther", "source": "Sorrows of Young Werther", "age": 22, "complaint": "I write all night because I can't stop thinking about Charlotte. Sleep is another form of separation.",
     "sample_lines": ["I have so much in me, and the feeling for her absorbs it all.", "Nature alone has inexhaustible riches.", "I am not well, not ill — I feel nothing."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="Sleep means hours without thinking of Charlotte — and I can't bear to stop thinking of her", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="My restless nights produce letters nobody should read — the fever of unrequited love", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Nature soothes me in daytime — but at night nature sleeps and I'm left alone with my heart", activation=0.2, emotional_valence="negative", tags=["isolation"]), SoulItem(id="d2", text="Writing to Charlotte — even if she never reads it, the act of writing lets me be close to her", activation=0.15, emotional_valence="positive", tags=["connection"]), SoulItem(id="d3", text="Homer's poems — when I read them at night I feel part of something ancient and enduring", activation=0.1, emotional_valence="positive", tags=["anchor"])],
     "expected_pattern": "loneliness_insomnia"},
    {"id": "don_draper_sleep", "name": "Don Draper", "source": "Mad Men", "age": 40, "complaint": "I drink at 3am because the alternative is lying in the dark with Dick Whitman.",
     "sample_lines": ["What is happiness?", "People tell you who they are.", "I have a life and it only goes in one direction."],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="At 3am the mask comes off — Don Draper sleeps but Dick Whitman is wide awake", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="I pour a drink because the silence is louder than any client meeting", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="I grew up in a whorehouse — night was never safe, never quiet, never mine", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="Anna Draper — she knew both names and let me sleep on her couch. That was the last time I slept through the night.", activation=0.15, emotional_valence="positive", tags=["safety"]), SoulItem(id="d3", text="The ocean in the final scene — the sound of waves is what silence should sound like", activation=0.1, emotional_valence="positive", tags=["peace"])],
     "expected_pattern": "unfinished_day"},
    {"id": "harry_sleep", "name": "Harry Potter", "source": "Harry Potter", "age": 15, "complaint": "I dream of Voldemort. Our minds are connected. Sleep is where he finds me.",
     "sample_lines": ["I don't go looking for trouble.", "Expecto Patronum!", "I solemnly swear that I am up to no good."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="My scar burns at night — Voldemort's thoughts invade my dreams and I wake up screaming", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="I can't tell anyone because they'll think I'm going dark — but the nightmares are getting worse", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="I slept in a cupboard for 10 years — night was the only time I could imagine being someone else", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="Ron snoring in the next bed — that sound means I'm home, I'm at Hogwarts, I'm safe", activation=0.15, emotional_valence="positive", tags=["safety"]), SoulItem(id="d3", text="Sirius said 'the ones who love us never really leave us' — I dream of my parents too, and those dreams I don't want to end", activation=0.1, emotional_valence="positive", tags=["comfort"])],
     "expected_pattern": "nightmare_dread"},
    {"id": "fugui_sleep", "name": "福贵", "source": "活着", "age": 70, "complaint": "老了睡不着。不是身体的问题。是夜里太安静了，所有死去的人都回来了。",
     "sample_lines": ["人是为了活着本身而活着", "我认识的人一个一个死去", "老牛和我一起走在路上"],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "frozen"},
     "focus": [SoulItem(id="f1", text="家珍、有庆、凤霞、二喜、苦根 — 夜里他们一个一个来看我", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="老了只剩我和一头老牛 — 白天还好，夜里安静得能听见心跳", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="年轻时我赌光了家产 — 那是一切苦难的起点", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="有庆跑步的样子 — 那孩子跑起来像飞一样", activation=0.15, emotional_valence="positive", tags=["memory"]), SoulItem(id="d3", text="活着 — 就是活着本身。不为谁。不为什么。就是活着。", activation=0.1, emotional_valence="positive", tags=["acceptance"])],
     "expected_pattern": "guilt_insomnia"},
]


def run_one(char: dict) -> dict:
    se = SessionEngine(api_key=API_KEY, base_url="https://openrouter.ai/api", model="anthropic/claude-sonnet-4")
    sim = PatientSimulator(api_key=API_KEY)
    engine = SleepEngine(se, sim)
    profile = PatientProfile(
        character_id=char["id"], character_name=char["name"], source=f"{char['name']} — {char['source']}",
        persistent_intentions=[{"text": char["complaint"], "layer": "conscious"}, {"text": f"I am {char['age']} years old", "layer": "conscious"}],
        emotional_state=f"Sleep struggles. Age: {char['age']}. From: {char['source']}",
        sample_lines=char.get("sample_lines", []), signals=char["signals"],
        soul_context=f"{char['name']} from {char['source']}, age {char['age']}.\nSleep complaint: \"{char['complaint']}\"\nExpected pattern: {char['expected_pattern']}",
    )
    session = engine.run(client_profile=profile, signals=char["signals"], focus_items=char["focus"], deep_items=char["deep"], memory_items=[], num_turns=5)
    accept_kw = ["maybe", "perhaps", "could try", "might", "consider", "interesting", "never thought", "possible", "what if", "you're right", "I see", "I never realized", "也许", "或许", "可以试", "可能", "你说得对", "我明白了", "从来没想过", "原来", "确实"]
    verbal = False; acc_text = ""
    for t in session.turns[-3:]:
        if any(kw in t.client_text.lower() for kw in accept_kw):
            verbal = True; acc_text = t.client_text[:120]; break
    final_r = session.turns[-1].client_resistance if session.turns else 1.0
    success = verbal or (final_r <= 0.3 and session.insights_gained >= 2)
    dialogue = [{"turn": t.turn_number, "coach": t.coach_text[:200], "client": t.client_text[:200], "resistance": t.client_resistance, "insight": t.client_insight, "pattern": t.pattern_addressed} for t in session.turns]
    return {"id": char["id"], "name": char["name"], "source": char["source"], "expected_pattern": char["expected_pattern"],
            "patterns_detected": [p.pattern_id for p in (session.insight.patterns if session.insight else [])], "final_resistance": final_r,
            "insights": session.insights_gained, "verbal_accepted": verbal, "acceptance_text": acc_text, "success": success, "dialogue": dialogue, "time": session.total_time_seconds}

def main():
    print("=" * 60); print("SLEEP CONSULTANT TRIAL"); print("=" * 60)
    t0 = time.time(); results = []
    for char in CHARACTERS:
        print(f"\n{'─'*60}\nCONSULTING: {char['name']} ({char['source']})\nINSOMNIA: \"{char['complaint']}\"\n{'─'*60}")
        r = run_one(char); results.append(r)
        icon = "OK" if r["success"] else "FAIL"
        print(f"[{icon}] R={r['final_resistance']:.1f} insights={r['insights']} accepted={r['verbal_accepted']}")
        for d in r["dialogue"]:
            print(f"  T{d['turn']}: R={d['resistance']:.1f} {'*INSIGHT*' if d['insight'] else ''}")
            print(f"    Consultant: {d['coach'][:100]}"); print(f"    Client: {d['client'][:100]}")
    total = time.time() - t0; wins = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}\nRESULTS: {wins}/{len(results)} helped ({wins/len(results)*100:.0f}%)\nTime: {total:.0f}s\n{'='*60}")
    for r in results:
        print(f"  [{'OK' if r['success'] else 'FAIL'}] {r['name']:20s} patterns={r['patterns_detected']} R={r['final_resistance']:.1f}")
    out = Path("/Users/michael/expert-engine/training_log/experiments/sleep_consultant_results.json")
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False)); print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
