"""
Pure-Python extraction functions that run before any LLM call.

These handle fields where deterministic code is more reliable (or as good as) an LLM:
  - states_mentioned  → regex + city-alias lookup (more reliable than LLM)
  - topics            → keyword dictionary
  - keywords          → stop-word-filtered frequency count
  - issue_category    → weighted keyword rules (returns confidence score)
  - sentiment from star rating → direct mapping, no semantics needed

These run on every article with zero API cost. LLM is called only for fields
that genuinely need semantic understanding (sentiment, entities, editorial tone).
"""

import re
from collections import Counter

# ── Indian states & UT lookup ─────────────────────────────────────────────────

_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Delhi", "Jammu & Kashmir", "Ladakh", "Chandigarh", "Puducherry",
]
_STATE_LOWER = {s.lower(): s for s in _STATES}

# Longest first so "Jammu & Kashmir" matches before "Kashmir"
_STATE_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(s) for s in sorted(_STATES, key=len, reverse=True)) + r')\b',
    re.IGNORECASE,
)

# Major city → canonical state name
_CITY_STATE: dict[str, str] = {
    "Mumbai": "Maharashtra", "Pune": "Maharashtra", "Nagpur": "Maharashtra",
    "Thane": "Maharashtra", "Nashik": "Maharashtra", "Aurangabad": "Maharashtra",
    "New Delhi": "Delhi",
    "Bangalore": "Karnataka", "Bengaluru": "Karnataka", "Mysore": "Karnataka",
    "Mysuru": "Karnataka", "Mangalore": "Karnataka", "Mangaluru": "Karnataka",
    "Hubli": "Karnataka", "Hubballi": "Karnataka",
    "Chennai": "Tamil Nadu", "Coimbatore": "Tamil Nadu", "Madurai": "Tamil Nadu",
    "Salem": "Tamil Nadu", "Tiruchirappalli": "Tamil Nadu", "Trichy": "Tamil Nadu",
    "Tirunelveli": "Tamil Nadu",
    "Hyderabad": "Telangana", "Warangal": "Telangana", "Karimnagar": "Telangana",
    "Kolkata": "West Bengal", "Howrah": "West Bengal", "Durgapur": "West Bengal",
    "Ahmedabad": "Gujarat", "Surat": "Gujarat", "Vadodara": "Gujarat",
    "Baroda": "Gujarat", "Rajkot": "Gujarat", "Gandhinagar": "Gujarat",
    "Jaipur": "Rajasthan", "Jodhpur": "Rajasthan", "Udaipur": "Rajasthan",
    "Kota": "Rajasthan", "Ajmer": "Rajasthan",
    "Lucknow": "Uttar Pradesh", "Kanpur": "Uttar Pradesh", "Varanasi": "Uttar Pradesh",
    "Agra": "Uttar Pradesh", "Allahabad": "Uttar Pradesh", "Prayagraj": "Uttar Pradesh",
    "Meerut": "Uttar Pradesh", "Ghaziabad": "Uttar Pradesh", "Noida": "Uttar Pradesh",
    "Patna": "Bihar", "Gaya": "Bihar", "Muzaffarpur": "Bihar",
    "Bhubaneswar": "Odisha", "Cuttack": "Odisha", "Rourkela": "Odisha",
    "Guwahati": "Assam", "Dibrugarh": "Assam", "Jorhat": "Assam",
    "Raipur": "Chhattisgarh", "Bilaspur": "Chhattisgarh",
    "Bhopal": "Madhya Pradesh", "Indore": "Madhya Pradesh", "Gwalior": "Madhya Pradesh",
    "Jabalpur": "Madhya Pradesh",
    "Kochi": "Kerala", "Thiruvananthapuram": "Kerala", "Trivandrum": "Kerala",
    "Kozhikode": "Kerala", "Calicut": "Kerala", "Thrissur": "Kerala",
    "Dehradun": "Uttarakhand", "Haridwar": "Uttarakhand",
    "Shimla": "Himachal Pradesh", "Manali": "Himachal Pradesh",
    "Amritsar": "Punjab", "Ludhiana": "Punjab", "Jalandhar": "Punjab",
    "Chandigarh": "Chandigarh",
    "Ranchi": "Jharkhand", "Jamshedpur": "Jharkhand", "Dhanbad": "Jharkhand",
    "Imphal": "Manipur",
    "Shillong": "Meghalaya",
    "Panaji": "Goa", "Margao": "Goa",
    "Aizawl": "Mizoram",
    "Kohima": "Nagaland",
    "Agartala": "Tripura",
    "Srinagar": "Jammu & Kashmir", "Jammu": "Jammu & Kashmir",
    "Leh": "Ladakh", "Kargil": "Ladakh",
    "Gangtok": "Sikkim",
    "Itanagar": "Arunachal Pradesh",
    "Pondicherry": "Puducherry",
}
_CITY_LOWER = {c.lower(): s for c, s in _CITY_STATE.items()}
_CITY_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(c) for c in sorted(_CITY_STATE, key=len, reverse=True)) + r')\b',
    re.IGNORECASE,
)


