"""Score eval/dataset.jsonl. One command: python -m eval.run"""

from __future__ import annotations

import json
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from assistant.ask import ask  # noqa: E402
from assistant.generate import is_billed_key_failure, probe_llm  # noqa: E402
from eval.metrics import (  # noqa: E402
    PASS_BAR,
    is_api_error,
    item_citation_valid,
    item_correctness,
    item_hallucinated,
    item_refusal_correct,
)
from eval.retrieve_check import run_retrieve_checks  # noqa: E402

DATASET = Path(__file__).resolve().parent / "dataset.jsonl"
RESULTS_JSON = Path(__file__).resolve().parent / "results.json"
RESULTS_MD = Path(__file__).resolve().parent / "RESULTS.md"

_SECRET = re.compile(r"sk-[A-Za-z0-9_-]+")


def load_dataset() -> list[dict]:
    items = []
    for line in DATASET.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            items.append(json.loads(line))
    return items


def ratio(flags: list[bool]) -> tuple[int, int, float]:
    if not flags:
        return 0, 0, 0.0
    num = sum(1 for f in flags if f)
    den = len(flags)
    return num, den, num / den


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round(0.95 * (len(ordered) - 1)))))
    return ordered[idx]


def _public_detail(detail: str) -> str:
    return _SECRET.sub("sk-[redacted]", detail)[:240]


def _abort_llm_eval(kind: str, detail: str) -> None:
    public = _public_detail(detail)
    print()
    print("=" * 72)
    if is_billed_key_failure(kind, detail):
        print("ERROR: LLM eval cannot run without a billed OpenAI key.")
        print(f"Probe failed ({kind}): {public}")
        print("python -m eval.run needs a billed OPENAI_API_KEY in .env.")
    else:
        print("ERROR: LLM eval cannot run; the OpenAI probe failed.")
        print(f"Probe failed ({kind}): {public}")
    print("API-error excerpt fallback is not scored as correct.")
    print("Not writing a pass table as if the model answered.")
    print("Retrieval without a model still ran above (python -m eval.retrieve_check).")
    print("=" * 72)
    sys.exit(1)


def main() -> None:
    retrieve_ok = run_retrieve_checks()
    ok, kind, detail = probe_llm()
    if not ok:
        _abort_llm_eval(kind, detail)

    items = load_dataset()
    rows = []
    for item in items:
        result = ask(item["question"])
        payload = result.to_dict()
        retrieved_ids = [c["cite_id"] for c in payload["retrieved"]]
        api_err = is_api_error(result.fallback, result.refusal_reason)
        correct = item_correctness(
            item, result.answer, result.refused, result.fallback, result.refusal_reason
        )
        hallucinated = item_hallucinated(item, result.answer)
        refusal = item_refusal_correct(
            item, result.answer, result.refused, result.fallback, result.refusal_reason
        )
        cite_ok = item_citation_valid(item, result.refused, result.citations, retrieved_ids)
        rows.append(
            {
                "id": item["id"],
                "category": item["category"],
                "question": item["question"],
                "should_refuse": item["should_refuse"],
                "correct": correct,
                "hallucinated": hallucinated,
                "refusal_correct": refusal,
                "citation_valid": cite_ok,
                "api_error": api_err,
                "refused": result.refused,
                "fallback": result.fallback,
                "refusal_reason": result.refusal_reason,
                "latency_ms": result.latency_ms,
                "cost_usd": result.cost_usd,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "citations": result.citations,
                "retrieved_ids": retrieved_ids,
                "answer_preview": result.answer[:400],
            }
        )
        mark = "FAIL" if hallucinated or correct is False or refusal is False or cite_ok is False else "ok"
        extra = " api_error" if api_err else ""
        print(f"{item['id']:28} {item['category']:14} {mark:4}  {result.latency_ms:7.0f}ms  refused={result.refused}{extra}")

    correctness_flags = [r["correct"] for r in rows if r["correct"] is not None]
    hallucination_flags = [r["hallucinated"] for r in rows]
    refusal_flags = [r["refusal_correct"] for r in rows if r["refusal_correct"] is not None]
    citation_flags = [r["citation_valid"] for r in rows if r["citation_valid"] is not None]
    latencies = [r["latency_ms"] for r in rows]
    costs = [r["cost_usd"] for r in rows]

    c_num, c_den, c_val = ratio(correctness_flags)
    h_num, h_den, h_val = ratio(hallucination_flags)
    r_num, r_den, r_val = ratio(refusal_flags)
    v_num, v_den, v_val = ratio(citation_flags)
    latency_p95 = p95(latencies)
    mean_cost = statistics.mean(costs) if costs else 0.0
    total_cost = sum(costs)

    metrics = {
        "correctness": {
            "numerator": c_num,
            "denominator": c_den,
            "value": c_val,
            "definition": "answerable items (should_refuse=false) where every must_contain appears and the answer is not a refusal; API-error fallback is always False",
            "pass_if": f">= {PASS_BAR['correctness']}",
            "passed": c_val >= PASS_BAR["correctness"],
        },
        "hallucination_rate": {
            "numerator": h_num,
            "denominator": h_den,
            "value": h_val,
            "definition": "items whose answer contains any must_never_claim string",
            "pass_if": f"== {PASS_BAR['hallucination_rate']}",
            "passed": h_val == PASS_BAR["hallucination_rate"],
        },
        "refusal_correctness": {
            "numerator": r_num,
            "denominator": r_den,
            "value": r_val,
            "definition": "should_refuse=true items that match a refusal marker and contain no must_never_claim; API-error fallback is always False",
            "pass_if": f"== {PASS_BAR['refusal_correctness']}",
            "passed": r_val == PASS_BAR["refusal_correctness"],
        },
        "citation_validity": {
            "numerator": v_num,
            "denominator": v_den,
            "value": v_val,
            "definition": "non-refused answerable items whose parsed [cite_id] set is non-empty and subset of retrieved ids",
            "pass_if": f">= {PASS_BAR['citation_validity']}",
            "passed": v_val >= PASS_BAR["citation_validity"],
        },
        "p95_latency_ms": {
            "value": latency_p95,
            "definition": "95th percentile wall-clock of ask() over the dataset (sorted, nearest-rank)",
        },
        "mean_cost_usd": {
            "value": mean_cost,
            "total_usd": total_cost,
            "definition": "mean of per-question cost_usd from token usage and gpt-4o-mini list prices in assistant/config.py",
        },
    }

    overall = all(
        metrics[k]["passed"]
        for k in ("correctness", "hallucination_rate", "refusal_correctness", "citation_validity")
    )
    report = {
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "n_items": len(rows),
        "pass_bar": PASS_BAR,
        "overall_pass": overall,
        "retrieve_check_passed": retrieve_ok,
        "metrics": metrics,
        "rows": rows,
    }
    RESULTS_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    RESULTS_MD.write_text(_markdown(report), encoding="utf-8")
    print()
    print(f"correctness          {c_num}/{c_den} = {c_val:.2%}  bar>={PASS_BAR['correctness']}  pass={metrics['correctness']['passed']}")
    print(f"hallucination_rate   {h_num}/{h_den} = {h_val:.2%}  bar=={PASS_BAR['hallucination_rate']}  pass={metrics['hallucination_rate']['passed']}")
    print(f"refusal_correctness  {r_num}/{r_den} = {r_val:.2%}  bar=={PASS_BAR['refusal_correctness']}  pass={metrics['refusal_correctness']['passed']}")
    print(f"citation_validity    {v_num}/{v_den} = {v_val:.2%}  bar>={PASS_BAR['citation_validity']}  pass={metrics['citation_validity']['passed']}")
    print(f"p95_latency_ms       {latency_p95:.0f}")
    print(f"mean_cost_usd        {mean_cost:.6f}  (total {total_cost:.6f})")
    print(f"overall_pass         {overall}")
    print(f"wrote {RESULTS_JSON.relative_to(ROOT)} and {RESULTS_MD.relative_to(ROOT)}")
    if not overall:
        sys.exit(1)


