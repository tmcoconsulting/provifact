"""Print only allowlisted aggregate counts from a validated public evidence package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

from evidenceops.domain import JsonValue, validate_evidence_object
from evidenceops.evidence import MISSION_SCHEMA_VERSION, validate_public_mission_snapshot
from evidenceops.sanitization import assert_public_safe


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args(argv)
    loaded = json.loads(args.package.read_text(encoding="utf-8"))
    if isinstance(loaded, dict) and loaded.get("schema_version") == MISSION_SCHEMA_VERSION:
        package = validate_public_mission_snapshot(loaded)
        assert_public_safe(package)
        metrics = cast(dict[str, JsonValue], package["metrics"])
        print("## Sanitized Apple validation")
        print(f"- data mode: {package['data_mode']}")
        for field in (
            "baseline_rule_count",
            "alignment_denominator",
            "aligned_requirements",
            "drifted_requirements",
            "policies_evaluated",
            "collection_gaps",
            "unmapped_objects",
        ):
            print(f"- {field.replace('_', ' ')}: {metrics[field]}")
        print("- raw or private evidence retained: no")
        print("- human review required: yes")
        return 0
    package = validate_evidence_object(loaded)
    if package["object_type"] != "sanitized_public_evidence_package":
        parser.error("package must be sanitized public evidence")
    assert_public_safe(package)
    print("## Sanitized live validation")
    for field in ("desired_state", "observations", "findings", "evidence_references"):
        values = cast(list[JsonValue], package[field])
        print(f"- {field.replace('_', ' ')}: {len(values)}")
    print("- raw or private evidence retained: no")
    print("- human review required: yes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
