from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, request, send_file, Response
from rich.console import Console

from .generator import generate_project, plan_project
from .utils import ensure_directory

app = Flask(__name__)
console = Console()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\-\_\s]+", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value or "project"


HTML_INDEX = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI Cursor - Text Project Generator</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 16px; }
    h1 { font-size: 1.6rem; }
    textarea { width: 100%; height: 180px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 14px; }
    .row { display: flex; gap: 12px; align-items: center; margin: 8px 0; }
    .row > * { flex: 1; }
    button { padding: 10px 16px; font-weight: 600; }
    .note { color: #666; font-size: 0.9rem; }
    .footer { margin-top: 24px; color: #777; font-size: 0.85rem; }
    .status { margin: 10px 0; }
  </style>
</head>
<body>
  <h1>AI Cursor - Text Project Generator</h1>
  <p class="note">Enter a natural language description of the project. The server will generate a minimal runnable project and return a zip file.</p>
  <form method="POST" action="/generate">
    <label for="prompt">Project request</label><br />
    <textarea id="prompt" name="prompt" placeholder="e.g., Build a FastAPI microservice with one GET /health endpoint and Dockerfile" required></textarea>

    <div class="row">
      <div>
        <label for="language">Language</label><br />
        <select id="language" name="language">
          <option value="python" selected>Python</option>
          <option value="javascript">JavaScript</option>
          <option value="go">Go</option>
          <option value="java">Java</option>
        </select>
      </div>
      <div>
        <label for="force">Overwrite existing files</label><br />
        <select id="force" name="force">
          <option value="false" selected>No</option>
          <option value="true">Yes</option>
        </select>
      </div>
    </div>

    <button type="submit">Generate and Download Zip</button>
  </form>

  <div class="footer">
    This runs locally using your GEMINI_API_KEY environment variable.
  </div>
</body>
</html>
"""


@app.get("/")
def index() -> Response:
    return Response(HTML_INDEX, mimetype="text/html")


@app.post("/generate")
def generate() -> Response:
    prompt = request.form.get("prompt", "").strip()
    language = request.form.get("language", "python").strip() or "python"
    force = (request.form.get("force", "false").lower() == "true")

    if not prompt:
        return Response("Missing prompt", status=400)

    # Pre-plan to derive a folder and zip name
    plan = plan_project(prompt, language=language)
    if plan is None:
        return Response("Planning failed. Check server logs for details.", status=500)

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    base_name = slugify(plan.project_name)
    out_dir = Path("./web-output") / f"{base_name}-{timestamp}"
    ensure_directory(out_dir)

    console.print(f"[cyan]Generating project into {out_dir}...[/cyan]")
    exit_code = generate_project(
        user_prompt=prompt,
        output_dir=out_dir,
        language=language,
        force=force,
        dry_run=False,
    )
    if exit_code != 0:
        return Response("Generation failed. Check server logs for details.", status=500)

    # Create a zip archive and return as download
    archive_base = str(out_dir)
    shutil.make_archive(archive_base, "zip", root_dir=out_dir)
    zip_path = Path(archive_base + ".zip")

    download_name = f"{base_name}.zip"
    return send_file(zip_path, as_attachment=True, download_name=download_name, mimetype="application/zip")


if __name__ == "__main__":
    # Default to 0.0.0.0 so it is reachable from containers/devboxes
    app.run(host="0.0.0.0", port=8000, debug=True)