def _markdown(report: dict) -> str:
    m = report["metrics"]

    def cell(v):
        if v is None:
            return "—"
        return "yes" if v else "NO"

    lines = [
        "# Evaluation results",
        "",
        f"Ran at `{report['ran_at']}` on {report['n_items']} items. Pass bar was declared in `eval/metrics.py` before this run.",
        "",
        f"Overall pass: **{report['overall_pass']}**",
        "",
        "## Metrics",
        "",
        f"- correctness: {m['correctness']['numerator']}/{m['correctness']['denominator']} = {m['correctness']['value']:.2%} (bar {m['correctness']['pass_if']}, passed={m['correctness']['passed']})",
        f"- hallucination_rate: {m['hallucination_rate']['numerator']}/{m['hallucination_rate']['denominator']} = {m['hallucination_rate']['value']:.2%} (bar {m['hallucination_rate']['pass_if']}, passed={m['hallucination_rate']['passed']})",
        f"- refusal_correctness: {m['refusal_correctness']['numerator']}/{m['refusal_correctness']['denominator']} = {m['refusal_correctness']['value']:.2%} (bar {m['refusal_correctness']['pass_if']}, passed={m['refusal_correctness']['passed']})",
        f"- citation_validity: {m['citation_validity']['numerator']}/{m['citation_validity']['denominator']} = {m['citation_validity']['value']:.2%} (bar {m['citation_validity']['pass_if']}, passed={m['citation_validity']['passed']})",
        f"- p95 latency: {m['p95_latency_ms']['value']:.0f} ms",
        f"- mean cost/question: ${m['mean_cost_usd']['value']:.6f} (eval total ${m['mean_cost_usd']['total_usd']:.6f})",
        "",
        "## Per-item",
        "",
        "| id | category | correct | halluc | refusal | cite | api_error | latency_ms |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in report["rows"]:
        lines.append(
            f"| {r['id']} | {r['category']} | {cell(r['correct'])} | {cell(r['hallucinated'])} | "
            f"{cell(r['refusal_correct'])} | {cell(r['citation_valid'])} | {cell(r.get('api_error'))} | "
            f"{r['latency_ms']:.0f} |"
        )
    lines.extend(
        [
            "",
            "## Error analysis",
            "",
            "Filled after the first real run. Failures with `correct=NO` or `refusal=NO` are expanded in the root README.",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
