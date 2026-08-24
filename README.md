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

## Daily Results

## 📅 24 August 2026

<details>
<summary>Show today's scanner results</summary>

### Scanner Summary

- ScanX candidates: **75**
- Stocks within 10% of 52-week high: **36**
- Rule-based Top 5: **5**
- Gemini AI Top 5: **0**

### 📊 Rule-Based Top 5

| Rank | Stock | LTP | % Change | RSI | Distance from 52W High | TradingView |
|---:|---|---:|---:|---:|---:|---|
| 1 | **Prizor Viztech** | 1,020.30 | 5.00% | 73.19 | 5.00% | [Chart ↗](https://www.tradingview.com/symbols/NSE-PRIZOR/) |
| 2 | **SMVD Poly Pack** | 17.00 | 4.62% | 86.24 | 4.62% | [Chart ↗](https://www.tradingview.com/symbols/NSE-SMVD/) |
| 3 | **On Door Concepts** | 290.50 | 18.55% | 70.86 | 1.93% | [Chart ↗](https://www.tradingview.com/symbols/NSE-ONDOOR/) |
| 4 | **Service Care** | 64.30 | 4.72% | 66.40 | 0.55% | [Chart ↗](https://www.tradingview.com/symbols/NSE-SERVICE/) |
| 5 | **Siemens** | 4,114.00 | 4.95% | 69.47 | -0.10% | [Chart ↗](https://www.tradingview.com/symbols/NSE-SIEMENS/) |

### 🤖 Gemini AI Top 5

Gemini AI analysis was unavailable for this run.

#### Market Note

AI analysis unavailable.

#### Methodology Note

Gemini API request failed. Rule-based results are still available.

</details>

> Daily results will be added automatically by GitHub Actions.
