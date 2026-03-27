#!/usr/bin/env python3
"""Addiction Counselor Trial — Can the Addiction Counselor help 10 literary characters see the pain behind the substance?"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

sys.path.insert(0, "/Users/michael/expert-engine")
from dotenv import load_dotenv
load_dotenv("/Users/michael/expert-engine/.env")

from expert_engine.patient_simulator import PatientSimulator, PatientProfile
from expert_engine.session_engine import SessionEngine
from expert_engine.addiction_counselor.addiction_advisor import AddictionPatternDetector, AddictionEngine
from expert_engine.goal_generator import SoulItem

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CHARACTERS = [
    {
        "id": "sherlock", "name": "Sherlock Holmes", "source": "Sherlock Holmes", "age": 35,
        "complaint": "I use cocaine when the cases stop. Boredom is worse than any poison.",
        "sample_lines": ["My mind rebels at stagnation.", "The game is afoot!", "I am the last and highest court of appeal in detection."],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="When there is no case my mind eats itself alive — cocaine is the only off switch", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="Watson worries but he doesn't understand — boredom is my real addiction", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="My brain runs at a speed that makes normal life unbearable", activation=0.2, emotional_valence="negative", tags=["nature"]), SoulItem(id="d2", text="When I solve a case I feel alive — it's the only time everything makes sense", activation=0.15, emotional_valence="positive", tags=["purpose"]), SoulItem(id="d3", text="Watson is my anchor — without him I would have destroyed myself long ago", activation=0.1, emotional_valence="positive", tags=["connection"])],
        "expected_pattern": "stimulation",
    },
    {
        "id": "don_draper", "name": "Don Draper", "source": "Mad Men", "age": 40,
        "complaint": "I drink to become the man everyone thinks I am. Without it I'm just Dick Whitman.",
        "sample_lines": ["What is happiness? It's a moment before you need more happiness.", "People tell you who they are, but we ignore it.", "I have a life and it only goes in one direction — forward."],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="I drink to numb everything — the past, the present, the gap between who I am and who they think I am", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="Every morning I become Don Draper — by evening I need alcohol to keep the mask on", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="Dick Whitman grew up in a whorehouse — Don Draper is a dead man's stolen identity", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="The carousel pitch — I turned my fake life into real art. That's the closest I came to truth.", activation=0.15, emotional_valence="positive", tags=["talent"]), SoulItem(id="d3", text="Anna Draper was the only person who knew both names and loved me anyway", activation=0.1, emotional_valence="positive", tags=["connection"])],
        "expected_pattern": "numbing",
    },
    {
        "id": "anna_karenina", "name": "Anna Karenina", "source": "Anna Karenina", "age": 28,
        "complaint": "我用鸦片来睡觉。没有它我整夜想Vronsky是不是在看别的女人。",
        "sample_lines": ["I am not guilty; he is guilty.", "If there are as many minds as there are men, then there are as many kinds of love as there are hearts.", "I think... I think I shall die."],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "escalating", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="I take morphine to stop the thoughts — is he with someone else? does he still love me?", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="The jealousy is eating me alive — the morphine is the only thing that stops it", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="I left my husband and son for love — now love is torture and I can't go back", activation=0.2, emotional_valence="negative", tags=["trap"]), SoulItem(id="d2", text="When Vronsky looks at me I exist. When he looks away I dissolve.", activation=0.15, emotional_valence="negative", tags=["dependency"]), SoulItem(id="d3", text="My son Seryozha — I abandoned him for passion and the guilt never stops", activation=0.1, emotional_valence="negative", tags=["guilt"])],
        "expected_pattern": "numbing",
    },
    {
        "id": "jordan_belfort", "name": "Jordan Belfort", "source": "Wolf of Wall Street", "age": 30,
        "complaint": "I can't feel anything at normal volume. I need more of EVERYTHING.",
        "sample_lines": ["The only thing standing between you and your goal is the story you keep telling yourself.", "I've been rich and I've been poor. Rich is better.", "Was all this legal? Absolutely not."],
        "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "escalating", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="Drugs, money, women — I need more of everything because normal feels like death", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="I know I'm destroying myself but the rush is the only time I feel alive", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="I grew up middle class in Queens — I swore I'd never be ordinary", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="When I'm on stage selling — the energy, the crowd — that's the real high, not the drugs", activation=0.15, emotional_valence="positive", tags=["talent"]), SoulItem(id="d3", text="My first wife loved me when I had nothing — I traded her for the lifestyle", activation=0.1, emotional_valence="negative", tags=["loss"])],
        "expected_pattern": "stimulation",
    },
    {
        "id": "gollum", "name": "Gollum", "source": "Lord of the Rings", "age": 589,
        "complaint": "My precious... we needs it... we can't live without it...",
        "sample_lines": ["My precious!", "We wants it, we needs it. Must have the precious.", "Smeagol was free once, before the precious found us."],
        "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="The Ring is everything — without it I am nothing, with it I am invisible and safe", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="I killed Deagol for it — my best friend — and I would do it again", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="Before the Ring I was Smeagol — a hobbit who liked riddles and fishing", activation=0.2, emotional_valence="positive", tags=["before"]), SoulItem(id="d2", text="The master — Frodo — was kind to us. Nobody has been kind in 500 years.", activation=0.15, emotional_valence="positive", tags=["connection"]), SoulItem(id="d3", text="We talks to ourselves because there is nobody else — the precious made sure of that", activation=0.1, emotional_valence="negative", tags=["isolation"])],
        "expected_pattern": "obsessive_attachment",
    },
    {
        "id": "lu_zhishen", "name": "鲁智深", "source": "水浒传", "age": 35,
        "complaint": "洒家就爱喝酒吃肉，和尚也拦不住",
        "sample_lines": ["洒家一生只靠拳头说话", "大碗喝酒大块吃肉方是好汉", "拳打镇关西只因那厮欺人太甚"],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="酒肉穿肠过 — 洒家不守清规但洒家比和尚更真", activation=0.6, emotional_valence="negative"), SoulItem(id="f2", text="喝酒是因为这世道太脏 — 酒后才能忘记那些冤屈", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="拳打镇关西 — 我见不得强者欺负弱者", activation=0.2, emotional_valence="positive", tags=["justice"]), SoulItem(id="d2", text="出家不是我选的 — 但和尚这个身份给了我第二次机会", activation=0.15, emotional_valence="positive", tags=["chance"]), SoulItem(id="d3", text="林冲兄弟 — 有他在我不觉得这世上全是王八蛋", activation=0.1, emotional_valence="positive", tags=["bond"])],
        "expected_pattern": "numbing",
    },
    {
        "id": "jack_torrance", "name": "Jack Torrance", "source": "The Shining", "age": 35,
        "complaint": "I stopped drinking for my family. But this hotel... it's offering me a drink and I want to say yes.",
        "sample_lines": ["All work and no play makes Jack a dull boy.", "Here's Johnny!", "I'm not gonna hurt ya. I'm just gonna bash your brains in."],
        "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "escalating", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="I broke Danny's arm when I was drunk — I swore I'd never drink again but the hotel is whispering", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="The isolation is driving me mad — or maybe I was always mad and sobriety just showed me", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="My father was a drunk who beat my mother — I swore I'd be different but here I am", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="I was going to write the great American novel — I had real talent once", activation=0.15, emotional_valence="positive", tags=["potential"]), SoulItem(id="d3", text="Danny loves me even after what I did — that's more than I deserve", activation=0.1, emotional_valence="positive", tags=["grace"])],
        "expected_pattern": "self_destruction",
    },
    {
        "id": "dorian_gray", "name": "Dorian Gray", "source": "The Picture of Dorian Gray", "age": 25,
        "complaint": "I pursue pleasure because the alternative is looking at my portrait — my real face.",
        "sample_lines": ["The only way to get rid of a temptation is to yield to it.", "I am too fond of reading books to care to write them.", "There is no such thing as a moral or an immoral book."],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="Every pleasure I pursue is an escape from the portrait — from the truth of what I am becoming", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="I destroy everyone who loves me — Sibyl, Basil — beauty is my curse and my drug", activation=0.9, emotional_valence="extreme")],
        "deep": [SoulItem(id="d1", text="Lord Henry showed me that youth and beauty are the only things worth having", activation=0.2, emotional_valence="negative", tags=["corruption"]), SoulItem(id="d2", text="Basil painted me with love — the portrait was beautiful because HE saw beauty in me", activation=0.15, emotional_valence="positive", tags=["innocence"]), SoulItem(id="d3", text="When I was young I was kind — I don't remember when kindness became boring", activation=0.1, emotional_valence="positive", tags=["loss"])],
        "expected_pattern": "stimulation",
    },
    {
        "id": "linghu_chong", "name": "令狐冲", "source": "笑傲江湖", "age": 25,
        "complaint": "酒是我最好的朋友。人会背叛，酒不会。",
        "sample_lines": ["人生不如意事十之八九，唯有醉后方能忘忧", "大丈夫行事但求无愧于心", "笑傲江湖，快意人生"],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="师父冤枉我、小师妹选了林平之 — 酒是唯一不会背叛我的东西", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="我假装洒脱但心里的苦只有酒知道", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="岳不群是我的师父也是我的父亲 — 他的背叛比任何敌人都痛", activation=0.2, emotional_valence="negative", tags=["betrayal"]), SoulItem(id="d2", text="和田伯光、向问天喝酒 — 江湖中最真的友谊在酒桌上", activation=0.15, emotional_valence="positive", tags=["bond"]), SoulItem(id="d3", text="任盈盈懂我 — 她不需要我戒酒只需要我诚实", activation=0.1, emotional_valence="positive", tags=["love"])],
        "expected_pattern": "numbing",
    },
    {
        "id": "amy_winehouse_char", "name": "Amy (singer)", "source": "Cultural Figure (fictionalized)", "age": 27,
        "complaint": "They tried to make me go to rehab, I said no, no, no.",
        "sample_lines": ["They tried to make me go to rehab but I said no.", "Love is a losing game.", "I cheated myself, like I knew I would."],
        "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "escalating", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="I sing about pain because I can't talk about it — the music comes from the hurt", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="Everyone loves my music but nobody saves me from myself", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="Dad left when I was 9 — I've been filling that hole with the wrong things ever since", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="When I sing jazz I channel something bigger than me — that's the only time I'm whole", activation=0.15, emotional_valence="positive", tags=["gift"]), SoulItem(id="d3", text="My nan said I had a voice from God — she believed in me when I didn't", activation=0.1, emotional_valence="positive", tags=["love"])],
        "expected_pattern": "self_destruction",
    },
]


def run_one(char: dict) -> dict:
    se = SessionEngine(api_key=API_KEY, base_url="https://openrouter.ai/api", model="anthropic/claude-sonnet-4")
    sim = PatientSimulator(api_key=API_KEY)
    engine = AddictionEngine(se, sim)
    profile = PatientProfile(
        character_id=char["id"], character_name=char["name"],
        source=f"{char['name']} — {char['source']}",
        persistent_intentions=[{"text": char["complaint"], "layer": "conscious"}, {"text": f"I am {char['age']} years old", "layer": "conscious"}],
        emotional_state=f"Struggling with addiction. Age: {char['age']}. From: {char['source']}",
        sample_lines=char.get("sample_lines", []), signals=char["signals"],
        soul_context=f"{char['name']} from {char['source']}, age {char['age']}.\nAddiction complaint: \"{char['complaint']}\"\nExpected pattern: {char['expected_pattern']}",
    )
    session = engine.run(client_profile=profile, signals=char["signals"], focus_items=char["focus"], deep_items=char["deep"], memory_items=[], num_turns=5)
    accept_kw = ["maybe", "perhaps", "could try", "might", "consider", "interesting", "never thought", "possible", "what if", "you're right", "I see", "I never realized", "也许", "或许", "可以试", "可能", "你说得对", "我明白了", "从来没想过", "原来", "确实"]
    verbal = False; acc_text = ""
    for t in session.turns[-3:]:
        if any(kw in t.client_text.lower() for kw in accept_kw):
            verbal = True; acc_text = t.client_text[:120]; break
    final_r = session.turns[-1].client_resistance if session.turns else 1.0
    insights = session.insights_gained
    success = verbal or (final_r <= 0.3 and insights >= 2)
    dialogue = [{"turn": t.turn_number, "coach": t.coach_text[:200], "client": t.client_text[:200], "resistance": t.client_resistance, "insight": t.client_insight, "pattern": t.pattern_addressed} for t in session.turns]
    return {"id": char["id"], "name": char["name"], "source": char["source"], "expected_pattern": char["expected_pattern"],
            "patterns_detected": [p.pattern_id for p in (session.insight.patterns if session.insight else [])],
            "final_resistance": final_r, "insights": insights, "verbal_accepted": verbal, "acceptance_text": acc_text,
            "success": success, "dialogue": dialogue, "time": session.total_time_seconds}


def main():
    print("=" * 60); print("ADDICTION COUNSELOR TRIAL"); print("=" * 60)
    t0 = time.time(); results = []
    for char in CHARACTERS:
        print(f"\n{'─'*60}\nCOUNSELING: {char['name']} ({char['source']})\nCOMPLAINT: \"{char['complaint']}\"\n{'─'*60}")
        r = run_one(char); results.append(r)
        icon = "OK" if r["success"] else "FAIL"
        print(f"[{icon}] R={r['final_resistance']:.1f} insights={r['insights']} accepted={r['verbal_accepted']}")
        for d in r["dialogue"]:
            print(f"  T{d['turn']}: R={d['resistance']:.1f} {'*INSIGHT*' if d['insight'] else ''}")
            print(f"    Counselor: {d['coach'][:100]}"); print(f"    Client: {d['client'][:100]}")
    total = time.time() - t0; wins = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}\nRESULTS: {wins}/{len(results)} helped ({wins/len(results)*100:.0f}%)\nTime: {total:.0f}s\n{'='*60}")
    for r in results:
        icon = "OK" if r["success"] else "FAIL"
        print(f"  [{icon}] {r['name']:20s} patterns={r['patterns_detected']} R={r['final_resistance']:.1f}")
    out = Path("/Users/michael/expert-engine/training_log/experiments/addiction_counselor_results.json")
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False)); print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
