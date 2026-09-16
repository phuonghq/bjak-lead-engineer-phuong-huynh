"""Ingest markdown sources and facts.yaml into knowledge/index.json."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

KNOWLEDGE_DIR = Path(__file__).resolve().parent
SOURCES_DIR = KNOWLEDGE_DIR / "sources"
FACTS_PATH = KNOWLEDGE_DIR / "facts.yaml"
INDEX_PATH = KNOWLEDGE_DIR / "index.json"

HEADING_SPLIT = re.compile(r"^##\s+", re.MULTILINE)
NON_SLUG = re.compile(r"[^a-z0-9]+")


def slug(heading: str) -> str:
    s = NON_SLUG.sub("-", heading.strip().lower()).strip("-")
    return s or "body"


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = yaml.safe_load(parts[1]) or {}
    return meta, parts[2].lstrip("\n")


def chunk_markdown(source_id: str, source_type: str, as_of: str, body: str) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    sections = HEADING_SPLIT.split(body)
    preamble = sections[0].strip()
    if preamble and not preamble.startswith("#"):
        chunks.append(_chunk(source_id, source_type, as_of, "preamble", preamble))
    elif preamble.startswith("#"):
        # Keep the H1 + any intro before the first ## as a title chunk only if there is
        # substance beyond a single heading line.
        lines = preamble.splitlines()
        rest = "\n".join(lines[1:]).strip()
        if rest:
            chunks.append(_chunk(source_id, source_type, as_of, "title", rest))
    for section in sections[1:]:
        if not section.strip():
            continue
        heading, _, text = section.partition("\n")
        heading = heading.strip()
        text = text.strip()
        body_text = f"{heading}\n\n{text}".strip()
        chunks.append(_chunk(source_id, source_type, as_of, heading, body_text))
    if not chunks:
        chunks.append(_chunk(source_id, source_type, as_of, "full", body.strip()))
    return chunks


def _chunk(source_id: str, source_type: str, as_of: str, heading: str, text: str) -> dict[str, Any]:
    cite_id = f"{source_id}#{slug(heading)}"
    return {
        "cite_id": cite_id,
        "source_id": source_id,
        "type": source_type,
        "heading": heading,
        "text": text,
        "as_of": as_of,
    }


def facts_to_chunks(facts: dict[str, Any]) -> list[dict[str, Any]]:
    as_of = str(facts.get("as_of", ""))
    chunks: list[dict[str, Any]] = []
    for i, role in enumerate(facts.get("roles") or []):
        heading = f"Role {role.get('employer')}"
        text = (
            f"Employer: {role.get('employer')}. Title: {role.get('title')} "
            f"from {role.get('start')} to {role.get('end')}. "
            f"Location: {role.get('location', 'unspecified')}."
        )
        chunk = _chunk("facts", "facts", as_of, heading, text)
        chunk["cite_id"] = f"facts#role-{i}"
        chunk["heading"] = heading
        chunk["fact_kind"] = "role"
        chunk["employer"] = role.get("employer")
        chunk["title"] = role.get("title")
        chunks.append(chunk)
    for i, edu in enumerate(facts.get("education") or []):
        heading = f"Education {edu.get('institution')}"
        text = (
            f"{edu.get('degree')} at {edu.get('institution')} "
            f"from {edu.get('start')} to {edu.get('end')}."
        )
        chunk = _chunk("facts", "facts", as_of, heading, text)
        chunk["cite_id"] = f"facts#education-{i}"
        chunk["fact_kind"] = "education"
        chunks.append(chunk)
    for i, claim in enumerate(facts.get("experience_claims") or []):
        heading = f"Experience claim {claim.get('claim')}"
        text = (
            f"Experience-length claim: {claim.get('claim')}. "
            f"{claim.get('note', '')}"
        )
        chunk = _chunk("facts", "facts", as_of, heading, text)
        chunk["cite_id"] = f"facts#experience-claim-{i}"
        chunk["fact_kind"] = "experience_claim"
        chunk["claim"] = claim.get("claim")
        chunks.append(chunk)
    return chunks


def ingest() -> dict[str, Any]:
    chunks: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for path in sorted(SOURCES_DIR.glob("*.md")):
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        source_id = str(meta.get("id") or path.stem)
        source_type = str(meta.get("type") or "unknown")
        as_of = str(meta.get("as_of") or "")
        provenance = str(meta.get("provenance") or "")
        sources.append(
            {
                "id": source_id,
                "type": source_type,
                "as_of": as_of,
                "provenance": provenance,
                "path": str(path.relative_to(KNOWLEDGE_DIR.parent)),
            }
        )
        chunks.extend(chunk_markdown(source_id, source_type, as_of, body))
    facts = yaml.safe_load(FACTS_PATH.read_text(encoding="utf-8")) or {}
    fact_chunks = facts_to_chunks(facts)
    chunks.extend(fact_chunks)
    index = {
        "ingested_at": date.today().isoformat(),
        "sources": sources,
        "facts": facts,
        "chunks": chunks,
    }
    INDEX_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return index


def main() -> None:
    index = ingest()
    print(
        f"Wrote {INDEX_PATH.relative_to(KNOWLEDGE_DIR.parent)} "
        f"with {len(index['chunks'])} chunks from {len(index['sources'])} sources."
    )


if __name__ == "__main__":
    main()
