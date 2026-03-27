#!/usr/bin/env python3
"""Simulate a Spanish user and test 10 random services against their needs."""

import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from wish_engine.models import ClassifiedWish, DetectorResults, WishLevel, WishType
from wish_engine.l2_fulfiller import fulfill_l2

# ── The User ─────────────────────────────────────────────────────────────────

PERSONA = {
    "name": "Lucía Morales",
    "age": 26,
    "gender": "F",
    "mbti": "INFP",
    "city": "Barcelona",
    "country": "Spain",
    "language": "Spanish (native), English (B2), Catalan (fluent)",
    "occupation": "Freelance illustrator",
    "values": ["aesthetics", "self-direction", "universalism"],
    "attachment": "anxious",
    "conflict_style": "avoiding",
    "emotion_state": {"emotions": {"anxiety": 0.55, "loneliness": 0.6, "creativity": 0.4}, "distress": 0.45},
    "fragility": "sensitive",
    "life_situation": """
    Lucía moved to Barcelona from a small town in Andalucía 3 years ago to pursue art.
    She freelances as an illustrator but income is unstable. She broke up with her boyfriend
    6 months ago and still hasn't fully recovered. She lives alone with her cat Frida.
    She's anxious about money, lonely in the big city, struggles with self-doubt about her art,
    and recently her grandmother in Córdoba was diagnosed with dementia. She wants to visit
    but can't afford the train. She's vegetarian, practices yoga occasionally, and loves
    Lorca's poetry. She's been having trouble sleeping and sometimes panic attacks on the metro.
    """,
}

# ── Her 10 Random Needs (simulating real life moments) ───────────────────────

NEEDS = [
    {
        "id": 1,
        "moment": "周三凌晨 2 点，失眠，焦虑发作",
        "wish_text": "I can't sleep and I'm having a panic attack, I need to calm down right now",
        "wish_type": WishType.HEALTH_WELLNESS,
        "expected_fulfiller": "l2_panic_relief",
        "what_she_really_needs": "即时呼吸引导 + 巴塞罗那 24 小时心理热线",
    },
    {
        "id": 2,
        "moment": "周四下午，接到奶奶病情恶化的电话",
        "wish_text": "My grandmother has dementia and I'm her caregiver from far away, I need remote care tools",
        "wish_type": WishType.HEALTH_WELLNESS,
        "expected_fulfiller": "l2_remote_care",
        "what_she_really_needs": "远程看护工具 + 科尔多瓦的老年护理资源 + 廉价火车票",
    },
    {
        "id": 3,
        "moment": "周五晚上，一个人在家，极度孤独",
        "wish_text": "I'm so lonely, I want to find people who share my niche art interests nearby",
        "wish_text_alt": "I feel alone, I want to join an interest circle for illustrators",
        "wish_type": WishType.FIND_RESOURCE,
        "expected_fulfiller": "l2_interest_circles",
        "what_she_really_needs": "巴塞罗那的插画师社群/画室聚会，小型（3-5人，因为她是 INFP）",
    },
    {
        "id": 4,
        "moment": "周六早上，想出去但不知道去哪，下雨了",
        "wish_text": "It's a rainy day and I want to do something cozy indoors",
        "wish_type": WishType.FIND_PLACE,
        "expected_fulfiller": "l2_rainy_day",
        "what_she_really_needs": "巴塞罗那雨天适合的安静咖啡馆/书店/博物馆",
    },
    {
        "id": 5,
        "moment": "周六下午，想吃点安慰食物但素食且没钱",
        "wish_text": "I need cheap vegetarian comfort food near me",
        "wish_type": WishType.FIND_PLACE,
        "expected_fulfiller": "l2_food",
        "what_she_really_needs": "便宜的素食安慰餐厅，安静氛围（INFP），附近 5km 内",
    },
    {
        "id": 6,
        "moment": "周日，想念前男友但不想承认",
        "wish_text": "I need to heal from my breakup, I want to explore new places I've never been",
        "wish_type": WishType.HEALTH_WELLNESS,
        "expected_fulfiller": "l2_breakup_healing",
        "what_she_really_needs": "分手疗愈路线：巴塞罗那她没去过的新地方，避开和前任的回忆地点",
    },
    {
        "id": 7,
        "moment": "周一，对自己的画没信心，想放弃",
        "wish_text": "I have no confidence in my art, I want to build courage and believe in myself",
        "wish_type": WishType.FIND_RESOURCE,
        "expected_fulfiller": "l2_confidence",
        "what_she_really_needs": "每日自信建设 + 适合 INFP 的温和方式（不是演讲，是日记/成就回顾）",
    },
    {
        "id": 8,
        "moment": "周二，收入焦虑，这个月房租可能不够",
        "wish_text": "I'm worried about money, I need financial help and maybe some deals or discounts",
        "wish_type": WishType.FIND_RESOURCE,
        "expected_fulfiller": "l2_deals",
        "what_she_really_needs": "巴塞罗那的免费活动 + 素食优惠 + freelancer 理财建议",
    },
    {
        "id": 9,
        "moment": "周三，想读洛尔卡的诗，用西班牙语",
        "wish_text": "I want to read poetry, especially Lorca, something that speaks to my soul",
        "wish_type": WishType.FIND_RESOURCE,
        "expected_fulfiller": "l2_poetry",
        "what_she_really_needs": "基于她的情绪（孤独+焦虑）推荐合适的诗歌，包括西班牙语诗人",
    },
    {
        "id": 10,
        "moment": "周四，Frida (猫) 生病了",
        "wish_text": "My cat is sick, I need a vet and pet care advice nearby",
        "wish_type": WishType.FIND_PLACE,
        "expected_fulfiller": "l2_pet_friendly",
        "what_she_really_needs": "附近的兽医 + 宠物急诊 + 如果猫死了的心理支持（pet_loss）",
    },
]

