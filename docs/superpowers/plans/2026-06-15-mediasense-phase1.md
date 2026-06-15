# MediaSense Phase 1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working multi-tenant media perception platform that collects English + Tamil news portal articles hourly, analyses sentiment via Gemini 2.0 Flash (Groq fallback), stores results in Supabase + InfluxDB + Cloudflare R2, and serves an interactive React dashboard.

**Architecture:** RSS collectors → Upstash Redis queue → NLP router (Gemini primary / Groq fallback) → Supabase (metadata) + InfluxDB (timeseries) + R2 (raw archive) → FastAPI → React SPA.

**Tech Stack:** Python 3.12, FastAPI, feedparser, fasttext, google-genai, groq, supabase-py, influxdb-client, boto3, redis, APScheduler · React 18, TypeScript, Vite, Recharts, TanStack Query · Supabase, InfluxDB Cloud, Cloudflare R2, Upstash Redis, Railway, Vercel.

---

## Project File Map

```
mediasense/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── config.py                # Pydantic settings (all env vars)
│   │   ├── auth/
│   │   │   ├── dependencies.py      # JWT verification via Supabase
│   │   │   └── router.py            # /auth endpoints (verify token)
│   │   ├── tenants/
│   │   │   ├── models.py            # SQLAlchemy: Agency, Brand, BrandConfig
│   │   │   ├── schemas.py           # Pydantic request/response schemas
│   │   │   └── router.py            # /agencies, /brands CRUD
│   │   ├── ingestion/
│   │   │   ├── portals.py           # Portal registry: RSS URLs + credibility
│   │   │   ├── rss_collector.py     # feedparser fetch + keyword filter
│   │   │   └── deduplication.py     # SHA-256 hash dedupe via Supabase
│   │   ├── nlp/
│   │   │   ├── language_detector.py # fasttext lid.176 wrapper
│   │   │   ├── gemini_handler.py    # Gemini 2.0 Flash sentiment
│   │   │   ├── groq_handler.py      # Groq Gemma2-9b fallback
│   │   │   ├── router.py            # NLP router: detect → dispatch → fallback
│   │   │   └── schemas.py           # NLPResult dataclass
│   │   ├── pipeline/
│   │   │   ├── worker.py            # Upstash Redis queue consumer
│   │   │   ├── orchestrator.py      # collect → dedupe → nlp → store per brand
│   │   │   ├── perception.py        # Perception score (0–100) calculator
│   │   │   └── scheduler.py         # APScheduler hourly cron
│   │   ├── storage/
│   │   │   ├── postgres.py          # Supabase article + sentiment writes/reads
│   │   │   ├── influxdb.py          # InfluxDB timeseries writes/reads
│   │   │   └── r2.py                # Cloudflare R2 raw article archive
│   │   └── dashboard/
│   │       ├── router.py            # /dashboard endpoints
│   │       └── schemas.py           # Dashboard response schemas
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_portals.py
│   │   ├── test_rss_collector.py
│   │   ├── test_deduplication.py
│   │   ├── test_language_detector.py
│   │   ├── test_gemini_handler.py
│   │   ├── test_groq_handler.py
│   │   ├── test_nlp_router.py
│   │   ├── test_perception.py
│   │   ├── test_orchestrator.py
│   │   └── test_dashboard_api.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── lib/
│   │   │   ├── api.ts               # Axios API client
│   │   │   ├── supabase.ts          # Supabase auth client
│   │   │   └── types.ts             # Shared TS types
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useDashboard.ts
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Overview.tsx
│   │   │   ├── MentionExplorer.tsx
│   │   │   ├── Sources.tsx
│   │   │   └── Topics.tsx
│   │   └── components/
│   │       ├── layout/TopNav.tsx
│   │       ├── charts/SentimentTrendChart.tsx
│   │       ├── charts/SourceBreakdownChart.tsx
│   │       ├── cards/KPICard.tsx
│   │       └── ui/SentimentBadge.tsx
│   ├── package.json
│   └── vite.config.ts
└── supabase/
    └── migrations/
        ├── 001_schema.sql
        └── 002_rls.sql
```

---

## Milestone 1 — Foundation

### Task 1: Project Scaffold

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/app/config.py`

- [ ] **Step 1: Create backend directory and requirements**

```
backend/requirements.txt
```
```
fastapi==0.115.5
uvicorn[standard]==0.32.1
pydantic-settings==2.6.1
feedparser==6.0.11
httpx==0.27.2
google-genai==1.12.1
groq==0.13.1
supabase==2.10.0
influxdb-client==1.45.0
boto3==1.35.74
redis==5.2.1
APScheduler==3.10.4
python-jose[cryptography]==3.3.0
python-multipart==0.0.12
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-mock==3.14.0
httpx==0.27.2
```

- [ ] **Step 2: Create `.env.example`**

```
backend/.env.example
```
```bash
# Supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# InfluxDB Cloud
INFLUXDB_URL=https://us-east-1-1.aws.cloud2.influxdata.com
INFLUXDB_TOKEN=your-token==
INFLUXDB_ORG=your-org-name
INFLUXDB_BUCKET=mediasense

# Cloudflare R2
R2_ACCOUNT_ID=abc123
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret
R2_BUCKET_NAME=mediasense-raw

# Upstash Redis
UPSTASH_REDIS_HOST=your-host.upstash.io
UPSTASH_REDIS_PORT=6379
UPSTASH_REDIS_PASSWORD=your-password

# NLP APIs
GEMINI_API_KEY=AIza...
GROQ_API_KEY=gsk_...

# App
SECRET_KEY=change-me-32-chars-minimum
ENVIRONMENT=development
```

- [ ] **Step 3: Create `app/config.py`**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    influxdb_url: str
    influxdb_token: str
    influxdb_org: str
    influxdb_bucket: str = "mediasense"

    r2_account_id: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket_name: str = "mediasense-raw"

    upstash_redis_host: str
    upstash_redis_port: int = 6379
    upstash_redis_password: str

    gemini_api_key: str
    groq_api_key: str

    secret_key: str
    environment: str = "development"

settings = Settings()
```

- [ ] **Step 4: Install dependencies and verify**

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python -c "import fastapi, feedparser, groq; print('OK')"
```
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git init
git add backend/requirements.txt backend/.env.example backend/app/config.py
git commit -m "feat: project scaffold and configuration"
```

---

### Task 2: Supabase Schema + Row-Level Security

**Files:**
- Create: `supabase/migrations/001_schema.sql`
- Create: `supabase/migrations/002_rls.sql`

- [ ] **Step 1: Write schema migration**

```sql
-- supabase/migrations/001_schema.sql

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE agencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE brands (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agency_id UUID REFERENCES agencies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE brand_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id UUID UNIQUE REFERENCES brands(id) ON DELETE CASCADE,
    keywords TEXT[] NOT NULL DEFAULT '{}',
    languages TEXT[] NOT NULL DEFAULT '{"en","ta"}',
    states TEXT[] NOT NULL DEFAULT '{}',
    portal_ids TEXT[] NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    agency_id UUID REFERENCES agencies(id),
    brand_id UUID REFERENCES brands(id),
    role TEXT NOT NULL CHECK (role IN ('agency_admin','agency_analyst','brand_admin','brand_viewer')),
    UNIQUE(user_id, brand_id),
    UNIQUE(user_id, agency_id)
);

CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id UUID NOT NULL REFERENCES brands(id),
    content_hash TEXT NOT NULL,
    portal_id TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    author TEXT,
    published_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    language TEXT,
    language_confidence FLOAT,
    sentiment_score FLOAT,
    sentiment_label TEXT CHECK (sentiment_label IN ('positive','negative','neutral')),
    entities TEXT[] DEFAULT '{}',
    topics TEXT[] DEFAULT '{}',
    keywords TEXT[] DEFAULT '{}',
    source_credibility FLOAT,
    reach_score INT DEFAULT 0,
    model_used TEXT,
    UNIQUE(brand_id, content_hash)
);

CREATE INDEX idx_articles_brand_collected ON articles(brand_id, collected_at DESC);
CREATE INDEX idx_articles_sentiment ON articles(brand_id, sentiment_label);
CREATE INDEX idx_articles_language ON articles(brand_id, language);

CREATE TABLE dedupe_hashes (
    content_hash TEXT NOT NULL,
    brand_id UUID NOT NULL REFERENCES brands(id),
    seen_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (content_hash, brand_id)
);
```

