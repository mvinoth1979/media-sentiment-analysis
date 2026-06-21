# Agent A — Virality Baseline + Review Clustering Alert

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add rolling-baseline virality detection for YouTube videos (Item 3) and a review-clustering alert that fires when 3+ negative articles share an issue category within 14 days (Item 7).

**Architecture:** Both items are alert-system extensions. A new `virality_detector.py` module handles per-video metric snapshots and baseline comparison. Both new alert types (`virality_spike`, `review_cluster`) plug into the existing `check_and_fire_alerts()` switch in `alerts.py` alongside the 5 existing alert types. No orchestrator changes needed — `check_and_fire_alerts` already runs at the end of every pipeline run.

**Tech Stack:** Python 3.12 · FastAPI · Supabase (PostgreSQL via supabase-py) · APScheduler · Resend email API

## Global Constraints

- Python: use `from __future__ import annotations` in new files
- Supabase client: always via `get_db()` from `app.storage.postgres`
- Config: settings from `app.config.settings`; never hardcode keys
- Resend email: `settings.resend_api_key` — skip silently if None
- Alert cooldown: existing 4h (`_COOLDOWN_HOURS`) applies to new alert types
- Migration naming: `017_video_metrics_history.sql` — run before application code

---

### Task 1: DB Migration — `video_metrics_history`

**Files:**
- Create: `backend/migrations/017_video_metrics_history.sql`
- Test: manual verification via Supabase dashboard

**Interfaces:**
- Produces: `video_metrics_history` table with columns `(id, article_id, brand_id, snapshot_date, view_count, comment_count, negative_count, created_at)`

- [ ] **Step 1: Write the migration file**

```sql
-- backend/migrations/017_video_metrics_history.sql
-- Daily metric snapshots for YouTube videos — used for rolling baseline virality detection.
-- Unique on (article_id, snapshot_date) so daily pipeline reruns are idempotent.

CREATE TABLE IF NOT EXISTS video_metrics_history (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id    UUID        NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    brand_id      UUID        NOT NULL,
    snapshot_date DATE        NOT NULL DEFAULT CURRENT_DATE,
    view_count    BIGINT      NOT NULL DEFAULT 0,
    comment_count INT         NOT NULL DEFAULT 0,
    negative_count INT        NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (article_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_vmh_brand_date
    ON video_metrics_history (brand_id, snapshot_date DESC);

CREATE INDEX IF NOT EXISTS idx_vmh_article
    ON video_metrics_history (article_id, snapshot_date DESC);
```

- [ ] **Step 2: Run the migration in Supabase**

Go to Supabase dashboard → SQL Editor → paste and run the migration. Verify the `video_metrics_history` table appears in the Table Editor.

---

### Task 2: `virality_detector.py` — Snapshot + Baseline Detection

**Files:**
- Create: `backend/app/pipeline/virality_detector.py`
- Test: `backend/tests/test_virality.py`

**Interfaces:**
- Consumes: `get_db()` from `app.storage.postgres`
- Produces:
  - `detect_virality(brand_id: str) -> list[dict]`
    Returns list of `{"article_id", "title", "flag_level": int, "triggered_metrics": list[str]}` for videos that exceeded 3× their 7-day rolling average on any metric.
  - `snapshot_and_detect(brand_id: str) -> list[dict]`
    Alias that callers (alerts.py) should use — identical to `detect_virality`.

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_virality.py
from __future__ import annotations
from unittest.mock import patch, MagicMock
from app.pipeline.virality_detector import detect_virality


def _make_article(article_id="a1", view_count=1000, comment_count=50, negative_count=5):
    return {
        "id": article_id,
        "title": "Test Video",
        "source_type": "youtube_video",
        "sentiment_label": "negative",
        "reach_metadata": {
            "view_count": view_count,
            "comment_count": comment_count,
        },
    }


def _make_history(article_id="a1", days=7, base_views=100, base_comments=10, base_neg=1):
    return [
        {
            "article_id": article_id,
            "snapshot_date": f"2026-06-{14+i:02d}",
            "view_count": base_views,
            "comment_count": base_comments,
            "negative_count": base_neg,
        }
        for i in range(days)
    ]


def test_no_videos_returns_empty():
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
    with patch("app.pipeline.virality_detector.get_db", return_value=db):
        assert detect_virality("brand-123") == []


