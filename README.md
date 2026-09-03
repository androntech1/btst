# 📈 Daily NSE Momentum Scanner & AI Engine

[![Daily Screener](https://github.com/androntech1/btst/actions/workflows/fetch_data.yml/badge.svg)](https://github.com/androntech1/btst/actions/workflows/fetch_data.yml)
[![Live Web Dashboard](https://img.shields.io/badge/Live_Dashboard-androntech1.github.io%2Fbtst-06b6d4?style=flat&logo=googlechrome)](https://androntech1.github.io/btst/)

Automated daily BTST momentum scanner for Indian NSE equities: 52-week-high breakout filtering, daily technicals, event gap-risk flags, and an optional AI ranking layer oriented toward a favorable next-day move.

---

## 🌐 Live Web Dashboard

Access the full interactive dashboard with real-time sortable tables, AI score meters, strength tags, risk flags, and historical scans:

👉 **[https://androntech1.github.io/btst/](https://androntech1.github.io/btst/)**

### ⚡ Latest Scan Summary (03 September 2026)
- **ScanX Candidates:** 47
- **Passed 52W High Filter:** 28 stocks within 10% of 52W High
- **Top Rule-Based Pick:** **RBL Bank** (Composite: **91.7/100**)
- **Data Exports:** [`data/data_latest.json`](data/data_latest.json) • [`data/manifest.json`](data/manifest.json) • raw/processed under [`data/`](data/)

---

## 🏗️ Scanner Architecture & Methodology

```text
ScanX NSE Equity Universe
       │
       ▼
[1] Mechanical Momentum Filter
    • Volume ≥ 2× 10-day SMA Volume
    • Positive Open Action (Open > BcOpen)
    • Positive Close Action (LTP > BcClose)
    • Momentum confirmation: RSI(14) ≥ 65
       │
       ▼
[2] 52-Week High Proximity + Enrichment (yfinance)
    • Current LTP within 10% of 52-Week High
    • Daily technicals: pivot/R1/S1, 20D overextension, ATR%, volume surge
    • yfinance event (ex-div/earnings) gap-risk flags
       │
       ├──► Rule-Based Top 5 (equal-weight composite: proximity + surge + RSI-health + not-overextended, × fundamentals gate)
       │
       ▼
[3] AI Quantitative & News Ranking (OpenRouter / Gemini) — toggle via AI_ENABLED
    • Blends technicals + catalyst/events for a next-day move
    • Output: AI Top 5 with Score (0-100), catalyst, strengths, risks & event flags
       │
       ▼
[4] Exports
    • data/raw/<date>.json (audit) + data/processed/<date>.json (flat)
    • data/data_latest.json + data/manifest.json (date index)
    • Interactive index.html on GitHub Pages
```

---

## ⚙️ Setup & Configuration

### Running Locally
```bash
git clone https://github.com/androntech1/btst.git
cd btst
pip install -r requirements.txt
cp .env.example .env   # then fill in OPENROUTER_API_KEY (or set AI_ENABLED=false)
python run_screener.py
```
This writes `data/raw/<date>.json`, `data/processed/<date>.json`, `data/data_latest.json`,
`data/manifest.json`, updates `README.md`, and re-embeds the latest scan into `index.html`
(open `index.html` directly in a browser to preview it offline). No API key is needed if
you set `AI_ENABLED=false` — the rule-based composite still runs standalone.

### Running via GitHub Actions
The [`fetch_data.yml`](.github/workflows/fetch_data.yml) workflow runs the same
`python run_screener.py` entry point in CI:
- **Scheduled:** automatically **Monday to Friday at 3:10 PM IST** (`10 15 * * 1-5`,
  `Asia/Kolkata`) — 20 minutes before market close, timed for BTST / momentum entries.
- **Manual:** open the repo's **Actions** tab → *Fetch and Filter ScanX Data* →
  **Run workflow** (`workflow_dispatch`) to trigger an off-schedule scan.
- **Secret required:** add `OPENROUTER_API_KEY` under **Settings → Secrets and
  variables → Actions** so the AI ranking step can run in CI (skip it and the workflow
  still runs rule-based only). `AI_PROVIDER` / `AI_MODEL` can be overridden as repo
  Actions **variables** if you don't want the defaults below.
- On success the workflow commits the refreshed `data/`, `README.md`, and `index.html`
  back to `main` as `github-actions[bot]` and GitHub Pages redeploys the dashboard.

### Environment Variables / Secrets
| Variable | Description | Default |
|:---|:---|:---|
| `OPENROUTER_API_KEY` | OpenRouter API Key (Required only when AI is enabled) | - |
| `AI_ENABLED` | Turn the AI ranking layer on/off (`false` runs rule-based only) | `true` |
| `AI_PROVIDER` | AI Provider (`openrouter` or `openai`) | `openrouter` |
| `AI_MODEL` | AI Model slug | `google/gemini-2.5-flash` |

---

> ⚠️ **Disclaimer:** This tool is for educational, screening, and research purposes only, not personalized investment advice. Scores are quantitative ranking signals, not guarantees of profit.