# ── Build DetectorResults for Lucía ──────────────────────────────────────────

LUCIA_DETECTOR = DetectorResults(
    mbti={"type": "INFP", "dimensions": {"E_I": 0.25, "S_N": 0.7, "T_F": 0.3, "J_P": 0.35}},
    emotion={"emotions": {"anxiety": 0.55, "loneliness": 0.6, "sadness": 0.3}, "distress": 0.45},
    values={"top_values": ["aesthetics", "self-direction", "universalism"]},
    attachment={"style": "anxious"},
    conflict={"style": "avoiding"},
    fragility={"pattern": "sensitive"},
    eq={"overall": 0.65},
)


def test_need(need: dict) -> dict:
    """Test one need against the L2 fulfiller system."""
    wish = ClassifiedWish(
        wish_text=need.get("wish_text_alt", need["wish_text"]),
        wish_type=need["wish_type"],
        level=WishLevel.L2,
        fulfillment_strategy="test",
    )

    try:
        result = fulfill_l2(wish, LUCIA_DETECTOR)
        recs = [{"title": r.title, "category": r.category, "reason": r.relevance_reason,
                 "score": r.score, "tags": r.tags[:5]} for r in result.recommendations]

        # Check if the right fulfiller was hit
        actual_tags = set()
        for r in result.recommendations:
            actual_tags.update(r.tags)

        return {
            "need_id": need["id"],
            "moment": need["moment"],
            "wish_text": wish.wish_text,
            "expected_fulfiller": need["expected_fulfiller"],
            "what_she_needs": need["what_she_really_needs"],
            "recommendations": recs,
            "has_recommendations": len(recs) > 0,
            "map_data": result.map_data.model_dump() if result.map_data else None,
            "reminder": result.reminder_option.text if result.reminder_option else None,
        }
    except Exception as e:
        return {
            "need_id": need["id"],
            "moment": need["moment"],
            "wish_text": wish.wish_text,
            "expected_fulfiller": need["expected_fulfiller"],
            "what_she_needs": need["what_she_really_needs"],
            "recommendations": [],
            "has_recommendations": False,
            "error": str(e),
        }


