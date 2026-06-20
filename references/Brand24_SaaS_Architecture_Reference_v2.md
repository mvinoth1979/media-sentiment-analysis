# SaaS Product Blueprint V2: Granular Architecture & Component Specification

**Target Audience:** AI Development Agents (Claude, Gemini, Cursor) and Full-Stack Engineering Teams.
**Purpose:** This document provides a highly technical, granular specification of a Social Listening SaaS (modeled after Brand24). It goes beyond UI layouts to include React/Vue component hierarchies, specific JSON data models, state management logic, and micro-interactions required to build a production-ready clone.

---

## 1. Granular Component Hierarchy (Frontend)

To reconstruct the main dashboard view, implement the following component tree. This structure ensures modularity and efficient re-rendering.

```text
<App>
  <AuthProvider>
    <ProjectProvider>
      <DashboardLayout>
        <!-- Fixed Left Sidebar -->
        <SidebarNav>
          <ProjectSelectorDropdown />
          <NavMenu tabs={['Mentions', 'Summary', 'Analysis', 'Sources', 'Influencers']} />
          <UserMenu />
        </SidebarNav>

        <!-- Scrollable Center Column -->
        <MainContentArea>
          <TopHeaderBar title="Mentions" />
          
          <DataVisualizationSection>
            <Tabs>
              <TabList>
                <Tab>Mentions & Reach</Tab>
                <Tab>Sentiment</Tab>
              </TabList>
              <TabPanels>
                <ChartContainer type="MultiAxisLine" data={timeseriesData} />
              </TabPanels>
            </Tabs>
          </DataVisualizationSection>

          <MentionFeedList>
            <FeedActionsBar sortBy={['Date', 'Popularity']} />
            {/* Rendered via Virtualized List for performance */}
            <VirtualScroller>
              <MentionCard />
              <MentionCard />
              <MentionCard />
            </VirtualScroller>
          </MentionFeedList>
        </MainContentArea>

        <!-- Fixed Right Sidebar -->
        <FilterPanel>
          <QuickActions buttons={['Summarize AI', 'Generate Report']} />
          <SourceFilter checkboxes={['Facebook', 'X', 'News', ...]} />
          <SentimentFilter checkboxes={['Positive', 'Neutral', 'Negative']} />
          <InfluenceSlider min={0} max={10} step={1} />
        </FilterPanel>
      </DashboardLayout>
    </ProjectProvider>
  </AuthProvider>
</App>
```

---

## 2. JSON Data Models & API Contracts

When designing the backend (Node.js/Python/Go) and the database schema, adhere to these explicit payload structures.

### A. The `Project` Object
Used to configure the search parameters.
```json
{
  "id": "proj_8f72c9a1b",
  "user_id": "usr_992xzb",
  "name": "Competitor Analysis - Beverages",
  "keywords": ["coca cola", "pepsi", "sprite"],
  "excluded_keywords": ["giveaway", "job"],
  "language_filter": "en",
  "status": "active", // active, paused, indexing
  "created_at": "2026-06-15T08:30:00Z",
  "meta": {
    "total_mentions": 14502,
    "last_indexed": "2026-06-16T13:10:00Z"
  }
}
```

### B. The `Mention` Object
The core atomic unit of the application. The frontend MentionCard component maps directly to this.
```json
{
  "id": "ment_7729abxw",
  "project_id": "proj_8f72c9a1b",
  "source_platform": "twitter",
  "source_url": "https://twitter.com/user/status/123456",
  "author": {
    "username": "SodaEnthusiast",
    "display_name": "Soda Enthusiast",
    "avatar_url": "https://example.com/avatar.jpg",
    "follower_count": 15420
  },
  "content": {
    "raw_text": "I really prefer the taste of pepsi over coca cola on a hot day.",
    "highlighted_html": "I really prefer the taste of <b>pepsi</b> over <b>coca cola</b> on a hot day."
  },
  "metrics": {
    "influence_score": 7.2, // Scale 0-10
    "estimated_reach": 4500,
    "engagement_count": 34
  },
  "analysis": {
    "sentiment": "positive", // positive, neutral, negative
    "sentiment_score": 0.85, // ML confidence score
    "language": "en"
  },
  "posted_at": "2026-06-16T12:45:00Z"
}
```

