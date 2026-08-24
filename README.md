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
- AI Top 5: **5**

### 📊 Rule-Based Top 5

| Rank | Stock | LTP | % Change | RSI | Distance from 52W High | TradingView |
|---:|---|---:|---:|---:|---:|---|
| 1 | **Prizor Viztech** | 1,020.30 | 5.00% | 73.19 | 5.00% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3APRIZOR&interval=D) |
| 2 | **SMVD Poly Pack** | 17.00 | 4.62% | 86.24 | 4.62% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ASMVD&interval=D) |
| 3 | **On Door Concepts** | 290.50 | 18.55% | 70.86 | 1.93% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3AONDOOR&interval=D) |
| 4 | **Service Care** | 64.30 | 4.72% | 66.40 | 0.55% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ASERVICE&interval=D) |
| 5 | **Siemens** | 4,114.00 | 4.95% | 69.47 | -0.10% | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ASIEMENS&interval=D) |

### 🤖 AI Top 5

| Rank | Stock | Score | Momentum | TradingView |
|---:|---|---:|---|---|
| 1 | **Shanthi Gears** | 92 | Excellent momentum driven by significant price appreciation and robust volume, indicating strong buyer interest. The high RSI should be monitored for potential pullbacks. | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ASHANTIGEAR&interval=D) |
| 2 | **Balu Forge Industries** | 89 | Strong momentum with a notable price surge and massive volume. The high RSI points to a powerful trend, but also warrants caution for potential short-term corrections. | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ABALUFORGE&interval=D) |
| 3 | **KRBL** | 85 | Robust momentum with a clear upward trend supported by price and volume. The extremely high RSI suggests strong bullish sentiment but also a need for careful monitoring. | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3AKRBL&interval=D) |
| 4 | **Siemens** | 82 | Solid momentum with price nearing its 52-week high, supported by good volume and a strong, but not extreme, RSI. This indicates a sustained upward trend. | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3ASIEMENS&interval=D) |
| 5 | **Redington** | 80 | Good momentum with a clear upward trajectory, supported by price action, volume, and a strong RSI. The stock is performing well and maintaining its gains near its yearly high. | [Daily Chart ↗](https://www.tradingview.com/chart/?symbol=NSE%3AREDINGTON&interval=D) |

#### AI Selection Details

**1. Shanthi Gears** — Score: **92**

**Why selected:** Shanthi Gears shows exceptional price momentum with a very high percentage change, supported by strong volume and a healthy RSI. Its proximity to the 52-week high further confirms its upward trend.

**Key strengths:**
- Very strong price percentage change (18.25%)
- High volume confirmation
- RSI (84.43) indicates strong momentum
- Relatively close to 52-week high (-7.26%)

**Risk flags:**
- RSI is quite high, suggesting potential short-term overextension

**2. Balu Forge Industries** — Score: **89**

**Why selected:** Balu Forge Industries exhibits very strong price momentum with a high percentage change and outstanding volume, indicating significant market interest. Its RSI is high, confirming strong upward pressure.

**Key strengths:**
- Very strong price percentage change (13.83%)
- Exceptional volume confirmation
- RSI (83.56) indicates strong momentum
- Within 10% of 52-week high (-9.3%)

**Risk flags:**
- RSI is very high, suggesting potential for short-term overextension

**3. KRBL** — Score: **85**

**Why selected:** KRBL demonstrates strong price momentum with a significant percentage change and good volume. Its RSI is very high, indicating strong buying interest, and it's within a reasonable distance from its 52-week high.

**Key strengths:**
- Strong price percentage change (7.58%)
- Good volume confirmation
- Very high RSI (80.04) confirming strong momentum
- Within 10% of 52-week high (-8.6%)

**Risk flags:**
- Very high RSI could indicate short-term overbought conditions

**4. Siemens** — Score: **82**

**Why selected:** Siemens shows strong price appreciation with good volume and is trading very close to its 52-week high. The RSI confirms healthy momentum without being excessively overextended.

**Key strengths:**
- Strong price percentage change (4.95%)
- Good volume confirmation
- Very close to 52-week high (-0.1%)
- Healthy RSI (69.47) indicating strong momentum

**5. Redington** — Score: **80**

**Why selected:** Redington displays strong price momentum with a good percentage change and significant volume. It is trading close to its 52-week high, and its RSI confirms strong buying interest.

**Key strengths:**
- Strong price percentage change (4.15%)
- Significant volume confirmation
- Close to 52-week high (-1.54%)
- Strong RSI (71.06) indicating momentum

#### Market Note

The selected stocks demonstrate strong individual momentum, with several showing significant price appreciation and volume confirmation. A few candidates exhibit very high RSI values, which, while confirming strong momentum, also suggest potential for short-term overextension. Investors should consider broader market conditions and individual risk tolerance.

#### Methodology Note

Stocks were ranked based on a composite score considering price momentum (percentage change), volume confirmation, proximity to 52-week high, and RSI. Higher weight was given to a combination of strong price and volume, and being close to the 52-week high. While high RSI confirms momentum, extremely high values were noted as potential short-term overextension. Secondary factors like PE and market capitalization were considered for tie-breaking or nuanced assessment.

**AI model:** `openrouter/google/gemini-2.5-flash`

</details>
