from __future__ import annotations

import json
import re
from functools import lru_cache

from rank_bm25 import BM25Okapi

from assistant.config import BM25_THRESHOLD, INDEX_PATH, TOP_K
from assistant.types import Chunk

TOKEN = re.compile(r"[a-z0-9]+", re.I)
# Stripped from queries so "Phuong was CTO at Google, right?" does not retrieve
# the whole CV on the name alone.
NAME_TOKENS = {"phuong", "huynh"}

STOPWORDS = {
    "a",
    "an",
    "the",
    "of",
    "in",
    "at",
    "to",
    "for",
    "and",
    "or",
    "your",
    "you",
    "what",
    "who",
    "how",
    "did",
    "do",
    "does",
    "is",
    "was",
    "were",
    "be",
    "been",
    "me",
    "my",
    "about",
    "tell",
    "please",
    "with",
    "from",
    "on",
    "his",
    "her",
    "their",
    "this",
    "that",
    "these",
    "those",
    "can",
    "could",
    "would",
    "should",
    "have",
    "has",
    "had",
    "i",
    "we",
    "they",
    "he",
    "she",
    "it",
    "as",
    "by",
    "if",
    "into",
    "over",
    "than",
    "then",
    "so",
    "just",
    "also",
    "any",
    "some",
    "more",
    "most",
    "such",
}

# Query-only. Kept in the corpus so "current role" still indexes, but stripped
# from questions so "current salary" does not retrieve on the word "current".
# Single-character query tokens are dropped separately: "Phuong's" → phuong + s,
# and s matches B.S.E. in the education chunk.
QUERY_WEAK = {"current", "currently", "now", "right", "confirm", "where", "cv", "resume"}


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOPWORDS]


@lru_cache(maxsize=1)
def load_index() -> dict:
    if not INDEX_PATH.exists():
        raise FileNotFoundError(
            f"{INDEX_PATH} is missing. Run `python -m knowledge.ingest` from the repo root."
        )
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def _as_chunk(raw: dict, score: float, via: str) -> Chunk:
    return Chunk(
        cite_id=raw["cite_id"],
        source_id=raw["source_id"],
        heading=raw["heading"],
        text=raw["text"],
        as_of=raw.get("as_of", ""),
        score=score,
        via=via,
    )


def retrieve(question: str, k: int = TOP_K) -> tuple[list[Chunk], float]:
    """Return (chunks, max_bm25). Fact hits are appended and do not replace BM25."""
    index = load_index()
    corpus = index["chunks"]
    tokens = [
        t
        for t in tokenize(question)
        if t not in NAME_TOKENS and t not in QUERY_WEAK and len(t) > 1
    ]
    if not tokens:
        return [], 0.0

    tokenized = [tokenize(c["text"]) for c in corpus]
    bm25 = BM25Okapi(tokenized)
    scores = bm25.get_scores(tokens)
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    max_bm25 = float(ranked[0][1]) if ranked else 0.0

    picked: dict[str, Chunk] = {}
    for idx, score in ranked[:k]:
        if score <= BM25_THRESHOLD:
            continue
        raw = corpus[idx]
        picked[raw["cite_id"]] = _as_chunk(raw, float(score), "bm25")

    qset = set(tokens)
    for raw in corpus:
        if raw.get("source_id") != "facts":
            continue
        hay = " ".join(
            str(raw.get(field, ""))
            for field in ("employer", "title", "claim")
        )
        if qset & set(tokenize(hay)):
            existing = picked.get(raw["cite_id"])
            score = existing.score if existing else 1.0
            picked[raw["cite_id"]] = _as_chunk(raw, score, "fact" if not existing else "bm25+fact")

    chunks = sorted(picked.values(), key=lambda c: c.score, reverse=True)
    return chunks, max_bm25
