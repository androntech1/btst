# 📈 Daily NSE Momentum Scanner

[![Daily Screener](https://github.com/androntech1/btst/actions/workflows/fetch_data.yml/badge.svg)](https://github.com/androntech1/btst/actions/workflows/fetch_data.yml)
[![Live Dashboard](https://img.shields.io/badge/Live-Web_Dashboard-blue?style=flat&logo=html5)](index.html)

Automated daily momentum watchlist generated from ScanX screening data, 52-week-high filtering, and AI quantitative ranking with real-time news verification.

> 🌐 **Interactive Dashboard:** Open [`index.html`](index.html) locally or on GitHub Pages to view real-time sortable tables, AI score meters, and 1-click TradingView charts.
>
> ⚠️ **Disclaimer:** This tool is for screening and research purposes only, not personalized investment advice. Scores are quantitative ranking signals, not guarantees of profit.

---

## 🏗️ Scanner Architecture & Methodology

```text
ScanX NSE Equity Universe
       │
       ▼
[1] Mechanical Momentum Filter
    • Volume ≥ 2× 10-day SMA Volume
    • Positive Open vs Reference Open (Open > BcOpen)
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
    • data_YYYY-MM-DD.json + data_latest.json
    • manifest.json (date index for web dashboard)
    • Clean README.md & Interactive index.html
```

---

## 📊 Daily Results

## 📅 24 August 2026

<details open>
<summary><strong>Scan Results for 24 August 2026</strong> (Click to toggle)</summary>

### 📈 Scanner Summary

- ScanX Momentum Candidates: **75**
- Within 10% of 52-Week High: **36**
- Rule-Based Top Picks: **5**
- AI Ranked Top Picks: **5**

### 📊 Rule-Based Top 5 (Closest to 52W High)

| Rank | Stock | LTP (₹) | % Change | RSI(14) | Dist from 52W High | TradingView |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| 1 | **Prizor Viztech** | 1,020.30 | 5.00% | 73.19 | 5.00% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3APRIZOR&interval=D) |
| 2 | **SMVD Poly Pack** | 17.00 | 4.62% | 86.24 | 4.62% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ASMVD&interval=D) |
| 3 | **On Door Concepts** | 290.50 | 18.55% | 70.86 | 1.93% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3AONDOOR&interval=D) |
| 4 | **Service Care** | 64.30 | 4.72% | 66.40 | 0.55% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ASERVICE&interval=D) |
| 5 | **Siemens** | 4,114.00 | 4.95% | 69.47 | -0.10% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ASIEMENS&interval=D) |

### 🤖 AI Quantitative Top 5 Picks

| Rank | Stock | AI Score | Momentum Assessment | TradingView |
|:---:|:---|:---:|:---|:---:|
| 1 | **Siemens** | **92/100** | High-conviction large cap momentum setup with steady accumulation near 52-week highs. | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ASIEMENS&interval=D) |
| 2 | **On Door Concepts** | **88/100** | High velocity retail breakout with strong upward momentum. | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3AONDOOR&interval=D) |
| 3 | **Prizor Viztech** | **84/100** | Strong trend-following setup in all-time high territory. | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3APRIZOR&interval=D) |
| 4 | **Service Care** | **79/100** | Constructive base breakout with steady volume participation. | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ASERVICE&interval=D) |
| 5 | **SMVD Poly Pack** | **74/100** | High momentum breakout, best managed with tight trailing stops due to high RSI. | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ASMVD&interval=D) |

#### 🔍 AI Analysis & Context

**1. Siemens** — Score: **92/100**
- **Rationale:** Strong large-cap breakout with high institutional volume, healthy RSI at 69.47, and trading just 0.1% below its 52-week high with robust industrial order book momentum.
- **Recent News:** Siemens recently reported strong industrial demand and steady quarterly earnings growth in energy and automation segments.
- **Strengths:** High market cap stability (₹1.46 Lakh Cr), Healthy RSI of 69.47 indicating solid momentum without extreme overextension, Solid volume expansion (1.3M+ shares)
- **Risk Flags:** Premium valuation with PE at 42.6

