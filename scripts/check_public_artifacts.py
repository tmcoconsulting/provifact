#!/usr/bin/env python3
"""Fail closed when generated public output contains prohibited identity markers."""

import argparse
import re
import sys
from collections.abc import Iterator
from html.parser import HTMLParser
from pathlib import Path
from typing import Final

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

from evidenceops.sanitization.credentials import CREDENTIAL_PATTERNS  # noqa: E402

_HIGH_CONFIDENCE_PATTERNS: Final = (
    ("raw fixture marker", re.compile(r"RAW_FIXTURE_MARKER")),
    ("synthetic raw serial marker", re.compile(r"SYNTH-SERIAL")),
    ("reserved fixture domain", re.compile(r"example\.invalid", re.IGNORECASE)),
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
_PROHIBITED_PATH_PARTS: Final = {"artifacts", "exports", "private", "raw"}
_PUBLIC_IDENTIFIER_ALLOWLIST: Final = {
    # Microsoft Graph public permission identifiers documented in the checked-in manifest.
    "dc377aa6-52d8-4e23-b271-2a7ae04cedf3",
    "f1493658-876a-4c87-8fa7-edb559b3476a",
}


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
        if any(part.lower() in _PROHIBITED_PATH_PARTS for part in relative.parts):
            findings.append((relative, 1, "private-evidence path"))
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in (*CREDENTIAL_PATTERNS, *_HIGH_CONFIDENCE_PATTERNS):
            for match in pattern.finditer(content):
                line = content.count("\n", 0, match.start()) + 1
                findings.append((relative, line, label))

        public_content = _public_content(relative, content)
        if public_content is None:
            continue
        for label, pattern in _PUBLIC_CONTENT_PATTERNS:
            for match in pattern.finditer(public_content):
                if (
                    label == "UUID-like identifier"
                    and match.group(0) in _PUBLIC_IDENTIFIER_ALLOWLIST
                ):
                    continue
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
