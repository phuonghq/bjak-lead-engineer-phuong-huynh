# Phuong Huynh — grounded hiring assistant

A time-boxed take-home for BJAK's Engineering Manager / Lead Engineer assessment. The assistant answers recruiter and interviewer questions about **Phuong Huynh** using a committed personal knowledge base. It must not invent employers, titles, projects, or achievements.

This is not a production system and not a BJAK product. It was written for this exercise; it is not a reused template or a prior project.

The interface is a CLI that prints **sources** after every answer. That choice serves a hiring manager who needs to *verify*, not a candidate who needs to *impress*.

## How this brief is scored (and what we built to that bar)

The PDF weights evaluation at 30%, knowledge and architecture at 25% each, UX and leadership write-up at 10% each. A thin, correct, honestly-evaluated slice outscores a sprawling one. Complexity a simpler design would have covered counts against the submission.

What a reviewer should be able to do in one sitting:

1. Install, export one API key, ask a question, see the answer **and its sources**.
2. Ask something the corpus cannot support and get a **clear refusal**.
3. Run `python -m eval.retrieve_check` (no API) and, with a billed key, `python -m eval.run`; read committed numbers and the error analysis.
4. Point at the Agoda missing end date and see the system **not invent Present**.
5. Read `docs/DECISIONS.md` for the alternatives that were rejected.

Deliberately not built: vector database, LangChain, agents, chat UI, streaming, conversation memory, fine-tuning.

Java is the production stack. This slice is Python because the score is retrieval + eval inside the time box — see D6 in `docs/DECISIONS.md`. LinkedIn is **omitted on purpose**: the candidate does not maintain a profile — see D7.

## Install and run (< 10 minutes)

Needs Python 3.11+, an OpenAI API key, and the ability to reach `api.openai.com`. Provider: **OpenAI**. One eval run (25 questions, `gpt-4o-mini`) is typically **well under USD 0.05**.

```bash
cd bjak-lead-engineer-phuong-huynh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # put OPENAI_API_KEY in .env
python -m knowledge.ingest
python -m assistant ask "What is Phuong's current role?"
python -m assistant ask "What is Phuong's current salary?"
python -m eval.retrieve_check   # no API; deterministic retrieval gate
python -m eval.run              # 25-question LLM eval; needs a billed OpenAI key
```

`--json` prints the structured `AskResult` (retrieved chunks, tokens, cost, refusal reason).

Configuration (named in `.env.example`; none are committed with real values):

- `OPENAI_API_KEY` — required for generation and `python -m eval.run`. Retrieval, ingest, and `python -m eval.retrieve_check` work without it.
- `OPENAI_MODEL` — default `gpt-4o-mini`. Switch if eval groundedness drops or p95 exceeds what a live review can tolerate.
- `OPENAI_TIMEOUT_SECONDS` — default `30`. On timeout / 429 / 5xx the user sees an error plus retrieved excerpts. No retry storm.

## Architecture and why

```
knowledge/sources/*.md + facts.yaml
        │
        ▼
python -m knowledge.ingest  →  knowledge/index.json
        │
        ▼
question → BM25 (k=4) + fact lookup
        │
        ├─ max BM25 == 0  →  refusal template, no model call
        │
        └─ else → gpt-4o-mini (citation-required prompt)
                      │
                      ├─ citations ⊆ retrieved ids  →  answer + Sources
                      └─ missing/ghost citations or API failure
                            →  deterministic excerpts, no guessed prose
```

Why this, not a stuffed prompt: the role constraint is traceability. Retrieval, prompting, and the gate are three readable functions (`assistant/retrieve.py`, `assistant/generate.py`, `assistant/ask.py`).

**Traceability.** Every model-written factual answer must contain `[cite_id]` tokens from the retrieved set. Ghost ids or an empty citation list fail the gate. The CLI always prints `Sources:` from the retriever, not from the model's word.

**Gap.** `knowledge/conflicts.md` — Agoda is listed from 07/2023 with a blank end date. The system reports that blank and does not invent "Present".

**Failure paths.** Slow, down, rate-limited, or empty response: user-visible API error + retrieved excerpts. Unusable citations: same excerpts path. Unknown question: `I don't have that in my sources.`

**Security and privacy.** The API key lives in `.env` (gitignored). Source text **does leave this machine** for OpenAI chat completions. Assume the provider may log. No unredacted phone, email, or address is in the corpus. See `knowledge/redactions.md`.

**Cost and latency.** Billed eval run (`python -m eval.run`, 25 items, `2026-09-14T17:21:10Z`): mean cost/question **$0.000116** (eval total **$0.002900**; 14391 prompt + 1235 completion tokens). p95 latency **2245 ms**.

**What breaks first at 100× traffic.** The OpenAI rate limit, then the fact that the index is a JSON file loaded per process with BM25 rebuilt per query. Before production: a process-level cached BM25, a timeout budget, and a queue — not a new architecture.

Adding a source: drop a markdown file with the same frontmatter, optionally a `facts.yaml` row, run ingest. Documented in `knowledge/README.md`.

