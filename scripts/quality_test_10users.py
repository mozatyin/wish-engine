#!/usr/bin/env python3
"""10 New Users × 5 Wishes Each — Quality Assessment (not just routing, but HOW GOOD)."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wish_engine.models import ClassifiedWish, DetectorResults, WishLevel, WishType
from wish_engine.l2_fulfiller import fulfill_l2

USERS = [
    {
        "name": "Sofia", "age": 23, "city": "Buenos Aires, Argentina", "mbti": "ENFJ",
        "background": "Psychology student, passionate about tango, broke, recently lost her dog, vegan",
        "det": DetectorResults(
            mbti={"type": "ENFJ", "dimensions": {"E_I": 0.75}},
            emotion={"emotions": {"sadness": 0.6, "loneliness": 0.4}},
            values={"top_values": ["benevolence", "universalism"]},
            attachment={"style": "secure"},
        ),
        "wishes": [
            {"text": "My dog Luna died last week and I can't stop crying", "type": WishType.HEALTH_WELLNESS},
            {"text": "I want to volunteer at an animal shelter to heal", "type": WishType.FIND_RESOURCE},
            {"text": "I need cheap vegan restaurants near my university", "type": WishType.FIND_PLACE},
            {"text": "I want to dance tango tonight to feel alive again", "type": WishType.FIND_PLACE},
            {"text": "I want to read poetry that understands loss", "type": WishType.FIND_RESOURCE},
        ],
    },
    {
        "name": "Hiroshi", "age": 30, "city": "Osaka, Japan", "mbti": "ISTP",
        "background": "Salaryman, 60hr/week, secretly wants to open a ramen shop, divorced, lives alone",
        "det": DetectorResults(
            mbti={"type": "ISTP", "dimensions": {"E_I": 0.25}},
            emotion={"emotions": {"fatigue": 0.7, "anxiety": 0.4}},
            values={"top_values": ["self-direction", "achievement"]},
            fragility={"pattern": "masked"},
        ),
        "wishes": [
            {"text": "I'm burned out from work, I need to find purpose and meaning in my life", "type": WishType.FIND_RESOURCE},
            {"text": "I want to learn cooking professionally, maybe a culinary course", "type": WishType.LEARN_SKILL},
            {"text": "I need a quiet place to think about my future alone", "type": WishType.FIND_PLACE},
            {"text": "I want to find other people who dream of starting their own restaurant", "type": WishType.FIND_RESOURCE},
            {"text": "I can't sleep because I keep thinking about my divorce", "type": WishType.HEALTH_WELLNESS},
        ],
    },
    {
        "name": "Aisha", "age": 18, "city": "Khartoum, Sudan", "mbti": "INFJ",
        "background": "Just finished high school, wants to study abroad, civil unrest, prayers 5x/day, loves calligraphy",
        "det": DetectorResults(
            mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}},
            emotion={"emotions": {"anxiety": 0.7, "hope": 0.3}},
            values={"top_values": ["tradition", "universalism"]},
            attachment={"style": "anxious"},
        ),
        "wishes": [
            {"text": "I want to find a scholarship to study medicine abroad", "type": WishType.FIND_RESOURCE},
            {"text": "The situation here is traumatic, I have collective trauma from the war", "type": WishType.HEALTH_WELLNESS},
            {"text": "I want to practice calligraphy with other artists, find a craft workshop", "type": WishType.FIND_RESOURCE},
            {"text": "When is the next prayer time? I need to find a mosque nearby", "type": WishType.FIND_PLACE},
            {"text": "I feel so alone and scared, I need someone to talk to as a companion", "type": WishType.HEALTH_WELLNESS},
        ],
    },
    {
        "name": "Diego", "age": 35, "city": "São Paulo, Brazil", "mbti": "ESTP",
        "background": "Uber driver, father of 2, wife has chronic illness, debts, loves football, hidden depression",
        "det": DetectorResults(
            mbti={"type": "ESTP", "dimensions": {"E_I": 0.7}},
            emotion={"emotions": {"anxiety": 0.6, "sadness": 0.5}},
            values={"top_values": ["security", "benevolence"]},
            fragility={"pattern": "defensive"},
        ),
        "wishes": [
            {"text": "I'm drowning in debt and the collectors won't stop calling", "type": WishType.FIND_RESOURCE},
            {"text": "My wife has chronic pain, I'm her caregiver and I'm exhausted, need respite", "type": WishType.HEALTH_WELLNESS},
            {"text": "I need free activities to do with my kids this weekend", "type": WishType.FIND_RESOURCE},
            {"text": "I want to find deals and discounts on groceries to save money", "type": WishType.FIND_RESOURCE},
            {"text": "I feel like a failure but I can't tell anyone, I need confidence", "type": WishType.HEALTH_WELLNESS},
        ],
    },
    {
        "name": "Noor", "age": 22, "city": "Amman, Jordan", "mbti": "ENFP",
        "background": "Fashion design student, LGBTQ+ (closeted), traditional family, loves indie music, anxious",
        "det": DetectorResults(
            mbti={"type": "ENFP", "dimensions": {"E_I": 0.7}},
            emotion={"emotions": {"anxiety": 0.6, "loneliness": 0.5}},
            values={"top_values": ["self-direction", "stimulation"]},
            attachment={"style": "anxious"},
        ),
        "wishes": [
            {"text": "I need a safe space where I can be myself without judgment, LGBTQ+ friendly", "type": WishType.FIND_PLACE},
            {"text": "I want to listen to music that understands my pain, indie or alternative", "type": WishType.FIND_RESOURCE},
            {"text": "I want to explore my identity, who am I really beyond my family's expectations", "type": WishType.FIND_RESOURCE},
            {"text": "I want to find a fashion design mentor who gets creative people", "type": WishType.FIND_RESOURCE},
            {"text": "I'm having a panic attack on the bus right now, help me calm down", "type": WishType.HEALTH_WELLNESS},
        ],
    },
    {
        "name": "Olga", "age": 40, "city": "Kyiv, Ukraine", "mbti": "ISTJ",
        "background": "Accountant, survived bombings, husband at front, son age 8, moved to Poland, homesick",
        "det": DetectorResults(
            mbti={"type": "ISTJ", "dimensions": {"E_I": 0.3}},
            emotion={"emotions": {"anxiety": 0.8, "sadness": 0.7}},
            values={"top_values": ["security", "tradition"]},
            fragility={"pattern": "hypervigilant"},
        ),
        "wishes": [
            {"text": "I have PTSD from the war, I need trauma support and collective healing", "type": WishType.HEALTH_WELLNESS},
            {"text": "I miss Ukrainian food so much, I want authentic hometown food near me", "type": WishType.FIND_PLACE},
            {"text": "My son needs kids activities in our new city to make friends", "type": WishType.FIND_PLACE},
            {"text": "I need immigration help with our refugee status and residency papers", "type": WishType.FIND_RESOURCE},
            {"text": "I want to find a quiet nature spot to cry without anyone seeing", "type": WishType.FIND_PLACE},
        ],
    },
    {
        "name": "Jamal", "age": 28, "city": "Detroit, USA", "mbti": "INFP",
        "background": "Ex-prisoner (3 years for marijuana), can't find work, poet, Muslim, recovering from addiction",
        "det": DetectorResults(
            mbti={"type": "INFP", "dimensions": {"E_I": 0.2}},
            emotion={"emotions": {"shame": 0.6, "anger": 0.4}},
            values={"top_values": ["self-direction", "universalism"]},
            attachment={"style": "avoidant"},
        ),
        "wishes": [
            {"text": "I need legal aid, my record makes it impossible to find work", "type": WishType.FIND_RESOURCE},
            {"text": "I've been sober for 90 days, I want to track my sobriety and stay clean", "type": WishType.HEALTH_WELLNESS},
            {"text": "I want to share my poetry at an open mic or poetry slam", "type": WishType.FIND_RESOURCE},
            {"text": "When is the next prayer time? I need to find a mosque", "type": WishType.FIND_PLACE},
            {"text": "I face discrimination everywhere because of my record, I need anti-discrimination help", "type": WishType.FIND_RESOURCE},
        ],
    },
    {
        "name": "Mei Lin", "age": 32, "city": "Singapore", "mbti": "ENTJ",
        "background": "Tech lead, workaholic, peripartum (8 months pregnant), husband travels for work, perfectionist",
        "det": DetectorResults(
            mbti={"type": "ENTJ", "dimensions": {"E_I": 0.6}},
            emotion={"emotions": {"anxiety": 0.5}},
            values={"top_values": ["achievement", "power"]},
            eq={"overall": 0.7},
        ),
        "wishes": [
            {"text": "I'm pregnant and worried about postpartum depression, what should I expect", "type": WishType.HEALTH_WELLNESS},
            {"text": "I need to plan my maternity leave and find a good prenatal yoga class", "type": WishType.LEARN_SKILL},
            {"text": "I want to find a coworking space where I can work from during my third trimester", "type": WishType.FIND_PLACE},
            {"text": "I need to plan my legacy at work before I go on leave", "type": WishType.FIND_RESOURCE},
            {"text": "I want a gift recommendation for my husband's birthday based on his personality", "type": WishType.FIND_RESOURCE},
        ],
    },
    {
        "name": "Kofi", "age": 19, "city": "Kumasi, Ghana", "mbti": "ESFP",
        "background": "Aspiring footballer, family can't afford training, loves Afrobeats, extrovert, first-gen smartphone",
        "det": DetectorResults(
            mbti={"type": "ESFP", "dimensions": {"E_I": 0.85}},
            emotion={"emotions": {"hope": 0.5, "frustration": 0.4}},
            values={"top_values": ["achievement", "stimulation"]},
        ),
        "wishes": [
            {"text": "I want to find free football training and sports activities near me", "type": WishType.FIND_PLACE},
            {"text": "I need a mentor who made it in sports, someone who understands the struggle", "type": WishType.FIND_RESOURCE},
            {"text": "I want to listen to music, Afrobeats to keep my energy up", "type": WishType.FIND_RESOURCE},
            {"text": "I need free wifi spots where I can watch training videos", "type": WishType.FIND_PLACE},
            {"text": "I want to start a small business on the side, maybe startup resources", "type": WishType.FIND_RESOURCE},
        ],
    },
    {
        "name": "Emma", "age": 45, "city": "Stockholm, Sweden", "mbti": "INTP",
        "background": "Divorced data scientist, teenage daughter with eating disorder, climate anxiety, atheist, loves documentaries",
        "det": DetectorResults(
            mbti={"type": "INTP", "dimensions": {"E_I": 0.2}},
            emotion={"emotions": {"worry": 0.7, "helplessness": 0.5}},
            values={"top_values": ["universalism", "self-direction"]},
        ),
        "wishes": [
            {"text": "My daughter has an eating disorder and I don't know how to help her", "type": WishType.HEALTH_WELLNESS},
            {"text": "I want to take environmental action, I have climate anxiety", "type": WishType.FIND_RESOURCE},
            {"text": "I need a documentary recommendation that will inspire me, not depress me", "type": WishType.FIND_RESOURCE},
            {"text": "I want deep social connections, not small talk, meaningful conversations", "type": WishType.FIND_RESOURCE},
            {"text": "I'm going through a breakup at 45, I need breakup healing activities", "type": WishType.HEALTH_WELLNESS},
        ],
    },
]


def assess_quality(wish_text, result, persona):
    """Rate recommendation quality 1-5 and explain gaps."""
    recs = result.recommendations
    if not recs:
        return 0, "No recommendations at all"

    issues = []
    bonuses = []

    # Check personality alignment
    mbti = persona["det"].mbti.get("type", "")
    is_introvert = mbti and mbti[0] == "I"
    for r in recs:
        if is_introvert and ("noisy" in r.tags or "loud" in r.tags):
            issues.append(f"Noisy rec '{r.title}' for introvert {mbti}")
        if is_introvert and ("quiet" in r.tags or "calming" in r.tags):
            bonuses.append("Introvert-friendly (quiet/calming)")
            break

    # Check emotion matching
    emotions = persona["det"].emotion.get("emotions", {})
    high_anxiety = emotions.get("anxiety", 0) > 0.5
    if high_anxiety:
        for r in recs:
            if "intense" in r.tags:
                issues.append(f"Intense rec '{r.title}' for anxious user")
            if "calming" in r.tags:
                bonuses.append("Anxiety-aware (calming)")
                break

    # Check relevance (does title/category relate to wish?)
    wish_lower = wish_text.lower()
    any_relevant = False
    for r in recs:
        title_lower = r.title.lower()
        cat_lower = r.category.lower()
        tags_str = " ".join(r.tags).lower()
        # Simple relevance: any keyword overlap
        wish_words = set(wish_lower.split())
        rec_words = set(title_lower.split()) | set(cat_lower.split()) | set(tags_str.split())
        overlap = wish_words & rec_words - {"i", "a", "to", "the", "my", "and", "or", "in", "for", "me", "need", "want"}
        if overlap:
            any_relevant = True
            break
    if not any_relevant:
        issues.append("No keyword overlap between wish and recommendations")

    # Check map data for location wishes
    if any(w in wish_lower for w in ["near", "nearby", "附近", "close"]):
        if result.map_data:
            bonuses.append("Has map data for location wish")
        else:
            issues.append("Location wish but no map data")

    # Check reminder
    if result.reminder_option:
        bonuses.append("Has reminder option")

    # Score
    score = 3  # base
    score += len(bonuses) * 0.5
    score -= len(issues) * 1.0
    score = max(1, min(5, round(score)))

    explanation = ""
    if bonuses:
        explanation += " +" + ", +".join(bonuses)
    if issues:
        explanation += " -" + ", -".join(issues)

    return score, explanation.strip()


def main():
    print("=" * 80)
    print("QUALITY TEST: 10 Users × 5 Wishes = 50 Assessments")
    print("=" * 80)

    all_scores = []
    total_wishes = 0

    for user in USERS:
        print(f"\n{'━' * 80}")
        print(f"👤 {user['name']}, {user['age']}, {user['city']} ({user['mbti']})")
        print(f"   {user['background']}")
        print(f"{'━' * 80}")

        for i, wish in enumerate(user["wishes"], 1):
            total_wishes += 1
            w = ClassifiedWish(
                wish_text=wish["text"], wish_type=wish["type"],
                level=WishLevel.L2, fulfillment_strategy="test",
            )

            try:
                result = fulfill_l2(w, user["det"])
                score, explanation = assess_quality(wish["text"], result, user)
                all_scores.append(score)

                stars = "★" * score + "☆" * (5 - score)
                print(f"\n  Wish {i}: \"{wish['text'][:70]}\"")
                print(f"  {stars} ({score}/5)")
                for j, r in enumerate(result.recommendations[:3], 1):
                    print(f"    {j}. {r.title} [{r.category}]")
                    print(f"       \"{r.relevance_reason[:65]}\"")
                    print(f"       Tags: {r.tags[:5]}")
                if result.map_data:
                    print(f"    📍 {result.map_data.place_type} ({result.map_data.radius_km}km)")
                if result.reminder_option:
                    print(f"    ⏰ {result.reminder_option.text}")
                if explanation:
                    print(f"    Quality: {explanation}")

            except Exception as e:
                all_scores.append(1)
                print(f"\n  Wish {i}: \"{wish['text'][:70]}\"")
                print(f"  ☆☆☆☆☆ ERROR: {str(e)[:60]}")

    # Summary
    avg = sum(all_scores) / len(all_scores) if all_scores else 0
    dist = {s: all_scores.count(s) for s in range(1, 6)}

    print(f"\n{'=' * 80}")
    print(f"QUALITY SUMMARY: {total_wishes} wishes assessed")
    print(f"{'=' * 80}")
    print(f"  Average quality: {avg:.1f}/5.0")
    print(f"  Distribution:")
    for s in range(5, 0, -1):
        bar = "█" * dist.get(s, 0) * 2
        print(f"    {'★'*s}{'☆'*(5-s)} ({s}/5): {dist.get(s, 0):2d} {bar}")
    print(f"\n  ★★★★★ (5/5): {dist.get(5,0)} — Perfect match")
    print(f"  ★★★★☆ (4/5): {dist.get(4,0)} — Good, minor gaps")
    print(f"  ★★★☆☆ (3/5): {dist.get(3,0)} — Acceptable, some issues")
    print(f"  ★★☆☆☆ (2/5): {dist.get(2,0)} — Poor, wrong domain")
    print(f"  ★☆☆☆☆ (1/5): {dist.get(1,0)} — Failed")

    # Save
    import json
    out = Path("/Users/michael/wish-engine/experiment_results")
    out.mkdir(exist_ok=True)
    with open(out / "quality_test_results.json", "w") as f:
        json.dump({"avg_score": avg, "distribution": dist, "total": total_wishes}, f, indent=2)
    print(f"\n  Saved to {out}/quality_test_results.json")


if __name__ == "__main__":
    main()