- [ ] **Step 2: Write RLS migration**

```sql
-- supabase/migrations/002_rls.sql

ALTER TABLE agencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE brands ENABLE ROW LEVEL SECURITY;
ALTER TABLE brand_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;

-- Agencies: visible to agency members
CREATE POLICY "agency members can view their agency"
ON agencies FOR SELECT
USING (id IN (
    SELECT agency_id FROM user_roles WHERE user_id = auth.uid()
));

-- Brands: visible if user has a role for that brand or parent agency
CREATE POLICY "users can view brands they have access to"
ON brands FOR SELECT
USING (
    id IN (SELECT brand_id FROM user_roles WHERE user_id = auth.uid())
    OR agency_id IN (SELECT agency_id FROM user_roles WHERE user_id = auth.uid())
);

-- Articles: scoped to brand
CREATE POLICY "users can view articles for their brands"
ON articles FOR SELECT
USING (
    brand_id IN (SELECT brand_id FROM user_roles WHERE user_id = auth.uid())
    OR brand_id IN (
        SELECT b.id FROM brands b
        JOIN user_roles ur ON ur.agency_id = b.agency_id
        WHERE ur.user_id = auth.uid()
    )
);
```

- [ ] **Step 3: Apply migrations via Supabase dashboard**

In the Supabase dashboard → SQL Editor, run `001_schema.sql` then `002_rls.sql`. Verify in Table Editor that all tables exist.

- [ ] **Step 4: Commit**

```bash
git add supabase/
git commit -m "feat: supabase schema and row-level security"
```

---

### Task 3: Portal Registry

**Files:**
- Create: `backend/app/ingestion/portals.py`
- Create: `backend/tests/test_portals.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_portals.py
from app.ingestion.portals import PORTALS, get_portal, get_portals_for_languages

def test_portals_have_required_fields():
    for p in PORTALS:
        assert "id" in p
        assert "name" in p
        assert "rss_url" in p
        assert "language" in p
        assert "credibility" in p
        assert 0.0 <= p["credibility"] <= 1.0

def test_get_portal_by_id():
    portal = get_portal("the_hindu")
    assert portal is not None
    assert portal["language"] == "en"

def test_get_portals_for_languages_english():
    portals = get_portals_for_languages(["en"])
    assert all(p["language"] == "en" for p in portals)
    assert len(portals) >= 5

def test_get_portals_for_languages_tamil():
    portals = get_portals_for_languages(["ta"])
    assert all(p["language"] == "ta" for p in portals)
    assert len(portals) >= 4

def test_get_portals_for_both_languages():
    portals = get_portals_for_languages(["en", "ta"])
    langs = {p["language"] for p in portals}
    assert "en" in langs and "ta" in langs
```

- [ ] **Step 2: Run — verify FAIL**

```bash
cd backend && pytest tests/test_portals.py -v
```
Expected: `ModuleNotFoundError: No module named 'app.ingestion.portals'`

- [ ] **Step 3: Implement portal registry**

```python
# backend/app/ingestion/portals.py
from typing import Optional

PORTALS: list[dict] = [
    # English portals
    {"id": "the_hindu",       "name": "The Hindu",         "language": "en", "credibility": 0.92,
     "rss_url": "https://www.thehindu.com/feeder/default.rss"},
    {"id": "times_of_india",  "name": "Times of India",    "language": "en", "credibility": 0.85,
     "rss_url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"},
    {"id": "ndtv",            "name": "NDTV",              "language": "en", "credibility": 0.88,
     "rss_url": "https://feeds.feedburner.com/ndtvnews-top-stories"},
    {"id": "india_today",     "name": "India Today",       "language": "en", "credibility": 0.84,
     "rss_url": "https://www.indiatoday.in/rss/home"},
    {"id": "the_news_minute", "name": "The News Minute",   "language": "en", "credibility": 0.82,
     "rss_url": "https://www.thenewsminute.com/feeds/rss"},
    {"id": "deccan_herald",   "name": "Deccan Herald",     "language": "en", "credibility": 0.80,
     "rss_url": "https://www.deccanherald.com/rss-feeds/news.rss"},
    {"id": "the_wire",        "name": "The Wire",          "language": "en", "credibility": 0.81,
     "rss_url": "https://thewire.in/feed"},
    {"id": "economic_times",  "name": "Economic Times",    "language": "en", "credibility": 0.86,
     "rss_url": "https://economictimes.indiatimes.com/rssfeedstopstories.cms"},
    # Tamil portals
    {"id": "dinamalar",       "name": "Dinamalar",         "language": "ta", "credibility": 0.88,
     "rss_url": "https://www.dinamalar.com/rss/top_news_rss.asp"},
    {"id": "dinamani",        "name": "Dinamani",          "language": "ta", "credibility": 0.85,
     "rss_url": "https://www.dinamani.com/rss/"},
    {"id": "dina_thanthi",    "name": "Dina Thanthi",      "language": "ta", "credibility": 0.86,
     "rss_url": "https://www.dinathanthi.com/feed/"},
    {"id": "vikatan",         "name": "Vikatan",           "language": "ta", "credibility": 0.83,
     "rss_url": "https://www.vikatan.com/rss/all-news.xml"},
    {"id": "puthiya_thalaimurai", "name": "Puthiya Thalaimurai", "language": "ta", "credibility": 0.80,
     "rss_url": "https://www.puthiyathalaimurai.com/feed/"},
    {"id": "kalakkal_news",   "name": "Kalakkal News",     "language": "ta", "credibility": 0.72,
     "rss_url": "https://www.kalakkal.com/feed/"},
    {"id": "tamil_samayam",   "name": "Tamil Samayam",     "language": "ta", "credibility": 0.82,
     "rss_url": "https://tamil.samayam.com/feeds/rss/index.cms"},
]

_portal_index: dict[str, dict] = {p["id"]: p for p in PORTALS}

def get_portal(portal_id: str) -> Optional[dict]:
    return _portal_index.get(portal_id)

def get_portals_for_languages(languages: list[str]) -> list[dict]:
    return [p for p in PORTALS if p["language"] in languages]
```

- [ ] **Step 4: Run — verify PASS**

```bash
pytest tests/test_portals.py -v
```
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add app/ingestion/portals.py tests/test_portals.py
git commit -m "feat: news portal registry with credibility scores"
```

---

## Milestone 2 — Ingestion Pipeline

### Task 4: RSS Collector

**Files:**
- Create: `backend/app/ingestion/rss_collector.py`
- Create: `backend/tests/test_rss_collector.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_rss_collector.py
from unittest.mock import patch, MagicMock
from app.ingestion.rss_collector import collect_portal, keyword_matches

def test_keyword_matches_exact():
    assert keyword_matches("Amul launches new product", ["Amul"]) is True

def test_keyword_matches_case_insensitive():
    assert keyword_matches("AMUL dairy products", ["amul"]) is True

def test_keyword_matches_no_match():
    assert keyword_matches("Cricket match results", ["Amul", "dairy"]) is False

def test_keyword_matches_partial_word_excluded():
    # "Amul" should not match "Ramul"
    assert keyword_matches("Ramul is a name", ["\\bAmul\\b"]) is False

def test_collect_portal_returns_articles(tmp_path):
    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_entry = MagicMock()
    mock_entry.title = "Amul announces price cut"
    mock_entry.link = "https://thehindu.com/story/1"
    mock_entry.get.side_effect = lambda k, d=None: {
        "summary": "Amul reduced prices by 5%",
        "author": "Staff Reporter",
        "published": "Mon, 15 Jun 2026 10:00:00 +0000",
    }.get(k, d)
    mock_feed.entries = [mock_entry]

    with patch("app.ingestion.rss_collector.feedparser.parse", return_value=mock_feed):
        articles = collect_portal(
            portal={"id": "the_hindu", "name": "The Hindu",
                    "rss_url": "https://rss.url", "language": "en", "credibility": 0.92},
            keywords=["Amul"],
            brand_id="brand-uuid-123"
        )

    assert len(articles) == 1
    assert articles[0]["title"] == "Amul announces price cut"
    assert articles[0]["portal_id"] == "the_hindu"
    assert articles[0]["brand_id"] == "brand-uuid-123"

