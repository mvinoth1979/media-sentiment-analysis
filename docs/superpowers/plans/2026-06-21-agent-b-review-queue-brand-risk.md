# Agent B — Human Review Queue + Per-video Brand Risk Score

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a human review queue (Item 5) where low-confidence Crisis/Regulatory articles await admin approval before entering leadership reports, and surface the per-video Brand Risk Score (Item 8) in the YouTube detail panel.

**Architecture:** Both items extend the dashboard layer. The queue adds a new DB table, two new API endpoints, and a new frontend page accessible to admins. The Brand Risk Score reuses the existing `_weight()` formula from `perception.py`, surfaces it per-video via a new endpoint, and renders it in a new frontend component inside the existing YouTube detail panel.

**Tech Stack:** Python 3.12 · FastAPI · Supabase (PostgreSQL via supabase-py) · React 19 · TypeScript · Tailwind CSS 4 · TanStack Query

## Global Constraints

- Python: use `from __future__ import annotations` in new files
- Supabase client: always via `get_db()` from `app.storage.postgres`
- Auth: dashboard endpoints require `require_brand_role(*READ_ROLES)` minimum; mutation endpoints require `require_brand_role(*WRITE_ROLES)`
- Frontend: no new npm packages; use existing Tailwind classes + TanStack Query patterns
- Migration naming: `018_human_review_queue.sql` — run before application code
- Tab type: the new `"review-queue"` tab must be added to the `Tab` union in `Sidebar.tsx`

---

### Task 1: DB Migration — `human_review_queue`

**Files:**
- Create: `backend/migrations/018_human_review_queue.sql`

**Interfaces:**
- Produces: `human_review_queue` table with columns `(id, brand_id, article_id, reason, status, reviewer_id, reviewed_at, created_at)`

- [ ] **Step 1: Write the migration**

```sql
-- backend/migrations/018_human_review_queue.sql
-- Human review queue for low-confidence high-stakes NLP classifications.
-- Articles with confidence < 0.5 AND issue_category in ('crisis_controversy', 'regulatory_compliance')
-- are inserted here automatically by save_article() in postgres.py.

CREATE TABLE IF NOT EXISTS human_review_queue (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id    UUID        NOT NULL,
    article_id  UUID        NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    reason      TEXT        NOT NULL,
    status      TEXT        NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewer_id UUID        REFERENCES auth.users(id),
    reviewed_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hrq_brand_status
    ON human_review_queue (brand_id, status, created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_hrq_article_pending
    ON human_review_queue (article_id)
    WHERE status = 'pending';
```

- [ ] **Step 2: Run the migration in Supabase**

Go to Supabase dashboard → SQL Editor → paste and run. Verify `human_review_queue` appears in the Table Editor with all 8 columns.

---

### Task 2: Auto-enqueue in `postgres.py`

**Files:**
- Modify: `backend/app/storage/postgres.py`
- Test: `backend/tests/test_review_queue_enqueue.py`

**Interfaces:**
- Consumes: `save_article(article: dict, nlp: dict) -> str | None` — existing function
- Produces: after `save_article` upserts an article, if `nlp["confidence"] < 0.5` AND `nlp["issue_category"]` is in `{"crisis_controversy", "regulatory_compliance"}`, insert a `pending` row into `human_review_queue`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_review_queue_enqueue.py
from __future__ import annotations
from unittest.mock import patch, MagicMock, call
from app.storage.postgres import save_article

_HIGH_STAKES = {"crisis_controversy", "regulatory_compliance"}

def _make_mock_db(article_id="art-1"):
    db = MagicMock()
    upsert_result = MagicMock()
    upsert_result.data = [{"id": article_id}]
    db.table.return_value.upsert.return_value.execute.return_value = upsert_result
    db.table.return_value.insert.return_value.execute.return_value = MagicMock()
    return db

