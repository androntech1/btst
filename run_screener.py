"""Daily NSE momentum / BTST scanner — pipeline orchestrator (single entry point).

ScanX universe (server-side momentum filter) -> 52W-high proximity + technicals + events
-> deterministic rule-based Top 5 -> optional AI ranking -> raw/processed JSON + README +
embedded dashboard. Run: ``python run_screener.py`` (see .env.example for configuration).
"""
import os
from datetime import datetime

from btst import ai, market_data, outputs, scanx, scoring
from btst.config import (AI_ENABLED, AI_MODEL, AI_PROVIDER, DATA_DIR,
                         LATEST_DATA_FILE, MANIFEST_FILE, PROCESSED_DIR,
                         README_FILE, RAW_DIR)


def main():
    print("=" * 70)
    print("DAILY NSE MOMENTUM SCANNER")
    print("=" * 70)
    print(f"AI Provider: {AI_PROVIDER}")
    print(f"AI Model:    {AI_MODEL}")
    print(f"AI Enabled:  {AI_ENABLED}")

    os.makedirs(DATA_DIR, exist_ok=True)

    # 1. ScanX universe (the momentum filter runs server-side inside the query)
    print("\nFetching data from ScanX API...")
    headers_list, rows, raw = scanx.fetch_universe()
    print(f"ScanX returned {len(rows)} momentum stocks.")

    # 2. 52-week-high proximity + technicals + events -> flat candidate objects
    candidates = market_data.enrich_candidates(headers_list, rows)

    # 3. Rule-based Top 5 (deterministic composite; proximity is the tie-break)
    rule_top_5 = scoring.rank(candidates)
    print("\nRule-based Top 5 (composite):")
    for position, c in enumerate(rule_top_5, start=1):
        print(f"  {position}. {c['symbol']:<12} Score: {c['score']:>5.1f} | Dist52W: {c['dist_52w_pct']:>6.2f}%")

    # 4. AI Top 5 (optional — governed by AI_ENABLED)
    print("\n" + "=" * 70)
    if AI_ENABLED:
        print("AI QUANTITATIVE & NEWS ANALYSIS")
        print("=" * 70)
        try:
            ai_result = ai.get_ai_top_5_picks(candidates)
            print("\nAI Top 5 Picks:")
            for pick in ai_result.get("top_5", []):
                print(f"  {pick.get('rank')}. {pick.get('symbol')} (Score: {pick.get('score')}/100)")
            print("AI analysis completed successfully.")
        except Exception as e:
            print(f"\nWARNING: AI analysis encountered an error: {e}")
            ai_result = {
                "top_5": [],
                "overall_market_note": "AI analysis temporarily unavailable.",
                "methodology_note": "AI API request failed. Rule-based results remain authoritative.",
                "generated_by": f"{AI_PROVIDER}/{AI_MODEL}",
                "error": str(e),
            }
    else:
        print("AI RANKING DISABLED (AI_ENABLED=false)")
        print("=" * 70)
        ai_result = {
            "top_5": [],
            "overall_market_note": "AI ranking disabled for this run.",
            "methodology_note": "Rule-based equal-weight composite is the sole ranking (AI_ENABLED=false).",
            "generated_by": "disabled",
        }

    # 5. Processed output (flat, dashboard-ready)
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")

    processed = {
        "date": today_date,
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "ai_enabled": AI_ENABLED,
        "ai_provider": AI_PROVIDER,
        "ai_model": AI_MODEL,
        "counts": {"scanx_universe": len(rows), "near_52w": len(candidates)},
        "candidates": candidates,
        "rule_based_top_5": rule_top_5,
        "ai_top_5": ai_result.get("top_5", []),
        "notes": {
            "overall_market_note": ai_result.get("overall_market_note", ""),
            "methodology_note": ai_result.get("methodology_note", ""),
        },
    }
    if ai_result.get("error"):
        processed["notes"]["ai_error"] = ai_result["error"]

    # 6. Save raw + processed + latest + manifest, and embed into the dashboard
    outputs.update_manifest_and_latest(today_date, processed, raw)

    # 7. Update README
    outputs.generate_readme(today_date, processed)

    # 8. Final summary
    print("\n" + "=" * 70)
    print("SCAN COMPLETE")
    print("=" * 70)
    print(f"ScanX stocks:        {len(rows)}")
    print(f"Near-52W candidates: {len(candidates)}")
    print(f"Rule-based Top 5:    {len(rule_top_5)}")
    print(f"AI enabled:          {AI_ENABLED}  (AI Top 5: {len(processed['ai_top_5'])})")
    print(f"Output:              {os.path.join(RAW_DIR, today_date + '.json')}, "
          f"{os.path.join(PROCESSED_DIR, today_date + '.json')}, {LATEST_DATA_FILE}, {MANIFEST_FILE}, {README_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