**2. On Door Concepts** — Score: **88/100**
- **Rationale:** Exceptional +18.55% single-day price surge accompanied by significant volume expansion and breaking out within 1.93% of 52-week high.
- **Recent News:** Retail expansion plans and positive retail sector sentiment reported recently.
- **Strengths:** Massive +18.55% price momentum, RSI of 70.86 confirming clear breakout velocity, Very close proximity to 52-week high (+1.93%)
- **Risk Flags:** High single-day surge may invite intraday profit booking

**3. Prizor Viztech** — Score: **84/100**
- **Rationale:** Consistent upper-circuit momentum (+5.00%), RSI at 73.19, and trading 5.0% above reference 52-week high with zero overhead supply.
- **Recent News:** Recent expansion in security and surveillance technology product portfolio.
- **Strengths:** Fresh 52-week high breakout territory, RSI at 73.19 confirming steady buyer dominance
- **Risk Flags:** Lower liquidity compared to large caps

**4. Service Care** — Score: **79/100**
- **Rationale:** Healthy +4.72% price action with an ideal RSI of 66.40 (confirming momentum without being overextended) and within 0.55% of 52-week high.
- **Recent News:** Recent announcements regarding staffing contracts and enterprise service additions.
- **Strengths:** Balanced RSI at 66.40 showing sustainable trend strength, Proximity to 52-week breakout
- **Risk Flags:** Small-cap volatility considerations

**5. SMVD Poly Pack** — Score: **74/100**
- **Rationale:** Strong price momentum (+4.62%) and breakout above 52-week high (+4.62%), though elevated RSI at 86.24 cautions short-term consolidation.
- **Recent News:** Packaging sector demand uptick noted in recent industrial reports.
- **Strengths:** Clean breakout above 52-week high, Consistent positive price action
- **Risk Flags:** Elevated RSI (86.24) indicates short-term overbought conditions

> **Market Context:** Broad-based momentum observed across industrial, retail, and manufacturing sectors with 36 candidates sustaining within 10% of their 52-week highs.

*Model: `openrouter/google/gemini-2.5-flash`*

</details>

## 📅 21 August 2026

<details>
<summary><strong>Scan Results for 21 August 2026</strong> (Click to toggle)</summary>

### 📈 Scanner Summary

- ScanX Momentum Candidates: **39**
- Within 10% of 52-Week High: **23**
- Rule-Based Top Picks: **5**

### 📊 Rule-Based Top 5

| Rank | Stock | LTP (₹) | % Change | RSI(14) | Dist from 52W High | TradingView |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| 1 | **SMVD Poly Pack** | 16.25 | 4.84% | 85.00 | 4.84% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ASMVD&interval=D) |
| 2 | **PCCL** | 184.50 | 9.98% | 78.40 | 3.50% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3APCCL&interval=D) |
| 3 | **Sambandam Spinning** | 142.10 | 12.30% | 71.20 | 2.10% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ASAMBANDAM&interval=D) |
| 4 | **Cordelia Cruises** | 312.00 | 5.20% | 68.90 | 1.05% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ACORDELIA&interval=D) |
| 5 | **IIFL Finance** | 679.80 | 6.77% | 77.86 | -1.06% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3AIIFL&interval=D) |

</details>

---

## ⚙️ Setup & Configuration

### Prerequisites
- Python 3.10+
- `pip install -r requirements.txt`

### Environment Variables / GitHub Secrets
| Variable | Description | Default |
|:---|:---|:---|
| `OPENROUTER_API_KEY` | OpenRouter API Key (Required for AI ranking) | - |
| `AI_PROVIDER` | AI Provider (`openrouter` or `openai`) | `openrouter` |
| `AI_MODEL` | Model ID slug | `google/gemini-2.5-flash` |

### Running Locally
```bash
python run_screener.py
```
This will fetch ScanX data, calculate 52W-high metrics via `yfinance`, query AI for ranking and context, and output `data_YYYY-MM-DD.json`, `data_latest.json`, `manifest.json`, and update `README.md`.
