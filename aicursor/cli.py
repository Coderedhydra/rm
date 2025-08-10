from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .generator import generate_project

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


@app.command()
def generate(
    prompt: str = typer.Option(
        ..., "--prompt", help="Natural language description of the project to generate"
    ),
    out: Path = typer.Option(
        Path("./generated-project"), "--out", help="Output directory for the generated project"
    ),
    language: str = typer.Option("python", "--language", help="Target language/framework focus"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files if present"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Only plan and preview; do not write files"),
):
    """Generate a new project from a natural language prompt using Gemini 2.5 Flash."""
    exit_code = generate_project(
        user_prompt=prompt,
        output_dir=out,
        language=language,
        force=force,
        dry_run=dry_run,
    )
    raise typer.Exit(code=exit_code)


if __name__ == "__main__":
    app()