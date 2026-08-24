# 📈 Daily NSE Momentum Scanner

Automated daily momentum watchlist generated from ScanX screening data, 52-week-high filtering, and AI-based quantitative ranking.

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
2. **AI Top 5** — independently ranked using the supplied quantitative fields.

When web search is available, the AI may also check recent company-specific news to provide context for the price/volume move. News does not replace or override the quantitative ranking.

Each stock has a **Daily Chart ↗** link that opens its NSE chart directly on TradingView using the **1D / Daily timeframe**.

## Daily Results

## 📅 24 August 2026

<details>
<summary>Show today's scanner results</summary>

### Scanner Summary

- ScanX candidates: **75**
- Stocks within 10% of 52-week high: **36**
- Rule-based Top 5: **5**
- AI Top 5: **0**

### 📊 Rule-Based Top 5

| Rank | Stock | LTP | % Change | RSI | Distance from 52W High | TradingView |
|---:|---|---:|---:|---:|---:|---|
| 1 | **Prizor Viztech** | 1,020.30 | 5.00% | 73.19 | 5.00% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3APRIZOR&interval=D) |
| 2 | **SMVD Poly Pack** | 17.00 | 4.62% | 86.24 | 4.62% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ASMVD&interval=D) |
| 3 | **On Door Concepts** | 290.50 | 18.55% | 70.86 | 1.93% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3AONDOOR&interval=D) |
| 4 | **Service Care** | 64.30 | 4.72% | 66.40 | 0.55% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ASERVICE&interval=D) |
| 5 | **Siemens** | 4,114.00 | 4.95% | 69.47 | -0.10% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ASIEMENS&interval=D) |

### 🤖 AI Top 5

AI analysis was unavailable for this run.

#### Market Note

AI analysis unavailable.

#### Methodology Note

AI API request failed. Rule-based results are still available.

**AI model:** `openrouter/google/gemini-2.5-flash`

</details>

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
