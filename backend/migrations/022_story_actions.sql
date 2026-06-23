-- Story actions: Watch / Investigate / Ignore per article per user
CREATE TABLE IF NOT EXISTS story_actions (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id    uuid NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    article_id  uuid NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    action      text NOT NULL CHECK (action IN ('watch','investigate','ignore')),
    user_id     uuid REFERENCES auth.users(id),
    notes       text,
    created_at  timestamptz DEFAULT now(),
    UNIQUE (brand_id, article_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_story_actions_brand ON story_actions(brand_id, created_at DESC);

-- Generated content: drafts for Response Studio (Sessions 4 + 10)
CREATE TABLE IF NOT EXISTS generated_content (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id        uuid NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    content_type    text NOT NULL CHECK (content_type IN ('press_release','faq','tweet','linkedin','ceo_statement')),
    content_text    text NOT NULL,
    context_json    jsonb DEFAULT '{}',
    status          text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','pending','approved','rejected')),
    created_by      uuid REFERENCES auth.users(id),
    approved_by     uuid REFERENCES auth.users(id),
    created_at      timestamptz DEFAULT now(),
    updated_at      timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_generated_content_brand ON generated_content(brand_id, created_at DESC);
