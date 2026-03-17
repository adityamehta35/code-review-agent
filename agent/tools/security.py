"""Security tool — run Bandit on Python source code and return structured findings."""

import json
import subprocess
import tempfile
from pathlib import Path


# Bandit severity/confidence → our severity mapping
_BANDIT_SEVERITY_MAP = {
    "HIGH": "critical",
    "MEDIUM": "warning",
    "LOW": "suggestion",
    "UNDEFINED": "suggestion",
}


def run_bandit_security(code: str, filename: str = "review_target.py") -> list[dict]:
    """
    Run Bandit on a Python source string.

    Returns a list of security finding dicts, each with:
        file, line, test_id, test_name, severity, confidence, message, more_info (url)
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [
                "bandit",
                "--format", "json",
                "--quiet",
                tmp_path,
            ],
            capture_output=True,
            text=True,
        )

        findings: list[dict] = []
        # Bandit exits 1 when issues are found — that is expected
        output = result.stdout.strip()
        if not output:
            return findings

        try:
            data: dict = json.loads(output)
        except json.JSONDecodeError:
            return [
                {
                    "file": filename,
                    "line": None,
                    "test_id": "PARSE_ERROR",
                    "test_name": "parse_error",
                    "severity": "warning",
                    "confidence": "high",
                    "message": f"Could not parse bandit output: {output[:300]}",
                    "more_info": "",
                }
            ]

        for r in data.get("results", []):
            findings.append(
                {
                    "file": filename,
                    "line": r.get("line_number"),
                    "test_id": r.get("test_id", ""),
                    "test_name": r.get("test_name", ""),
                    "severity": _BANDIT_SEVERITY_MAP.get(
                        r.get("issue_severity", "LOW").upper(), "suggestion"
                    ),
                    "confidence": r.get("issue_confidence", "").lower(),
                    "message": r.get("issue_text", ""),
                    "more_info": r.get("more_info", ""),
                }
            )

        return findings

    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# Tool schema for the Anthropic API
# ──────────────────────────────────────────────────────────────────────────────

TOOLS: list[dict] = [
    {
        "name": "run_bandit_security",
        "description": (
            "Run the Bandit security linter on a Python source string. "
            "Detects common security issues such as use of exec/eval, SQL injection risks, "
            "hardcoded passwords, insecure random number generation, dangerous subprocess calls, "
            "and more. Returns findings with severity (critical/warning/suggestion) and "
            "confidence levels."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python source code to scan for security vulnerabilities.",
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
