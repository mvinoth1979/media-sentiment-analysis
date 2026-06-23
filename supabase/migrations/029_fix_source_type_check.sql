-- Migration 029: expand articles source_type CHECK constraint
--
-- The original constraint (articles_source_type_check) was added in Supabase
-- Studio and doesn't include google_review or play_store_review, causing
-- INSERT failures for SerpAPI Google Reviews and Play Store collectors.
-- PostgreSQL requires DROP + ADD to modify a CHECK constraint.

ALTER TABLE articles
  DROP CONSTRAINT IF EXISTS articles_source_type_check;

ALTER TABLE articles
  ADD CONSTRAINT articles_source_type_check CHECK (
    source_type IN (
      'news',
      'rss',
      'blog',
      'portal',
      'youtube_video',
      'youtube_comment',
      'reddit_post',
      'reddit_comment',
      'forum',
      'google_review',
      'trustpilot_review',
      'mouthshut_review',
      'justdial_review',
      'ambitionbox_review',
      'tripadvisor_review',
      'team_bhp_review',
      'amazon_review',
      'flipkart_review',
      'glassdoor_review',
      'indiamart_review',
      'play_store_review'
    )
  );
