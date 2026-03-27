#!/usr/bin/env python3
"""Immigration Advisor Trial — Can the Immigration Advisor help 10 literary travelers find their ground?"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

sys.path.insert(0, "/Users/michael/expert-engine")
from dotenv import load_dotenv
load_dotenv("/Users/michael/expert-engine/.env")

from expert_engine.patient_simulator import PatientSimulator, PatientProfile
from expert_engine.session_engine import SessionEngine
from expert_engine.immigration_advisor.immigration_advisor import ImmigrationPatternDetector, ImmigrationEngine
from expert_engine.goal_generator import SoulItem

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CHARACTERS = [
    {"id": "santiago_imm", "name": "Santiago", "source": "The Alchemist", "age": 18, "complaint": "I left my sheep and my country to find a treasure. I don't know if I'll ever go home.",
     "sample_lines": ["When you want something, all the universe conspires.", "Tell your heart that the fear of suffering is worse than the suffering itself.", "Maktub."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I left Spain with nothing — every country I pass through I belong a little and leave a little behind", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="In the oasis I found Fatima — but my destiny calls me to the pyramids", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="My father wanted me to be a priest — I chose to be a shepherd to see the world", activation=0.2, emotional_valence="positive", tags=["freedom"]), SoulItem(id="d2", text="The old king said my Personal Legend awaits — I want to believe", activation=0.15, emotional_valence="positive", tags=["faith"]), SoulItem(id="d3", text="I was robbed in Tangier and rebuilt from zero — I can survive anywhere", activation=0.1, emotional_valence="positive", tags=["resilience"])],
     "expected_pattern": "between_worlds"},
    {"id": "mowgli", "name": "Mowgli", "source": "The Jungle Book", "age": 12, "complaint": "The wolves raised me but I'm not a wolf. The humans don't want me either.",
     "sample_lines": ["I am two peoples — I am of the jungle and of the man village.", "We be of one blood, thou and I.", "Let me go — I must go back to my own people!"],
     "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="The wolves say I'm a man-cub. The villagers say I'm a wild animal. I'm neither.", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="Shere Khan wants me dead because I belong to no world — I'm a threat to both", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Baloo and Bagheera love me — but they know I can't stay in the jungle forever", activation=0.2, emotional_valence="positive", tags=["love"]), SoulItem(id="d2", text="I can speak to animals AND humans — I'm the only one who can", activation=0.15, emotional_valence="positive", tags=["gift"]), SoulItem(id="d3", text="The red flower (fire) — humans' weapon that I can wield. It makes me powerful in both worlds.", activation=0.1, emotional_valence="positive", tags=["power"])],
     "expected_pattern": "between_worlds"},
    {"id": "heidi", "name": "Heidi", "source": "Heidi", "age": 8, "complaint": "They took me from the mountain to the city. I can't breathe here. I want my grandfather.",
     "sample_lines": ["The mountains are calling!", "I miss the goats and the stars.", "Clara, the wind here has no voice."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="Frankfurt is a prison — no mountains, no stars, no grandfather. I can't breathe.", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="Clara needs me and I love her — but I'm dying inside without my Alps", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Grandfather was the only family I had — everyone else abandoned me", activation=0.2, emotional_valence="negative", tags=["loss"]), SoulItem(id="d2", text="On the mountain I talked to the wind and the goats answered — nature is my language", activation=0.15, emotional_valence="positive", tags=["home"]), SoulItem(id="d3", text="Clara walked because of me — I can help people even away from home", activation=0.1, emotional_valence="positive", tags=["gift"])],
     "expected_pattern": "nostalgia_trap"},
    {"id": "sun_shaoping_imm", "name": "孙少平", "source": "平凡的世界", "age": 22, "complaint": "我从农村到城市打工，城里人不把我当人看",
     "sample_lines": ["人的痛苦只能在生活和劳动中消化", "我不甘心一辈子当农民", "书籍是我通向另一个世界的窗口"],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="在城里我是'乡巴佬' — 回村里我又是'不安分的人'", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="田晓霞和我之间的差距不是感情 — 是两个世界的距离", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="哥哥少安留在了村里 — 我选择了走出去但代价是孤独", activation=0.2, emotional_valence="negative", tags=["choice"]), SoulItem(id="d2", text="每读完一本书世界就大一点 — 书是我的翅膀", activation=0.15, emotional_valence="positive", tags=["growth"]), SoulItem(id="d3", text="煤矿虽苦但有兄弟 — 我在哪里都能找到自己的人", activation=0.1, emotional_valence="positive", tags=["resilience"])],
     "expected_pattern": "between_worlds"},
    {"id": "fievel", "name": "Fievel Mousekewitz", "source": "An American Tail", "age": 6, "complaint": "Papa said there are no cats in America. There are cats everywhere.",
     "sample_lines": ["Somewhere out there, Papa is thinking of me.", "America! Where there are no cats!", "Papa! Papa!"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "anxious"},
     "focus": [SoulItem(id="f1", text="We came to America to be safe — but I got separated from my family on the ship", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="I'm alone in a huge city and I don't speak the language and there are cats", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Papa's violin — when he plays I know everything will be okay", activation=0.2, emotional_valence="positive", tags=["home"]), SoulItem(id="d2", text="I made friends with Tiger the cat — not all cats are enemies, just like not all is bad here", activation=0.15, emotional_valence="positive", tags=["hope"]), SoulItem(id="d3", text="Papa said 'in America there are no cats' — the promise was a lie but the love was real", activation=0.1, emotional_valence="positive", tags=["truth"])],
     "expected_pattern": "displacement_grief"},
    {"id": "paddington", "name": "Paddington Bear", "source": "Paddington", "age": 5, "complaint": "I came from Peru with a label: Please look after this bear. Nobody reads labels anymore.",
     "sample_lines": ["A wise bear always keeps a marmalade sandwich in his hat.", "If we're kind and polite, the world will be right.", "I'm a very rare bear!"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="Aunt Lucy sent me to London because she believed in the kindness of strangers — I'm still believing", activation=0.6, emotional_valence="negative"), SoulItem(id="f2", text="The Browns took me in — but I still miss Peru and marmalade tastes different here", activation=0.5, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="In Peru I was loved simply for being me — here I have to explain myself constantly", activation=0.2, emotional_valence="negative", tags=["adjustment"]), SoulItem(id="d2", text="Mrs. Brown said 'in London everyone is different, and that means anyone can fit in'", activation=0.15, emotional_valence="positive", tags=["belonging"]), SoulItem(id="d3", text="I changed Windsor Gardens — they were strangers until I brought them together", activation=0.1, emotional_valence="positive", tags=["gift"])],
     "expected_pattern": "cultural_bridge"},
    {"id": "xu_sanguan_imm", "name": "许三观", "source": "许三观卖血记", "age": 40, "complaint": "文革时候全家被整，我带着家人到处流浪",
     "sample_lines": ["走到哪算哪", "家人在哪里家就在哪里", "只要还有血可以卖"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="被迫离开了家 — 从城里到乡下从乡下到更远的地方", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="我一辈子都在被时代推着走 — 从来没有选过自己的方向", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="每到一个地方我都能找到活法 — 卖血、做苦力、什么都行", activation=0.2, emotional_valence="positive", tags=["survival"]), SoulItem(id="d2", text="许玉兰和三个儿子 — 只要他们在我就不怕", activation=0.15, emotional_valence="positive", tags=["family"]), SoulItem(id="d3", text="一碗炒猪肝两碗黄酒 — 无论在哪里这个仪式就是我的家", activation=0.1, emotional_valence="positive", tags=["ritual"])],
     "expected_pattern": "displacement_grief"},
    {"id": "kim_kipling", "name": "Kim", "source": "Kim (Kipling)", "age": 13, "complaint": "I am Doyle's son and I am also a chela of the Lama. I am Irish and I am Indian. I am the Friend of all the World.",
     "sample_lines": ["Who is Kim? What is Kim?", "I am Kim. I am Kim.", "The great game is played by many peoples."],
     "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="I look Indian, speak Indian, think Indian — but my father was Irish and the British claim me as spy", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="Am I the Lama's disciple seeking enlightenment or Doyle's son serving the Empire?", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="The Grand Trunk Road is my home — not any one city but the road itself", activation=0.2, emotional_valence="positive", tags=["freedom"]), SoulItem(id="d2", text="The Lama loves me without needing me to be anything — just Kim", activation=0.15, emotional_valence="positive", tags=["love"]), SoulItem(id="d3", text="I can be anyone, speak any language, belong anywhere — this is my power", activation=0.1, emotional_valence="positive", tags=["gift"])],
     "expected_pattern": "between_worlds"},
    {"id": "joy_luck_mother", "name": "Suyuan Woo", "source": "The Joy Luck Club", "age": 55, "complaint": "I left my twin daughters in China during the war. In America my daughter doesn't understand why I push so hard.",
     "sample_lines": ["I wanted my children to have the best combination: American circumstances and Chinese character.", "In America, you can be anything you want to be.", "Best quality!"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "compete", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I left my twin babies on the road during the war — I thought I was dying. I survived. They didn't know me.", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="Jing-Mei doesn't understand — I push her because in China I lost everything by being weak", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="The Joy Luck Club — four women who found each other in San Francisco. We carry China together.", activation=0.2, emotional_valence="positive", tags=["community"]), SoulItem(id="d2", text="I cook Chinese food with American ingredients — that's my life: making it work with what's here", activation=0.15, emotional_valence="positive", tags=["adaptation"]), SoulItem(id="d3", text="My daughter will find her sisters someday — my story doesn't end with me", activation=0.1, emotional_valence="positive", tags=["legacy"])],
     "expected_pattern": "cultural_bridge"},
    {"id": "marjane", "name": "Marjane Satrapi", "source": "Persepolis (fictionalized)", "age": 18, "complaint": "I left Iran for Vienna. I'm too Iranian for Europe and too European for Iran.",
     "sample_lines": ["I was a Westerner in Iran, an Iranian in the West.", "My identity was torn apart.", "I am the revolution's child."],
     "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="In Vienna they see my headscarf. In Tehran they see my punk rock. Nowhere do they see ME.", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="I left because of the war — I didn't choose exile, exile chose me", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="Grandma said: 'Always keep your dignity and be true to yourself.' She survived worse.", activation=0.2, emotional_valence="positive", tags=["wisdom"]), SoulItem(id="d2", text="I draw comics — turning my pain into art is the only way I've found to be whole", activation=0.15, emotional_valence="positive", tags=["art"]), SoulItem(id="d3", text="I am my grandmother's courage and my uncle's rebellion — I carry them.", activation=0.1, emotional_valence="positive", tags=["heritage"])],
     "expected_pattern": "between_worlds"},
]


def run_one(char: dict) -> dict:
    se = SessionEngine(api_key=API_KEY, base_url="https://openrouter.ai/api", model="anthropic/claude-sonnet-4")
    sim = PatientSimulator(api_key=API_KEY)
    engine = ImmigrationEngine(se, sim)
    profile = PatientProfile(
        character_id=char["id"], character_name=char["name"], source=f"{char['name']} — {char['source']}",
        persistent_intentions=[{"text": char["complaint"], "layer": "conscious"}, {"text": f"I am {char['age']} years old", "layer": "conscious"}],
        emotional_state=f"Immigration/displacement struggle. Age: {char['age']}. From: {char['source']}",
        sample_lines=char.get("sample_lines", []), signals=char["signals"],
        soul_context=f"{char['name']} from {char['source']}, age {char['age']}.\nImmigration complaint: \"{char['complaint']}\"\nExpected pattern: {char['expected_pattern']}",
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
    print("=" * 60); print("IMMIGRATION ADVISOR TRIAL"); print("=" * 60)
    t0 = time.time(); results = []
    for char in CHARACTERS:
        print(f"\n{'─'*60}\nADVISING: {char['name']} ({char['source']})\nSTRUGGLE: \"{char['complaint']}\"\n{'─'*60}")
        r = run_one(char); results.append(r)
        icon = "OK" if r["success"] else "FAIL"
        print(f"[{icon}] R={r['final_resistance']:.1f} insights={r['insights']} accepted={r['verbal_accepted']}")
        for d in r["dialogue"]:
            print(f"  T{d['turn']}: R={d['resistance']:.1f} {'*INSIGHT*' if d['insight'] else ''}")
            print(f"    Advisor: {d['coach'][:100]}"); print(f"    Client: {d['client'][:100]}")
    total = time.time() - t0; wins = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}\nRESULTS: {wins}/{len(results)} helped ({wins/len(results)*100:.0f}%)\nTime: {total:.0f}s\n{'='*60}")
    for r in results:
        print(f"  [{'OK' if r['success'] else 'FAIL'}] {r['name']:20s} patterns={r['patterns_detected']} R={r['final_resistance']:.1f}")
    out = Path("/Users/michael/expert-engine/training_log/experiments/immigration_advisor_results.json")
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False)); print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
