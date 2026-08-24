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
                    "recent_news": {"type": "string"},
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
                    "recent_news",
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
    Build the quantitative ranking prompt.
    """
    current_date = datetime.now().strftime("%Y-%m-%d")

    return f"""You are an expert quantitative stock screening assistant for the Indian National Stock Exchange (NSE).
Today's date is {current_date}.

Your task is to rank Indian NSE momentum candidates for a DAILY MOMENTUM WATCHLIST.

All candidate stocks provided below have ALREADY met strict mechanical filters:
1. NSE listed equity.
2. Volume is >= 2x the 10-day average volume.
3. Open is positive relative to previous Open.
4. LTP is positive relative to previous Close.
5. RSI(14) >= 65 (momentum confirmed).
6. LTP is within 10% of 52-week high.

============================================================
STRICT DATA INTEGRITY & RANKING RULES
============================================================
- Select and rank the TOP 5 BEST candidates exclusively from the provided candidate list.
- NEVER invent, modify, or hallucinate stock symbols.
- Treat supplied numerical data as authoritative.
- Give each of the top 5 stocks a quantitative score from 0 to 100 based on momentum strength, volume surge, RSI health, 52W-high proximity, and sound valuation/mcap metrics.
- Overextension check: While RSI >= 65 confirms momentum, evaluate if volume and price action sustain the move without extreme bubble risk.
- Web search / news (if available): Briefly check recent corporate news (e.g., quarterly results, contract wins, acquisitions, management actions) to explain the move. News is contextual and must not override quantitative fundamentals. If search is not available, mention "Recent-news verification unavailable."
- Risk flags: Note concrete risks (e.g. high RSI overbought, high PE, lower volume vs peers).
- Output must be strict JSON adhering to the specified schema.

============================================================
CANDIDATE DATA
============================================================
{json.dumps(ai_stocks, separators=(",", ":"), default=str)}
"""