def test_collect_portal_filters_non_matching():
    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_entry = MagicMock()
    mock_entry.title = "Cricket World Cup preview"
    mock_entry.link = "https://thehindu.com/story/2"
    mock_entry.get.side_effect = lambda k, d=None: {"summary": "India vs Australia"}.get(k, d)
    mock_feed.entries = [mock_entry]

    with patch("app.ingestion.rss_collector.feedparser.parse", return_value=mock_feed):
        articles = collect_portal(
            portal={"id": "the_hindu", "name": "The Hindu",
                    "rss_url": "https://rss.url", "language": "en", "credibility": 0.92},
            keywords=["Amul"],
            brand_id="brand-uuid-123"
        )

    assert len(articles) == 0
```

- [ ] **Step 2: Run — verify FAIL**

```bash
pytest tests/test_rss_collector.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement RSS collector**

```python
# backend/app/ingestion/rss_collector.py
import re
import hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import feedparser

def keyword_matches(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    for kw in keywords:
        pattern = kw if kw.startswith("\\b") else re.escape(kw.lower())
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False

def _parse_date(entry) -> datetime:
    raw = entry.get("published") or entry.get("updated", "")
    try:
        return parsedate_to_datetime(raw).astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

def collect_portal(portal: dict, keywords: list[str], brand_id: str) -> list[dict]:
    try:
        feed = feedparser.parse(portal["rss_url"])
    except Exception:
        return []

    articles = []
    for entry in feed.entries:
        title = getattr(entry, "title", "") or ""
        body = entry.get("summary", "") or entry.get("content", [{}])[0].get("value", "")
        combined = f"{title} {body}"

        if not keyword_matches(combined, keywords):
            continue

        url = entry.get("link", "")
        content_hash = hashlib.sha256(f"{portal['id']}::{url}".encode()).hexdigest()

        articles.append({
            "brand_id": brand_id,
            "content_hash": content_hash,
            "portal_id": portal["id"],
            "portal_name": portal["name"],
            "url": url,
            "title": title,
            "body": body,
            "author": entry.get("author", ""),
            "published_at": _parse_date(entry).isoformat(),
            "language": portal["language"],
            "source_credibility": portal["credibility"],
        })

    return articles
```

- [ ] **Step 4: Run — verify PASS**

```bash
pytest tests/test_rss_collector.py -v
```
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add app/ingestion/rss_collector.py tests/test_rss_collector.py
git commit -m "feat: RSS collector with keyword filtering and content hashing"
```

---

### Task 5: Deduplication

**Files:**
- Create: `backend/app/ingestion/deduplication.py`
- Create: `backend/tests/test_deduplication.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_deduplication.py
from unittest.mock import MagicMock, patch
from app.ingestion.deduplication import filter_new_articles

def _make_articles(hashes: list[str]) -> list[dict]:
    return [{"content_hash": h, "brand_id": "b1", "title": f"Article {h}"} for h in hashes]

def test_all_new_articles_pass_through():
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.in_.return_value.execute.return_value.data = []

    with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
        result = filter_new_articles(_make_articles(["hash1", "hash2"]), "b1")

    assert len(result) == 2

def test_seen_articles_are_filtered():
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.in_.return_value.execute.return_value.data = [
        {"content_hash": "hash1"}
    ]

    with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
        result = filter_new_articles(_make_articles(["hash1", "hash2"]), "b1")

    assert len(result) == 1
    assert result[0]["content_hash"] == "hash2"

def test_empty_input_returns_empty():
    mock_db = MagicMock()
    with patch("app.ingestion.deduplication.get_supabase", return_value=mock_db):
        result = filter_new_articles([], "b1")
    assert result == []
```

- [ ] **Step 2: Run — verify FAIL**

```bash
pytest tests/test_deduplication.py -v
```

- [ ] **Step 3: Implement deduplication**

```python
# backend/app/ingestion/deduplication.py
from supabase import create_client, Client
from app.config import settings

def get_supabase() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)

def filter_new_articles(articles: list[dict], brand_id: str) -> list[dict]:
    if not articles:
        return []

    db = get_supabase()
    hashes = [a["content_hash"] for a in articles]

    seen = db.table("dedupe_hashes") \
             .select("content_hash") \
             .in_("content_hash", hashes) \
             .execute().data

    seen_set = {r["content_hash"] for r in seen}
    new_articles = [a for a in articles if a["content_hash"] not in seen_set]

    if new_articles:
        db.table("dedupe_hashes").insert([
            {"content_hash": a["content_hash"], "brand_id": brand_id}
            for a in new_articles
        ]).execute()

    return new_articles
```

- [ ] **Step 4: Run — verify PASS**

```bash
pytest tests/test_deduplication.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/ingestion/deduplication.py tests/test_deduplication.py
git commit -m "feat: article deduplication via Supabase hash table"
```

---

## Milestone 3 — NLP Layer

### Task 6: Language Detector

**Files:**
- Create: `backend/app/nlp/language_detector.py`
- Create: `backend/tests/test_language_detector.py`

- [ ] **Step 1: Download fasttext model**

```bash
# Run once to download the language detection model (~900MB)
python -c "
import urllib.request, os
os.makedirs('models', exist_ok=True)
url = 'https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin'
print('Downloading fasttext lid.176.bin ...')
urllib.request.urlretrieve(url, 'models/lid.176.bin')
print('Done')
"
```

- [ ] **Step 2: Write failing tests**

```python
# backend/tests/test_language_detector.py
from app.nlp.language_detector import detect_language

def test_detects_english():
    lang, conf = detect_language("The company announced record profits this quarter.")
    assert lang == "en"
    assert conf > 0.8

def test_detects_tamil():
    lang, conf = detect_language("நிறுவனம் இந்த காலாண்டில் சாதனை லாபத்தை அறிவித்தது.")
    assert lang == "ta"
    assert conf > 0.8

def test_short_text_returns_result():
    lang, conf = detect_language("hello")
    assert isinstance(lang, str)
    assert 0.0 <= conf <= 1.0

def test_empty_text_returns_unknown():
    lang, conf = detect_language("")
    assert lang == "unknown"
    assert conf == 0.0
```

- [ ] **Step 3: Implement language detector**

```python
# backend/app/nlp/language_detector.py
import os
import fasttext

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "models", "lid.176.bin")
_model = None

def _get_model():
    global _model
    if _model is None:
        fasttext.FastText.eprint = lambda x: None  # suppress warnings
        _model = fasttext.load_model(_MODEL_PATH)
    return _model

def detect_language(text: str) -> tuple[str, float]:
    if not text or not text.strip():
        return "unknown", 0.0
    model = _get_model()
    clean = text.replace("\n", " ").strip()[:500]
    labels, probs = model.predict(clean, k=1)
    lang = labels[0].replace("__label__", "")
    return lang, float(probs[0])
```

- [ ] **Step 4: Run — verify PASS**

```bash
pytest tests/test_language_detector.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/nlp/language_detector.py tests/test_language_detector.py models/.gitkeep
git commit -m "feat: fasttext language detection (lid.176)"
```

---

### Task 7: NLP Schemas

**Files:**
- Create: `backend/app/nlp/schemas.py`

- [ ] **Step 1: Create shared NLP output schema**

```python
# backend/app/nlp/schemas.py
from dataclasses import dataclass, field

@dataclass
class NLPResult:
    sentiment_score: float          # -1.0 to +1.0
    sentiment_label: str            # "positive" | "negative" | "neutral"
    entities: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    model_used: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "entities": self.entities,
            "topics": self.topics,
            "keywords": self.keywords,
            "model_used": self.model_used,
            "confidence": self.confidence,
        }
```

- [ ] **Step 2: Commit**

```bash
git add app/nlp/schemas.py
git commit -m "feat: NLP result schema"
```

---

### Task 8: Gemini NLP Handler

**Files:**
- Create: `backend/app/nlp/gemini_handler.py`
- Create: `backend/tests/test_gemini_handler.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_gemini_handler.py
import json
from unittest.mock import patch, MagicMock
from app.nlp.gemini_handler import analyse_with_gemini
from app.nlp.schemas import NLPResult

