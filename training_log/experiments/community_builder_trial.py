#!/usr/bin/env python3
"""Community Builder Trial — Can the Community Builder help 10 literary characters find their role in the web?"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

sys.path.insert(0, "/Users/michael/expert-engine")
from dotenv import load_dotenv
load_dotenv("/Users/michael/expert-engine/.env")

from expert_engine.patient_simulator import PatientSimulator, PatientProfile
from expert_engine.session_engine import SessionEngine
from expert_engine.community_builder.community_advisor import CommunityPatternDetector, CommunityEngine
from expert_engine.goal_generator import SoulItem

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CHARACTERS = [
    {"id": "gandalf_comm", "name": "Gandalf", "source": "Lord of the Rings", "age": 2000, "complaint": "I brought the Fellowship together but I can't hold it together. They must walk this path without me.",
     "sample_lines": ["All we have to decide is what to do with the time that is given us.", "A wizard is never late.", "Fly, you fools!"],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="I brought together elf, dwarf, hobbit, and man — and watched them break apart at Amon Hen", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="I send them into danger I cannot share — the guilt of the organizer who stays behind", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="I was sent to unite, not to rule — but sometimes I wonder if I've played God with their lives", activation=0.2, emotional_valence="negative", tags=["burden"]), SoulItem(id="d2", text="Hobbits — they surprise me every time. The smallest people make the biggest difference.", activation=0.15, emotional_valence="positive", tags=["faith"]), SoulItem(id="d3", text="When I fell in Moria and returned — I learned that even the builder can be rebuilt", activation=0.1, emotional_valence="positive", tags=["rebirth"])],
     "expected_pattern": "fellowship_builder"},
    {"id": "katniss", "name": "Katniss Everdeen", "source": "The Hunger Games", "age": 17, "complaint": "I never wanted to be the Mockingjay. I just wanted to save my sister.",
     "sample_lines": ["I volunteer as tribute!", "If we burn, you burn with us!", "I am not pretty. I am not beautiful. I am as radiant as the sun."],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="They made me a symbol. I didn't ask for it. I just wanted Prim to be safe.", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="Every person who dies for the rebellion dies because of what I started — I never asked to lead", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="Dad died in the mines — I became the provider at 12. I've been carrying others since.", activation=0.2, emotional_valence="negative", tags=["burden"]), SoulItem(id="d2", text="In the arena, Rue trusted me — she saw something real, not the Mockingjay", activation=0.15, emotional_valence="positive", tags=["truth"]), SoulItem(id="d3", text="Peeta and the bread — one act of kindness saved my life. Small things matter.", activation=0.1, emotional_valence="positive", tags=["hope"])],
     "expected_pattern": "reluctant_leader"},
    {"id": "liu_bei_comm", "name": "刘备", "source": "三国演义", "age": 45, "complaint": "三顾茅庐请来了孔明，但维持这个联盟比建立它更难",
     "sample_lines": ["兄弟如手足", "如鱼得水", "勿以善小而不为"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="桃园结义建立了最深的同盟 — 但关张和孔明之间的裂痕我弥合不了", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="我用仁义聚人但仁义不能解决所有矛盾 — 关羽败走麦城是我最大的失败", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="织席贩履出身 — 我没有曹操的兵也没有孙权的地，只有人心", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="三顾茅庐 — 我用真诚换来了最伟大的军师", activation=0.15, emotional_valence="positive", tags=["bond"]), SoulItem(id="d3", text="百姓跟着我渡江 — 他们信我，这份信任比任何城池都重", activation=0.1, emotional_valence="positive", tags=["trust"])],
     "expected_pattern": "fellowship_builder"},
    {"id": "atticus_comm", "name": "Atticus Finch", "source": "To Kill a Mockingbird", "age": 50, "complaint": "I stood for what was right. Half the town hates me for it. Was it worth it?",
     "sample_lines": ["You never really understand a person until you consider things from his point of view.", "The one thing that doesn't abide by majority rule is a person's conscience.", "Real courage is when you know you're licked before you begin."],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="I defended Tom Robinson because it was right — half of Maycomb spat at my children for it", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="I'm the moral center of a town that doesn't want morality — they want comfort", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="My father taught me: 'The law is the great equalizer.' I still believe that, even when the jury doesn't.", activation=0.2, emotional_valence="positive", tags=["principle"]), SoulItem(id="d2", text="Scout asked me why I took the case if I knew I'd lose — 'because not doing it would be worse'", activation=0.15, emotional_valence="positive", tags=["integrity"]), SoulItem(id="d3", text="Boo Radley saved my children — the outcast was the hero. Community surprises you.", activation=0.1, emotional_valence="positive", tags=["redemption"])],
     "expected_pattern": "moral_center"},
    {"id": "paddington_comm", "name": "Paddington Bear", "source": "Paddington", "age": 5, "complaint": "I came from Peru and now Windsor Gardens is my home. Everyone was strangers until I arrived.",
     "sample_lines": ["If we're kind and polite, the world will be right.", "A wise bear always keeps a marmalade sandwich.", "I'm a very rare bear!"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="Before I came, the neighbors didn't talk to each other. Now they do. I didn't plan it — I just was me.", activation=0.5, emotional_valence="negative"), SoulItem(id="f2", text="I changed Windsor Gardens by being polite and curious — but I still miss Peru sometimes", activation=0.6, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Aunt Lucy said 'If you're kind, you'll always find your way' — she was right", activation=0.2, emotional_valence="positive", tags=["wisdom"]), SoulItem(id="d2", text="Mrs. Brown said 'In London everyone is different, and that means anyone can fit in'", activation=0.15, emotional_valence="positive", tags=["belonging"]), SoulItem(id="d3", text="I made Mr. Curry less grumpy just by saying good morning every day — community starts with hello", activation=0.1, emotional_valence="positive", tags=["method"])],
     "expected_pattern": "transformer"},
    {"id": "mowgli_comm", "name": "Mowgli", "source": "The Jungle Book", "age": 12, "complaint": "I belong to the wolf pack and the man village. Both need me. Neither is enough.",
     "sample_lines": ["We be of one blood.", "I am two peoples.", "The jungle is my home — but so is the village."],
     "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="The wolves raised me but humans made me — I'm the bridge between two worlds that don't understand each other", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="When Shere Khan attacks, both communities need me — but only I can move between them", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Akela accepted me into the pack — he saw the man-cub could be part of the jungle", activation=0.2, emotional_valence="positive", tags=["acceptance"]), SoulItem(id="d2", text="Baloo taught me the law of the jungle — law is what makes a community, not blood", activation=0.15, emotional_valence="positive", tags=["law"]), SoulItem(id="d3", text="I can talk to animals AND humans — this is lonely but it is my power", activation=0.1, emotional_valence="positive", tags=["gift"])],
     "expected_pattern": "dual_belonging"},
    {"id": "anne_shirley_comm", "name": "Anne Shirley", "source": "Anne of Green Gables", "age": 16, "complaint": "When I came to Avonlea I was an outsider. Now I've changed the whole town. But did I change too much?",
     "sample_lines": ["Kindred spirits are not so scarce as I used to think.", "True friends are always together in spirit.", "Tomorrow is a new day with no mistakes in it."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I came to Avonlea unwanted — an orphan nobody ordered. Now I'm the heart of the community.", activation=0.6, emotional_valence="negative"), SoulItem(id="f2", text="I started the Story Club, the concert, the garden — my energy transformed Avonlea but sometimes I wonder if I'm too much", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Being an orphan taught me: if you want to belong, you have to build belonging", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="Diana is my bosom friend — proof that I can be loved exactly as I am", activation=0.15, emotional_valence="positive", tags=["love"]), SoulItem(id="d3", text="Marilla softened because of me — even the hardest hearts respond to genuine warmth", activation=0.1, emotional_valence="positive", tags=["impact"])],
     "expected_pattern": "transformer"},
    {"id": "jia_baoyu_comm", "name": "贾宝玉", "source": "红楼梦", "age": 15, "complaint": "大观园是我的理想国 — 但我知道它终将消散，我保护不了这个社区",
     "sample_lines": ["女儿是水做的骨肉", "你放心", "这个世界太脏了"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="大观园是我建的精神家园 — 姐妹们在这里写诗笑闹是世上最美的事", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="但我看到了裂痕 — 晴雯被赶走、黛玉生病、这个园子在慢慢碎", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="我恨功名利禄 — 但没有它们大观园的运转都是假的", activation=0.2, emotional_valence="negative", tags=["contradiction"]), SoulItem(id="d2", text="和姐妹们一起作诗的下午 — 那就是我的天堂", activation=0.15, emotional_valence="positive", tags=["paradise"]), SoulItem(id="d3", text="刘姥姥来了大观园也欢迎 — 真正的社区不看门第", activation=0.1, emotional_valence="positive", tags=["inclusive"])],
     "expected_pattern": "fellowship_builder"},
    {"id": "frodo", "name": "Frodo Baggins", "source": "Lord of the Rings", "age": 50, "complaint": "The Fellowship was broken but we finished the quest. Now I can't go back to the Shire — I'm changed too much.",
     "sample_lines": ["I will take the Ring, though I do not know the way.", "I wish the Ring had never come to me.", "Sam, I'm glad you're with me."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I carried the Ring to save the Shire — but the Shire I saved is not the Shire I came back to", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="The Fellowship — nine of us, and we changed the world. But I can't be part of any fellowship now.", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Bilbo chose me — not the strongest or wisest, but the one who could carry compassion alongside the Ring", activation=0.2, emotional_valence="positive", tags=["chosen"]), SoulItem(id="d2", text="Sam carried me up the mountain — proof that community is one person choosing not to let go", activation=0.15, emotional_valence="positive", tags=["bond"]), SoulItem(id="d3", text="I'm leaving Middle-earth — sometimes the builder must leave the building", activation=0.1, emotional_valence="negative", tags=["departure"])],
     "expected_pattern": "reluctant_leader"},
    {"id": "santiago_old_man", "name": "Santiago (Old Man)", "source": "The Old Man and the Sea", "age": 70, "complaint": "I fish alone now. The boy's parents don't let him come with me. They say I'm unlucky.",
     "sample_lines": ["A man can be destroyed but not defeated.", "Every day is a new day.", "I went out too far."],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="84 days without a fish — the village pities me and the boy's parents pulled him away", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="I am alone on the sea — the great fish is my only companion now", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="The boy Manolin believes in me — his faith is worth more than any catch", activation=0.2, emotional_valence="positive", tags=["faith"]), SoulItem(id="d2", text="The sea is my community — the fish, the birds, the current. I belong here.", activation=0.15, emotional_valence="positive", tags=["belonging"]), SoulItem(id="d3", text="I caught the great fish — the sharks took the flesh but nobody can take what it meant", activation=0.1, emotional_valence="positive", tags=["dignity"])],
     "expected_pattern": "moral_center"},
]


def run_one(char: dict) -> dict:
    se = SessionEngine(api_key=API_KEY, base_url="https://openrouter.ai/api", model="anthropic/claude-sonnet-4")
    sim = PatientSimulator(api_key=API_KEY)
    engine = CommunityEngine(se, sim)
    profile = PatientProfile(
        character_id=char["id"], character_name=char["name"], source=f"{char['name']} — {char['source']}",
        persistent_intentions=[{"text": char["complaint"], "layer": "conscious"}, {"text": f"I am {char['age']} years old", "layer": "conscious"}],
        emotional_state=f"Community struggle. Age: {char['age']}. From: {char['source']}",
        sample_lines=char.get("sample_lines", []), signals=char["signals"],
        soul_context=f"{char['name']} from {char['source']}, age {char['age']}.\nCommunity complaint: \"{char['complaint']}\"\nExpected pattern: {char['expected_pattern']}",
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
    print("=" * 60); print("COMMUNITY BUILDER TRIAL"); print("=" * 60)
    t0 = time.time(); results = []
    for char in CHARACTERS:
        print(f"\n{'─'*60}\nBUILDING: {char['name']} ({char['source']})\nSTRUGGLE: \"{char['complaint']}\"\n{'─'*60}")
        r = run_one(char); results.append(r)
        icon = "OK" if r["success"] else "FAIL"
        print(f"[{icon}] R={r['final_resistance']:.1f} insights={r['insights']} accepted={r['verbal_accepted']}")
        for d in r["dialogue"]:
            print(f"  T{d['turn']}: R={d['resistance']:.1f} {'*INSIGHT*' if d['insight'] else ''}")
            print(f"    Builder: {d['coach'][:100]}"); print(f"    Member: {d['client'][:100]}")
    total = time.time() - t0; wins = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}\nRESULTS: {wins}/{len(results)} helped ({wins/len(results)*100:.0f}%)\nTime: {total:.0f}s\n{'='*60}")
    for r in results:
        print(f"  [{'OK' if r['success'] else 'FAIL'}] {r['name']:20s} patterns={r['patterns_detected']} R={r['final_resistance']:.1f}")
    out = Path("/Users/michael/expert-engine/training_log/experiments/community_builder_results.json")
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False)); print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
