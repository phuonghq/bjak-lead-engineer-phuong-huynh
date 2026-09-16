from __future__ import annotations

import json

import typer

from assistant.ask import ask as run_ask

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    help="Grounded assistant for Phuong Huynh's background.",
)


@app.callback()
def _root() -> None:
    """Grounded assistant for Phuong Huynh's background."""


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question a recruiter or interviewer might ask."),
    json_out: bool = typer.Option(False, "--json", help="Print the full AskResult as JSON."),
) -> None:
    result = run_ask(question)
    # Click 8.2+ can pass the default as the string "False"; only --json should dump JSON.
    if json_out is True:
        typer.echo(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return
    typer.echo(result.answer)
    typer.echo("")
    typer.echo("Sources:")
    if not result.retrieved:
        typer.echo("  (none above BM25 threshold)")
    else:
        for chunk in result.retrieved:
            typer.echo(f"  - [{chunk.cite_id}] ({chunk.via}, score={chunk.score:.3f}) {chunk.heading}")
    if result.refused:
        typer.echo(f"\nRefusal: {result.refusal_reason}")
    if result.fallback:
        typer.echo(f"Fallback: {result.fallback}")
    typer.echo(
        f"\nlatency_ms={result.latency_ms:.0f}  tokens={result.prompt_tokens}+{result.completion_tokens}  "
        f"cost_usd={result.cost_usd:.6f}  max_bm25={result.max_bm25:.3f}"
    )


if __name__ == "__main__":
    app()