MOCK_RESPONSE = json.dumps({
    "sentiment_score": 0.75,
    "sentiment_label": "positive",
    "entities": ["Amul", "Chennai"],
    "topics": ["product_launch", "pricing"],
    "keywords": ["new", "product", "affordable"],
    "confidence": 0.91
})

def test_gemini_returns_nlp_result():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = MOCK_RESPONSE

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result = analyse_with_gemini("Amul launches affordable product in Chennai", "en")

    assert isinstance(result, NLPResult)
    assert result.sentiment_label == "positive"
    assert result.sentiment_score == 0.75
    assert "Amul" in result.entities
    assert result.model_used == "gemini-2.0-flash"

def test_gemini_handles_invalid_json():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = "not json"

    with patch("app.nlp.gemini_handler._get_client", return_value=mock_client):
        result = analyse_with_gemini("Some text", "en")

    assert result is None
```

- [ ] **Step 2: Run — verify FAIL**

```bash
pytest tests/test_gemini_handler.py -v
```

- [ ] **Step 3: Implement Gemini handler**

```python
# backend/app/nlp/gemini_handler.py
import json
from google import genai
from app.config import settings
from app.nlp.schemas import NLPResult

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client

_PROMPT = """Analyse the sentiment of the following news article text for the brand/product mentions it contains.

Return ONLY valid JSON with this exact schema:
{{
  "sentiment_score": <float from -1.0 (very negative) to +1.0 (very positive)>,
  "sentiment_label": <"positive" | "negative" | "neutral">,
  "entities": [<named entities: brands, people, locations, products>],
  "topics": [<topics from: product_quality, pricing, customer_service, leadership, campaign, legal, expansion, financial, other>],
  "keywords": [<up to 8 significant keywords>],
  "confidence": <float 0.0 to 1.0>
}}

Article language: {language}
Article text:
{text}"""

def analyse_with_gemini(text: str, language: str) -> NLPResult | None:
    prompt = _PROMPT.format(language=language, text=text[:3000])
    try:
        response = _get_client().models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        data = json.loads(raw)
        return NLPResult(
            sentiment_score=float(data["sentiment_score"]),
            sentiment_label=data["sentiment_label"],
            entities=data.get("entities", []),
            topics=data.get("topics", []),
            keywords=data.get("keywords", []),
            model_used="gemini-2.0-flash",
            confidence=float(data.get("confidence", 0.0)),
        )
    except Exception:
        return None
```

- [ ] **Step 4: Run — verify PASS**

```bash
pytest tests/test_gemini_handler.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/nlp/gemini_handler.py tests/test_gemini_handler.py
git commit -m "feat: Gemini 2.0 Flash NLP handler"
```

---

### Task 9: Groq Fallback Handler

**Files:**
- Create: `backend/app/nlp/groq_handler.py`
- Create: `backend/tests/test_groq_handler.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_groq_handler.py
import json
from unittest.mock import patch, MagicMock
from app.nlp.groq_handler import analyse_with_groq
from app.nlp.schemas import NLPResult

MOCK_RESPONSE = json.dumps({
    "sentiment_score": -0.6,
    "sentiment_label": "negative",
    "entities": ["Amul"],
    "topics": ["pricing"],
    "keywords": ["price", "hike", "expensive"],
    "confidence": 0.82
})

def test_groq_returns_nlp_result():
    mock_choice = MagicMock()
    mock_choice.message.content = MOCK_RESPONSE
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value.choices = [mock_choice]

    with patch("app.nlp.groq_handler._get_client", return_value=mock_client):
        result = analyse_with_groq("Amul hikes prices again", "en")

    assert isinstance(result, NLPResult)
    assert result.sentiment_label == "negative"
    assert result.model_used == "groq-gemma2-9b-it"

def test_groq_returns_none_on_failure():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API error")

    with patch("app.nlp.groq_handler._get_client", return_value=mock_client):
        result = analyse_with_groq("Some text", "ta")

    assert result is None
```

- [ ] **Step 2: Run — verify FAIL**

```bash
pytest tests/test_groq_handler.py -v
```

- [ ] **Step 3: Implement Groq handler**

```python
# backend/app/nlp/groq_handler.py
import json
from groq import Groq
from app.config import settings
from app.nlp.schemas import NLPResult

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client

_SYSTEM = (
    "You are a sentiment analysis engine. "
    "Return ONLY valid JSON. No explanation, no markdown, no code fences."
)

_USER = """Analyse sentiment of this news article text for brand/product mentions.

Return JSON: {{"sentiment_score": float -1 to 1, "sentiment_label": "positive"|"negative"|"neutral",
"entities": [strings], "topics": [strings], "keywords": [strings], "confidence": float 0-1}}

Language: {language}
Text: {text}"""

def analyse_with_groq(text: str, language: str) -> NLPResult | None:
    try:
        resp = _get_client().chat.completions.create(
            model="gemma2-9b-it",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": _USER.format(language=language, text=text[:2000])},
            ],
            temperature=0.1,
            max_tokens=512,
        )
        raw = resp.choices[0].message.content.strip()
        data = json.loads(raw)
        return NLPResult(
            sentiment_score=float(data["sentiment_score"]),
            sentiment_label=data["sentiment_label"],
            entities=data.get("entities", []),
            topics=data.get("topics", []),
            keywords=data.get("keywords", []),
            model_used="groq-gemma2-9b-it",
            confidence=float(data.get("confidence", 0.0)),
        )
    except Exception:
        return None
```

- [ ] **Step 4: Run — verify PASS**

```bash
pytest tests/test_groq_handler.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/nlp/groq_handler.py tests/test_groq_handler.py
git commit -m "feat: Groq Gemma2-9b fallback NLP handler"
```

---

### Task 10: NLP Router

**Files:**
- Create: `backend/app/nlp/router.py`
- Create: `backend/tests/test_nlp_router.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_nlp_router.py
from unittest.mock import patch, MagicMock
from app.nlp.router import analyse_article
from app.nlp.schemas import NLPResult

def _mock_result(label: str, model: str) -> NLPResult:
    return NLPResult(sentiment_score=0.5, sentiment_label=label,
                     model_used=model, confidence=0.9)

def test_english_article_uses_gemini():
    with patch("app.nlp.router.analyse_with_gemini",
               return_value=_mock_result("positive", "gemini-2.0-flash")) as mock_g, \
         patch("app.nlp.router.detect_language", return_value=("en", 0.99)):
        result = analyse_article({"body": "Amul profits rise", "title": "Amul up", "language": "en"})

    assert result.model_used == "gemini-2.0-flash"
    mock_g.assert_called_once()

def test_tamil_article_uses_gemini():
    with patch("app.nlp.router.analyse_with_gemini",
               return_value=_mock_result("negative", "gemini-2.0-flash")), \
         patch("app.nlp.router.detect_language", return_value=("ta", 0.97)):
        result = analyse_article({"body": "அமுல் விலை", "title": "விலை", "language": "ta"})

    assert result is not None

def test_gemini_failure_falls_back_to_groq():
    with patch("app.nlp.router.analyse_with_gemini", return_value=None), \
         patch("app.nlp.router.analyse_with_groq",
               return_value=_mock_result("neutral", "groq-gemma2-9b-it")), \
         patch("app.nlp.router.detect_language", return_value=("en", 0.99)):
        result = analyse_article({"body": "Some text", "title": "Title", "language": "en"})

    assert result.model_used == "groq-gemma2-9b-it"

def test_both_fail_returns_none():
    with patch("app.nlp.router.analyse_with_gemini", return_value=None), \
         patch("app.nlp.router.analyse_with_groq", return_value=None), \
         patch("app.nlp.router.detect_language", return_value=("en", 0.9)):
        result = analyse_article({"body": "text", "title": "t", "language": "en"})

    assert result is None
```

- [ ] **Step 2: Run — verify FAIL**

```bash
pytest tests/test_nlp_router.py -v
```

- [ ] **Step 3: Implement NLP router**

```python
# backend/app/nlp/router.py
from app.nlp.language_detector import detect_language
from app.nlp.gemini_handler import analyse_with_gemini
from app.nlp.groq_handler import analyse_with_groq
from app.nlp.schemas import NLPResult

