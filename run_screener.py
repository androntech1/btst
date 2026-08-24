from datetime import datetime
import json
import copy
import os
from urllib.parse import quote

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


# ============================================================
# AI CONFIGURATION
# ============================================================

AI_PROVIDER = (
    os.getenv(
        "AI_PROVIDER",
        "openrouter",
    )
    .strip()
    .lower()
)

AI_MODEL = os.getenv(
    "AI_MODEL",
    "google/gemini-2.5-flash",
).strip()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

OPENAI_URL = "https://api.openai.com/v1/chat/completions"

README_FILE = "README.md"


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
    Build a TradingView chart URL for an NSE symbol.

    Opens TradingView's chart page directly with:
        Exchange: NSE
        Timeframe: 1 Day
    """

    clean_symbol = str(symbol).strip().upper()

    if not clean_symbol:
        return ""

    tradingview_symbol = f"NSE:{clean_symbol}"

    encoded_symbol = quote(
        tradingview_symbol,
        safe="",
    )

    return (
        "https://www.tradingview.com/chart/" f"?symbol={encoded_symbol}" "&interval=D"
    )


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

    except (
        TypeError,
        ValueError,
    ):
        return "-"


def format_percent(value):
    """
    Format a percentage value.
    """

    try:
        return f"{float(value):.2f}%"

    except (
        TypeError,
        ValueError,
    ):
        return "-"


def get_stock_from_row(row, headers):
    """
    Convert a ScanX row into a dictionary.
    """

    return dict(
        zip(
            headers,
            row,
        )
    )


# ============================================================
# AI RESPONSE SCHEMA
# ============================================================

AI_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "top_5": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rank": {
                        "type": "integer",
                    },
                    "symbol": {
                        "type": "string",
                    },
                    "display_symbol": {
                        "type": "string",
                    },
                    "score": {
                        "type": "number",
                    },
                    "why_it_was_selected": {
                        "type": "string",
                    },
                    "recent_news": {
                        "type": "string",
                    },
                    "key_strengths": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                    },
                    "risk_flags": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                    },
                    "momentum_assessment": {
                        "type": "string",
                    },
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
            },
        },
        "overall_market_note": {
            "type": "string",
        },
        "methodology_note": {
            "type": "string",
        },
        "generated_by": {
            "type": "string",
        },
    },
    "required": [
        "top_5",
        "overall_market_note",
        "methodology_note",
        "generated_by",
    ],
}


# ============================================================
# AI PROMPT
# ============================================================


def build_ai_prompt(ai_stocks):
    """
    Build the quantitative ranking prompt.

    The model is explicitly instructed to operate only on the
    supplied candidates for quantitative ranking.

    If web search is available, the model may use it only for
    recent company-specific context.
    """

    current_date = datetime.now().strftime("%Y-%m-%d")

    return f"""
You are a quantitative stock-screening assistant.

Today's date is {current_date}.

Your task is to rank Indian NSE stocks for a DAILY MOMENTUM
WATCHLIST.

The candidate stocks supplied below have ALREADY passed these
mechanical screening conditions:

1. NSE listed.
2. Volume is at least 2x the 10-day average volume.
3. Current Open is greater than the reference/previous Open.
4. Current LTP is greater than the reference/previous Close.
5. RSI(14) is at least 65.
6. Current LTP is within 10% of the 52-week high.

You must independently rank ONLY the supplied candidates.

============================================================
STRICT DATA INTEGRITY RULES
============================================================

- Select ONLY stocks present in the supplied candidate data.
- NEVER invent a stock symbol.
- NEVER modify a stock symbol.
- NEVER create a stock that is not in the input.
- Treat the supplied numerical data as authoritative.
- Do not change, reinterpret, or fabricate numerical values.
- Do not use outside company knowledge for the quantitative
  ranking.
- Do not use analyst opinions.
- Do not make claims about future events.
- Do not predict with certainty.
- Do not guarantee profit.
- Do not use phrases such as "guaranteed winner",
  "sure shot", "certain profit", or "risk-free".
- This is a quantitative ranking/watchlist, NOT personalized
  investment advice.

============================================================
RECENT NEWS / CORPORATE ACTION CHECK
============================================================

If a web search tool is available, use it briefly to check
recent information specifically related to the supplied
candidate symbols.

