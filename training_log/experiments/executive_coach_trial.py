#!/usr/bin/env python3
"""Executive Coach Trial — Can the Executive Coach help 10 literary leaders see their leadership patterns?"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

sys.path.insert(0, "/Users/michael/expert-engine")
from dotenv import load_dotenv
load_dotenv("/Users/michael/expert-engine/.env")

from expert_engine.patient_simulator import PatientSimulator, PatientProfile
from expert_engine.session_engine import SessionEngine
from expert_engine.executive_coach.executive_advisor import LeadershipPatternDetector, ExecutiveEngine
from expert_engine.goal_generator import SoulItem

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CHARACTERS = [
    {
        "id": "michael_corleone", "name": "Michael Corleone", "source": "The Godfather", "age": 45,
        "complaint": "Every decision I make alone. I trust no one. And I'm losing everyone.",
        "sample_lines": ["It's not personal, it's strictly business.", "Keep your friends close, but your enemies closer.", "Just when I thought I was out, they pull me back in."],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "frozen"},
        "focus": [SoulItem(id="f1", text="I trust no one and every decision is mine alone — the weight is crushing", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="I lost Kay, I lost Fredo, I lost myself — all for the family business", activation=0.9, emotional_valence="extreme")],
        "deep": [SoulItem(id="d1", text="I was the one who wasn't supposed to be in the family business — I was going to be different", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="When I held my newborn I saw what I was fighting for — a future free of this", activation=0.15, emotional_valence="positive", tags=["hope"]), SoulItem(id="d3", text="My father could command loyalty through love. I only know how through fear.", activation=0.1, emotional_valence="negative", tags=["blind_spot"])],
        "expected_pattern": "lonely_decider",
    },
    {
        "id": "lady_macbeth", "name": "Lady Macbeth", "source": "Macbeth", "age": 35,
        "complaint": "I pushed him to take the crown. Now the blood won't wash off.",
        "sample_lines": ["Unsex me here, and fill me from the crown to the toe top-full of direst cruelty.", "Out, damned spot!", "What's done cannot be undone."],
        "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="I wanted power so badly I made my husband a murderer — now power tastes like blood", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="I was stronger than him once. Now I can't sleep and he doesn't need me anymore.", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="In a world where women have no power, ambition was my only weapon", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="Before all this, Macbeth looked at me like I was the entire world", activation=0.15, emotional_valence="positive", tags=["loss"]), SoulItem(id="d3", text="I played the ruthless queen but I'm the one who can't handle what we did", activation=0.1, emotional_valence="negative", tags=["irony"])],
        "expected_pattern": "power_corrupted",
    },
    {
        "id": "zhuge_liang", "name": "诸葛亮", "source": "三国演义", "age": 53,
        "complaint": "鞠躬尽瘁死而后已 — 但后主扶不起来我还要撑多久",
        "sample_lines": ["出师未捷身先死", "鞠躬尽瘁，死而后已", "臣本布衣，躬耕于南阳"],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="先帝托孤于我 — 我不能让他失望但后主实在扶不起来", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="我事事亲为因为不放心别人 — 但我的身体已经撑不住了", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="先帝三顾茅庐 — 那份知遇之恩我这辈子还不完", activation=0.2, emotional_valence="positive", tags=["loyalty"]), SoulItem(id="d2", text="躬耕南阳的日子 — 那时候我是最自由最快乐的", activation=0.15, emotional_valence="positive", tags=["freedom"]), SoulItem(id="d3", text="我培养了姜维 — 至少有人能接过去", activation=0.1, emotional_valence="positive", tags=["legacy"])],
        "expected_pattern": "servant_leader",
    },
    {
        "id": "gandalf", "name": "Gandalf", "source": "Lord of the Rings", "age": 2000,
        "complaint": "I guide them but I cannot carry the burden for them. Sometimes I wonder if I've asked too much.",
        "sample_lines": ["All we have to decide is what to do with the time that is given us.", "I am a servant of the Secret Fire, wielder of the flame of Anor.", "Fly, you fools!"],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="I send hobbits to face darkness I cannot face for them — the guilt is immense", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="I chose Frodo because his heart is pure — but I may have chosen him to die", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="I was sent to guide, not to rule — but sometimes guidance means sending children to war", activation=0.2, emotional_valence="negative", tags=["burden"]), SoulItem(id="d2", text="When Frodo offered me the Ring I refused — I know what power would do to me", activation=0.15, emotional_valence="positive", tags=["wisdom"]), SoulItem(id="d3", text="The hobbits surprise me every time. Their courage comes from love, not strength.", activation=0.1, emotional_valence="positive", tags=["hope"])],
        "expected_pattern": "lonely_decider",
    },
    {
        "id": "captain_ahab", "name": "Captain Ahab", "source": "Moby-Dick", "age": 58,
        "complaint": "I will find that whale. I don't care what it costs.",
        "sample_lines": ["From hell's heart I stab at thee!", "I'd strike the sun if it insulted me.", "All my means are sane, my motive and my object mad."],
        "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "escalating", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="The white whale took my leg and my sanity — I will have my revenge or die", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="My crew follows me out of fear and awe — not one of them would choose this mission", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="Before the whale I was a respected captain with a wife and child waiting at home", activation=0.2, emotional_valence="positive", tags=["before"]), SoulItem(id="d2", text="Starbuck sees what I've become and I hate him for it because he's right", activation=0.15, emotional_valence="negative", tags=["mirror"]), SoulItem(id="d3", text="The sea was my first love — the whale just gave my love a target for hate", activation=0.1, emotional_valence="negative", tags=["corruption"])],
        "expected_pattern": "obsessive_visionary",
    },
    {
        "id": "miranda_priestly", "name": "Miranda Priestly", "source": "The Devil Wears Prada", "age": 50,
        "complaint": "I built an empire. Two marriages failed. My daughters barely know me. That's the cost.",
        "sample_lines": ["That's all.", "By all means, move at a glacial pace.", "Everybody wants to be us."],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="My standards built this empire but destroyed every personal relationship I have", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="My daughters' recital is tonight and I will probably miss it — again", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="I started as an assistant who was told she'd never make it — every day I prove them wrong", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="When I see real talent I want to mentor it — that's the closest I come to generosity", activation=0.15, emotional_valence="positive", tags=["hidden"]), SoulItem(id="d3", text="My daughters look at me with disappointment — the same look I give everyone who fails to meet my standard", activation=0.1, emotional_valence="negative", tags=["mirror"])],
        "expected_pattern": "perfectionist_driver",
    },
    {
        "id": "cao_cao_exec", "name": "曹操", "source": "三国演义", "age": 55,
        "complaint": "我用人不疑但最后还是只信自己",
        "sample_lines": ["唯才是举", "宁教我负天下人", "对酒当歌，人生几何"],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="我唯才是举但关键时刻还是只信自己的判断 — 因为别人让我失望过", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="赤壁之败 — 我自负地不听谏言，损失了一切", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="宦官之后 — 我从最底层靠才华和手段走到今天", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="对酒当歌 — 写诗的时候我是真实的，不需要算计", activation=0.15, emotional_valence="positive", tags=["authentic"]), SoulItem(id="d3", text="郭嘉死后我再没有一个能完全说真话的谋士", activation=0.1, emotional_valence="negative", tags=["loss"])],
        "expected_pattern": "lonely_decider",
    },
    {
        "id": "tyrion", "name": "Tyrion Lannister", "source": "Game of Thrones", "age": 35,
        "complaint": "I'm the smartest person in every room but no one sees past the dwarf",
        "sample_lines": ["I drink and I know things.", "Never forget what you are. The rest of the world will not.", "A mind needs books as a sword needs a whetstone."],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="I've saved cities and nobody respects me because of how I look", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="I use wit as armor — if I make them laugh they won't see me cry", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="My father wished I was never born. I've been proving him wrong my whole life.", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="When I was Hand of the King and saved King's Landing — that was the best version of me", activation=0.15, emotional_valence="positive", tags=["peak"]), SoulItem(id="d3", text="Jaime loved me despite everything — proof that I am lovable if people bother to look", activation=0.1, emotional_valence="positive", tags=["connection"])],
        "expected_pattern": "servant_leader",
    },
    {
        "id": "elizabeth_i", "name": "Elizabeth I", "source": "History/Drama", "age": 55,
        "complaint": "I married my country. I have no heir. Was it worth it?",
        "sample_lines": ["I know I have the body of a weak and feeble woman, but I have the heart and stomach of a king.", "I will have but one mistress here, and no master.", "I do not so much rejoice that God hath made me to be a Queen, as to be a Queen over so thankful a people."],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="I chose England over love, over children, over everything — and now I'm alone with a crown", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="Every advisor wants me to marry. I refuse — marriage means losing my power.", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="My mother was beheaded by my father — I learned that love and power cannot coexist", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="I brought England its golden age — that IS my legacy, better than any heir", activation=0.15, emotional_valence="positive", tags=["legacy"]), SoulItem(id="d3", text="Robert Dudley — the only man I might have loved, if love hadn't meant giving up everything", activation=0.1, emotional_valence="positive", tags=["sacrifice"])],
        "expected_pattern": "lonely_decider",
    },
    {
        "id": "liu_bei", "name": "刘备", "source": "三国演义", "age": 50,
        "complaint": "我以仁义待人但仁义让我错过了多少战机",
        "sample_lines": ["兄弟如手足", "勿以恶小而为之，勿以善小而不为", "我有孔明，如鱼得水"],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="我以仁义自居但仁义让我在关键时刻犹豫 — 不取荆州、不杀刘璋", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="关羽死后我明知不该伐吴但义气让我不顾一切", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="织席贩履出身 — 我没有曹操的家世只有仁义这一张牌", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="桃园结义 — 那是我一生最真实最纯粹的时刻", activation=0.15, emotional_valence="positive", tags=["bond"]), SoulItem(id="d3", text="孔明帮我看到了天下大势 — 有他我才从流浪变成了建国", activation=0.1, emotional_valence="positive", tags=["growth"])],
        "expected_pattern": "servant_leader",
    },
]


def run_one(char: dict) -> dict:
    se = SessionEngine(api_key=API_KEY, base_url="https://openrouter.ai/api", model="anthropic/claude-sonnet-4")
    sim = PatientSimulator(api_key=API_KEY)
    engine = ExecutiveEngine(se, sim)
    profile = PatientProfile(
        character_id=char["id"], character_name=char["name"],
        source=f"{char['name']} — {char['source']}",
        persistent_intentions=[{"text": char["complaint"], "layer": "conscious"}, {"text": f"I am {char['age']} years old", "layer": "conscious"}],
        emotional_state=f"Struggling with leadership. Age: {char['age']}. From: {char['source']}",
        sample_lines=char.get("sample_lines", []), signals=char["signals"],
        soul_context=f"{char['name']} from {char['source']}, age {char['age']}.\nLeadership complaint: \"{char['complaint']}\"\nExpected pattern: {char['expected_pattern']}",
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
    print("=" * 60); print("EXECUTIVE COACH TRIAL"); print("=" * 60)
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
        icon = "OK" if r["success"] else "FAIL"
        print(f"  [{icon}] {r['name']:20s} patterns={r['patterns_detected']} R={r['final_resistance']:.1f}")
    out = Path("/Users/michael/expert-engine/training_log/experiments/executive_coach_results.json")
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False)); print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
