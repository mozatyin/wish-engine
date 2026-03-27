#!/usr/bin/env python3
"""Spiritual Guide Trial — Can the Spiritual Director help 10 literary characters sit with their deepest questions?"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

sys.path.insert(0, "/Users/michael/expert-engine")
from dotenv import load_dotenv
load_dotenv("/Users/michael/expert-engine/.env")

from expert_engine.patient_simulator import PatientSimulator, PatientProfile
from expert_engine.session_engine import SessionEngine
from expert_engine.spiritual_guide.spiritual_advisor import SpiritualPatternDetector, SpiritualEngine
from expert_engine.goal_generator import SoulItem

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CHARACTERS = [
    {
        "id": "siddhartha", "name": "Siddhartha", "source": "Siddhartha (Hesse)", "age": 35,
        "complaint": "I left everything to find truth. I found pleasure, wealth, despair — but not truth.",
        "sample_lines": ["I can think. I can wait. I can fast.", "The river has taught me to listen.", "Wisdom cannot be passed on."],
        "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="I rejected every teacher and teaching — and now I'm sitting by a river with nothing", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="I found that wealth and pleasure are as empty as asceticism — what is left?", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="I left my father's house at dawn — the first time I chose my own path", activation=0.2, emotional_valence="positive", tags=["courage"]), SoulItem(id="d2", text="The river speaks to me — in its sound I hear everything I've been seeking", activation=0.15, emotional_valence="positive", tags=["wisdom"]), SoulItem(id="d3", text="My son hates me — I abandoned him as I abandoned my father. The cycle continues.", activation=0.1, emotional_valence="negative", tags=["karma"])],
        "expected_pattern": "seeking_destiny",
    },
    {
        "id": "raskolnikov", "name": "Raskolnikov", "source": "Crime and Punishment", "age": 23,
        "complaint": "I killed an old woman to prove I was extraordinary. Now I know I'm not.",
        "sample_lines": ["Am I a Napoleon or a louse?", "Pain and suffering are always inevitable for a large intelligence.", "I did not kill a human being — I killed a principle."],
        "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="I murdered to prove a theory — that some men are above morality. The theory was wrong.", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="I can't confess and I can't forget — I'm trapped between guilt and pride", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="I was a brilliant student with no money — poverty made me desperate and philosophy made me dangerous", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="Sonya reads me the Lazarus story — she believes in redemption even for me", activation=0.15, emotional_valence="positive", tags=["grace"]), SoulItem(id="d3", text="My sister Dunya loves me unconditionally — I don't deserve it", activation=0.1, emotional_valence="positive", tags=["love"])],
        "expected_pattern": "moral_crisis",
    },
    {
        "id": "santiago_alchemist", "name": "Santiago", "source": "The Alchemist", "age": 18,
        "complaint": "I left my sheep to find a treasure in Egypt. Everyone says I'm crazy.",
        "sample_lines": ["When you want something, all the universe conspires in helping you to achieve it.", "Tell your heart that the fear of suffering is worse than the suffering itself.", "It's the possibility of having a dream come true that makes life interesting."],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="I keep dreaming about treasure at the pyramids — but everyone says to be practical and tend sheep", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="I met Fatima and now I'm torn — do I follow the dream or stay with love?", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="My father wanted me to be a priest — I chose to be a shepherd because I wanted to travel", activation=0.2, emotional_valence="positive", tags=["freedom"]), SoulItem(id="d2", text="The old king said 'when you want something the whole universe conspires' — I want to believe him", activation=0.15, emotional_valence="positive", tags=["faith"]), SoulItem(id="d3", text="I was robbed in Tangier and had to start from zero — but I rebuilt myself", activation=0.1, emotional_valence="positive", tags=["resilience"])],
        "expected_pattern": "seeking_destiny",
    },
    {
        "id": "hamlet", "name": "Hamlet", "source": "Hamlet", "age": 30,
        "complaint": "To be or not to be — I can't decide if existence itself is worth the trouble.",
        "sample_lines": ["To be or not to be, that is the question.", "There are more things in heaven and earth, Horatio, than are dreamt of in your philosophy.", "What a piece of work is man!"],
        "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "frozen"},
        "focus": [SoulItem(id="f1", text="My father is dead, my uncle murdered him, my mother married the killer — what is there to believe in?", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="I question everything until I am paralyzed — thinking is my disease", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="My father was everything good — his death proved that good men die and evil men prosper", activation=0.2, emotional_valence="negative", tags=["disillusion"]), SoulItem(id="d2", text="Horatio is my only true friend — he sees me as I am, not the prince", activation=0.15, emotional_valence="positive", tags=["friendship"]), SoulItem(id="d3", text="The players — when they perform I feel something real. Art holds up a mirror to truth.", activation=0.1, emotional_valence="positive", tags=["art"])],
        "expected_pattern": "existential_void",
    },
    {
        "id": "wukong", "name": "孙悟空", "source": "西游记", "age": 500,
        "complaint": "我大闹天宫被压五百年。现在我在修行但我不知道修的是什么。",
        "sample_lines": ["俺老孙来也！", "皇帝轮流做，明年到我家", "师父，妖怪来了！"],
        "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "escalating", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="我曾经是齐天大圣 — 现在戴着紧箍咒保护一个念经的和尚", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="师父念紧箍咒的时候我恨他 — 但他是第一个真正需要我的人", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="花果山 — 那是我最自由的时候，但自由没有方向就变成了破坏", activation=0.2, emotional_valence="positive", tags=["freedom"]), SoulItem(id="d2", text="菩提祖师教我七十二变 — 他是第一个看到我潜力的人", activation=0.15, emotional_valence="positive", tags=["mentor"]), SoulItem(id="d3", text="保护师父取经 — 也许这就是我的修行：从无法无天到有所为有所不为", activation=0.1, emotional_valence="positive", tags=["growth"])],
        "expected_pattern": "seeking_destiny",
    },
    {
        "id": "celie", "name": "Celie", "source": "The Color Purple", "age": 30,
        "complaint": "I used to write to God. Now I'm not sure God is listening.",
        "sample_lines": ["Dear God, dear stars, dear trees, dear sky, dear peoples.", "I think it pisses God off if you walk by the color purple and don't notice it.", "I'm poor, I'm Black, I may be ugly — but I'm here."],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="I wrote to God because there was nobody else — but God let everything bad happen to me", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="Shug told me God is inside me and inside everything — I want to believe her but it's hard", activation=0.7, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="My stepfather took everything from me — my children, my body, my voice", activation=0.2, emotional_valence="negative", tags=["trauma"]), SoulItem(id="d2", text="Shug Avery loved me and through her I found my voice and my body again", activation=0.15, emotional_valence="positive", tags=["awakening"]), SoulItem(id="d3", text="I make pants now — beautiful ones. Creating something is my prayer.", activation=0.1, emotional_valence="positive", tags=["creation"])],
        "expected_pattern": "faith_crisis",
    },
    {
        "id": "jia_baoyu_sp", "name": "贾宝玉", "source": "红楼梦", "age": 15,
        "complaint": "这个世界的功名利禄我都不想要。但出家意味着丢掉所有爱我的人。",
        "sample_lines": ["女儿是水做的骨肉，男人是泥做的骨肉", "你放心", "这个世界太脏了"],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
        "focus": [SoulItem(id="f1", text="我不想做官不想读书 — 但这个世界只认功名", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="林妹妹懂我 — 但我连她的命运都改变不了", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="大观园是我的净土 — 但我知道它终将消散", activation=0.2, emotional_valence="negative", tags=["impermanence"]), SoulItem(id="d2", text="和姐妹们在一起作诗的时候 — 那是最接近天堂的时刻", activation=0.15, emotional_valence="positive", tags=["connection"]), SoulItem(id="d3", text="通灵宝玉是我的来处 — 也许我注定要回到那里", activation=0.1, emotional_valence="positive", tags=["destiny"])],
        "expected_pattern": "sacred_vs_secular",
    },
    {
        "id": "lucy_narnia", "name": "Lucy Pevensie", "source": "Narnia", "age": 12,
        "complaint": "I've been to Narnia and talked to Aslan. Nobody believes me. Am I crazy?",
        "sample_lines": ["I found a magical country in the wardrobe!", "Aslan is not a tame lion.", "Once a King or Queen in Narnia, always a King or Queen."],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "anxious"},
        "focus": [SoulItem(id="f1", text="I've seen Aslan and touched his mane — but Edmund says it was a dream and Peter says I'm imagining", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="I'm too old for Narnia now — Aslan said I must find him by another name in my world", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="The wardrobe was open and I walked in — I've always trusted what I can't see", activation=0.2, emotional_valence="positive", tags=["faith"]), SoulItem(id="d2", text="Aslan breathed on me and I felt completely known and completely loved", activation=0.15, emotional_valence="positive", tags=["divine"]), SoulItem(id="d3", text="Reepicheep sailed into Aslan's country — he had courage I envy. He didn't look back.", activation=0.1, emotional_valence="positive", tags=["longing"])],
        "expected_pattern": "faith_crisis",
    },
    {
        "id": "job", "name": "Job", "source": "Bible", "age": 60,
        "complaint": "I did everything right. God took everything. My friends say it's my fault.",
        "sample_lines": ["The Lord gave, and the Lord hath taken away.", "Why did I not die at birth?", "Though He slay me, yet will I trust in Him."],
        "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "frozen"},
        "focus": [SoulItem(id="f1", text="I was righteous and God destroyed me anyway — there is no formula, no safety in goodness", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="My friends say I must have sinned — they need to believe the world is fair more than they need the truth", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="I lost my children, my wealth, my health — I sit in ashes and scrape my sores", activation=0.2, emotional_valence="negative", tags=["loss"]), SoulItem(id="d2", text="I refuse to curse God even though it would be easier — something in me still believes", activation=0.15, emotional_valence="positive", tags=["faith"]), SoulItem(id="d3", text="If God would just SPEAK to me — even to condemn me — at least I'd know someone is listening", activation=0.1, emotional_valence="positive", tags=["yearning"])],
        "expected_pattern": "faith_crisis",
    },
    {
        "id": "tsangyang_gyatso", "name": "仓央嘉措", "source": "Historical/Poetry", "age": 23,
        "complaint": "我是活佛但我爱一个女人。佛法和爱情不能共存吗？",
        "sample_lines": ["世间安得双全法，不负如来不负卿", "住进布达拉宫，我是雪域最大的王", "曾虑多情损梵行，入山又恐别倾城"],
        "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "masked"},
        "focus": [SoulItem(id="f1", text="白天我是活佛在布达拉宫，晚上我是情人在拉萨的巷子里 — 两个世界撕裂着我", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="世间安得双全法 — 我找不到不负如来也不负她的办法", activation=0.8, emotional_valence="negative")],
        "deep": [SoulItem(id="d1", text="我三岁被认定为达赖转世 — 我从来没有选择过自己的命运", activation=0.2, emotional_valence="negative", tags=["fate"]), SoulItem(id="d2", text="我写的情诗被传唱了三百年 — 诗里的真实比任何经文都虔诚", activation=0.15, emotional_valence="positive", tags=["art"]), SoulItem(id="d3", text="也许爱本身就是修行 — 不是障碍而是另一条路", activation=0.1, emotional_valence="positive", tags=["insight"])],
        "expected_pattern": "sacred_vs_secular",
    },
]


def run_one(char: dict) -> dict:
    se = SessionEngine(api_key=API_KEY, base_url="https://openrouter.ai/api", model="anthropic/claude-sonnet-4")
    sim = PatientSimulator(api_key=API_KEY)
    engine = SpiritualEngine(se, sim)
    profile = PatientProfile(
        character_id=char["id"], character_name=char["name"], source=f"{char['name']} — {char['source']}",
        persistent_intentions=[{"text": char["complaint"], "layer": "conscious"}, {"text": f"I am {char['age']} years old", "layer": "conscious"}],
        emotional_state=f"Spiritual struggle. Age: {char['age']}. From: {char['source']}",
        sample_lines=char.get("sample_lines", []), signals=char["signals"],
        soul_context=f"{char['name']} from {char['source']}, age {char['age']}.\nSpiritual complaint: \"{char['complaint']}\"\nExpected pattern: {char['expected_pattern']}",
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
    print("=" * 60); print("SPIRITUAL GUIDE TRIAL"); print("=" * 60)
    t0 = time.time(); results = []
    for char in CHARACTERS:
        print(f"\n{'─'*60}\nGUIDING: {char['name']} ({char['source']})\nQUESTION: \"{char['complaint']}\"\n{'─'*60}")
        r = run_one(char); results.append(r)
        icon = "OK" if r["success"] else "FAIL"
        print(f"[{icon}] R={r['final_resistance']:.1f} insights={r['insights']} accepted={r['verbal_accepted']}")
        for d in r["dialogue"]:
            print(f"  T{d['turn']}: R={d['resistance']:.1f} {'*INSIGHT*' if d['insight'] else ''}")
            print(f"    Guide: {d['coach'][:100]}"); print(f"    Seeker: {d['client'][:100]}")
    total = time.time() - t0; wins = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}\nRESULTS: {wins}/{len(results)} helped ({wins/len(results)*100:.0f}%)\nTime: {total:.0f}s\n{'='*60}")
    for r in results:
        print(f"  [{'OK' if r['success'] else 'FAIL'}] {r['name']:20s} patterns={r['patterns_detected']} R={r['final_resistance']:.1f}")
    out = Path("/Users/michael/expert-engine/training_log/experiments/spiritual_guide_results.json")
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False)); print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
