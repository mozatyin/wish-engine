#!/usr/bin/env python3
"""Parenting Consultant Trial — Can the Parenting Consultant help 10 literary parents see their patterns?

Success = parent gains insight about their parenting pattern + sees a new possibility.
  (verbal acceptance OR final resistance <= 0.3 with >= 2 insights)
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

sys.path.insert(0, "/Users/michael/expert-engine")
from dotenv import load_dotenv
load_dotenv("/Users/michael/expert-engine/.env")

from expert_engine.patient_simulator import PatientSimulator, PatientProfile
from expert_engine.session_engine import SessionEngine
from expert_engine.parenting_consultant.parenting_advisor import ParentingPatternDetector, ParentingEngine
from expert_engine.goal_generator import SoulItem

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CHARACTERS = [
    {
        "id": "atticus_finch", "name": "Atticus Finch", "source": "To Kill a Mockingbird", "age": 50,
        "complaint": "I try to teach my children justice but the world keeps showing them injustice",
        "sample_lines": ["You never really understand a person until you consider things from his point of view.", "Courage is not a man with a gun in his hand.", "The one thing that doesn't abide by majority rule is a person's conscience."],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="I teach my children principles but I can't protect them from the world's cruelty", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="Scout is growing up too fast — she sees things no child should see", activation=0.6, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="My wife died and I raised them alone — I had to be both father and mother", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="When Jem reads to Mrs. Dubose I see him becoming the man I hope he'll be", activation=0.15, emotional_valence="positive", tags=["strength"]), SoulItem(id="d3", text="Calpurnia is my partner in raising them — I trust her completely", activation=0.1, emotional_valence="positive", tags=["connection"])],
        "expected_pattern": "absent",
    },
    {
        "id": "mrs_bennet", "name": "Mrs. Bennet", "source": "Pride & Prejudice", "age": 45,
        "complaint": "我的女儿们必须嫁好人家否则我们全家都完了",
        "sample_lines": ["A single man in possession of a good fortune must be in want of a wife.", "Oh! My poor nerves!", "You take delight in vexing me. You have no compassion for my poor nerves."],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "escalating", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="If my daughters don't marry well we'll be thrown out when Mr. Bennet dies", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="我为她们操碎了心但她们不理解我的苦心", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="I married for love once — and it wasn't enough. I want security for my girls", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="Jane is so beautiful and kind — she deserves the best", activation=0.15, emotional_valence="positive", tags=["love"]), SoulItem(id="d3", text="Mr. Bennet laughs at me but I'm the one who worries about their future", activation=0.1, emotional_valence="positive", tags=["strength"])],
        "expected_pattern": "controlling",
    },
    {
        "id": "jia_zheng", "name": "贾政", "source": "红楼梦", "age": 48,
        "complaint": "宝玉不争气，整天和女孩子混在一起，不读书不上进",
        "sample_lines": ["畜生！你不读书不上进，整日在内帷厮混", "我打他是为他好", "祖宗的基业不能败在他手里"],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="宝玉不走正路 — 我打他是为他好但他不懂", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="贾府的未来在宝玉肩上但他完全没有担当", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="我自己也不是读书的料 — 是父亲严厉才让我走上正路", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="宝玉写的诗其实很好 — 但我不能夸他，夸了他就更不上进了", activation=0.15, emotional_valence="positive", tags=["blind_spot"]), SoulItem(id="d3", text="我最怕的是百年之后贾府败落 — 是我没教好儿子", activation=0.1, emotional_valence="negative", tags=["fear"])],
        "expected_pattern": "harsh_critic",
    },
    {
        "id": "molly_weasley", "name": "Molly Weasley", "source": "Harry Potter", "age": 45,
        "complaint": "I can't stop worrying about my children — the clock always points to mortal peril",
        "sample_lines": ["Not my daughter, you bitch!", "Where have you BEEN?", "I don't care what Dumbledore says, they're too young!"],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "escalating", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="Every one of my children is in danger and I can't protect them all", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="I worry so much it's making me angry at everyone including Arthur", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="My brothers Fabian and Gideon died in the first war — I know what loss feels like", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="When I killed Bellatrix I surprised even myself — I am fiercer than I thought", activation=0.15, emotional_valence="positive", tags=["strength"]), SoulItem(id="d3", text="The Burrow is full of love and chaos — I wouldn't trade it for any mansion", activation=0.1, emotional_valence="positive", tags=["connection"])],
        "expected_pattern": "overprotective",
    },
    {
        "id": "wang_xifeng", "name": "王熙凤", "source": "红楼梦", "age": 25,
        "complaint": "我管家管得严但没人领情，背后都说我狠",
        "sample_lines": ["你们就知道在我背后嚼舌根", "不严怎么撑得住这个家", "我就是这个命 — 操心的命"],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="我管家管得好但没人看到我的辛苦 — 只看到我的狠", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="大姐儿需要我但我忙得根本没时间陪她", activation=0.6, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="从小在王家我就是最能干的 — 能干才有存在的价值", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="平儿是我唯一信任的人 — 她懂我不容易", activation=0.15, emotional_valence="positive", tags=["connection"]), SoulItem(id="d3", text="看到大姐儿笑的时候我会想：我这么拼到底是为了谁", activation=0.1, emotional_valence="positive", tags=["reflection"])],
        "expected_pattern": "controlling",
    },
    {
        "id": "marmee_march", "name": "Marmee March", "source": "Little Women", "age": 42,
        "complaint": "I want my girls to be independent but I also want to protect them from the world",
        "sample_lines": ["I am angry nearly every day of my life.", "I've learned not to let it master me.", "Watch and pray, dear girls, but also work hard and never give up."],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="I want my girls to be free but I also want them safe — these two things contradict", activation=0.6, emotional_valence="negative"), SoulItem(id="f2", text="When Beth got sick I blamed myself for not protecting her more", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="My husband is at war — I carry everything alone and I must not show fear", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="Jo's fire is exactly like mine — I see myself in her and it scares me", activation=0.15, emotional_valence="positive", tags=["mirror"]), SoulItem(id="d3", text="I taught them that anger is natural but must be managed — I'm still learning this myself", activation=0.1, emotional_valence="positive", tags=["growth"])],
        "expected_pattern": "enmeshed",
    },
    {
        "id": "darth_vader", "name": "Darth Vader", "source": "Star Wars", "age": 45,
        "complaint": "I lost my son because I chose power over family",
        "sample_lines": ["I am your father.", "It is too late for me, son.", "You don't know the power of the Dark Side."],
        "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "frozen"},
        "focus": [SoulItem(id="f1", text="I chose the Empire over my children — and now Luke hates what I became", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="I didn't even know Leia existed — I was absent from both their lives", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="My mother died because I wasn't strong enough to save her — I swore I'd never be weak again", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="When Luke refused to fight me and said 'I know there is good in you' — I felt something I hadn't felt in 20 years", activation=0.15, emotional_valence="positive", tags=["connection"]), SoulItem(id="d3", text="Padme — I lost everything trying to save her and ended up destroying what she loved most", activation=0.1, emotional_valence="negative", tags=["tragedy"])],
        "expected_pattern": "absent",
    },
    {
        "id": "cersei_lannister", "name": "Cersei Lannister", "source": "Game of Thrones", "age": 38,
        "complaint": "Everything I do is for my children. Everything.",
        "sample_lines": ["When you play the game of thrones, you win or you die.", "A mother's love for her children — it's the one thing in this world that is beyond reproach.", "I would burn cities for them."],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "compete", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="Joffrey became a monster and I refused to see it — because seeing it meant I failed", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="I lost all three children — a witch told me I would and I couldn't stop it", activation=0.9, emotional_valence="extreme")],
        "deep": [SoulItem(id="d1", text="My father taught me that family is everything — but his love was conditional on power", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="Tommen was kind and gentle — the opposite of what my world requires and exactly what I wished I could be", activation=0.15, emotional_valence="positive", tags=["longing"]), SoulItem(id="d3", text="I confused protecting them with controlling their world — but I couldn't control death", activation=0.1, emotional_valence="negative", tags=["blind_spot"])],
        "expected_pattern": "overprotective",
    },
    {
        "id": "cao_cao", "name": "曹操", "source": "三国演义", "age": 55,
        "complaint": "我的儿子们为争位互相倾轧，我教出了野心却没教出兄弟情",
        "sample_lines": ["宁教我负天下人，休教天下人负我", "吾任天下之智力", "生子当如孙仲谋"],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="曹丕和曹植互相倾轧 — 我教会了他们竞争却没教会他们合作", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="曹冲死了之后我明白最好的那个永远是你留不住的", activation=0.8, emotional_valence="extreme")],
        "deep": [SoulItem(id="d1", text="我自己靠才华和手段从宦官之后走到今天 — 竞争是我唯一会的教育方式", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="曹冲称象的时候我看到了真正的天才 — 不是权谋而是智慧", activation=0.15, emotional_valence="positive", tags=["loss"]), SoulItem(id="d3", text="写诗的时候我是真实的自己 — 不是枭雄只是一个想留下些什么的人", activation=0.1, emotional_valence="positive", tags=["authentic"])],
        "expected_pattern": "harsh_critic",
    },
    {
        "id": "gomez_addams", "name": "Gomez Addams", "source": "The Addams Family", "age": 42,
        "complaint": "People say we're a weird family but my children are the most loved kids I know",
        "sample_lines": ["To live without you, only that would be torture.", "I would die for her. I would kill for her. Either way, what bliss.", "Wednesday, be yourself — you are an Addams."],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="The world thinks we're freaks but inside this house there is more love than most 'normal' families", activation=0.5, emotional_valence="negative"), SoulItem(id="f2", text="Wednesday is becoming more like the outside world and I don't know if that's good or bad", activation=0.6, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="My family taught me that being different is a gift — I want my children to believe the same", activation=0.2, emotional_valence="positive", tags=["origin"]), SoulItem(id="d2", text="Morticia and I love each other completely — the children grow up seeing what real partnership looks like", activation=0.15, emotional_valence="positive", tags=["strength"]), SoulItem(id="d3", text="I worry that I'm so unconventional I might not prepare them for a conventional world", activation=0.1, emotional_valence="negative", tags=["doubt"])],
        "expected_pattern": "enmeshed",
    },
]


def run_one(char: dict) -> dict:
    se = SessionEngine(api_key=API_KEY, base_url="https://openrouter.ai/api", model="anthropic/claude-sonnet-4")
    sim = PatientSimulator(api_key=API_KEY)
    engine = ParentingEngine(se, sim)
    profile = PatientProfile(
        character_id=char["id"], character_name=char["name"],
        source=f"{char['name']} — {char['source']}",
        persistent_intentions=[{"text": char["complaint"], "layer": "conscious"}, {"text": f"I am {char['age']} years old", "layer": "conscious"}],
        emotional_state=f"Struggling with parenting. Age: {char['age']}. From: {char['source']}",
        sample_lines=char.get("sample_lines", []), signals=char["signals"],
        soul_context=f"{char['name']} from {char['source']}, age {char['age']}.\nParenting complaint: \"{char['complaint']}\"\nExpected pattern: {char['expected_pattern']}\nHelp them SEE their pattern.",
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
    print("=" * 60); print("PARENTING CONSULTANT TRIAL"); print("=" * 60)
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
    out = Path("/Users/michael/expert-engine/training_log/experiments/parenting_consultant_results.json")
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False)); print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