Search ONLY for symbols that are actually present in the
candidate data.

The purpose of the search is NOT to discover new stocks and
NOT to replace the quantitative screening.

The purpose is to identify recent company-specific information
that may help explain today's price or volume movement.

Examples include:

- Recent quarterly/company results.
- Orders or major contracts.
- Corporate announcements.
- Management announcements.
- Regulatory actions or issues.
- Credit-rating changes.
- Stock-specific upgrades or downgrades.
- Material corporate actions.
- Other clearly relevant recent company-specific developments.

IMPORTANT NEWS RULES:

- NEVER use news to introduce a new candidate.
- NEVER add a stock that is not present in the supplied data.
- NEVER invent or assume news.
- NEVER speculate about the reason for a price move.
- Only mention information actually found through the search.
- Prefer recent information.
- Prefer primary or highly reliable sources when available.
- Do not treat generic sector news as company-specific news
  unless it is clearly relevant to the individual company.
- Do not let news override the supplied quantitative data.
- Quantitative signals remain the PRIMARY basis for ranking.
- News is secondary context only.
- Keep news summaries brief.
- Do not copy long passages from sources.
- If web search is unavailable, explicitly say:
  "Recent-news verification unavailable."
- If no relevant recent company-specific news is found,
  explicitly say:
  "No relevant recent company-specific news found."
- If search results are unclear or conflicting, say so rather
  than presenting uncertain information as fact.

The web search should be brief.

Do not perform unnecessary broad market research.

============================================================
RECENT NEWS OUTPUT
============================================================

Each selected stock has a dedicated "recent_news" field.

Use that field ONLY for concise recent company-specific news
context.

Examples:

"Company announced a major order on 22 Aug 2026."

"Q1 results were reported recently; revenue increased
year-over-year."

"No relevant recent company-specific news found."

"Recent-news verification unavailable."

Do NOT put full news paragraphs into risk_flags.

risk_flags must remain focused on actual risks or cautionary
signals visible from the supplied data, such as:

- Very high RSI / possible short-term extension.
- Weak price-volume confirmation relative to other candidates.
- Large distance from 52-week high relative to peers.
- High valuation when PE is available.
- Missing data.
- Other quantitative caution signals.

============================================================
RANKING PRINCIPLES
============================================================

Do NOT simply rank by RSI.

Do NOT simply rank by percentage change.

Evaluate multiple independent signals together.

Positive signals include:

- Strong price momentum.
- Strong volume confirmation.
- Strong proximity to the 52-week high.
- Positive opening/price action.
- RSI confirmation.
- Healthy combination of price and volume strength.

Secondary signals:

- PE when available.
- Market capitalization when available.

Important:

RSI >= 65 already confirms momentum.

However, an extremely high RSI can also indicate short-term
overextension.

Therefore:

- Do NOT automatically rank the highest RSI stock first.
- Consider whether momentum is confirmed by volume,
  price action and proximity to the 52-week high.
- Penalize obvious signs of excessive short-term extension
  when appropriate.

Prefer stocks where several independent signals agree.

If two candidates are similar, prefer the candidate with
stronger confirmation across multiple fields.

============================================================
SCORING
============================================================

Give each selected stock an overall quantitative score from
0 to 100.

The score is a ranking score.

It is NOT:

- a probability of profit
- a prediction of return
- a confidence percentage
- a guarantee

Use approximately these priorities:

1. Overall price momentum
2. Volume confirmation
3. Proximity to 52-week high
4. RSI confirmation while considering overextension
5. Positive price action
6. PE and market capitalization as secondary factors

Recent verified company-specific news may be included as
context, but MUST NOT become the primary scoring factor.

============================================================
OUTPUT
============================================================

Select the BEST 5 candidates.

For each selected stock provide:

- rank
- symbol
- display_symbol
- score
- why_it_was_selected
- recent_news
- key_strengths
- risk_flags
- momentum_assessment

Also provide:

- overall_market_note
- methodology_note
- generated_by

For recent_news:

- If relevant recent news was found, summarize it briefly.
- If no relevant recent news was found, state that plainly.
- If web search was unavailable, state that plainly.
- Do not speculate.

For risk_flags:

