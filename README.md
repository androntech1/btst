# 📈 Daily NSE Momentum Scanner

Automated daily momentum watchlist generated from ScanX screening data, 52-week-high filtering, and Gemini-based quantitative ranking.

> **Note:** This is a screening/watchlist tool, not personalized investment advice. Scores are quantitative rankings and are not probabilities of profit.

## How the scanner works

The scanner first applies mechanical conditions to NSE stocks:

- Volume ≥ 2× 10-day average volume
- Positive opening/price action
- LTP above the reference close
- RSI(14) ≥ 65
- LTP within 10% of the 52-week high

Stocks passing those conditions are then ranked in two ways:

1. **Rule-Based Top 5** — sorted by proximity to the 52-week high.
2. **Gemini AI Top 5** — independently ranked using the supplied quantitative fields.

Each stock has a **Chart ↗** link that opens its NSE chart on TradingView.

## 🏗️ Scanner Architecture

```text
ScanX NSE Universe
       │
       ▼
Mechanical Momentum Filter
(volume ≥ 2× avg, positive price action, RSI ≥ 65)
       │
       ▼
52-Week High Filter
(LTP within 10% of 52W high via yfinance)
       │
       ├──────────────► Rule-Based Top 5
       │                (closest to 52W high)
       │
       ▼
AI Ranking Layer
(Gemini via OpenRouter)
       │
       ├── Quantitative ranking first
       │   • price momentum
       │   • volume confirmation
       │   • 52W-high proximity
       │   • RSI / overextension
       │   • PE & market cap as secondary factors
       │
       └── Recent-news verification
           • results / orders
           • corporate actions
           • regulatory developments
           • upgrades / downgrades
           • only for supplied candidates
           • never used to invent candidates
       │
       ▼
Validated AI Top 5
       │
       ▼
Daily JSON + README Dashboard
