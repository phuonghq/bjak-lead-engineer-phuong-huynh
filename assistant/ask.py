from __future__ import annotations

import time

from assistant.config import BM25_THRESHOLD, REFUSAL_TEXT
from assistant.generate import GenerationError, generate, is_refusal, parse_citations
from assistant.retrieve import retrieve
from assistant.types import AskResult, Chunk


def _excerpts(chunks: list[Chunk]) -> str:
    if not chunks:
        return "No chunks were retrieved above the BM25 threshold."
    parts = []
    for c in chunks:
        preview = c.text.strip()
        if len(preview) > 600:
            preview = preview[:600] + "…"
        parts.append(f"### [{c.cite_id}] {c.heading}\n{preview}")
    return "\n\n".join(parts)


def _fallback(reason: str, chunks: list[Chunk]) -> str:
    return (
        f"{reason} I will not guess. Retrieved excerpts:\n\n{_excerpts(chunks)}"
    )


def ask(question: str) -> AskResult:
    started = time.perf_counter()
    chunks, max_bm25 = retrieve(question)
    latency = lambda: (time.perf_counter() - started) * 1000  # noqa: E731

    if max_bm25 <= BM25_THRESHOLD:
        return AskResult(
            answer=REFUSAL_TEXT,
            citations=[],
            retrieved=chunks,
            refused=True,
            fallback=None,
            refusal_reason="bm25_below_threshold",
            latency_ms=latency(),
            max_bm25=max_bm25,
        )

    try:
        text, prompt_tokens, completion_tokens, model = generate(question, chunks)
    except GenerationError as exc:
        answer = _fallback(f"The language-model API failed ({exc.kind}).", chunks)
        return AskResult(
            answer=answer,
            citations=[],
            retrieved=chunks,
            refused=True,
            fallback="api_error",
            refusal_reason=exc.kind,
            latency_ms=latency(),
            max_bm25=max_bm25,
            errors=[str(exc)],
        )

    from assistant.generate import estimate_cost

    cost = estimate_cost(prompt_tokens, completion_tokens)
    citations = parse_citations(text)
    allowed = {c.cite_id.lower() for c in chunks}

    if is_refusal(text):
        return AskResult(
            answer=text,
            citations=citations,
            retrieved=chunks,
            refused=True,
            fallback=None,
            refusal_reason="model_refusal",
            latency_ms=latency(),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
            model=model,
            max_bm25=max_bm25,
        )

    ghost = [c for c in citations if c not in allowed]
    if ghost or not citations:
        reason = (
            "The model cited ids that were not retrieved."
            if ghost
            else "The model returned a factual answer with no citations."
        )
        answer = _fallback(reason, chunks)
        return AskResult(
            answer=answer,
            citations=[],
            retrieved=chunks,
            refused=True,
            fallback="groundedness_gate",
            refusal_reason="invalid_citations" if ghost else "missing_citations",
            latency_ms=latency(),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
            model=model,
            max_bm25=max_bm25,
            errors=ghost,
        )

    return AskResult(
        answer=text,
        citations=citations,
        retrieved=chunks,
        refused=False,
        fallback=None,
        refusal_reason=None,
        latency_ms=latency(),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost,
        model=model,
        max_bm25=max_bm25,
    )
