# Agent C — Source Authority Tiers + SoV Caveat Disclosure

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the gnews portal tier label (Item 4 — currently all gnews articles incorrectly get Tier 4 when they should be labelled "Wire") and add a caveat disclosure to the Competitor Share of Voice donut chart (Item 10).

**Architecture:** Both changes are small. The tier infrastructure (`get_portal_tier`, `TIER_LABELS`, `HeadlineItem.source_tier`, `tierBadge()` in `TopHeadlines.tsx`) is already fully implemented and working. The only gap is that articles whose `portal_id` starts with `gnews_` (Google News RSS articles) fall through to the "no portal found" branch of `get_portal_tier()` and return `4`, when they should be labelled "Wire" to distinguish them from hyperlocal portals. The SoV caveat is a pure frontend addition of a tooltip + footnote.

**Tech Stack:** Python 3.12 · FastAPI · React 19 · TypeScript · Tailwind CSS 4

## Global Constraints

- Python: no new files needed — all changes in `backend/app/ingestion/portals.py`
- Frontend: no new npm packages; use existing Tailwind classes
- Do NOT change the tier thresholds (0.87 / 0.78 / 0.68) — they are correct and used in production
- Do NOT rename existing constants (`TIER_LABELS`, `CATEGORY_LABELS`, etc.)

---

### Task 1: Fix gnews Portal Tier in `portals.py`

**Files:**
- Modify: `backend/app/ingestion/portals.py`
- Test: `backend/tests/test_portals.py` (extend existing file)

**Interfaces:**
- Consumes: `get_portal_tier(portal_id: str) -> int` — existing function
- Produces: `get_portal_tier("gnews_en")` now returns `5` (Wire tier); `TIER_LABELS[5] = "Wire"`

**Why tier 5?** YouTube already uses `0`. Tiers 1–4 are news credibility levels. Wire (5) is a separate conceptual bucket — not a credibility ranking but a source-type label. The frontend already hides tier badges for YouTube (checks `item.source_tier > 0`), so Wire (5) will show as expected.

- [ ] **Step 1: Write failing test**

