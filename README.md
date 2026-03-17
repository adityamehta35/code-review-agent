# 🔍 Code Review Agent

> An autonomous AI agent that reviews GitHub pull requests like a senior engineer — fetching diffs, running static analysis, scanning for security issues, and posting a structured review comment, all without human intervention.

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Anthropic](https://img.shields.io/badge/Claude-Opus_4.5-D97757?style=flat&logo=anthropic&logoColor=white)](https://anthropic.com)
[![Ruff](https://img.shields.io/badge/Linter-Ruff-D7FF64?style=flat&logo=ruff&logoColor=black)](https://docs.astral.sh/ruff)
[![Bandit](https://img.shields.io/badge/Security-Bandit-326CE5?style=flat&logo=python&logoColor=white)](https://bandit.readthedocs.io)
[![PyGitHub](https://img.shields.io/badge/GitHub_API-PyGitHub-181717?style=flat&logo=github&logoColor=white)](https://pygithub.readthedocs.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What It Does

Give it a GitHub PR URL. It handles the rest.

The agent reads every changed file, lints the Python code with Ruff, scans for security vulnerabilities with Bandit, applies its own expert analysis, and posts a structured review comment directly on the pull request — complete with severity levels, file locations, and actionable suggestions.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI / GitHub Actions                      │
│                    review <github-pr-url>                        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         agent/agent.py                           │
│                      Agentic Loop (Claude)                       │
│                                                                  │
│   ┌─────────────┐     tool_use      ┌──────────────────────┐   │
│   │             │ ◄───────────────► │   Tool Dispatcher    │   │
│   │  Claude     │                   │                      │   │
│   │  Opus 4.5   │   tool_result     │  fetch_pr_details    │   │
│   │             │ ◄───────────────  │  get_file_content    │   │
│   │  (Anthropic │                   │  run_ruff_linter     │   │
│   │   Messages  │   end_turn        │  run_bandit_security │   │
│   │   API)      │ ─────────────►    │  post_review_comment │   │
│   └─────────────┘                   └──────────┬───────────┘   │
└──────────────────────────────────────────────  │  ─────────────┘
                                                 │
              ┌──────────────────────────────────┼────────────────┐
              │                                  │                │
              ▼                                  ▼                ▼
  ┌───────────────────┐             ┌────────────────┐  ┌────────────────┐
  │  GitHub API       │             │  Ruff (subprocess)│  │Bandit(subprocess)│
  │  (PyGitHub)       │             │                │  │                │
  │                   │             │  Lints Python  │  │  Scans Python  │
  │  • PR metadata    │             │  files against │  │  for security  │
  │  • File diffs     │             │  300+ rules    │  │  vulnerabilities│
  │  • File content   │             │                │  │                │
  │  • Post comment   │             └────────────────┘  └────────────────┘
  └───────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| AI Model | Claude Opus 4.5 (Anthropic) | Reasoning, synthesis, review generation |
| GitHub Integration | PyGitHub | PR metadata, diffs, posting comments |
| Linting | Ruff | Fast Python style and correctness checks |
| Security Scanning | Bandit | Python security vulnerability detection |
| Data Validation | Pydantic v2 | Typed models for review results |
| Config | python-dotenv | `.env` file loading |
| CI/CD | GitHub Actions | Automatic trigger on PR open/update |

---

## Setup

### Prerequisites

- Python 3.12+
- An [Anthropic API key](https://console.anthropic.com/settings/keys)
- A [GitHub personal access token](https://github.com/settings/tokens) with `repo` and `pull_requests` scopes

### 1. Clone the repository

```bash
git clone https://github.com/your-username/code-review-agent.git
cd code-review-agent
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:

```env
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=github_pat_...
```

### 3. Install dependencies

```bash
pip install -e .
```

This installs the `review` CLI command along with all dependencies (Anthropic SDK, PyGitHub, Ruff, Bandit, Pydantic, python-dotenv).

### 4. Run a review

```bash
review https://github.com/owner/repo/pull/42
```

Or via Python directly:

```bash
python -m agent.agent https://github.com/owner/repo/pull/42
```

---

## Example Output

Running `review https://github.com/octocat/linguist/pull/4` produces console output like:

```
Starting review for https://github.com/octocat/linguist/pull/4
  → fetch_pr_details(pr_url)
  → get_file_content(repo, file_path, ref)
  → run_ruff_linter(code, filename)
  → run_bandit_security(code, filename)
  → post_review_comment(repo, pr_number, body)

────────────────────────────────────────────────────────────────
Review posted successfully.
```

And the following comment appears on the pull request:

---

## 🤖 Automated Code Review

This PR adds a new `DatabaseManager` class and refactors the authentication flow. The changes are generally well-structured, but there are several issues that should be addressed before merging.

**Findings:** 2 critical · 3 warning · 4 suggestion

### 🔴 Critical

- **[security]** — `lib/db.py` line 47: Use of `subprocess` with `shell=True` is a command injection risk
  > 💡 Pass arguments as a list instead: `subprocess.run(["pg_dump", db_name], check=True)`

- **[security]** — `lib/auth.py` line 12: Hardcoded secret key detected — `SECRET_KEY = "dev-secret-abc123"`
  > 💡 Load from environment: `SECRET_KEY = os.environ["SECRET_KEY"]`

### 🟡 Warning

- **[lint]** — `lib/db.py` line 23: F841 — local variable `conn` is assigned but never used
  > 💡 Remove the assignment or use `_` if intentional

- **[lint]** — `lib/auth.py` line 88: E501 — line too long (134 > 100 characters)

- **[logic]** — `lib/db.py` line 71: `except Exception` swallows all errors including `KeyboardInterrupt` — catch specific exceptions instead

### 🔵 Suggestion

- **[style]** — `lib/db.py` line 5: Missing type annotations on public method `connect()`
- **[style]** — `lib/auth.py` line 34: Docstring missing from public class `TokenValidator`
- **[tests]** — No test files were modified. The new `DatabaseManager` class has no visible test coverage
- **[style]** — `lib/db.py` line 102: Consider using a context manager (`with`) for database connection cleanup

**Verdict:** ❌ Changes Requested

---

## How It Works

The agent runs a **tool-use loop** against the Anthropic Messages API. Claude autonomously decides which tools to call, in what order, and when it has enough information to write the review.

```
1. User provides a PR URL
         │
         ▼
2. Claude reads the prompt and calls fetch_pr_details
   → Returns: PR title, author, list of changed files with unified diffs
         │
         ▼
3. For each changed Python file, Claude calls:
   a. get_file_content   → full source for deeper context
   b. run_ruff_linter    → style, import, and correctness issues (300+ rules)
   c. run_bandit_security → security vulnerabilities (CWE-mapped findings)
         │
         ▼
4. Claude synthesises all tool results with its own reading of the diff:
   - Correlates linter codes with the actual change
   - Weighs severity based on context (a bare except in a retry loop
     is worse than in a CLI script)
   - Adds findings Ruff/Bandit can't catch: logic errors, missing tests,
     architectural concerns
         │
         ▼
5. Claude calls post_review_comment with a formatted markdown body
   → Comment appears on the GitHub PR
         │
         ▼
6. Claude returns end_turn — loop exits
```

### The agentic loop in code

```python
while True:
    response = client.messages.create(
        model="claude-opus-4-5",
        tools=ALL_TOOLS,
        messages=messages,
    )

    # Convert Pydantic ContentBlocks → plain dicts for next iteration
    messages.append({
        "role": "assistant",
        "content": [block.model_dump() for block in response.content],
    })

    if response.stop_reason == "end_turn":
        return final_text          # Claude is done

    # Execute whichever tools Claude requested, feed results back
    tool_results = [call_tool(block) for block in response.content
                    if block.type == "tool_use"]
    messages.append({"role": "user", "content": tool_results})
    # → loop continues
```

Claude never sees the raw GitHub API or subprocess calls — it only sees the tool results returned as structured data. This keeps the model focused on reasoning rather than plumbing.

---

## GitHub Actions Integration

The included workflow (`.github/workflows/review.yml`) triggers the agent automatically on every pull request:

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
```

Add your secrets to the repository (**Settings → Secrets → Actions**):

| Secret | Value |
|--------|-------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `GITHUB_TOKEN` | Automatically provided by GitHub Actions |

No further configuration needed — every new PR will receive an automated review within ~30 seconds.

---

## Project Structure

```
code-review-agent/
├── agent/
│   ├── agent.py          # Agentic loop — drives Claude with tool use
│   ├── models.py         # Pydantic models: ReviewComment, ReviewResult, Severity
│   ├── prompts.py        # System prompt and review prompt template
│   └── tools/
│       ├── github.py     # PyGitHub: fetch PR info, post comments
│       ├── linter.py     # Ruff: Python style and correctness
│       └── security.py   # Bandit: security vulnerability scanning
├── .github/
│   └── workflows/
│       └── review.yml    # GitHub Actions trigger
├── .env.example          # Environment variable template
├── config.toml           # Agent configuration
└── pyproject.toml        # Dependencies and CLI entry point
```

---

## Future Improvements

- **Multi-language support** — Add ESLint for JavaScript/TypeScript and golangci-lint for Go files in the same PR
- **Inline review comments** — Use the GitHub [pull request review API](https://docs.github.com/en/rest/pulls/reviews) to post comments directly on specific diff lines rather than a single top-level comment
- **Caching** — Cache Ruff and Bandit results per file SHA so re-runs on `synchronize` events don't re-analyse unchanged files
- **Configurable severity thresholds** — Let teams set a minimum severity to post a review (e.g. ignore suggestions in fast-moving repos)
- **PR description awareness** — Give Claude the linked Jira/Linear ticket or RFC document for richer context about *intent*, not just implementation
- **Suggested code fixes** — Use the GitHub [suggestions API](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/commenting-on-a-pull-request#adding-line-comments-to-a-pull-request) to embed one-click-apply code fixes directly in the review
- **Review memory** — Persist past reviews per repository so the agent can detect recurring issues and flag repeat offenders
- **Test coverage integration** — Pipe in `coverage.py` reports to flag new code paths that lack test coverage

---

## License

MIT — see [LICENSE](LICENSE).
