"""Linter tool — run Ruff on Python source code and return structured results."""

import json
import subprocess
import tempfile
from pathlib import Path


def run_ruff_linter(code: str, filename: str = "review_target.py") -> list[dict]:
    """
    Run Ruff on a Python source string.

    Returns a list of issue dicts, each with:
        file, line, col, code, message, fix_available (bool)
    """
    suffix = Path(filename).suffix or ".py"
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8") as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [
                "ruff",
                "check",
                "--output-format=json",
                "--no-cache",
                tmp_path,
            ],
            capture_output=True,
            text=True,
        )

        issues: list[dict] = []
        # Ruff exits 1 when there are violations — that is expected
        if not result.stdout.strip():
            return issues

        try:
            raw: list[dict] = json.loads(result.stdout)
        except json.JSONDecodeError:
            return [
                {
                    "file": filename,
                    "line": None,
                    "col": None,
                    "code": "PARSE_ERROR",
                    "message": f"Could not parse ruff output: {result.stdout[:300]}",
                    "fix_available": False,
                }
            ]

        for item in raw:
            location = item.get("location", {})
            issues.append(
                {
                    "file": filename,
                    "line": location.get("row"),
                    "col": location.get("column"),
                    "code": item.get("code", "unknown"),
                    "message": item.get("message", ""),
                    "fix_available": item.get("fix") is not None,
                    "url": item.get("url", ""),
                }
            )

        return issues

    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# Tool schema for the Anthropic API
# ──────────────────────────────────────────────────────────────────────────────

TOOLS: list[dict] = [
    {
        "name": "run_ruff_linter",
        "description": (
            "Run the Ruff linter on a Python source string. "
            "Returns a list of style, correctness, and import issues with line numbers, "
            "Ruff rule codes (e.g. E501, F401), and whether an auto-fix is available."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python source code to lint.",
                },
                "filename": {
                    "type": "string",
                    "description": "Original filename shown in results (default: review_target.py).",
                },
            },
            "required": ["code"],
        },
    },
]
