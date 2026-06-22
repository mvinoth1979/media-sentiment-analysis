"""
API tier selection and client rotation for the NLP pipeline.

Routing philosophy:
  Tier 0 — Code only   : Google reviews (star→sentiment), ≤8-word comments
  Tier 1 — Groq free   : EN social comments, EN YouTube/Reddit posts, EN blogs
  Tier 2 — Gemini free : EN news articles (primary), falls back to Groq
  Tier 3 — Gemini paid : Indic-language news, AI summary, competitor discovery

This routes ~69% of calls away from the paid Gemini quota.
Paid quota is reserved for content where multilingual quality matters most.
"""

import threading
import time
import logging
from enum import Enum, auto
from typing import Optional

from google import genai
from groq import Groq
from app.config import settings

log = logging.getLogger(__name__)


class NLPTier(Enum):
    NONE         = auto()   # Code-only — no LLM call needed
    GROQ         = auto()   # Groq free tier
    GEMINI_FREE  = auto()   # Gemini free-tier key
    GEMINI_PAID  = auto()   # Gemini paid key (reserved for Indic + high-value calls)


_INDIC_LANGS    = frozenset({"ta", "hi", "gu", "bn", "kn"})
_SOCIAL_COMMENT = frozenset({"youtube_comment", "reddit_comment"})
_SOCIAL_POST    = frozenset({"youtube_video", "reddit_post"})
_REVIEW         = frozenset({"google_review"})


def select_tier(
    source_type: str,
    language: str,
    word_count: int,
    has_star: bool,
) -> NLPTier:
    """
    Choose the cheapest tier that delivers acceptable quality for this article.
    Called before language detection completes — re-call with confirmed language if needed.
    """
    # ── Tier 0: zero LLM cost ────────────────────────────────────────────────
    if source_type in _REVIEW and has_star:
        return NLPTier.NONE          # star rating → code sentiment, no LLM needed
    if word_count <= 8:
        return NLPTier.NONE          # too short for meaningful NLP

    # ── Tier 1: Groq (social, EN) ────────────────────────────────────────────
    if source_type in _SOCIAL_COMMENT:
        return NLPTier.GROQ          # short, informal; LLaMA is adequate

    if source_type in _SOCIAL_POST and language not in _INDIC_LANGS:
        return NLPTier.GROQ          # EN YT/Reddit posts — Groq handles well

    # ── Tier 3: Gemini paid (Indic language, highest accuracy needed) ────────
    if language in _INDIC_LANGS:
        return NLPTier.GEMINI_PAID

    # ── Tier 2: Gemini free (EN news — default for articles) ─────────────────
    if settings.gemini_free_api_key:
        return NLPTier.GEMINI_FREE

    # Free key not configured → use paid (graceful degradation)
    return NLPTier.GEMINI_PAID


class APIRouter:
    """
    Thread-safe singleton factory that:
    - Tracks per-key rate-limit windows
    - Provides lazy-initialised client instances
    - Round-robins across multiple Groq keys when configured
    """

    _lock = threading.Lock()
    _rate_limited_until: dict[str, float] = {}

    # Lazy client instances
    _gemini_paid_client: Optional[genai.Client] = None
    _gemini_free_client: Optional[genai.Client] = None

    # Groq pool: list of (label, client) — built once on first use
    _groq_pool: list[tuple[str, Groq]] = []
    _groq_pool_ready: bool = False
    _groq_rr: int = 0

    @classmethod
    def _available(cls, label: str) -> bool:
        return time.time() >= cls._rate_limited_until.get(label, 0)

    @classmethod
    def mark_rate_limited(cls, label: str, seconds: int = 65) -> None:
        """Call this when a 429 is received from the key identified by label."""
        with cls._lock:
            cls._rate_limited_until[label] = time.time() + seconds
        log.warning("API key '%s' rate-limited — cooling down %ds", label, seconds)

    @classmethod
    def get_gemini_client(cls, paid: bool) -> Optional[tuple[genai.Client, str]]:
        """
        Returns (client, label) if the key is configured and not rate-limited.
        Returns None otherwise — caller should try a fallback tier.
        """
        if paid:
            key, label = settings.gemini_api_key, "gemini_paid"
        else:
            key, label = settings.gemini_free_api_key, "gemini_free"

        if not key:
            return None
        if not cls._available(label):
            log.debug("Gemini '%s' still cooling down — skipping", label)
            return None

        with cls._lock:
            if paid and cls._gemini_paid_client is None:
                cls._gemini_paid_client = genai.Client(api_key=key)
            elif not paid and cls._gemini_free_client is None:
                cls._gemini_free_client = genai.Client(api_key=key)

        return (cls._gemini_paid_client if paid else cls._gemini_free_client), label

    @classmethod
    def get_groq_client(cls) -> Optional[tuple[Groq, str]]:
        """
        Returns (client, label) via round-robin across configured Groq keys.
        Returns None if no keys configured or all are rate-limited.
        """
        with cls._lock:
            if not cls._groq_pool_ready:
                keys = [k for k in [settings.groq_api_key, settings.groq_api_key_2] if k]
                cls._groq_pool = [(f"groq_{i}", Groq(api_key=k)) for i, k in enumerate(keys)]
                cls._groq_pool_ready = True

            if not cls._groq_pool:
                return None

            n = len(cls._groq_pool)
            for _ in range(n):
                idx = cls._groq_rr % n
                cls._groq_rr += 1
                label, client = cls._groq_pool[idx]
                if cls._available(label):
                    return client, label

        return None  # all Groq keys currently rate-limited


# Module-level singleton — import this everywhere
router = APIRouter()
