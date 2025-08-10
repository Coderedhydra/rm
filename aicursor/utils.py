import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console

console = Console()


def load_api_key_from_env() -> Optional[str]:
    """Load GEMINI_API_KEY from environment or .env file."""
    load_dotenv()  # load from .env if present
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[red]GEMINI_API_KEY is not set. Export it or add it to .env[/red]")
        return None
    return api_key


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text_file(root: Path, relative_path: str, content: str, force: bool = False) -> Path:
    """Write content to a file under root at relative_path.

    Respects force flag to prevent accidental overwrite.
    """
    file_path = root / relative_path
    ensure_directory(file_path.parent)
    if file_path.exists() and not force:
        raise FileExistsError(f"File exists: {file_path}. Use --force to overwrite.")
    file_path.write_text(content, encoding="utf-8")
    return file_path