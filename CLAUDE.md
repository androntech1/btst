# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

**btst** is a daily momentum scanner for Indian NSE equities with an AI ranking layer.
It fetches a stock universe, applies mechanical momentum filters, verifies proximity to
the 52-week high, ranks the top candidates with an LLM, and publishes JSON + an
interactive dashboard to GitHub Pages.

## Commands

```bash
pip install -r requirements.txt   # deps: requests, yfinance
python run_screener.py            # runs the full pipeline end-to-end
```

There is **no test suite and no linter/formatter** configured. `run_screener.py` is the
single entry point; running it locally requires `OPENROUTER_API_KEY` set in the
environment (see below) or the AI step will fall back / fail.

## Pipeline (data flow)

```
ScanX/Dhan API  ──►  mechanical momentum filter  ──►  yfinance 52W-high proximity
   (universe)        (volume≥2×SMA10, RSI≥65,          (within 10% of 52W high)
                      positive open/close action)
        │
        ▼
  AI ranking (OpenRouter/OpenAI → Gemini)  ──►  JSON exports + README summary + index.html
        (top 5, score 0–100, strengths/risks)      (data/, GitHub Pages dashboard)
```

## Key files

| Path | Responsibility |
|------|----------------|
| `run_screener.py` | Whole pipeline. Sections: ScanX config/payload → formatting helpers → AI config (`get_ai_api_configuration`, `extract_ai_text`, `parse_ai_json`, `get_ai_top_5_picks`) → `update_manifest_and_latest` → `generate_readme` → `main`. |
| `prompts.py` | Owns `AI_RESPONSE_SCHEMA` (strict JSON schema) and `build_ai_prompt()`. Change AI output shape **here**, not inline in the screener. |
| `index.html` | Standalone GitHub Pages dashboard (sortable tables, score meters). Reads the JSON in `data/`. |
| `data/` | Generated outputs: `data_YYYY-MM-DD.json`, `data_latest.json`, `manifest.json` (date index). |
| `.github/workflows/fetch_data.yml` | CI that runs the screener on schedule and commits results. |
| `.agents/` | Config for the `ponytail` plugin (not application code). |

## Environment variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENROUTER_API_KEY` | API key for the AI ranking step (required for AI output). | – |
| `AI_PROVIDER` | `openrouter` or `openai`. | `openrouter` |
| `AI_MODEL` | Model slug. | `google/gemini-2.5-flash` |

In CI the key comes from the `OPENROUTER_API_KEY` GitHub Actions secret.

## Automation

GitHub Actions runs the screener **Mon–Fri at 15:10 IST** (`cron: '10 15 * * 1-5'`,
`Asia/Kolkata`) and via manual `workflow_dispatch`. The workflow then commits
`data/ prompts.py README.md index.html .gitignore` back to the repo with
`github-actions[bot]`.

## Conventions & gotchas

- **Generated artifacts:** `data/*.json`, the "Latest Scan Summary" block in `README.md`,
  and the data embedded in `index.html` are produced by `run_screener.py`. Don't hand-edit
  the generated portions — change the generator (`generate_readme`, `update_manifest_and_latest`)
  and re-run instead.
- **AI output is schema-constrained:** responses must satisfy `AI_RESPONSE_SCHEMA` in
  `prompts.py`. If you add/rename a field the AI returns, update the schema and the prompt
  together.
- **Provider fallback:** the AI layer supports both OpenRouter and OpenAI selected via
  `AI_PROVIDER`; keep both paths working when touching `get_ai_api_configuration`.
- **All times are IST.** The scan is timed ~20 min before NSE close.
- **Dev environment is Windows** with a bash shell; prefer forward-slash paths.
