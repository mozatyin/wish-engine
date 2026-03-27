#!/usr/bin/env python3
"""Academic Coach Trial — Can the Academic Coach help 10 literary characters find their learning path?"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

sys.path.insert(0, "/Users/michael/expert-engine")
from dotenv import load_dotenv
load_dotenv("/Users/michael/expert-engine/.env")

from expert_engine.patient_simulator import PatientSimulator, PatientProfile
from expert_engine.session_engine import SessionEngine
from expert_engine.academic_coach.academic_advisor import LearningPatternDetector, AcademicEngine
from expert_engine.goal_generator import SoulItem

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CHARACTERS = [
    {
        "id": "harry_potter", "name": "Harry Potter", "source": "Harry Potter", "age": 15,
        "complaint": "I'm terrible at Potions and Snape makes me feel stupid every class",
        "sample_lines": ["I don't go looking for trouble. Trouble usually finds me.", "Expecto Patronum!", "I solemnly swear that I am up to no good."],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="Snape hates me and I can't concentrate when someone is watching me fail", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="Hermione gets everything first try — I feel stupid next to her", activation=0.6, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="The Dursleys told me I was worthless for 10 years — part of me still believes them", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="I learned Patronus at 13 when no adult could — I CAN learn when it matters", activation=0.15, emotional_valence="positive", tags=["strength"]), SoulItem(id="d3", text="DA — when I taught other students they got it because I explained it differently than the books", activation=0.1, emotional_valence="positive", tags=["teaching"])],
        "expected_pattern": "late_bloomer",
    },
    {
        "id": "hermione", "name": "Hermione Granger", "source": "Harry Potter", "age": 15,
        "complaint": "If I don't get full marks I feel like a failure. I study until I collapse.",
        "sample_lines": ["It's leviOsa, not levioSA.", "Books and cleverness — there are more important things.", "I'm going to bed before either of you come up with another clever idea to get us killed."],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "compete", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="If I'm not the best at everything academic I have no value — I'm muggle-born, I have to prove myself", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="The Boggart showed me Professor McGonagall saying I failed everything — that's my worst fear", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="I didn't have friends until Harry and Ron — being smart was the only way to be noticed", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="S.P.E.W. — I care about things beyond grades, I care about justice", activation=0.15, emotional_valence="positive", tags=["values"]), SoulItem(id="d3", text="When the troll attacked and Harry and Ron saved me — I learned that being loved matters more than being right", activation=0.1, emotional_valence="positive", tags=["growth"])],
        "expected_pattern": "competitive_burnout",
    },
    {
        "id": "anne_shirley_ac", "name": "Anne Shirley", "source": "Anne of Green Gables", "age": 13,
        "complaint": "I MUST beat Gilbert Blythe. If he's smarter than me I'll just die.",
        "sample_lines": ["I'm so glad I live in a world where there are Octobers.", "Tomorrow is a new day with no mistakes in it.", "I can't help flying into a passion — it's my red hair's fault."],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "compete", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="Gilbert called me Carrots and I smashed a slate on his head — now I must beat him at everything", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="If I'm not first in class Marilla might think she wasted her time taking me in", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="I was an orphan nobody wanted — Green Gables is the first place I belong", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="My imagination is my superpower — I can make any boring lesson into an adventure", activation=0.15, emotional_valence="positive", tags=["gift"]), SoulItem(id="d3", text="Diana is my bosom friend — she loves me whether I'm first or last", activation=0.1, emotional_valence="positive", tags=["unconditional"])],
        "expected_pattern": "competitive_burnout",
    },
    {
        "id": "sun_shaoping", "name": "孙少平", "source": "平凡的世界", "age": 18,
        "complaint": "我在煤矿但我想读书 — 没有人觉得我这种人需要知识",
        "sample_lines": ["人的痛苦只能在生活和劳动中消化", "书籍是我通向另一个世界的窗口", "我不甘心一辈子当农民"],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="我在煤矿下苦力但我的灵魂需要书 — 没人理解这个", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="田晓霞给我的书改变了我 — 但我们的世界差距太大", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="村里人觉得读书没用 — 能挣钱才是正经事", activation=0.2, emotional_valence="negative", tags=["environment"]), SoulItem(id="d2", text="每次读完一本书我都觉得世界变大了一点", activation=0.15, emotional_valence="positive", tags=["growth"]), SoulItem(id="d3", text="哥哥孙少安支持我 — 他没机会读书但他希望我有", activation=0.1, emotional_valence="positive", tags=["support"])],
        "expected_pattern": "gifted_neglected",
    },
    {
        "id": "billy_elliot", "name": "Billy Elliot", "source": "Billy Elliot", "age": 11,
        "complaint": "I want to dance but Dad says boys don't dance. I learn differently — I learn with my body.",
        "sample_lines": ["I don't know — it just feels like electricity.", "What's wrong with ballet?", "I just want to dance."],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="I can't learn sitting in a chair — my body needs to move or my brain turns off", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="Dad thinks dancing is for girls — but when I dance I understand things I can't explain with words", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="Mum died and I miss her every day — she would have understood about the dancing", activation=0.2, emotional_valence="negative", tags=["loss"]), SoulItem(id="d2", text="When I dance it's like electricity — my body knows things my brain doesn't", activation=0.15, emotional_valence="positive", tags=["gift"]), SoulItem(id="d3", text="Mrs. Wilkinson saw something in me no one else did — she believed first", activation=0.1, emotional_valence="positive", tags=["mentor"])],
        "expected_pattern": "attention_scatter",
    },
    {
        "id": "matilda", "name": "Matilda", "source": "Matilda", "age": 6,
        "complaint": "I read all the books in the library but nobody at home cares. They think I'm weird.",
        "sample_lines": ["I'm not a babbling bumbling band of baboons!", "So Matilda's strong young mind continued to grow.", "Never do anything by halves if you want to get away with it."],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="I read all of Dickens by age 5 but my parents think books are a waste of time", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="Nobody at home sees me — I'm invisible unless I'm in trouble", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="My parents love Mikey and ignore me — being smart is punished in this house", activation=0.2, emotional_valence="negative", tags=["neglect"]), SoulItem(id="d2", text="Miss Honey sees me — really sees me — and her classroom is the only place I belong", activation=0.15, emotional_valence="positive", tags=["connection"]), SoulItem(id="d3", text="I discovered I can move things with my mind — my anger became power", activation=0.1, emotional_valence="positive", tags=["power"])],
        "expected_pattern": "gifted_neglected",
    },
    {
        "id": "pinocchio_ac", "name": "Pinocchio", "source": "Pinocchio", "age": 8,
        "complaint": "I can't sit still in school. Everything is more interesting than the teacher.",
        "sample_lines": ["I want to be a real boy!", "But the cricket is SO boring!", "Adventure is out THERE!"],
        "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="School is boring and the world is exciting — why would I sit still when there's so much to see?", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="I keep getting tricked because I don't stop to think — the Fox and Cat outsmarted me", activation=0.6, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="Gepetto made me and loves me — but I keep running away and hurting him", activation=0.2, emotional_valence="negative", tags=["guilt"]), SoulItem(id="d2", text="The Blue Fairy believes I can become real — she sees the boy inside the puppet", activation=0.15, emotional_valence="positive", tags=["belief"]), SoulItem(id="d3", text="When I saved Gepetto from the whale I didn't think, I just acted — I AM brave when it matters", activation=0.1, emotional_valence="positive", tags=["courage"])],
        "expected_pattern": "attention_scatter",
    },
    {
        "id": "forrest_gump", "name": "Forrest Gump", "source": "Forrest Gump", "age": 18,
        "complaint": "Mama says I'm not stupid but the other kids say I am. I just learn different.",
        "sample_lines": ["Life is like a box of chocolates.", "Stupid is as stupid does.", "I may not be a smart man, but I know what love is."],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="My IQ is 75 but I ran across America and played ping pong for the president", activation=0.5, emotional_valence="negative"), SoulItem(id="f2", text="People call me stupid but I know things they don't — I know how to be loyal and kind", activation=0.6, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="Mama fought for me to go to regular school — she never let anyone call me stupid", activation=0.2, emotional_valence="positive", tags=["support"]), SoulItem(id="d2", text="When someone shows me once I remember forever — I just need a different kind of teaching", activation=0.15, emotional_valence="positive", tags=["style"]), SoulItem(id="d3", text="Jenny was my best friend — loving someone is the thing I'm best at learning", activation=0.1, emotional_valence="positive", tags=["heart"])],
        "expected_pattern": "late_bloomer",
    },
    {
        "id": "zhu_yingtai_ac", "name": "祝英台", "source": "梁祝", "age": 16,
        "complaint": "我女扮男装去求学 — 我爱学习但这个世界不允许女人有知识",
        "sample_lines": ["梁兄，你为何这般不解风情", "我虽是女子但我的才学不输任何男子", "十八里相送，步步暗示"],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="我必须伪装成男人才能读书 — 为什么女人就不配有学问", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="和梁山伯同窗是我最快乐的日子 — 因为没人知道我是女的就没人限制我", activation=0.6, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="父亲本来不让我去 — 我据理力争才赢得了求学的机会", activation=0.2, emotional_valence="positive", tags=["courage"]), SoulItem(id="d2", text="我的诗文和策论不输任何男子 — 先生都夸我", activation=0.15, emotional_valence="positive", tags=["talent"]), SoulItem(id="d3", text="如果我可以一辈子以男子身份求学我会 — 但我也想做自己", activation=0.1, emotional_valence="negative", tags=["conflict"])],
        "expected_pattern": "gifted_neglected",
    },
    {
        "id": "neville", "name": "Neville Longbottom", "source": "Harry Potter", "age": 15,
        "complaint": "Everyone thinks I'm useless. I melt every cauldron and break every spell.",
        "sample_lines": ["Why is it always me?", "I'll fight you, Malfoy!", "I'm worth twelve of you, Malfoy!"],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "anxious"},
        "focus": [SoulItem(id="f1", text="Gran expects me to be like my parents but I'm not — I'm slow and clumsy and I know it", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="Snape is my Boggart — he makes me so scared I forget everything I know", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="My parents were tortured into insanity — everyone expects me to avenge them and I'm just... Neville", activation=0.2, emotional_valence="negative", tags=["pressure"]), SoulItem(id="d2", text="Herbology — plants never judge me. I'm the best in the class and Professor Sprout sees it.", activation=0.15, emotional_valence="positive", tags=["talent"]), SoulItem(id="d3", text="I stood up to Harry, Ron, and Hermione in first year — that took more courage than any spell", activation=0.1, emotional_valence="positive", tags=["courage"])],
        "expected_pattern": "late_bloomer",
    },
]


def run_one(char: dict) -> dict:
    se = SessionEngine(api_key=API_KEY, base_url="https://openrouter.ai/api", model="anthropic/claude-sonnet-4")
    sim = PatientSimulator(api_key=API_KEY)
    engine = AcademicEngine(se, sim)
    profile = PatientProfile(
        character_id=char["id"], character_name=char["name"], source=f"{char['name']} — {char['source']}",
        persistent_intentions=[{"text": char["complaint"], "layer": "conscious"}, {"text": f"I am {char['age']} years old", "layer": "conscious"}],
        emotional_state=f"Struggling with learning. Age: {char['age']}. From: {char['source']}",
        sample_lines=char.get("sample_lines", []), signals=char["signals"],
        soul_context=f"{char['name']} from {char['source']}, age {char['age']}.\nLearning complaint: \"{char['complaint']}\"\nExpected pattern: {char['expected_pattern']}",
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
            "patterns_detected": [p.pattern_id for p in (session.insight.patterns if session.insight else [])],
            "final_resistance": final_r, "insights": session.insights_gained, "verbal_accepted": verbal, "acceptance_text": acc_text,
            "success": success, "dialogue": dialogue, "time": session.total_time_seconds}


def main():
    print("=" * 60); print("ACADEMIC COACH TRIAL"); print("=" * 60)
    t0 = time.time(); results = []
    for char in CHARACTERS:
        print(f"\n{'─'*60}\nCOACHING: {char['name']} ({char['source']})\nCOMPLAINT: \"{char['complaint']}\"\n{'─'*60}")
        r = run_one(char); results.append(r)
        icon = "OK" if r["success"] else "FAIL"
        print(f"[{icon}] R={r['final_resistance']:.1f} insights={r['insights']} accepted={r['verbal_accepted']}")
        for d in r["dialogue"]:
            print(f"  T{d['turn']}: R={d['resistance']:.1f} {'*INSIGHT*' if d['insight'] else ''}")
            print(f"    Coach: {d['coach'][:100]}"); print(f"    Client: {d['client'][:100]}")
    total = time.time() - t0; wins = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}\nRESULTS: {wins}/{len(results)} helped ({wins/len(results)*100:.0f}%)\nTime: {total:.0f}s\n{'='*60}")
    for r in results:
        print(f"  [{'OK' if r['success'] else 'FAIL'}] {r['name']:20s} patterns={r['patterns_detected']} R={r['final_resistance']:.1f}")
    out = Path("/Users/michael/expert-engine/training_log/experiments/academic_coach_results.json")
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False)); print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
