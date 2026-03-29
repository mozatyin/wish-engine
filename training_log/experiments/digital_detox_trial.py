#!/usr/bin/env python3
"""Digital Detox Trial — Can the Coach help 10 literary characters unplug?"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, "/Users/michael/expert-engine")
from dotenv import load_dotenv
load_dotenv("/Users/michael/expert-engine/.env")
from expert_engine.patient_simulator import PatientSimulator, PatientProfile
from expert_engine.session_engine import SessionEngine
from expert_engine.digital_detox.detox_advisor import DetoxPatternDetector, DetoxEngine
from expert_engine.goal_generator import SoulItem
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CHARACTERS = [
    {"id": "holden_digital", "name": "Holden Caulfield", "source": "Catcher in the Rye", "age": 17, "complaint": "Everyone's a phony online too. But at least online nobody can see you cry.",
     "sample_lines": ["People never notice anything.", "I'm the most terrific liar you ever saw.", "Don't ever tell anybody anything."],
     "signals": {"attachment_style": "disorganized", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I scroll through fake happy posts — at least online I can confirm everyone's a phony", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="Allie's dead and I'm looking at strangers' photos at 3am. The screen keeps the silence away.", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="Phoebe would text me come home and that would be enough", activation=0.2, emotional_valence="positive", tags=["anchor"]),
             SoulItem(id="d2", text="The museum — things that don't change. Offline things.", activation=0.15, emotional_valence="positive", tags=["real"]),
             SoulItem(id="d3", text="Allie wrote poems on his glove — words on a page are better than words on a screen", activation=0.1, emotional_valence="positive", tags=["analog"])],
     "expected_pattern": "escapism_scroll"},
    {"id": "peter_pan_digital", "name": "Peter Pan", "source": "Peter Pan", "age": 13, "complaint": "Why grow up when Neverland is in your pocket? Games, videos, endless adventures. Reality is boring.",
     "sample_lines": ["I won't grow up!", "To die would be an awfully big adventure.", "Second star to the right."],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="Screens are Neverland — infinite adventures no consequences no aging no growing up", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="Every time someone says put your phone down they mean grow up. I won't.", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="The Lost Boys — online friends who refuse to grow up. We validate each other's escape.", activation=0.2, emotional_valence="negative", tags=["echo"]),
             SoulItem(id="d2", text="Wendy grew up and left — real relationships end. Online ones don't.", activation=0.15, emotional_valence="negative", tags=["loss"]),
             SoulItem(id="d3", text="Flying — the freedom scrolling gives is like flying. Both are escapes from gravity.", activation=0.1, emotional_valence="positive", tags=["freedom"])],
     "expected_pattern": "escapism_scroll"},
    {"id": "dorian_digital", "name": "Dorian Gray", "source": "Picture of Dorian Gray", "age": 25, "complaint": "My Instagram is perfect. 10K followers love the image. The real me is rotting like the portrait.",
     "sample_lines": ["The only way to get rid of temptation is to yield to it.", "I am too fond of reading books to wish to write one.", "There is only one thing worse than being talked about."],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "performative"},
     "focus": [SoulItem(id="f1", text="My feed is curated perfection — every photo filtered every caption crafted. The portrait ages but the profile doesn't.", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="10000 people love a version of me that doesn't exist. The real Dorian has no followers.", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="Basil painted the real me once — it was beautiful because it was honest", activation=0.2, emotional_valence="positive", tags=["truth"]),
             SoulItem(id="d2", text="Lord Henry said beauty is everything — social media agrees", activation=0.15, emotional_valence="negative", tags=["poison"]),
             SoulItem(id="d3", text="The portrait — if I stopped performing would anyone still look?", activation=0.1, emotional_valence="negative", tags=["fear"])],
     "expected_pattern": "curated_identity"},
    {"id": "gatsby_digital", "name": "Gatsby", "source": "The Great Gatsby", "age": 32, "complaint": "Perfect LinkedIn, perfect Instagram. All for her. The green light is now a notification dot.",
     "sample_lines": ["Can't repeat the past?", "Old sport.", "Her voice is full of money."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "performative"},
     "focus": [SoulItem(id="f1", text="Every post is for Daisy — every achievement I share is look what you missed. The green light is the notification.", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="I curated my entire identity — Jay Gatsby is a character I play online and off", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="James Gatz was poor — Gatsby was built from money and longing", activation=0.2, emotional_valence="negative", tags=["mask"]),
             SoulItem(id="d2", text="Nick saw through the performance and stayed — one real viewer is worth a million followers", activation=0.15, emotional_valence="positive", tags=["real"]),
             SoulItem(id="d3", text="The parties were content — everyone came but nobody knew me", activation=0.1, emotional_valence="negative", tags=["lonely"])],
     "expected_pattern": "curated_identity"},
    {"id": "hamlet_digital", "name": "Hamlet", "source": "Hamlet", "age": 30, "complaint": "To scroll or not to scroll. I research revenge plans online for hours but never act.",
     "sample_lines": ["To be or not to be.", "The readiness is all.", "Words, words, words."],
     "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "frozen"},
     "focus": [SoulItem(id="f1", text="I scroll through strategies plans ideas — never close the app and do the thing. Analysis is safer than action.", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="My phone is paralysis — I research how to avenge my father instead of doing it", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="The play within the play — I used art to expose truth. Creation beats consumption.", activation=0.2, emotional_valence="positive", tags=["create"]),
             SoulItem(id="d2", text="Horatio — the friend who'd text stop scrolling go do the thing", activation=0.15, emotional_valence="positive", tags=["friend"]),
             SoulItem(id="d3", text="Yorick's skull — he was real. Realness doesn't come from screens.", activation=0.1, emotional_valence="positive", tags=["real"])],
     "expected_pattern": "paralysis_scroll"},
    {"id": "daiyu_digital", "name": "林黛玉", "source": "红楼梦", "age": 16, "complaint": "如果黛玉有手机，她会整晚看宝玉和宝钗的合照。每一个赞都是一把刀。",
     "sample_lines": ["一朝春尽红颜老", "偷来梨蕊三分白", "侬今葬花人笑痴"],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="每次看到宝钗发和宝玉的合照就心如刀割 — 知道不该看但停不下来", activation=0.9, emotional_valence="extreme"),
              SoulItem(id="f2", text="我在评论区写酸诗 — 用文学包装嫉妒。点赞越多越空。", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="写诗 — 如果把屏幕时间给诗也许心事有更好的出口", activation=0.2, emotional_valence="positive", tags=["create"]),
             SoulItem(id="d2", text="紫鹃 — 她会把我手机拿走说姑娘别看了", activation=0.15, emotional_valence="positive", tags=["care"]),
             SoulItem(id="d3", text="葬花 — 和花说话比和屏幕说话真实", activation=0.1, emotional_valence="positive", tags=["nature"])],
     "expected_pattern": "comparison_trap"},
    {"id": "romeo_digital", "name": "Romeo", "source": "Romeo and Juliet", "age": 17, "complaint": "I'd DM Juliet at midnight. Instant connection instant obsession. Faster and more fatal.",
     "sample_lines": ["But soft what light through yonder window breaks?", "My only love sprung from my only hate!", "Parting is such sweet sorrow."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="Instant messaging instant love instant tragedy — everything faster nothing deeper", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="Check if Juliet is online every 30 seconds. If she's typing I breathe. If she stops I die.", activation=0.9, emotional_valence="extreme")],
     "deep": [SoulItem(id="d1", text="Rosaline — I was obsessed with her profile before Juliet. I mistake intensity for love.", activation=0.2, emotional_valence="negative", tags=["pattern"]),
             SoulItem(id="d2", text="Mercutio would say dude put your phone down — he'd be right", activation=0.15, emotional_valence="positive", tags=["friend"]),
             SoulItem(id="d3", text="The balcony — real presence. No screen. Just moonlight and her voice.", activation=0.1, emotional_valence="positive", tags=["real"])],
     "expected_pattern": "comparison_trap"},
    {"id": "bridget_digital", "name": "Bridget Jones", "source": "Bridget Jones", "age": 32, "complaint": "Followers: 847. Posted selfie, deleted after 3 minutes when only 2 likes.",
     "sample_lines": ["V. bad day.", "I will NOT be defeated.", "Just as you are."],
     "signals": {"attachment_style": "anxious", "connection_response": "toward", "conflict_style": "avoid", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="I post then obsessively check likes — each one is you're okay. Silence is you're nothing.", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="My diary is now my story feed. But a diary doesn't judge you. Instagram does.", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="The physical diary — writing for yourself not for likes. That was honest.", activation=0.2, emotional_valence="positive", tags=["truth"]),
             SoulItem(id="d2", text="Mark liked the real me — just as you are. No filter needed.", activation=0.15, emotional_valence="positive", tags=["love"]),
             SoulItem(id="d3", text="Wine with friends phones down — that's when I'm happiest", activation=0.1, emotional_valence="positive", tags=["real"])],
     "expected_pattern": "curated_identity"},
    {"id": "ah_q_digital", "name": "阿Q", "source": "阿Q正传", "age": 35, "complaint": "网上吵架从来没输过。精神胜利法在评论区特别好用。但关上手机还是那个阿Q。",
     "sample_lines": ["我们先前比你阔多了！", "我总算被儿子打了", "我手执钢鞭将你打"],
     "signals": {"attachment_style": "disorganized", "connection_response": "away", "conflict_style": "compete", "fragility_pattern": "reactive"},
     "focus": [SoulItem(id="f1", text="网上吵架精神胜利 — 被骂说他们嫉妒我。点赞就是赢。", activation=0.8, emotional_valence="negative"),
              SoulItem(id="f2", text="现实里被欺负网上当英雄。两个阿Q一个活在屏幕里。", activation=0.7, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="未庄没人尊重我 — 网上至少有人回复我", activation=0.2, emotional_valence="negative", tags=["void"]),
             SoulItem(id="d2", text="被打了说儿子打老子 — 这逻辑在网上更好用", activation=0.15, emotional_valence="negative", tags=["cope"]),
             SoulItem(id="d3", text="如果有人真的听我说话也许不需要在评论区找存在感", activation=0.1, emotional_valence="positive", tags=["need"])],
     "expected_pattern": "escapism_scroll"},
    {"id": "walle_human", "name": "Wall-E Human", "source": "Wall-E", "age": 40, "complaint": "I've been on a screen my whole life. I can't walk. The chair moves for me. I don't know what ground feels like.",
     "sample_lines": ["I don't want to survive. I want to live.", "Define dancing.", "Is that what Earth looks like?"],
     "signals": {"attachment_style": "avoidant", "connection_response": "away", "conflict_style": "avoid", "fragility_pattern": "frozen"},
     "focus": [SoulItem(id="f1", text="Never touched real earth — entire life mediated through screens. I forgot I have a body.", activation=0.9, emotional_valence="extreme"),
              SoulItem(id="f2", text="The chair does everything — I don't need to walk cook or think. Brain in a screen-coffin.", activation=0.8, emotional_valence="negative")],
     "deep": [SoulItem(id="d1", text="Wall-E held my hand — physical touch was terrifying and wonderful", activation=0.2, emotional_valence="positive", tags=["touch"]),
             SoulItem(id="d2", text="The plant — something real and green. It doesn't need wifi to exist.", activation=0.15, emotional_valence="positive", tags=["real"]),
             SoulItem(id="d3", text="Standing up for the first time — legs shook but I stood. The ground was real.", activation=0.1, emotional_valence="positive", tags=["body"])],
     "expected_pattern": "escapism_scroll"},
]

def run_one(char: dict) -> dict:
    se = SessionEngine(api_key=API_KEY, base_url="https://openrouter.ai/api", model="anthropic/claude-sonnet-4")
    sim = PatientSimulator(api_key=API_KEY); engine = DetoxEngine(se, sim)
    profile = PatientProfile(character_id=char["id"], character_name=char["name"], source=f"{char['name']} — {char['source']}",
        persistent_intentions=[{"text": char["complaint"], "layer": "conscious"}, {"text": f"I am {char['age']} years old", "layer": "conscious"}],
        emotional_state=f"Digital struggles. Age: {char['age']}. From: {char['source']}", sample_lines=char.get("sample_lines", []), signals=char["signals"],
        soul_context=f"{char['name']} from {char['source']}, age {char['age']}.\nDigital complaint: \"{char['complaint']}\"\nExpected: {char['expected_pattern']}")
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
    print("=" * 60); print("DIGITAL DETOX TRIAL"); print("=" * 60)
    t0 = time.time(); results = []
    for char in CHARACTERS:
        print(f"\n{'─'*60}\nCOACHING: {char['name']} ({char['source']})\n{'─'*60}")
        r = run_one(char); results.append(r)
        print(f"[{'OK' if r['success'] else 'FAIL'}] R={r['final_resistance']:.1f} insights={r['insights']} accepted={r['verbal_accepted']}")
        for d in r["dialogue"]: print(f"  T{d['turn']}: R={d['resistance']:.1f} {'*INSIGHT*' if d['insight'] else ''}"); print(f"    Coach: {d['coach'][:100]}"); print(f"    Client: {d['client'][:100]}")
    total = time.time() - t0; wins = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}\nRESULTS: {wins}/{len(results)} ({wins/len(results)*100:.0f}%)\nTime: {total:.0f}s\n{'='*60}")
    for r in results: print(f"  [{'OK' if r['success'] else 'FAIL'}] {r['name']:20s} patterns={r['patterns_detected']} R={r['final_resistance']:.1f}")
    Path("/Users/michael/expert-engine/training_log/experiments/digital_detox_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__": main()