---

## 3. Micro-Interactions & State Management Specifications

### Frame 1: Onboarding Wizard (Keyword Entry)
* **State:** Maintain a `draftProject` object in local state.
* **Interaction (Keyword Input):** * *Behavior:* As the user types and presses 'Enter' or comma (`,`), convert the text into a visual "chip" or "tag".
    * *Validation:* Prevent duplicate tags. Limit to 10 keywords per project for standard tiers.
    * *Disable State:* The "Next" button must be `disabled` if the keyword array length is 0.

### Frame 2: The Data Loading Screen
* **Implementation Strategy:** Do not use standard REST polling. The backend process of scraping Twitter/News feeds takes 10-60 seconds.
* **Protocol:** Implement Server-Sent Events (SSE) or WebSockets.
* **UI Updates:** The backend should emit events like `{"status": "scraping_twitter", "progress": 20}`, `{"status": "running_nlp", "progress": 70}`. The frontend maps these to a deterministic progress bar and changing text prompts to keep the user engaged.

### Frame 3: The Mentions Dashboard & Filtering
* **State Management (Context/Redux):** The Right Sidebar (Filters) and the Center Column (Data) must share state. 
* **Action Flow:**
    1. User toggles the "Negative" sentiment checkbox in `<FilterPanel>`.
    2. Global state `activeFilters.sentiment` updates to `['negative']`.
    3. A custom hook (e.g., `useMentionsQuery(activeFilters)`) triggers.
    4. *Crucial UX:* Show a subtle skeleton loader over the *existing* feed data (do not wipe the screen white) while fetching the filtered data.
    5. URL Synchronization: Update the browser URL query parameters (`?sentiment=negative&min_influence=4`) so users can bookmark or share the exact filter state.

### Frame 4: Chart Interactivity (Recharts/Chart.js)
* **Hover State:** When hovering over the line chart, a vertical cursor line should span the Y-axis.
* **Tooltip Configuration:** The tooltip must display the exact Date, the Metric Name (e.g., "Mentions"), and the formatted Value (e.g., "12.4k").
* **Responsive Behavior:** The chart container must use `width: 100%` and listen to `ResizeObserver` events to redraw when the user expands/collapses the sidebars.

---

## 4. CSS / UI Styling Guidelines (Tailwind CSS Approach)

To mimic the clean, professional B2B SaaS aesthetic:

* **Color Palette:**
    * Primary Brand: Slate/Indigo (`bg-slate-900` for sidebars, `text-indigo-600` for active accents).
    * Background: Very light gray (`bg-gray-50`) for the main content area to make white cards pop.
    * Semantic Sentiment: `text-emerald-600` / `bg-emerald-100` (Positive), `text-rose-600` / `bg-rose-100` (Negative), `text-gray-500` / `bg-gray-100` (Neutral).
* **Typography:** Inter or Roboto. Strict hierarchy.
    * Headers: `text-xl font-semibold text-gray-900`
    * Body: `text-sm text-gray-600`
* **Card Styling (Mention Feed):**
    * Class setup: `bg-white border border-gray-200 rounded-lg shadow-sm p-4 hover:shadow-md transition-shadow duration-200`.

---

## 5. Edge Cases & Error Handling for the AI Agent

When writing the code, ensure Claude/the developer accounts for these edge cases:

1.  **Rate Limiting:** If the backend hits third-party API rate limits, the UI must gracefully display: "Data collection is temporarily throttled. Showing partial results." Do not crash.
2.  **Missing Data:** Many scraped articles will lack an author avatar or follower count. The UI must use robust fallback mechanisms (e.g., a styled div with the author's initials).
3.  **Long Text Truncation:** A Reddit post might be 2000 words long. The `<MentionCard>` must clamp text to ~3 lines using `line-clamp-3` and provide a "Read more" toggle.
4.  **Zero-State Filters:** If a user filters by "TikTok" and "Influence > 9" and no data exists, display a friendly Empty State illustration with a "Clear Filters" button, rather than a blank screen.
