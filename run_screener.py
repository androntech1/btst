from datetime import datetime
import json
import copy
import os
import re
from urllib.parse import quote

import requests
import yfinance as yf

from prompts import AI_RESPONSE_SCHEMA, build_ai_prompt


# ============================================================
# CONFIGURATION
# ============================================================

SCANX_URL = "https://ow-scanx-analytics.dhan.co/customscan/v2/fetchdt"

SCANX_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://scanx.trade",
}


# ============================================================
# AI CONFIGURATION
# ============================================================

AI_PROVIDER = os.getenv("AI_PROVIDER", "openrouter").strip().lower()
AI_MODEL = os.getenv("AI_MODEL", "google/gemini-2.5-flash").strip()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

DATA_DIR = "data"
README_FILE = "README.md"
LATEST_DATA_FILE = os.path.join(DATA_DIR, "data_latest.json")
MANIFEST_FILE = os.path.join(DATA_DIR, "manifest.json")


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
# TRADINGVIEW LINK
# ============================================================

def tradingview_url(symbol):
    """
    Build a TradingView chart URL for an NSE symbol (Daily timeframe).
    """
    clean_symbol = str(symbol).strip().upper()
    if not clean_symbol:
        return ""
    tradingview_symbol = f"NSE:{clean_symbol}"
    encoded_symbol = quote(tradingview_symbol, safe="")
    return f"https://www.tradingview.com/chart/?symbol={encoded_symbol}&interval=D"


# ============================================================
# MARKDOWN HELPERS
# ============================================================

def markdown_escape(value):
    """
    Escape characters that can interfere with Markdown tables.
    """
    if value is None:
        return ""
    text = str(value)
    return (
        text.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\n", " ")
        .replace("\r", " ")
    )


def format_number(value, decimals=2):
    """
    Format numeric values safely for Markdown.
    """
    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "-"


def format_percent(value):
    """
    Format a percentage value.
    """
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "-"


def get_stock_from_row(row, headers):
    """
    Convert a ScanX row into a dictionary.
    """
    return dict(zip(headers, row))


# ============================================================
# AI API HELPERS
# ============================================================

def get_ai_api_configuration():
    """
    Return the API URL, API key and headers based on the selected AI provider.
    """
    if AI_PROVIDER == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY environment variable is not set. "
                "Add OPENROUTER_API_KEY to GitHub Actions Secrets."
            )
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/",
            "X-Title": "Daily NSE Momentum Scanner",
        }
        return OPENROUTER_URL, headers

    if AI_PROVIDER == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable is not set. "
                "Add OPENAI_API_KEY to GitHub Actions Secrets."
            )
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        return OPENAI_URL, headers

    raise RuntimeError(
        f"Unsupported AI_PROVIDER: {AI_PROVIDER}. "
        f"Supported providers: openrouter, openai."
    )


def extract_ai_text(response_json):
    """
    Extract the assistant's text from an OpenAI/OpenRouter chat completion response.
    """
    try:
        choices = response_json.get("choices", [])
        if not choices:
            raise RuntimeError(f"No choices in response: {response_json}")
        message = choices[0].get("message", {})
        content = message.get("content")
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(
            f"Could not find generated text in AI response.\nError: {e}\n"
            f"Response:\n{json.dumps(response_json, indent=2)}"
        )

    if content is None:
        raise RuntimeError("AI returned an empty response.")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict):
                text = part.get("text")
                if text:
                    text_parts.append(str(text))
        if text_parts:
            return "".join(text_parts)

    raise RuntimeError(f"AI returned content in unexpected format: {repr(content)}")


def parse_ai_json(text):
    """
    Robustly parse JSON returned by AI.
    Handles markdown code blocks, thoughts, citations, and extra preambles.
    """
    clean_text = str(text).strip()

    # 1. Strip reasoning tags if present
    clean_text = re.sub(r"<thought>[\s\S]*?</thought>", "", clean_text, flags=re.IGNORECASE).strip()
    clean_text = re.sub(r"<think>[\s\S]*?</think>", "", clean_text, flags=re.IGNORECASE).strip()

    # 2. Check for markdown code blocks (```json ... ``` or ``` ... ```)
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean_text, flags=re.IGNORECASE)
    if code_block_match:
        candidate_json = code_block_match.group(1).strip()
        try:
            return json.loads(candidate_json)
        except json.JSONDecodeError:
            pass

    # 3. Direct JSON parse
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        pass

    # 4. Extract outer JSON object {...}
    json_match = re.search(r"(\{[\s\S]*\})", clean_text)
    if json_match:
        candidate_json = json_match.group(1).strip()
        try:
            return json.loads(candidate_json)
        except json.JSONDecodeError:
            # Try removing trailing commas
            fixed_json = re.sub(r",\s*([\]}])", r"\1", candidate_json)
            try:
                return json.loads(fixed_json)
            except json.JSONDecodeError:
                pass

    raise RuntimeError(
        f"AI returned text that could not be parsed as valid JSON.\nRaw output:\n{clean_text[:1000]}"
    )