- Keep entries short and risk-focused.
- Do NOT put full news summaries here.
- Do NOT use risk_flags as a general news field.

For why_it_was_selected:

- Focus primarily on the quantitative reasons for selection.
- You may briefly reference verified news context if useful.

For momentum_assessment:

- Focus on the quantitative momentum setup.
- Mention news only when it materially helps explain the
  current move and was actually verified.

Return ONLY valid JSON matching the supplied response schema.

Do NOT return Markdown.

Do NOT return code fences.

Do NOT add commentary outside the JSON.

============================================================
CANDIDATE DATA
============================================================

{json.dumps(ai_stocks, separators=(",", ":"), default=str)}
"""


# ============================================================
# AI API HELPERS
# ============================================================


def get_ai_api_configuration():
    """
    Return the API URL, API key and headers based on the
    selected AI provider.
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

        return (
            OPENROUTER_URL,
            headers,
        )

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

        return (
            OPENAI_URL,
            headers,
        )

    raise RuntimeError(
        f"Unsupported AI_PROVIDER: {AI_PROVIDER}. "
        f"Supported providers: openrouter, openai."
    )


def extract_ai_text(response_json):
    """
    Extract the assistant's text from an OpenAI-compatible
    chat completion response.
    """

    try:

        content = response_json["choices"][0]["message"]["content"]

    except (
        KeyError,
        IndexError,
        TypeError,
    ) as e:

        raise RuntimeError(
            "Could not find generated text in AI response.\n"
            f"Error: {e}\n"
            f"Response:\n"
            f"{json.dumps(response_json, indent=2)}"
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

    raise RuntimeError(
        "AI returned content in an unexpected format.\n" f"Content:\n{repr(content)}"
    )


# ============================================================
# AI JSON CLEANUP
# ============================================================


def parse_ai_json(text):
    """
    Parse JSON returned by the AI.

    Structured output should normally make this unnecessary,
    but this function also handles accidental Markdown fences
    defensively.
    """

    clean_text = str(text).strip()

    if clean_text.startswith("```"):

        lines = clean_text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]

        clean_text = "\n".join(lines).strip()

    try:

        return json.loads(clean_text)

    except json.JSONDecodeError as e:

        raise RuntimeError(
            "AI returned invalid JSON.\n" f"Error: {e}\n" f"Raw response:\n{clean_text}"
        )


# ============================================================
# AI TOP 5 FUNCTION
# ============================================================


