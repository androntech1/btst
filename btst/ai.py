"""AI ranking layer: OpenRouter / OpenAI plumbing and the Top-5 ranking call."""
import copy
import json
import os
import re

import requests

from btst.config import AI_MODEL, AI_PROVIDER, OPENAI_URL, OPENROUTER_URL
from btst.prompts import AI_RESPONSE_SCHEMA, build_ai_prompt


def get_ai_api_configuration():
    """
    Return the API URL and headers based on the selected AI provider. The API key is read
    lazily here (not at import) so the module imports fine without credentials.
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


def get_ai_top_5_picks(candidates):
    """
    Send enriched flat candidate objects to the AI provider to rank the top 5 for a
    next-day (BTST) move. Includes automated fallback if web search or schema validation
    encounters issues.
    """
    if not candidates:
        return {
            "top_5": [],
            "overall_market_note": "No stocks passed the mechanical filtering criteria.",
            "methodology_note": "AI ranking was not required because there were no candidates.",
            "generated_by": f"{AI_PROVIDER}/{AI_MODEL}",
        }

    # Feed the AI the enriched, decision-relevant fields (technicals + events), not the raw
    # ScanX header soup. The AI blends these in language; no hardcoded formula.
    ai_stocks = []
    for c in candidates:
        ai_stocks.append({
            "symbol": c["symbol"],
            "name": c["name"],
            "ltp": c["ltp"],
            "pct_change": c["pct_change"],
            "volume": c["volume"],
            "rsi": c["rsi"],
            "pe": c["pe"],
            "mcap_cr": c["mcap_cr"],
            "dist_52w_pct": c["dist_52w_pct"],
            "rule_score": c["score"],
            "technicals": c["technicals"],
            "next_event": c["next_event"],
            "event_risk": c["event_risk"],
            "flags": c["flags"],
        })

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
    allowed_symbols = {str(c["symbol"]).strip().upper() for c in candidates}
    display_by_symbol = {str(c["symbol"]).strip().upper(): c["name"] for c in candidates}

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

        pick["symbol"] = symbol
        pick["display_symbol"] = display_by_symbol.get(symbol, symbol)

        # Clean string / list fields
        pick["recent_news"] = str(pick.get("recent_news", "") or "").strip()
        pick["why_it_was_selected"] = str(pick.get("why_it_was_selected", "") or "").strip()
        pick["momentum_assessment"] = str(pick.get("momentum_assessment", "") or "").strip()
        pick["catalyst"] = str(pick.get("catalyst", "") or "").strip()
        pick["event_risk"] = str(pick.get("event_risk", "") or "").strip()
        pick["technical_rating"] = str(pick.get("technical_rating", "") or "").strip()

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
