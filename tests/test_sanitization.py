import json
import secrets
from pathlib import Path
from typing import cast

import pytest

from evidenceops.domain import JsonValue
from evidenceops.sanitization import (
    SanitizationError,
    SensitiveValueError,
    UnknownFieldError,
    sanitize_document,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "synthetic"


def _load_fixture(name: str) -> dict[str, JsonValue]:
    loaded = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return cast(dict[str, JsonValue], loaded)


def test_sensitive_fields_are_transformed_or_removed() -> None:
    source = _load_fixture("managed-devices.raw.json")
    sanitized = sanitize_document(source, pseudonym_key=secrets.token_bytes(32))
    serialized = json.dumps(sanitized, sort_keys=True)

    assert "RAW_FIXTURE_MARKER" not in serialized
    assert "SYNTH-SERIAL" not in serialized
    assert "example.invalid" not in serialized
    assert "192.0.2." not in serialized
    assert "access_token" not in sanitized
    assert "authorization" not in sanitized


def test_relationships_survive_deterministic_pseudonymization() -> None:
    source = _load_fixture("managed-devices.raw.json")
    key = secrets.token_bytes(32)
    first = sanitize_document(source, pseudonym_key=key)
    second = sanitize_document(source, pseudonym_key=key)

    assert first == second
    devices = cast(list[dict[str, JsonValue]], first["devices"])
    assert devices[0]["group_id"] == devices[1]["group_id"]
    assert devices[0]["managed_device_id"] != devices[1]["managed_device_id"]


def test_different_keys_produce_different_pseudonyms() -> None:
    source = _load_fixture("managed-devices.raw.json")

    first = sanitize_document(source, pseudonym_key=secrets.token_bytes(32))
    second = sanitize_document(source, pseudonym_key=secrets.token_bytes(32))

    assert first["tenant_id"] != second["tenant_id"]


def test_unknown_field_fails_closed() -> None:
    source = _load_fixture("unknown-field.raw.json")

    with pytest.raises(UnknownFieldError, match="unclassified field"):
        sanitize_document(source, pseudonym_key=secrets.token_bytes(32))


def test_sensitive_value_in_allowed_field_fails_closed() -> None:
    source: dict[str, JsonValue] = {
        "schema_version": "1.0",
        "description": "Contact synthetic.person@example.invalid",
    }

    with pytest.raises(SensitiveValueError, match="email address"):
        sanitize_document(source, pseudonym_key=secrets.token_bytes(32))


def test_short_pseudonym_key_is_rejected() -> None:
    with pytest.raises(SanitizationError, match="at least 32 bytes"):
        sanitize_document({"schema_version": "1.0"}, pseudonym_key=b"too-short")
