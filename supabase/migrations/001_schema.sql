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
    brand_id UUID NOT NULL UNIQUE REFERENCES brands(id) ON DELETE CASCADE,
    keywords TEXT[] NOT NULL DEFAULT '{}',
    languages TEXT[] NOT NULL DEFAULT '{"en","ta"}',
    states TEXT[] NOT NULL DEFAULT '{}',
    competitors TEXT[] NOT NULL DEFAULT '{}',
    portal_ids TEXT[] NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    agency_id UUID REFERENCES agencies(id) ON DELETE CASCADE,
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('agency_admin','agency_analyst','brand_admin','brand_viewer')),
    CHECK ((agency_id IS NOT NULL) OR (brand_id IS NOT NULL)),
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
