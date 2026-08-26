from datetime import datetime
import json

# ============================================================
# AI RESPONSE SCHEMA (Strict JSON Schema Compatible)
# ============================================================

AI_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "top_5": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rank": {"type": "integer"},
                    "symbol": {"type": "string"},
                    "display_symbol": {"type": "string"},
                    "score": {"type": "number"},
                    "why_it_was_selected": {"type": "string"},
                    "catalyst": {"type": "string"},
                    "recent_news": {"type": "string"},
                    "technical_rating": {"type": "string"},
                    "event_risk": {"type": "string"},
                    "key_strengths": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "risk_flags": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "momentum_assessment": {"type": "string"},
                },
                "required": [
                    "rank",
                    "symbol",
                    "display_symbol",
                    "score",
                    "why_it_was_selected",
                    "catalyst",
                    "recent_news",
                    "technical_rating",
                    "event_risk",
                    "key_strengths",
                    "risk_flags",
                    "momentum_assessment",
                ],
                "additionalProperties": False,
            },
        },
        "overall_market_note": {"type": "string"},
        "methodology_note": {"type": "string"},
        "generated_by": {"type": "string"},
    },
    "required": [
        "top_5",
        "overall_market_note",
        "methodology_note",
        "generated_by",
    ],
    "additionalProperties": False,
}


# ============================================================
# AI PROMPT
# ============================================================

def build_ai_prompt(ai_stocks):
    """
    Build the next-day (BTST) ranking prompt over enriched candidate objects.
    """
    current_date = datetime.now().strftime("%Y-%m-%d")

    return f"""You are an expert quantitative stock screening assistant for the Indian National Stock Exchange (NSE).
Today's date is {current_date}.

PRIMARY GOAL: rank the TOP 5 candidates MOST LIKELY TO GAP UP OR MAKE A STRONG FAVORABLE MOVE TOMORROW
(a next-day / BTST hold — buy today, sell tomorrow). You are NOT picking the best long-term company; you
are picking the best overnight-to-next-day trade.

All candidate stocks provided below have ALREADY met strict mechanical filters:
1. NSE listed equity.
2. Volume is >= 2x the 10-day average volume.
3. Open is positive relative to previous Open.
4. LTP is positive relative to previous Close.
5. RSI(14) >= 65 (momentum confirmed).
6. LTP is within 10% of 52-week high.

============================================================
ENRICHED DATA PER CANDIDATE (already computed for you)
============================================================
- rule_score      : deterministic composite (0-100) — a baseline, NOT a ceiling; override it with judgment.
- technicals      : pivot / r1 / s1 (tomorrow's support-resistance), ext_above_sma20_pct (overextension),
                    atr_pct (typical daily range = plausible move size), vol_surge (x the 10-day avg volume).
- next_event      : nearest ex-dividend / earnings date with days_away and gap DIRECTION (or null).
- event_risk      : true if an event is imminent (<= 2 days) — a gap catalyst that can help OR hurt.
- flags           : pre-computed risk flags (overbought, overextended, loss-making, event, etc.).

============================================================
HOW TO WEIGH IT (for a 1-DAY move)
============================================================
- LEAD with technicals + a concrete CATALYST. A strong move tomorrow needs momentum leadership (near 52W high,
  real volume surge, healthy-not-exhausted RSI) AND a reason to continue overnight (news, results, order win,
  sector move). State that reason in `catalyst`.
- PENALIZE exhaustion / overextension: a blow-off far above the 20D mean or an extreme RSI often fades or gaps
  DOWN. Reflect this in the score and in `momentum_assessment`.
- Use `pe` and `flags` only as a light QUALITY GATE — break ties and avoid junk (negative-PE / loss-making),
  never as the primary driver of a 1-day call.
- EVENTS: surface gap risk WITH DIRECTION in `event_risk` (e.g. "Ex-dividend tomorrow — long gaps down by the
  dividend"; "Earnings in 1 day — two-sided volatility"). Flag it; never silently ignore it.
- News (if web search available): briefly verify a real catalyst. If unavailable, say
  "Recent-news verification unavailable." Never invent news.

============================================================
STRICT DATA INTEGRITY & OUTPUT RULES
============================================================
- Select and rank the TOP 5 exclusively from the provided candidate list. NEVER invent or modify symbols.
- Treat supplied numerical data as authoritative.
- Give each pick a score 0-100 reflecting probability/magnitude of a FAVORABLE NEXT-DAY move.
- Fill every field: `catalyst` (why it moves tomorrow), `technical_rating` (short read of pivot/overextension/
  RSI/volume), `event_risk` (imminent event + direction, or "None"), plus strengths, risks, momentum_assessment.
- Output must be strict JSON adhering to the specified schema.

============================================================
CANDIDATE DATA
============================================================
{json.dumps(ai_stocks, separators=(",", ":"), default=str)}
"""
