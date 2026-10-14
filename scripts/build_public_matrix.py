"""Stage the canonical public matrix for a validated Mission snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evidenceops.evidence.matrix import build_public_matrix
from evidenceops.evidence.mission import load_public_mission_snapshot


def write_matrix(source: Path, output: Path) -> None:
    """Construct from a bounded public input; never accept a private envelope."""
    matrix = build_public_matrix(load_public_mission_snapshot(source))
    if output.is_symlink():
        raise ValueError("matrix output must not be a symlink")
    if source.resolve() == output.resolve():
        raise ValueError("matrix output must not replace its Mission source")
    temporary = output.with_suffix(output.suffix + ".tmp")
    if temporary.exists() or temporary.is_symlink():
        raise ValueError("matrix temporary output already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        temporary.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mission", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_matrix(args.mission, args.output)
    print("canonical public matrix staged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
