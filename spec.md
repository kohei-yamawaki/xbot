# Project Specification: US Stock Trend Bot (Resilient & Zero-Cost Core)

## 1. Project Goal
Develop a fully automated Python-based bot that tracks US stock market trends (News + Reddit Sentiment) and generates a daily report.
**Core Philosophy:** "Zero Runtime Cost".
- **Primary Output:** Commit a Markdown report to the repository (GitHub Pages/View compatible).
- **Secondary Output:** Post to X (Twitter) *only if* valid API credits/keys are available. Gracefully handle 402/403 errors without failing the workflow.

## 2. Technical Architecture
- **Infrastructure:** GitHub Actions (Scheduled).
- **Intelligence (LLM):** Google Gen AI SDK (`google-genai`). Model: `gemini-2.0-flash`.
- **Data Sources:**
  - Yahoo Finance RSS (News) via `feedparser`.
  - Reddit (r/wallstreetbets, etc.) via `praw`.
  - Google Trends via `pytrends` (Best effort).
- **State Management:** `data/processed_ids.json` (Self-modifying repository pattern).
- **Visuals:** Dynamic image generation using `Pillow`.

## 3. Key Constraints & Logic
1.  **Timezone Handling:**
    - Market Hours: US Market Open (JST 23:30 - 06:00).
    - **CRITICAL:** GitHub Actions uses **UTC**. Schedule must be converted (JST -9 hours).
2.  **Output Specifications:**
    - **Report (Markdown):** Save to `reports/YYYY-MM-DD.md`.
    - **X Post (Optional):** Max 280 chars. Must include ticker ($NVDA), sentiment emoji, and source URL.
    - **Image:** 1200x675px (Twitter card size). Green background for Bullish, Red for Bearish.
3.  **Resilience (Acceptance Criteria):**
    - **Deduplication:** Check `processed_ids.json` before processing.
    - **Concurrency:** Prevent multiple Actions from overwriting the JSON state simultaneously.
    - **Error Handling:** Use `tenacity` for retries on network calls.
    - **X API Failure:** If X API returns 402/403 (Payment Required), log a warning but **DO NOT** fail the job. Proceed to commit the report.

## 4. Directory Structure
```text
.
├── .github/
│   └── workflows/
│       └── bot.yml      # Cron (UTC) + Concurrency settings
├── data/
│   └── processed_ids.json # State DB
├── reports/             # Generated Markdown reports
├── src/
│   ├── main.py          # Entry point
│   ├── news_fetcher.py  # RSS Logic
│   ├── reddit_loader.py # PRAW Logic
│   ├── llm_engine.py    # Google Gen AI SDK integration
│   ├── image_gen.py     # Pillow Logic
│   ├── x_client.py      # Tweepy (with robust error handling)
│   └── utils.py         # Logger & State helpers
└── requirements.txt