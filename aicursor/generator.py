import json
import os
from pathlib import Path
from typing import List, Optional

import google.generativeai as genai
from pydantic import BaseModel, Field, ValidationError
from rich.console import Console
from rich.table import Table

from .prompts import (
    PROJECT_PLANNING_SYSTEM_INSTRUCTION,
    PROJECT_PLAN_USER_PROMPT_TEMPLATE,
    FILE_GENERATION_SYSTEM_INSTRUCTION,
    FILE_PROMPT_TEMPLATE,
)
from .utils import ensure_directory, load_api_key_from_env, write_text_file

console = Console()


class PlannedFile(BaseModel):
    path: str = Field(..., description="Relative path from project root, e.g., src/app.py")
    description: str = Field(..., description="One line describing the file's purpose")
    language: Optional[str] = Field(None, description="Language of this file, if applicable")
    overwrite_ok: bool = Field(False, description="If true, this file may be overwritten without force")


class ProjectPlan(BaseModel):
    project_name: str
    summary: str
    language: str = Field("python")
    dependencies: List[str] = Field(default_factory=list)
    files: List[PlannedFile]
    post_generation_commands: List[str] = Field(default_factory=list)


def _configure_client() -> Optional[genai.GenerativeModel]:
    api_key = load_api_key_from_env()
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=PROJECT_PLANNING_SYSTEM_INSTRUCTION,
    )
    return model


def plan_project(user_prompt: str, language: str = "python") -> Optional[ProjectPlan]:
    model = _configure_client()
    if model is None:
        return None

    generation_config = {
        "temperature": 0.4,
        "response_mime_type": "application/json",
        "response_schema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string"},
                "summary": {"type": "string"},
                "language": {"type": "string"},
                "dependencies": {"type": "array", "items": {"type": "string"}},
                "files": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "description": {"type": "string"},
                            "language": {"type": "string"},
                            "overwrite_ok": {"type": "boolean"},
                        },
                        "required": ["path", "description"],
                        "additionalProperties": False,
                    },
                },
                "post_generation_commands": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["project_name", "summary", "language", "files"],
            "additionalProperties": False,
        },
    }

    user_prompt_text = PROJECT_PLAN_USER_PROMPT_TEMPLATE.format(language=language) + user_prompt

    console.print("[cyan]Planning project with Gemini 2.5 Flash...[/cyan]")
    response = model.generate_content(user_prompt_text, generation_config=generation_config)

    try:
        plan_json = response.text
        plan_obj = json.loads(plan_json)
        plan = ProjectPlan(**plan_obj)
        return plan
    except (json.JSONDecodeError, ValidationError) as exc:
        console.print(f"[red]Failed to parse plan: {exc}[/red]")
        console.print("Raw response:")
        console.print(response.text)
        return None


def generate_file_content(
    file_path: str,
    file_description: str,
    project_summary: str,
    language: str,
) -> Optional[str]:
    api_key = load_api_key_from_env()
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=FILE_GENERATION_SYSTEM_INSTRUCTION,
    )

    prompt = FILE_PROMPT_TEMPLATE.format(
        project_summary=project_summary,
        file_path=file_path,
        file_description=file_description,
        language=language,
    )

    generation_config = {
        "temperature": 0.3,
        "response_mime_type": "text/plain",
    }

    response = model.generate_content(prompt, generation_config=generation_config)
    return response.text


def print_plan(plan: ProjectPlan) -> None:
    table = Table(title=f"Plan: {plan.project_name}")
    table.add_column("File path")
    table.add_column("Description")
    for f in plan.files:
        table.add_row(f.path, f.description)
    console.print(table)
    if plan.dependencies:
        console.print("[bold]Dependencies:[/bold] " + ", ".join(plan.dependencies))
    if plan.post_generation_commands:
        console.print("[bold]Post-generation commands:[/bold]")
        for cmd in plan.post_generation_commands:
            console.print(f"- {cmd}")


def generate_project(
    user_prompt: str,
    output_dir: Path,
    language: str = "python",
    force: bool = False,
    dry_run: bool = False,
) -> int:
    plan = plan_project(user_prompt=user_prompt, language=language)
    if plan is None:
        return 1

    print_plan(plan)

    if dry_run:
        console.print("[yellow]Dry run: not writing files.[/yellow]")
        return 0

    ensure_directory(output_dir)

    console.print("[cyan]Generating files...[/cyan]")
    for planned_file in plan.files:
        try:
            content = generate_file_content(
                file_path=planned_file.path,
                file_description=planned_file.description,
                project_summary=plan.summary,
                language=plan.language or language,
            )
            if content is None:
                return 1
            write_text_file(
                root=output_dir,
                relative_path=planned_file.path,
                content=content,
                force=force or planned_file.overwrite_ok,
            )
            console.print(f"[green]Wrote[/green] {planned_file.path}")
        except FileExistsError as exc:
            console.print(f"[red]{exc}[/red]")
            return 1
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]Failed to generate {planned_file.path}: {exc}[/red]")
            return 1

    if plan.dependencies:
        # Optionally write a requirements file if language is python
        if (plan.language or language).lower().startswith("python"):
            try:
                reqs = "\n".join(plan.dependencies) + "\n"
                write_text_file(output_dir, "requirements.txt", reqs, force=force)
                console.print("[green]Wrote[/green] requirements.txt from plan dependencies")
            except Exception as exc:  # noqa: BLE001
                console.print(f"[yellow]Could not write planned requirements.txt: {exc}[/yellow]")

    console.print("[bold green]Project generation complete.[/bold green]")
    return 0