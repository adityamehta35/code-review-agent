"""Search tool — grep/glob over the local repo for context during review."""

import os
import subprocess
from pathlib import Path


def grep_codebase(pattern: str, path: str = ".", file_glob: str = "*.py") -> list[dict]:
    """Search files in a directory for a regex pattern. Returns matched lines."""
    result = subprocess.run(
        ["grep", "-rn", "--include", file_glob, pattern, path],
        capture_output=True,
        text=True,
    )
    matches = []
    for line in result.stdout.strip().splitlines():
        # grep -n output: filename:lineno:content
        parts = line.split(":", 2)
        if len(parts) >= 3:
            matches.append(
                {
                    "file": parts[0],
                    "line": int(parts[1]),
                    "content": parts[2].strip(),
                }
            )
    return matches


def find_files(path: str = ".", pattern: str = "**/*.py") -> list[str]:
    """Find files matching a glob pattern under path."""
    base = Path(path)
    return [str(p) for p in base.glob(pattern) if p.is_file()]


def read_file_snippet(filepath: str, start_line: int, end_line: int) -> str:
    """Read specific line range from a file for context."""
    try:
        lines = Path(filepath).read_text(encoding="utf-8", errors="replace").splitlines()
        snippet = lines[max(0, start_line - 1) : end_line]
        return "\n".join(f"{start_line + i}: {l}" for i, l in enumerate(snippet))
    except (OSError, UnicodeDecodeError) as exc:
        return f"Error reading file: {exc}"


# ---------------------------------------------------------------------------
# Tool definitions for Claude tool use
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "grep_codebase",
        "description": (
            "Search files in a local directory for a regex pattern. "
            "Useful for finding usages of a function, class, or symbol in the broader codebase."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for."},
                "path": {"type": "string", "description": "Directory to search (default: current directory)."},
                "file_glob": {
                    "type": "string",
                    "description": "File glob filter, e.g. '*.py' or '*.ts' (default: *.py).",
                },
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "find_files",
        "description": "Find files matching a glob pattern under a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Root directory to search."},
                "pattern": {"type": "string", "description": "Glob pattern, e.g. '**/*.py'."},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "read_file_snippet",
        "description": "Read a line range from a local file for additional context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to the file to read."},
                "start_line": {"type": "integer", "description": "First line to read (1-indexed)."},
                "end_line": {"type": "integer", "description": "Last line to read (inclusive)."},
            },
            "required": ["filepath", "start_line", "end_line"],
        },
    },
]
