"""Environment configuration and output paths.

Loads a local ``.env`` (if present) so ``python run_screener.py`` works without exporting
variables by hand. Real environment variables and CI secrets always win (``setdefault``).
See ``.env.example`` for the supported keys.
"""
import os


def _parse_dotenv(text):
    """Parse ``KEY=VALUE`` lines into a dict; skip blanks and ``#`` comments, strip quotes."""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key:
            out[key] = val.strip().strip('"').strip("'")
    return out


def _load_dotenv(path=".env"):
    """Populate os.environ from a .env file without clobbering real env / CI secrets."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return
    for key, val in _parse_dotenv(text).items():
        os.environ.setdefault(key, val)  # real env / CI secrets win


_load_dotenv()


# ============================================================
# AI CONFIGURATION
# ============================================================

AI_PROVIDER = os.getenv("AI_PROVIDER", "openrouter").strip().lower()
AI_MODEL = os.getenv("AI_MODEL", "google/gemini-2.5-flash").strip()

# AI ranking on/off switch. Off => skip the LLM entirely; the deterministic rule-based
# composite is the sole output (and the dashboard hides its AI section). Default: on.
AI_ENABLED = os.getenv("AI_ENABLED", "true").strip().lower() not in ("false", "0", "no", "off")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


# ============================================================
# OUTPUT PATHS
# ============================================================

DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
README_FILE = "README.md"
LATEST_DATA_FILE = os.path.join(DATA_DIR, "data_latest.json")
MANIFEST_FILE = os.path.join(DATA_DIR, "manifest.json")
INDEX_HTML = "index.html"


if __name__ == "__main__":
    # self-check: parser skips blanks/comments/junk lines; setdefault lets real env win.
    parsed = _parse_dotenv('# comment\n\nAI_MODEL="x/y"\nJUNK LINE\nK=1\n')
    assert parsed == {"AI_MODEL": "x/y", "K": "1"}, parsed
    os.environ["BTST_SELFCHECK"] = "real"
    for k, v in _parse_dotenv("BTST_SELFCHECK=fromfile").items():
        os.environ.setdefault(k, v)
    assert os.environ["BTST_SELFCHECK"] == "real"
    print("config self-check OK")