SUPPORTED_LANGUAGES = {"en", "ta"}

def analyse_article(article: dict) -> NLPResult | None:
    text = f"{article.get('title', '')} {article.get('body', '')}".strip()
    declared_lang = article.get("language", "")

    detected_lang, lang_conf = detect_language(text)
    language = detected_lang if lang_conf > 0.75 else declared_lang

    if language not in SUPPORTED_LANGUAGES:
        language = "en"

    result = analyse_with_gemini(text, language)
    if result is None:
        result = analyse_with_groq(text, language)

    return result
```

- [ ] **Step 4: Run — verify PASS**

```bash
pytest tests/test_nlp_router.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/nlp/router.py tests/test_nlp_router.py
git commit -m "feat: NLP router with Gemini primary and Groq fallback"
```

---

## Milestone 4 — Storage + Perception Score

### Task 11: Perception Score Calculator

**Files:**
- Create: `backend/app/pipeline/perception.py`
- Create: `backend/tests/test_perception.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_perception.py
from app.pipeline.perception import calculate_perception_score

def test_all_positive_gives_high_score():
    articles = [
        {"sentiment_score": 0.9, "source_credibility": 0.9, "reach_score": 5000},
        {"sentiment_score": 0.8, "source_credibility": 0.85, "reach_score": 3000},
    ]
    score = calculate_perception_score(articles)
    assert score > 70

def test_all_negative_gives_low_score():
    articles = [
        {"sentiment_score": -0.9, "source_credibility": 0.9, "reach_score": 5000},
        {"sentiment_score": -0.8, "source_credibility": 0.85, "reach_score": 3000},
    ]
    score = calculate_perception_score(articles)
    assert score < 30

def test_empty_articles_returns_fifty():
    assert calculate_perception_score([]) == 50.0

def test_score_in_valid_range():
    articles = [
        {"sentiment_score": 0.5, "source_credibility": 0.7, "reach_score": 1000},
        {"sentiment_score": -0.3, "source_credibility": 0.5, "reach_score": 500},
    ]
    score = calculate_perception_score(articles)
    assert 0.0 <= score <= 100.0

def test_high_credibility_source_weighted_more():
    low_credibility = [{"sentiment_score": -0.9, "source_credibility": 0.1, "reach_score": 100}]
    high_credibility = [{"sentiment_score": 0.9, "source_credibility": 0.95, "reach_score": 10000}]
    score = calculate_perception_score(low_credibility + high_credibility)
    assert score > 50
```

- [ ] **Step 2: Run — verify FAIL**

```bash
pytest tests/test_perception.py -v
```

- [ ] **Step 3: Implement perception calculator**

```python
# backend/app/pipeline/perception.py
import math

def _weight(article: dict) -> float:
    credibility = article.get("source_credibility", 0.5)
    reach = article.get("reach_score", 0)
    reach_normalised = math.log10(reach + 1) / math.log10(10001)
    return credibility * (0.6 + 0.4 * reach_normalised)

def calculate_perception_score(articles: list[dict]) -> float:
    if not articles:
        return 50.0

    total_weight = 0.0
    weighted_sum = 0.0

    for a in articles:
        score = a.get("sentiment_score", 0.0)
        w = _weight(a)
        weighted_sum += score * w
        total_weight += w

    if total_weight == 0:
        return 50.0

    normalised = weighted_sum / total_weight   # -1.0 to +1.0
    return round((normalised + 1.0) / 2.0 * 100.0, 2)
```

- [ ] **Step 4: Run — verify PASS**

```bash
pytest tests/test_perception.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/pipeline/perception.py tests/test_perception.py
git commit -m "feat: credibility-weighted perception score calculator"
```

---

### Task 12: Storage Layer

**Files:**
- Create: `backend/app/storage/postgres.py`
- Create: `backend/app/storage/influxdb.py`
- Create: `backend/app/storage/r2.py`

- [ ] **Step 1: Implement Supabase storage**

```python
# backend/app/storage/postgres.py
from supabase import create_client, Client
from app.config import settings

def get_db() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)

def save_article(article: dict, nlp: dict) -> str | None:
    db = get_db()
    row = {**article, **nlp}
    row.pop("body", None)
    result = db.table("articles").upsert(row, on_conflict="brand_id,content_hash").execute()
    return result.data[0]["id"] if result.data else None

def get_articles(brand_id: str, limit: int = 50, offset: int = 0,
                 sentiment: str | None = None, language: str | None = None) -> list[dict]:
    db = get_db()
    q = db.table("articles").select("*").eq("brand_id", brand_id) \
           .order("collected_at", desc=True).range(offset, offset + limit - 1)
    if sentiment:
        q = q.eq("sentiment_label", sentiment)
    if language:
        q = q.eq("language", language)
    return q.execute().data

def get_kpi_summary(brand_id: str) -> dict:
    db = get_db()
    rows = db.table("articles").select(
        "sentiment_label"
    ).eq("brand_id", brand_id).execute().data
    total = len(rows)
    if total == 0:
        return {"total": 0, "positive": 0, "negative": 0, "neutral": 0,
                "positive_pct": 0, "negative_pct": 0, "neutral_pct": 0}
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for r in rows:
        counts[r["sentiment_label"]] = counts.get(r["sentiment_label"], 0) + 1
    return {
        "total": total,
        **counts,
        "positive_pct": round(counts["positive"] / total * 100, 1),
        "negative_pct": round(counts["negative"] / total * 100, 1),
        "neutral_pct":  round(counts["neutral"]  / total * 100, 1),
    }
```

- [ ] **Step 2: Implement InfluxDB timeseries storage**

```python
# backend/app/storage/influxdb.py
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from app.config import settings

def _client():
    return InfluxDBClient(
        url=settings.influxdb_url,
        token=settings.influxdb_token,
        org=settings.influxdb_org,
    )

def write_sentiment_point(brand_id: str, perception_score: float,
                           counts: dict, timestamp: datetime | None = None):
    ts = timestamp or datetime.now(timezone.utc)
    point = (
        Point("brand_sentiment")
        .tag("brand_id", brand_id)
        .field("perception_score", perception_score)
        .field("positive_count", counts.get("positive", 0))
        .field("negative_count", counts.get("negative", 0))
        .field("neutral_count",  counts.get("neutral", 0))
        .field("total_count",    counts.get("total", 0))
        .time(ts)
    )
    with _client() as c:
        c.write_api(write_options=SYNCHRONOUS).write(
            bucket=settings.influxdb_bucket, record=point
        )

def query_sentiment_trend(brand_id: str, days: int = 7) -> list[dict]:
    flux = f'''
from(bucket: "{settings.influxdb_bucket}")
  |> range(start: -{days}d)
  |> filter(fn: (r) => r._measurement == "brand_sentiment")
  |> filter(fn: (r) => r.brand_id == "{brand_id}")
  |> filter(fn: (r) => r._field == "perception_score")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> yield(name: "mean")
'''
    with _client() as c:
        tables = c.query_api().query(flux, org=settings.influxdb_org)
        return [
            {"time": record.get_time().isoformat(), "value": record.get_value()}
            for table in tables for record in table.records
        ]
```

- [ ] **Step 3: Implement Cloudflare R2 archive**

```python
# backend/app/storage/r2.py
import json
import boto3
from datetime import datetime, timezone
from app.config import settings

def _client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    )

def archive_article(article: dict) -> str:
    ts = datetime.now(timezone.utc)
    key = f"{article['brand_id']}/{ts.strftime('%Y/%m/%d')}/{article['content_hash']}.json"
    _client().put_object(
        Bucket=settings.r2_bucket_name,
        Key=key,
        Body=json.dumps(article, ensure_ascii=False),
        ContentType="application/json",
    )
    return key
