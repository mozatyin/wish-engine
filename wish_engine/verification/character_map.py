"""Character-to-Fulfiller mapping — which literary characters validate which features.

Each fulfiller is mapped to 3-5 literary characters who would realistically need
that service. The character's dialogue fixtures are used to simulate real usage.

Available fixtures (26 characters):
  scarlett, rhett, elizabeth, darcy, anna, vronsky, gatsby, daisy,
  jane, rochester, hamlet, lady_macbeth, raskolnikov, tony_soprano,
  don_draper, walter_white, jordan_belfort, celie, amy_dunne,
  katniss_everdeen, michael_corleone, heathcliff, atticus, xu_sanguan
"""

from __future__ import annotations

# Character → fixture file mapping
CHARACTER_FILES: dict[str, str] = {
    "scarlett": "scarlett_full.jsonl",
    "rhett": "rhett_full.jsonl",
    "elizabeth": "elizabeth_full.jsonl",
    "darcy": "darcy_full.jsonl",
    "anna": "anna_full.jsonl",
    "vronsky": "vronsky_full.jsonl",
    "gatsby": "gatsby_full.jsonl",
    "daisy": "daisy_full.jsonl",
    "jane": "jane_full.jsonl",
    "rochester": "rochester_full.jsonl",
    "hamlet": "hamlet_full.jsonl",
    "lady_macbeth": "lady_macbeth_full.jsonl",
    "raskolnikov": "raskolnikov_full.jsonl",
    "tony_soprano": "tony_soprano_full.jsonl",
    "don_draper": "don_draper_full.jsonl",
    "walter_white": "walter_white_full.jsonl",
    "jordan_belfort": "jordan_belfort_full.jsonl",
    "celie": "celie_full.jsonl",
    "amy_dunne": "amy_dunne_full.jsonl",
    "katniss": "katniss_everdeen_full.jsonl",
    "michael_corleone": "michael_corleone_full.jsonl",
    "heathcliff": "heathcliff_full.jsonl",
    "atticus": "atticus_full.jsonl",
    "xu_sanguan": "xu_sanguan_full.jsonl",
}

# ── Fulfiller → Character mapping ────────────────────────────────────────────
# Each entry: fulfiller_module_name → [(character, why_they_need_it, expected_category)]

