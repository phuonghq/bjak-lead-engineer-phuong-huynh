# Knowledge layer

What the assistant can see, how it got there, how it is retrieved, and how to add a source without redesigning the pipeline.

## What it can see

| Source | File | What it is |
| --- | --- | --- |
| `cv` | `sources/cv.md` | Source of truth. Cleaned August 2026 CV. Minimum source required by the brief. |
| `projects` | `sources/projects.md` | Project bullets copied from the CV role descriptions (Agoda Supply Platform, NCS Rewards, Alibaba AliPay/Lazada/DARAZ, VinID resident-service, Quoine crypto exchange). |
| `working-style` | `sources/working-style.md` | Mentoring, ownership, collaboration, and ops behaviour quoted from CV bullets. |
| `facts` | `facts.yaml` | Structured roles + education + the CV's "8+ years" claim. Agoda `end` is `unspecified`. |

There is **no LinkedIn source**. See `redactions.md`. See `conflicts.md` for the Agoda missing end date.

## Collect → clean → structure → index

1. **Collect.** Candidate CV `PHUONG HUYNH_8.2026.docx` (August 2026). Converted with `textutil`; the docx is not committed.
2. **Clean.** Strip phone, email, WhatsApp/Zalo, and neighborhood-level address. Do not ingest LinkedIn.
3. **Structure.** Each markdown file has YAML frontmatter (`id`, `type`, `as_of`, `provenance`). Roles also live in `facts.yaml` so date/title questions do not depend on BM25 luck.
4. **Index.** `python -m knowledge.ingest` splits markdown on `## ` headings, slugifies headings into citation ids (`cv#summary`), and writes `index.json`.

`index.json` is generated. Re-run ingest after editing sources. It is committed so a reviewer can run the assistant without an extra step, and so eval is reproducible.

## Storage and retrieval

- On disk: markdown + `facts.yaml` + `index.json` (no vector database).
- At query time: BM25 over chunk tokens (k=4) plus a lexical lookup of `facts.yaml` rows whose employer/title/claim tokens hit the question.
- If the best BM25 score is 0 after stopwording, the model is **not** called. The user gets the refusal template.

## Adding a source later (without LinkedIn)

1. Drop `knowledge/sources/<name>.md` with the same frontmatter shape. Do not add a LinkedIn scrape unless the candidate asks for it and you have verified it is theirs.
2. If it contains roles or claims that should be exact-matchable, append a row to `facts.yaml` with `source_id` set to that file's `id`.
3. Run `python -m knowledge.ingest`.
4. Add eval questions that would fail if the new source were missing. Multi-source items should combine CV sections (experience + projects, or two jobs), not CV+LinkedIn.

No schema change, no new store, no prompt rewrite required for ingestion. The ask path already cites whatever `cite_id` the index carries.

## Maintenance

- `as_of` on each file is the CV month (2026-08). Stale facts are expected; the gap policy is "show what is written", not "fill in Present".
- To retire a source, delete the file (and any facts rows pointing at it) and re-ingest.
