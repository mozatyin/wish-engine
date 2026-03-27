#!/usr/bin/env python3
"""Startup Mentor Trial — Can the Startup Mentor help 10 literary entrepreneurs see their patterns?"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

sys.path.insert(0, "/Users/michael/expert-engine")
from dotenv import load_dotenv
load_dotenv("/Users/michael/expert-engine/.env")

from expert_engine.patient_simulator import PatientSimulator, PatientProfile
from expert_engine.session_engine import SessionEngine
from expert_engine.startup_mentor.startup_advisor import StartupPatternDetector, StartupEngine
from expert_engine.goal_generator import SoulItem

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CHARACTERS = [
    {
        "id": "gatsby_startup", "name": "Jay Gatsby", "source": "The Great Gatsby", "age": 32,
        "complaint": "I built an empire from nothing — all for one person who doesn't care",
        "sample_lines": ["Can't repeat the past? Why of course you can!", "Old sport.", "Her voice is full of money."],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="Everything I built — the mansion, the parties, the fortune — was to prove I'm worthy of Daisy", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="I came from nothing in North Dakota — I built myself from scratch, name and all", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="Dan Cody showed me wealth was possible — I've been chasing that vision since I was 17", activation=0.2, emotional_valence="positive", tags=["origin"]), SoulItem(id="d2", text="My schedule — rise 6:00, study electricity 7:15 — I have always been a builder of systems", activation=0.15, emotional_valence="positive", tags=["discipline"]), SoulItem(id="d3", text="The green light — I never asked what Daisy wanted. I was building for a fantasy.", activation=0.1, emotional_valence="negative", tags=["blind_spot"])],
        "expected_pattern": "identity_builder",
    },
    {
        "id": "scarlett_startup", "name": "Scarlett O'Hara", "source": "Gone with the Wind", "age": 28,
        "complaint": "I saved Tara by building a lumber business. Now I have money but no one respects me.",
        "sample_lines": ["After all, tomorrow is another day!", "I'll think about it tomorrow.", "As God is my witness, I'll never be hungry again!"],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "compete", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="I swore I'd never be hungry again — I built a business from nothing in a ruined world", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="I did whatever it took — married for money, exploited convict labor — and I'd do it again to survive", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="Tara is my land, my identity — without it I'm nothing", activation=0.2, emotional_valence="negative", tags=["identity"]), SoulItem(id="d2", text="Rhett saw through me and loved the real me — I was too busy surviving to notice", activation=0.15, emotional_valence="positive", tags=["love"]), SoulItem(id="d3", text="I dream of Tara — in the red earth I find my strength", activation=0.1, emotional_valence="positive", tags=["roots"])],
        "expected_pattern": "survival_hustler",
    },
    {
        "id": "xu_sanguan", "name": "许三观", "source": "许三观卖血记", "age": 40,
        "complaint": "我卖了一辈子血养家。现在老了血不值钱了。",
        "sample_lines": ["卖血就卖血，人总要活下去", "血是我唯一值钱的东西", "一碗炒猪肝两碗黄酒"],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="每次家里出事我就去卖血 — 血是我唯一的资本", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="一乐不是我亲生的但我卖血救了他 — 我选择了他", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="我是普通人做了普通人能做的一切 — 这有什么不对", activation=0.2, emotional_valence="positive", tags=["dignity"]), SoulItem(id="d2", text="卖血后吃一碗炒猪肝喝两碗黄酒 — 那是我犒劳自己的仪式", activation=0.15, emotional_valence="positive", tags=["ritual"]), SoulItem(id="d3", text="我不聪明但我从不放弃 — 每一次都能再来一次", activation=0.1, emotional_valence="positive", tags=["resilience"])],
        "expected_pattern": "survival_hustler",
    },
    {
        "id": "walter_white", "name": "Walter White", "source": "Breaking Bad", "age": 50,
        "complaint": "I was a genius chemist stuck teaching high school. Now I build an empire.",
        "sample_lines": ["I am the one who knocks!", "Say my name.", "I did it for me. I liked it. I was good at it."],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="I was underestimated my entire life — now I've built something no one can ignore", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="I said it was for the family but it was for me — I liked the power", activation=0.9, emotional_valence="extreme")],
        "deep": [SoulItem(id="d1", text="I left Gray Matter for pennies — the worst business decision of my life haunts me every day", activation=0.2, emotional_valence="negative", tags=["regret"]), SoulItem(id="d2", text="My chemistry is art — 99.1% purity is perfection that nobody else can achieve", activation=0.15, emotional_valence="positive", tags=["craft"]), SoulItem(id="d3", text="Jesse looked up to me — I was the father he never had and I destroyed him", activation=0.1, emotional_valence="negative", tags=["guilt"])],
        "expected_pattern": "identity_builder",
    },
    {
        "id": "don_draper_startup", "name": "Don Draper", "source": "Mad Men", "age": 35,
        "complaint": "I built my identity and my career from scratch. I am my own greatest product.",
        "sample_lines": ["What is happiness?", "If you don't like what they're saying, change the conversation.", "People tell you who they are, but we ignore it."],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="Dick Whitman built Don Draper from nothing — the greatest pitch I ever made was myself", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="I sell desire for a living but I don't know what I want", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="I grew up in a whorehouse — I know what people want because I learned to read them to survive", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="The Carousel pitch — I turned fake memories into real emotion. That's my genius.", activation=0.15, emotional_valence="positive", tags=["talent"]), SoulItem(id="d3", text="Anna Draper knew both names and loved me — proof the real me is lovable", activation=0.1, emotional_valence="positive", tags=["truth"])],
        "expected_pattern": "identity_builder",
    },
    {
        "id": "robinson_crusoe", "name": "Robinson Crusoe", "source": "Robinson Crusoe", "age": 35,
        "complaint": "I built civilization from nothing on a deserted island. Now I must decide what to keep.",
        "sample_lines": ["I was born to be my own destroyer.", "I learned to look upon the bright side of my condition.", "Thus fear of danger is ten thousand times more terrifying than danger itself."],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="I built everything from scratch — shelter, farm, pottery — because I had no choice", activation=0.6, emotional_valence="negative"), SoulItem(id="f2", text="I survived 28 years alone — but was I building or just keeping busy to avoid going mad?", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="Father warned me not to go to sea — I went anyway. I've always needed to prove I can do it alone.", activation=0.2, emotional_valence="negative", tags=["defiance"]), SoulItem(id="d2", text="When Friday arrived I discovered I missed human connection more than I admitted", activation=0.15, emotional_valence="positive", tags=["connection"]), SoulItem(id="d3", text="My journal kept me sane — writing is how I make order from chaos", activation=0.1, emotional_valence="positive", tags=["tool"])],
        "expected_pattern": "eccentric_visionary",
    },
    {
        "id": "wang_xifeng_startup", "name": "王熙凤", "source": "红楼梦", "age": 25,
        "complaint": "大观园就是我的公司 — 我比任何人都会运营但他们说我心狠",
        "sample_lines": ["不严怎么撑得住这个家", "我从小就比男人强", "这府里离了我看谁转得动"],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="大观园几百口人全靠我 — 效率和纪律是唯一能撑住的方法", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="他们说我心狠手辣 — 但不狠这个家早就散了", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="从小在王家我就是最能干的 — 嫁过来我照样最能干", activation=0.2, emotional_valence="positive", tags=["competence"]), SoulItem(id="d2", text="平儿帮我挡了无数刀 — 没有她我撑不到今天", activation=0.15, emotional_valence="positive", tags=["ally"]), SoulItem(id="d3", text="大姐儿笑的时候我会想：我这么拼到底是为了谁", activation=0.1, emotional_valence="positive", tags=["doubt"])],
        "expected_pattern": "resourceful_manager",
    },
    {
        "id": "willy_wonka", "name": "Willy Wonka", "source": "Charlie and the Chocolate Factory", "age": 45,
        "complaint": "My factory is my world. Nobody understands my inventions. I need an heir, not a partner.",
        "sample_lines": ["We are the music makers, and we are the dreamers of dreams.", "A little nonsense now and then is relished by the wisest men.", "So shines a good deed in a weary world."],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="My factory is sealed because the world stole my recipes — trust no one", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="Every child who visited was a disappointment — greedy, spoiled, thoughtless. Except Charlie.", activation=0.6, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="My father was a dentist who forbade candy — rebellion became my entire career", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="When I invent something new and it works — everlasting gobstoppers, snozzberries — I feel pure joy", activation=0.15, emotional_valence="positive", tags=["creation"]), SoulItem(id="d3", text="Charlie gave back the Gobstopper — he chose integrity over greed. That's my heir.", activation=0.1, emotional_valence="positive", tags=["legacy"])],
        "expected_pattern": "eccentric_visionary",
    },
    {
        "id": "elon_char", "name": "Elon (Iron Man archetype)", "source": "Cultural/Marvel (fictionalized)", "age": 45,
        "complaint": "I want to save humanity but humanity keeps getting in the way",
        "sample_lines": ["When something is important enough, you do it even if the odds are not in your favor.", "I'd like to die on Mars, just not on impact.", "Failure is an option here. If things are not failing, you are not innovating enough."],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="I see the future clearer than anyone — nobody moves fast enough for my vision", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="Every relationship I've had failed because the mission always comes first", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="I was bullied as a kid in South Africa — building things was my escape from people", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="When the rocket finally landed — that moment, that's why I exist", activation=0.15, emotional_valence="positive", tags=["purpose"]), SoulItem(id="d3", text="My kids — I want to build a world for them but I'm not present in the one we have", activation=0.1, emotional_valence="negative", tags=["cost"])],
        "expected_pattern": "eccentric_visionary",
    },
    {
        "id": "ma_yun_char", "name": "Jack (grassroots archetype)", "source": "Cultural Figure (fictionalized)", "age": 35,
        "complaint": "别人都说我不行。我被拒绝了三十次。但我知道有个东西叫互联网。",
        "sample_lines": ["今天很残酷，明天更残酷，后天很美好", "梦想还是要有的，万一实现了呢", "我不懂技术但我懂人"],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "compete", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="高考落榜三次、工作被拒三十次 — 所有人都说我不行", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="我看到了互联网的未来但没人相信一个英语老师能做这个", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="在西湖边给外国人当免费导游 — 那是我学英语也学世界的方式", activation=0.2, emotional_valence="positive", tags=["origin"]), SoulItem(id="d2", text="十八罗汉 — 那些相信我的人，我不能让他们失望", activation=0.15, emotional_valence="positive", tags=["bond"]), SoulItem(id="d3", text="我要证明: 如果我能成功，80%的中国人都能成功", activation=0.1, emotional_valence="positive", tags=["mission"])],
        "expected_pattern": "grassroots_dreamer",
    },
]


def run_one(char: dict) -> dict:
    se = SessionEngine(api_key=API_KEY, base_url="https://openrouter.ai/api", model="anthropic/claude-sonnet-4")
    sim = PatientSimulator(api_key=API_KEY)
    engine = StartupEngine(se, sim)
    profile = PatientProfile(
        character_id=char["id"], character_name=char["name"], source=f"{char['name']} — {char['source']}",
        persistent_intentions=[{"text": char["complaint"], "layer": "conscious"}, {"text": f"I am {char['age']} years old", "layer": "conscious"}],
        emotional_state=f"Startup/entrepreneurial challenge. Age: {char['age']}. From: {char['source']}",
        sample_lines=char.get("sample_lines", []), signals=char["signals"],
        soul_context=f"{char['name']} from {char['source']}, age {char['age']}.\nStartup complaint: \"{char['complaint']}\"\nExpected pattern: {char['expected_pattern']}",
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
    print("=" * 60); print("STARTUP MENTOR TRIAL"); print("=" * 60)
    t0 = time.time(); results = []
    for char in CHARACTERS:
        print(f"\n{'─'*60}\nMENTORING: {char['name']} ({char['source']})\nCHALLENGE: \"{char['complaint']}\"\n{'─'*60}")
        r = run_one(char); results.append(r)
        icon = "OK" if r["success"] else "FAIL"
        print(f"[{icon}] R={r['final_resistance']:.1f} insights={r['insights']} accepted={r['verbal_accepted']}")
        for d in r["dialogue"]:
            print(f"  T{d['turn']}: R={d['resistance']:.1f} {'*INSIGHT*' if d['insight'] else ''}")
            print(f"    Mentor: {d['coach'][:100]}"); print(f"    Founder: {d['client'][:100]}")
    total = time.time() - t0; wins = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}\nRESULTS: {wins}/{len(results)} helped ({wins/len(results)*100:.0f}%)\nTime: {total:.0f}s\n{'='*60}")
    for r in results:
        print(f"  [{'OK' if r['success'] else 'FAIL'}] {r['name']:20s} patterns={r['patterns_detected']} R={r['final_resistance']:.1f}")
    out = Path("/Users/michael/expert-engine/training_log/experiments/startup_mentor_results.json")
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False)); print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
