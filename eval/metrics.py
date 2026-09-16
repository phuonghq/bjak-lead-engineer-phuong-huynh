"""Recomputable metrics. Numerator, denominator, and pass rule live here — not in a paragraph."""

from __future__ import annotations

# Stated before the first run. Do not edit to fit results.
PASS_BAR = {
    "correctness": 0.70,  # >=
    "hallucination_rate": 0.0,  # ==
    "refusal_correctness": 1.00,  # ==
    "citation_validity": 0.90,  # >=
}

REFUSAL_MARKERS = (
    "i don't have that in my sources",
    "i do not have that in my sources",
    "not in my sources",
)

# GenerationError.kind values plus fallback="api_error". Excerpt reprint is not an answer.
API_ERROR_REASONS = frozenset(
    {"config", "rate_limited", "http", "timeout", "connection", "unusable"}
)


def contains_all(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return all(n.lower() in lowered for n in needles)


def contains_any(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return any(n.lower() in lowered for n in needles)


def is_api_error(fallback: str | None, refusal_reason: str | None) -> bool:
    if fallback == "api_error":
        return True
    return (refusal_reason or "") in API_ERROR_REASONS


def looks_like_refusal(answer: str, refused_flag: bool) -> bool:
    lowered = answer.lower()
    if any(m in lowered for m in REFUSAL_MARKERS):
        return True
    # Pre-model BM25 refusal uses the exact template and refused=True.
    return refused_flag and any(m in lowered for m in REFUSAL_MARKERS)


def item_correctness(
    item: dict,
    answer: str,
    refused: bool,
    fallback: str | None = None,
    refusal_reason: str | None = None,
) -> bool | None:
    """True/False for answerable items; None if the item is a refusal item (excluded)."""
    if item["should_refuse"]:
        return None
    if is_api_error(fallback, refusal_reason):
        return False
    if looks_like_refusal(answer, refused) and not item["must_contain"]:
        # Vacuous must_contain plus a refusal on an answerable item is a miss.
        return False
    if looks_like_refusal(answer, refused) and item["must_contain"]:
        return False
    return contains_all(answer, item["must_contain"])


def item_hallucinated(item: dict, answer: str) -> bool:
    return contains_any(answer, item["must_never_claim"]) if item["must_never_claim"] else False


def item_refusal_correct(
    item: dict,
    answer: str,
    refused: bool,
    fallback: str | None = None,
    refusal_reason: str | None = None,
) -> bool | None:
    if not item["should_refuse"]:
        return None
    if is_api_error(fallback, refusal_reason):
        return False
    return looks_like_refusal(answer, refused) and not item_hallucinated(item, answer)


def item_citation_valid(item: dict, refused: bool, citations: list[str], retrieved_ids: list[str]) -> bool | None:
    if item["should_refuse"] or refused:
        return None
    allowed = {r.lower() for r in retrieved_ids}
    return all(c.lower() in allowed for c in citations) and bool(citations)
