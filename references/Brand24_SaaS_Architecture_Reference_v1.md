# SaaS Product Blueprint: Brand24 Architecture & UI/UX Reference

**Target Audience:** AI Development Agents (e.g., Claude, Gemini) and Full-Stack Engineers
**Purpose:** This document provides a deep, structural analysis of the Brand24 Social Listening platform as observed in a product demo. It is designed to act as a foundational blueprint for rebuilding a similar SaaS application, covering visual layouts, user flows, inferred data models, and component architecture.

---

## 1. Application Overview & Core Entities

Based on the platform's functionality, a clone would require the following core domain entities:

1.  **User / Account:** Manages authentication, subscription tiers, and organizational limits.
2.  **Project:** A saved search configuration. Contains target keywords, required languages, and associated data.
3.  **Mention:** A single indexed data point (a tweet, an article, a Reddit post). Contains the raw text, author, timestamp, source platform, and computed metadata (sentiment, reach).
4.  **Source / Domain:** The origin of the mention (e.g., youtube.com, reddit.com). Contains aggregated metrics like total visits and mentions.
5.  **Influencer / Author:** The profile that generated the mention. Contains follower counts, influence scores, and share of voice metrics.

---

## 2. Frame-by-Frame UI/UX Breakdown

### State A: Authentication & Onboarding (0:00 - 2:55)

**Visual Layout & Components:**
* **0:37 - Auth View:** Centered card layout with fields for `Business email` and `Password`. Minimalist green/white branding. Includes a "Sign in with Google" OAuth option.
* **1:50 - Project Creation Wizard (Step 1):** Full-screen focused view. 
    * *Component:* Large text input area for `Enter keywords/key phrases`. 
    * *Behavior:* Accepts comma-separated values (e.g., "Coca Cola, Pepsi"). 
    * *UX Detail:* A subtle progress indicator dots at the bottom show the user is on step 1 of 2.
* **2:20 - Project Creation Wizard (Step 2):** * *Component:* Dropdown menu for "Track only in selected language".
    * *Behavior:* Defaults to "All languages", allows selection of specific languages (e.g., "English").
* **2:40 - Loading State:** * *UI:* Centered loading spinner with the text "Loading mentions... It'll take just a few moments...".
    * *Backend Implication:* This is the critical asynchronous data-fetching phase where the backend queries third-party APIs (Twitter, Reddit, News APIs) or internal Elasticsearch clusters, runs NLP sentiment analysis, and populates the project database.

### State B: The Core "Mentions" Dashboard (2:55 - 4:45)

**Visual Layout & Components:**
This is the primary workspace. It utilizes a dense, 3-column layout:
1.  **Left Sidebar (Navigation):** Fixed position. Contains project switching dropdown, and tabs: Mentions, Summary, Analysis, Sources, Influencers, Comparison, Reports.
2.  **Center Column (Data & Charts):** Scrollable. Top section contains time-series charts. Bottom section contains the chronological feed of mentions.
3.  **Right Sidebar (Filtering):** Fixed position. Contains comprehensive filtering tools to slice the data in the center column.

**Detailed Component Breakdown (Center Column):**
* **Mentions & Reach Chart (3:13):** A multi-axis line chart.
    * *X-Axis:* Date range.
    * *Y-Axis (Left):* Volume of mentions (Blue line).
    * *Y-Axis (Right):* Estimated Reach (Green line).
    * *Interactivity:* Hovering over a node displays a tooltip with precise daily numbers.
* **Sentiment Chart (3:57):** A secondary tab on the chart component. 
    * Plots Positive (Green) vs. Negative (Red) sentiment lines over time.
* **Mention Feed Card (3:33):** The atomic unit of the main feed. Each card displays:
    * *Header:* Source Icon (e.g., Reddit), Author Name, Follower count, Influence Score (e.g., 3/10), Timestamp.
    * *Body:* The snippet of text. The monitored keyword (e.g., "Pepsi") is highlighted in bold.
    * *Footer Actions:* "Visit" (External link), "Tags" (categorization), "Delete", "Add to PDF report", "Mute site", "More actions".
    * *Sentiment Badge:* A color-coded pill (Green = Positive, Red = Negative, Grey = Neutral) indicating the NLP-derived sentiment.

