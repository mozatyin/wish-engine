"""City-specific place data — real places for top cities when no Google API key.

This is NOT a generic catalog. These are REAL places with REAL names in specific cities.
When the product team gets a Google Places API key, this becomes the fallback.
"""

from __future__ import annotations
from typing import Any

# Real places in real cities
CITY_PLACES: dict[str, list[dict[str, Any]]] = {
    "dubai": [
        {"title": "The Sum of Us Cafe", "description": "Award-winning specialty coffee + brunch. Quiet corners, laptop-friendly. Al Quoz.", "category": "cafe", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "coffee", "calming", "wifi", "solo-friendly"], "lat": 25.1416, "lng": 55.2279},
        {"title": "Al Barari Nature Walk", "description": "Lush botanical gardens with 2km walking trail. One of the quietest spots in Dubai.", "category": "park", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["nature", "quiet", "calming", "walking", "peaceful", "solo-friendly"], "lat": 25.1127, "lng": 55.2731},
        {"title": "Alserkal Avenue", "description": "Art galleries and creative spaces in Al Quoz industrial district. Free exhibitions.", "category": "art_gallery", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["art", "quiet", "calming", "culture", "free", "creative"], "lat": 25.1433, "lng": 55.2261},
        {"title": "Dubai Public Library - Al Ras", "description": "Historic library near Gold Souk. Air-conditioned, quiet reading rooms.", "category": "library", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "reading", "calming", "study", "free", "air-conditioned"], "lat": 25.2697, "lng": 55.2963},
        {"title": "JBR Beach Walk", "description": "3km beachfront promenade. Busy evenings but peaceful mornings.", "category": "beach", "noise": "moderate", "social": "medium", "mood": "calming", "tags": ["beach", "walking", "nature", "outdoor", "calming"], "lat": 25.0784, "lng": 55.1337},
        {"title": "Kite Beach Yoga (free)", "description": "Free community yoga every Saturday morning 7am. Bring your own mat.", "category": "yoga", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["yoga", "exercise", "calming", "free", "outdoor", "community"], "lat": 25.1583, "lng": 55.1936},
        {"title": "Wild & The Moon", "description": "Vegan cafe with healthy bowls. Quiet, Instagram-worthy interior.", "category": "restaurant", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["vegan", "healthy", "quiet", "calming", "cafe"], "lat": 25.2048, "lng": 55.2708},
        {"title": "Shelter Gym - JLT", "description": "CrossFit box + functional fitness. Community-driven, coaches know your name.", "category": "gym", "noise": "loud", "social": "high", "mood": "intense", "tags": ["exercise", "intense", "social", "fitness", "community"], "lat": 25.0747, "lng": 55.1460},
        {"title": "Masjid Jumeirah", "description": "Open to all visitors for tours. One of the few mosques welcoming non-Muslims.", "category": "mosque", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["mosque", "spiritual", "traditional", "quiet", "calming", "culture"], "lat": 25.2336, "lng": 55.2622},
        {"title": "Kinokuniya Book Store - Dubai Mall", "description": "Massive multi-language bookstore. Arabic, English, Japanese, French sections.", "category": "bookstore", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["reading", "quiet", "calming", "books", "multilingual"], "lat": 25.1972, "lng": 55.2796},
    ],
    "riyadh": [
        {"title": "Wadi Hanifah", "description": "Restored valley park. 80km of walking trails through natural landscape.", "category": "park", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["nature", "quiet", "calming", "walking", "peaceful"], "lat": 24.7136, "lng": 46.6753},
        {"title": "Edge of the World (Jebel Fihrayn)", "description": "Dramatic cliff edge overlooking endless desert. 90min drive from Riyadh.", "category": "nature", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["nature", "quiet", "calming", "dramatic", "outdoor", "solo-friendly"], "lat": 24.8350, "lng": 46.3647},
        {"title": "Naila Art Gallery", "description": "Contemporary Saudi art. Quiet, thoughtful exhibitions.", "category": "art_gallery", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["art", "quiet", "calming", "culture", "saudi"], "lat": 24.6877, "lng": 46.6850},
        {"title": "King Fahd National Library", "description": "Stunning architecture. Free reading rooms, Arabic and English collections.", "category": "library", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "reading", "calming", "study", "free"], "lat": 24.6881, "lng": 46.7049},
        {"title": "Mugg & Bean", "description": "South African cafe chain. Quiet corners, good coffee, laptop-friendly.", "category": "cafe", "noise": "moderate", "social": "medium", "mood": "calming", "tags": ["coffee", "calming", "wifi", "cafe"], "lat": 24.7241, "lng": 46.6359},
    ],
    "shanghai": [
        {"title": "1933 \u8001\u573a\u574a", "description": "Art deco slaughterhouse turned creative space. Galleries, studios, quiet courtyards.", "category": "art_gallery", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["art", "quiet", "calming", "culture", "creative", "architecture"], "lat": 31.2526, "lng": 121.4904},
        {"title": "\u6b66\u5eb7\u8def", "description": "French Concession tree-lined street. Independent bookshops, cafes, galleries.", "category": "walking_street", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["walking", "quiet", "calming", "culture", "cafe", "books", "solo-friendly"], "lat": 31.2043, "lng": 121.4368},
        {"title": "\u4e0a\u6d77\u56fe\u4e66\u9986\u4e1c\u9986", "description": "New mega-library in Pudong. Silent study rooms, city views, free.", "category": "library", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "reading", "calming", "study", "free", "modern"], "lat": 31.2185, "lng": 121.5570},
        {"title": "M50\u521b\u610f\u56ed", "description": "Art district in Moganshan Rd. 100+ galleries, free entry. Quiet weekdays.", "category": "art_gallery", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["art", "quiet", "creative", "free", "culture"], "lat": 31.2498, "lng": 121.4492},
        {"title": "\u9759\u5b89\u5bfa\u65c1\u7684\u611a\u56ed\u8def", "description": "Hidden boutiques and tiny cafes behind the temple. Less touristy.", "category": "walking_street", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "cafe", "calming", "hidden", "local", "solo-friendly"], "lat": 31.2234, "lng": 121.4454},
    ],
    "cairo": [
        {"title": "Al-Azhar Park", "description": "12-hectare oasis in Islamic Cairo. Lake, gardens, city views. Quiet mornings.", "category": "park", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["nature", "quiet", "calming", "park", "views"], "lat": 30.0380, "lng": 31.2633},
        {"title": "Makan Egyptian Center for Culture and Arts", "description": "Live traditional music weekly. Intimate venue, 50 seats.", "category": "music_venue", "noise": "moderate", "social": "medium", "mood": "calming", "tags": ["music", "culture", "traditional", "intimate", "calming"], "lat": 30.0447, "lng": 31.2357},
        {"title": "Diwan Bookstore - Zamalek", "description": "Best English/Arabic bookstore in Cairo. Cafe upstairs, quiet atmosphere.", "category": "bookstore", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["reading", "quiet", "calming", "books", "cafe", "arabic"], "lat": 30.0585, "lng": 31.2202},
        {"title": "The Greek Campus", "description": "Coworking/startup space in downtown Cairo. Fast wifi, events.", "category": "coworking", "noise": "moderate", "social": "medium", "mood": "calming", "tags": ["coworking", "wifi", "startup", "productive"], "lat": 30.0398, "lng": 31.2393},
        {"title": "Cairo Jazz Club", "description": "Live jazz, indie, electronic. Best nightlife in Cairo. Thurs-Sat.", "category": "music_venue", "noise": "loud", "social": "high", "mood": "intense", "tags": ["music", "social", "nightlife", "jazz", "intense"], "lat": 30.0712, "lng": 31.2105},
    ],
    "barcelona": [
        {"title": "Federal Caf\u00e9 - G\u00f2tic", "description": "Quiet Australian-style cafe. Excellent coffee, laptop-friendly, courtyard.", "category": "cafe", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "coffee", "calming", "wifi", "solo-friendly"], "lat": 41.3797, "lng": 2.1770},
        {"title": "Parc del Laberint d'Horta", "description": "18th century maze garden. Barcelona's oldest park. Few tourists know it.", "category": "park", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["nature", "quiet", "calming", "hidden", "garden", "solo-friendly"], "lat": 41.4397, "lng": 2.1466},
        {"title": "MACBA (Museum of Contemporary Art)", "description": "Free entry some evenings. Thought-provoking contemporary art.", "category": "museum", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["art", "quiet", "calming", "culture", "free", "museum"], "lat": 41.3832, "lng": 2.1672},
        {"title": "La Central del Raval", "description": "Beautiful bookshop in a former chapel. Spanish, Catalan, English books.", "category": "bookstore", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["reading", "quiet", "calming", "books", "architecture"], "lat": 41.3811, "lng": 2.1701},
        {"title": "Flax & Kale", "description": "Flexitarian restaurant. Vegan-friendly, healthy, trendy. Eixample.", "category": "restaurant", "noise": "moderate", "social": "medium", "mood": "calming", "tags": ["vegan", "healthy", "calming", "restaurant"], "lat": 41.3929, "lng": 2.1638},
    ],
}