Add to `backend/tests/test_portals.py` (extend the existing file, don't replace it):

```python
# Add these tests to the existing test_portals.py

from app.ingestion.portals import get_portal_tier, TIER_LABELS

def test_gnews_portal_returns_wire_tier():
    assert get_portal_tier("gnews_en") == 5
    assert get_portal_tier("gnews_ta") == 5
    assert get_portal_tier("gnews_hi") == 5

def test_wire_tier_label_exists():
    assert TIER_LABELS[5] == "Wire"

def test_known_tier1_portal():
    assert get_portal_tier("the_hindu") == 1

def test_youtube_portal_returns_zero():
    assert get_portal_tier("youtube_search") == 0
```

- [ ] **Step 2: Run tests to confirm they fail**

```
cd backend && python -m pytest tests/test_portals.py::test_gnews_portal_returns_wire_tier tests/test_portals.py::test_wire_tier_label_exists -v
```

Expected: `AssertionError` — `get_portal_tier("gnews_en")` returns `4`, `TIER_LABELS` has no key `5`

- [ ] **Step 3: Add Wire tier to `portals.py`**

In `backend/app/ingestion/portals.py`, modify the `TIER_LABELS` dict to add the Wire entry:

```python
TIER_LABELS: dict[int, str] = {
    0: "YouTube",
    1: "Tier 1",
    2: "Tier 2",
    3: "Tier 3",
    4: "Tier 4",
    5: "Wire",
}
```

Modify the `get_portal_tier` function to handle gnews portals before the credibility lookup:

```python
def get_portal_tier(portal_id: str) -> int:
    """
    Maps a portal to Source Authority Tier 1–4 (0 for YouTube, 5 for Wire/gnews).
    Derived from existing credibility scores:
      Tier 1: national outlets        credibility >= 0.87
      Tier 2: regional / vernacular   credibility >= 0.78
      Tier 3: trade / specialist      credibility >= 0.68
      Tier 4: hyperlocal / community  credibility <  0.68
      Tier 5: Wire / Google News RSS  (gnews_ prefix)
    """
    if portal_id.startswith("youtube_"):
        return 0
    if portal_id.startswith("gnews_"):
        return 5
    portal = get_portal(portal_id)
    if not portal:
        return 4
    cred = portal.get("credibility", 0.5)
    if cred >= 0.87:
        return 1
    if cred >= 0.78:
        return 2
    if cred >= 0.68:
        return 3
    return 4
```

- [ ] **Step 4: Run tests to confirm they pass**

```
cd backend && python -m pytest tests/test_portals.py -v
```

Expected: all portals tests pass including the 4 new ones

- [ ] **Step 5: Update frontend Wire badge color**

The `tierBadge()` utility in `frontend/src/lib/utils.ts` (or wherever it's defined) handles tiers 1–4. Add tier 5 (Wire) so it renders correctly.

Find `tierBadge` in the frontend. It likely looks like:

```typescript
export function tierBadge(tier: number) {
  if (tier === 1) return { label: "T1", bg: "bg-indigo-50", color: "text-indigo-700" };
  if (tier === 2) return { label: "T2", bg: "bg-blue-50",   color: "text-blue-700"   };
  if (tier === 3) return { label: "T3", bg: "bg-slate-50",  color: "text-slate-600"  };
  return             { label: "T4", bg: "bg-gray-50",   color: "text-gray-500"   };
}
```

Replace it with:

```typescript
export function tierBadge(tier: number) {
  if (tier === 1) return { label: "T1",   bg: "bg-indigo-50", color: "text-indigo-700" };
  if (tier === 2) return { label: "T2",   bg: "bg-blue-50",   color: "text-blue-700"   };
  if (tier === 3) return { label: "T3",   bg: "bg-slate-50",  color: "text-slate-600"  };
  if (tier === 5) return { label: "Wire", bg: "bg-amber-50",  color: "text-amber-700"  };
  return             { label: "T4",   bg: "bg-gray-50",   color: "text-gray-500"   };
}
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/ingestion/portals.py backend/tests/test_portals.py
git add frontend/src/lib/utils.ts   # or wherever tierBadge lives
git commit -m "feat: Wire tier (5) for gnews portals + amber badge in TopHeadlines"
```

---

### Task 2: SoV Caveat Disclosure in `CompetitorShareOfVoice.tsx`

**Files:**
- Modify: `frontend/src/components/CompetitorShareOfVoice.tsx`

**Interfaces:**
- Produces: ℹ️ tooltip on the section heading + a grey footnote below the donut in expanded mode; compact mode gets the footnote only

- [ ] **Step 1: Add the tooltip state and caveat text**

In `frontend/src/components/CompetitorShareOfVoice.tsx`, add a `useState` import if not already present (it is — the file already uses it):

Add the caveat constant near the top of the component (after the `FALLBACK_ENTRIES` constant):

```typescript
const SOV_CAVEAT = "Based on YouTube and news portal coverage only. Twitter/X, Instagram, and Facebook are not yet monitored and are excluded from these figures.";
```

- [ ] **Step 2: Update the compact mode render**

In the compact `return (...)` block, change the heading row from:

```tsx
<span className="text-[11px] font-semibold text-gray-800">Share of Voice</span>
```

to:

```tsx
<span className="text-[11px] font-semibold text-gray-800">Share of Voice</span>
```

And add a footnote at the very bottom of the compact container (before the closing `</div>` of the outermost compact div):

```tsx
<p className="text-[8px] text-gray-400 mt-1 leading-tight">{SOV_CAVEAT}</p>
```

- [ ] **Step 3: Update the expanded mode render**

In the full (non-compact) `return (...)` block, change the heading from:

```tsx
<div className="text-sm font-semibold text-gray-800 mb-3">Competitor Share of Voice</div>
```

to:

```tsx
<div className="flex items-center gap-1.5 mb-3">
  <span className="text-sm font-semibold text-gray-800">Competitor Share of Voice</span>
  <div className="relative group">
    <button className="w-4 h-4 rounded-full bg-gray-100 text-gray-400 text-[10px] flex items-center justify-center hover:bg-gray-200 transition-colors">
      ℹ
    </button>
    <div className="absolute left-5 top-0 z-10 hidden group-hover:block w-64 bg-gray-800 text-white text-[10px] p-2 rounded-lg shadow-lg leading-relaxed">
      {SOV_CAVEAT}
    </div>
  </div>
</div>
```

And add the footnote at the very bottom of the expanded container (after the legend list, before the closing `</div>`):

```tsx
<p className="text-[9px] text-gray-400 mt-3 leading-tight border-t border-gray-100 pt-2">
  YouTube &amp; news coverage only — social media channels excluded.
</p>
```

- [ ] **Step 4: Verify TypeScript compiles**

```
cd frontend && npx tsc --noEmit
```

Expected: no type errors

- [ ] **Step 5: Visual check**

Start the dev server:
```
cd frontend && npm run dev
```

Navigate to any brand's Overview → click Competitors section. Verify:
- The ℹ️ icon appears next to "Competitor Share of Voice"
- Hovering shows the tooltip text
- The grey footnote appears below the legend
- Compact mode (in the grid) shows the small footnote below the entries

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/CompetitorShareOfVoice.tsx
git commit -m "feat: SoV caveat disclosure — info tooltip + footnote on YouTube/news-only scope"
```

---

### Task 3: Final agent C commit

- [ ] **Step 1: Run all backend tests**

```
cd backend && python -m pytest tests/test_portals.py -v
```

Expected: all tests pass.

- [ ] **Step 2: Final commit**

```bash
git add -A
git commit -m "feat: agent C complete — Wire tier for gnews portals + SoV caveat disclosure"
```