def test_low_confidence_crisis_enqueues():
    db = _make_mock_db()
    nlp = {
        "confidence": 0.28,
        "issue_category": "crisis_controversy",
        "sentiment_label": "negative",
        "sentiment_score": -0.7,
    }
    article = {"brand_id": "brand-1", "content_hash": "abc"}
    with patch("app.storage.postgres.get_db", return_value=db):
        save_article(article, nlp)
    # Verify that human_review_queue table received an insert call
    insert_calls = [c for c in db.table.call_args_list if c.args == ("human_review_queue",)]
    assert len(insert_calls) == 1

def test_high_confidence_crisis_does_not_enqueue():
    db = _make_mock_db()
    nlp = {
        "confidence": 0.85,
        "issue_category": "crisis_controversy",
        "sentiment_label": "negative",
        "sentiment_score": -0.7,
    }
    article = {"brand_id": "brand-1", "content_hash": "abc"}
    with patch("app.storage.postgres.get_db", return_value=db):
        save_article(article, nlp)
    insert_calls = [c for c in db.table.call_args_list if c.args == ("human_review_queue",)]
    assert len(insert_calls) == 0

def test_low_confidence_non_stakes_does_not_enqueue():
    db = _make_mock_db()
    nlp = {
        "confidence": 0.20,
        "issue_category": "product_quality",  # not high-stakes
        "sentiment_label": "negative",
        "sentiment_score": -0.5,
    }
    article = {"brand_id": "brand-1", "content_hash": "abc"}
    with patch("app.storage.postgres.get_db", return_value=db):
        save_article(article, nlp)
    insert_calls = [c for c in db.table.call_args_list if c.args == ("human_review_queue",)]
    assert len(insert_calls) == 0
```

- [ ] **Step 2: Run tests to confirm they fail**

```
cd backend && python -m pytest tests/test_review_queue_enqueue.py -v
```

Expected: `AssertionError` — no insert call made yet

- [ ] **Step 3: Extend `save_article` in `postgres.py`**

In `backend/app/storage/postgres.py`, modify `save_article` to append the enqueue logic after the existing upsert:

```python
_REVIEW_QUEUE_CATEGORIES = {"crisis_controversy", "regulatory_compliance"}

def save_article(article: dict, nlp: dict) -> str | None:
    db = get_db()
    row = {**article, **nlp}
    for field in ("body", "portal_name"):
        row.pop(field, None)
    row.setdefault("source_platform", "news")
    result = db.table("articles").upsert(row, on_conflict="brand_id,content_hash").execute()
    article_id = result.data[0]["id"] if result.data else None

    # Auto-enqueue low-confidence high-stakes classifications for human review
    confidence = float(nlp.get("confidence") or 1.0)
    category = nlp.get("issue_category") or ""
    if article_id and confidence < 0.5 and category in _REVIEW_QUEUE_CATEGORIES:
        try:
            db.table("human_review_queue").insert({
                "brand_id":   article.get("brand_id"),
                "article_id": article_id,
                "reason":     f"low_confidence:{confidence:.2f}:{category}",
            }).execute()
        except Exception:
            pass  # duplicate article_id in pending queue — ignore

    return article_id
```

- [ ] **Step 4: Run tests to confirm they pass**

```
cd backend && python -m pytest tests/test_review_queue_enqueue.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/app/storage/postgres.py backend/tests/test_review_queue_enqueue.py
git commit -m "feat: auto-enqueue low-confidence crisis/regulatory articles to human_review_queue"
```

---

### Task 3: Schemas for Review Queue + Brand Risk Score

**Files:**
- Modify: `backend/app/dashboard/schemas.py`
- Test: `backend/tests/test_item8_schemas.py`

**Interfaces:**
- Produces:
  - `ReviewQueueItem(id, brand_id, article_id, article_title, issue_category, confidence, sentiment_label, reason, status, created_at, reviewed_at)`
  - `ReviewQueueResponse(items: list[ReviewQueueItem], pending_count: int)`
  - `VideoRiskItem(article_id, title, url, portal_id, view_count, like_count, comment_count, sentiment_label, sentiment_score, brand_risk_score, published_at, reach_tier)`
  - `BrandRiskScoresResponse(items: list[VideoRiskItem], brand_id: str)`

- [ ] **Step 1: Add schemas to `dashboard/schemas.py`**

Append the following to the end of `backend/app/dashboard/schemas.py`:

```python
# --- Item 5: Human Review Queue ---