```

- [ ] **Step 4: Commit**

```bash
git add app/storage/
git commit -m "feat: storage layer - Supabase, InfluxDB, Cloudflare R2"
```

---

## Milestone 5 — Pipeline Orchestration

### Task 13: Pipeline Orchestrator

**Files:**
- Create: `backend/app/pipeline/orchestrator.py`
- Create: `backend/tests/test_orchestrator.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_orchestrator.py
from unittest.mock import patch, MagicMock
from app.pipeline.orchestrator import run_brand_pipeline
from app.nlp.schemas import NLPResult

def _nlp_result():
    return NLPResult(0.7, "positive", ["Amul"], ["pricing"], ["good"],
                     "gemini-2.0-flash", 0.9)

def test_pipeline_processes_new_articles():
    brand = {"id": "b1", "name": "Amul"}
    config = {"keywords": ["Amul"], "languages": ["en"], "portal_ids": []}

    mock_articles = [{"content_hash": "h1", "brand_id": "b1",
                      "title": "Amul wins", "body": "great product",
                      "portal_id": "the_hindu", "language": "en",
                      "source_credibility": 0.9, "reach_score": 5000}]

    with patch("app.pipeline.orchestrator.get_portals_for_languages", return_value=[
                {"id": "the_hindu", "name": "The Hindu", "rss_url": "u",
                 "language": "en", "credibility": 0.9}]), \
         patch("app.pipeline.orchestrator.collect_portal", return_value=mock_articles), \
         patch("app.pipeline.orchestrator.filter_new_articles", return_value=mock_articles), \
         patch("app.pipeline.orchestrator.analyse_article", return_value=_nlp_result()), \
         patch("app.pipeline.orchestrator.archive_article", return_value="key"), \
         patch("app.pipeline.orchestrator.save_article", return_value="article-id"), \
         patch("app.pipeline.orchestrator.write_sentiment_point") as mock_influx:
        stats = run_brand_pipeline(brand, config)

    assert stats["processed"] == 1
    assert stats["errors"] == 0
    mock_influx.assert_called_once()

def test_pipeline_skips_when_no_new_articles():
    brand = {"id": "b1", "name": "Amul"}
    config = {"keywords": ["Amul"], "languages": ["en"], "portal_ids": []}

    with patch("app.pipeline.orchestrator.get_portals_for_languages", return_value=[
                {"id": "the_hindu", "name": "The Hindu", "rss_url": "u",
                 "language": "en", "credibility": 0.9}]), \
         patch("app.pipeline.orchestrator.collect_portal", return_value=[]), \
         patch("app.pipeline.orchestrator.filter_new_articles", return_value=[]), \
         patch("app.pipeline.orchestrator.write_sentiment_point") as mock_influx:
        stats = run_brand_pipeline(brand, config)

    assert stats["processed"] == 0
    mock_influx.assert_not_called()
```

- [ ] **Step 2: Run — verify FAIL**

```bash
pytest tests/test_orchestrator.py -v
```

- [ ] **Step 3: Implement orchestrator**

```python
# backend/app/pipeline/orchestrator.py
import logging
from app.ingestion.portals import get_portals_for_languages
from app.ingestion.rss_collector import collect_portal
from app.ingestion.deduplication import filter_new_articles
from app.nlp.router import analyse_article
from app.pipeline.perception import calculate_perception_score
from app.storage.postgres import save_article
from app.storage.influxdb import write_sentiment_point
from app.storage.r2 import archive_article

log = logging.getLogger(__name__)

def run_brand_pipeline(brand: dict, config: dict) -> dict:
    brand_id = brand["id"]
    keywords = config.get("keywords", [])
    languages = config.get("languages", ["en"])
    stats = {"brand_id": brand_id, "collected": 0, "processed": 0, "errors": 0}

    portals = get_portals_for_languages(languages)
    all_articles: list[dict] = []

    for portal in portals:
        try:
            articles = collect_portal(portal, keywords, brand_id)
            all_articles.extend(articles)
        except Exception as e:
            log.error("Portal %s failed: %s", portal["id"], e)
            stats["errors"] += 1

    stats["collected"] = len(all_articles)
    new_articles = filter_new_articles(all_articles, brand_id)

    if not new_articles:
        return stats

    processed_articles = []
    for article in new_articles:
        try:
            nlp = analyse_article(article)
            if nlp is None:
                stats["errors"] += 1
                continue
            nlp_dict = nlp.to_dict()
            archive_article({**article, **nlp_dict})
            save_article(article, nlp_dict)
            processed_articles.append({**article, **nlp_dict})
            stats["processed"] += 1
        except Exception as e:
            log.error("Article %s failed: %s", article.get("content_hash"), e)
            stats["errors"] += 1

    if processed_articles:
        score = calculate_perception_score(processed_articles)
        counts = {
            "positive": sum(1 for a in processed_articles if a.get("sentiment_label") == "positive"),
            "negative": sum(1 for a in processed_articles if a.get("sentiment_label") == "negative"),
            "neutral":  sum(1 for a in processed_articles if a.get("sentiment_label") == "neutral"),
            "total": len(processed_articles),
        }
        write_sentiment_point(brand_id, score, counts)

    return stats
```

- [ ] **Step 4: Run — verify PASS**

```bash
pytest tests/test_orchestrator.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/pipeline/orchestrator.py tests/test_orchestrator.py
git commit -m "feat: pipeline orchestrator - collect, dedupe, NLP, store"
```

---

### Task 14: Queue Worker + Scheduler

**Files:**
- Create: `backend/app/pipeline/worker.py`
- Create: `backend/app/pipeline/scheduler.py`

- [ ] **Step 1: Implement Upstash Redis worker**

```python
# backend/app/pipeline/worker.py
import json
import logging
import redis
from app.config import settings
from app.pipeline.orchestrator import run_brand_pipeline

log = logging.getLogger(__name__)
QUEUE_KEY = "mediasense:pipeline:queue"

def get_redis():
    return redis.Redis(
        host=settings.upstash_redis_host,
        port=settings.upstash_redis_port,
        password=settings.upstash_redis_password,
        ssl=True,
        decode_responses=True,
    )

def enqueue_brand(brand: dict, config: dict):
    r = get_redis()
    r.rpush(QUEUE_KEY, json.dumps({"brand": brand, "config": config}))

def process_queue(max_items: int = 100):
    r = get_redis()
    processed = 0
    while processed < max_items:
        item = r.lpop(QUEUE_KEY)
        if item is None:
            break
        try:
            data = json.loads(item)
            stats = run_brand_pipeline(data["brand"], data["config"])
            log.info("Pipeline done: %s", stats)
        except Exception as e:
            log.error("Queue item failed: %s", e)
        processed += 1
    return processed
```

- [ ] **Step 2: Implement APScheduler**

```python
# backend/app/pipeline/scheduler.py
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from supabase import create_client
from app.config import settings
from app.pipeline.worker import enqueue_brand

log = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

def _enqueue_all_brands():
    db = create_client(settings.supabase_url, settings.supabase_service_role_key)
    brands = db.table("brands").select("id, name").execute().data
    for brand in brands:
        config_row = db.table("brand_configs").select("*") \
                       .eq("brand_id", brand["id"]).execute().data
        if not config_row:
            continue
        config = config_row[0]
        enqueue_brand(brand, {
            "keywords": config.get("keywords", []),
            "languages": config.get("languages", ["en"]),
        })
    log.info("Enqueued %d brands for processing", len(brands))

def start_scheduler():
    scheduler.add_job(_enqueue_all_brands, "interval", hours=1, id="hourly_pipeline")
    scheduler.start()
    log.info("Scheduler started — hourly pipeline active")
```

- [ ] **Step 3: Commit**

```bash
git add app/pipeline/worker.py app/pipeline/scheduler.py
git commit -m "feat: Upstash Redis queue worker and hourly APScheduler"
```

---

## Milestone 6 — API Layer

### Task 15: FastAPI Application + Auth

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/auth/dependencies.py`

- [ ] **Step 1: Implement FastAPI app**

```python
# backend/app/main.py
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.pipeline.scheduler import start_scheduler
from app.pipeline.worker import process_queue
from app.auth.router import router as auth_router
from app.tenants.router import router as tenant_router
from app.dashboard.router import router as dashboard_router

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    asyncio.create_task(_queue_loop())
    yield

async def _queue_loop():
    import asyncio
    from app.pipeline.worker import process_queue
    while True:
        process_queue(max_items=50)
        await asyncio.sleep(60)

app = FastAPI(title="MediaSense API", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://your-app.vercel.app"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth_router,      prefix="/auth",      tags=["auth"])
app.include_router(tenant_router,    prefix="/tenants",   tags=["tenants"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])

@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 2: Implement JWT auth dependency**

```python
# backend/app/auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings

bearer = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.supabase_anon_key,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return {"user_id": payload.get("sub"), "email": payload.get("email")}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired token")
```

- [ ] **Step 3: Commit**

```bash
git add app/main.py app/auth/dependencies.py
git commit -m "feat: FastAPI app with Supabase JWT auth middleware"
```

---

### Task 16: Dashboard API Endpoints

**Files:**
- Create: `backend/app/dashboard/schemas.py`
- Create: `backend/app/dashboard/router.py`

- [ ] **Step 1: Create dashboard schemas**

```python
# backend/app/dashboard/schemas.py
from pydantic import BaseModel

class KPISummary(BaseModel):
    perception_score: float
    total: int
    positive: int
    negative: int
    neutral: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float

class TrendPoint(BaseModel):
    time: str
    value: float

class ArticleItem(BaseModel):
    id: str
    title: str
    url: str
    portal_id: str
    published_at: str | None
    sentiment_label: str
    sentiment_score: float
    language: str
    entities: list[str]
    topics: list[str]
    keywords: list[str]
    model_used: str

class SourceStat(BaseModel):
    portal_id: str
    count: int
    positive: int
    negative: int
    neutral: int

class OverviewResponse(BaseModel):
    kpi: KPISummary
    trend: list[TrendPoint]
    recent_mentions: list[ArticleItem]
    top_sources: list[SourceStat]
    top_keywords: list[str]
    top_topics: list[str]
```

- [ ] **Step 2: Implement dashboard router**

```python
# backend/app/dashboard/router.py
from collections import Counter
from fastapi import APIRouter, Depends, Query
from app.auth.dependencies import get_current_user
from app.storage.postgres import get_articles, get_kpi_summary
from app.storage.influxdb import query_sentiment_trend
from app.pipeline.perception import calculate_perception_score
from app.dashboard.schemas import OverviewResponse, KPISummary, ArticleItem, SourceStat, TrendPoint

router = APIRouter()

@router.get("/overview/{brand_id}", response_model=OverviewResponse)
def get_overview(brand_id: str, days: int = Query(7, ge=1, le=90),
                 user=Depends(get_current_user)):
    kpi_raw = get_kpi_summary(brand_id)
    trend_raw = query_sentiment_trend(brand_id, days)
    recent = get_articles(brand_id, limit=10)

    recent_score = calculate_perception_score([
        {"sentiment_score": a.get("sentiment_score", 0),
         "source_credibility": a.get("source_credibility", 0.5),
         "reach_score": a.get("reach_score", 0)} for a in recent
    ])

    kw_counter: Counter = Counter()
    topic_counter: Counter = Counter()
    source_map: dict[str, dict] = {}

    all_articles = get_articles(brand_id, limit=500)
    for a in all_articles:
        kw_counter.update(a.get("keywords", []))
        topic_counter.update(a.get("topics", []))
        pid = a.get("portal_id", "unknown")
        if pid not in source_map:
            source_map[pid] = {"portal_id": pid, "count": 0,
                               "positive": 0, "negative": 0, "neutral": 0}
        source_map[pid]["count"] += 1
        label = a.get("sentiment_label", "neutral")
        source_map[pid][label] = source_map[pid].get(label, 0) + 1

    return OverviewResponse(
        kpi=KPISummary(perception_score=recent_score, **kpi_raw),
        trend=[TrendPoint(**p) for p in trend_raw],
        recent_mentions=[ArticleItem(**{k: a.get(k, "") for k in ArticleItem.model_fields}) for a in recent],
        top_sources=[SourceStat(**v) for v in sorted(source_map.values(),
                                                      key=lambda x: x["count"], reverse=True)[:5]],
        top_keywords=[kw for kw, _ in kw_counter.most_common(15)],
        top_topics=[t for t, _ in topic_counter.most_common(10)],
    )

@router.get("/mentions/{brand_id}")
def get_mentions(brand_id: str, limit: int = Query(50, le=200),
                 offset: int = 0, sentiment: str | None = None,
                 language: str | None = None, user=Depends(get_current_user)):
    return get_articles(brand_id, limit=limit, offset=offset,
                        sentiment=sentiment, language=language)
```

- [ ] **Step 3: Commit**

```bash
git add app/dashboard/ tests/test_dashboard_api.py
git commit -m "feat: dashboard API - overview, mentions endpoints"
```

---

## Milestone 7 — Frontend

### Task 17: Frontend Scaffold

**Files:**
- Create: `frontend/` (Vite React TypeScript project)

- [ ] **Step 1: Scaffold Vite project**

```bash
cd ..
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install @supabase/supabase-js axios @tanstack/react-query recharts
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

- [ ] **Step 2: Configure Tailwind**

```javascript
// frontend/tailwind.config.js
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
}
```

```css
/* frontend/src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 3: Create API client and types**

```typescript
// frontend/src/lib/types.ts
export interface KPISummary {
  perception_score: number;
  total: number;
  positive: number;
  negative: number;
  neutral: number;
  positive_pct: number;
  negative_pct: number;
  neutral_pct: number;
}

export interface TrendPoint { time: string; value: number; }

export interface ArticleItem {
  id: string;
  title: string;
  url: string;
  portal_id: string;
  published_at: string;
  sentiment_label: "positive" | "negative" | "neutral";
  sentiment_score: number;
  language: string;
  entities: string[];
  topics: string[];
  keywords: string[];
  model_used: string;
}

export interface OverviewData {
  kpi: KPISummary;
  trend: TrendPoint[];
  recent_mentions: ArticleItem[];
  top_sources: { portal_id: string; count: number }[];
  top_keywords: string[];
  top_topics: string[];
}
```

```typescript
// frontend/src/lib/api.ts
import axios from "axios";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("sb_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const fetchOverview = (brandId: string, days = 7) =>
  api.get<import("./types").OverviewData>(`/dashboard/overview/${brandId}?days=${days}`)
     .then(r => r.data);

export const fetchMentions = (brandId: string, params?: Record<string, string>) =>
  api.get(`/dashboard/mentions/${brandId}`, { params }).then(r => r.data);

export default api;
```

- [ ] **Step 4: Commit**

```bash
cd frontend
git add .
git commit -m "feat: frontend scaffold - Vite, React, TypeScript, Tailwind"
```

---

### Task 18: Overview Dashboard Page

**Files:**
- Create: `frontend/src/components/cards/KPICard.tsx`
- Create: `frontend/src/components/charts/SentimentTrendChart.tsx`
- Create: `frontend/src/components/ui/SentimentBadge.tsx`
- Create: `frontend/src/pages/Overview.tsx`

- [ ] **Step 1: KPI Card component**

```tsx
// frontend/src/components/cards/KPICard.tsx
interface Props {
  label: string;
  value: string | number;
  sub?: string;
  color?: "green" | "red" | "yellow" | "blue" | "purple";
}
const colors = {
  green: "text-green-400", red: "text-red-400",
  yellow: "text-yellow-400", blue: "text-blue-400", purple: "text-purple-400",
};
export function KPICard({ label, value, sub, color = "blue" }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">{label}</div>
      <div className={`text-3xl font-bold ${colors[color]}`}>{value}</div>
      {sub && <div className="text-xs text-gray-500 mt-1">{sub}</div>}
    </div>
  );
}
```

- [ ] **Step 2: Sentiment badge**

```tsx
// frontend/src/components/ui/SentimentBadge.tsx
const styles = {
  positive: "bg-green-900/40 text-green-400 border border-green-800",
  negative: "bg-red-900/40 text-red-400 border border-red-800",
  neutral:  "bg-yellow-900/40 text-yellow-400 border border-yellow-800",
};
export function SentimentBadge({ label }: { label: "positive" | "negative" | "neutral" }) {
  return <span className={`text-xs px-2 py-0.5 rounded ${styles[label]}`}>{label}</span>;
}
```

- [ ] **Step 3: Sentiment trend chart**

```tsx
// frontend/src/components/charts/SentimentTrendChart.tsx
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import type { TrendPoint } from "../../lib/types";

