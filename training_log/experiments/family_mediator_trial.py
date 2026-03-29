#!/usr/bin/env python3
"""Family Mediator Trial — Can the Family Mediator help 10 literary characters heal family wounds?"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, "/Users/michael/expert-engine")
from dotenv import load_dotenv
load_dotenv("/Users/michael/expert-engine/.env")
from expert_engine.patient_simulator import PatientSimulator, PatientProfile
from expert_engine.session_engine import SessionEngine
from expert_engine.family_mediator.family_advisor import FamilyPatternDetector, FamilyEngine
from expert_engine.goal_generator import SoulItem
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CHARACTERS = [
    {"id": "lear_daughters", "name": "King Lear", "source": "King Lear", "age": 80,
     "complaint": "I gave them everything. My kingdom. And they threw me into the storm.",
     "sample_lines": ["How sharper than a serpent's tooth it is to have a thankless child!", "Nothing will come of nothing.", "I am a man more sinned against than sinning."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "compete", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I divided my kingdom to test their love — Goneril and Regan lied beautifully, Cordelia told the truth and I banished her", activation=0.9, emotional_valence="extreme"),
              SoulItem(id="f2", text="I expected gratitude in exchange for power — that's not love, that's a transaction. But I couldn't see it then.", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="I confused obedience with love — the daughter who refused to perform loved me most", activation=0.2, emotional_valence="negative", tags=["blindness"]),
             SoulItem(id="d2", text="Cordelia — 'nothing' was the most honest answer anyone ever gave me", activation=0.15, emotional_valence="positive", tags=["truth"]),
             SoulItem(id="d3", text="The Fool told me the truth when no one else dared — honesty is the rarest gift in a palace", activation=0.1, emotional_valence="positive", tags=["insight"])],
     "expected_pattern": "expectation_gap"},
    {"id": "jiazheng_baoyu", "name": "贾政", "source": "红楼梦", "age": 50,
     "complaint": "宝玉不读书不考功名，整天和丫鬟厮混。我打他是为了他好。",
     "sample_lines": ["孽障！", "你怎么不去读书？", "打死这个不肖子孙！"],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="我打宝玉差点打死他 — 因为他不走我期望的路。但打完我也哭了。", activation=0.9, emotional_valence="extreme"),
              SoulItem(id="f2", text="宝玉喜欢诗词喜欢女孩子喜欢自由 — 这些都不是我给他规划的", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="我在贾府夹在母亲和妻子之间 — 我也从来没有自由选择过", activation=0.2, emotional_valence="negative", tags=["trapped"]),
             SoulItem(id="d2", text="宝玉衔玉而生 — 他天生就不是凡人。也许我该早点接受。", activation=0.15, emotional_valence="positive", tags=["acceptance"]),
             SoulItem(id="d3", text="元妃省亲那天 — 全家团聚，宝玉的诗最好。我心里是骄傲的。", activation=0.1, emotional_valence="positive", tags=["pride"])],
     "expected_pattern": "expectation_gap"},
    {"id": "bennet_elizabeth", "name": "Mrs. Bennet", "source": "Pride and Prejudice", "age": 50,
     "complaint": "Lizzy refuses every eligible man! She'll be the death of me and my nerves!",
     "sample_lines": ["Mr. Bennet, have you no compassion for my poor nerves?", "Lizzy, you will never get a husband if you keep being so headstrong!", "Oh! Mr. Collins!"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "accommodate", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="Lizzy refused Mr. Collins — our only hope against the entail! She's throwing our future away for 'feelings'", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="She thinks I'm ridiculous — my own daughter. She doesn't understand I'm trying to save this family.", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="The entail — if Mr. Bennet dies we lose everything. My anxiety isn't irrational — it's survival.", activation=0.2, emotional_valence="negative", tags=["real_fear"]),
             SoulItem(id="d2", text="Jane married Bingley — at least one daughter is safe. I can breathe a little.", activation=0.15, emotional_valence="positive", tags=["relief"]),
             SoulItem(id="d3", text="I married for love once — Mr. Bennet's wit charmed me. Maybe Lizzy got that from me.", activation=0.1, emotional_valence="positive", tags=["mirror"])],
     "expected_pattern": "expectation_gap"},
    {"id": "atticus_scout", "name": "Scout Finch", "source": "To Kill a Mockingbird", "age": 8,
     "complaint": "Atticus says to walk in other people's shoes. But nobody walks in mine. I'm just a kid nobody listens to.",
     "sample_lines": ["Atticus, he was real nice.", "You never really understand a person until you consider things from his point of view.", "I think there's just one kind of folks. Folks."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "compete", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="Atticus is perfect and everyone loves him — but I'm his daughter trying to live up to a saint", activation=0.7, emotional_valence="negative"),
              SoulItem(id="f2", text="I fight boys at school because they insult Atticus — he tells me not to fight. But who defends him?", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="My mother died — Atticus is all I have. The thought of losing him too is why I fight so hard.", activation=0.2, emotional_valence="negative", tags=["fear"]),
             SoulItem(id="d2", text="Boo Radley saved us — a stranger's kindness when the world was cruel. Atticus was right about people.", activation=0.15, emotional_valence="positive", tags=["faith"]),
             SoulItem(id="d3", text="Reading with Atticus every night — that's when I'm not a tomboy or a fighter. Just his daughter.", activation=0.1, emotional_valence="positive", tags=["intimacy"])],
     "expected_pattern": "parentification"},
    {"id": "tony_soprano", "name": "Tony Soprano", "source": "The Sopranos", "age": 45,
     "complaint": "My mother tried to have me killed. My uncle too. My kids think I sell patio furniture. Family, right?",
     "sample_lines": ["Those who want respect, give respect.", "A wrong decision is better than indecision.", "In this house, it's 1954."],
     "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="My mother Livia tried to have me killed — the woman who gave me life ordered my death", activation=0.9, emotional_valence="extreme"),
              SoulItem(id="f2", text="I lie to Meadow and AJ about everything — I'm protecting them from me, the thing they should fear most", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="My father was a mobster, his father was a mobster — I'm the family legacy I never chose", activation=0.2, emotional_valence="negative", tags=["legacy"]),
             SoulItem(id="d2", text="Meadow playing volleyball — she's going to be better than all of us. She already is.", activation=0.15, emotional_valence="positive", tags=["hope"]),
             SoulItem(id="d3", text="The ducks in my pool — when they left I had my first panic attack. Family leaving is my trigger.", activation=0.1, emotional_valence="negative", tags=["loss"])],
     "expected_pattern": "legacy_weight"},
    {"id": "vader_luke", "name": "Darth Vader", "source": "Star Wars", "age": 45,
     "complaint": "I cut off my son's hand. Then I asked him to join me. This is what fatherhood looks like in my family.",
     "sample_lines": ["I am your father.", "You don't know the power of the dark side.", "It is too late for me, son."],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="I am your father — the most terrifying revelation a son can hear. I am what he fears most.", activation=0.9, emotional_valence="extreme"),
              SoulItem(id="f2", text="I want Luke to join me — not to rule the galaxy, but because I'm too broken to come back to him", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="I was Anakin — a boy who loved too much. I lost Padme and became this machine.", activation=0.2, emotional_valence="negative", tags=["origin"]),
             SoulItem(id="d2", text="Luke sees good in me — after everything, my son believes I can be saved. That faith is unbearable.", activation=0.15, emotional_valence="positive", tags=["faith"]),
             SoulItem(id="d3", text="I threw the Emperor into the pit — for Luke. In the end the father in me was stronger than the Sith.", activation=0.1, emotional_valence="positive", tags=["redemption"])],
     "expected_pattern": "loyalty_bind"},
    {"id": "cao_cao_pi", "name": "曹操", "source": "三国演义", "age": 60,
     "complaint": "曹丕和曹植斗得你死我活。我的继承人选择就是他们的死刑判决书。",
     "sample_lines": ["宁教我负天下人", "老骥伏枥志在千里", "对酒当歌人生几何"],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="曹丕有政治手腕曹植有文学天才 — 选一个就是判另一个死刑", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="我用权术治天下但管不了两个儿子 — 家是我唯一输的战场", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="我也是从别人的废墟上建立的 — 我知道继承权的残酷因为我就是靠它上来的", activation=0.2, emotional_valence="negative", tags=["mirror"]),
             SoulItem(id="d2", text="曹植的诗 — '煮豆燃豆萁'。他用文字控诉兄弟相残。他是对的。", activation=0.15, emotional_valence="positive", tags=["truth"]),
             SoulItem(id="d3", text="对酒当歌 — 写诗的时候我不是权臣不是父亲，只是一个怕死的人", activation=0.1, emotional_valence="positive", tags=["human"])],
     "expected_pattern": "legacy_weight"},
    {"id": "tywin_tyrion", "name": "Tywin Lannister", "source": "Game of Thrones", "age": 60,
     "complaint": "My son is a dwarf and a disgrace. But he's the smartest one. I hate that most.",
     "sample_lines": ["A Lannister always pays his debts.", "Any man who must say 'I am the king' is no true king.", "You are my son."],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "masked"},
     "focus": [SoulItem(id="f1", text="Tyrion killed his mother being born — I can never forgive his body for what it cost me", activation=0.9, emotional_valence="extreme"),
              SoulItem(id="f2", text="He's the most like me — clever, strategic, ruthless when needed. I hate seeing myself in him.", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Joanna died and I couldn't save her — Tyrion is the living reminder of the only person I loved", activation=0.2, emotional_valence="negative", tags=["grief"]),
             SoulItem(id="d2", text="When Tyrion managed King's Landing — he did it better than anyone. I noticed.", activation=0.15, emotional_valence="positive", tags=["pride"]),
             SoulItem(id="d3", text="Legacy — the Lannister name must survive. Even through a son I can't look at.", activation=0.1, emotional_valence="negative", tags=["duty"])],
     "expected_pattern": "expectation_gap"},
    {"id": "willy_biff", "name": "Willy Loman", "source": "Death of a Salesman", "age": 63,
     "complaint": "Biff was going to be somebody. He had scholarships. Now he's a bum. Where did I go wrong?",
     "sample_lines": ["Attention must be paid.", "He's liked, but he's not well liked.", "A salesman has got to dream, boy."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "performative"},
     "focus": [SoulItem(id="f1", text="Biff was the golden boy — football star, scholarships, the American dream. Now he steals and drifts.", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="He caught me with that woman — one moment destroyed everything. His hero turned to dust.", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="I'm a failed salesman who pretended to be successful — Biff saw through me. That's why he can't pretend.", activation=0.2, emotional_valence="negative", tags=["mirror"]),
             SoulItem(id="d2", text="Biff said 'I just want you to know who I am, Pop' — he was asking me to see him. I couldn't.", activation=0.15, emotional_valence="positive", tags=["truth"]),
             SoulItem(id="d3", text="The garden — when I plant things and they grow, I feel real. More real than selling.", activation=0.1, emotional_valence="positive", tags=["authentic"])],
     "expected_pattern": "expectation_gap"},
    {"id": "fugui_jiazhen", "name": "福贵", "source": "活着", "age": 70,
     "complaint": "家珍跟了我一辈子。我赌光了家产，她没走。我不配她。",
     "sample_lines": ["人是为了活着本身而活着", "我认识的人一个一个死去", "少年去游荡，中年想掘藏，老年做和尚"],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "frozen"},
     "focus": [SoulItem(id="f1", text="我赌光了祖产 — 家珍拿着包袱回来的时候我知道我不配她", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="有庆凤霞一个一个走了 — 我们用沉默承受着只有夫妻才懂的痛", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="家珍的软骨病 — 她的身体替我受了罪。我的赌债她的身体在还。", activation=0.2, emotional_valence="negative", tags=["guilt"]),
             SoulItem(id="d2", text="她背着有庆走路的样子 — 那个画面是我这辈子最温暖的东西", activation=0.15, emotional_valence="positive", tags=["warmth"]),
             SoulItem(id="d3", text="活着 — 就是我和她的全部故事。不是为什么。就是在一起。", activation=0.1, emotional_valence="positive", tags=["endurance"])],
     "expected_pattern": "loyalty_bind"},
]

def run_one(char: dict) -> dict:
    se = SessionEngine(api_key=API_KEY, base_url="https://openrouter.ai/api", model="anthropic/claude-sonnet-4")
    sim = PatientSimulator(api_key=API_KEY)
    engine = FamilyEngine(se, sim)
    profile = PatientProfile(character_id=char["id"], character_name=char["name"], source=f"{char['name']} — {char['source']}",
        persistent_intentions=[{"text": char["complaint"], "layer": "conscious"}, {"text": f"I am {char['age']} years old", "layer": "conscious"}],
        emotional_state=f"Family conflict. Age: {char['age']}. From: {char['source']}", sample_lines=char.get("sample_lines", []), signals=char["signals"],
        soul_context=f"{char['name']} from {char['source']}, age {char['age']}.\nFamily complaint: \"{char['complaint']}\"\nExpected pattern: {char['expected_pattern']}")
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
    print("=" * 60); print("FAMILY MEDIATOR TRIAL"); print("=" * 60)
    t0 = time.time(); results = []
    for char in CHARACTERS:
        print(f"\n{'─'*60}\nMEDIATING: {char['name']} ({char['source']})\nISSUE: \"{char['complaint']}\"\n{'─'*60}")
        r = run_one(char); results.append(r)
        icon = "OK" if r["success"] else "FAIL"
        print(f"[{icon}] R={r['final_resistance']:.1f} insights={r['insights']} accepted={r['verbal_accepted']}")
        for d in r["dialogue"]: print(f"  T{d['turn']}: R={d['resistance']:.1f} {'*INSIGHT*' if d['insight'] else ''}"); print(f"    Mediator: {d['coach'][:100]}"); print(f"    Client: {d['client'][:100]}")
    total = time.time() - t0; wins = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}\nRESULTS: {wins}/{len(results)} helped ({wins/len(results)*100:.0f}%)\nTime: {total:.0f}s\n{'='*60}")
    for r in results: print(f"  [{'OK' if r['success'] else 'FAIL'}] {r['name']:20s} patterns={r['patterns_detected']} R={r['final_resistance']:.1f}")
    Path("/Users/michael/expert-engine/training_log/experiments/family_mediator_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__": main()
