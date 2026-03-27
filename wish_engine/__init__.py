"""Wish Engine — SoulMap V10 wish detection, classification, fulfillment, and rendering."""

from wish_engine.models import (
    AgentProfile,
    CardType,
    ClassifiedWish,
    CrossDetectorPattern,
    DetectedWish,
    DetectorResults,
    EmotionState,
    Intention,
    L1FulfillmentResult,
    L2FulfillmentResult,
    L3MatchResult,
    MapData,
    NegotiationProposal,
    NegotiationResponse,
    NegotiationState,
    Recommendation,
    ReminderOption,
    RenderOutput,
    WishLevel,
    WishState,
    WishType,
)
from wish_engine.detector import detect_wishes
from wish_engine.classifier import classify, classify_batch, WISH_TYPES, FULFILLMENT_STRATEGIES
from wish_engine.l1_fulfiller import fulfill
from wish_engine.renderer import render, render_lifecycle
from wish_engine.adapter import detect_from_soul_items
from wish_engine.marketplace import Marketplace, Match, MatchState, Request, AgentRecord
from wish_engine.match_reason import generate_match_reason
from wish_engine.l2_fulfiller import fulfill_l2, L2Fulfiller, PersonalityFilter
from wish_engine.l2_places import PlaceFulfiller
from wish_engine.apis.places_api import nearby_search as places_nearby_search, is_available as places_api_available
from wish_engine.apis.places_personality import enrich_place, enrich_places, wish_to_search_params
from wish_engine.l2_books import BookFulfiller
from wish_engine.l2_courses import CourseFulfiller
from wish_engine.l2_career import CareerFulfiller
from wish_engine.l2_wellness import WellnessFulfiller
from wish_engine.l2_events import EventFulfiller
from wish_engine.apis.events_api import search_all as events_search_all, is_available as events_api_available
from wish_engine.apis.events_personality import enrich_event as events_enrich_event
from wish_engine.deduplicator import deduplicate
from wish_engine.engine import WishEngine, WishEngineResult
from wish_engine.queue import WishQueue, WishPriority, QueuedWish
from wish_engine.l3_matcher import L3Matcher, L3MatchScore, MATCH_THRESHOLD
from wish_engine.agent_negotiator import AgentNegotiator
from wish_engine.compass import (
    WishCompass,
    ScanResult,
    Shell,
    ShellStage,
    Signal,
    ContradictionPattern,
    SecretVault,
    TriggerEngine,
    RevelationRenderer,
    Revelation,
    RevelationStyle,
    CompassStarOutput,
    render_shell_star,
    DialogueScanner,
    save_vault,
    load_vault,
)

__all__ = [
    # Models
    "AgentProfile",
    "CardType",
    "ClassifiedWish",
    "CrossDetectorPattern",
    "DetectedWish",
    "DetectorResults",
    "EmotionState",
    "Intention",
    "L1FulfillmentResult",
    "L2FulfillmentResult",
    "L3MatchResult",
    "MapData",
    "Recommendation",
    "ReminderOption",
    "NegotiationProposal",
    "NegotiationResponse",
    "NegotiationState",
    "RenderOutput",
    "WishLevel",
    "WishState",
    "WishType",
    # Functions
    "detect_wishes",
    "classify",
    "classify_batch",
    "fulfill",
    "render",
    "render_lifecycle",
    # Adapter (SoulGraph → Wish Engine)
    "detect_from_soul_items",
    # L2 Fulfillment
    "fulfill_l2",
    "L2Fulfiller",
    "PersonalityFilter",
    "PlaceFulfiller",
    "BookFulfiller",
    "CourseFulfiller",
    "CareerFulfiller",
    "WellnessFulfiller",
    # Deduplicator
    "deduplicate",
    # Queue
    "WishQueue",
    "WishPriority",
    "QueuedWish",
    # Engine (facade)
    "WishEngine",
    "WishEngineResult",
    # Marketplace (L3)
    "Marketplace",
    "generate_match_reason",
    "Match",
    "MatchState",
    "Request",
    "AgentRecord",
    # L3 Matcher
    "L3Matcher",
    "L3MatchScore",
    "MATCH_THRESHOLD",
    # Agent Negotiator
    "AgentNegotiator",
    # Compass
    "WishCompass",
    "ScanResult",
    "Shell",
    "ShellStage",
    "Signal",
    "ContradictionPattern",
    "SecretVault",
    "TriggerEngine",
    "RevelationRenderer",
    "Revelation",
    "RevelationStyle",
    "CompassStarOutput",
    "render_shell_star",
    "DialogueScanner",
    "save_vault",
    "load_vault",
    # Event Discovery
    "EventFulfiller",
    "events_search_all",
    "events_api_available",
    "events_enrich_event",
    # Google Places API
    "places_nearby_search",
    "places_api_available",
    "enrich_place",
    "enrich_places",
    "wish_to_search_params",
    # Constants
    "WISH_TYPES",
    "FULFILLMENT_STRATEGIES",
]
