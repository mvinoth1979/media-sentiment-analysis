"""Tests for Item 8: ReviewQueueItem/Response and VideoRiskItem/BrandRiskScoresResponse schemas."""
import pytest
from pydantic import ValidationError


def test_review_queue_item_valid():
    from app.dashboard.schemas import ReviewQueueItem

    item = ReviewQueueItem(
        id="q-1",
        brand_id="brand-1",
        article_id="art-1",
        reason="low_confidence_crisis",
        status="pending",
        created_at="2026-06-21T00:00:00Z",
        reviewer_id=None,
        reviewed_at=None,
        article_title=None,
        article_url=None,
    )
    assert item.status == "pending"
    assert item.reviewer_id is None


def test_review_queue_item_status_values():
    from app.dashboard.schemas import ReviewQueueItem

    for status in ("pending", "approved", "rejected"):
        item = ReviewQueueItem(
            id="q-1", brand_id="b", article_id="a",
            reason="r", status=status, created_at="2026-06-21T00:00:00Z",
        )
        assert item.status == status


def test_review_queue_response_contains_items():
    from app.dashboard.schemas import ReviewQueueItem, ReviewQueueResponse

    items = [
        ReviewQueueItem(
            id=f"q-{i}", brand_id="b", article_id=f"a-{i}",
            reason="r", status="pending", created_at="2026-06-21T00:00:00Z",
        )
        for i in range(3)
    ]
    resp = ReviewQueueResponse(items=items, total=3)
    assert resp.total == 3
    assert len(resp.items) == 3


def test_video_risk_item_valid():
    from app.dashboard.schemas import VideoRiskItem

    item = VideoRiskItem(
        article_id="art-1",
        title="Test video",
        url="https://youtube.com/watch?v=abc",
        portal_id="youtube_channel_1",
        view_count=500_000,
        like_count=10_000,
        comment_count=500,
        sentiment_score=0.2,
        risk_score=-1.5,
        reach_tier="High",
        published_at="2026-06-01T00:00:00Z",
    )
    assert item.reach_tier == "High"
    assert item.risk_score == -1.5


def test_video_risk_item_reach_tier_values():
    from app.dashboard.schemas import VideoRiskItem

    for tier in ("Viral", "High", "Mid", "Low"):
        item = VideoRiskItem(
            article_id="a", title="t", url="u", portal_id="p",
            view_count=1000, like_count=10, comment_count=5,
            sentiment_score=0.5, risk_score=0.5, reach_tier=tier,
        )
        assert item.reach_tier == tier


def test_brand_risk_scores_response():
    from app.dashboard.schemas import VideoRiskItem, BrandRiskScoresResponse

    item = VideoRiskItem(
        article_id="a", title="t", url="u", portal_id="p",
        view_count=100, like_count=5, comment_count=2,
        sentiment_score=-0.5, risk_score=-0.8, reach_tier="Low",
    )
    resp = BrandRiskScoresResponse(videos=[item], brand_id="brand-1", period_days=30)
    assert resp.brand_id == "brand-1"
    assert len(resp.videos) == 1


def test_review_queue_patch_request_valid():
    from app.dashboard.schemas import ReviewQueuePatchRequest

    req = ReviewQueuePatchRequest(status="approved")
    assert req.status == "approved"


def test_review_queue_patch_request_invalid_status():
    from app.dashboard.schemas import ReviewQueuePatchRequest
    with pytest.raises(ValidationError):
        ReviewQueuePatchRequest(status="unknown_status")
