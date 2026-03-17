"""AST analysis tool — detects structural issues in Python code without running it."""

import ast
from dataclasses import dataclass


@dataclass
class ASTIssue:
    line: int
    message: str
    category: str


class _Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.issues: list[ASTIssue] = []

    # ---- helpers ----
    def _issue(self, node: ast.AST, message: str, category: str) -> None:
        self.issues.append(ASTIssue(line=getattr(node, "lineno", 0), message=message, category=category))

    # ---- checks ----
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Flag functions that are too long
        if hasattr(node, "end_lineno") and node.end_lineno - node.lineno > 60:
            self._issue(node, f"Function '{node.name}' is {node.end_lineno - node.lineno} lines long (>60)", "complexity")

        # Flag missing docstrings on public functions
        if not node.name.startswith("_"):
            if not (node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)):
                self._issue(node, f"Public function '{node.name}' is missing a docstring", "documentation")

        # Flag bare except clauses
        for child in ast.walk(node):
            if isinstance(child, ast.ExceptHandler) and child.type is None:
                self._issue(child, "Bare 'except:' clause catches all exceptions including SystemExit", "error-handling")

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Flag missing class docstring
        if not (node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)):
            self._issue(node, f"Class '{node.name}' is missing a docstring", "documentation")
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        self._issue(node, "Use of 'assert' in non-test code is stripped by Python -O", "reliability")
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        self._issue(node, f"Use of 'global' statement for: {', '.join(node.names)}", "design")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Detect print() left in production code
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self._issue(node, "Leftover 'print()' call — use logging instead", "style")
        self.generic_visit(node)


def analyze_python(code: str, filename: str = "review_target.py") -> list[dict]:
    """Parse Python source and return structural issues as a list of dicts."""
    try:
        tree = ast.parse(code, filename=filename)
    except SyntaxError as exc:
        return [
            {
                "file": filename,
                "line": exc.lineno or 0,
                "message": f"Syntax error: {exc.msg}",
                "category": "syntax",
            }
        ]

    visitor = _Visitor()
    visitor.visit(tree)

    return [
        {
            "file": filename,
            "line": issue.line,
            "message": issue.message,
            "category": issue.category,
        }
        for issue in visitor.issues
    ]


# ---------------------------------------------------------------------------
# Tool definitions for Claude tool use
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "analyze_python_ast",
        "description": (
            "Perform AST-level static analysis on a Python source string. "
            "Detects structural issues like missing docstrings, bare except clauses, "
            "overly long functions, assert usage, global statements, and leftover print calls. "
            "Does not execute the code."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python source code to analyze."},
                "filename": {
                    "type": "string",
                    "description": "Filename for display purposes (default: review_target.py).",
                },
            },
            "required": ["code"],
        },
    },
]
