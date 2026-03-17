"""GitHub tool — fetch PR metadata, file content, and post review comments via PyGitHub."""

import os
import re
from typing import Any

from dotenv import load_dotenv
from github import Auth, Github
from github.PullRequest import PullRequest
from github.Repository import Repository

load_dotenv()

_GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


def _client() -> Github:
    return Github(auth=Auth.Token(_GITHUB_TOKEN))


def _parse_pr_url(pr_url: str) -> tuple[str, int]:
    """Return (owner/repo, pr_number) from a GitHub PR URL."""
    match = re.search(r"github\.com/([^/]+/[^/]+)/pull/(\d+)", pr_url)
    if not match:
        raise ValueError(f"Not a valid GitHub PR URL: {pr_url!r}")
    return match.group(1), int(match.group(2))


# ──────────────────────────────────────────────────────────────────────────────
# Public functions used by the agent
# ──────────────────────────────────────────────────────────────────────────────

def fetch_pr_details(pr_url: str) -> dict[str, Any]:
    """
    Fetch PR metadata and the list of changed files (including diff patches).

    Returns a dict suitable for passing directly back to Claude as a tool result.
    """
    repo_name, pr_number = _parse_pr_url(pr_url)
    g = _client()
    repo: Repository = g.get_repo(repo_name)
    pr: PullRequest = repo.get_pull(pr_number)

    files = []
    for f in pr.get_files():
        files.append(
            {
                "filename": f.filename,
                "status": f.status,           # added | modified | removed | renamed
                "additions": f.additions,
                "deletions": f.deletions,
                "patch": f.patch,             # unified diff string (may be None for binary)
                "raw_url": f.raw_url,
            }
        )

    return {
        "repo": repo_name,
        "number": pr_number,
        "title": pr.title,
        "description": pr.body,
        "author": pr.user.login,
        "base_branch": pr.base.ref,
        "head_branch": pr.head.ref,
        "head_sha": pr.head.sha,
        "state": pr.state,
        "files": files,
    }


def get_file_content(repo: str, file_path: str, ref: str) -> str:
    """Download the raw content of a file at a specific commit ref."""
    g = _client()
    gh_repo: Repository = g.get_repo(repo)
    contents = gh_repo.get_contents(file_path, ref=ref)
    # contents may be a list for directories — guard against that
    if isinstance(contents, list):
        raise ValueError(f"{file_path!r} is a directory, not a file")
    return contents.decoded_content.decode("utf-8", errors="replace")


def post_review_comment(repo: str, pr_number: int, body: str) -> dict[str, Any]:
    """Post a markdown comment on a pull request."""
    g = _client()
    gh_repo: Repository = g.get_repo(repo)
    pr: PullRequest = gh_repo.get_pull(pr_number)
    comment = pr.create_issue_comment(body)
    return {"comment_id": comment.id, "url": comment.html_url}


# ──────────────────────────────────────────────────────────────────────────────
# Tool schemas for the Anthropic API
# ──────────────────────────────────────────────────────────────────────────────

TOOLS: list[dict] = [
    {
        "name": "fetch_pr_details",
        "description": (
            "Fetch metadata and changed-file list (with diff patches) for a GitHub pull request. "
            "Returns the PR title, description, author, branch names, head commit SHA, "
            "and an array of changed files each containing the unified diff patch."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pr_url": {
                    "type": "string",
                    "description": "Full GitHub PR URL, e.g. https://github.com/owner/repo/pull/42",
                }
            },
            "required": ["pr_url"],
        },
    },
    {
        "name": "get_file_content",
        "description": (
            "Download the full source of a file at a specific commit ref. "
            "Use this when you need the complete file rather than just the diff patch."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository in owner/name format, e.g. octocat/hello-world",
                },
                "file_path": {
                    "type": "string",
                    "description": "Path to the file inside the repo, e.g. src/app.py",
                },
                "ref": {
                    "type": "string",
                    "description": "Git ref (commit SHA, branch name, or tag) to fetch the file at.",
                },
            },
            "required": ["repo", "file_path", "ref"],
        },
    },
    {
        "name": "post_review_comment",
        "description": "Post a markdown-formatted review comment on a GitHub pull request.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repository in owner/name format.",
                },
                "pr_number": {
                    "type": "integer",
                    "description": "Pull request number.",
                },
                "body": {
                    "type": "string",
                    "description": "Markdown body of the review comment to post.",
                },
            },
            "required": ["repo", "pr_number", "body"],
        },
    },
]
