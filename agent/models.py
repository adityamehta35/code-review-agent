from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    SUGGESTION = "suggestion"


class ReviewComment(BaseModel):
    severity: Severity
    category: str          # e.g. "lint", "security", "style", "logic"
    file: Optional[str] = None
    line: Optional[int] = None
    message: str
    suggestion: Optional[str] = None


class ReviewResult(BaseModel):
    summary: str
    comments: list[ReviewComment]
    verdict: str           # "approved" | "changes_requested"

    # ------------------------------------------------------------------ #
    # Counts                                                               #
    # ------------------------------------------------------------------ #

    @property
    def critical_count(self) -> int:
        return sum(1 for c in self.comments if c.severity == Severity.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for c in self.comments if c.severity == Severity.WARNING)

    # ------------------------------------------------------------------ #
    # Markdown rendering                                                   #
    # ------------------------------------------------------------------ #

    def as_markdown(self) -> str:
        lines: list[str] = ["## 🤖 Automated Code Review\n"]
        lines.append(f"{self.summary}\n")
        lines.append(
            f"**Findings:** {self.critical_count} critical · "
            f"{self.warning_count} warning · "
            f"{len(self.comments) - self.critical_count - self.warning_count} suggestion\n"
        )

        icons = {
            Severity.CRITICAL: "🔴",
            Severity.WARNING: "🟡",
            Severity.SUGGESTION: "🔵",
        }

        by_severity = {s: [] for s in Severity}
        for comment in self.comments:
            by_severity[comment.severity].append(comment)

        for severity in Severity:
            bucket = by_severity[severity]
            if not bucket:
                continue
            lines.append(f"\n### {icons[severity]} {severity.value.title()}\n")
            for c in bucket:
                loc = ""
                if c.file:
                    loc = f"`{c.file}`"
                    if c.line:
                        loc += f" line {c.line}"
                    loc = f" — {loc}"
                lines.append(f"- **[{c.category}]**{loc}: {c.message}")
                if c.suggestion:
                    lines.append(f"  > 💡 {c.suggestion}")

        verdict_icon = "✅ Approved" if self.verdict == "approved" else "❌ Changes Requested"
        lines.append(f"\n**Verdict:** {verdict_icon}")
        return "\n".join(lines)
