"""Print only allowlisted aggregate counts from a validated public evidence package."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import cast

from evidenceops.domain import JsonValue, validate_evidence_object
from evidenceops.evidence import load_evidence_package
from evidenceops.sanitization import assert_public_safe


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    package = validate_evidence_object(load_evidence_package(args.package))
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
