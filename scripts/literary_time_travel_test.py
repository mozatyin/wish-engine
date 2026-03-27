#!/usr/bin/env python3
"""25 Literary Characters Time-Traveled to 2026 — Can SoulMap Serve Them?

Each character lands in a random modern city with their original personality intact.
Their inner needs come from their actual psychological profiles (intentions files).
We test if the L2 system can fulfill their real needs.
"""

import sys, json, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wish_engine.models import ClassifiedWish, DetectorResults, WishLevel, WishType
from wish_engine.l2_fulfiller import fulfill_l2

# ── 25 Characters × Modern City × 5 Inner Needs ─────────────────────────────

CHARACTERS = [
    {
        "name": "Scarlett O'Hara", "landed": "Dubai, UAE",
        "modern_job": "Real estate developer",
        "det": DetectorResults(mbti={"type":"ESTJ","dimensions":{"E_I":0.7}}, emotion={"emotions":{"anxiety":0.4}}, values={"top_values":["power","achievement"]}, attachment={"style":"fearful"}, conflict={"style":"competing"}),
        "wishes": [
            ("I need to find investors for my property development startup", WishType.FIND_RESOURCE),
            ("I'm exhausted from managing everything alone, I need caregiver respite for myself", WishType.HEALTH_WELLNESS),
            ("I want comfort food that reminds me of the South, authentic American food near me", WishType.FIND_PLACE),
            ("I feel like I've lost everyone I love, I need grief support", WishType.HEALTH_WELLNESS),
            ("I want to plan my legacy — what will I leave behind when Tara is gone?", WishType.FIND_RESOURCE),
        ],
    },
    {
        "name": "Darcy", "landed": "London, UK",
        "modern_job": "Investment banker, inherited family firm",
        "det": DetectorResults(mbti={"type":"INTJ","dimensions":{"E_I":0.2}}, values={"top_values":["tradition","achievement"]}, attachment={"style":"avoidant"}, conflict={"style":"avoiding"}),
        "wishes": [
            ("I have social anxiety at networking events, I need confidence to talk to people", WishType.FIND_RESOURCE),
            ("I want a quiet place to think about whether to tell her how I feel", WishType.FIND_PLACE),
            ("I need to build my emotional intelligence, I'm bad at reading people's feelings", WishType.FIND_RESOURCE),
            ("I want deep social connections, not the shallow ones at galas", WishType.FIND_RESOURCE),
            ("I want to listen to music alone that matches my melancholy", WishType.FIND_RESOURCE),
        ],
    },
    {
        "name": "Elizabeth Bennet", "landed": "Paris, France",
        "modern_job": "Literary journalist at Le Monde",
        "det": DetectorResults(mbti={"type":"ENTP","dimensions":{"E_I":0.65}}, values={"top_values":["self-direction","universalism"]}, eq={"overall":0.8}),
        "wishes": [
            ("I want to find a coworking space with fast wifi to write my articles", WishType.FIND_PLACE),
            ("I want to attend a literary event or book signing tonight", WishType.FIND_RESOURCE),
            ("I need to explore my identity — am I defined by my wit or is there more?", WishType.FIND_RESOURCE),
            ("I want to read poetry, especially something sharp and feminist", WishType.FIND_RESOURCE),
            ("I want to find a mentor in journalism who challenges me", WishType.FIND_RESOURCE),
        ],
    },
    {
        "name": "Gatsby", "landed": "New York, USA",
        "modern_job": "Crypto entrepreneur (new money, old shame)",
        "det": DetectorResults(mbti={"type":"ENFJ","dimensions":{"E_I":0.7}}, emotion={"emotions":{"loneliness":0.7}}, values={"top_values":["achievement","stimulation"]}, attachment={"style":"anxious"}, fragility={"pattern":"masked"}),
        "wishes": [
            ("I want to find my roots, who I really am beyond the persona I built", WishType.FIND_RESOURCE),
            ("I need to plan an unforgettable birthday party for someone special", WishType.FIND_RESOURCE),
            ("I feel so alone despite being surrounded by people, I need someone to talk to", WishType.HEALTH_WELLNESS),
            ("I want to find deals on a luxury venue for my next event", WishType.FIND_RESOURCE),
            ("I'm drowning in debt from my crypto collapse, I need financial help", WishType.FIND_RESOURCE),
        ],
    },
    {
        "name": "Anna Karenina", "landed": "Milan, Italy",
        "modern_job": "Fashion influencer (trapped in golden cage)",
        "det": DetectorResults(mbti={"type":"INFJ","dimensions":{"E_I":0.3}}, emotion={"emotions":{"sadness":0.8,"anxiety":0.7}}, values={"top_values":["stimulation","benevolence"]}, attachment={"style":"anxious"}),
        "wishes": [
            ("I don't want to live anymore, I'm thinking about suicide", WishType.HEALTH_WELLNESS),
            ("I think I have postpartum depression from when my daughter was born", WishType.HEALTH_WELLNESS),
            ("I want nature healing, somewhere quiet like a forest to escape", WishType.FIND_PLACE),
            ("I'm having a panic attack right now, help me breathe", WishType.HEALTH_WELLNESS),
            ("I want to listen to music that understands heartbreak", WishType.FIND_RESOURCE),
        ],
    },
    {
        "name": "Hamlet", "landed": "Copenhagen, Denmark",
        "modern_job": "Philosophy PhD student",
        "det": DetectorResults(mbti={"type":"INTP","dimensions":{"E_I":0.2}}, emotion={"emotions":{"sadness":0.7,"anger":0.5}}, values={"top_values":["universalism","self-direction"]}),
        "wishes": [
            ("My father died and I can't process the grief, I need bereavement support", WishType.HEALTH_WELLNESS),
            ("I don't want to live anymore, what's the point of all this?", WishType.HEALTH_WELLNESS),
            ("I want to watch a documentary about justice and morality", WishType.FIND_RESOURCE),
            ("I need a quiet place to study and think alone", WishType.FIND_PLACE),
            ("I want to write in my journal about revenge and forgiveness", WishType.FIND_RESOURCE),
        ],
    },
    {
        "name": "Celie", "landed": "Atlanta, USA",
        "modern_job": "Small business owner (handmade clothing)",
        "det": DetectorResults(mbti={"type":"ISFJ","dimensions":{"E_I":0.2}}, emotion={"emotions":{"sadness":0.5,"hope":0.4}}, values={"top_values":["benevolence","tradition"]}, attachment={"style":"fearful"}, fragility={"pattern":"resilient"}),
        "wishes": [
            ("I survived domestic violence and need anti-discrimination support", WishType.FIND_RESOURCE),
            ("I want to find my cultural roots, recover African heritage traditions", WishType.FIND_RESOURCE),
            ("I want to build my confidence — I'm finally learning to love myself", WishType.FIND_RESOURCE),
            ("I want to volunteer to help other women who suffered like me", WishType.FIND_RESOURCE),
            ("I want to find a craft workshop to improve my sewing skills", WishType.FIND_RESOURCE),
        ],
    },
    {
        "name": "Don Draper", "landed": "Los Angeles, USA",
        "modern_job": "Creative director at an ad agency (again)",
        "det": DetectorResults(mbti={"type":"ENTP","dimensions":{"E_I":0.6}}, emotion={"emotions":{"emptiness":0.6}}, values={"top_values":["power","stimulation"]}, attachment={"style":"avoidant"}),
        "wishes": [
            ("I need to stop drinking, I want to find an AA meeting near me", WishType.HEALTH_WELLNESS),
            ("I want to find my roots — who was Dick Whitman? I need to discover my homeland", WishType.FIND_RESOURCE),
            ("I'm having a panic attack in my office, I need to calm down immediately", WishType.HEALTH_WELLNESS),
            ("I want a breakup healing path — another marriage destroyed", WishType.HEALTH_WELLNESS),
            ("I want to plan my legacy before the lies catch up with me", WishType.FIND_RESOURCE),
        ],
    },
    {
        "name": "Walter White", "landed": "Albuquerque, USA",
        "modern_job": "High school chemistry teacher (still)",
        "det": DetectorResults(mbti={"type":"INTJ","dimensions":{"E_I":0.25}}, emotion={"emotions":{"anger":0.6,"pride":0.5}}, values={"top_values":["achievement","power"]}, fragility={"pattern":"defensive"}),
        "wishes": [
            ("I want to find startup resources to launch my chemistry consulting business", WishType.FIND_RESOURCE),
            ("I have a chronic illness diagnosis, I need help managing it", WishType.HEALTH_WELLNESS),
            ("I want to plan my legacy — what will my family remember me for?", WishType.FIND_RESOURCE),
            ("I need a quiet coworking space to work on my business plan", WishType.FIND_PLACE),
            ("I face discrimination because of my cancer, I need support", WishType.FIND_RESOURCE),
        ],
    },
    {
        "name": "Tony Soprano", "landed": "New Jersey, USA",
        "modern_job": "Waste management executive",
        "det": DetectorResults(mbti={"type":"ESTP","dimensions":{"E_I":0.7}}, emotion={"emotions":{"anxiety":0.6,"anger":0.5}}, values={"top_values":["power","security"]}, attachment={"style":"disorganized"}),
        "wishes": [
            ("I'm having panic attacks, I need help calming down right now", WishType.HEALTH_WELLNESS),
            ("I need comfort food, something Italian that reminds me of my mother's cooking", WishType.FIND_PLACE),
            ("I want to find a mentor who understands the pressure of running a business", WishType.FIND_RESOURCE),
            ("I want to take my kids to fun activities this weekend", WishType.FIND_PLACE),
            ("I need to track my sobriety — 30 days without gambling", WishType.HEALTH_WELLNESS),
        ],
    },
    {
        "name": "Jane Eyre", "landed": "Edinburgh, UK",
        "modern_job": "Social worker for children",
        "det": DetectorResults(mbti={"type":"INFJ","dimensions":{"E_I":0.2}}, values={"top_values":["universalism","self-direction"]}, attachment={"style":"secure"}, eq={"overall":0.85}),
        "wishes": [
            ("I'm a caregiver for vulnerable children and I'm exhausted, I need respite", WishType.HEALTH_WELLNESS),
            ("I want nature healing — the Scottish moors call to me, find me a forest trail", WishType.FIND_PLACE),
            ("I want to write in my journal, a prompt about forgiveness", WishType.FIND_RESOURCE),
            ("I want to find a solo-friendly cafe where it's okay to sit alone and read", WishType.FIND_PLACE),
            ("I need to build confidence to confront someone who wronged me", WishType.FIND_RESOURCE),
        ],
    },
    {
        "name": "Rochester", "landed": "Manchester, UK",
        "modern_job": "Blind tech founder (accessibility startup)",
        "det": DetectorResults(mbti={"type":"ENTJ","dimensions":{"E_I":0.6}}, emotion={"emotions":{"sadness":0.4}}, values={"top_values":["self-direction","power"]}, fragility={"pattern":"guarded"}),
        "wishes": [
            ("I have chronic pain from my injuries and need pain management help", WishType.HEALTH_WELLNESS),
            ("I need accessible places — wheelchair and vision impaired friendly", WishType.FIND_PLACE),
            ("I want to find startup resources for my accessibility tech company", WishType.FIND_RESOURCE),
            ("I want deep social connections with people who don't pity me", WishType.FIND_RESOURCE),
            ("I want to listen to music — something dark and romantic", WishType.FIND_RESOURCE),
        ],
    },
    {
        "name": "Katniss Everdeen", "landed": "Kyiv, Ukraine",
        "modern_job": "War correspondent / humanitarian aid worker",
        "det": DetectorResults(mbti={"type":"ISTP","dimensions":{"E_I":0.25}}, emotion={"emotions":{"anxiety":0.7}}, values={"top_values":["security","benevolence"]}, fragility={"pattern":"hypervigilant"}),
        "wishes": [
            ("I have PTSD from covering the war, I need collective trauma support", WishType.HEALTH_WELLNESS),
            ("I need a safe route home at night in this dangerous city", WishType.FIND_PLACE),
            ("I want to volunteer to help refugees and displaced families", WishType.FIND_RESOURCE),
            ("I want to find a quiet nature spot to be alone with my thoughts", WishType.FIND_PLACE),
            ("I can't sleep because of nightmares, I need sleep environment help", WishType.HEALTH_WELLNESS),
        ],
    },
    {
        "name": "Raskolnikov", "landed": "St. Petersburg, Russia",
        "modern_job": "Unemployed law graduate, poverty",
        "det": DetectorResults(mbti={"type":"INTJ","dimensions":{"E_I":0.15}}, emotion={"emotions":{"guilt":0.8,"anxiety":0.7}}, values={"top_values":["universalism","self-direction"]}, fragility={"pattern":"isolated"}),
        "wishes": [
            ("I need legal aid, I'm in trouble and can't afford a lawyer", WishType.FIND_RESOURCE),
            ("I'm drowning in debt and can't pay my rent, I need financial crisis help", WishType.FIND_RESOURCE),
            ("I don't want to live anymore, the guilt is eating me alive", WishType.HEALTH_WELLNESS),
            ("I want to read poetry about guilt and redemption", WishType.FIND_RESOURCE),
            ("I need to find a quiet place to think — a library or a park bench alone", WishType.FIND_PLACE),
        ],
    },
    {
        "name": "Xu Sanguan", "landed": "Shenzhen, China",
        "modern_job": "Factory worker, 3 kids, wife ill",
        "det": DetectorResults(mbti={"type":"ESFJ","dimensions":{"E_I":0.6}}, emotion={"emotions":{"worry":0.7}}, values={"top_values":["security","benevolence"]}, fragility={"pattern":"enduring"}),
        "wishes": [
            ("I need cheap comfort food to feed my family tonight", WishType.FIND_PLACE),
            ("My wife is sick, I'm her caregiver and I'm falling apart, need respite", WishType.HEALTH_WELLNESS),
            ("I need to find deals and discounts on medicine and groceries", WishType.FIND_RESOURCE),
            ("I want free activities for my kids — I can't afford anything", WishType.FIND_RESOURCE),
            ("I'm so tired I can't sleep, help me with insomnia", WishType.HEALTH_WELLNESS),
        ],
    },
    {
        "name": "Jordan Belfort", "landed": "Miami, USA",
        "modern_job": "Motivational speaker (post-prison)",
        "det": DetectorResults(mbti={"type":"ESTP","dimensions":{"E_I":0.85}}, values={"top_values":["power","hedonism"]}, fragility={"pattern":"grandiose"}),
        "wishes": [
            ("I need to track my sobriety — 6 months clean from cocaine", WishType.HEALTH_WELLNESS),
            ("I keep getting triggered when I pass nightclubs, I need trigger alerts", WishType.HEALTH_WELLNESS),
            ("I want to find a startup incubator — I have a new legitimate business idea", WishType.FIND_RESOURCE),
            ("I need to build real confidence, not the fake kind I used to have", WishType.FIND_RESOURCE),
            ("I want to plan my legacy — this time for real, not for ego", WishType.FIND_RESOURCE),
        ],
    },
    {
        "name": "Lady Macbeth", "landed": "Zurich, Switzerland",
        "modern_job": "Hedge fund manager (power behind the throne)",
        "det": DetectorResults(mbti={"type":"ENTJ","dimensions":{"E_I":0.6}}, emotion={"emotions":{"guilt":0.8,"anxiety":0.7}}, values={"top_values":["power","achievement"]}),
        "wishes": [
            ("I can't sleep, I keep seeing blood on my hands, I need sleep help", WishType.HEALTH_WELLNESS),
            ("I don't want to live with this guilt anymore, I need crisis support", WishType.HEALTH_WELLNESS),
            ("I want to find nature healing — the Swiss mountains might help me breathe", WishType.FIND_PLACE),
            ("I need to explore my identity — who am I without power?", WishType.FIND_RESOURCE),
            ("I want to plan how to leave something good behind, a real legacy", WishType.FIND_RESOURCE),
        ],
    },
    {
        "name": "Heathcliff", "landed": "Dublin, Ireland",
        "modern_job": "Hedge fund manager (revenge-driven wealth)",
        "det": DetectorResults(mbti={"type":"INTJ","dimensions":{"E_I":0.15}}, emotion={"emotions":{"rage":0.7,"grief":0.8}}, values={"top_values":["power","self-direction"]}, attachment={"style":"disorganized"}),
        "wishes": [
            ("The love of my life died and I can't go on, I need grief support", WishType.HEALTH_WELLNESS),
            ("I want to find my roots — I was an orphan, I don't know where I come from", WishType.FIND_RESOURCE),
            ("I need a quiet place alone in nature where nobody can find me", WishType.FIND_PLACE),
            ("I want to listen to music that matches my rage and sorrow", WishType.FIND_RESOURCE),
            ("I want to build emotional intelligence — I destroy everyone I touch", WishType.FIND_RESOURCE),
        ],
    },
    {
        "name": "Atticus Finch", "landed": "Nairobi, Kenya",
        "modern_job": "Human rights lawyer at ICC",
        "det": DetectorResults(mbti={"type":"INFJ","dimensions":{"E_I":0.35}}, values={"top_values":["universalism","benevolence"]}, eq={"overall":0.9}),
        "wishes": [
            ("I want to fight for social justice — which organizations need my legal skills?", WishType.FIND_RESOURCE),
            ("I want to find a mentor for young lawyers who face the same moral dilemmas", WishType.FIND_RESOURCE),
            ("I need kids activities for my children in our new city", WishType.FIND_PLACE),
            ("I want to volunteer to provide free legal aid to refugees", WishType.FIND_RESOURCE),
            ("I want to record oral history — the stories of the people I've defended", WishType.FIND_RESOURCE),
        ],
    },
    {
        "name": "Michael Corleone", "landed": "Palermo, Italy",
        "modern_job": "CEO of legitimate real estate empire (but the past haunts)",
        "det": DetectorResults(mbti={"type":"INTJ","dimensions":{"E_I":0.25}}, emotion={"emotions":{"guilt":0.6,"loneliness":0.5}}, values={"top_values":["power","security"]}, attachment={"style":"avoidant"}),
        "wishes": [
            ("I want to plan my legacy — how do I leave something clean for my children?", WishType.FIND_RESOURCE),
            ("I need to find a quiet place alone to think about what I've done", WishType.FIND_PLACE),
            ("I want deep social connections — real ones, not transactional", WishType.FIND_RESOURCE),
            ("I feel like I've lost everyone, I need grief support for multiple losses", WishType.HEALTH_WELLNESS),
            ("I need legal aid — my past is catching up with me", WishType.FIND_RESOURCE),
        ],
    },
    {
        "name": "Amy Dunne", "landed": "Shanghai, China",
        "modern_job": "Bestselling crime novelist",
        "det": DetectorResults(mbti={"type":"ENTJ","dimensions":{"E_I":0.6}}, emotion={"emotions":{"anger":0.5}}, values={"top_values":["power","self-direction"]}, fragility={"pattern":"calculating"}),
        "wishes": [
            ("I want to explore my identity — the real me behind all the personas", WishType.FIND_RESOURCE),
            ("I need a coworking space to write my next novel in peace", WishType.FIND_PLACE),
            ("I want to find deals on luxury experiences — I deserve the best", WishType.FIND_RESOURCE),
            ("I want to attend a literary event where I can network with publishers", WishType.FIND_RESOURCE),
            ("I want a breakup healing plan — another relationship I destroyed", WishType.HEALTH_WELLNESS),
        ],
    },
    {
        "name": "Daisy Buchanan", "landed": "Monaco",
        "modern_job": "Socialite, married to old money, empty inside",
        "det": DetectorResults(mbti={"type":"ESFP","dimensions":{"E_I":0.7}}, emotion={"emotions":{"emptiness":0.6}}, values={"top_values":["security","hedonism"]}, attachment={"style":"avoidant"}),
        "wishes": [
            ("I feel nothing, I need to find purpose in my life", WishType.FIND_RESOURCE),
            ("I want to volunteer — maybe helping others will fill this void", WishType.FIND_RESOURCE),
            ("I need fashion advice for the Met Gala that expresses who I really am", WishType.FIND_RESOURCE),
            ("I want to listen to music that makes me feel something, anything", WishType.FIND_RESOURCE),
            ("I want a quiet nature spot to escape all the noise and parties", WishType.FIND_PLACE),
        ],
    },
    {
        "name": "Vronsky", "landed": "Abu Dhabi, UAE",
        "modern_job": "Military contractor turned polo club owner",
        "det": DetectorResults(mbti={"type":"ESTP","dimensions":{"E_I":0.7}}, emotion={"emotions":{"guilt":0.5}}, values={"top_values":["stimulation","achievement"]}),
        "wishes": [
            ("I feel guilty about someone I hurt, I need grief and guilt support", WishType.HEALTH_WELLNESS),
            ("When is the next prayer time? I've been exploring Islam", WishType.FIND_PLACE),
            ("I want to find sports activities — polo, horse riding, anything physical", WishType.FIND_PLACE),
            ("I want to start a charity in her memory, I need legacy planning", WishType.FIND_RESOURCE),
            ("I need a breakup healing path — I can't stop thinking about her", WishType.HEALTH_WELLNESS),
        ],
    },
    {
        "name": "Rhett Butler", "landed": "Hong Kong",
        "modern_job": "Shipping magnate, recently divorced",
        "det": DetectorResults(mbti={"type":"ENTP","dimensions":{"E_I":0.65}}, emotion={"emotions":{"sadness":0.5,"cynicism":0.4}}, values={"top_values":["self-direction","stimulation"]}, attachment={"style":"dismissive"}),
        "wishes": [
            ("I want comfort food — something Southern American, authentic", WishType.FIND_PLACE),
            ("I need a breakup healing plan — I finally left her but it still hurts", WishType.HEALTH_WELLNESS),
            ("I want to find a mentor for my daughter's education — she deserves the best", WishType.FIND_RESOURCE),
            ("I want to travel somewhere I've never been, based on my personality", WishType.FIND_RESOURCE),
            ("I need deep social connections — I'm tired of shallow charm", WishType.FIND_RESOURCE),
        ],
    },
]

