# Decisions

Each record: the call, the alternative that was rejected, and the constraint that decided it. Written during the slice, not after the fact.

## D1 — Retrieval-augmented generation with a citation gate, not a single stuffed prompt

**Chose.** Chunk the corpus, BM25-retrieve top 4, add structured fact hits, then call `gpt-4o-mini` with a citation-required prompt and a post-gate.

**Rejected.** Dump the whole CV into one chat completion.

**Constraint.** The brief's load-bearing rule is traceability: a stated fact must map to a source, or the system must refuse. A stuffed prompt cannot score retrieval, cannot add a source without growing the prompt, and cannot fail closed when overlap is zero. The corpus is tens of chunks, so a vector database was also rejected: BM25 is enough and is explainable in the live 30 minutes.

## D2 — Lexical BM25 plus `facts.yaml`, not embeddings

**Chose.** `rank-bm25` over section chunks, plus exact token overlap on structured roles and the CV's "8+ years" claim.

**Rejected.** OpenAI embeddings + a local vector index (Chroma / FAISS).

**Constraint.** Time box and defendability. Embeddings add a second model, a distance threshold nobody can recompute by hand, and a failure mode (semantic near-misses that look confident). Date and title questions are exact. The Agoda missing end date is exact. Those belong in YAML.

## D3 — Rule-based eval, not LLM-as-judge

**Chose.** `must_contain` / `must_never_claim` / `should_refuse` labels, scored by substring checks in `eval/metrics.py`.

**Rejected.** LLM-as-judge with a second prompt.

**Constraint.** A metric nobody can recompute is not a metric. LLM-as-judge would need its own prompt committed, a spot-check agreement number, and another API call per item. The pass bar is declared in code before the first run. We accepted that substring labels are strict (and will miss a paraphrased-but-correct answer) in exchange for numbers a reviewer can recompute from `eval/results.json`.

## D4 — CLI that prints sources, not a chat UI

**Chose.** `python -m assistant ask "…"`.

**Rejected.** Streamlit / a chat window.

**Constraint.** The brief says they would rather see a CLI that shows its sources than a polished chat window that does not. The interface serves a hiring manager who needs to *verify*, not a candidate who needs to *impress*. Conversation history and streaming were optional and were cut.

## D5 — Refuse before the model when BM25 is zero (after stripping the name)

**Chose.** If the query, minus stopwords and the tokens `phuong` / `huynh`, has no lexical overlap, do not call the model.

**Rejected.** Always call the model and trust the system prompt to refuse.

**Constraint.** Name-only overlap would retrieve the whole CV for "Phuong was CTO at Google, right?". That is how a model gets enough fluent context to agree. Not calling it is the deterministic fallback the brief asks for on the unusable-input path.

## D6 — Python for this slice, not Java

**Chose.** Python 3.12, `openai` SDK, `rank-bm25`, Typer CLI, a one-command eval.

**Rejected.** Java (the production / main stack): OpenAI HTTP client + Lucene or a hand-rolled BM25 + JUnit.

**Constraint.** The brief scores groundedness, eval, and judgement under 120 minutes, not framework familiarity. It also says a fashionable stack scores no better than a justified one. Python is the faster eval loop. Java is what I would ship on my team. Evidence to switch: the live review requires a change I cannot make confidently in Python, or this moves from a take-home into a service my team owns.

## D7 — Omit LinkedIn on purpose

**Chose.** No LinkedIn file in the corpus. The assistant sees the August 2026 CV and files derived from it only.

**Rejected.** Scrape the candidate's real profile https://www.linkedin.com/in/phuong-huynh-510b54124/ — or keep the earlier ingest of https://www.linkedin.com/in/phuonghd.

**Constraint.** The CV is the brief's minimum. The first ingest was the **wrong person** (Startech / Grove & Dean). Using it is the same failure class as fabricating an employer. The candidate does not maintain LinkedIn and asked it removed. A neglected or wrong profile is a fabrication risk, not a useful stale-source demo. The real gap is inside the CV: Agoda `07/2023 –` with no end date.

## What was cut, and the next three things

Cut inside the time box: embeddings, LangChain, agents, a web UI, conversation memory, streaming, LLM-as-judge, any attempt to ingest GitHub or local IdeaProjects code (unverified authorship).

Next three, in order:

1. Human spot-check of 20 eval answers against the labels (the missing agreement number).
2. A labelled project write-up the candidate actually authored (not LinkedIn, not unverified GitHub) and two new multi-source questions against it.
3. Nightly eval in CI on corpus or prompt change, with a groundedness regression budget.

## AI use

Used a coding assistant to draft repo layout, ingest/retrieve/ask/eval code, and first-pass README prose.

Changed after review: the first knowledge corpus was the wrong LinkedIn profile and was wiped; sources were rewritten from PHUONG HUYNH_8.2026.docx only; PII was redacted; eval labels were written by hand against that CV; the name-token BM25 strip was added because a name-only retrieve would have failed the adversarial Google item in a way that looks like a model bug but is a retrieval bug.

**Refused to let a model decide:** the gap policy (Agoda has no end date — do not invent Present) and every `must_contain` / `must_never_claim` / `should_refuse` label. Those are the score.

## Self-review (two comments I would leave on this PR)

1. `facts.yaml` is hand-maintained beside the markdown. Ingest does not extract roles from CV headings, so a new job added only to `cv.md` is invisible to fact lookup until someone edits YAML. Either generate facts from a single table, or fail ingest when a role heading has no facts row.
2. Citation validity checks ids, not that the cited chunk actually entails the sentence. A model can cite `[cv#summary]` while stating a date that lives in another chunk. That is the next gate if this guarded money movement.
