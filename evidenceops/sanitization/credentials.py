"""Shared high-confidence credential signatures for every repository egress gate."""

from __future__ import annotations

import json
import re
from pathlib import Path
from re import Pattern
from typing import Final

CredentialPattern = tuple[str, Pattern[str]]
_CATALOG_PATH: Final = Path(__file__).with_name("credential-patterns.v1.json")


def _load_catalog(path: Path) -> tuple[str, tuple[CredentialPattern, ...]]:
    """Load the cross-runtime catalog or stop every dependent egress gate."""
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("credential pattern catalog could not be loaded") from exc
    if not isinstance(loaded, dict) or set(loaded) != {"catalog_version", "patterns"}:
        raise RuntimeError("credential pattern catalog has unexpected or missing fields")
    version = loaded.get("catalog_version")
    patterns = loaded.get("patterns")
    if not isinstance(version, str) or not version or not isinstance(patterns, list):
        raise RuntimeError("credential pattern catalog metadata is invalid")
    compiled: list[CredentialPattern] = []
    for entry in patterns:
        if not isinstance(entry, dict) or set(entry) != {"label", "expression", "flags"}:
            raise RuntimeError("credential pattern entry has unexpected or missing fields")
        label = entry.get("label")
        expression = entry.get("expression")
        flags = entry.get("flags")
        if (
            not isinstance(label, str)
            or not label
            or not isinstance(expression, str)
            or not expression
            or flags not in {"", "i"}
        ):
            raise RuntimeError("credential pattern entry is invalid")
        compiled.append((label, re.compile(expression, re.IGNORECASE if flags == "i" else 0)))
    if not compiled:
        raise RuntimeError("credential pattern catalog must not be empty")
    return version, tuple(compiled)


# Publication, repository scanning, generated-site scanning, and both Python and Worker
# pre-model egress load this exact machine-readable catalog.
CREDENTIAL_PATTERN_CATALOG_VERSION, CREDENTIAL_PATTERNS = _load_catalog(_CATALOG_PATH)
