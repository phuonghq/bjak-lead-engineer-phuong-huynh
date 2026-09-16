from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Chunk:
    cite_id: str
    source_id: str
    heading: str
    text: str
    as_of: str = ""
    score: float = 0.0
    via: str = "bm25"


@dataclass
class AskResult:
    answer: str
    citations: list[str]
    retrieved: list[Chunk]
    refused: bool
    fallback: str | None
    refusal_reason: str | None
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    model: str | None = None
    max_bm25: float = 0.0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "citations": self.citations,
            "retrieved": [
                {
                    "cite_id": c.cite_id,
                    "source_id": c.source_id,
                    "heading": c.heading,
                    "score": round(c.score, 4),
                    "via": c.via,
                    "as_of": c.as_of,
                }
                for c in self.retrieved
            ],
            "refused": self.refused,
            "fallback": self.fallback,
            "refusal_reason": self.refusal_reason,
            "latency_ms": round(self.latency_ms, 1),
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "model": self.model,
            "max_bm25": round(self.max_bm25, 4),
            "errors": self.errors,
        }
