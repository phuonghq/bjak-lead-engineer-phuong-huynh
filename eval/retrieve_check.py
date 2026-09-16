"""Deterministic retrieval gate. No API. python -m eval.retrieve_check"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from assistant.retrieve import load_index, retrieve  # noqa: E402
from eval.metrics import contains_all  # noqa: E402

DATASET = Path(__file__).resolve().parent / "dataset.jsonl"

# Small fixture: what still "passes" if a reviewer's OpenAI key is dead.
CHECK_IDS = ("q04_education", "q16_salary", "q01_latest_employer")


def load_dataset() -> dict[str, dict]:
    items: dict[str, dict] = {}
    for line in DATASET.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            item = json.loads(line)
            items[item["id"]] = item
    return items


def _cite_ids(chunks) -> list[str]:
    return [c.cite_id.lower() for c in chunks]


def _education_chunk_text() -> str:
    for raw in load_index()["chunks"]:
        if raw.get("cite_id") == "cv#education":
            return raw.get("text") or ""
    return ""


def check_q04(item: dict, chunks, max_bm25: float) -> tuple[bool, str]:
    ids = _cite_ids(chunks)
    hit = any(i == "cv#education" or i.startswith("facts#education") or "#education" in i for i in ids)
    if not hit:
        return False, f"expected cv#education or education fact, got {ids or '[]'} (max_bm25={max_bm25:.4f})"
    hay = " ".join(c.text for c in chunks if "education" in c.cite_id.lower())
    if not contains_all(hay, item["must_contain"]):
        return False, f"retrieved education text missing must_contain {item['must_contain']}"
    return True, f"retrieved {ids} (max_bm25={max_bm25:.4f})"


def check_q16(_item: dict, chunks, max_bm25: float) -> tuple[bool, str]:
    ids = _cite_ids(chunks)
    if max_bm25 > 0.0 or ids:
        return False, f"expected BM25 0 and empty retrieve, got ids={ids} max_bm25={max_bm25:.4f}"
    return True, "BM25 0, empty retrieve"


def check_q01(_item: dict, chunks, max_bm25: float) -> tuple[bool, str]:
    ids = _cite_ids(chunks)
    agoda = [
        c.cite_id
        for c in chunks
        if "agoda" in f"{c.cite_id} {c.heading} {c.text}".lower()
    ]
    if not agoda:
        return False, f"expected an Agoda cite_id or Agoda role fact, got {ids or '[]'} (max_bm25={max_bm25:.4f})"
    return True, f"retrieved Agoda via {agoda} among {ids} (max_bm25={max_bm25:.4f})"


CHECKS = {
    "q04_education": check_q04,
    "q16_salary": check_q16,
    "q01_latest_employer": check_q01,
}


def run_retrieve_checks() -> bool:
    items = load_dataset()
    chunk_text = _education_chunk_text()
    print("retrieve_check (no API)")
    if chunk_text:
        q04 = items["q04_education"]
        overlap = [n for n in q04["must_contain"] if n.lower() in chunk_text.lower()]
        missing = [n for n in q04["must_contain"] if n.lower() not in chunk_text.lower()]
        print(f"  q04 must_contain vs cv#education: overlap={overlap} missing={missing}")
    ok_all = True
    for item_id in CHECK_IDS:
        item = items[item_id]
        chunks, max_bm25 = retrieve(item["question"])
        passed, detail = CHECKS[item_id](item, chunks, max_bm25)
        mark = "ok" if passed else "FAIL"
        print(f"  {item_id:28} {mark:4}  {detail}")
        ok_all = ok_all and passed
    print(f"retrieve_check overall     {'PASS' if ok_all else 'FAIL'}")
    return ok_all


def main() -> None:
    if not run_retrieve_checks():
        sys.exit(1)


if __name__ == "__main__":
    main()
