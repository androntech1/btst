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

> Daily results will be added automatically by GitHub Actions.
