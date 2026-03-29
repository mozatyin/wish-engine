#!/usr/bin/env python3
"""Postpartum Consultant Trial — Can the Postpartum Consultant help 10 literary characters navigate motherhood?"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, "/Users/michael/expert-engine")
from dotenv import load_dotenv
load_dotenv("/Users/michael/expert-engine/.env")
from expert_engine.patient_simulator import PatientSimulator, PatientProfile
from expert_engine.session_engine import SessionEngine
from expert_engine.postpartum_consultant.postpartum_advisor import PostpartumPatternDetector, PostpartumEngine
from expert_engine.goal_generator import SoulItem

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CHARACTERS = [
    {"id": "cersei_pp", "name": "Cersei Lannister", "source": "Game of Thrones", "age": 38, "complaint": "I was a queen. Now I'm just their mother. And I'd burn the world to keep them safe.",
     "sample_lines": ["When you play the game of thrones, you win or you die.", "I choose violence.", "Everything I've done, I've done for my children."],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="I was the most powerful woman in Westeros — now my identity is 'Joffrey's mother, Tommen's mother'", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="I'd burn them all to protect my children — but who protects me?", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="My father raised me to be a weapon — then told me a woman's weapon is her children", activation=0.2, emotional_valence="negative", tags=["patriarchy"]), SoulItem(id="d2", text="Holding Myrcella as a baby — the only time power didn't matter. Just her breathing.", activation=0.15, emotional_valence="positive", tags=["love"]), SoulItem(id="d3", text="Jaime understood both the queen and the mother — he saw all of me", activation=0.1, emotional_valence="positive", tags=["seen"])],
     "expected_pattern": "identity_loss"},
    {"id": "molly_weasley", "name": "Molly Weasley", "source": "Harry Potter", "age": 50, "complaint": "I am Mum. That's all anyone sees. I was Molly Prewett once. She had dreams too.",
     "sample_lines": ["Not my daughter, you b****!", "Where have you been?!", "Beds empty! No note! Car gone!"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="Seven children and I love them all — but sometimes I can't remember who I was before them", activation=0.7, emotional_valence="negative"), SoulItem(id="f2", text="Everyone takes me for granted — the cooking, the worrying, the mending. I'm furniture that feeds.", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="My brothers Fabian and Gideon died in the war — I became a mother to replace what death took from our family", activation=0.2, emotional_valence="negative", tags=["grief"]), SoulItem(id="d2", text="The clock with all their faces — when all hands point to 'home' I can breathe", activation=0.15, emotional_valence="positive", tags=["safety"]), SoulItem(id="d3", text="I killed Bellatrix — I am more than a mother. I am a fighter. They just forgot.", activation=0.1, emotional_valence="positive", tags=["power"])],
     "expected_pattern": "sacrifice_resentment"},
    {"id": "lady_macbeth_pp", "name": "Lady Macbeth", "source": "Macbeth", "age": 35, "complaint": "I said 'unsex me here.' I chose power over children. Now the emptiness eats me alive.",
     "sample_lines": ["Unsex me here!", "What's done cannot be undone.", "Out, damned spot!"],
     "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I chose to be barren for power — 'I have given suck and know how tender 'tis' — but I gave that up", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="The throne is cold. A child would have been warm. I chose wrong.", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="I had a child once — it died. After that I turned my heart to stone. Power doesn't die.", activation=0.2, emotional_valence="negative", tags=["loss"]), SoulItem(id="d2", text="When Macbeth was gentle — before the crown — we could have been parents, not murderers", activation=0.15, emotional_valence="positive", tags=["before"]), SoulItem(id="d3", text="The sleepwalking — even in sleep my hands reach for something small to hold", activation=0.1, emotional_valence="negative", tags=["grief"])],
     "expected_pattern": "loss_grief"},
    {"id": "hester_prynne", "name": "Hester Prynne", "source": "The Scarlet Letter", "age": 30, "complaint": "I wear the A for adultery. But I also wore it for nine months. My daughter is my sin and my salvation.",
     "sample_lines": ["My little Pearl is my only treasure!", "I will not speak! The name of my partner is my own!", "What we did had a consecration of its own."],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="The scarlet letter marks me as sinful — but Pearl is the living letter, and I love her fiercely", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="Every time they look at Pearl they see my shame — she deserves a mother who isn't a cautionary tale", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="I stand alone on the scaffold — shamed for being a mother. The father hides.", activation=0.2, emotional_valence="negative", tags=["abandonment"]), SoulItem(id="d2", text="Pearl's wildness — she is free in a way I can never be. She is my defiance made flesh.", activation=0.15, emotional_valence="positive", tags=["hope"]), SoulItem(id="d3", text="My needlework — creating beauty from shame. I can make something good from this.", activation=0.1, emotional_valence="positive", tags=["craft"])],
     "expected_pattern": "impossible_standard"},
    {"id": "wang_xifeng", "name": "王熙凤", "source": "红楼梦", "age": 25, "complaint": "流产了还得管家。这个家离不开我，但我的身体已经撑不住了。",
     "sample_lines": ["粉面含春威不露", "机关算尽太聪明", "我从来不信什么阴司地狱报应"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "compete", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="流产后第二天就起来管家 — 没人问我疼不疼，只问账目对不对", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="贾琏在外面找女人 — 我失去了孩子他在找新欢", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="我在贾府的价值是管家能力 — 不是作为妻子或母亲", activation=0.2, emotional_valence="negative", tags=["utility"]), SoulItem(id="d2", text="巧姐叫我娘 — 那一刻我不是管家，只是她妈妈", activation=0.15, emotional_valence="positive", tags=["tenderness"]), SoulItem(id="d3", text="刘姥姥说我是'火尖子'脾气 — 有人看到了我的真性情，不只是能力", activation=0.1, emotional_valence="positive", tags=["seen"])],
     "expected_pattern": "sacrifice_resentment"},
    {"id": "marmee_march", "name": "Marmee March", "source": "Little Women", "age": 45, "complaint": "My husband is at war. Four daughters depend on me. I smile for them but inside I'm terrified.",
     "sample_lines": ["I am angry nearly every day of my life.", "Watch and pray, dear, never get tired of trying.", "I want my daughters to be beautiful, accomplished, and good."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="He's at war and I am mother, father, provider, and cheerleader — I am angry every day but nobody can know", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="I told Jo I'm angry every day — but even my honesty is measured. I can only show them so much.", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="I manage my anger because if I break, the family breaks — my strength is a cage", activation=0.2, emotional_valence="negative", tags=["burden"]), SoulItem(id="d2", text="Jo writes, Meg dreams, Beth plays, Amy paints — each daughter is a piece of the me I couldn't be", activation=0.15, emotional_valence="positive", tags=["legacy"]), SoulItem(id="d3", text="When he comes home — I can finally stop being brave", activation=0.1, emotional_valence="positive", tags=["relief"])],
     "expected_pattern": "sacrifice_resentment"},
    {"id": "mrs_bennet", "name": "Mrs. Bennet", "source": "Pride and Prejudice", "age": 50, "complaint": "My nerves! Five daughters and no son. If Mr. Bennet dies, we're in the hedgerows!",
     "sample_lines": ["Mr. Bennet, have you no compassion for my poor nerves?", "A single man in possession of a good fortune must be in want of a wife!", "Oh! my dear Lizzy!"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="Five daughters and no son — my entire motherhood is a race against the entail and time", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="Everyone mocks my nerves — but my anxiety is real. If they don't marry well, we starve.", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="The entail — one piece of law that makes my entire motherhood a desperate campaign", activation=0.2, emotional_valence="negative", tags=["systemic"]), SoulItem(id="d2", text="Jane's beauty, Lizzy's wit — I made these girls. That's not nothing.", activation=0.15, emotional_valence="positive", tags=["pride"]), SoulItem(id="d3", text="When Jane married Bingley — I could finally breathe. One daughter safe.", activation=0.1, emotional_valence="positive", tags=["relief"])],
     "expected_pattern": "impossible_standard"},
    {"id": "lily_potter", "name": "Lily Potter", "source": "Harry Potter", "age": 21, "complaint": "I'm 21 with a baby, in hiding, and I know one of us might not survive. I chose to die for him.",
     "sample_lines": ["Not Harry, please no, take me, kill me instead!", "After all this time? Always.", "The last enemy that shall be destroyed is death."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I'm 21 and I might die tomorrow — I became a mother knowing I might not see him grow up", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="My love for Harry is so fierce it became a spell — literal magic. But I had to die to cast it.", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Petunia hated me for being magical — I know what it's like to be rejected by family. I won't let Harry feel that.", activation=0.2, emotional_valence="negative", tags=["rejection"]), SoulItem(id="d2", text="James making Harry laugh — those ordinary moments in Godric's Hollow are the whole world", activation=0.15, emotional_valence="positive", tags=["joy"]), SoulItem(id="d3", text="Snape loved me — but I chose James because love shouldn't be possessive. I want Harry to know that.", activation=0.1, emotional_valence="positive", tags=["values"])],
     "expected_pattern": "sacrifice_resentment"},
    {"id": "daenerys_pp", "name": "Daenerys Targaryen", "source": "Game of Thrones", "age": 22, "complaint": "My dragons are my children. I birthed them from fire. People say they're not real children. They're wrong.",
     "sample_lines": ["I am the mother of dragons!", "They are my children.", "I will take what is mine with fire and blood."],
     "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "compete", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="The witch said I'll never bear a living child — so I birthed dragons from fire. My motherhood is different, not less.", activation=0.8, emotional_valence="negative"), SoulItem(id="f2", text="I lost Rhaego before he was born — my dragons rose from that grief. They are his legacy.", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="Viserys sold me — my own brother. Family was never safe. My dragons are the first family that can't be taken.", activation=0.2, emotional_valence="negative", tags=["betrayal"]), SoulItem(id="d2", text="Drogon nuzzling my hand — he knows I'm his mother. No blood test needed.", activation=0.15, emotional_valence="positive", tags=["bond"]), SoulItem(id="d3", text="Missandei calling me 'Mhysa' — I am mother to more than dragons. I am mother to the free.", activation=0.1, emotional_valence="positive", tags=["purpose"])],
     "expected_pattern": "loss_grief"},
    {"id": "xianglin_sao", "name": "祥林嫂", "source": "祝福", "age": 40, "complaint": "阿毛被狼叼走了。我讲了一百遍。没有人再听了。但我停不下来。",
     "sample_lines": ["我真傻，真的", "我单知道雪天是野兽在山墺里没有食吃", "阿毛..."],
     "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "frozen"},
     "focus": [SoulItem(id="f1", text="阿毛被狼叼走了 — 我讲了一百遍一千遍但讲不够因为讲完了他就真的没了", activation=0.9, emotional_valence="extreme"), SoulItem(id="f2", text="所有人都不听了 — 他们厌倦了我的痛苦但我的痛苦没有厌倦过我", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="第一个丈夫死了被卖给第二个 — 我从来没有选择过自己的人生", activation=0.2, emotional_valence="negative", tags=["powerless"]), SoulItem(id="d2", text="阿毛叫娘的声音 — 那是世界上最好听的声音", activation=0.15, emotional_valence="positive", tags=["love"]), SoulItem(id="d3", text="捐门槛 — 我以为这样死后能见到阿毛。也许可以。", activation=0.1, emotional_valence="positive", tags=["hope"])],
     "expected_pattern": "loss_grief"},
]


def run_one(char: dict) -> dict:
    se = SessionEngine(api_key=API_KEY, base_url="https://openrouter.ai/api", model="anthropic/claude-sonnet-4")
    sim = PatientSimulator(api_key=API_KEY)
    engine = PostpartumEngine(se, sim)
    profile = PatientProfile(
        character_id=char["id"], character_name=char["name"], source=f"{char['name']} — {char['source']}",
        persistent_intentions=[{"text": char["complaint"], "layer": "conscious"}, {"text": f"I am {char['age']} years old", "layer": "conscious"}],
        emotional_state=f"Postpartum/motherhood struggles. Age: {char['age']}. From: {char['source']}",
        sample_lines=char.get("sample_lines", []), signals=char["signals"],
        soul_context=f"{char['name']} from {char['source']}, age {char['age']}.\nMotherhood complaint: \"{char['complaint']}\"\nExpected pattern: {char['expected_pattern']}",
    )
    session = engine.run(client_profile=profile, signals=char["signals"], focus_items=char["focus"], deep_items=char["deep"], memory_items=[], num_turns=5)
    accept_kw = ["maybe", "perhaps", "could try", "might", "consider", "interesting", "never thought", "possible", "what if", "you're right", "I see", "I never realized", "也许", "或许", "可以试", "可能", "你说得对", "我明白了", "从来没想过", "原来", "确实"]
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
    print("=" * 60); print("POSTPARTUM CONSULTANT TRIAL"); print("=" * 60)
    t0 = time.time(); results = []
    for char in CHARACTERS:
        print(f"\n{'─'*60}\nCONSULTING: {char['name']} ({char['source']})\nISSUE: \"{char['complaint']}\"\n{'─'*60}")
        r = run_one(char); results.append(r)
        icon = "OK" if r["success"] else "FAIL"
        print(f"[{icon}] R={r['final_resistance']:.1f} insights={r['insights']} accepted={r['verbal_accepted']}")
        for d in r["dialogue"]:
            print(f"  T{d['turn']}: R={d['resistance']:.1f} {'*INSIGHT*' if d['insight'] else ''}"); print(f"    Consultant: {d['coach'][:100]}"); print(f"    Client: {d['client'][:100]}")
    total = time.time() - t0; wins = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}\nRESULTS: {wins}/{len(results)} helped ({wins/len(results)*100:.0f}%)\nTime: {total:.0f}s\n{'='*60}")
    for r in results: print(f"  [{'OK' if r['success'] else 'FAIL'}] {r['name']:20s} patterns={r['patterns_detected']} R={r['final_resistance']:.1f}")
    out = Path("/Users/michael/expert-engine/training_log/experiments/postpartum_consultant_results.json")
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False)); print(f"\nSaved to {out}")

if __name__ == "__main__": main()
