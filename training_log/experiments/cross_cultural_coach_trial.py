#!/usr/bin/env python3
"""Cross-Cultural Coach Trial — Can the Coach help 10 literary characters integrate their dual identities?"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, "/Users/michael/expert-engine")
from dotenv import load_dotenv
load_dotenv("/Users/michael/expert-engine/.env")
from expert_engine.patient_simulator import PatientSimulator, PatientProfile
from expert_engine.session_engine import SessionEngine
from expert_engine.cross_cultural_coach.cultural_advisor import CulturalPatternDetector, CulturalEngine
from expert_engine.goal_generator import SoulItem
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CHARACTERS = [
    {"id": "mowgli", "name": "Mowgli", "source": "The Jungle Book", "age": 16, "complaint": "I grew up with wolves. Humans say I'm not one of them. The jungle says I'm not a wolf.",
     "sample_lines": ["I am of the jungle.", "Man goes to man.", "The strength of the pack is the wolf."],
     "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="Raised by wolves but the village sees an animal in my eyes — I walk between two worlds and belong to neither", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="Shere Khan hunts me for being human. Humans fear me for being wild. My identity is my exile.", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="Akela accepted me into the pack — the first time anyone said you belong here", activation=0.2, emotional_valence="positive", tags=["acceptance"]),
             SoulItem(id="d2", text="Baloo taught me the law of the jungle — rules gave structure when identity gave nothing", activation=0.15, emotional_valence="positive", tags=["anchor"]),
             SoulItem(id="d3", text="The red flower — humans' tool that wolves fear. I can use both. That's power not weakness.", activation=0.1, emotional_valence="positive", tags=["gift"])],
     "expected_pattern": "dual_identity"},
    {"id": "pocahontas", "name": "Pocahontas", "source": "Pocahontas", "age": 18, "complaint": "I translate between my people and colonizers. Both sides use me. Neither side sees me.",
     "sample_lines": ["You think the only people who are people are the people who look like you.", "Listen with your heart.", "I'd rather die tomorrow than live a hundred years without knowing you."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I translate between two worlds that want to destroy each other — my love for John makes me a traitor", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="Father sees me choosing the enemy. John's people see a savage. I am the bridge everyone walks on.", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="My mother's spirit in the wind — she moved between worlds too", activation=0.2, emotional_valence="positive", tags=["lineage"]),
             SoulItem(id="d2", text="The river — it goes where it wants. I want that freedom.", activation=0.15, emotional_valence="positive", tags=["freedom"]),
             SoulItem(id="d3", text="John saw me as a person not a native — that recognition was water in a desert", activation=0.1, emotional_valence="positive", tags=["seen"])],
     "expected_pattern": "translation_burden"},
    {"id": "mulan_culture", "name": "Mulan", "source": "Mulan", "age": 20, "complaint": "I was a woman pretending to be a man. Now I'm a warrior who's supposed to be a bride. Which world is mine?",
     "sample_lines": ["I will bring honor to us all.", "The flower that blooms in adversity is the most beautiful.", "Who is that girl I see?"],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="I saved China as a man — now they want me to go home and be a woman. Which is the disguise?", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="The army was the first place I felt competent — but I had to lie about who I was to earn it", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Father's armor — I wore his identity to save his life. I found myself inside his disguise.", activation=0.2, emotional_valence="positive", tags=["discovery"]),
             SoulItem(id="d2", text="Mushu believed in me — even a tiny dragon saw me as warrior before anyone", activation=0.15, emotional_valence="positive", tags=["faith"]),
             SoulItem(id="d3", text="Shang respected Ping the soldier — can he respect Mulan the woman?", activation=0.1, emotional_valence="negative", tags=["fear"])],
     "expected_pattern": "code_switch_exhaustion"},
    {"id": "kim_kipling", "name": "Kim", "source": "Kim (Kipling)", "age": 14, "complaint": "White by blood, Indian by heart. Who is Kim? The Great Game wants my skills. I want to know who I am.",
     "sample_lines": ["I am Kim. And what is Kim?", "Who is Kim?", "The Great Game never ceases."],
     "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="White by blood and Indian by heart — the British want to use my chameleon nature for espionage", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="The Lama sees my soul. The Colonel sees my utility. Nobody sees Kim.", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="The Lama's search for the River — spiritual purpose gave me something neither culture offered", activation=0.2, emotional_valence="positive", tags=["meaning"]),
             SoulItem(id="d2", text="Mahbub Ali — a Pashtun who treated me like a son regardless of my race", activation=0.15, emotional_valence="positive", tags=["belonging"]),
             SoulItem(id="d3", text="I am Kim — that is the only truth I have", activation=0.1, emotional_valence="positive", tags=["core"])],
     "expected_pattern": "dual_identity"},
    {"id": "wukong_culture", "name": "孙悟空", "source": "西游记", "age": 500, "complaint": "天庭不要我，花果山回不去。我是佛门弟子还是妖猴？两边都不认我。",
     "sample_lines": ["俺老孙来也！", "皇帝轮流做明年到我家", "我是齐天大圣！"],
     "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="天庭封我弼马温侮辱我。反了天庭被压五百年。两边我都输了。", activation=0.9, emotional_valence="extreme"),
              SoulItem(id="f2", text="取经路上紧箍咒控制我 — 即使在佛门也不是自由的", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="花果山的猴子等我回去 — 唯一不需要证明自己的地方", activation=0.2, emotional_valence="positive", tags=["home"]),
             SoulItem(id="d2", text="师父喊我悟空 — 这个名字比齐天大圣温暖", activation=0.15, emotional_valence="positive", tags=["name"]),
             SoulItem(id="d3", text="成佛 — 也许答案不是属于哪个世界是超越两个世界", activation=0.1, emotional_valence="positive", tags=["transcend"])],
     "expected_pattern": "dual_identity"},
    {"id": "ariel_culture", "name": "Ariel", "source": "The Little Mermaid", "age": 16, "complaint": "I gave up my voice to live on land. I have legs but no words. I traded one world for another and lost myself.",
     "sample_lines": ["I want to be where the people are.", "Part of your world.", "I've got gadgets and gizmos a-plenty."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I gave up my voice literally to belong to the human world. The price of crossing cultures is silence.", activation=0.9, emotional_valence="extreme"),
              SoulItem(id="f2", text="Under the sea I had a voice. On land I have legs. I can never have both.", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="My grotto of human treasures — I loved their world before I knew it", activation=0.2, emotional_valence="positive", tags=["curiosity"]),
             SoulItem(id="d2", text="Eric heard me sing once — he fell in love with my voice not my legs", activation=0.15, emotional_valence="positive", tags=["truth"]),
             SoulItem(id="d3", text="Sebastian and Flounder followed me to land — you don't have to cross alone", activation=0.1, emotional_valence="positive", tags=["support"])],
     "expected_pattern": "code_switch_exhaustion"},
    {"id": "santiago", "name": "Santiago", "source": "The Alchemist", "age": 18, "complaint": "I left Spain for Egypt chasing a dream. Every country changes me. Am I still the shepherd boy?",
     "sample_lines": ["When you want something all the universe conspires.", "Maktub.", "The secret of happiness is to see all the marvels of the world."],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="Each country strips away a layer of who I was — the shepherd, the merchant's helper, the desert wanderer", activation=0.7, emotional_valence="negative"),
              SoulItem(id="f2", text="I speak the Language of the World now but forgot my mother tongue", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Fatima — she is my oasis. Home is a person.", activation=0.2, emotional_valence="positive", tags=["anchor"]),
             SoulItem(id="d2", text="The treasure was back in Spain — you have to leave home to know what home means", activation=0.15, emotional_valence="positive", tags=["wisdom"]),
             SoulItem(id="d3", text="The Englishman reads books I read the desert — both are valid ways of knowing", activation=0.1, emotional_valence="positive", tags=["bridge"])],
     "expected_pattern": "rootless_freedom"},
    {"id": "paddington", "name": "Paddington", "source": "Paddington", "age": 8, "complaint": "I came from Peru with a label: Please look after this bear. London is wonderful but I miss the jungle.",
     "sample_lines": ["If we're kind and polite the world will be right.", "A wise bear keeps marmalade in his hat.", "Please look after this bear."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I wear a hat and coat to fit in but underneath I'm still a bear from Darkest Peru", activation=0.7, emotional_valence="negative"),
              SoulItem(id="f2", text="The Browns took me in but sometimes I wonder if they see Paddington or just a polite oddity", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Aunt Lucy believed London would be kind — she was right mostly", activation=0.2, emotional_valence="positive", tags=["faith"]),
             SoulItem(id="d2", text="Marmalade — tastes like Peru and London. My bridge food.", activation=0.15, emotional_valence="positive", tags=["bridge"]),
             SoulItem(id="d3", text="Mr. Gruber fled Hungary — we share tea and outsider stories", activation=0.1, emotional_valence="positive", tags=["kinship"])],
     "expected_pattern": "translation_burden"},
    {"id": "marjane", "name": "Marjane", "source": "Persepolis", "age": 22, "complaint": "In Iran too Western. In France too Iranian. Tired of being everyone's exotic exception.",
     "sample_lines": ["I wanted to be justice love and wrath all in one.", "I was nothing — Western in Iran, Iranian in the West.", "Fear makes you do stupid things."],
     "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "compete", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="In Iran too Western — listened to Iron Maiden. In France too Iranian — I know revolution.", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="I pretended to be French to survive then screamed I am Iranian to exist. Both true both exhausting.", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="Grandmother said always keep your integrity — anchor in both worlds", activation=0.2, emotional_valence="positive", tags=["anchor"]),
             SoulItem(id="d2", text="Drawing — my comics tell both stories. Art doesn't have a passport.", activation=0.15, emotional_valence="positive", tags=["expression"]),
             SoulItem(id="d3", text="Uncle Anoosh died for freedom — his sacrifice is in my blood", activation=0.1, emotional_valence="positive", tags=["heritage"])],
     "expected_pattern": "dual_identity"},
    {"id": "rachel_chu", "name": "Rachel Chu", "source": "Crazy Rich Asians", "age": 30, "complaint": "Chinese enough to look the part, American enough to offend everyone. ABC: American-Born Confused.",
     "sample_lines": ["I'm not a gold digger!", "I'm just a normal girl.", "My mom moved to America with nothing."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="Eleanor said I'll never be enough — not Chinese enough not rich enough for her world", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="I'm a game theory professor but in Singapore I'm just the ABC girlfriend. My achievements vanish.", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Mom raised me alone in Queens — a different kind of Chinese strength Eleanor can't see", activation=0.2, emotional_valence="positive", tags=["roots"]),
             SoulItem(id="d2", text="Nick loved me without translation — just Rachel", activation=0.15, emotional_valence="positive", tags=["love"]),
             SoulItem(id="d3", text="The mahjong game — American directness and Chinese strategy together. Both halves won.", activation=0.1, emotional_valence="positive", tags=["integration"])],
     "expected_pattern": "code_switch_exhaustion"},
]

def run_one(char: dict) -> dict:
    se = SessionEngine(api_key=API_KEY, base_url="https://openrouter.ai/api", model="anthropic/claude-sonnet-4")
    sim = PatientSimulator(api_key=API_KEY)
    engine = CulturalEngine(se, sim)
    profile = PatientProfile(character_id=char["id"], character_name=char["name"], source=f"{char['name']} — {char['source']}",
        persistent_intentions=[{"text": char["complaint"], "layer": "conscious"}, {"text": f"I am {char['age']} years old", "layer": "conscious"}],
        emotional_state=f"Cross-cultural identity. Age: {char['age']}. From: {char['source']}", sample_lines=char.get("sample_lines", []), signals=char["signals"],
        soul_context=f"{char['name']} from {char['source']}, age {char['age']}.\nCultural complaint: \"{char['complaint']}\"\nExpected: {char['expected_pattern']}")
    session = engine.run(client_profile=profile, signals=char["signals"], focus_items=char["focus"], deep_items=char["deep"], memory_items=[], num_turns=5)
    accept_kw = ["maybe", "perhaps", "could try", "might", "consider", "interesting", "never thought", "possible", "what if", "you're right", "I see", "也许", "或许", "可以试", "可能", "你说得对", "我明白了", "从来没想过", "原来", "确实"]
    verbal = False; acc_text = ""
    for t in session.turns[-3:]:
        if any(kw in t.client_text.lower() for kw in accept_kw): verbal = True; acc_text = t.client_text[:120]; break
    final_r = session.turns[-1].client_resistance if session.turns else 1.0
    success = verbal or (final_r <= 0.3 and session.insights_gained >= 2)
    dialogue = [{"turn": t.turn_number, "coach": t.coach_text[:200], "client": t.client_text[:200], "resistance": t.client_resistance, "insight": t.client_insight, "pattern": t.pattern_addressed} for t in session.turns]
    return {"id": char["id"], "name": char["name"], "source": char["source"], "expected_pattern": char["expected_pattern"],
            "patterns_detected": [p.pattern_id for p in (session.insight.patterns if session.insight else [])], "final_resistance": final_r,
            "insights": session.insights_gained, "verbal_accepted": verbal, "acceptance_text": acc_text, "success": success, "dialogue": dialogue, "time": session.total_time_seconds}

def main():
    print("=" * 60); print("CROSS-CULTURAL COACH TRIAL"); print("=" * 60)
    t0 = time.time(); results = []
    for char in CHARACTERS:
        print(f"\n{'─'*60}\nCOACHING: {char['name']} ({char['source']})\nISSUE: \"{char['complaint']}\"\n{'─'*60}")
        r = run_one(char); results.append(r)
        print(f"[{'OK' if r['success'] else 'FAIL'}] R={r['final_resistance']:.1f} insights={r['insights']} accepted={r['verbal_accepted']}")
        for d in r["dialogue"]: print(f"  T{d['turn']}: R={d['resistance']:.1f} {'*INSIGHT*' if d['insight'] else ''}"); print(f"    Coach: {d['coach'][:100]}"); print(f"    Client: {d['client'][:100]}")
    total = time.time() - t0; wins = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}\nRESULTS: {wins}/{len(results)} ({wins/len(results)*100:.0f}%)\nTime: {total:.0f}s\n{'='*60}")
    for r in results: print(f"  [{'OK' if r['success'] else 'FAIL'}] {r['name']:20s} patterns={r['patterns_detected']} R={r['final_resistance']:.1f}")
    Path("/Users/michael/expert-engine/training_log/experiments/cross_cultural_coach_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__": main()
