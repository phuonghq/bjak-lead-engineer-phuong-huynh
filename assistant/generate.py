from __future__ import annotations

import os
import re

import httpx
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

from assistant.config import (
    OPENAI_INPUT_USD_PER_MTOK,
    OPENAI_OUTPUT_USD_PER_MTOK,
    REFUSAL_TEXT,
)
from assistant.prompts import SYSTEM_PROMPT, build_context
from assistant.types import Chunk

CITATION_RE = re.compile(r"\[([a-z0-9_-]+#[a-z0-9_.-]+)\]", re.I)


class GenerationError(Exception):
    def __init__(self, kind: str, detail: str):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail


def parse_citations(text: str) -> list[str]:
    seen: list[str] = []
    for match in CITATION_RE.findall(text):
        cite = match.lower()
        if cite not in seen:
            seen.append(cite)
    return seen


def is_refusal(text: str) -> bool:
    lowered = text.strip().lower()
    return REFUSAL_TEXT.lower() in lowered or lowered.startswith("i do not have that in my sources")


def estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    return (
        prompt_tokens / 1_000_000 * OPENAI_INPUT_USD_PER_MTOK
        + completion_tokens / 1_000_000 * OPENAI_OUTPUT_USD_PER_MTOK
    )


def _openai_client(*, max_retries: int | None = None) -> tuple[OpenAI, str]:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise GenerationError("config", "OPENAI_API_KEY is empty")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    timeout = float(os.environ.get("OPENAI_TIMEOUT_SECONDS", "30"))
    # openai==1.54.3 still passes proxies= into httpx.Client; httpx>=0.28 dropped that kwarg.
    http_client = httpx.Client(timeout=timeout)
    kwargs: dict = {"api_key": api_key, "timeout": timeout, "http_client": http_client}
    if max_retries is not None:
        kwargs["max_retries"] = max_retries
    return OpenAI(**kwargs), model


def map_openai_error(exc: BaseException) -> GenerationError:
    if isinstance(exc, GenerationError):
        return exc
    if isinstance(exc, AuthenticationError):
        return GenerationError("config", str(exc))
    if isinstance(exc, RateLimitError):
        return GenerationError("rate_limited", str(exc))
    if isinstance(exc, APITimeoutError):
        return GenerationError("timeout", str(exc))
    if isinstance(exc, APIConnectionError):
        return GenerationError("connection", str(exc))
    if isinstance(exc, APIStatusError):
        return GenerationError("http", f"{exc.status_code} {exc}")
    return GenerationError("unusable", str(exc))


_BILLING_MARKERS = (
    "insufficient_quota",
    "insufficient_funds",
    "credit_balance",
    "exceeded your current quota",
    "billing_not_active",
    "401",
    "invalid_api_key",
    "incorrect api key",
    "unauthorized",
    "authentication",
)


def is_billed_key_failure(kind: str, detail: str) -> bool:
    """True when the key is missing, unauthorized, or out of credit — not a model answer."""
    if kind == "config":
        return True
    blob = f"{kind} {detail}".lower()
    if kind in {"rate_limited", "http"} and any(m in blob for m in _BILLING_MARKERS):
        return True
    if "401" in blob:
        return True
    return False


def probe_llm() -> tuple[bool, str, str]:
    """One-token completion. Returns (ok, kind, detail). Never prints the API key."""
    try:
        client, model = _openai_client(max_retries=0)
        client.chat.completions.create(
            model=model,
            temperature=0,
            max_tokens=1,
            messages=[{"role": "user", "content": "ok"}],
        )
    except Exception as exc:  # noqa: BLE001 — probe must not crash eval.run
        err = map_openai_error(exc)
        return False, err.kind, err.detail
    return True, "", ""


def generate(question: str, chunks: list[Chunk]) -> tuple[str, int, int, str]:
    client, model = _openai_client()
    user = (
        f"Context:\n{build_context(chunks)}\n\n"
        f"Question: {question}\n\n"
        "Answer with citations. If you cannot, reply with exactly the refusal sentence."
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
        )
    except Exception as exc:  # noqa: BLE001 — surface anything unusable as a fallback
        raise map_openai_error(exc) from exc

    choice = resp.choices[0].message.content if resp.choices else None
    if not choice or not choice.strip():
        raise GenerationError("unusable", "empty model response")
    usage = resp.usage
    prompt_tokens = int(usage.prompt_tokens) if usage else 0
    completion_tokens = int(usage.completion_tokens) if usage else 0
    return choice.strip(), prompt_tokens, completion_tokens, model