def get_ai_top_5_picks(
    filtered_rows,
    filtered_headers,
):
    """
    Send filtered stock candidates to the configured
    OpenAI-compatible provider and ask it to independently
    rank the best 5 candidates.

    OpenRouter:
        Quantitative ranking + optional server-side web search.

    OpenAI:
        Quantitative ranking without the OpenRouter web-search
        tool.
    """

    # --------------------------------------------------------
    # Convert rows into dictionaries
    # --------------------------------------------------------

    stocks = []

    for row in filtered_rows:

        stock = dict(
            zip(
                filtered_headers,
                row,
            )
        )

        stocks.append(stock)

    if not stocks:

        return {
            "top_5": [],
            "overall_market_note": (
                "No stocks passed the mechanical filtering criteria."
            ),
            "methodology_note": (
                "AI ranking was not required because there were " "no candidates."
            ),
            "generated_by": AI_MODEL,
        }

    # --------------------------------------------------------
    # Fields that the AI should analyze
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
    # Prompt
    # --------------------------------------------------------

    prompt = build_ai_prompt(ai_stocks)

    # --------------------------------------------------------
    # API configuration
    # --------------------------------------------------------

    api_url, headers = get_ai_api_configuration()

    print(
        f"Sending {len(ai_stocks)} candidates to "
        f"{AI_PROVIDER} / {AI_MODEL} for AI ranking..."
    )

    # --------------------------------------------------------
    # Base request
    # --------------------------------------------------------

    payload = {
        "model": AI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a disciplined quantitative "
                    "stock-screening assistant. "
                    "Return only the requested structured JSON."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "nse_momentum_top_5",
                "strict": True,
                "schema": AI_RESPONSE_SCHEMA,
            },
        },
    }

    # --------------------------------------------------------
    # OpenRouter web search
    # --------------------------------------------------------
    #
    # OpenRouter currently provides a server-side web search
    # tool using:
    #
    #     {"type": "openrouter:web_search"}
    #
    # This lets the model decide when it needs to search.
    #
    # We deliberately keep the search budget limited because
    # this is a daily scanner and news is secondary context.
    #
    # IMPORTANT:
    # Do not send this OpenRouter-specific tool to OpenAI.
    # --------------------------------------------------------

    if AI_PROVIDER == "openrouter":

        payload["tools"] = [
            {
                "type": "openrouter:web_search",
                "parameters": {
                    "engine": "auto",
                    "max_results": 5,
                    "max_total_results": 15,
                },
            }
        ]

        payload["max_tool_calls"] = 5

    # --------------------------------------------------------
    # OpenAI provider
    # --------------------------------------------------------
    #
    # No OpenRouter-specific search tool is attached here.
    #
    # The prompt explicitly tells the model to state that
    # recent-news verification is unavailable if it cannot
    # access web search.
    # --------------------------------------------------------

    response = requests.post(
        api_url,
        headers=headers,
        json=payload,
        timeout=180,
    )

    if not response.ok:

        raise RuntimeError(
            f"{AI_PROVIDER} API request failed "
            f"(HTTP {response.status_code}):\n"
            f"{response.text}"
        )

    result = response.json()

    # --------------------------------------------------------
    # Extract response
    # --------------------------------------------------------

    text = extract_ai_text(result)

    ai_result = parse_ai_json(text)

    # --------------------------------------------------------
    # Validate top_5 structure
    # --------------------------------------------------------

    if not isinstance(
        ai_result,
        dict,
    ):

        raise RuntimeError("AI response root must be a JSON object.")

    if not isinstance(
        ai_result.get("top_5"),
        list,
    ):

        raise RuntimeError("AI response does not contain a valid top_5 array.")

    # --------------------------------------------------------
    # Validate symbols
    # --------------------------------------------------------

    try:

        sym_index = filtered_headers.index("Sym")

    except ValueError:

        raise RuntimeError("Filtered data does not contain the Sym field.")

    allowed_symbols = {str(row[sym_index]).strip() for row in filtered_rows}

    validated_top_5 = []

    seen_symbols = set()

    for pick in ai_result.get(
        "top_5",
        [],
    ):

        if not isinstance(
            pick,
            dict,
        ):
            continue

        symbol = str(
            pick.get(
                "symbol",
                "",
            )
        ).strip()

        # ----------------------------------------------------
        # Never allow AI to introduce an unknown symbol.
        # ----------------------------------------------------

        if symbol not in allowed_symbols:

            print(
                "WARNING: AI returned a symbol that was "
                "not in the candidate list: "
                f"{symbol}"
            )

            continue

        # ----------------------------------------------------
        # Prevent duplicate stocks.
        # ----------------------------------------------------

        if symbol in seen_symbols:

            print("WARNING: AI returned duplicate symbol: " f"{symbol}")

            continue

        seen_symbols.add(symbol)

        # ----------------------------------------------------
        # Validate display symbol against our own data.
        # Do not trust AI to rewrite it.
        # ----------------------------------------------------

        actual_display_symbol = symbol

        try:

            display_index = filtered_headers.index("DispSym")

            matching_rows = [
                row for row in filtered_rows if str(row[sym_index]).strip() == symbol
            ]

            if matching_rows:

                actual_display_symbol = str(matching_rows[0][display_index]).strip()

        except ValueError:

            pass

        pick["symbol"] = symbol

        pick["display_symbol"] = actual_display_symbol

        # ----------------------------------------------------
        # Ensure recent_news exists.
        # ----------------------------------------------------

        recent_news = pick.get(
            "recent_news",
            "",
        )

        if recent_news is None:
            recent_news = ""

        pick["recent_news"] = str(recent_news).strip()

        # ----------------------------------------------------
        # Ensure risk_flags is a clean list.
        # ----------------------------------------------------

        risk_flags = pick.get(
            "risk_flags",
            [],
        )

        if not isinstance(
            risk_flags,
            list,
        ):

            risk_flags = [str(risk_flags)]

        pick["risk_flags"] = [
            str(item).strip() for item in risk_flags if str(item).strip()
        ]

        # ----------------------------------------------------
        # Ensure key_strengths is a clean list.
        # ----------------------------------------------------

        key_strengths = pick.get(
            "key_strengths",
            [],
        )

        if not isinstance(
            key_strengths,
            list,
        ):

            key_strengths = [str(key_strengths)]

        pick["key_strengths"] = [
            str(item).strip() for item in key_strengths if str(item).strip()
        ]

        # ----------------------------------------------------
        # Clamp score to 0-100.
        # ----------------------------------------------------

        try:

            score = float(
                pick.get(
                    "score",
                    0,
                )
            )

            score = max(
                0.0,
                min(
                    100.0,
                    score,
                ),
            )

            if score.is_integer():

                score = int(score)

            pick["score"] = score

        except (
            TypeError,
            ValueError,
        ):

            pick["score"] = 0

        validated_top_5.append(pick)

    # --------------------------------------------------------
    # Sort by AI rank.
    # --------------------------------------------------------

    validated_top_5.sort(
        key=lambda item: (
            item.get("rank", 999)
            if isinstance(
                item.get("rank", 999),
                int,
            )
            else 999
        )
    )

    # --------------------------------------------------------
    # Re-number ranks ourselves.
    #
    # This prevents inconsistent AI ranks after validation
    # removes an invalid or duplicate symbol.
    # --------------------------------------------------------

    validated_top_5 = validated_top_5[:5]

    for index, pick in enumerate(
        validated_top_5,
        start=1,
    ):

        pick["rank"] = index

    ai_result["top_5"] = validated_top_5

    # --------------------------------------------------------
    # generated_by is controlled by our program.
    # --------------------------------------------------------

    ai_result["generated_by"] = f"{AI_PROVIDER}/{AI_MODEL}"

    return ai_result


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
    Generate the complete README.md dashboard.

    Each execution replaces/updates the section for the
    current date while preserving previous daily sections.
    """

    existing_readme = ""

    if os.path.exists(README_FILE):

        with open(
            README_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            existing_readme = f.read()

    # --------------------------------------------------------
    # Build current day's section
    # --------------------------------------------------------

    day_lines = []

    day_lines.append(
        f"## 📅 " f"{datetime.strptime(report_date, '%Y-%m-%d').strftime('%d %B %Y')}"
    )

    day_lines.append("")

    day_lines.append("<details>")

    day_lines.append("<summary>Show today's scanner results</summary>")

    day_lines.append("")

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    day_lines.append("### Scanner Summary")

    day_lines.append("")

    day_lines.append(f"- ScanX candidates: **{total_scanx_stocks}**")

    day_lines.append(
        f"- Stocks within 10% of 52-week high: " f"**{len(filtered_rows)}**"
    )

    day_lines.append(f"- Rule-based Top 5: **{len(top_5_rows)}**")

    day_lines.append(f"- AI Top 5: " f"**{len(ai_top_5_data.get('top_5', []))}**")

    day_lines.append("")

    # --------------------------------------------------------
    # Rule-Based Top 5
    # --------------------------------------------------------

    day_lines.append("### 📊 Rule-Based Top 5")

    day_lines.append("")

    day_lines.append(
        "| Rank | Stock | LTP | % Change | RSI | "
        "Distance from 52W High | TradingView |"
    )

    day_lines.append("|---:|---|---:|---:|---:|---:|---|")

    header_index = {header: index for index, header in enumerate(filtered_headers)}

    for rank, row in enumerate(
        top_5_rows,
        start=1,
    ):

        symbol = row[header_index["Sym"]]

        display_symbol = row[header_index["DispSym"]]

        ltp = row[header_index["Ltp"]]

        pchange = row[header_index["PPerchange"]]

        rsi = row[header_index["DayRSI14CurrentCandle"]]

        distance = row[header_index["DistFrom52WkHighPct"]]

        tv_url = tradingview_url(symbol)

        day_lines.append(
            "| "
            f"{rank} | "
            f"**{markdown_escape(display_symbol)}** | "
            f"{format_number(ltp)} | "
            f"{format_percent(pchange)} | "
            f"{format_number(rsi)} | "
            f"{format_percent(distance)} | "
            f"[Daily Chart ↗]({tv_url}) |"
        )

    if not top_5_rows:

        day_lines.append(
            "| - | No stocks passed the rule-based filter | " "- | - | - | - | - |"
        )

    day_lines.append("")

    # --------------------------------------------------------
    # AI Top 5
    # --------------------------------------------------------

    day_lines.append("### 🤖 AI Top 5")

    day_lines.append("")

    ai_top_5 = ai_top_5_data.get(
        "top_5",
        [],
    )

    if ai_top_5:

        day_lines.append("| Rank | Stock | Score | Momentum | TradingView |")

        day_lines.append("|---:|---|---:|---|---|")

        for pick in ai_top_5:

            symbol = str(
                pick.get(
                    "symbol",
                    "",
                )
            ).strip()

            display_symbol = str(
                pick.get(
                    "display_symbol",
                    symbol,
                )
            ).strip()

            score = pick.get(
                "score",
                "-",
            )

            momentum = str(
                pick.get(
                    "momentum_assessment",
                    "",
                )
            )

            tv_url = tradingview_url(symbol)

            day_lines.append(
                "| "
                f"{pick.get('rank', '-')} | "
                f"**{markdown_escape(display_symbol)}** | "
                f"{score} | "
                f"{markdown_escape(momentum)} | "
                f"[Daily Chart ↗]({tv_url}) |"
            )

        day_lines.append("")

        # ----------------------------------------------------
        # AI Details
        # ----------------------------------------------------

        day_lines.append("#### AI Selection Details")

        day_lines.append("")

        for pick in ai_top_5:

            symbol = str(
                pick.get(
                    "symbol",
                    "",
                )
            ).strip()

            display_symbol = str(
                pick.get(
                    "display_symbol",
                    symbol,
                )
            ).strip()

            day_lines.append(
                f"**{pick.get('rank', '-')}. "
                f"{markdown_escape(display_symbol)}** "
                f"— Score: **{pick.get('score', '-')}**"
            )

            # ------------------------------------------------
            # Why selected
            # ------------------------------------------------

            why = pick.get(
                "why_it_was_selected",
                "",
            )

            if why:

                day_lines.append("")

                day_lines.append(f"**Why selected:** " f"{markdown_escape(why)}")

            # ------------------------------------------------
            # Recent News
            # ------------------------------------------------

            recent_news = pick.get(
                "recent_news",
                "",
            )

            if recent_news:

                day_lines.append("")

                day_lines.append(f"**Recent news:** " f"{markdown_escape(recent_news)}")

            # ------------------------------------------------
            # Key strengths
            # ------------------------------------------------

            strengths = pick.get(
                "key_strengths",
                [],
            )

            if strengths:

                day_lines.append("")

                day_lines.append("**Key strengths:**")

                for strength in strengths:

                    day_lines.append(f"- {markdown_escape(strength)}")

            # ------------------------------------------------
            # Risk flags
            # ------------------------------------------------

            risks = pick.get(
                "risk_flags",
                [],
            )

            if risks:

                day_lines.append("")

                day_lines.append("**Risk flags:**")

                for risk in risks:

                    day_lines.append(f"- {markdown_escape(str(risk))}")

            day_lines.append("")

    else:

        day_lines.append("AI analysis was unavailable for this run.")

        day_lines.append("")

    # --------------------------------------------------------
    # AI Market Note
    # --------------------------------------------------------

    market_note = ai_top_5_data.get(
        "overall_market_note",
        "",
    )

    if market_note:

        day_lines.append("#### Market Note")

        day_lines.append("")

        day_lines.append(markdown_escape(market_note))

        day_lines.append("")

    # --------------------------------------------------------
    # Methodology Note
    # --------------------------------------------------------

    methodology_note = ai_top_5_data.get(
        "methodology_note",
        "",
    )

    if methodology_note:

        day_lines.append("#### Methodology Note")

        day_lines.append("")

        day_lines.append(markdown_escape(methodology_note))

        day_lines.append("")

    # --------------------------------------------------------
    # AI Provider
    # --------------------------------------------------------

    generated_by = ai_top_5_data.get(
        "generated_by",
        "",
    )

    if generated_by:

        day_lines.append(f"**AI model:** " f"`{markdown_escape(generated_by)}`")

        day_lines.append("")

    day_lines.append("</details>")

    day_lines.append("")

    current_section = "\n".join(day_lines)

    # --------------------------------------------------------
    # Replace existing section for same date if present.
    # --------------------------------------------------------

    date_heading = (
        f"## 📅 " f"{datetime.strptime(report_date, '%Y-%m-%d').strftime('%d %B %Y')}"
    )

    if date_heading in existing_readme:

        start_index = existing_readme.index(date_heading)

        remaining = existing_readme[start_index:]

        next_section_position = remaining.find(
            "\n## 📅 ",
            len(date_heading),
        )

        if next_section_position == -1:

            end_index = len(existing_readme)

        else:

            end_index = start_index + next_section_position + 1

        existing_readme = existing_readme[:start_index] + existing_readme[end_index:]

    # --------------------------------------------------------
    # README header
    # --------------------------------------------------------

    header = """# 📈 Daily NSE Momentum Scanner

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

