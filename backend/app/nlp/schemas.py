from dataclasses import dataclass, field


@dataclass
class NLPResult:
    sentiment_score: float          # -1.0 to +1.0
    sentiment_label: str            # "positive" | "negative" | "neutral"
    entities: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    states_mentioned: list[str] = field(default_factory=list)
    model_used: str = ""
    confidence: float = 0.0
    source_type: str = "news"       # pass-through from article — "news" | "youtube_video" | "youtube_comment"

    def to_dict(self) -> dict:
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
        }
