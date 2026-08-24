from datetime import datetime
import json
import copy
import os

import requests
import yfinance as yf


# ============================================================
# CONFIGURATION
# ============================================================

SCANX_URL = "https://ow-scanx-analytics.dhan.co/customscan/v2/fetchdt"

SCANX_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://scanx.trade",
}

# Gemini REST API
# Keep the API key OUT of this file.
# GitHub Actions will provide it through:
# GEMINI_API_KEY
GEMINI_MODEL = "gemini-3.7-flash"

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/{GEMINI_MODEL}:generateContent"
)


# ============================================================
# SCANX PAYLOAD
# ============================================================

SCANX_PAYLOAD = {
    "data": {
        "count": 100,
        "sort": "Mcap",
        "sorder": "desc",
        "fields": [
            "DispSym",
            "Ltp",
            "Pchange",
            "PPerchange",
            "Volume",
            "Pe",
            "Mcap",
            "Open",
            "BcOpen",
            "BcClose",
            "DayRSI14CurrentCandle",
            "Sym",
        ],
        "pgno": 1,
        "query": {
            "logic_op": "AND",
            "params": [
                {
                    "field": "Exch",
                    "op": "eq",
                    "val": "NSE",
                },
                {
                    "field": "Volume",
                    "op": "gte",
                    "field2": "DaySMA10VolMul_2",
                    "val": "",
                },
                {
                    "field": "Open",
                    "op": "gt",
                    "field2": "BcOpen",
                    "val": "",
                },
                {
                    "field": "Ltp",
                    "op": "gt",
                    "field2": "BcClose",
                    "val": "",
                },
                {
                    "field": "DayRSI14CurrentCandle",
                    "op": "gte",
                    "val": "65",
                },
                {
                    "field": "OgInst",
                    "op": "eq",
                    "val": "ES",
                },
                {
                    "field": "Volume",
                    "op": "gte",
                    "val": "0",
                },
            ],
        },
    }
}


# ============================================================
# GEMINI AI FUNCTION
# ============================================================