def test_video_exceeding_3x_baseline_is_flagged():
    article = _make_article(view_count=400)  # 4× baseline of 100
    history = _make_history(base_views=100, base_comments=10, base_neg=1)
    db = MagicMock()
    articles_mock = MagicMock()
    articles_mock.data = [article]
    history_mock = MagicMock()
    history_mock.data = history

    def table_side_effect(name):
        m = MagicMock()
        if name == "articles":
            m.select.return_value.eq.return_value.eq.return_value.gte.return_value.execute.return_value = articles_mock
        else:
            m.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value = history_mock
        return m

    db.table.side_effect = table_side_effect
    with patch("app.pipeline.virality_detector.get_db", return_value=db):
        result = detect_virality("brand-123")

    assert len(result) == 1
    assert result[0]["flag_level"] >= 1
    assert "views" in result[0]["triggered_metrics"]


def test_video_below_3x_baseline_not_flagged():
    article = _make_article(view_count=250)  # 2.5× baseline — below threshold
    history = _make_history(base_views=100)
    db = MagicMock()
    articles_mock = MagicMock()
    articles_mock.data = [article]
    history_mock = MagicMock()
    history_mock.data = history

    def table_side_effect(name):
        m = MagicMock()
        if name == "articles":
            m.select.return_value.eq.return_value.eq.return_value.gte.return_value.execute.return_value = articles_mock
        else:
            m.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value = history_mock
        return m

    db.table.side_effect = table_side_effect
    with patch("app.pipeline.virality_detector.get_db", return_value=db):
        result = detect_virality("brand-123")

    assert result == []


def test_flag_level_3_when_all_metrics_triggered():
    article = _make_article(view_count=400, comment_count=50, negative_count=5)
    history = _make_history(base_views=100, base_comments=10, base_neg=1)
    db = MagicMock()
    articles_mock = MagicMock()
    articles_mock.data = [article]
    history_mock = MagicMock()
    history_mock.data = history

    def table_side_effect(name):
        m = MagicMock()
        if name == "articles":
            m.select.return_value.eq.return_value.eq.return_value.gte.return_value.execute.return_value = articles_mock
        else:
            m.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value = history_mock
        return m

    db.table.side_effect = table_side_effect
    with patch("app.pipeline.virality_detector.get_db", return_value=db):
        result = detect_virality("brand-123")

    assert result[0]["flag_level"] == 3
```

- [ ] **Step 2: Run tests to confirm they fail**

```
cd backend && python -m pytest tests/test_virality.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.pipeline.virality_detector'`

- [ ] **Step 3: Implement `virality_detector.py`**

```python
# backend/app/pipeline/virality_detector.py
from __future__ import annotations
import logging
from datetime import date, datetime, timedelta, timezone
from app.storage.postgres import get_db

log = logging.getLogger(__name__)

_VIRALITY_MULTIPLIER = 3.0
_LOOKBACK_DAYS = 7
_LOOKBACK_ARTICLE_DAYS = 30


def detect_virality(brand_id: str) -> list[dict]:
    """Snapshot today's metrics for all YT videos and return those exceeding 3× 7-day avg."""
    db = get_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=_LOOKBACK_ARTICLE_DAYS)).isoformat()

    articles = (
        db.table("articles")
        .select("id, title, reach_metadata, sentiment_label")
        .eq("brand_id", brand_id)
        .eq("source_type", "youtube_video")
        .gte("collected_at", cutoff)
        .execute()
        .data
    )

    triggered: list[dict] = []

    for article in articles:
        article_id = article["id"]
        reach = article.get("reach_metadata") or {}
        today_views    = int(reach.get("view_count")    or 0)
        today_comments = int(reach.get("comment_count") or 0)
        today_negative = 1 if article.get("sentiment_label") == "negative" else 0

        history_cutoff = (date.today() - timedelta(days=_LOOKBACK_DAYS)).isoformat()
        history = (
            db.table("video_metrics_history")
            .select("view_count, comment_count, negative_count")
            .eq("article_id", article_id)
            .gte("snapshot_date", history_cutoff)
            .order("snapshot_date", desc=True)
            .limit(_LOOKBACK_DAYS)
            .execute()
            .data
        )

        _upsert_snapshot(db, article_id, brand_id, today_views, today_comments, today_negative)

        if not history:
            continue

        avg_views    = sum(h["view_count"]    for h in history) / len(history)
        avg_comments = sum(h["comment_count"] for h in history) / len(history)
        avg_negative = sum(h["negative_count"] for h in history) / len(history)

        triggered_metrics: list[str] = []
        if avg_views    > 0 and today_views    > avg_views    * _VIRALITY_MULTIPLIER:
            triggered_metrics.append("views")
        if avg_comments > 0 and today_comments > avg_comments * _VIRALITY_MULTIPLIER:
            triggered_metrics.append("comments")
        if avg_negative > 0 and today_negative > avg_negative * _VIRALITY_MULTIPLIER:
            triggered_metrics.append("negative")

        if triggered_metrics:
            triggered.append({
                "article_id": article_id,
                "title": (article.get("title") or "")[:80],
                "flag_level": len(triggered_metrics),
                "triggered_metrics": triggered_metrics,
            })

    return triggered


def _upsert_snapshot(db, article_id: str, brand_id: str,
                     view_count: int, comment_count: int, negative_count: int) -> None:
    try:
        db.table("video_metrics_history").upsert(
            {
                "article_id":    article_id,
                "brand_id":      brand_id,
                "snapshot_date": date.today().isoformat(),
                "view_count":    view_count,
                "comment_count": comment_count,
                "negative_count": negative_count,
            },
            on_conflict="article_id,snapshot_date",
        ).execute()
    except Exception as e:
        log.warning("Failed to upsert virality snapshot for %s: %s", article_id[:8], e)
```