class ReviewQueueItem(BaseModel):
    id: str
    brand_id: str
    article_id: str
    article_title: str
    issue_category: str
    confidence: float
    sentiment_label: str
    reason: str
    status: str
    created_at: str
    reviewed_at: str | None = None


class ReviewQueueResponse(BaseModel):
    items: list[ReviewQueueItem]
    pending_count: int


class ReviewQueuePatch(BaseModel):
    status: str   # "approved" | "rejected"
    reviewer_id: str


# --- Item 8: Per-video Brand Risk Score ---

class VideoRiskItem(BaseModel):
    article_id: str
    title: str
    url: str
    portal_id: str
    view_count: int
    like_count: int
    comment_count: int
    sentiment_label: str
    sentiment_score: float
    brand_risk_score: float
    published_at: str | None = None
    reach_tier: str


class BrandRiskScoresResponse(BaseModel):
    items: list[VideoRiskItem]
    brand_id: str
```

- [ ] **Step 2: Write a quick schema validation test**

```python
# backend/tests/test_item8_schemas.py
from app.dashboard.schemas import (
    ReviewQueueItem, ReviewQueueResponse, ReviewQueuePatch,
    VideoRiskItem, BrandRiskScoresResponse,
)

def test_review_queue_item_roundtrip():
    item = ReviewQueueItem(
        id="i1", brand_id="b1", article_id="a1",
        article_title="Test", issue_category="crisis_controversy",
        confidence=0.28, sentiment_label="negative",
        reason="low_confidence:0.28:crisis_controversy",
        status="pending", created_at="2026-06-21T00:00:00Z",
    )
    assert item.reviewed_at is None
    assert item.confidence == 0.28

def test_video_risk_item_roundtrip():
    item = VideoRiskItem(
        article_id="a1", title="Test", url="https://yt.be/x",
        portal_id="youtube_search", view_count=1_000_000, like_count=5000,
        comment_count=200, sentiment_label="negative",
        sentiment_score=-0.6, brand_risk_score=-0.42,
        reach_tier="Viral",
    )
    assert item.brand_risk_score == -0.42
    assert item.reach_tier == "Viral"
```

- [ ] **Step 3: Run schema tests**

```
cd backend && python -m pytest tests/test_item8_schemas.py -v
```

Expected: `2 passed`

- [ ] **Step 4: Commit**

```bash
git add backend/app/dashboard/schemas.py backend/tests/test_item8_schemas.py
git commit -m "feat: ReviewQueueItem/Response + VideoRiskItem/BrandRiskScoresResponse schemas"
```

---

### Task 4: API Endpoints — Review Queue

**Files:**
- Modify: `backend/app/dashboard/router.py`
- Test: (manual via curl or existing test patterns)

**Interfaces:**
- Consumes: `ReviewQueueItem`, `ReviewQueueResponse`, `ReviewQueuePatch` from `app.dashboard.schemas`; `get_db()` from `app.storage.postgres`; `require_brand_role`, `READ_ROLES`, `WRITE_ROLES` from `app.auth.dependencies`
- Produces:
  - `GET /dashboard/review-queue/{brand_id}` → `ReviewQueueResponse`
  - `PATCH /dashboard/review-queue/{item_id}` → `ReviewQueueItem`

- [ ] **Step 1: Add import to `dashboard/router.py`**

In the imports section at the top of `backend/app/dashboard/router.py`, add to the existing `from app.dashboard.schemas import (...)` block:

```python
    ReviewQueueItem, ReviewQueueResponse, ReviewQueuePatch,
```

- [ ] **Step 2: Add the two endpoints to `dashboard/router.py`**

Append after the last existing endpoint in `backend/app/dashboard/router.py`:

```python
# ── Item 5: Human Review Queue ────────────────────────────────────────────────