def get_ai_top_5_picks(filtered_rows, filtered_headers):
    """
    Send filtered stock candidates to Gemini and ask it to
    independently rank the best 5 candidates.

    The API key is read from the GEMINI_API_KEY environment variable.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set. "
            "Add GEMINI_API_KEY to GitHub Actions Secrets."
        )

    # --------------------------------------------------------
    # Convert rows into dictionaries
    # --------------------------------------------------------

    stocks = []

    for row in filtered_rows:
        stock = dict(zip(filtered_headers, row))
        stocks.append(stock)

    if not stocks:
        return {
            "top_5": [],
            "overall_market_note": (
                "No stocks passed the mechanical filtering criteria."
            ),
            "methodology_note": (
                "Gemini was not required because there were no candidates."
            ),
            "generated_by": GEMINI_MODEL,
        }

    # --------------------------------------------------------
    # Fields that Gemini should analyze
    # --------------------------------------------------------

    useful_fields = [
        "DispSym",
        "Ltp",
        "Pchange",
        "PPerchange",
        "Volume",
        "Pe",
        "Mcap",
        "Open",
        "BcOpen",
        "BcClose",
        "DayRSI14CurrentCandle",
        "Sym",
        "Calculated52WkHigh",
        "DistFrom52WkHighPct",
    ]

    ai_stocks = []

    for stock in stocks:
        clean_stock = {}

        for field in useful_fields:
            if field in stock:
                clean_stock[field] = stock[field]

        ai_stocks.append(clean_stock)

    # --------------------------------------------------------
    # AI PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are a quantitative stock-screening assistant.

Your task is to rank Indian NSE stocks for a DAILY MOMENTUM WATCHLIST.

The candidate stocks supplied below have ALREADY passed these
mechanical screening conditions:

1. NSE listed.
2. Volume is at least 2x the 10-day average volume.
3. Current Open is greater than the reference/previous Open.
4. Current LTP is greater than the reference/previous Close.
5. RSI(14) is at least 65.
6. Current LTP is within 10% of the 52-week high.

You must now independently rank ONLY the supplied candidates.

========================
STRICT RULES
========================

- Select ONLY stocks present in the supplied candidate data.
- NEVER invent a stock symbol.
- NEVER modify a stock symbol.
- NEVER create a stock that is not in the input.
- Do not use outside company knowledge.
- Do not use information that is not present in the supplied data.
- Do not predict with certainty.
- Do not guarantee profit.
- Do not use phrases such as "guaranteed winner", "sure shot",
  "certain profit", or "risk-free".
- This is a quantitative ranking/watchlist, NOT personalized investment advice.
- Do not simply rank by RSI.
- Do not simply rank by percentage change.
- Consider multiple independent signals.
- Strong volume confirmation is positive.
- Strong price momentum is positive.
- Being close to the 52-week high is positive.
- Positive Open/price action is positive.
- RSI >= 65 confirms momentum.
- Extremely high RSI may indicate short-term overextension and should
  therefore be considered a risk factor rather than automatically being
  treated as better.
- PE can be considered as a secondary factor when available.
- Market capitalization can be considered as a secondary liquidity/stability
  factor.
- Prefer stocks with confirmation from several signals.
- Penalize obvious signs of excessive short-term extension when appropriate.
- If two candidates are similar, prefer the candidate with stronger
  confirmation across multiple fields.

========================
RANKING FRAMEWORK
========================

Use the following approximate priorities:

1. Overall price momentum
2. Volume confirmation
3. Proximity to 52-week high
4. RSI confirmation while considering overextension
5. Positive price action
6. PE and market capitalization as secondary factors

The score should be your overall quantitative assessment from 0 to 100.

Do NOT pretend the score is a probability of profit.

========================
OUTPUT REQUIREMENTS
========================

Select the BEST 5 candidates.

For each selected stock provide:

- rank
- symbol
- display_symbol
- score
- why_it_was_selected
- key_strengths
- risk_flags
- momentum_assessment

Also provide:

- overall_market_note
- methodology_note
- generated_by

Return ONLY valid JSON.

Do NOT return Markdown.
Do NOT return code fences.
Do NOT add any text outside the JSON.

========================
CANDIDATE DATA
========================

{json.dumps(ai_stocks, separators=(",", ":"), default=str)}
"""

    # --------------------------------------------------------
    # STRUCTURED JSON SCHEMA
    # --------------------------------------------------------

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "top_5": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "rank": {
                            "type": "INTEGER",
                        },
                        "symbol": {
                            "type": "STRING",
                        },
                        "display_symbol": {
                            "type": "STRING",
                        },
                        "score": {
                            "type": "NUMBER",
                        },
                        "why_it_was_selected": {
                            "type": "STRING",
                        },
                        "key_strengths": {
                            "type": "ARRAY",
                            "items": {
                                "type": "STRING",
                            },
                        },
                        "risk_flags": {
                            "type": "ARRAY",
                            "items": {
                                "type": "STRING",
                            },
                        },
                        "momentum_assessment": {
                            "type": "STRING",
                        },
                    },
                    "required": [
                        "rank",
                        "symbol",
                        "display_symbol",
                        "score",
                        "why_it_was_selected",
                        "key_strengths",
                        "risk_flags",
                        "momentum_assessment",
                    ],
                },
            },
            "overall_market_note": {
                "type": "STRING",
            },
            "methodology_note": {
                "type": "STRING",
            },
            "generated_by": {
                "type": "STRING",
            },
        },
        "required": [
            "top_5",
            "overall_market_note",
            "methodology_note",
            "generated_by",
        ],
    }

    # --------------------------------------------------------
    # GEMINI REQUEST
    # --------------------------------------------------------

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key,
    }

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt,
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "response_mime_type": "application/json",
            "response_schema": response_schema,
        },
    }

    print(
        f"Sending {len(ai_stocks)} candidates to "
        f"{GEMINI_MODEL} for AI ranking..."
    )

    response = requests.post(
        GEMINI_URL,
        headers=headers,
        json=payload,
        timeout=120,
    )

    # This gives us the actual HTTP error if Gemini rejects the request.
    if not response.ok:
        raise RuntimeError(
            f"Gemini API request failed "
            f"(HTTP {response.status_code}):\n"
            f"{response.text}"
        )

    result = response.json()

    # --------------------------------------------------------
    # EXTRACT GEMINI RESPONSE
    # --------------------------------------------------------

    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(
            "Could not find generated text in Gemini response.\n"
            f"Error: {e}\n"
            f"Response:\n{json.dumps(result, indent=2)}"
        )

    try:
        ai_result = json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "Gemini returned invalid JSON.\n"
            f"Error: {e}\n"
            f"Raw response:\n{text}"
        )

    # --------------------------------------------------------
    # VALIDATE SYMBOLS
    # --------------------------------------------------------

    sym_index = filtered_headers.index("Sym")

    allowed_symbols = {
        str(row[sym_index]).strip()
        for row in filtered_rows
    }

    validated_top_5 = []

    for pick in ai_result.get("top_5", []):
        symbol = str(pick.get("symbol", "")).strip()

        if symbol in allowed_symbols:
            validated_top_5.append(pick)
        else:
            print(
                f"WARNING: Gemini returned a symbol that was "
                f"not in the candidate list: {symbol}"
            )

    # --------------------------------------------------------
    # SORT BY AI RANK
    # --------------------------------------------------------

    validated_top_5.sort(
        key=lambda item: item.get("rank", 999)
    )

    # Keep maximum 5.
    validated_top_5 = validated_top_5[:5]

    ai_result["top_5"] = validated_top_5

    # Make sure generated_by is controlled by our program.
    ai_result["generated_by"] = GEMINI_MODEL

    return ai_result


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print("=" * 70)
    print("DAILY STOCK SCANNER")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. FETCH DATA FROM SCANX
    # --------------------------------------------------------

    print("\nFetching data from ScanX API...")

    response = requests.post(
        SCANX_URL,
        headers=SCANX_HEADERS,
        json=SCANX_PAYLOAD,
        timeout=60,
    )

    if not response.ok:
        raise RuntimeError(
            f"ScanX API request failed "
            f"(HTTP {response.status_code}):\n"
            f"{response.text}"
        )

    raw_data = response.json()

    # Preserve deep copy of original response.
    original_data = copy.deepcopy(raw_data)

    # --------------------------------------------------------
    # Validate ScanX response
    # --------------------------------------------------------

    if "headers" not in raw_data:
        raise RuntimeError(
            "ScanX response does not contain 'headers'."
        )

    if "data" not in raw_data:
        raise RuntimeError(
            "ScanX response does not contain 'data'."
        )

    headers_list = raw_data["headers"]
    rows = raw_data["data"]

    if not rows:
        print("ScanX returned zero stocks.")

    print(f"ScanX returned {len(rows)} stocks.")

    # --------------------------------------------------------
    # 2. ADD 52-WEEK HIGH COLUMNS
    # --------------------------------------------------------

    filtered_headers = list(headers_list)

    filtered_headers.extend(
        [
            "Calculated52WkHigh",
            "DistFrom52WkHighPct",
        ]
    )

    try:
        sym_idx = headers_list.index("Sym")
        ltp_idx = headers_list.index("Ltp")
    except ValueError as e:
        raise RuntimeError(
            f"Required ScanX field missing: {e}"
        )

    filtered_rows = []
    filtered_symbols = []

    print(
        f"\nProcessing {len(rows)} stocks and checking "
        f"52-week highs via yfinance..."
    )

    # --------------------------------------------------------
    # 3. YFINANCE 52-WEEK HIGH FILTER
    # --------------------------------------------------------

    for row in rows:

        try:
            sym = str(row[sym_idx]).strip()
            ltp = float(row[ltp_idx])
        except (ValueError, TypeError, IndexError) as e:
            print(
                f"Skipping malformed row due to error: {e}"
            )
            continue

        ticker_symbol = f"{sym}.NS"

        try:
            print(
                f"Checking {ticker_symbol}..."
            )

            ticker = yf.Ticker(ticker_symbol)

            hist = ticker.history(
                period="1y",
                auto_adjust=False
            )

            if hist.empty:
                print(
                    f"  No historical data available for {sym}"
                )
                continue

            # Make sure High contains valid numerical values.
            high_series = hist["High"].dropna()

            if high_series.empty:
                print(
                    f"  No High values available for {sym}"
                )
                continue

            wk52_high = float(high_series.max())

            # ------------------------------------------------
            # FILTER:
            # Stock must be within 10% of 52-week high
            # ------------------------------------------------

            if ltp >= (0.90 * wk52_high):

                dist_pct = round(
                    ((ltp - wk52_high) / wk52_high) * 100,
                    2
                )

                new_row = list(row)

                new_row.append(
                    round(wk52_high, 2)
                )

                new_row.append(
                    dist_pct
                )

                filtered_rows.append(new_row)
                filtered_symbols.append(sym)

                print(
                    f"  PASS | LTP={ltp:.2f} | "
                    f"52W High={wk52_high:.2f} | "
                    f"Distance={dist_pct:.2f}%"
                )

            else:
                print(
                    f"  FAIL | LTP={ltp:.2f} | "
                    f"52W High={wk52_high:.2f}"
                )

        except Exception as e:
            print(
                f"Skipping {sym} due to yfinance error: {e}"
            )

    print(
        f"\n52-week filter complete. "
        f"{len(filtered_rows)} stocks passed."
    )

    # --------------------------------------------------------
    # 4. BUILD FILTERED RESPONSE
    # --------------------------------------------------------

    filtered_data = copy.deepcopy(raw_data)

    filtered_data["headers"] = filtered_headers
    filtered_data["data"] = filtered_rows
    filtered_data["tot_rec"] = len(filtered_rows)

    # --------------------------------------------------------
    # 5. RULE-BASED TOP 5
    # --------------------------------------------------------

    dist_idx = filtered_headers.index(
        "DistFrom52WkHighPct"
    )

    sorted_filtered_rows = sorted(
        filtered_rows,
        key=lambda x: x[dist_idx],
        reverse=True,
    )

    top_5_rows = sorted_filtered_rows[:5]

    top_5_data = copy.deepcopy(filtered_data)

    top_5_data["data"] = top_5_rows
    top_5_data["tot_rec"] = len(top_5_rows)

    top_5_symbols = [
        row[sym_idx]
        for row in top_5_rows
    ]

    print("\nRule-based Top 5:")
    for rank, symbol in enumerate(
        top_5_symbols,
        start=1
    ):
        print(
            f"  {rank}. {symbol}"
        )

    # --------------------------------------------------------
    # 6. GEMINI AI TOP 5
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("GEMINI AI ANALYSIS")
    print("=" * 70)

    try:

        ai_top_5_data = get_ai_top_5_picks(
            filtered_rows,
            filtered_headers,
        )

        print("\nGemini AI Top 5:")

        for pick in ai_top_5_data.get("top_5", []):

            print(
                f"  {pick.get('rank')}. "
                f"{pick.get('symbol')} "
                f"(Score: {pick.get('score')})"
            )

        print(
            "\nGemini AI analysis completed successfully."
        )

    except Exception as e:

        print(
            "\nWARNING: Gemini AI analysis failed."
        )

        print(
            f"Reason: {e}"
        )

        # IMPORTANT:
        # Do not fail the entire stock scanner if Gemini
        # is temporarily unavailable.

        ai_top_5_data = {
            "top_5": [],
            "overall_market_note": (
                "AI analysis unavailable."
            ),
            "methodology_note": (
                "Gemini API request failed. "
                "Rule-based results are still available."
            ),
            "generated_by": GEMINI_MODEL,
            "error": str(e),
        }

    # --------------------------------------------------------
    # 7. MASTER OUTPUT
    # --------------------------------------------------------

    now = datetime.now()

    master_output = {
        "date": now.strftime("%Y-%m-%d"),

        "timestamp": now.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        # Original ScanX response
        "original_scanx_results": original_data,

        # Stocks passing 52-week high filter
        "filtered_52w_results": filtered_data,

        # Existing rule-based Top 5
        "top_5_picks": top_5_data,

        # Existing rule-based symbols
        "top_5_symbols": top_5_symbols,

        # All symbols passing the 52-week filter
        "filtered_symbols": filtered_symbols,

        # NEW: Gemini AI Top 5
        "ai_top_5_picks": ai_top_5_data,
    }

    # --------------------------------------------------------
    # 8. SAVE JSON
    # --------------------------------------------------------

    today_date = now.strftime(
        "%Y-%m-%d"
    )

    filename = f"data_{today_date}.json"

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            master_output,
            f,
            indent=4,
            ensure_ascii=False,
        )

    # --------------------------------------------------------
    # 9. FINAL SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("SCAN COMPLETE")
    print("=" * 70)

    print(
        f"Original stocks:       {len(rows)}"
    )

    print(
        f"52W filtered stocks:   {len(filtered_rows)}"
    )

    print(
        f"Rule-based Top 5:      {len(top_5_rows)}"
    )

    print(
        f"AI Top 5:              "
        f"{len(ai_top_5_data.get('top_5', []))}"
    )

    print(
        f"Output file:           {filename}"
    )

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
