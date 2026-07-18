#!/usr/bin/env python3
"""Fail closed when generated public output contains prohibited identity markers."""

import argparse
import re
from collections.abc import Iterator
from html.parser import HTMLParser
from pathlib import Path
from typing import Final

_HIGH_CONFIDENCE_PATTERNS: Final = (
    ("raw fixture marker", re.compile(r"RAW_FIXTURE_MARKER")),
    ("synthetic raw serial marker", re.compile(r"SYNTH-SERIAL")),
    ("reserved fixture domain", re.compile(r"example\.invalid", re.IGNORECASE)),
    ("private key", re.compile(r"-----BEGIN " r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    (
        "GitHub token",
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    ),
    ("bearer credential", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{20,}=*", re.IGNORECASE)),
)

_PUBLIC_CONTENT_PATTERNS: Final = (
    ("email address", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    (
        "UUID-like identifier",
        re.compile(
            r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b",
            re.IGNORECASE,
        ),
    ),
    (
        "IP address",
        re.compile(
            r"(?<![\d.])(?:25[0-5]|2[0-4]\d|1?\d?\d)"
            r"(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?![\d.])"
        ),
    ),
)

_NON_CONTENT_ASSET_DIRS: Final = {"javascripts", "stylesheets", "webfonts"}


class _VisibleTextParser(HTMLParser):
    """Extract user-visible text while excluding theme scripts, styles, and SVG paths."""

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag in {"script", "style", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        return "\n".join(self.parts)


def _iter_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.stat().st_size <= 2_000_000:
            yield path


def scan(root: Path) -> list[tuple[Path, int, str]]:
    findings: list[tuple[Path, int, str]] = []
    for path in _iter_files(root):
        relative = path.relative_to(root)
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in _HIGH_CONFIDENCE_PATTERNS:
            for match in pattern.finditer(content):
                line = content.count("\n", 0, match.start()) + 1
                findings.append((relative, line, label))

        public_content = _public_content(relative, content)
        if public_content is None:
            continue
        for label, pattern in _PUBLIC_CONTENT_PATTERNS:
            for match in pattern.finditer(public_content):
                line = public_content.count("\n", 0, match.start()) + 1
                findings.append((relative, line, label))
    return findings


def _public_content(relative: Path, content: str) -> str | None:
    if relative.suffix == ".html":
        parser = _VisibleTextParser()
        parser.feed(content)
        return parser.text()
    if relative.parts[:2] == ("assets", "data"):
        return content
    if any(part in _NON_CONTENT_ASSET_DIRS for part in relative.parts):
        return None
    if relative == Path("search/search_index.json"):
        return None
    if relative.suffix in {".json", ".txt", ".xml"}:
        return content
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path("site"))
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        parser.error(f"public artifact directory does not exist: {root}")
    findings = scan(root)
    if findings:
        for path, line, label in findings:
            print(f"{path}:{line}: prohibited {label}")
        return 1
    print("public artifact scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
