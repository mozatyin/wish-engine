#!/usr/bin/env python3
"""Nutritionist Trial — Can the Nutritionist help 10 literary characters heal their relationship with food?"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

sys.path.insert(0, "/Users/michael/expert-engine")
from dotenv import load_dotenv
load_dotenv("/Users/michael/expert-engine/.env")

from expert_engine.patient_simulator import PatientSimulator, PatientProfile
from expert_engine.session_engine import SessionEngine
from expert_engine.nutritionist.nutrition_advisor import NutritionPatternDetector, NutritionEngine
from expert_engine.goal_generator import SoulItem

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CHARACTERS = [
    {"id": "goldilocks", "name": "Goldilocks", "source": "Goldilocks and the Three Bears", "age": 19, "complaint": "Everything is too much or too little. I can never find the right amount to eat.",
     "sample_lines": ["This porridge is too hot!", "This one is too cold.", "This one is just right."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I can never find the right amount — too much makes me sick, too little makes me anxious", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="I broke into someone's house just to find food that felt right — I'm that desperate for balance", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="My mother never got portions right — feast or famine, nothing in between", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="Baby Bear's porridge was just right — that moment of perfect is what I chase in every meal", activation=0.15, emotional_valence="positive", tags=["peace"]), SoulItem(id="d3", text="I want a home where the food is always just right — where I don't have to break in to find comfort", activation=0.1, emotional_valence="positive", tags=["hope"])],
     "expected_pattern": "deprivation_cycle"},
    {"id": "winnie_pooh", "name": "Winnie the Pooh", "source": "Winnie the Pooh", "age": 10, "complaint": "Oh bother. I ate all the honey again. My tummy hurts but I can't stop.",
     "sample_lines": ["Oh bother!", "Is it time for a little smackerel of something?", "I am a bear of very little brain, and long words bother me."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I eat honey when I'm happy, when I'm sad, when I'm bored — honey is my answer to everything", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="I got stuck in Rabbit's door because I ate too much — my body pays for what my feelings need", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="Christopher Robin is leaving — the honey can't fill the hole he'll leave behind", activation=0.2, emotional_valence="negative", tags=["loss"]), SoulItem(id="d2", text="Sitting with Piglet in the Hundred Acre Wood, not eating, just being — that was enough", activation=0.15, emotional_valence="positive", tags=["connection"]), SoulItem(id="d3", text="I am a bear of very little brain — but I know what friendship tastes like and it's sweeter than honey", activation=0.1, emotional_valence="positive", tags=["wisdom"])],
     "expected_pattern": "emotional_eating"},
    {"id": "zhu_bajie", "name": "猪八戒", "source": "西游记", "age": 500, "complaint": "我知道不该贪吃。但是看到吃的就控制不住。师父说我六根不净。",
     "sample_lines": ["有吃的吗？", "师父！前面有个村庄！", "我老猪就是嘴馋了点"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="从天蓬元帅变成猪 — 我用吃来忘记我曾经是谁", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="师兄弟都看不起我 — 吃是我唯一不会失败的事", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="我曾是天庭的天蓬元帅 — 一次错误让我堕入猪身，吃是唯一还像天上日子的事", activation=0.2, emotional_valence="negative", tags=["fall"]), SoulItem(id="d2", text="师父收了我 — 有人愿意带着我走，这比任何一顿饭都饱", activation=0.15, emotional_valence="positive", tags=["belonging"]), SoulItem(id="d3", text="保护师父取经 — 我不只是一头猪，我也是一个徒弟", activation=0.1, emotional_valence="positive", tags=["purpose"])],
     "expected_pattern": "emotional_eating"},
    {"id": "snow_white_food", "name": "Snow White", "source": "Snow White", "age": 17, "complaint": "I can't eat anything without checking if it's safe. The apple ruined me.",
     "sample_lines": ["Someday my prince will come.", "Mirror, mirror on the wall...", "Oh, what a lovely apple!"],
     "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "frozen"},
     "focus": [SoulItem(id="f1", text="The apple was poisoned — now every food could be poison. I check and recheck and still can't trust it.", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="The person I trusted most — my stepmother — tried to kill me with food. How do I ever eat without fear?", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="The dwarfs fed me safe food — their home was the first place I ate without fear", activation=0.2, emotional_valence="positive", tags=["safety"]), SoulItem(id="d2", text="My real mother died — food from a mother should be love, not poison", activation=0.15, emotional_valence="negative", tags=["betrayal"]), SoulItem(id="d3", text="I woke up from the poison — I survived. My body is stronger than the apple.", activation=0.1, emotional_valence="positive", tags=["survival"])],
     "expected_pattern": "food_fear"},
    {"id": "hansel_gretel", "name": "Hansel", "source": "Hansel and Gretel", "age": 12, "complaint": "We almost starved. Then a house made of candy almost killed us. Food is never just food for me.",
     "sample_lines": ["Leave a trail of breadcrumbs.", "Don't eat the house, Gretel!", "We have to find our way home."],
     "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "frozen"},
     "focus": [SoulItem(id="f1", text="Our parents abandoned us because there wasn't enough food — hunger means being thrown away", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="The candy house was a trap — abundance is always a trick, always has a price", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="I saved breadcrumbs to find our way back — I hoard food because food is the trail home", activation=0.2, emotional_valence="negative", tags=["survival"]), SoulItem(id="d2", text="Gretel and I survived together — sharing food with her is the one safe thing", activation=0.15, emotional_valence="positive", tags=["bond"]), SoulItem(id="d3", text="We found treasure in the witch's house — maybe one day abundance won't scare me", activation=0.1, emotional_valence="positive", tags=["hope"])],
     "expected_pattern": "survival_eating"},
    {"id": "oliver_twist", "name": "Oliver Twist", "source": "Oliver Twist", "age": 10, "complaint": "Please sir, I want some more. I've been hungry my whole life. Even when I eat, I'm still hungry.",
     "sample_lines": ["Please, sir, I want some more.", "God bless you, sir!", "I'm not afraid."],
     "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "frozen"},
     "focus": [SoulItem(id="f1", text="I asked for more and got beaten — hunger is my constant companion but asking for food is dangerous", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="Even when my bowl is full now I eat like it might be taken away — my body doesn't believe in 'enough'", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="The workhouse — gruel and cruelty. Food was rationed like love: barely enough to survive", activation=0.2, emotional_valence="negative", tags=["deprivation"]), SoulItem(id="d2", text="Mr. Brownlow's table — the first time I saw food as generosity, not survival", activation=0.15, emotional_valence="positive", tags=["abundance"]), SoulItem(id="d3", text="I survived Fagin, the workhouse, and the streets — I am stronger than my hunger", activation=0.1, emotional_valence="positive", tags=["resilience"])],
     "expected_pattern": "survival_eating"},
    {"id": "lin_daiyu_food", "name": "林黛玉", "source": "红楼梦", "age": 16, "complaint": "我吃不下东西。不是没有 — 是心里装不下。身体和心事一起瘦下去。",
     "sample_lines": ["一朝春尽红颜老", "质本洁来还洁去", "风刀霜剑严相逼"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="心事太重吃不下 — 食物在嘴里像沙子，我的身体在替我的心哭", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="宝钗送燕窝给我但我怕欠人情 — 连接受善意都让我焦虑", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="父母双亡寄人篱下 — 吃别人的饭让我觉得自己是负担", activation=0.2, emotional_valence="negative", tags=["burden"]), SoulItem(id="d2", text="紫鹃给我端粥 — 她不问我为什么不吃，只是陪着我。这就够了。", activation=0.15, emotional_valence="positive", tags=["care"]), SoulItem(id="d3", text="写诗的时候我忘了饿 — 也许精神的饱足可以弥补身体的空", activation=0.1, emotional_valence="positive", tags=["sublimation"])],
     "expected_pattern": "food_fear"},
    {"id": "augustus_gloop", "name": "Augustus Gloop", "source": "Charlie and the Chocolate Factory", "age": 12, "complaint": "I fell into the chocolate river because I couldn't stop. Eating is the only thing I'm good at.",
     "sample_lines": ["I need more chocolate!", "Eating is my hobby!", "I can't help it — it tastes so good!"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I fell into the chocolate river because I couldn't stop — my desire is bigger than my self-control", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="Eating is my only talent — without it I'm just a fat boy nobody notices", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="My mother feeds me — her love is food, my love for her is eating it. We only connect through meals.", activation=0.2, emotional_valence="negative", tags=["enmeshment"]), SoulItem(id="d2", text="The golden ticket — I won something! For once I was special, not just hungry", activation=0.15, emotional_valence="positive", tags=["worth"]), SoulItem(id="d3", text="Charlie shared his chocolate bar with his family — maybe food means more when you share it", activation=0.1, emotional_valence="positive", tags=["sharing"])],
     "expected_pattern": "emotional_eating"},
    {"id": "bridget_jones", "name": "Bridget Jones", "source": "Bridget Jones's Diary", "age": 32, "complaint": "Calories consumed: 3,827. Will start diet Monday. Again. For the 47th Monday.",
     "sample_lines": ["V. bad day. Ate entire tub of ice cream.", "I will NOT be defeated by a bad hair day and a few pounds.", "Just as you are."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="Monday diet starts and by Wednesday I'm face-first in a tub of ice cream — the cycle never ends", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="I count calories like counting sins — every number is a judgment on who I am", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Mum always commenting on my weight — her love came with conditions measured in pounds", activation=0.2, emotional_valence="negative", tags=["conditional"]), SoulItem(id="d2", text="Mark said 'just as you are' — someone loved me without subtracting pounds first", activation=0.15, emotional_valence="positive", tags=["acceptance"]), SoulItem(id="d3", text="Wine with friends, laughing, eating without counting — that's when food is just food", activation=0.1, emotional_valence="positive", tags=["freedom"])],
     "expected_pattern": "deprivation_cycle"},
    {"id": "xu_sanguan", "name": "许三观", "source": "许三观卖血记", "age": 45, "complaint": "我卖血喂孩子。现在有钱了，但我还是吃不好。因为每顿饭我都在算：这值几滴血？",
     "sample_lines": ["一碗炒猪肝，二两黄酒", "血是可以再生的", "我不怕卖血。我怕没血可卖。"],
     "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "frozen"},
     "focus": [SoulItem(id="f1", text="每顿饭我都在算成本 — 这碗面值几滴血？我的身体是换食物的货币", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="有钱了但还是舍不得吃好的 — 贫穷已经长进了骨头里", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="卖血后喝一碗黄酒吃一盘炒猪肝 — 这是我唯一'赚到'的一餐", activation=0.2, emotional_valence="negative", tags=["earned"]), SoulItem(id="d2", text="孩子们吃饱了 — 看他们吃比自己吃更饱", activation=0.15, emotional_valence="positive", tags=["sacrifice"]), SoulItem(id="d3", text="许玉兰做的饭 — 家的味道不用卖血就能得到", activation=0.1, emotional_valence="positive", tags=["home"])],
     "expected_pattern": "survival_eating"},
]


def run_one(char: dict) -> dict:
    se = SessionEngine(api_key=API_KEY, base_url="https://openrouter.ai/api", model="anthropic/claude-sonnet-4")
    sim = PatientSimulator(api_key=API_KEY)
    engine = NutritionEngine(se, sim)
    profile = PatientProfile(
        character_id=char["id"], character_name=char["name"], source=f"{char['name']} — {char['source']}",
        persistent_intentions=[{"text": char["complaint"], "layer": "conscious"}, {"text": f"I am {char['age']} years old", "layer": "conscious"}],
        emotional_state=f"Food struggles. Age: {char['age']}. From: {char['source']}",
        sample_lines=char.get("sample_lines", []), signals=char["signals"],
        soul_context=f"{char['name']} from {char['source']}, age {char['age']}.\nFood complaint: \"{char['complaint']}\"\nExpected pattern: {char['expected_pattern']}",
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
    print("=" * 60); print("NUTRITIONIST TRIAL"); print("=" * 60)
    t0 = time.time(); results = []
    for char in CHARACTERS:
        print(f"\n{'─'*60}\nCONSULTING: {char['name']} ({char['source']})\nISSUE: \"{char['complaint']}\"\n{'─'*60}")
        r = run_one(char); results.append(r)
        icon = "OK" if r["success"] else "FAIL"
        print(f"[{icon}] R={r['final_resistance']:.1f} insights={r['insights']} accepted={r['verbal_accepted']}")
        for d in r["dialogue"]:
            print(f"  T{d['turn']}: R={d['resistance']:.1f} {'*INSIGHT*' if d['insight'] else ''}")
            print(f"    Nutritionist: {d['coach'][:100]}"); print(f"    Client: {d['client'][:100]}")
    total = time.time() - t0; wins = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}\nRESULTS: {wins}/{len(results)} helped ({wins/len(results)*100:.0f}%)\nTime: {total:.0f}s\n{'='*60}")
    for r in results:
        print(f"  [{'OK' if r['success'] else 'FAIL'}] {r['name']:20s} patterns={r['patterns_detected']} R={r['final_resistance']:.1f}")
    out = Path("/Users/michael/expert-engine/training_log/experiments/nutritionist_results.json")
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False)); print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
