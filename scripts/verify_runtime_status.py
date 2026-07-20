#!/usr/bin/env python3
"""Validate the public-safe production status response after deployment."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Final

from evidenceops.sanitization import assert_public_safe

ALLOWED_DATA_MODES: Final = {
    "SYNTHETIC DEMO DATA",
    "LIVE SANITIZED TENANT DATA",
    "DEGRADED OR STALE DATA",
}
ALLOWED_NARRATIVE_MODES: Final = {"fixture", "openai"}
STATUS_FIELDS: Final = frozenset(
    {
        "schema_version",
        "service",
        "status",
        "narrative_mode",
        "model",
        "model_configured",
        "narrative_available",
        "public_data_boundary",
        "human_review_required",
        "data_mode",
        "evidence_timestamp",
        "source_snapshot_id",
        "live_intune_collection_performed",
        "intune_write_capability",
        "byok_supported",
        "assistant_endpoint",
    }
)


def verify_runtime_status(
    value: object,
    *,
    expected_data_mode: str,
    expected_narrative_mode: str,
    expected_source_snapshot_id: str,
) -> None:
    """Fail unless the status exactly reflects the reviewed deployment mode."""
    if expected_data_mode not in ALLOWED_DATA_MODES:
        raise ValueError("unsupported expected data mode")
    if expected_narrative_mode not in ALLOWED_NARRATIVE_MODES:
        raise ValueError("unsupported expected narrative mode")
    if not re.fullmatch(r"mission-[0-9a-f]{24}", expected_source_snapshot_id):
        raise ValueError("invalid expected source snapshot ID")
    if not isinstance(value, dict):
        raise ValueError("runtime status must be an object")
    assert_public_safe(value)
    if set(value) != STATUS_FIELDS:
        raise ValueError("runtime status has an unknown field or is incomplete")
    expected = {
        "schema_version": "1.0.0",
        "service": "Provifact narrative boundary",
        "status": "ok",
        "narrative_mode": expected_narrative_mode,
        "model": "gpt-5.6-terra",
        "model_configured": True,
        "narrative_available": True,
        "public_data_boundary": "synthetic-or-fail-closed-sanitized-only",
        "human_review_required": True,
        "data_mode": expected_data_mode,
        "live_intune_collection_performed": expected_data_mode == "LIVE SANITIZED TENANT DATA",
        "intune_write_capability": False,
        "byok_supported": False,
        "assistant_endpoint": "/api/ask",
    }
    for field, item in expected.items():
        if value.get(field) != item:
            raise ValueError(f"runtime status field {field} does not match deployment policy")
    for field in ("evidence_timestamp", "source_snapshot_id"):
        if not isinstance(value.get(field), str) or not value[field]:
            raise ValueError(f"runtime status field {field} is missing")
    if value["source_snapshot_id"] != expected_source_snapshot_id:
        raise ValueError("runtime status source snapshot does not match the reviewed package")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("status", type=Path)
    parser.add_argument("--expected-data-mode", required=True)
    parser.add_argument("--expected-narrative-mode", required=True)
    parser.add_argument("--expected-source-snapshot-id", required=True)
    args = parser.parse_args(argv)
    try:
        loaded = json.loads(args.status.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("runtime status could not be read") from exc
    verify_runtime_status(
        loaded,
        expected_data_mode=args.expected_data_mode,
        expected_narrative_mode=args.expected_narrative_mode,
        expected_source_snapshot_id=args.expected_source_snapshot_id,
    )
    print("production runtime status matches deployment policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
