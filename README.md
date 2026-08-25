# 📈 Daily NSE Momentum Scanner & AI Engine

[![Daily Screener](https://github.com/androntech1/btst/actions/workflows/fetch_data.yml/badge.svg)](https://github.com/androntech1/btst/actions/workflows/fetch_data.yml)
[![Live Web Dashboard](https://img.shields.io/badge/Live_Dashboard-androntech1.github.io%2Fbtst-06b6d4?style=flat&logo=googlechrome)](https://androntech1.github.io/btst/)

Automated daily momentum scanner for Indian NSE equities featuring 52-week-high breakout filtering, AI quantitative ranking, real-time corporate news verification, and 1-click TradingView charts.

---

## 🌐 Live Web Dashboard

Access the full interactive dashboard with real-time sortable tables, AI score meters, strength tags, risk flags, and historical scans:

👉 **[https://androntech1.github.io/btst/](https://androntech1.github.io/btst/)**

### ⚡ Latest Scan Summary (25 August 2026)
- **ScanX Candidates:** 27
- **Passed 52W High Filter:** 16 stocks within 10% of 52W High
- **Top AI Quantitative Pick:** Available on live dashboard
- **Data Exports:** [`data/data_latest.json`](data/data_latest.json) • [`data/manifest.json`](data/manifest.json)

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
[2] 52-Week High Proximity Filter (yfinance)
    • Current LTP within 10% of 52-Week High
       │
       ├──► Rule-Based Top 5 (sorted by closest proximity to 52W High)
       │
       ▼
[3] AI Quantitative & News Ranking (OpenRouter / Gemini)
    • Multi-factor ranking: Momentum, Volume Surge, RSI Health, Mcap/PE
    • Server-side news verification for candidate context
    • Output: AI Top 5 with Score (0-100), Strengths, Risks & Rationale
       │
       ▼
[4] Master Exports
    • data/data_YYYY-MM-DD.json + data/data_latest.json
    • data/manifest.json (date index for web dashboard)
    • Interactive index.html on GitHub Pages
```

---

## ⚙️ Setup & Configuration

### Automated Schedule
- Runs automatically via GitHub Actions **Monday to Friday at 3:10 PM IST** (`10 15 * * 1-5`, `Asia/Kolkata`).
- Scans data 20 minutes before market close, ideal for BTST / momentum entries.

### Running Locally
```bash
pip install -r requirements.txt
python run_screener.py
```

### Environment Variables / Secrets
| Variable | Description | Default |
|:---|:---|:---|
| `OPENROUTER_API_KEY` | OpenRouter API Key (Required for AI ranking) | - |
| `AI_PROVIDER` | AI Provider (`openrouter` or `openai`) | `openrouter` |
| `AI_MODEL` | AI Model slug | `google/gemini-2.5-flash` |

---

> ⚠️ **Disclaimer:** This tool is for educational, screening, and research purposes only, not personalized investment advice. Scores are quantitative ranking signals, not guarantees of profit.