CITY_EVENTS: dict[str, list[dict[str, Any]]] = {
    "dubai": [
        {"title": "Alserkal Art Week", "description": "Free gallery openings, artist talks, installations across Al Quoz", "category": "exhibition", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["art", "culture", "free", "quiet", "creative"]},
        {"title": "Dubai Comedy Festival", "description": "International stand-up at Madinat Jumeirah. March/April annually.", "category": "comedy", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["comedy", "social", "fun", "entertainment"]},
        {"title": "Global Village", "description": "Cultural pavilions from 90 countries. Food, shopping, performances. Oct-Apr.", "category": "festival", "noise": "loud", "social": "high", "mood": "intense", "tags": ["culture", "social", "food", "festival", "noisy"]},
        {"title": "Friday Beach Yoga", "description": "Free community yoga at Kite Beach every Friday 7am", "category": "yoga", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["yoga", "free", "calming", "outdoor", "community"]},
        {"title": "Quranic Recitation at Jumeirah Mosque", "description": "Weekly recitation and discussion. Open to all faiths.", "category": "religious", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["spiritual", "traditional", "quiet", "calming", "community"]},
    ],
    "riyadh": [
        {"title": "Riyadh Season", "description": "Annual entertainment festival. Concerts, food, activities across the city.", "category": "festival", "noise": "loud", "social": "high", "mood": "intense", "tags": ["festival", "entertainment", "social", "noisy"]},
        {"title": "JAX District Events", "description": "Art exhibitions and cultural events in Diriyah", "category": "exhibition", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["art", "culture", "quiet", "creative"]},
    ],
    "shanghai": [
        {"title": "M50 Gallery Opening", "description": "Weekly gallery openings with free wine. Saturdays 3-6pm.", "category": "exhibition", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["art", "free", "quiet", "creative", "social"]},
        {"title": "JZ Club Jazz Night", "description": "Live jazz every Thursday-Saturday. Shanghai's best jazz venue.", "category": "jazz", "noise": "moderate", "social": "medium", "mood": "calming", "tags": ["music", "jazz", "culture", "calming"]},
        {"title": "\u4e0a\u6d77\u8bfb\u4e66\u4f1a", "description": "Weekly Chinese/English book club at various cafes", "category": "book_signing", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["reading", "quiet", "social", "community", "calming"]},
    ],
    "cairo": [
        {"title": "El Sawy Culturewheel", "description": "Daily events: music, poetry, film screenings. Under the 6th October Bridge.", "category": "cultural_center", "noise": "moderate", "social": "medium", "mood": "calming", "tags": ["culture", "music", "film", "community"]},
        {"title": "Cairo Downtown Contemporary Art Festival", "description": "Annual contemporary art across downtown galleries", "category": "exhibition", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["art", "culture", "quiet", "free"]},
    ],
    "barcelona": [
        {"title": "Primavera Sound", "description": "Major indie/alternative music festival. June annually. Parc del F\u00f2rum.", "category": "festival", "noise": "loud", "social": "high", "mood": "intense", "tags": ["music", "festival", "social", "noisy", "indie"]},
        {"title": "Open House Barcelona", "description": "Free access to normally closed architectural gems. Annual October.", "category": "exhibition", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["architecture", "culture", "free", "quiet"]},
        {"title": "Mercat de Sant Antoni Sunday Book Market", "description": "Weekly second-hand book and comics market. Sunday mornings.", "category": "market", "noise": "moderate", "social": "medium", "mood": "calming", "tags": ["books", "market", "culture", "free", "outdoor"]},
    ],
}