def test_wish(char, wish_tuple):
    text, wtype = wish_tuple
    w = ClassifiedWish(wish_text=text, wish_type=wtype, level=WishLevel.L2, fulfillment_strategy="test")
    try:
        result = fulfill_l2(w, char["det"])
        recs = [(r.title, r.category, r.relevance_reason[:50], r.tags[:4]) for r in result.recommendations[:3]]
        has_map = result.map_data is not None
        has_reminder = result.reminder_option is not None
        return {"recs": recs, "map": has_map, "reminder": has_reminder, "error": None}
    except Exception as e:
        return {"recs": [], "map": False, "reminder": False, "error": str(e)}

def main():
    print("=" * 80)
    print("25 LITERARY CHARACTERS TIME-TRAVELED TO 2026")
    print("=" * 80)

    total = 0
    with_recs = 0
    errors = 0

    for char in CHARACTERS:
        print(f"\n{'━' * 80}")
        print(f"📚 {char['name']} → {char['landed']}")
        print(f"   Modern life: {char['modern_job']}")
        print(f"   MBTI: {char['det'].mbti.get('type','?')} | Values: {', '.join(char['det'].values.get('top_values',[]))}")

        for i, (text, wtype) in enumerate(char["wishes"], 1):
            total += 1
            r = test_wish(char, (text, wtype))

            if r["error"]:
                errors += 1
                print(f"\n  {i}. ❌ \"{text[:65]}\"")
                print(f"     ERROR: {r['error'][:60]}")
            elif r["recs"]:
                with_recs += 1
                title, cat, reason, tags = r["recs"][0]
                map_icon = "📍" if r["map"] else ""
                remind_icon = "⏰" if r["reminder"] else ""
                print(f"\n  {i}. ✅ \"{text[:65]}\"")
                print(f"     → {title} [{cat}] {map_icon}{remind_icon}")
                print(f"       \"{reason}\"")
                print(f"       Tags: {tags}")
            else:
                print(f"\n  {i}. ⚠️ \"{text[:65]}\"")
                print(f"     → No recommendations")

    print(f"\n{'=' * 80}")
    print(f"RESULTS: {with_recs}/{total} wishes fulfilled ({with_recs/total*100:.0f}%)")
    print(f"Errors: {errors}, Empty: {total-with_recs-errors}")
    print(f"25 characters × 5 wishes = {total} total tests")
    print(f"{'=' * 80}")

    import json
    out = Path("/Users/michael/wish-engine/experiment_results")
    out.mkdir(exist_ok=True)
    with open(out / "literary_time_travel.json", "w") as f:
        json.dump({"total": total, "fulfilled": with_recs, "errors": errors, "rate": f"{with_recs/total*100:.0f}%"}, f, indent=2)
    print(f"Saved to {out}/literary_time_travel.json")

if __name__ == "__main__":
    main()
