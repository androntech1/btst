"""Data exports (raw / processed / latest / manifest), dashboard embedding, and README."""
import json
import os
import re
from datetime import datetime

from btst.config import (AI_MODEL, AI_PROVIDER, INDEX_HTML, LATEST_DATA_FILE,
                         MANIFEST_FILE, PROCESSED_DIR, RAW_DIR, README_FILE)


def update_manifest_and_latest(today_date, processed, raw):
    """
    Persist the two daily artifacts and refresh the dashboard inputs:
      - data/raw/<date>.json        : untouched ScanX response (audit / reprocess).
      - data/processed/<date>.json  : flat, dashboard-ready object.
      - data/data_latest.json       : copy of the latest processed object (dashboard reads this).
      - data/manifest.json          : date index, globbed from data/processed/.
      - index.html                  : embedded latest processed object + manifest (offline viewing).
    """
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # 1. Daily raw + processed files
    with open(os.path.join(RAW_DIR, f"{today_date}.json"), "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=4, ensure_ascii=False)
    with open(os.path.join(PROCESSED_DIR, f"{today_date}.json"), "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=4, ensure_ascii=False)

    # 2. Root latest = the processed object
    with open(LATEST_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=4, ensure_ascii=False)
    print(f"Latest data saved to {LATEST_DATA_FILE}")

    # 3. Manifest date index from data/processed/*.json
    dates = {today_date}
    if os.path.isdir(PROCESSED_DIR):
        for filename in os.listdir(PROCESSED_DIR):
            if filename.endswith(".json"):
                d = filename[:-5]
                if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
                    dates.add(d)

    sorted_dates = sorted(list(dates), reverse=True)

    manifest_data = {
        "latest_date": today_date,
        "available_dates": sorted_dates,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ai_enabled": processed.get("ai_enabled", True),
        "ai_model": f"{AI_PROVIDER}/{AI_MODEL}",
    }

    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=4, ensure_ascii=False)
    print(f"Manifest updated with {len(sorted_dates)} dates: {MANIFEST_FILE}")

    # 4. Embed the flat processed object into index.html for direct file:// / offline viewing
    if os.path.exists(INDEX_HTML):
        try:
            with open(INDEX_HTML, "r", encoding="utf-8") as f:
                html_content = f.read()

            json_str = json.dumps(processed, separators=(",", ":"), ensure_ascii=False)
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

            with open(INDEX_HTML, "w", encoding="utf-8") as f:
                f.write(html_content)
            print("Updated embedded dataset in index.html for direct offline viewing.")
        except Exception as e:
            print(f"Note: Could not update embedded data in index.html: {e}")


def generate_readme(report_date, processed):
    """
    Generate a clean README.md linking to the live GitHub Pages dashboard.
    AI-off aware: when AI ranking is disabled, the summary highlights the rule-based leader.
    """
    date_obj = datetime.strptime(report_date, "%Y-%m-%d")
    date_formatted = date_obj.strftime("%d %B %Y")

    counts = processed.get("counts", {})
    scanx_universe = counts.get("scanx_universe", 0)
    near_52w = counts.get("near_52w", 0)
    ai_enabled = processed.get("ai_enabled", True)
    ai_top = processed.get("ai_top_5", [])
    rule_top = processed.get("rule_based_top_5", [])

    if ai_enabled and ai_top:
        pick = ai_top[0]
        name = pick.get("display_symbol", pick.get("symbol", ""))
        top_pick_label = "Top AI Quantitative Pick"
        top_pick_summary = f"**{name}** (AI Score: **{pick.get('score', '-')}/100**)"
    elif rule_top:
        top = rule_top[0]
        top_pick_label = "Top Rule-Based Pick"
        top_pick_summary = f"**{top.get('name', top.get('symbol', ''))}** (Composite: **{top.get('score', '-')}/100**)"
        if not ai_enabled:
            top_pick_summary += "  _(AI ranking disabled)_"
    else:
        top_pick_label = "Top Pick"
        top_pick_summary = "No candidates today"

    ai_arch_line = (
        "[3] AI Quantitative & News Ranking (OpenRouter / Gemini) — toggle via AI_ENABLED\n"
        "    • Blends technicals + catalyst/events for a next-day move\n"
        "    • Output: AI Top 5 with Score (0-100), catalyst, strengths, risks & event flags"
        if ai_enabled else
        "[3] AI Ranking DISABLED (AI_ENABLED=false)\n"
        "    • Rule-based composite is the sole, authoritative ranking"
    )

    readme_content = f"""# 📈 Daily NSE Momentum Scanner & AI Engine

[![Daily Screener](https://github.com/androntech1/btst/actions/workflows/fetch_data.yml/badge.svg)](https://github.com/androntech1/btst/actions/workflows/fetch_data.yml)
[![Live Web Dashboard](https://img.shields.io/badge/Live_Dashboard-androntech1.github.io%2Fbtst-06b6d4?style=flat&logo=googlechrome)](https://androntech1.github.io/btst/)

Automated daily BTST momentum scanner for Indian NSE equities: 52-week-high breakout filtering, daily technicals, event gap-risk flags, and an optional AI ranking layer oriented toward a favorable next-day move.

---

## 🌐 Live Web Dashboard

Access the full interactive dashboard with real-time sortable tables, AI score meters, strength tags, risk flags, and historical scans:

👉 **[https://androntech1.github.io/btst/](https://androntech1.github.io/btst/)**

### ⚡ Latest Scan Summary ({date_formatted})
- **ScanX Candidates:** {scanx_universe}
- **Passed 52W High Filter:** {near_52w} stocks within 10% of 52W High
- **{top_pick_label}:** {top_pick_summary}
- **Data Exports:** [`data/data_latest.json`](data/data_latest.json) • [`data/manifest.json`](data/manifest.json) • raw/processed under [`data/`](data/)

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
[2] 52-Week High Proximity + Enrichment (yfinance)
    • Current LTP within 10% of 52-Week High
    • Daily technicals: pivot/R1/S1, 20D overextension, ATR%, volume surge
    • yfinance event (ex-div/earnings) gap-risk flags
       │
       ├──► Rule-Based Top 5 (equal-weight composite: proximity + surge + RSI-health + not-overextended, × fundamentals gate)
       │
       ▼
{ai_arch_line}
       │
       ▼
[4] Exports
    • data/raw/<date>.json (audit) + data/processed/<date>.json (flat)
    • data/data_latest.json + data/manifest.json (date index)
    • Interactive index.html on GitHub Pages
```

---

## ⚙️ Setup & Configuration

### Running Locally
```bash
git clone https://github.com/androntech1/btst.git
cd btst
pip install -r requirements.txt
cp .env.example .env   # then fill in OPENROUTER_API_KEY (or set AI_ENABLED=false)
python run_screener.py
```
This writes `data/raw/<date>.json`, `data/processed/<date>.json`, `data/data_latest.json`,
`data/manifest.json`, updates `README.md`, and re-embeds the latest scan into `index.html`
(open `index.html` directly in a browser to preview it offline). No API key is needed if
you set `AI_ENABLED=false` — the rule-based composite still runs standalone.

### Running via GitHub Actions
The [`fetch_data.yml`](.github/workflows/fetch_data.yml) workflow runs the same
`python run_screener.py` entry point in CI:
- **Scheduled:** automatically **Monday to Friday at 3:10 PM IST** (`10 15 * * 1-5`,
  `Asia/Kolkata`) — 20 minutes before market close, timed for BTST / momentum entries.
- **Manual:** open the repo's **Actions** tab → *Fetch and Filter ScanX Data* →
  **Run workflow** (`workflow_dispatch`) to trigger an off-schedule scan.
- **Secret required:** add `OPENROUTER_API_KEY` under **Settings → Secrets and
  variables → Actions** so the AI ranking step can run in CI (skip it and the workflow
  still runs rule-based only). `AI_PROVIDER` / `AI_MODEL` can be overridden as repo
  Actions **variables** if you don't want the defaults below.
- On success the workflow commits the refreshed `data/`, `README.md`, and `index.html`
  back to `main` as `github-actions[bot]` and GitHub Pages redeploys the dashboard.

### Environment Variables / Secrets
| Variable | Description | Default |
|:---|:---|:---|
| `OPENROUTER_API_KEY` | OpenRouter API Key (Required only when AI is enabled) | - |
| `AI_ENABLED` | Turn the AI ranking layer on/off (`false` runs rule-based only) | `true` |
| `AI_PROVIDER` | AI Provider (`openrouter` or `openai`) | `openrouter` |
| `AI_MODEL` | AI Model slug | `google/gemini-2.5-flash` |

---

> ⚠️ **Disclaimer:** This tool is for educational, screening, and research purposes only, not personalized investment advice. Scores are quantitative ranking signals, not guarantees of profit.
"""

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(readme_content.strip() + "\n")

    print(f"README updated successfully: {README_FILE}")
