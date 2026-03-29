"""Utility APIs. All free, no key."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError


# 66. URL screenshot preview
def website_preview(url: str) -> str:
    """Returns URL to a screenshot of the website."""
    from urllib.parse import quote

    return f"https://image.thum.io/get/{quote(url, safe=':/')}"


# 67. UUID generator (local)
def generate_uuid() -> str:
    import uuid

    return str(uuid.uuid4())


# 68. Password strength checker (local)
def check_password_strength(password: str) -> dict:
    score = 0
    feedback = []
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("At least 8 characters")
    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append("Add uppercase letter")
    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append("Add lowercase letter")
    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append("Add number")
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        score += 1
    else:
        feedback.append("Add special character")
    strength = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"][min(score, 4)]
    return {"score": score, "strength": strength, "feedback": feedback}


# 69. Text readability score (local)
def readability_score(text: str) -> dict:
    words = text.split()
    sentences = max(text.count(".") + text.count("!") + text.count("?"), 1)
    syllables = sum(max(1, sum(1 for c in w.lower() if c in "aeiou")) for w in words)
    avg_words_per_sentence = len(words) / sentences
    avg_syllables_per_word = syllables / max(len(words), 1)
    # Flesch Reading Ease
    score = 206.835 - 1.015 * avg_words_per_sentence - 84.6 * avg_syllables_per_word
    if score >= 90:
        level = "Very Easy (5th grade)"
    elif score >= 70:
        level = "Easy (6th-7th grade)"
    elif score >= 50:
        level = "Moderate (8th-9th grade)"
    elif score >= 30:
        level = "Difficult (college)"
    else:
        level = "Very Difficult (graduate)"
    return {
        "flesch_score": round(score, 1),
        "level": level,
        "word_count": len(words),
        "sentence_count": sentences,
    }


# 70. Lorem Ipsum generator (local)
def lorem_ipsum(paragraphs: int = 1) -> str:
    base = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
        "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in "
        "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."
    )
    return "\n\n".join([base] * paragraphs)


def is_available() -> bool:
    return True
