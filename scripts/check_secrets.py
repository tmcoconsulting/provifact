#!/usr/bin/env python3
"""Fail when a workspace file contains a high-confidence credential pattern."""

import argparse
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Final

_EXCLUDED_PARTS: Final = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "htmlcov",
    "site",
}

_PATTERNS: Final = (
    (
        "private key",
        re.compile(r"-----BEGIN " r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    (
        "GitHub token",
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    ),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("bearer credential", re.compile(r"authorization\s*[:=]\s*bearer\s+\S+", re.IGNORECASE)),
    (
        "non-empty secret environment assignment",
        re.compile(
            r"^(?:OPENAI_API_KEY|AZURE_CLIENT_SECRET|EVIDENCEOPS_PSEUDONYM_KEY)="
            r"[^\s#][^\s]*$",
            re.MULTILINE,
        ),
    ),
)


def _iter_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in _EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.stat().st_size > 2_000_000:
            continue
        yield path


def scan(root: Path) -> list[tuple[Path, int, str]]:
    """Return locations and labels only; never echo a possible secret value."""
    findings: list[tuple[Path, int, str]] = []
    for path in _iter_files(root):
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in _PATTERNS:
            for match in pattern.finditer(content):
                line = content.count("\n", 0, match.start()) + 1
                findings.append((path.relative_to(root), line, label))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args()
    findings = scan(args.root.resolve())
    if findings:
        for path, line, label in findings:
            print(f"{path}:{line}: prohibited {label}")
        return 1
    print("secret scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
