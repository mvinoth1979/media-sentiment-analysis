# Supabase Migrations

This directory contains database schema and security migrations for the MediaSense platform.

## How to Apply Migrations

Migrations must be applied manually via the Supabase SQL Editor (these are not auto-applied):

1. Open https://app.supabase.com → your project → SQL Editor
2. Copy and run `001_schema.sql` first (creates all tables and indexes)
3. Copy and run `002_rls.sql` second (enables Row-Level Security policies)
4. Copy and run `003_trend_annotations.sql` (adds the `trend_annotations` table for trend-chart annotations)

Always apply in order. Never skip or reorder migrations.

## Database Architecture

### Core Tables

- **agencies** - Top-level organizational units
- **brands** - Brands owned by agencies
- **brand_configs** - Keywords, languages, states, and portal settings per brand
- **user_roles** - Maps Supabase Auth user UUIDs to agency/brand roles with permission levels
- **articles** - Raw article data + NLP results (sentiment, entities, topics, language detection)
- **dedupe_hashes** - Lightweight deduplication table for fast duplicate checking
- **trend_annotations** - User-added notes pinned to a date on a brand's sentiment trend chart

### Key Design Decisions

- **Single articles table**: Stores both raw article info AND NLP results to avoid expensive joins in dashboard queries
- **UNIQUE constraints on user_roles**: Prevents duplicate role assignments (one role per user per brand, one per user per agency)
- **Composite indexes on articles**: `(brand_id, collected_at DESC)` and `(brand_id, sentiment_label)` support dashboard filtering
- **Soft multi-tenancy**: user_roles table provides role-based access control; RLS policies enforce it

## Authentication & Access Control

### Backend (Python)

- Uses `SUPABASE_SERVICE_ROLE_KEY` which **bypasses RLS automatically**
- Can read/write all data without RLS restrictions
- INSERT/UPDATE/DELETE operations go directly through (no policies needed)

### Frontend/Dashboard

- Uses `SUPABASE_ANON_KEY` with Supabase Auth (authenticated user)
- Subject to RLS policies defined in `002_rls.sql`
- Can only see data they have explicit access to via user_roles

## RLS Policy Overview

| Table | SELECT Policy |
|-------|---|
| agencies | User can see agencies where they have a role |
| brands | User can see brands they have a direct role for, OR brands under agencies they have a role for |
| articles | User can see articles for brands they have access to (same logic as brands) |
| brand_configs | RLS enabled; access follows brand visibility |

## Troubleshooting

- **"permission denied" errors**: Verify user has a user_roles entry with the correct agency_id or brand_id
- **RLS not blocking**: Check that auth.uid() is set (only when authenticated via Supabase Auth)
- **Service key operations failing**: Verify `SUPABASE_SERVICE_ROLE_KEY` is set in environment
