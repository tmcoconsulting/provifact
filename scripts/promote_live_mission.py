#!/usr/bin/env python3
"""Revalidate one scanned live Mission package before a static production build."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Final

from evidenceops.evidence import validate_public_mission_snapshot
from evidenceops.sanitization import assert_public_safe

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[1]
DEFAULT_DESTINATION: Final = REPOSITORY_ROOT / "docs/assets/data/mission-control.json"
MAX_PUBLIC_PACKAGE_BYTES: Final = 2_000_000


def promote_live_mission(source: Path, destination: Path = DEFAULT_DESTINATION) -> None:
    """Validate and atomically stage a live public Mission package."""
    if source.is_symlink() or not source.is_file():
        raise ValueError("live Mission source must be one regular file")
    if source.stat().st_size > MAX_PUBLIC_PACKAGE_BYTES:
        raise ValueError("live Mission source exceeds the public package limit")
    try:
        loaded = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("live Mission source could not be read") from exc
    mission = validate_public_mission_snapshot(loaded)
    assert_public_safe(mission)
    if mission["data_mode"] != "LIVE SANITIZED TENANT DATA":
        raise ValueError("publication handoff must contain live sanitized tenant data")
    if destination.is_symlink():
        raise ValueError("live Mission destination must not be a symlink")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    if temporary.exists() or temporary.is_symlink():
        raise ValueError("live Mission temporary destination already exists")
    try:
        temporary.write_text(
            json.dumps(mission, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args(argv)
    promote_live_mission(args.source, args.destination)
    print("live sanitized Mission package staged for static build")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