# ============================================================
# AI TOP 5 FUNCTION WITH AUTOMATED FALLBACK
# ============================================================

def get_ai_top_5_picks(filtered_rows, filtered_headers):
    """
    Send filtered candidates to the AI provider to rank the top 5 picks.
    Includes automated fallback if web search or schema validation encounters issues.
    """
    stocks = []
    for row in filtered_rows:
        stock = dict(zip(filtered_headers, row))
        stocks.append(stock)

    if not stocks:
        return {
            "top_5": [],
            "overall_market_note": "No stocks passed the mechanical filtering criteria.",
            "methodology_note": "AI ranking was not required because there were no candidates.",
            "generated_by": f"{AI_PROVIDER}/{AI_MODEL}",
        }

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
        clean_stock = {field: stock[field] for field in useful_fields if field in stock}
        ai_stocks.append(clean_stock)

    prompt = build_ai_prompt(ai_stocks)
    api_url, headers = get_ai_api_configuration()

    print(f"Sending {len(ai_stocks)} candidates to {AI_PROVIDER} / {AI_MODEL} for AI ranking...")

    # Build primary payload with strict json_schema
    base_payload = {
        "model": AI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a quantitative stock screener assistant for the Indian NSE stock market. "
                    "You must output exclusively structured JSON complying with the requested schema."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
    }

    ai_result = None
    last_error = None

    # ATTEMPT 1: With strict schema and optional OpenRouter web search tool
    try:
        payload_1 = copy.deepcopy(base_payload)
        payload_1["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "nse_momentum_top_5",
                "strict": True,
                "schema": AI_RESPONSE_SCHEMA,
            },
        }

        if AI_PROVIDER == "openrouter":
            payload_1["tools"] = [
                {
                    "type": "openrouter:web_search",
                    "parameters": {
                        "max_results": 5,
                        "max_total_results": 10,
                    },
                }
            ]
            payload_1["max_tool_calls"] = 5

        print("Executing AI analysis (Attempt 1: Structured schema + Web Search)...")
        response = requests.post(api_url, headers=headers, json=payload_1, timeout=120)

        if response.ok:
            result_json = response.json()
            text = extract_ai_text(result_json)
            ai_result = parse_ai_json(text)
        else:
            print(f"Attempt 1 failed with status {response.status_code}: {response.text[:300]}")
            last_error = f"HTTP {response.status_code}: {response.text[:300]}"

    except Exception as e:
        print(f"Attempt 1 encountered exception: {e}")
        last_error = str(e)

    # ATTEMPT 2 (FALLBACK): If Attempt 1 failed, call without tools in standard JSON mode
    if not ai_result or not isinstance(ai_result, dict) or "top_5" not in ai_result:
        print("Executing AI analysis fallback (Attempt 2: Direct JSON mode without external tools)...")
        try:
            payload_2 = copy.deepcopy(base_payload)
            payload_2["response_format"] = {"type": "json_object"}
            response = requests.post(api_url, headers=headers, json=payload_2, timeout=90)
            if not response.ok:
                raise RuntimeError(f"Fallback request failed with HTTP {response.status_code}: {response.text}")
            result_json = response.json()
            text = extract_ai_text(result_json)
            ai_result = parse_ai_json(text)
        except Exception as fallback_e:
            print(f"Fallback Attempt 2 failed: {fallback_e}")
            raise RuntimeError(f"AI ranking failed in both attempts. Primary error: {last_error}; Fallback error: {fallback_e}")

    # Validate top_5 structure
    if not isinstance(ai_result, dict):
        raise RuntimeError("AI response root must be a JSON object.")

    raw_top_5 = ai_result.get("top_5")
    if not isinstance(raw_top_5, list):
        for alt_key in ["top5", "picks", "top_picks", "candidates"]:
            if isinstance(ai_result.get(alt_key), list):
                raw_top_5 = ai_result[alt_key]
                break

    if not isinstance(raw_top_5, list):
        raise RuntimeError("AI response does not contain a valid top_5 array.")

    # Validate symbols against candidates
    sym_index = filtered_headers.index("Sym")
    allowed_symbols = {str(row[sym_index]).strip().upper() for row in filtered_rows}

    validated_top_5 = []
    seen_symbols = set()

    for pick in raw_top_5:
        if not isinstance(pick, dict):
            continue

        symbol = str(pick.get("symbol", "")).strip().upper()
        if symbol not in allowed_symbols:
            print(f"WARNING: AI returned a symbol not in candidate list: {symbol}. Skipping.")
            continue

        if symbol in seen_symbols:
            print(f"WARNING: AI returned duplicate symbol: {symbol}. Skipping.")
            continue

        seen_symbols.add(symbol)

        # Match actual display symbol
        actual_display_symbol = symbol
        display_index = filtered_headers.index("DispSym")
        matching_rows = [row for row in filtered_rows if str(row[sym_index]).strip().upper() == symbol]
        if matching_rows:
            actual_display_symbol = str(matching_rows[0][display_index]).strip()

        pick["symbol"] = symbol
        pick["display_symbol"] = actual_display_symbol

        # Clean string / list fields
        pick["recent_news"] = str(pick.get("recent_news", "") or "").strip()
        pick["why_it_was_selected"] = str(pick.get("why_it_was_selected", "") or "").strip()
        pick["momentum_assessment"] = str(pick.get("momentum_assessment", "") or "").strip()

        # Risk flags
        risk_flags = pick.get("risk_flags", [])
        if not isinstance(risk_flags, list):
            risk_flags = [str(risk_flags)]
        pick["risk_flags"] = [str(item).strip() for item in risk_flags if str(item).strip()]

        # Key strengths
        key_strengths = pick.get("key_strengths", [])
        if not isinstance(key_strengths, list):
            key_strengths = [str(key_strengths)]
        pick["key_strengths"] = [str(item).strip() for item in key_strengths if str(item).strip()]

        # Score clamp 0-100
        try:
            score = float(pick.get("score", 0))
            score = max(0.0, min(100.0, score))
            if score.is_integer():
                score = int(score)
            pick["score"] = score
        except (TypeError, ValueError):
            pick["score"] = 0

        validated_top_5.append(pick)

    # Sort and re-rank
    validated_top_5.sort(key=lambda item: item.get("score", 0), reverse=True)
    validated_top_5 = validated_top_5[:5]
    for idx, pick in enumerate(validated_top_5, start=1):
        pick["rank"] = idx

    ai_result["top_5"] = validated_top_5
    ai_result["generated_by"] = f"{AI_PROVIDER}/{AI_MODEL}"
    return ai_result