export function SentimentTrendChart({ data }: { data: TrendPoint[] }) {
  const formatted = data.map(d => ({
    time: new Date(d.time).toLocaleDateString("en-IN", { weekday: "short" }),
    score: Math.round(d.value),
  }));
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="text-sm font-semibold text-gray-200 mb-3">Perception Score — 7 Days</div>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={formatted}>
          <XAxis dataKey="time" tick={{ fill: "#6b7280", fontSize: 11 }} />
          <YAxis domain={[0, 100]} tick={{ fill: "#6b7280", fontSize: 11 }} />
          <Tooltip contentStyle={{ background: "#1f2937", border: "none" }} />
          <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **Step 4: Overview page**

```tsx
// frontend/src/pages/Overview.tsx
import { useQuery } from "@tanstack/react-query";
import { fetchOverview } from "../lib/api";
import { KPICard } from "../components/cards/KPICard";
import { SentimentTrendChart } from "../components/charts/SentimentTrendChart";
import { SentimentBadge } from "../components/ui/SentimentBadge";
import type { ArticleItem } from "../lib/types";

const BRAND_ID = import.meta.env.VITE_BRAND_ID || "";

export function Overview() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["overview", BRAND_ID],
    queryFn: () => fetchOverview(BRAND_ID),
    refetchInterval: 60_000,
  });

  if (isLoading) return <div className="text-gray-400 p-8">Loading...</div>;
  if (error || !data) return <div className="text-red-400 p-8">Failed to load dashboard.</div>;

  return (
    <div className="p-6 space-y-6">
      {/* KPI Row */}
      <div className="grid grid-cols-5 gap-4">
        <KPICard label="Perception Score" value={data.kpi.perception_score.toFixed(1)} color="purple" />
        <KPICard label="Total Mentions"   value={data.kpi.total} color="blue" />
        <KPICard label="Positive"  value={`${data.kpi.positive_pct}%`} sub={`${data.kpi.positive} articles`}  color="green" />
        <KPICard label="Negative"  value={`${data.kpi.negative_pct}%`} sub={`${data.kpi.negative} articles`}  color="red" />
        <KPICard label="Neutral"   value={`${data.kpi.neutral_pct}%`}  sub={`${data.kpi.neutral} articles`}   color="yellow" />
      </div>

      {/* Trend + Sources */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2">
          <SentimentTrendChart data={data.trend} />
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-sm font-semibold text-gray-200 mb-3">Top Sources</div>
          <div className="space-y-2">
            {data.top_sources.map(s => (
              <div key={s.portal_id}>
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>{s.portal_id.replace(/_/g, " ")}</span>
                  <span>{s.count}</span>
                </div>
                <div className="bg-gray-800 rounded h-1.5">
                  <div className="bg-indigo-500 h-full rounded"
                       style={{ width: `${Math.min(100, (s.count / (data.kpi.total || 1)) * 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent mentions */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <div className="text-sm font-semibold text-gray-200 mb-3">Recent Mentions</div>
        <div className="space-y-3">
          {data.recent_mentions.map((a: ArticleItem) => (
            <div key={a.id} className="border-l-2 border-gray-700 pl-3">
              <div className="text-xs text-gray-500 mb-1">
                {a.portal_id.replace(/_/g, " ")} · {a.language.toUpperCase()} ·{" "}
                {a.published_at ? new Date(a.published_at).toLocaleString("en-IN") : ""}
              </div>
              <a href={a.url} target="_blank" rel="noreferrer"
                 className="text-sm text-gray-200 hover:text-indigo-400 line-clamp-2">
                {a.title}
              </a>
              <div className="mt-1">
                <SentimentBadge label={a.sentiment_label} />
                <span className="text-xs text-gray-600 ml-2">{a.sentiment_score.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Topics + Keywords */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-sm font-semibold text-gray-200 mb-3">Topics</div>
          <div className="flex flex-wrap gap-2">
            {data.top_topics.map(t => (
              <span key={t} className="bg-blue-900/30 text-blue-300 text-xs px-2 py-1 rounded-full border border-blue-800">
                {t.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-sm font-semibold text-gray-200 mb-3">Keywords</div>
          <div className="flex flex-wrap gap-2">
            {data.top_keywords.map(k => (
              <span key={k} className="bg-gray-800 text-gray-300 text-xs px-2 py-1 rounded-full">
                {k}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add src/
git commit -m "feat: Overview dashboard page with KPIs, trend chart, mentions feed"
```

---

## Milestone 8 — Deployment

### Task 19: Railway Deployment (Backend)

- [ ] **Step 1: Create `backend/Procfile`**

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- [ ] **Step 2: Create `backend/railway.json`**

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": { "builder": "NIXPACKS" },
  "deploy": { "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT" }
}
```

- [ ] **Step 3: Deploy**

```bash
# Install Railway CLI
npm install -g @railway/cli
railway login
railway init          # link to project
railway up            # deploy backend
railway variables set SUPABASE_URL=... GEMINI_API_KEY=... # set all env vars from .env
```

- [ ] **Step 4: Verify health endpoint**

```bash
curl https://your-app.up.railway.app/health
```
Expected: `{"status":"ok"}`

- [ ] **Step 5: Commit**

```bash
git add Procfile railway.json
git commit -m "chore: Railway deployment config"
```

---

### Task 20: Vercel Deployment (Frontend)

- [ ] **Step 1: Create `frontend/.env.production`**

```bash
VITE_API_URL=https://your-backend.up.railway.app
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
VITE_BRAND_ID=your-first-brand-uuid
```

- [ ] **Step 2: Deploy**

```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
# Set env vars in Vercel dashboard → Settings → Environment Variables
```

- [ ] **Step 3: Update CORS in backend**

In `backend/app/main.py`, add your Vercel URL to `allow_origins`:
```python
allow_origins=["http://localhost:5173", "https://your-app.vercel.app"],
```

- [ ] **Step 4: End-to-end smoke test**

```
1. Open https://your-app.vercel.app
2. Add a brand via Supabase dashboard (insert into brands + brand_configs)
3. Trigger pipeline manually: POST /dashboard/trigger/{brand_id} (add a temp debug route)
4. Verify articles appear in Overview dashboard within 5 minutes
5. Check InfluxDB Cloud dashboard for data points
6. Check Cloudflare R2 bucket for archived JSON files
```

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "chore: Vercel frontend deployment and end-to-end verified"
```

---

## Full Test Run

```bash
cd backend
pytest tests/ -v --tb=short
```

Expected: All tests pass. Total ~25 test cases covering portal registry, RSS collection, deduplication, language detection, Gemini handler, Groq handler, NLP router, perception calculator, and pipeline orchestrator.

---

## Self-Review Checklist

- [x] Portal registry (F1.3 — collect from configured portals) ✓ Task 3
- [x] RSS collector with keyword filter (F1.2) ✓ Task 4
- [x] Deduplication (F1.2) ✓ Task 5
- [x] Language detection (F1.3) ✓ Task 6
- [x] Gemini NLP — English + Tamil (F1.4, F1.5) ✓ Tasks 8–10
- [x] Groq fallback (F1.5) ✓ Task 9
- [x] Perception score (F1.6) ✓ Task 11
- [x] Storage — Supabase + InfluxDB + R2 (F1.2, F1.6) ✓ Task 12
- [x] Pipeline orchestrator (F1.12) ✓ Task 13
- [x] Hourly scheduler + queue (F1.12) ✓ Task 14
- [x] JWT auth (F1.11) ✓ Task 15
- [x] Dashboard Overview API (F1.7) ✓ Task 16
- [x] Mentions API (F1.8) ✓ Task 16
- [x] React dashboard — Overview page (F1.7) ✓ Task 18
- [x] Deployment — Railway + Vercel ✓ Tasks 19–20
- [ ] Tenant management API (F1.11 — agency/brand CRUD) — implement after smoke test
- [ ] Mention Explorer page (F1.8) — implement after smoke test
- [ ] Sources + Topics pages (F1.9, F1.10) — implement after smoke test