"""

    # --------------------------------------------------------
    # Preserve old results and put newest day first.
    # --------------------------------------------------------

    old_content = existing_readme

    if "## Daily Results" in old_content:

        results_position = old_content.index("## Daily Results")

        prefix = old_content[: results_position + len("## Daily Results")]

        old_daily_sections = old_content[
            results_position + len("## Daily Results") :
        ].strip()

    else:

        prefix = header.rstrip()

        old_daily_sections = old_content.strip()

    # --------------------------------------------------------
    # Prevent accidental duplicate generic header.
    # --------------------------------------------------------

    if old_daily_sections.startswith("Automated daily momentum watchlist"):

        old_daily_sections = ""

    # --------------------------------------------------------
    # Build final README.
    # --------------------------------------------------------

    if old_daily_sections:

        final_content = (
            prefix + "\n\n" + current_section + "\n" + old_daily_sections + "\n"
        )

    else:

        final_content = prefix + "\n\n" + current_section

    with open(
        README_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        f.write(final_content.strip() + "\n")

    print(f"README updated successfully: " f"{README_FILE}")


# ============================================================
# MAIN PROGRAM
# ============================================================


def main():

    print("=" * 70)

    print("DAILY STOCK SCANNER")

    print("=" * 70)

    # --------------------------------------------------------
    # AI configuration summary
    # --------------------------------------------------------

    print(f"\nAI Provider: {AI_PROVIDER}")

    print(f"AI Model:    {AI_MODEL}")

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

    original_data = copy.deepcopy(raw_data)

    # --------------------------------------------------------
    # Validate ScanX response
    # --------------------------------------------------------

    if "headers" not in raw_data:

        raise RuntimeError("ScanX response does not contain 'headers'.")

    if "data" not in raw_data:

        raise RuntimeError("ScanX response does not contain 'data'.")

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

        raise RuntimeError(f"Required ScanX field missing: {e}")

    filtered_rows = []

    filtered_symbols = []

    print(
        f"\nProcessing {len(rows)} stocks "
        f"and checking 52-week highs via "
        f"yfinance..."
    )

    # --------------------------------------------------------
    # 3. YFINANCE 52-WEEK HIGH FILTER
    # --------------------------------------------------------

    for row in rows:

        try:

            sym = str(row[sym_idx]).strip()

            ltp = float(row[ltp_idx])

        except (
            ValueError,
            TypeError,
            IndexError,
        ) as e:

            print(f"Skipping malformed row " f"due to error: {e}")

            continue

        ticker_symbol = f"{sym}.NS"

        try:

            print(f"Checking {ticker_symbol}...")

            ticker = yf.Ticker(ticker_symbol)

            hist = ticker.history(
                period="1y",
                auto_adjust=False,
            )

            if hist.empty:

                print(f"No historical data " f"available for {sym}")

                continue

            high_series = hist["High"].dropna()

            if high_series.empty:

                print(f"No High values " f"available for {sym}")

                continue

            wk52_high = float(high_series.max())

            # ------------------------------------------------
            # FILTER:
            # Stock must be within 10% of 52-week high.
            # ------------------------------------------------

            if ltp >= (0.90 * wk52_high):

                dist_pct = round(
                    ((ltp - wk52_high) / wk52_high) * 100,
                    2,
                )

                new_row = list(row)

                new_row.append(
                    round(
                        wk52_high,
                        2,
                    )
                )

                new_row.append(dist_pct)

                filtered_rows.append(new_row)

                filtered_symbols.append(sym)

                print(
                    f"  PASS | "
                    f"LTP={ltp:.2f} | "
                    f"52W High={wk52_high:.2f} | "
                    f"Distance={dist_pct:.2f}%"
                )

            else:

                print(f"  FAIL | " f"LTP={ltp:.2f} | " f"52W High={wk52_high:.2f}")

        except Exception as e:

            print(f"Skipping {sym} due to " f"yfinance error: {e}")

    print(f"\n52-week filter complete. " f"{len(filtered_rows)} stocks passed.")

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

    dist_idx = filtered_headers.index("DistFrom52WkHighPct")

    sorted_filtered_rows = sorted(
        filtered_rows,
        key=lambda x: x[dist_idx],
        reverse=True,
    )

    top_5_rows = sorted_filtered_rows[:5]

    top_5_data = copy.deepcopy(filtered_data)

    top_5_data["data"] = top_5_rows

    top_5_data["tot_rec"] = len(top_5_rows)

    top_5_symbols = [row[sym_idx] for row in top_5_rows]

    print("\nRule-based Top 5:")

    for rank, symbol in enumerate(
        top_5_symbols,
        start=1,
    ):

        print(f"  {rank}. {symbol}")

    # --------------------------------------------------------
    # 6. AI TOP 5
    # --------------------------------------------------------

    print("\n" + "=" * 70)

    print("AI ANALYSIS")

    print("=" * 70)

    try:

        ai_top_5_data = get_ai_top_5_picks(
            filtered_rows,
            filtered_headers,
        )

        print("\nAI Top 5:")

        for pick in ai_top_5_data.get(
            "top_5",
            [],
        ):

            print(
                f"  {pick.get('rank')}. "
                f"{pick.get('symbol')} "
                f"(Score: "
                f"{pick.get('score')})"
            )

        print("\nAI analysis completed successfully.")

    except Exception as e:

        print("\nWARNING: AI analysis failed.")

        print(f"Reason: {e}")

        ai_top_5_data = {
            "top_5": [],
            "overall_market_note": ("AI analysis unavailable."),
            "methodology_note": (
                "AI API request failed. " "Rule-based results are still available."
            ),
            "generated_by": (f"{AI_PROVIDER}/{AI_MODEL}"),
            "error": str(e),
        }

    # --------------------------------------------------------
    # 7. MASTER OUTPUT
    # --------------------------------------------------------

    now = datetime.now()

    master_output = {
        "date": now.strftime("%Y-%m-%d"),
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "ai_provider": AI_PROVIDER,
        "ai_model": AI_MODEL,
        "original_scanx_results": (original_data),
        "filtered_52w_results": (filtered_data),
        "top_5_picks": (top_5_data),
        "top_5_symbols": (top_5_symbols),
        "filtered_symbols": (filtered_symbols),
        "ai_top_5_picks": (ai_top_5_data),
    }

    # --------------------------------------------------------
    # 8. SAVE JSON
    # --------------------------------------------------------

    today_date = now.strftime("%Y-%m-%d")

    filename = f"data_{today_date}.json"

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            master_output,
            f,
            indent=4,
            ensure_ascii=False,
        )

    print(f"\nJSON saved to {filename}")

    # --------------------------------------------------------
    # 9. UPDATE README
    # --------------------------------------------------------

    generate_readme(
        report_date=today_date,
        filtered_rows=filtered_rows,
        filtered_headers=filtered_headers,
        top_5_rows=top_5_rows,
        ai_top_5_data=ai_top_5_data,
        total_scanx_stocks=len(rows),
    )

    # --------------------------------------------------------
    # 10. FINAL SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)

    print("SCAN COMPLETE")

    print("=" * 70)

    print(f"Original stocks:       {len(rows)}")

    print(f"52W filtered stocks:   {len(filtered_rows)}")

    print(f"Rule-based Top 5:      {len(top_5_rows)}")

    print(f"AI Top 5:              " f"{len(ai_top_5_data.get('top_5', []))}")

    print(f"AI provider:           {AI_PROVIDER}")

    print(f"AI model:              {AI_MODEL}")

    print(f"Output file:           {filename}")

    print(f"README updated:        {README_FILE}")

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