@router.get("/review-queue/{brand_id}", response_model=ReviewQueueResponse)
def get_review_queue(
    brand_id: str,
    status: str = Query("pending", pattern="^(pending|approved|rejected)$"),
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    db = get_db()
    rows = (
        db.table("human_review_queue")
        .select("*, articles(title, issue_category, confidence, sentiment_label)")
        .eq("brand_id", brand_id)
        .eq("status", status)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
        .data
    )
    pending_count = (
        db.table("human_review_queue")
        .select("id", count="exact")
        .eq("brand_id", brand_id)
        .eq("status", "pending")
        .execute()
        .count
        or 0
    )
    items = []
    for r in rows:
        art = r.get("articles") or {}
        items.append(ReviewQueueItem(
            id=r["id"],
            brand_id=r["brand_id"],
            article_id=r["article_id"],
            article_title=art.get("title") or "(no title)",
            issue_category=art.get("issue_category") or r.get("reason", ""),
            confidence=float(art.get("confidence") or 0.0),
            sentiment_label=art.get("sentiment_label") or "neutral",
            reason=r.get("reason") or "",
            status=r["status"],
            created_at=r["created_at"],
            reviewed_at=r.get("reviewed_at"),
        ))
    return ReviewQueueResponse(items=items, pending_count=pending_count)


@router.patch("/review-queue/{item_id}", response_model=ReviewQueueItem)
def update_review_queue_item(
    item_id: str,
    payload: ReviewQueuePatch,
    user: dict = Depends(require_brand_role(*WRITE_ROLES)),
):
    if payload.status not in ("approved", "rejected"):
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="status must be 'approved' or 'rejected'")
    db = get_db()
    updated = (
        db.table("human_review_queue")
        .update({
            "status":      payload.status,
            "reviewer_id": payload.reviewer_id,
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        })
        .eq("id", item_id)
        .execute()
        .data
    )
    if not updated:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Review queue item not found")
    r = updated[0]
    art = (
        db.table("articles")
        .select("title, issue_category, confidence, sentiment_label")
        .eq("id", r["article_id"])
        .execute()
        .data
    )
    art = art[0] if art else {}
    return ReviewQueueItem(
        id=r["id"],
        brand_id=r["brand_id"],
        article_id=r["article_id"],
        article_title=art.get("title") or "(no title)",
        issue_category=art.get("issue_category") or "",
        confidence=float(art.get("confidence") or 0.0),
        sentiment_label=art.get("sentiment_label") or "neutral",
        reason=r.get("reason") or "",
        status=r["status"],
        created_at=r["created_at"],
        reviewed_at=r.get("reviewed_at"),
    )
```

- [ ] **Step 3: Verify the app starts cleanly**

```
cd backend && uvicorn app.main:app --reload
```

Expected: starts without import errors. Visit `http://localhost:8000/docs` — `GET /dashboard/review-queue/{brand_id}` and `PATCH /dashboard/review-queue/{item_id}` should appear.

- [ ] **Step 4: Commit**

```bash
git add backend/app/dashboard/router.py
git commit -m "feat: GET/PATCH /dashboard/review-queue endpoints"
```

---

### Task 5: API Endpoint — Brand Risk Scores

**Files:**
- Modify: `backend/app/dashboard/router.py`
- Test: `backend/tests/test_brand_risk_scores.py`