- [ ] **Step 4: Run tests to confirm they pass**

```
cd backend && python -m pytest tests/test_virality.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/migrations/017_video_metrics_history.sql backend/app/pipeline/virality_detector.py backend/tests/test_virality.py
git commit -m "feat: virality detector — daily YT metric snapshots + 3x baseline detection"
```

---

### Task 3: `alerts.py` — Add `virality_spike` + `review_cluster` Alert Types

**Files:**
- Modify: `backend/app/storage/alerts.py`
- Test: `backend/tests/test_alerts_virality.py`

**Interfaces:**
- Consumes: `detect_virality(brand_id)` from `app.pipeline.virality_detector` — returns `list[dict]` with `flag_level: int`
- Produces: Two new alert types (`virality_spike`, `review_cluster`) recognized by `check_and_fire_alerts()`. Threshold for `virality_spike` = minimum flag_level (1=emerging, 2=risk, 3=crisis). Threshold for `review_cluster` = minimum negative article count (default 3).

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_alerts_virality.py
from __future__ import annotations
from unittest.mock import patch, MagicMock
from app.storage.alerts import _check_virality, _check_review_cluster


def test_check_virality_returns_none_when_no_triggers():
    with patch("app.storage.alerts.detect_virality", return_value=[]):
        result = _check_virality("brand-1", threshold=1)
    assert result is None


def test_check_virality_returns_highest_flagged_video():
    videos = [
        {"title": "Video A", "flag_level": 1, "triggered_metrics": ["views"]},
        {"title": "Video B", "flag_level": 3, "triggered_metrics": ["views", "comments", "negative"]},
    ]
    with patch("app.storage.alerts.detect_virality", return_value=videos):
        result = _check_virality("brand-1", threshold=1)
    assert result is not None
    val, ctx = result
    assert val == 3.0
    assert "Video B" in ctx


def test_check_virality_filters_below_threshold():
    videos = [{"title": "V", "flag_level": 1, "triggered_metrics": ["views"]}]
    with patch("app.storage.alerts.detect_virality", return_value=videos):
        result = _check_virality("brand-1", threshold=2)
    assert result is None


def test_check_review_cluster_returns_none_when_below_threshold():
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.neq.return_value.not_.return_value.is_.return_value.execute.return_value.data = [
        {"issue_category": "product_quality"},
        {"issue_category": "product_quality"},
    ]
    with patch("app.storage.alerts.get_db", return_value=db):
        result = _check_review_cluster("brand-1", threshold=3)
    assert result is None


def test_check_review_cluster_returns_category_when_at_threshold():
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.neq.return_value.not_.return_value.is_.return_value.execute.return_value.data = [
        {"issue_category": "customer_experience"},
        {"issue_category": "customer_experience"},
        {"issue_category": "customer_experience"},
    ]
    with patch("app.storage.alerts.get_db", return_value=db):
        result = _check_review_cluster("brand-1", threshold=3)
    assert result is not None
    val, ctx = result
    assert val == 3.0
    assert "customer_experience" in ctx
```

- [ ] **Step 2: Run tests to confirm they fail**

```
cd backend && python -m pytest tests/test_alerts_virality.py -v
```

Expected: `ImportError` — `_check_virality` not defined in alerts.py

- [ ] **Step 3: Add `_check_virality` to `alerts.py`**

Add this import at the top of `backend/app/storage/alerts.py` (after the existing imports):

```python
from app.pipeline.virality_detector import detect_virality
```

Add this function after `_check_journalist_beat` (around line 80):

```python
# ── Item 3: Virality spike check ──────────────────────────────────────────────