def get_city_places(city: str) -> list[dict[str, Any]]:
    """Get real places for a specific city."""
    return CITY_PLACES.get(city.lower(), [])


def get_city_events(city: str) -> list[dict[str, Any]]:
    """Get real events for a specific city."""
    return CITY_EVENTS.get(city.lower(), [])


def get_supported_cities() -> list[str]:
    return list(CITY_PLACES.keys())


def detect_city(text: str) -> str:
    """Try to detect city from text."""
    text_lower = text.lower()
    city_hints = {
        "dubai": ["dubai", "\u062f\u0628\u064a", "\u8fea\u62dc", "jbr", "marina", "deira"],
        "riyadh": ["riyadh", "\u0627\u0644\u0631\u064a\u0627\u0636", "\u5229\u96c5\u5f97"],
        "shanghai": ["shanghai", "\u4e0a\u6d77", "\u6d66\u4e1c", "\u5916\u6ee9"],
        "cairo": ["cairo", "\u0627\u0644\u0642\u0627\u0647\u0631\u0629", "\u5f00\u7f57", "zamalek"],
        "barcelona": ["barcelona", "\u5df4\u585e\u7f57\u90a3", "g\u00f2tic", "eixample", "raval"],
    }
    for city, hints in city_hints.items():
        if any(h in text_lower for h in hints):
            return city
    return ""