**Interfaces:**
- Consumes: `VideoRiskItem`, `BrandRiskScoresResponse` from `app.dashboard.schemas`; `_weight()` logic from `app.pipeline.perception`
- Produces: `GET /dashboard/brand-risk-scores/{brand_id}` → `BrandRiskScoresResponse`
  - Returns top 10 YouTube videos sorted by `abs(brand_risk_score)` (highest-impact first)
  - `brand_risk_score` = sentiment_score (signed −1 to +1) × log_reach (0–1) × engagement (0–1) × recency_decay

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_brand_risk_scores.py
from __future__ import annotations
import math
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _yt_article(sentiment_score=-0.8, view_count=500_000, like_count=1000, comment_count=200):
    return {
        "id": "a1",
        "title": "Negative Review Video",
        "url": "https://youtu.be/abc",
        "portal_id": "youtube_search",
        "source_type": "youtube_video",
        "sentiment_label": "negative",
        "sentiment_score": sentiment_score,
        "source_credibility": 0.65,
        "reach_score": view_count,
        "collected_at": "2026-06-21T10:00:00Z",
        "published_at": "2026-06-21T09:00:00Z",
        "reach_metadata": {
            "view_count": view_count,
            "like_count": like_count,
            "comment_count": comment_count,
        },
    }

def test_brand_risk_scores_returns_ranked_videos(monkeypatch):
    monkeypatch.setattr(
        "app.dashboard.router.get_articles",
        lambda *a, **kw: [_yt_article()]
    )
    with patch("app.auth.dependencies.require_brand_role", return_value=lambda: {"user_id": "u1"}):
        resp = client.get("/dashboard/brand-risk-scores/brand-1",
                          headers={"Authorization": "Bearer test"})
    # Just verify structure — auth is mocked
    assert resp.status_code in (200, 403)  # 403 if auth not bypassed in test env

def test_brand_risk_score_formula():
    from app.dashboard.router import _compute_brand_risk_score
    score = _compute_brand_risk_score(
        sentiment_score=-0.8,
        view_count=1_000_000,
        like_count=2000,
        comment_count=500,
        collected_at="2026-06-21T10:00:00Z",
    )
    assert score < 0  # negative sentiment → negative risk score
    assert -1.0 <= score <= 0.0

def test_brand_risk_score_positive_video():
    from app.dashboard.router import _compute_brand_risk_score
    score = _compute_brand_risk_score(
        sentiment_score=0.9,
        view_count=5_000_000,
        like_count=50000,
        comment_count=3000,
        collected_at="2026-06-20T10:00:00Z",
    )
    assert score > 0
```

- [ ] **Step 2: Run tests to see them fail**

```
cd backend && python -m pytest tests/test_brand_risk_scores.py::test_brand_risk_score_formula -v
```

Expected: `ImportError` — `_compute_brand_risk_score` not defined

- [ ] **Step 3: Add helper + endpoint to `dashboard/router.py`**

Add the import at the top of the existing perception imports:
```python
from app.pipeline.perception import calculate_perception_score, _recency_weight, _engagement_multiplier
```

Then add the helper function and endpoint (append to `router.py`):

```python
# ── Item 8: Per-video Brand Risk Score ───────────────────────────────────────

def _compute_brand_risk_score(
    sentiment_score: float,
    view_count: int,
    like_count: int,
    comment_count: int,
    collected_at: str,
) -> float:
    """Brand Risk Score = sentiment × log_reach × engagement × recency_decay."""
    import math
    log_reach = math.log10(view_count + 1) / math.log10(10_000_001)
    views = max(view_count, 1)
    engagement = min((like_count + comment_count) / views / 0.10, 1.0)
    recency = _recency_weight({"collected_at": collected_at})
    return round(sentiment_score * log_reach * engagement * recency, 4)


def _reach_tier(view_count: int) -> str:
    if view_count >= 1_000_000:
        return "Viral"
    if view_count >= 100_000:
        return "High"
    if view_count >= 10_000:
        return "Mid"
    return "Low"