# ============================================================
# DATA EXPORTS: LATEST JSON & MANIFEST
# ============================================================

def update_manifest_and_latest(today_date, master_output):
    """
    Save data_latest.json and update manifest.json in data/ directory with all available scan dates.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    # 1. Save data/data_latest.json
    with open(LATEST_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(master_output, f, indent=4, ensure_ascii=False)
    print(f"Latest data saved to {LATEST_DATA_FILE}")

    # 2. Collect all available daily json files in data/
    dates = {today_date}
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.startswith("data_") and filename.endswith(".json") and filename != "data_latest.json":
                d = filename[5:-5]
                if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
                    dates.add(d)

    sorted_dates = sorted(list(dates), reverse=True)

    manifest_data = {
        "latest_date": today_date,
        "available_dates": sorted_dates,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ai_model": f"{AI_PROVIDER}/{AI_MODEL}",
    }

    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=4, ensure_ascii=False)
    print(f"Manifest updated with {len(sorted_dates)} dates: {MANIFEST_FILE}")

    # 3. Update embedded data in index.html for direct file:// and offline viewing
    if os.path.exists("index.html"):
        try:
            with open("index.html", "r", encoding="utf-8") as f:
                html_content = f.read()

            json_str = json.dumps(master_output, separators=(",", ":"), ensure_ascii=False)
            manifest_str = json.dumps(manifest_data, separators=(",", ":"), ensure_ascii=False)

            html_content = re.sub(
                r"window\.__EMBEDDED_DATA__\s*=\s*\{.*?\};",
                f"window.__EMBEDDED_DATA__ = {json_str};",
                html_content,
                flags=re.DOTALL,
            )
            html_content = re.sub(
                r"window\.__EMBEDDED_MANIFEST__\s*=\s*\{.*?\};",
                f"window.__EMBEDDED_MANIFEST__ = {manifest_str};",
                html_content,
                flags=re.DOTALL,
            )

            with open("index.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("Updated embedded dataset in index.html for direct offline viewing.")
        except Exception as e:
            print(f"Note: Could not update embedded data in index.html: {e}")


# ============================================================
# README GENERATION
# ============================================================

def generate_readme(
    report_date,
    filtered_rows,
    filtered_headers,
    top_5_rows,
    ai_top_5_data,
    total_scanx_stocks,
):
    """
    Generate a clean, modern README.md linking directly to the live GitHub Pages dashboard.
    """
    date_obj = datetime.strptime(report_date, "%Y-%m-%d")
    date_formatted = date_obj.strftime("%d %B %Y")

    top_ai = ai_top_5_data.get("top_5", [])
    top_ai_summary = "Available on live dashboard"
    if top_ai:
        pick = top_ai[0]
        name = pick.get("display_symbol", pick.get("symbol", ""))
        score = pick.get("score", "-")
        top_ai_summary = f"**{name}** (AI Score: **{score}/100**)"

    readme_content = f"""# 📈 Daily NSE Momentum Scanner & AI Engine

