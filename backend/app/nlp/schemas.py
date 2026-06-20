from dataclasses import dataclass, field


@dataclass
class NLPResult:
    sentiment_score: float          # -1.0 to +1.0  (overall, body-weighted for news)
    sentiment_label: str            # "positive" | "negative" | "neutral"
    entities: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    states_mentioned: list[str] = field(default_factory=list)
    model_used: str = ""
    confidence: float = 0.0
    source_type: str = "news"       # pass-through from article

    # A2: headline vs. body sentiment (news only; None for YouTube)
    headline_sentiment_score: float | None = None
    body_sentiment_score: float | None = None

    # B1: editorial framing (set alongside A2 in the same Gemini call)
    editorial_tone: str = ""        # "factual" | "positive_frame" | "negative_frame" | "critical"

    # Structured issue taxonomy (12 categories)
    issue_category: str = "other"

    def to_dict(self) -> dict:
        hs = self.headline_sentiment_score
        bs = self.body_sentiment_score
        divergence = (
            abs(hs - bs) >= 0.4
            if hs is not None and bs is not None
            else False
        )
        return {
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "entities": self.entities,
            "topics": self.topics,
            "keywords": self.keywords,
            "states_mentioned": self.states_mentioned,
            "model_used": self.model_used,
            "confidence": self.confidence,
            "source_type": self.source_type,
            "headline_sentiment_score": hs,
            "body_sentiment_score": bs,
            "sentiment_divergence": divergence,
            "editorial_tone": self.editorial_tone,
            "issue_category": self.issue_category,
        }
