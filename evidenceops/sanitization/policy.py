"""Explicit field classification and deterministic pseudonymization.

The sanitizer is deliberately strict: every mapping key must be classified. New provider
fields therefore stop publication until a human decides whether to allow, drop, or
pseudonymize them.
"""

import hashlib
import hmac
import re
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from evidenceops.domain import JsonValue


class SanitizationError(ValueError):
    """Base class for publication-blocking sanitization errors."""


class UnknownFieldError(SanitizationError):
    """Raised when an input field has not been explicitly classified."""


class SensitiveValueError(SanitizationError):
    """Raised when a prohibited value survives field transformation."""


class FieldAction(StrEnum):
    """Allowed transformations for a classified input field."""

    ALLOW = "allow"
    DROP = "drop"
    PSEUDONYMIZE = "pseudonymize"


@dataclass(frozen=True, slots=True)
class SanitizationPolicy:
    """A complete field-action map and pseudonym namespace map."""

    actions: dict[str, FieldAction]
    pseudonym_prefixes: dict[str, str]


_ALLOWED_FIELDS: Final = {
    "schema_version",
    "fixture_notice",
    "provider",
    "platform",
    "control_id",
    "title",
    "description",
    "baseline",
    "observations",
    "devices",
    "settings",
    "assignments",
    "desired_value",
    "observed_value",
    "status",
    "severity",
    "source_type",
    "collected_at",
    "synthetic",
    "os_version",
    "compliance_state",
    "value",
}

_PSEUDONYM_FIELDS: Final = {
    "tenant_id": "tenant",
    "subscription_id": "subscription",
    "application_id": "application",
    "service_principal_id": "service-principal",
    "user_principal_name": "user",
    "email": "user",
    "personal_name": "person",
    "device_name": "device",
    "serial_number": "serial",
    "imei": "imei",
    "meid": "meid",
    "hardware_id": "hardware",
    "entra_object_id": "entra-object",
    "managed_device_id": "managed-device",
    "group_id": "group",
    "group_name": "group-name",
    "ip_address": "network-address",
    "internal_domain": "internal-domain",
    "correlation_id": "correlation",
}

_DROP_FIELDS: Final = {
    "access_token",
    "refresh_token",
    "client_secret",
    "private_key",
    "certificate",
    "authorization",
}

_actions = dict.fromkeys(_ALLOWED_FIELDS, FieldAction.ALLOW)
_actions.update(dict.fromkeys(_PSEUDONYM_FIELDS, FieldAction.PSEUDONYMIZE))
_actions.update(dict.fromkeys(_DROP_FIELDS, FieldAction.DROP))

DEFAULT_PUBLIC_POLICY: Final = SanitizationPolicy(
    actions=dict(MappingProxyType(_actions)),
    pseudonym_prefixes=dict(MappingProxyType(_PSEUDONYM_FIELDS)),
)

_PROHIBITED_OUTPUT_PATTERNS: Final = (
    ("email address", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    ("IP address", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    (
        "UUID-like identifier",
        re.compile(
            r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b",
            re.IGNORECASE,
        ),
    ),
    ("private-key material", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("bearer authorization", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]+=*", re.IGNORECASE)),
)


def sanitize_document(
    document: dict[str, JsonValue],
    *,
    pseudonym_key: bytes,
    policy: SanitizationPolicy = DEFAULT_PUBLIC_POLICY,
) -> dict[str, JsonValue]:
    """Return a public-safe copy or raise before producing an artifact.

    The caller supplies pseudonym key material at runtime. A key shorter than 32 bytes is
    rejected, and EvidenceOps never persists it.
    """
    if len(pseudonym_key) < 32:
        raise SanitizationError("pseudonym_key must contain at least 32 bytes")
    sanitized = _sanitize_mapping(document, policy=policy, pseudonym_key=pseudonym_key)
    _assert_public_safe(sanitized)
    return sanitized


def _sanitize_mapping(
    value: dict[str, JsonValue],
    *,
    policy: SanitizationPolicy,
    pseudonym_key: bytes,
) -> dict[str, JsonValue]:
    result: dict[str, JsonValue] = {}
    for field, item in value.items():
        try:
            action = policy.actions[field]
        except KeyError as exc:
            raise UnknownFieldError(f"unclassified field: {field}") from exc

        if action is FieldAction.DROP:
            continue
        if action is FieldAction.PSEUDONYMIZE:
            if not isinstance(item, str) or not item:
                raise SanitizationError(f"field {field} requires a non-empty string")
            prefix = policy.pseudonym_prefixes[field]
            result[field] = _pseudonymize(prefix, item, pseudonym_key)
            continue
        result[field] = _sanitize_allowed_value(
            item,
            policy=policy,
            pseudonym_key=pseudonym_key,
        )
    return result


def _sanitize_allowed_value(
    value: JsonValue,
    *,
    policy: SanitizationPolicy,
    pseudonym_key: bytes,
) -> JsonValue:
    if isinstance(value, dict):
        return _sanitize_mapping(value, policy=policy, pseudonym_key=pseudonym_key)
    if isinstance(value, list):
        return [
            _sanitize_allowed_value(item, policy=policy, pseudonym_key=pseudonym_key)
            for item in value
        ]
    return value


def _pseudonymize(prefix: str, value: str, key: bytes) -> str:
    digest = hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()[:20]
    return f"{prefix}-{digest}"


def _assert_public_safe(value: JsonValue) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _assert_public_safe(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_public_safe(item)
        return
    if not isinstance(value, str):
        return
    for label, pattern in _PROHIBITED_OUTPUT_PATTERNS:
        if pattern.search(value):
            raise SensitiveValueError(f"prohibited {label} survived sanitization")
