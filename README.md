# AI Cursor (Minimal)

A minimal, text-only, "Cursor-like" CLI that can generate an entire project from a natural language prompt using Google's Gemini 2.5 Flash.

- Uses `gemini-2.5-flash` via `google-generativeai`
- Python-first support
- Plans the project, then generates files iteratively

## Quick start

1) Create and activate a Python 3.10+ environment

2) Install dependencies:

```bash
pip install -r requirements.txt
```

3) Set your API key (copy `.env.example` to `.env`):

```bash
export GEMINI_API_KEY="YOUR_KEY_HERE"
```

4) Generate a project:

```bash
python -m aicursor.cli generate \
  --prompt "Build a FastAPI microservice with one GET /health endpoint and Dockerfile" \
  --out ./generated-app \
  --language python
```

Flags:
- `--force` to overwrite existing files
- `--dry-run` to preview without writing

## Notes
- Do not commit your real API key. Use the `GEMINI_API_KEY` environment variable.
- This is an MVP. Extend prompts and planning logic for broader language/framework support.