def _check_virality(brand_id: str, threshold: int) -> tuple[float, str] | None:
    """Return (flag_level, video_title) for the highest-flagged video at or above threshold."""
    try:
        videos = detect_virality(brand_id)
    except Exception as e:
        log.warning("Virality check failed for %s: %s", brand_id[:8], e)
        return None
    if not videos:
        return None
    above = [v for v in videos if v["flag_level"] >= threshold]
    if not above:
        return None
    best = max(above, key=lambda v: v["flag_level"])
    label = {1: "Emerging Issue", 2: "Reputation Risk", 3: "Crisis Alert"}.get(best["flag_level"], "Alert")
    metrics = " + ".join(best["triggered_metrics"])
    return float(best["flag_level"]), f"{best['title']} [{label}: {metrics}]"


# ── Item 7: Review cluster check ──────────────────────────────────────────────

def _check_review_cluster(brand_id: str, threshold: int) -> tuple[float, str] | None:
    """Return (count, category) if any issue_category has >= threshold negative articles in 14 days."""
    from collections import Counter
    db = get_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    rows = (
        db.table("articles")
        .select("issue_category")
        .eq("brand_id", brand_id)
        .eq("sentiment_label", "negative")
        .gte("collected_at", cutoff)
        .neq("issue_category", "other")
        .not_.is_("issue_category", "null")
        .execute()
        .data
    )
    if not rows:
        return None
    counts = Counter(r["issue_category"] for r in rows if r.get("issue_category"))
    if not counts:
        return None
    top_cat, top_count = counts.most_common(1)[0]
    if top_count >= threshold:
        return float(top_count), top_cat
    return None
```

- [ ] **Step 4: Add new alert types to `_ALERT_META` in `alerts.py`**

Add these two entries to the existing `_ALERT_META` dict (after the `journalist_beat` entry):

```python
    "virality_spike": {
        "subject": "Virality Spike Alert",
        "value_label": "Video going viral",
        "detail_fn": lambda v, ctx, thr: (
            f"A YouTube video has exceeded 3× its 7-day baseline on multiple metrics — "
            f"<strong style='color:#f87171'>{ctx}</strong>"
        ),
    },
    "review_cluster": {
        "subject": "Review Cluster Alert",
        "value_label": "Issue cluster detected",
        "detail_fn": lambda v, ctx, thr: (
            f"<strong style='color:#f87171'>{v:.0f} negative mentions</strong> of "
            f"<strong>{ctx.replace('_', ' ').title()}</strong> in the last 14 days "
            f"(threshold: {thr:.0f})"
        ),
    },
```

- [ ] **Step 5: Wire new types into `check_and_fire_alerts`**

In `check_and_fire_alerts()`, add these two branches in the `for cfg in configs` loop (after the `elif alert_type == "journalist_beat"` block):

```python
        elif alert_type == "virality_spike":
            result = _check_virality(brand_id, int(threshold))
            if result:
                current_value, extra_context = result

        elif alert_type == "review_cluster":
            result = _check_review_cluster(brand_id, int(threshold))
            if result:
                current_value, extra_context = result
```

- [ ] **Step 6: Run all tests**

```
cd backend && python -m pytest tests/test_alerts_virality.py tests/test_virality.py -v
```

Expected: `9 passed`

- [ ] **Step 7: Commit**

```bash
git add backend/app/storage/alerts.py backend/tests/test_alerts_virality.py
git commit -m "feat: virality_spike + review_cluster alert types in alerts.py"
```

---

### Task 4: Smoke-test end-to-end on staging

- [ ] **Step 1: Create a `virality_spike` alert config for a test brand**

Via Supabase SQL editor:
```sql
INSERT INTO alert_configs (brand_id, alert_type, threshold, notify_email, enabled)
VALUES ('<your-brand-uuid>', 'virality_spike', 1, 'test@example.com', true);
```

- [ ] **Step 2: Trigger a pipeline run**

```
POST /pipeline/trigger   Authorization: Bearer <master_admin_token>
```

- [ ] **Step 3: Verify snapshot written**

```sql
SELECT * FROM video_metrics_history WHERE brand_id = '<your-brand-uuid>' ORDER BY created_at DESC LIMIT 5;
```

Expected: rows with today's date and view/comment counts from `reach_metadata`.

- [ ] **Step 4: Create a `review_cluster` alert and verify it fires**

```sql
INSERT INTO alert_configs (brand_id, alert_type, threshold, notify_email, enabled)
VALUES ('<your-brand-uuid>', 'review_cluster', 3, 'test@example.com', true);
```

Run pipeline again. Check logs for `Alert email sent` if 3+ negative articles share an issue_category in the last 14 days.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: agent A complete — virality_spike + review_cluster alerts live"
```
