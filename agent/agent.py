"""
Autonomous code review agent.

Entry point:
    python -m agent.agent <github-pr-url>
    # or, after `pip install -e .`:
    review <github-pr-url>
"""

import json
import os
import sys
from typing import Any

import anthropic
from dotenv import load_dotenv

from agent.prompts import REVIEW_PROMPT, SYSTEM_PROMPT
from agent.tools import github, linter, security

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# Tool registry
# ──────────────────────────────────────────────────────────────────────────────

ALL_TOOLS: list[dict] = github.TOOLS + linter.TOOLS + security.TOOLS

TOOL_DISPATCH: dict[str, Any] = {
    "fetch_pr_details":   lambda a: github.fetch_pr_details(**a),
    "get_file_content":   lambda a: github.get_file_content(**a),
    "post_review_comment": lambda a: github.post_review_comment(**a),
    "run_ruff_linter":    lambda a: linter.run_ruff_linter(**a),
    "run_bandit_security": lambda a: security.run_bandit_security(**a),
}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _to_str(obj: Any) -> str:
    """Serialise a tool return value to a string for the API."""
    if isinstance(obj, str):
        return obj
    try:
        return json.dumps(obj, default=str, indent=2)
    except TypeError:
        return str(obj)


def _call_tool(name: str, tool_input: dict) -> str:
    handler = TOOL_DISPATCH.get(name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        return _to_str(handler(tool_input))
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": type(exc).__name__, "detail": str(exc)})


# ──────────────────────────────────────────────────────────────────────────────
# Agent loop
# ──────────────────────────────────────────────────────────────────────────────

def run_review(pr_url: str) -> str:
    """
    Run an autonomous code review on *pr_url*.

    Drives an agentic tool-use loop with Claude until it posts the review
    and returns ``end_turn``.  Returns the final assistant text.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Check your .env file.")

    client = anthropic.Anthropic(api_key=api_key)

    messages: list[dict] = [
        {"role": "user", "content": REVIEW_PROMPT.format(pr_url=pr_url)},
    ]

    print(f"Starting review for {pr_url}")

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            tools=ALL_TOOLS,      # type: ignore[arg-type]
            messages=messages,    # type: ignore[arg-type]
        )

        # Convert Pydantic ContentBlock objects → plain dicts before storing.
        # Passing the SDK model objects directly back into the next API call
        # causes a TypeError because the serialiser doesn't know how to handle them.
        messages.append({
            "role": "assistant",
            "content": [block.model_dump() for block in response.content],
        })

        if response.stop_reason == "end_turn":
            final_text = next(
                (b.text for b in response.content if hasattr(b, "text")), ""
            )
            return final_text

        if response.stop_reason != "tool_use":
            print(f"Unexpected stop_reason: {response.stop_reason!r}")
            break

        # Execute every tool call Claude requested, collect results
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"  → {block.name}({', '.join(block.input.keys())})")
            result = _call_tool(block.name, block.input)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                }
            )

        messages.append({"role": "user", "content": tool_results})

    return "Review loop ended without a final text response."


# ──────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: review <github-pr-url>")
        print("  e.g. review https://github.com/octocat/hello-world/pull/1")
        sys.exit(1)

    pr_url = sys.argv[1]
    result = run_review(pr_url)
    print("\n" + "─" * 60)
    print(result)


if __name__ == "__main__":
    main()