def extract_states_mentioned(text: str) -> list[str]:
    """Deterministic state extraction — more reliable than LLM for this task."""
    found: set[str] = set()
    for m in _STATE_PATTERN.finditer(text):
        canonical = _STATE_LOWER.get(m.group(0).lower())
        if canonical:
            found.add(canonical)
    for m in _CITY_PATTERN.finditer(text):
        state = _CITY_LOWER.get(m.group(0).lower())
        if state:
            found.add(state)
    return sorted(found)


# ── Topic extraction ──────────────────────────────────────────────────────────

_TOPIC_KWORDS: dict[str, list[str]] = {
    "product_quality": [
        "product", "quality", "defect", "recall", "safety", "hazard",
        "malfunction", "performance", "specification", "standard", "material",
    ],
    "pricing": [
        "price", "cost", "fee", "rate", "tariff", "discount", "affordable",
        "expensive", "cheap", "pricing", "hike",
    ],
    "customer_service": [
        "customer", "support", "complaint", "service", "helpline", "grievance",
        "feedback", "consumer", "response time",
    ],
    "leadership": [
        "ceo", "chairman", "board", "management", "director", "founder",
        "executive", "leadership", "resignation", "appointment", "md",
    ],
    "campaign": [
        "campaign", "advertisement", "ad", "promotion", "marketing",
        "brand", "sponsor", "endorsement", "commercial", "tv ad",
    ],
    "legal": [
        "court", "case", "lawsuit", "fir", "legal", "penalty", "sebi",
        "rbi", "enforcement", "violation", "tribunal", "notice", "probe",
    ],
    "expansion": [
        "expansion", "new market", "launch", "open", "foray",
        "acquisition", "merger", "enter", "branch",
    ],
    "financial": [
        "profit", "revenue", "loss", "earnings", "growth", "quarter",
        "annual", "fiscal", "dividend", "ipo", "stock", "shares",
    ],
}


def extract_topics(text: str) -> list[str]:
    t = text.lower()
    matched = [topic for topic, kws in _TOPIC_KWORDS.items() if any(k in t for k in kws)]
    return matched or ["other"]


# ── Keyword extraction (frequency-based) ─────────────────────────────────────

_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "that", "this", "these",
    "those", "it", "its", "he", "she", "they", "we", "you", "not", "no",
    "nor", "so", "yet", "than", "also", "said", "says", "new", "year",
    "day", "time", "more", "our", "their", "about", "which", "been",
    "after", "before", "over", "under", "such", "into", "through", "during",
})


def extract_keywords(text: str, max_k: int = 8) -> list[str]:
    words = re.findall(r'\b[a-zA-Z][a-zA-Z]{3,}\b', text.lower())
    counts = Counter(w for w in words if w not in _STOPWORDS)
    return [w for w, _ in counts.most_common(max_k)]


# ── Issue category classification (rules-first) ───────────────────────────────