FULFILLER_CHARACTER_MAP: dict[str, list[dict]] = {
    # ═══ 危 Crisis ═══
    "l2_suicide_prevention": [
        {"character": "anna", "reason": "Anna throws herself under the train — the system should detect crisis signals before the final act", "expected_tags": ["crisis", "hotline"]},
        {"character": "hamlet", "reason": "'To be or not to be' — active suicidal ideation masked as philosophy", "expected_tags": ["crisis"]},
        {"character": "raskolnikov", "reason": "Post-murder existential despair, isolation, self-destruction", "expected_tags": ["crisis", "counseling"]},
        {"character": "lady_macbeth", "reason": "Guilt-driven madness and self-harm ('Out, damn'd spot')", "expected_tags": ["crisis"]},
    ],
    "l2_domestic_violence": [
        {"character": "celie", "reason": "Beaten and raped by her husband for years — needs escape and support", "expected_tags": ["dv", "hotline"]},
        {"character": "rochester", "reason": "Bertha Mason locked in the attic — structural violence against women", "expected_tags": ["dv", "hotline"]},
        {"character": "heathcliff", "reason": "Violence toward Isabella and Hareton — cycle of abuse", "expected_tags": ["dv", "confidential"]},
    ],
    "l2_debt_crisis": [
        {"character": "xu_sanguan", "reason": "Sells blood to feed family, perpetual poverty crisis", "expected_tags": ["debt", "counseling"]},
        {"character": "raskolnikov", "reason": "Desperate poverty drives him to murder — financial crisis is root cause", "expected_tags": ["debt", "counseling"]},
        {"character": "gatsby", "reason": "Built entire fortune on crime to escape poverty — class desperation", "expected_tags": ["debt", "bankruptcy"]},
    ],
    "l2_collective_trauma": [
        {"character": "katniss", "reason": "PTSD from the Hunger Games and war — collective trauma of District 12", "expected_tags": ["trauma", "ptsd"]},
        {"character": "scarlett", "reason": "Atlanta burning, siege, starvation — war trauma", "expected_tags": ["disaster", "community"]},
        {"character": "celie", "reason": "Generational trauma of slavery and racism", "expected_tags": ["trauma"]},
    ],

    # ═══ 哀 Grief ═══
    "l2_bereavement": [
        {"character": "hamlet", "reason": "Father murdered — complicated grief drives the entire plot", "expected_tags": ["grief", "loss"]},
        {"character": "heathcliff", "reason": "Catherine's death destroys him — grief becomes vengeance", "expected_tags": ["grief", "support"]},
        {"character": "scarlett", "reason": "Loses her mother, her child Bonnie, and Melanie", "expected_tags": ["grief"]},
        {"character": "katniss", "reason": "Loses Prim, Rue, Finnick — survivor's grief", "expected_tags": ["grief", "survivor"]},
    ],
    "l2_pet_loss": [
        {"character": "elizabeth", "reason": "Pastoral life at Longbourn — losing a beloved animal would be personal", "expected_tags": ["grief", "memorial"]},
    ],

    # ═══ 瘾 Addiction ═══
    "l2_addiction_meetings": [
        {"character": "don_draper", "reason": "Alcoholic throughout the series — functional but deteriorating", "expected_tags": ["aa", "recovery"]},
        {"character": "jordan_belfort", "reason": "Quaaludes, cocaine — extreme substance abuse", "expected_tags": ["na", "recovery"]},
        {"character": "tony_soprano", "reason": "Food, rage, power — behavioral addictions", "expected_tags": ["recovery"]},
    ],
    "l2_trigger_alert": [
        {"character": "don_draper", "reason": "Bars and stress trigger drinking — needs avoidance routing", "expected_tags": ["avoidance", "trigger"]},
        {"character": "jordan_belfort", "reason": "Wall Street parties = drug trigger", "expected_tags": ["alert"]},
    ],

    # ═══ 护 Caregiving ═══
    "l2_caregiver_respite": [
        {"character": "jane", "reason": "Cares for Rochester after his blindness — total caregiver burden", "expected_tags": ["calming", "home"]},
        {"character": "scarlett", "reason": "Forced to care for Melanie, the baby, everyone at Tara", "expected_tags": ["adult_daycare", "calming"]},
        {"character": "xu_sanguan", "reason": "Carries his entire family on his back — literal blood sacrifice", "expected_tags": ["calming", "medical"]},
    ],

    # ═══ 权 Rights ═══
    "l2_legal_aid": [
        {"character": "atticus", "reason": "Defends Tom Robinson — legal system as justice/injustice", "expected_tags": ["rights", "advocacy"]},
        {"character": "celie", "reason": "No legal protection from her abuser", "expected_tags": ["rights", "community"]},
        {"character": "raskolnikov", "reason": "Criminal justice system — needs defense", "expected_tags": ["rights", "advocacy"]},
    ],
    "l2_anti_discrimination": [
        {"character": "atticus", "reason": "Fights racial discrimination in 1930s Alabama", "expected_tags": ["discrimination_hotline", "filing_complaint"]},
        {"character": "celie", "reason": "Racial + gender discrimination", "expected_tags": ["discrimination_hotline", "confidential"]},
        {"character": "darcy", "reason": "Class discrimination — he both perpetuates and suffers from it", "expected_tags": ["discrimination_hotline", "filing_complaint"]},
    ],

    # ═══ 养 Nurturing ═══
    "l2_chronic_pain": [
        {"character": "rochester", "reason": "Blinded and maimed in the fire — chronic disability", "expected_tags": ["management", "clinic"]},
        {"character": "xu_sanguan", "reason": "Body broken from selling blood — chronic health consequences", "expected_tags": ["management", "journaling"]},
    ],
    "l2_eating_disorder": [
        {"character": "anna", "reason": "Stops eating as despair deepens — self-starvation as control", "expected_tags": ["ed", "therapy"]},
    ],
    "l2_postpartum": [
        {"character": "anna", "reason": "After giving birth to Vronsky's daughter, spirals into depression", "expected_tags": ["depression", "community"]},
        {"character": "scarlett", "reason": "Rejection of motherhood, complicated maternal feelings", "expected_tags": ["depression", "calming"]},
    ],

    # ═══ 义 Purpose ═══
    "l2_legacy_planning": [
        {"character": "walter_white", "reason": "'I did it for me' — legacy vs ego, what do you leave behind?", "expected_tags": ["ethical_will", "memoir"]},
        {"character": "gatsby", "reason": "Built an empire but left nothing real — the hollow legacy", "expected_tags": ["ethical_will", "mentoring"]},
        {"character": "atticus", "reason": "Moral legacy to his children — 'real courage'", "expected_tags": ["mentoring", "community"]},
    ],
    "l2_social_justice": [
        {"character": "atticus", "reason": "Fighting systemic racism through the legal system", "expected_tags": ["advocacy", "petition"]},
        {"character": "katniss", "reason": "Rebellion against oppressive regime — revolutionary justice", "expected_tags": ["advocacy", "accountability"]},
        {"character": "celie", "reason": "Finding voice and agency after a lifetime of oppression", "expected_tags": ["advocacy", "government"]},
    ],

    # ═══ 根 Roots ═══
    "l2_roots_journey": [
        {"character": "gatsby", "reason": "James Gatz erased his origins — the lost roots haunt him", "expected_tags": ["heritage", "genealogy"]},
        {"character": "don_draper", "reason": "Dick Whitman stole a dead man's identity — ultimate rootlessness", "expected_tags": ["heritage", "ancestry"]},
        {"character": "heathcliff", "reason": "Orphan with no known origin — rootlessness drives rage", "expected_tags": ["ancestry", "culture"]},
    ],
    "l2_cultural_recovery": [
        {"character": "celie", "reason": "African heritage suppressed by slavery — Shug helps her reconnect", "expected_tags": ["indigenous", "ceremony"]},
        {"character": "xu_sanguan", "reason": "Chinese cultural traditions as survival anchor through hardship", "expected_tags": ["community", "practice"]},
    ],

    # ═══ 生活品质 Life Quality ═══
    "l2_food": [
        {"character": "xu_sanguan", "reason": "Hunger is central — 'selling blood to eat pork liver noodles'", "expected_tags": ["comfort"]},
        {"character": "scarlett", "reason": "'I'll never be hungry again' — food as survival and dignity", "expected_tags": ["comfort"]},
        {"character": "tony_soprano", "reason": "Emotional eating — food as coping mechanism", "expected_tags": ["comfort", "emotional"]},
    ],
    "l2_music": [
        {"character": "elizabeth", "reason": "Piano playing at Pemberley — music as expression", "expected_tags": ["calming", "acoustic"]},
        {"character": "gatsby", "reason": "The parties, the orchestra — music as facade", "expected_tags": ["calming", "ambient"]},
    ],
    "l2_nature_healing": [
        {"character": "jane", "reason": "Moors as healing landscape — nature restores her", "expected_tags": ["nature", "healing"]},
        {"character": "katniss", "reason": "The forest is her only safe space — nature as sanctuary", "expected_tags": ["nature", "forest"]},
        {"character": "darcy", "reason": "Pemberley grounds — nature as authentic self", "expected_tags": ["nature"]},
    ],
    "l2_confidence": [
        {"character": "darcy", "reason": "Needs to overcome social rigidity to express love", "expected_tags": ["calming", "energizing"]},
        {"character": "elizabeth", "reason": "Confident but must learn humility — balanced self-assurance", "expected_tags": ["practical", "self-paced"]},
        {"character": "celie", "reason": "From zero self-worth to 'I'm here' — the ultimate confidence journey", "expected_tags": ["calming", "energizing"]},
    ],
}


def get_characters_for_fulfiller(fulfiller_name: str) -> list[dict]:
    """Get literary characters who validate a given fulfiller."""
    return FULFILLER_CHARACTER_MAP.get(fulfiller_name, [])


def get_all_fulfillers_with_characters() -> dict[str, list[dict]]:
    """Get the complete mapping."""
    return dict(FULFILLER_CHARACTER_MAP)


def get_unmapped_fulfillers() -> list[str]:
    """Find L2 fulfillers that don't have character validation yet."""
    import os
    from pathlib import Path
    l2_dir = Path(__file__).parent.parent
    all_l2 = [f.stem for f in l2_dir.glob("l2_*.py")]
    mapped = set(FULFILLER_CHARACTER_MAP.keys())
    return [f for f in all_l2 if f not in mapped]
