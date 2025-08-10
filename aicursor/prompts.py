PROJECT_PLANNING_SYSTEM_INSTRUCTION = (
    "You are an expert software architect and code generator. "
    "Given a natural language product request, produce a coherent, minimal, and runnable project plan."
)

PROJECT_PLAN_USER_PROMPT_TEMPLATE = """
You will create a plan for a new software project based on the user's request.
- The default target stack is {language}; prefer simple scaffolds.
- Keep scope minimal but complete and runnable.
- Include only essential files to run and demonstrate the app.
- Prefer widely used libraries and latest stable patterns.

Return ONLY JSON complying with the response schema. Do not include code fences.
User request:
"""

FILE_GENERATION_SYSTEM_INSTRUCTION = (
    "You are a meticulous senior engineer. Generate complete file contents only. "
    "Do not include explanations or backticks."
)

FILE_PROMPT_TEMPLATE = """
Project overview:
{project_summary}

Generate the complete contents for the file at path: {file_path}
Purpose: {file_description}

Rules:
- Output only the file's raw content. No backticks, no explanation.
- Ensure imports, dependencies, and relative paths are consistent across the project.
- If the file is a config or dependency file, include practical default versions.
- If the language is {language}, follow community conventions.
"""