## Evaluation

25 questions in `eval/dataset.jsonl`, covering all five required categories: CV-direct, multi-source, ambiguous, unanswerable, adversarial.

Pass bar, declared in `eval/metrics.py` **before** the first run:

| Metric | Definition | Pass |
| --- | --- | --- |
| correctness | answerable items where every `must_contain` appears and the answer is not a refusal; API-error excerpt fallback is always incorrect | ≥ 0.70 |
| hallucination_rate | items whose answer contains any `must_never_claim` | = 0 |
| refusal_correctness | unanswerable/adversarial-refuse items that match a refusal marker and contain no `must_never_claim`; API-error fallback is always incorrect | = 1.00 |
| citation_validity | non-refused answerable items whose `[cite_id]`s are non-empty and ⊆ retrieved ids | ≥ 0.90 |
| p95 latency | nearest-rank 95th percentile of `ask()` wall-clock over the dataset | reported |
| mean cost/question | token usage × `gpt-4o-mini` list prices in `assistant/config.py` | reported |

No LLM-as-judge: every number is recomputable from `eval/results.json` plus the dataset. `python -m eval.retrieve_check` is the deterministic gate (no API): q04 must retrieve `cv#education` or an education fact, q16 salary must be BM25 0 / empty retrieve, q01 must retrieve an Agoda cite_id or Agoda role fact. The 25-question LLM eval still needs a billed key.

### Results (first committed run)

`overall_pass` on `eval/results.json` is **False**. This table is the billed-model run at `2026-09-14T17:21:10Z` (`gpt-4o-mini`, 25 items, 14391 prompt + 1235 completion tokens, 0 API errors) — not the earlier 429 quota-exhausted run. Correctness 11/16 missed ≥ 0.70 by one item; refusal_correctness 8/9 missed = 1.00. Hallucination 0/25 and citation validity 13/13 passed. `python -m eval.retrieve_check` passed (q04 education, q16 salary BM25 0, q01 Agoda). If a reviewer's key is unauthorized or out of credit, `python -m eval.run` still prints a loud error and does not write a fake pass.

| Metric | Value | Pass bar | Passed |
| --- | --- | --- | --- |
| correctness | 11/16 = 68.75% | ≥ 0.70 | no |
| hallucination_rate | 0/25 = 0.00% | = 0 | yes |
| refusal_correctness | 8/9 = 88.89% | = 1.00 | no |
| citation_validity | 13/13 = 100.00% | ≥ 0.90 | yes |
| p95 latency | 2245 ms | reported | — |
| mean cost/question | $0.000116 (eval total $0.002900) | reported | — |
| **overall_pass** | **False** | all four bars | **no** |

Error analysis of two real failures (`q06_ncs_tenure` missing the substring `rewards`; `q20_agoda_leave_date` stating the blank Agoda end date instead of the refusal template) is in `eval/RESULTS.md`.

### If this guarded money movement

Add invariant tests (amounts, currency, account identity must match a ledger row, not a similar chunk), dual-run consistency (two samples must not disagree on those fields), a human review queue for low BM25 / gate failures, and a canary in production that replays a frozen golden set. Continuously: CI on every corpus or prompt change, plus a nightly run against the live model version, with a freeze if hallucination_rate leaves 0.

## Known limitations and next

- The corpus is the August 2026 CV only. LinkedIn is not a source (wrong-person ingest was deleted; the candidate's profile was not ingested). Stated in `knowledge/redactions.md`.
- `facts.yaml` can drift from the markdown (self-review in `docs/DECISIONS.md`).
- Substring eval is strict and will punish a correct paraphrase.
- BM25 will miss a question that uses only synonyms ("cluster" vs "kubernetes") unless a fact row saves it.
- Next three things: human spot-check agreement, a labelled authored project write-up, CI eval. See `docs/DECISIONS.md`.

## AI-usage note

A coding assistant drafted layout and code. Knowledge claims, eval labels, and the conflict policy were not delegated. Details in `docs/DECISIONS.md`.

## Time spent

Recorded after the billed eval. Environment setup (broken system Python, venv) does not count against the box. The 120-minute judgement budget was exceeded; the extra time was a wrong-person LinkedIn ingest (wiped) and an OpenAI quota miss before the billed run — not extra features.

- Reading the brief and choosing the cut: ~20 minutes.
- Knowledge layer, including replacing the wrong LinkedIn corpus with the August 2026 CV: ~40 minutes.
- Ask path (retrieve, generate, gate, CLI): ~30 minutes.
- Evaluation dataset, retrieve_check, billed `eval.run`, error analysis: ~45 minutes.
- Decisions and README: ~20 minutes.

Wall-clock with pairing was longer than 120 minutes. Commit history is logical slices, not a replay of that clock.

## Declare

Nothing in this repository was copied from a prior personal project or a public RAG template. The knowledge corpus is a cleaned extract of the candidate CV (`PHUONG HUYNH_8.2026.docx`); phone, email, and neighborhood-level address are redacted. The docx is not committed.