def main():
    print("=" * 70)
    print("🇪🇸 SPANISH USER SIMULATION: Lucía Morales, 26, Barcelona")
    print("=" * 70)
    print(f"\nProfile: {PERSONA['mbti']} | {PERSONA['occupation']} | Values: {', '.join(PERSONA['values'])}")
    print(f"Emotion: anxiety={PERSONA['emotion_state']['emotions']['anxiety']}, "
          f"loneliness={PERSONA['emotion_state']['emotions']['loneliness']}")
    print(f"Situation: {PERSONA['life_situation'].strip()[:200]}...")
    print()

    results = []
    satisfied = 0
    partially = 0
    failed = 0

    for need in NEEDS:
        print(f"\n{'─' * 60}")
        print(f"Need #{need['id']}: {need['moment']}")
        print(f"She says: \"{need['wish_text'][:80]}\"")
        print(f"She really needs: {need['what_she_really_needs'][:80]}")

        result = test_need(need)
        results.append(result)

        if result.get("error"):
            print(f"\n  ❌ ERROR: {result['error']}")
            failed += 1
            continue

        if not result["has_recommendations"]:
            print(f"\n  ❌ NO RECOMMENDATIONS")
            failed += 1
            continue

        print(f"\n  Star says:")
        for i, rec in enumerate(result["recommendations"][:3], 1):
            print(f"    {i}. {rec['title']} [{rec['category']}]")
            print(f"       Reason: {rec['reason'][:60]}")
            print(f"       Tags: {rec['tags']}")

        if result["map_data"]:
            print(f"  📍 Map: {result['map_data']['place_type']} within {result['map_data']['radius_km']}km")
        if result["reminder"]:
            print(f"  ⏰ Reminder: {result['reminder']}")

        # Evaluate quality
        gaps = []

        # Check INFP filtering
        for rec in result["recommendations"]:
            if "noisy" in rec["tags"] or "loud" in rec["tags"]:
                gaps.append("❌ Recommended noisy place to introvert INFP")

        # Check emotion matching
        if need["id"] == 1:  # panic attack
            if not any("breathing" in str(r) or "calm" in str(r) or "panic" in str(r)
                       for r in result["recommendations"]):
                gaps.append("⚠️ No immediate breathing/panic relief technique")

        # Check vegetarian for food
        if need["id"] == 5:
            if not any("vegetarian" in str(r["tags"]) or "vegan" in str(r["tags"])
                       for r in result["recommendations"]):
                gaps.append("⚠️ No vegetarian filter applied")

        # Check Spanish/Lorca for poetry
        if need["id"] == 9:
            if not any("spanish" in str(r).lower() or "lorca" in str(r).lower()
                       for r in result["recommendations"]):
                gaps.append("⚠️ No Spanish poetry/Lorca — only generic recommendations")

        # Check location awareness
        if need["id"] in [4, 5, 10]:
            if not result["map_data"]:
                gaps.append("⚠️ No map data — can't show nearby places in Barcelona")

        if not gaps:
            print(f"\n  ✅ SATISFIED — recommendations seem relevant")
            satisfied += 1
        else:
            print(f"\n  ⚠️ PARTIALLY SATISFIED — gaps found:")
            for gap in gaps:
                print(f"    {gap}")
            partially += 1

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("SUMMARY FOR LUCÍA")
    print(f"{'=' * 70}")
    print(f"  ✅ Satisfied: {satisfied}/10")
    print(f"  ⚠️  Partial:  {partially}/10")
    print(f"  ❌ Failed:    {failed}/10")

    print(f"\n{'─' * 60}")
    print("GAP ANALYSIS — What SoulMap can't do yet for Lucía:")
    print(f"{'─' * 60}")

    print("""
  1. 🌍 NO SPANISH LANGUAGE
     All recommendations are in English. Lucía speaks Spanish natively.
     The system has Chinese and Arabic keywords but NO Spanish.
     Gap: Need Spanish keyword routing for ALL fulfillers.

  2. 📍 NO REAL LOCATION
     Recommendations say "near you" but don't know she's in Barcelona.
     Without Google Places API key, everything is generic catalog.
     Gap: Need real API keys or city-specific catalogs.

  3. 🥬 NO DIETARY FILTER
     The allergy_friendly fulfiller exists but food fulfiller doesn't
     auto-apply vegetarian filter from her profile.
     Gap: Cross-reference dietary preferences into food recommendations.

  4. 📖 NO SPANISH POETS
     Poetry catalog has arabic_classical and chinese_tang but no
     Spanish poetry (Lorca, Machado, Neruda, Alberti).
     Gap: Expand poetry catalog with Spanish/Latin American literature.

  5. 💰 NO FREELANCER-SPECIFIC FINANCE
     Finance fulfiller has generic budgeting but nothing about
     irregular income, invoice management, tax for autonomos in Spain.
     Gap: Freelancer/gig economy financial advice.

  6. 🐱 NO PET EMERGENCY
     Pet_friendly finds pet cafes but not emergency vets.
     Gap: Separate l2_pet_emergency fulfiller or expand pet_friendly.

  7. 🚂 NO CHEAP TRAVEL
     She can't afford the train to visit grandma in Córdoba.
     No budget travel/transport recommendation.
     Gap: Budget travel fulfiller with personality matching.

  8. 🇪🇸 NO SPANISH CULTURAL CONTEXT
     Ramadan/Chinese New Year are covered, but not:
     - La Tomatina, Las Fallas, Semana Santa, Sant Jordi
     - Spanish siesta culture, tapas social norms
     Gap: Expand festival/cultural catalog for European cultures.
""")

    # Save
    import json
    out = Path("/Users/michael/wish-engine/experiment_results")
    out.mkdir(exist_ok=True)
    with open(out / "spanish_user_test.json", "w") as f:
        json.dump({"persona": PERSONA, "results": results,
                    "satisfied": satisfied, "partial": partially, "failed": failed},
                   f, indent=2, ensure_ascii=False, default=str)
    print(f"  Results saved to {out}/spanish_user_test.json")


if __name__ == "__main__":
    main()
