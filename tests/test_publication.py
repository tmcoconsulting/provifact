from __future__ import annotations

import copy
import json
import shutil
import stat
import subprocess
from pathlib import Path
from typing import cast

import pytest

from evidenceops.demo import FIXED_COLLECTION_TIME, build_synthetic_private_package
from evidenceops.domain import (
    EvidenceObject,
    JsonValue,
    make_evidence_object,
    validate_evidence_object,
)
from evidenceops.evidence import (
    PublicationError,
    load_evidence_package,
    publish_private_package,
    write_private_package,
    write_public_package,
)
from evidenceops.sanitization import SensitiveValueError, UnknownFieldError

TEST_PSEUDONYM_KEY = bytes(range(32))


def _rebuild_private(package: EvidenceObject, **updates: JsonValue) -> EvidenceObject:
    payload = {
        key: value
        for key, value in package.items()
        if key not in {"schema_version", "object_type", "evidence_id", "content_fingerprint"}
    }
    payload.update(updates)
    return make_evidence_object("private_evidence_package", payload)


def test_publication_removes_private_fields_and_records_policy_fingerprints() -> None:
    private = build_synthetic_private_package()
    public = publish_private_package(
        private,
        pseudonym_key=TEST_PSEUDONYM_KEY,
        published_at_utc=FIXED_COLLECTION_TIME,
    )
    validate_evidence_object(public)
    serialized = json.dumps(public, sort_keys=True)
    assert public["object_type"] == "sanitized_public_evidence_package"
    assert public["source_type"] == "curated-synthetic-fixture"
    assert "private_trace" not in serialized
    assert "retention" not in serialized
    publication = cast(dict[str, JsonValue], public["publication"])
    assert publication["publication_policy_version"] == "evidenceops-publication-v1.0.0"
    assert publication["source_private_fingerprint"] == private["content_fingerprint"]
    assert cast(str, publication["sanitized_content_fingerprint"]).startswith("sha256:")


def test_nested_unknown_field_fails_even_inside_dropped_private_boundary() -> None:
    private = build_synthetic_private_package()
    unsafe = _rebuild_private(
        private,
        private_trace={
            "fixture_notice": "SYNTHETIC_TEST_DATA_ONLY",
            "nested": {"future_sensitive_vendor_field": "must not pass"},
        },
    )
    with pytest.raises(UnknownFieldError, match="unclassified field: nested"):
        publish_private_package(
            unsafe,
            pseudonym_key=TEST_PSEUDONYM_KEY,
            published_at_utc=FIXED_COLLECTION_TIME,
        )


@pytest.mark.parametrize(
    "prohibited",
    [
        "person@private.example",
        "SERIAL-ABCDEF123456",
        "11111111-2222-4333-8444-555555555555",
        "10.20.30.40",
        "internal.corp",
        "Bearer " + "abcdefghijklmnopqrstuvwxyz123456",
        "eyJabcdefghijk" + ".abcdefghijklmnop.abcdefghijklmnop",
        "-----BEGIN " + "PRIVATE KEY-----",
        "-----BEGIN " + "CERTIFICATE-----",
        "RAW_FIXTURE_MARKER_DEVICE",
    ],
)
def test_publication_rejects_sensitive_value_smuggled_into_allowed_text(
    prohibited: str,
) -> None:
    private = build_synthetic_private_package()
    desired = copy.deepcopy(cast(list[EvidenceObject], private["desired_state"]))
    first_payload = {
        key: value
        for key, value in desired[0].items()
        if key not in {"schema_version", "object_type", "evidence_id", "content_fingerprint"}
    }
    first_payload["description"] = prohibited
    desired[0] = make_evidence_object("desired_state_record", first_payload)
    unsafe = _rebuild_private(private, desired_state=cast(JsonValue, desired))
    with pytest.raises(SensitiveValueError):
        publish_private_package(
            unsafe,
            pseudonym_key=TEST_PSEUDONYM_KEY,
            published_at_utc=FIXED_COLLECTION_TIME,
        )


def test_private_writer_requires_ignored_repository_path_and_mode_600(tmp_path: Path) -> None:
    git = shutil.which("git")
    assert git is not None
    subprocess.run(  # noqa: S603  # nosec B603 - test-only resolved git executable
        [git, "init", "--quiet"], cwd=tmp_path, check=True
    )
    (tmp_path / ".gitignore").write_text("private/\n", encoding="utf-8")
    package = build_synthetic_private_package()
    output = write_private_package(
        package,
        directory=tmp_path / "private",
        repository_root=tmp_path,
    )
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    assert load_evidence_package(output) == package
    with pytest.raises(PublicationError, match="overwrite"):
        write_private_package(
            package,
            directory=tmp_path / "private",
            repository_root=tmp_path,
        )


def test_private_writer_rejects_nonignored_and_outside_paths(tmp_path: Path) -> None:
    git = shutil.which("git")
    assert git is not None
    subprocess.run(  # noqa: S603  # nosec B603 - test-only resolved git executable
        [git, "init", "--quiet"], cwd=tmp_path, check=True
    )
    package = build_synthetic_private_package()
    with pytest.raises(PublicationError, match="not covered"):
        write_private_package(package, directory=tmp_path / "visible", repository_root=tmp_path)
    with pytest.raises(PublicationError, match="inside"):
        write_private_package(
            package,
            directory=tmp_path.parent / "outside",
            repository_root=tmp_path,
        )


def test_public_writer_refuses_overwrite(tmp_path: Path) -> None:
    public = publish_private_package(
        build_synthetic_private_package(),
        pseudonym_key=TEST_PSEUDONYM_KEY,
        published_at_utc=FIXED_COLLECTION_TIME,
    )
    output = tmp_path / "public.json"
    assert write_public_package(public, output=output) == output
    with pytest.raises(PublicationError, match="overwrite"):
        write_public_package(public, output=output)


def test_loader_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(PublicationError, match="could not be read"):
        load_evidence_package(path)
