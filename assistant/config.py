from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

KNOWLEDGE_DIR = REPO_ROOT / "knowledge"
INDEX_PATH = KNOWLEDGE_DIR / "index.json"

# BM25 scores of 0 mean no lexical overlap after stopwording. Anything above is a hit.
# Documented so a reviewer can change it live without hunting.
BM25_THRESHOLD = 0.0
TOP_K = 4

OPENAI_INPUT_USD_PER_MTOK = 0.15
OPENAI_OUTPUT_USD_PER_MTOK = 0.60

REFUSAL_TEXT = "I don't have that in my sources."
