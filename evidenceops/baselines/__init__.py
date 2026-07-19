"""Pinned, attribution-safe baseline metadata used by deterministic evidence."""

from evidenceops.baselines.mscp import (
    APPROVAL_RECORD,
    BASELINE_RULES,
    DEMO_RULE_MAPPINGS,
    EXTRACTED_INVENTORY_SHA256,
    verify_approved_baseline,
)

__all__ = [
    "APPROVAL_RECORD",
    "BASELINE_RULES",
    "DEMO_RULE_MAPPINGS",
    "EXTRACTED_INVENTORY_SHA256",
    "verify_approved_baseline",
]