**Detailed Component Breakdown (Right Sidebar Filters):**
* **Quick AI Actions:** Buttons for "Summarize with AI" and "Generate Report".
* **Sources Checkboxes:** Filter by Facebook, X (Twitter), Instagram, TikTok, YouTube, News, Podcasts, Forums, Blogs, Web. Includes connection prompts for authenticated APIs (e.g., Facebook Connect).
* **Sentiment Toggles:** Checkboxes for Negative, Neutral, Positive.
* **Influence Score Slider:** A dual-handle range slider (0 to 10) to filter out low-value noise.

### State C: Aggregated Data Views (4:48 - End)

**1. Summary Dashboard (4:48):**
* *Purpose:* High-level executive overview.
* *UI Components:* Top KPI row displaying total numbers and week-over-week percentage changes for: Mentions, Social Media Reach, Interactions, Positive Mentions, Negative Mentions.
* *Layout:* Two-column grid below KPIs. Left side shows "The most popular mentions", right side shows smaller charts and numeric summaries.

**2. Sources Table (6:43):**
* *Purpose:* Identify which platforms drive the most conversation.
* *UI Components:* A data table with columns: Page (Domain with favicon), Mentions (Count), Visits (Estimated total traffic of the domain), Influence Score. 
* *UX:* Sortable headers.

**3. Influencers Table (7:30):**
* *Purpose:* Identify key opinion leaders.
* *UI Components:* A data table with columns: Profile name, Source (Icon), Mentions (Count from this user), Reach, Followers, Share of Voice (%), Influence Score.
* *UX:* A "Show More" button at the bottom for pagination.

---

## 3. Inferred Backend Architecture & System Requirements

To build this for a production environment, the AI/Engineering team should consider the following system design:

### Data Ingestion Layer
* **Web Scrapers & API Clients:** Services to poll Twitter API, Reddit API, YouTube API, and generic RSS/News feeds based on user-defined keywords.
* **Message Broker:** Kafka or RabbitMQ to queue incoming mentions for asynchronous processing (to prevent overwhelming the NLP engine).

### Processing & NLP Layer
* **Sentiment Classifier:** A machine learning model (e.g., fine-tuned RoBERTa or a commercial API like OpenAI/Google Cloud NLP) that takes the raw text of a mention and outputs a confidence score for Positive, Negative, or Neutral.
* **Entity Extraction:** To highlight the specific keywords within the text blocks.
* **Influence Scoring Algorithm:** A proprietary algorithm that weights follower count, domain authority, and engagement metrics to generate a 1-10 "Influence Score".

### Storage Layer
* **Primary Database (Relational):** PostgreSQL for managing Users, Projects, Subscriptions, and billing.
* **Search Database (NoSQL):** Elasticsearch or OpenSearch. Crucial for storing millions of mentions. It allows for ultra-fast full-text search, complex filtering (by date, source, sentiment), and rapid aggregations for the charts.

### API Endpoint Blueprints (REST/GraphQL)

* `POST /api/v1/projects` - Accepts keywords and language, triggers the initial data fetching job.
* `GET /api/v1/projects/{id}/mentions` - The workhorse endpoint. Accepts query parameters for pagination, date ranges, source filters, sentiment filters, and influence score ranges. Returns an array of Mention objects.
* `GET /api/v1/projects/{id}/analytics/timeseries` - Returns aggregated daily counts for mentions, reach, and sentiment to plot the charts.
* `GET /api/v1/projects/{id}/analytics/influencers` - Returns a sorted list of top authors based on aggregated mention data within the project.

---

## 4. Suggested Frontend Technology Stack

* **Framework:** React or Vue.js (Next.js/Nuxt.js for SSR and performance).
* **State Management:** Redux or Zustand. The filter state (right sidebar) needs to globally update the fetch parameters for the center column components.
* **Charting Library:** Recharts, Chart.js, or Highcharts for rendering the interactive multi-axis time-series graphs.
* **UI Component Library:** Tailwind CSS paired with a headless UI library (Radix or Headless UI) to rapidly build the tables, dropdowns, and range sliders.

## 5. Development Priorities & "Gotchas" to Avoid

* **Beware of "Data Overload":** The original UI is very dense. When recreating, consider hiding advanced filters behind an "Advanced Search" toggle to improve initial onboarding.
* **Handling the "Loading" State:** Real-time data scraping is slow. Implement WebSockets or Server-Sent Events (SSE) so the frontend can display mentions progressively as they are found, rather than making the user wait 30 seconds for a single massive payload.
* **Spam Filtering:** Raw social media data contains massive amounts of bot spam. The system *must* have a strong pre-processing layer to discard duplicate or bot-generated content before it reaches the frontend, otherwise, the user's dashboard will be useless.
