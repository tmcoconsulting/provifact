"""Pinned, attribution-safe baseline metadata used by deterministic evidence."""

from evidenceops.baselines.intune import (
    INTUNE_PROVIDER_MAPPINGS,
    PROVIDER_MAPPING_REGISTRY_VERSION,
    AssignmentRequirement,
    MappingReviewStatus,
    ProviderAlias,
    ProviderRuleMapping,
    UnsupportedProviderValueError,
    matching_alias,
    normalize_provider_definition_id,
    normalize_provider_value,
    reviewed_provider_definition_ids,
    validate_provider_mapping_registry,
)
from evidenceops.baselines.mscp import (
    APPROVAL_RECORD,
    BASELINE_RULE_TITLES,
    BASELINE_RULES,
    DEMO_RULE_MAPPINGS,
    EXTRACTED_INVENTORY_SHA256,
    verify_approved_baseline,
)

__all__ = [
    "APPROVAL_RECORD",
    "AssignmentRequirement",
    "BASELINE_RULES",
    "BASELINE_RULE_TITLES",
    "DEMO_RULE_MAPPINGS",
    "EXTRACTED_INVENTORY_SHA256",
    "INTUNE_PROVIDER_MAPPINGS",
    "MappingReviewStatus",
    "PROVIDER_MAPPING_REGISTRY_VERSION",
    "ProviderAlias",
    "ProviderRuleMapping",
    "UnsupportedProviderValueError",
    "matching_alias",
    "normalize_provider_definition_id",
    "normalize_provider_value",
    "reviewed_provider_definition_ids",
    "verify_approved_baseline",
    "validate_provider_mapping_registry",
]