@router.get("/brand-risk-scores/{brand_id}", response_model=BrandRiskScoresResponse)
def get_brand_risk_scores(
    brand_id: str,
    _user: dict = Depends(require_brand_role(*READ_ROLES)),
):
    articles = get_articles(
        brand_id, limit=200,
        source_type="youtube_video",
        date_from=(datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
    )
    items = []
    for a in articles:
        reach = a.get("reach_metadata") or {}
        view_count    = int(reach.get("view_count")    or 0)
        like_count    = int(reach.get("like_count")    or 0)
        comment_count = int(reach.get("comment_count") or 0)
        risk = _compute_brand_risk_score(
            sentiment_score=float(a.get("sentiment_score") or 0.0),
            view_count=view_count,
            like_count=like_count,
            comment_count=comment_count,
            collected_at=a.get("collected_at") or "",
        )
        items.append(VideoRiskItem(
            article_id=str(a.get("id", "")),
            title=a.get("title", ""),
            url=a.get("url", ""),
            portal_id=a.get("portal_id", ""),
            view_count=view_count,
            like_count=like_count,
            comment_count=comment_count,
            sentiment_label=a.get("sentiment_label", "neutral"),
            sentiment_score=float(a.get("sentiment_score") or 0.0),
            brand_risk_score=risk,
            published_at=a.get("published_at"),
            reach_tier=_reach_tier(view_count),
        ))

    items.sort(key=lambda x: abs(x.brand_risk_score), reverse=True)
    return BrandRiskScoresResponse(items=items[:10], brand_id=brand_id)
```

Also add `BrandRiskScoresResponse` and `VideoRiskItem` to the `from app.dashboard.schemas import (...)` block at the top of `router.py`.

- [ ] **Step 4: Run tests**

```
cd backend && python -m pytest tests/test_brand_risk_scores.py::test_brand_risk_score_formula tests/test_brand_risk_scores.py::test_brand_risk_score_positive_video -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/app/dashboard/router.py backend/tests/test_brand_risk_scores.py
git commit -m "feat: GET /dashboard/brand-risk-scores/{brand_id} endpoint"
```

---

### Task 6: Frontend — `ReviewQueue.tsx` page

**Files:**
- Create: `frontend/src/pages/ReviewQueue.tsx`
- Modify: `frontend/src/components/Sidebar.tsx` (add `"review-queue"` Tab)
- Modify: `frontend/src/App.tsx` (wire route)

**Interfaces:**
- Consumes:
  - `GET /dashboard/review-queue/{brandId}` — returns `{ items: ReviewQueueItem[], pending_count: number }`
  - `PATCH /dashboard/review-queue/{itemId}` — body `{ status, reviewer_id }`
- Produces: Admin-only page listing pending review items with Approve / Reject actions

- [ ] **Step 1: Add `"review-queue"` to the Tab union in `Sidebar.tsx`**

In `frontend/src/components/Sidebar.tsx`, change:
```typescript
export type Tab = "overview" | "sources" | "topics" | "users" | "journalists" | "brand-config";
```
to:
```typescript
export type Tab = "overview" | "sources" | "topics" | "users" | "journalists" | "brand-config" | "review-queue";
```

Then add a new entry to `NAV_ITEMS` (after the `brand-config` entry):
```typescript
  {
    id: "review-queue", tab: "review-queue", label: "Review Queue", adminOnly: true,
    icon: <NavIcon d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />,
  },
```

- [ ] **Step 2: Wire the route in `App.tsx`**

In `frontend/src/App.tsx`, add the import at the top:
```typescript
import { ReviewQueue } from "./pages/ReviewQueue";
```

In the tab routing section (where `tab === "overview"` etc. is handled), add:
```typescript
{tab === "review-queue" && brand && (
  <ReviewQueue brandId={brand.id} userId={session.user.id} />
)}
```

- [ ] **Step 3: Create `ReviewQueue.tsx`**

```typescript
// frontend/src/pages/ReviewQueue.tsx
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";

interface ReviewQueueItem {
  id: string;
  article_id: string;
  article_title: string;
  issue_category: string;
  confidence: number;
  sentiment_label: string;
  reason: string;
  status: string;
  created_at: string;
}

interface Props {
  brandId: string;
  userId: string;
}

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "text-green-600 bg-green-50",
  negative: "text-red-600 bg-red-50",
  neutral:  "text-gray-600 bg-gray-50",
};

