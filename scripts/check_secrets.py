#!/usr/bin/env python3
"""Fail when a workspace file contains a high-confidence credential pattern."""

import argparse
import re
import shutil
import subprocess  # nosec B404
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Final

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

from evidenceops.sanitization.credentials import CREDENTIAL_PATTERNS  # noqa: E402

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
_PROHIBITED_TRACKED_PARTS: Final = {"artifacts", "exports", "private", "raw", "site"}
_PROHIBITED_TRACKED_SUFFIXES: Final = {".cer", ".crt", ".key", ".p12", ".pem", ".pfx"}

_REPOSITORY_ONLY_PATTERNS: Final = (
    (
        "non-empty secret environment assignment",
        re.compile(
            r"^(?:OPENAI_API_KEY|AZURE_CLIENT_SECRET|AZURE_TENANT_ID|AZURE_CLIENT_ID|"
            r"EVIDENCEOPS_GRAPH_ACCESS_TOKEN|EVIDENCEOPS_PSEUDONYM_KEY)="
            r"[^\s#][^\s]*$",
            re.MULTILINE,
        ),
    ),
)


def _iter_files(root: Path) -> Iterator[Path]:
    git_executable = shutil.which("git")
    if git_executable is not None:
        result = subprocess.run(  # noqa: S603  # nosec B603
            [git_executable, "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if result.returncode == 0:
            for encoded in result.stdout.split(b"\0"):
                if not encoded:
                    continue
                path = root / encoded.decode("utf-8")
                if path.is_file() and path.stat().st_size <= 2_000_000:
                    yield path
            return
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
        relative = path.relative_to(root)
        lowered_parts = {part.lower() for part in relative.parts}
        if (
            lowered_parts.intersection(_PROHIBITED_TRACKED_PARTS)
            or path.suffix.lower() in _PROHIBITED_TRACKED_SUFFIXES
            or (path.name == ".env" or path.name.startswith(".env."))
            and path.name != ".env.example"
        ):
            findings.append((relative, 1, "prohibited private artifact path"))
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in (*CREDENTIAL_PATTERNS, *_REPOSITORY_ONLY_PATTERNS):
            for match in pattern.finditer(content):
                line = content.count("\n", 0, match.start()) + 1
                findings.append((relative, line, label))
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
