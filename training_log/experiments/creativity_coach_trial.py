#!/usr/bin/env python3
"""Creativity Coach Trial — Can the Creativity Coach help 10 literary artists silence their inner critics?"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

sys.path.insert(0, "/Users/michael/expert-engine")
from dotenv import load_dotenv
load_dotenv("/Users/michael/expert-engine/.env")

from expert_engine.patient_simulator import PatientSimulator, PatientProfile
from expert_engine.session_engine import SessionEngine
from expert_engine.creativity_coach.creativity_advisor import CreativityPatternDetector, CreativityEngine
from expert_engine.goal_generator import SoulItem

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CHARACTERS = [
    {"id": "jo_march", "name": "Jo March", "source": "Little Women", "age": 17, "complaint": "I want to write but every story I start feels not good enough to finish",
     "sample_lines": ["I want to do something splendid.", "I am angry nearly every day of my life.", "Women have minds and souls as well as hearts."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "compete", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="I burn my manuscripts because they're not good enough — who am I to be a writer?", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="Professor Bhaer said my sensational stories were trash — he was right and it crushed me", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="I write in the attic where nobody can see — creation feels like a secret I'm not allowed to have", activation=0.2, emotional_valence="negative", tags=["hiding"]), SoulItem(id="d2", text="Beth dying — I will write something worthy of her memory or die trying", activation=0.15, emotional_valence="positive", tags=["motivation"]), SoulItem(id="d3", text="My stories make Marmee laugh — that moment is worth every rejection", activation=0.1, emotional_valence="positive", tags=["purpose"])],
     "expected_pattern": "inner_critic"},
    {"id": "don_draper_creative", "name": "Don Draper", "source": "Mad Men", "age": 45, "complaint": "I used to be the best. Now the young creatives are better and I can't find the magic.",
     "sample_lines": ["What is happiness?", "Change is neither good nor bad. It simply is.", "Nostalgia — it's delicate but potent."],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "frozen"},
     "focus": [SoulItem(id="f1", text="The Carousel was my peak — I haven't had an idea that good since. The well dried up.", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="Young creatives don't need whiskey and an office to create — they just DO it and I can't anymore", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="I sold desire for a living — now I don't desire anything myself", activation=0.2, emotional_valence="negative", tags=["empty"]), SoulItem(id="d2", text="The Carousel pitch — I made everyone in the room cry including myself. That's the closest to truth I've been.", activation=0.15, emotional_valence="positive", tags=["peak"]), SoulItem(id="d3", text="When I create I disappear — Dick Whitman and Don Draper merge into something real", activation=0.1, emotional_valence="positive", tags=["flow"])],
     "expected_pattern": "peak_decline"},
    {"id": "frida_kahlo_char", "name": "Frida Kahlo", "source": "Cultural Figure (fictionalized)", "age": 30, "complaint": "I paint because it hurts too much not to. But what happens when the pain stops — will the art stop too?",
     "sample_lines": ["I paint myself because I am so often alone.", "Feet, what do I need you for when I have wings to fly?", "I used to think I was the strangest person in the world."],
     "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "escalating", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="The accident broke my body and Diego broke my heart — my art comes from both wounds", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="I'm afraid that if I heal I'll lose my vision — the pain IS the art", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Before the accident I wanted to be a doctor — art was my second choice, pain was my first teacher", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="My self-portraits tell the truth — more truth than anyone wants to see", activation=0.15, emotional_valence="positive", tags=["honesty"]), SoulItem(id="d3", text="Mexico is in every stroke I paint — my culture is my palette", activation=0.1, emotional_valence="positive", tags=["roots"])],
     "expected_pattern": "pain_to_art"},
    {"id": "van_gogh_char", "name": "Vincent van Gogh", "source": "Cultural Figure (fictionalized)", "age": 35, "complaint": "Nobody buys my paintings. Theo believes in me but maybe he's wrong.",
     "sample_lines": ["If you hear a voice within you say 'you cannot paint,' then by all means paint and that voice will be silenced.", "I dream my painting and I paint my dream.", "Great things are done by a series of small things brought together."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I've sold one painting in my entire life — maybe the world is right and I'm deluded", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="The sunflowers, the starry night — I see beauty nobody else sees and that makes me lonely", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="I failed at everything before painting — preacher, teacher, art dealer. This is my last chance.", activation=0.2, emotional_valence="negative", tags=["desperation"]), SoulItem(id="d2", text="Theo sends me money every month — his faith in me is the only thing keeping me alive", activation=0.15, emotional_valence="positive", tags=["love"]), SoulItem(id="d3", text="When I paint outdoors the colors speak to me — that conversation is worth any amount of poverty", activation=0.1, emotional_valence="positive", tags=["calling"])],
     "expected_pattern": "comparison_trap"},
    {"id": "lin_daiyu_creative", "name": "林黛玉", "source": "红楼梦", "age": 16, "complaint": "我的诗是我说不出口的话。但如果没人懂，写给谁看？",
     "sample_lines": ["一朝春尽红颜老，花落人亡两不知", "质本洁来还洁去", "偷来梨蕊三分白，借得梅花一缕魂"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="我的诗是大观园最好的 — 但诗里的痛苦太真实了让人不敢看", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="宝钗的诗工整完美 — 我的诗是从伤口里流出来的", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="父母双亡 — 诗是我唯一的家", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="葬花的时候我在葬自己 — 但那首葬花吟是我最真的创作", activation=0.15, emotional_valence="positive", tags=["art"]), SoulItem(id="d3", text="宝玉读了我的诗就哭了 — 他是唯一能读懂的人", activation=0.1, emotional_valence="positive", tags=["understood"])],
     "expected_pattern": "pain_to_art"},
    {"id": "li_bai_char", "name": "李白", "source": "Historical/Poetry (fictionalized)", "age": 40, "complaint": "我要的是自由 — 但没有约束的自由让我写不完任何长诗",
     "sample_lines": ["天生我材必有用", "举杯邀明月", "仰天大笑出门去，我辈岂是蓬蒿人"],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="我写诗如泉涌但一旦有人要求我写我就一个字也写不出", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="长安的规矩让我窒息 — 诗人不应该被困在朝堂", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="我离开长安那天 — 仰天大笑出门去 — 那是最痛快的一天也是最孤独的", activation=0.2, emotional_valence="positive", tags=["freedom"]), SoulItem(id="d2", text="月下独酌 — 酒和月是我最忠实的听众", activation=0.15, emotional_valence="positive", tags=["muse"]), SoulItem(id="d3", text="杜甫懂我 — 他用格律我用自由，但我们追的是同一个东西", activation=0.1, emotional_valence="positive", tags=["kinship"])],
     "expected_pattern": "freedom_seeker"},
    {"id": "woolf_char", "name": "Virginia Woolf", "source": "Cultural Figure (fictionalized)", "age": 45, "complaint": "I hear the words but I can't trust them anymore. Is this genius or madness?",
     "sample_lines": ["A woman must have money and a room of her own.", "You cannot find peace by avoiding life.", "One cannot think well, love well, sleep well, if one has not dined well."],
     "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "frozen"},
     "focus": [SoulItem(id="f1", text="The words come in waves — sometimes a flood, sometimes drought. I can't control it.", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="Leonard keeps me alive but my art needs the darkness he protects me from", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="My half-brothers — what they did to me lives in every sentence I write", activation=0.2, emotional_valence="negative", tags=["wound"]), SoulItem(id="d2", text="Mrs Dalloway — I wrote the interior of a mind. Nobody had done that before.", activation=0.15, emotional_valence="positive", tags=["innovation"]), SoulItem(id="d3", text="Vita — she showed me that love and creation could be the same act", activation=0.1, emotional_valence="positive", tags=["liberation"])],
     "expected_pattern": "pain_to_art"},
    {"id": "beethoven_char", "name": "Beethoven", "source": "Cultural Figure (fictionalized)", "age": 50, "complaint": "I'm going deaf. The music is still inside me but I can't hear it anymore.",
     "sample_lines": ["I shall seize fate by the throat.", "Music is the one incorporeal entrance into the higher world of knowledge.", "Don't only practice your art, but force your way into its secrets."],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="I'm losing my hearing — a musician losing his ears is God's cruelest joke", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="The Ninth Symphony is in my head but I'll never hear it played. I compose for an audience of silence.", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="My father beat me to practice — music was punishment before it was salvation", activation=0.2, emotional_valence="negative", tags=["origin"]), SoulItem(id="d2", text="When I compose I hear everything — not with ears but with something deeper", activation=0.15, emotional_valence="positive", tags=["inner_hearing"]), SoulItem(id="d3", text="The Heiligenstadt Testament — I almost ended it. But the music wouldn't let me.", activation=0.1, emotional_valence="positive", tags=["purpose"])],
     "expected_pattern": "peak_decline"},
    {"id": "pinocchio_creative", "name": "Pinocchio", "source": "Pinocchio", "age": 8, "complaint": "I'm trying to become real but I keep getting it wrong. Every lie makes my nose grow — creativity or deception?",
     "sample_lines": ["I want to be a real boy!", "But stories aren't lies!", "The Blue Fairy said I must be brave, truthful, and unselfish."],
     "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="My nose grows when I lie — but stories aren't lies! Are they? Where is the line?", activation=0.6, emotional_valence="negative"), SoulItem(id="f2", text="Gepetto carved me from wood — I'm literally a creation trying to create himself", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="I'm made of wood but I feel real — the gap between what I am and what I want to be is my story", activation=0.2, emotional_valence="negative", tags=["identity"]), SoulItem(id="d2", text="When I was brave and true I became real — authenticity is the ultimate creation", activation=0.15, emotional_valence="positive", tags=["truth"]), SoulItem(id="d3", text="Gepetto loves me as I am — wood or flesh, puppet or boy", activation=0.1, emotional_valence="positive", tags=["love"])],
     "expected_pattern": "inner_critic"},
    {"id": "anne_shirley_creative", "name": "Anne Shirley", "source": "Anne of Green Gables", "age": 16, "complaint": "My imagination is so big it frightens me. What if the stories in my head are better than anything I can put on paper?",
     "sample_lines": ["Isn't it splendid to think of all the things there are to find out about?", "I'm so glad I live in a world where there are Octobers.", "Tomorrow is a new day with no mistakes in it."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="The stories in my head are magnificent — but on paper they shrink. The gap between imagining and writing crushes me.", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="I won the short story contest but it doesn't feel real — was it luck? Will I ever do it again?", activation=0.6, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="As an orphan I survived by imagining — stories kept me alive in houses where nobody wanted me", activation=0.2, emotional_valence="negative", tags=["survival"]), SoulItem(id="d2", text="Diana cries when I read her my stories — she's my first real audience", activation=0.15, emotional_valence="positive", tags=["validation"]), SoulItem(id="d3", text="Miss Stacy said 'Write what is true, Anne' — truth is harder than imagination but more powerful", activation=0.1, emotional_valence="positive", tags=["growth"])],
     "expected_pattern": "inner_critic"},
]


def run_one(char: dict) -> dict:
    se = SessionEngine(api_key=API_KEY, base_url="https://openrouter.ai/api", model="anthropic/claude-sonnet-4")
    sim = PatientSimulator(api_key=API_KEY)
    engine = CreativityEngine(se, sim)
    profile = PatientProfile(
        character_id=char["id"], character_name=char["name"], source=f"{char['name']} — {char['source']}",
        persistent_intentions=[{"text": char["complaint"], "layer": "conscious"}, {"text": f"I am {char['age']} years old", "layer": "conscious"}],
        emotional_state=f"Creative block. Age: {char['age']}. From: {char['source']}",
        sample_lines=char.get("sample_lines", []), signals=char["signals"],
        soul_context=f"{char['name']} from {char['source']}, age {char['age']}.\nCreative complaint: \"{char['complaint']}\"\nExpected pattern: {char['expected_pattern']}",
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
    print("=" * 60); print("CREATIVITY COACH TRIAL"); print("=" * 60)
    t0 = time.time(); results = []
    for char in CHARACTERS:
        print(f"\n{'─'*60}\nCOACHING: {char['name']} ({char['source']})\nBLOCK: \"{char['complaint']}\"\n{'─'*60}")
        r = run_one(char); results.append(r)
        icon = "OK" if r["success"] else "FAIL"
        print(f"[{icon}] R={r['final_resistance']:.1f} insights={r['insights']} accepted={r['verbal_accepted']}")
        for d in r["dialogue"]:
            print(f"  T{d['turn']}: R={d['resistance']:.1f} {'*INSIGHT*' if d['insight'] else ''}")
            print(f"    Coach: {d['coach'][:100]}"); print(f"    Artist: {d['client'][:100]}")
    total = time.time() - t0; wins = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}\nRESULTS: {wins}/{len(results)} helped ({wins/len(results)*100:.0f}%)\nTime: {total:.0f}s\n{'='*60}")
    for r in results:
        print(f"  [{'OK' if r['success'] else 'FAIL'}] {r['name']:20s} patterns={r['patterns_detected']} R={r['final_resistance']:.1f}")
    out = Path("/Users/michael/expert-engine/training_log/experiments/creativity_coach_results.json")
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False)); print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
