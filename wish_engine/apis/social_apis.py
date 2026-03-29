"""Social & communication APIs. Free, no key or local compute."""
from __future__ import annotations
import json
import random
from urllib.request import urlopen, Request
from urllib.error import URLError


# 91. Conversation starters (local)
def conversation_starter(context: str = "general") -> str:
    starters = {
        "general": [
            "What's the most interesting thing you've read recently?",
            "If you could learn any skill instantly, what would it be?",
            "What's a small thing that made you happy this week?",
        ],
        "deep": [
            "What do you think people misunderstand about you?",
            "What's a belief you held strongly that you've changed your mind about?",
            "What would you do if you knew you couldn't fail?",
        ],
        "fun": [
            "What's the weirdest food combination you secretly love?",
            "If you could have dinner with anyone, living or dead, who?",
            "What's your most unpopular opinion?",
        ],
        "first_date": [
            "What's your idea of a perfect day?",
            "What are you passionate about?",
            "What's on your bucket list?",
        ],
        "family": [
            "What's your favorite family tradition?",
            "What did you want to be when you grew up?",
            "What's a lesson your parents taught you?",
        ],
    }
    options = starters.get(context, starters["general"])
    return random.choice(options)


# 92. Compliment generator (local)
def random_compliment() -> str:
    compliments = [
        "You have a way of making people feel heard.",
        "Your strength is quiet but powerful.",
        "The world is better because you're in it.",
        "Your perspective matters more than you know.",
        "You handle hard things with more grace than you realize.",
        "Someone out there is grateful you exist.",
        "Your kindness ripples further than you can see.",
        "You're allowed to take up space.",
        "Your feelings are valid. All of them.",
        "You don't have to be perfect to be worthy of love.",
    ]
    return random.choice(compliments)


# 93. Ice breaker questions (local)
def ice_breaker(group_size: str = "small") -> str:
    small = [
        "Everyone share one word that describes how they feel right now",
        "What's something you're looking forward to this week?",
    ]
    large = [
        "Find someone wearing the same color as you and introduce yourself",
        "Share one surprising fact about yourself with the person next to you",
    ]
    return random.choice(small if group_size == "small" else large)


# 94. Conflict resolution prompt (local)
def conflict_prompt() -> str:
    prompts = [
        "Before responding, take 3 breaths. Then ask: 'What are you really feeling?'",
        "Try saying: 'I feel [emotion] when [behavior] because [need].'",
        "Ask yourself: Will this matter in 5 years?",
        "What would the kindest version of yourself say right now?",
        "Is this about being right, or about being connected?",
    ]
    return random.choice(prompts)


# 95. Love language identifier questions (local)
def love_language_question() -> dict:
    questions = [
        {
            "question": "What makes you feel most loved?",
            "options": {
                "A": "Hearing 'I love you' (Words of Affirmation)",
                "B": "A long hug (Physical Touch)",
                "C": "A thoughtful gift (Receiving Gifts)",
                "D": "Quality time together (Quality Time)",
                "E": "Someone doing chores for you (Acts of Service)",
            },
        },
        {
            "question": "What hurts you most when missing?",
            "options": {
                "A": "Not hearing appreciation",
                "B": "No physical affection",
                "C": "Forgotten special occasions",
                "D": "Not spending time together",
                "E": "Having to do everything yourself",
            },
        },
    ]
    return random.choice(questions)


def is_available() -> bool:
    return True