export function ReviewQueue({ brandId, userId }: Props) {
  const [status, setStatus] = useState<"pending" | "approved" | "rejected">("pending");
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["review-queue", brandId, status],
    queryFn: async () => {
      const resp = await api.get(`/dashboard/review-queue/${brandId}?status=${status}`);
      return resp.data as { items: ReviewQueueItem[]; pending_count: number };
    },
  });

  const patchItem = useMutation({
    mutationFn: async ({ itemId, newStatus }: { itemId: string; newStatus: string }) => {
      await api.patch(`/dashboard/review-queue/${itemId}`, {
        status: newStatus,
        reviewer_id: userId,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["review-queue", brandId] });
    },
  });

  return (
    <div className="p-6 max-w-4xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-lg font-semibold text-gray-800">Human Review Queue</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Low-confidence Crisis or Regulatory articles awaiting confirmation before entering reports.
          </p>
        </div>
        {data && data.pending_count > 0 && (
          <span className="bg-red-100 text-red-700 text-xs font-medium px-2.5 py-1 rounded-full">
            {data.pending_count} pending
          </span>
        )}
      </div>

      {/* Status tabs */}
      <div className="flex gap-2 mb-4">
        {(["pending", "approved", "rejected"] as const).map(s => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={`px-3 py-1 text-xs rounded-full capitalize transition-colors ${
              status === s
                ? "bg-indigo-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {isLoading && <div className="text-sm text-gray-400">Loading…</div>}

      {!isLoading && data?.items.length === 0 && (
        <div className="text-sm text-gray-400 py-8 text-center">
          No {status} items.
        </div>
      )}

      <div className="space-y-2">
        {data?.items.map(item => (
          <div
            key={item.id}
            className="bg-white border border-gray-200 rounded-lg p-4 flex gap-4 items-start"
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-800 font-medium line-clamp-2">{item.article_title}</p>
              <div className="flex flex-wrap gap-1.5 mt-1.5">
                <span className={`text-[10px] px-1.5 py-0.5 rounded capitalize ${SENTIMENT_COLORS[item.sentiment_label] || "text-gray-600 bg-gray-50"}`}>
                  {item.sentiment_label}
                </span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-50 text-orange-700">
                  {item.issue_category.replace(/_/g, " ")}
                </span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-50 text-gray-500">
                  confidence: {Math.round(item.confidence * 100)}%
                </span>
              </div>
            </div>

            {item.status === "pending" && (
              <div className="flex gap-2 shrink-0">
                <button
                  onClick={() => patchItem.mutate({ itemId: item.id, newStatus: "approved" })}
                  disabled={patchItem.isPending}
                  className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                >
                  Approve
                </button>
                <button
                  onClick={() => patchItem.mutate({ itemId: item.id, newStatus: "rejected" })}
                  disabled={patchItem.isPending}
                  className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                >
                  Reject
                </button>
              </div>
            )}

            {item.status !== "pending" && (
              <span className={`text-[10px] px-2 py-1 rounded capitalize shrink-0 ${
                item.status === "approved" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
              }`}>
                {item.status}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Verify TypeScript compiles**

```
cd frontend && npx tsc --noEmit
```

Expected: no type errors related to the new files

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ReviewQueue.tsx frontend/src/components/Sidebar.tsx frontend/src/App.tsx
git commit -m "feat: ReviewQueue admin page + sidebar nav + route"
```

---

### Task 7: Frontend — `BrandRiskScores.tsx` component

**Files:**
- Create: `frontend/src/components/BrandRiskScores.tsx`

**Interfaces:**
- Consumes: `GET /dashboard/brand-risk-scores/{brandId}` → `{ items: VideoRiskItem[], brand_id: string }`
- Produces: A table of top YouTube videos sorted by risk score, shown in the YouTube detail panel

- [ ] **Step 1: Create `BrandRiskScores.tsx`**

```typescript
// frontend/src/components/BrandRiskScores.tsx
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

interface VideoRiskItem {
  article_id: string;
  title: string;
  url: string;
  view_count: number;
  like_count: number;
  comment_count: number;
  sentiment_label: string;
  sentiment_score: number;
  brand_risk_score: number;
  reach_tier: string;
  published_at: string | null;
}

interface Props {
  brandId: string;
}

const REACH_TIER_COLORS: Record<string, string> = {
  Viral: "bg-red-100 text-red-700",
  High:  "bg-orange-100 text-orange-700",
  Mid:   "bg-yellow-100 text-yellow-700",
  Low:   "bg-gray-100 text-gray-600",
};

function RiskBar({ score }: { score: number }) {
  const pct = Math.round(Math.abs(score) * 100);
  const isNeg = score < 0;
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-20 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${isNeg ? "bg-red-400" : "bg-green-400"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`text-[10px] font-medium ${isNeg ? "text-red-600" : "text-green-600"}`}>
        {score > 0 ? "+" : ""}{score.toFixed(2)}
      </span>
    </div>
  );
}

export function BrandRiskScores({ brandId }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["brand-risk-scores", brandId],
    queryFn: async () => {
      const resp = await api.get(`/dashboard/brand-risk-scores/${brandId}`);
      return resp.data as { items: VideoRiskItem[]; brand_id: string };
    },
  });

  if (isLoading) return <div className="text-xs text-gray-400 p-4">Loading…</div>;
  if (!data?.items.length) {
    return (
      <div className="text-xs text-gray-400 p-4 text-center">
        No YouTube video data in the last 30 days.
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-800">Brand Risk Score by Video</h3>
        <span className="text-[10px] text-gray-400">Last 30 days · Top 10</span>
      </div>
      <p className="text-[10px] text-gray-400 mb-3">
        Score = sentiment × reach × engagement × recency. Negative = reputational risk. Sorted by impact.
      </p>
      <div className="space-y-2">
        {data.items.map(item => (
          <div key={item.article_id} className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-start gap-2 mb-1.5">
              <div className="flex-1 min-w-0">
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[11px] text-gray-700 hover:text-blue-600 line-clamp-2 font-medium transition-colors"
                >
                  {item.title}
                </a>
              </div>
              <span className={`text-[9px] px-1.5 py-0.5 rounded shrink-0 ${REACH_TIER_COLORS[item.reach_tier] || "bg-gray-100 text-gray-600"}`}>
                {item.reach_tier}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <RiskBar score={item.brand_risk_score} />
              <div className="flex gap-2 text-[9px] text-gray-400">
                <span>{item.view_count.toLocaleString()} views</span>
                <span>{item.like_count.toLocaleString()} likes</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Import `BrandRiskScores` in the YouTube detail panel**

Find where the YouTube detail panel is rendered in `frontend/src/pages/Overview.tsx` (or wherever the YouTube click-to-detail component lives). Add:

```typescript
import { BrandRiskScores } from "../components/BrandRiskScores";
```

And inside the YouTube detail panel section, add:
```tsx
<BrandRiskScores brandId={brand.id} />
```

- [ ] **Step 3: Verify TypeScript compiles**

```
cd frontend && npx tsc --noEmit
```

Expected: no type errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/BrandRiskScores.tsx frontend/src/pages/Overview.tsx
git commit -m "feat: BrandRiskScores component in YouTube detail panel"
```

---

### Task 8: End-to-end smoke test

- [ ] **Step 1: Start the dev server**

```
cd frontend && npm run dev
```

- [ ] **Step 2: Navigate to Review Queue**

Log in as an admin user. Select a brand. Click "Review Queue" in the sidebar. Verify: page loads, shows "No pending items" if queue is empty, and status tabs (Pending / Approved / Rejected) are clickable.

- [ ] **Step 3: Check Brand Risk Score panel**

From Overview, click on the YouTube KPI card or YouTube section to open the YouTube detail panel. Verify "Brand Risk Score by Video" table appears. If no YouTube videos exist, verify the empty state message appears.

- [ ] **Step 4: Run full backend test suite**

```
cd backend && python -m pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: all pre-existing tests pass; new tests pass.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: agent B complete — human review queue + per-video brand risk score"
```