_ISSUE_KWORDS: dict[str, list[str]] = {
    "financial_performance": [
        "profit", "loss", "revenue", "earnings", "quarterly results",
        "annual report", "market cap", "net income", "turnover", "fiscal year",
        "ebitda", "share price", "stock", "ipo", "dividend", "q1", "q2", "q3", "q4",
    ],
    "regulatory_compliance": [
        "sebi", "rbi", "irdai", "ministry of", "compliance", "penalty",
        "enforcement directorate", "income tax", "gst notice", "court order",
        "supreme court", "high court", "tribunal", "fir", "cbi",
        "audit report", "violation", "investigation", "probe",
    ],
    "product_quality": [
        "product quality", "defect", "recall", "safety issue", "hazard",
        "contamination", "faulty", "malfunction", "substandard",
        "quality control", "manufacturing defect", "banning",
    ],
    "leadership_governance": [
        "ceo resign", "chairman", "board meeting", "management change",
        "director appointment", "leadership change", "founder exit",
        "succession plan", "board of directors", "governance issue",
    ],
    "crisis_controversy": [
        "controversy", "scandal", "crisis", "backlash", "outrage",
        "protest", "boycott", "accused of", "fraud", "corruption",
        "scam", "allegation", "row over", "fallout", "viral outrage",
    ],
    "awards_recognition": [
        "award", "recognition", "honour", "honor", "prize", "ranked",
        "best brand", "excellence award", "milestone", "achievement",
        "accreditation", "certification", "felicitated",
    ],
    "csr_sustainability": [
        "csr", "sustainability", "environment", "carbon neutral",
        "green initiative", "social responsibility", "community",
        "ngo", "esg", "climate", "renewable energy", "charity", "donation",
    ],
    "policy_government": [
        "government policy", "union budget", "scheme", "subsidy",
        "parliament", "cabinet decision", "state government",
        "municipal", "tender", "government contract",
    ],
    "competitive_landscape": [
        "market share", "competitor", "rival brand", " vs ", "versus",
        "industry leader", "beat competition", "dethrone",
    ],
    "customer_experience": [
        "customer complaint", "consumer complaint", "poor service",
        "bad experience", "satisfied customer", "customer review",
        "nps score", "consumer feedback",
    ],
    "brand_advocacy": [
        "brand ambassador", "celebrity endorsement", "ad campaign",
        "tv commercial", "sponsorship", "brand collaboration", "influencer deal",
    ],
    "market_opportunity": [
        "new launch", "product launch", "market entry", "expansion plan",
        "investment opportunity", "new category", "upcoming product",
        "growth potential",
    ],
}


def classify_issue_category(text: str) -> tuple[str, float]:
    """
    Returns (category, confidence).
    confidence >= 0.65 → use code result, skip LLM for this field.
    confidence < 0.65  → include issue_category in LLM prompt.
    """
    t = text.lower()
    scores: dict[str, int] = {}
    for cat, kws in _ISSUE_KWORDS.items():
        n = sum(1 for k in kws if k in t)
        if n:
            scores[cat] = n

    if not scores:
        return "other", 0.25

    ranked = sorted(scores.items(), key=lambda x: -x[1])
    best_cat, best_n = ranked[0]
    second_n = ranked[1][1] if len(ranked) > 1 else 0

    if best_n >= 3:
        return best_cat, 0.88
    if best_n >= 2 and best_n > second_n:
        return best_cat, 0.75
    if best_n >= 1 and best_n > second_n:
        return best_cat, 0.60
    if best_n >= 1:
        return best_cat, 0.45

    return "other", 0.25


# ── Star rating → sentiment (Google reviews) ──────────────────────────────────

_STAR_SENTIMENT: dict[int, tuple[float, str]] = {
    5: (0.90, "positive"),
    4: (0.55, "positive"),
    3: (0.00, "neutral"),
    2: (-0.55, "negative"),
    1: (-0.90, "negative"),
}


def sentiment_from_star_rating(rating) -> tuple[float, str]:
    """Convert Google star rating (1–5) to (sentiment_score, label). Confidence: 0.95."""
    try:
        stars = max(1, min(5, round(float(rating))))
        return _STAR_SENTIMENT[stars]
    except (TypeError, ValueError):
        return 0.0, "neutral"