[![Daily Screener](https://github.com/androntech1/btst/actions/workflows/fetch_data.yml/badge.svg)](https://github.com/androntech1/btst/actions/workflows/fetch_data.yml)
[![Live Web Dashboard](https://img.shields.io/badge/Live_Dashboard-androntech1.github.io%2Fbtst-06b6d4?style=flat&logo=googlechrome)](https://androntech1.github.io/btst/)

Automated daily momentum scanner for Indian NSE equities featuring 52-week-high breakout filtering, AI quantitative ranking, real-time corporate news verification, and 1-click TradingView charts.

---

## 🌐 Live Web Dashboard

Access the full interactive dashboard with real-time sortable tables, AI score meters, strength tags, risk flags, and historical scans:

👉 **[https://androntech1.github.io/btst/](https://androntech1.github.io/btst/)**

### ⚡ Latest Scan Summary ({date_formatted})
- **ScanX Candidates:** {total_scanx_stocks}
- **Passed 52W High Filter:** {len(filtered_rows)} stocks within 10% of 52W High
- **Top AI Quantitative Pick:** {top_ai_summary}
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
"""

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(readme_content.strip() + "\n")

    print(f"README updated successfully: {README_FILE}")


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    print("=" * 70)
    print("DAILY NSE MOMENTUM SCANNER")
    print("=" * 70)
    print(f"AI Provider: {AI_PROVIDER}")
    print(f"AI Model:    {AI_MODEL}")

    os.makedirs(DATA_DIR, exist_ok=True)

    # 1. FETCH DATA FROM SCANX
    print("\nFetching data from ScanX API...")
    response = requests.post(
        SCANX_URL,
        headers=SCANX_HEADERS,
        json=SCANX_PAYLOAD,
        timeout=60,
    )

    if not response.ok:
        raise RuntimeError(f"ScanX API request failed (HTTP {response.status_code}):\n{response.text}")

    raw_data = response.json()
    original_data = copy.deepcopy(raw_data)

    if "headers" not in raw_data or "data" not in raw_data:
        raise RuntimeError("ScanX response missing required 'headers' or 'data' fields.")

    headers_list = raw_data["headers"]
    rows = raw_data["data"]
    print(f"ScanX returned {len(rows)} momentum stocks.")

    # 2. 52-WEEK HIGH FILTER VIA YFINANCE
    filtered_headers = list(headers_list)
    filtered_headers.extend(["Calculated52WkHigh", "DistFrom52WkHighPct"])

    try:
        sym_idx = headers_list.index("Sym")
        ltp_idx = headers_list.index("Ltp")
    except ValueError as e:
        raise RuntimeError(f"Required ScanX field missing: {e}")

    filtered_rows = []
    filtered_symbols = []

    print(f"\nProcessing {len(rows)} stocks and evaluating 52-week highs via yfinance...")

    for row in rows:
        try:
            sym = str(row[sym_idx]).strip()
            ltp = float(row[ltp_idx])
        except (ValueError, TypeError, IndexError) as e:
            print(f"Skipping malformed row: {e}")
            continue

        ticker_symbol = f"{sym}.NS"
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="1y", auto_adjust=False)

            if hist.empty:
                print(f"No historical data for {sym}")
                continue

            high_series = hist["High"].dropna()
            if high_series.empty:
                print(f"No High series for {sym}")
                continue

            wk52_high = float(high_series.max())

            # FILTER: LTP within 10% of 52-week high
            if ltp >= (0.90 * wk52_high):
                dist_pct = round(((ltp - wk52_high) / wk52_high) * 100, 2)
                new_row = list(row)
                new_row.append(round(wk52_high, 2))
                new_row.append(dist_pct)
                filtered_rows.append(new_row)
                filtered_symbols.append(sym)
                print(f"  [PASS] {sym:<12} | LTP: {ltp:>8.2f} | 52W High: {wk52_high:>8.2f} | Dist: {dist_pct:>6.2f}%")
        except Exception as e:
            print(f"Skipping {sym} due to yfinance error: {e}")

    print(f"\n52-Week High filter complete: {len(filtered_rows)} of {len(rows)} stocks passed.")

    filtered_data = copy.deepcopy(raw_data)
    filtered_data["headers"] = filtered_headers
    filtered_data["data"] = filtered_rows
    filtered_data["tot_rec"] = len(filtered_rows)

    # 3. RULE-BASED TOP 5
    dist_idx = filtered_headers.index("DistFrom52WkHighPct")
    sorted_filtered_rows = sorted(filtered_rows, key=lambda x: x[dist_idx], reverse=True)
    top_5_rows = sorted_filtered_rows[:5]

    top_5_data = copy.deepcopy(filtered_data)
    top_5_data["data"] = top_5_rows
    top_5_data["tot_rec"] = len(top_5_rows)
    top_5_symbols = [row[sym_idx] for row in top_5_rows]

    print("\nRule-based Top 5:")
    for rank, symbol in enumerate(top_5_symbols, start=1):
        print(f"  {rank}. {symbol}")

    # 4. AI TOP 5
    print("\n" + "=" * 70)
    print("AI QUANTITATIVE & NEWS ANALYSIS")
    print("=" * 70)

    try:
        ai_top_5_data = get_ai_top_5_picks(filtered_rows, filtered_headers)
        print("\nAI Top 5 Picks:")
        for pick in ai_top_5_data.get("top_5", []):
            print(f"  {pick.get('rank')}. {pick.get('symbol')} (Score: {pick.get('score')}/100)")
        print("AI analysis completed successfully.")
    except Exception as e:
        print(f"\nWARNING: AI analysis encountered an error: {e}")
        ai_top_5_data = {
            "top_5": [],
            "overall_market_note": "AI analysis temporarily unavailable.",
            "methodology_note": "AI API request failed. Rule-based results remain authoritative.",
            "generated_by": f"{AI_PROVIDER}/{AI_MODEL}",
            "error": str(e),
        }

    # 5. MASTER OUTPUT
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")

    master_output = {
        "date": today_date,
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "ai_provider": AI_PROVIDER,
        "ai_model": AI_MODEL,
        "original_scanx_results": original_data,
        "filtered_52w_results": filtered_data,
        "top_5_picks": top_5_data,
        "top_5_symbols": top_5_symbols,
        "filtered_symbols": filtered_symbols,
        "ai_top_5_picks": ai_top_5_data,
    }

    # 6. SAVE DAILY JSON, LATEST JSON & MANIFEST IN data/
    filename = os.path.join(DATA_DIR, f"data_{today_date}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(master_output, f, indent=4, ensure_ascii=False)
    print(f"\nDaily JSON saved to {filename}")

    update_manifest_and_latest(today_date, master_output)

    # 7. UPDATE README
    generate_readme(
        report_date=today_date,
        filtered_rows=filtered_rows,
        filtered_headers=filtered_headers,
        top_5_rows=top_5_rows,
        ai_top_5_data=ai_top_5_data,
        total_scanx_stocks=len(rows),
    )

    # 8. FINAL SUMMARY
    print("\n" + "=" * 70)
    print("SCAN COMPLETE")
    print("=" * 70)
    print(f"Original stocks:     {len(rows)}")
    print(f"52W filtered stocks: {len(filtered_rows)}")
    print(f"Rule-based Top 5:    {len(top_5_rows)}")
    print(f"AI Top 5:            {len(ai_top_5_data.get('top_5', []))}")
    print(f"Output files:        {filename}, {LATEST_DATA_FILE}, {MANIFEST_FILE}, {README_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
