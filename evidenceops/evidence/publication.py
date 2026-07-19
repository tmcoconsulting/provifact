"""Private evidence storage and fail-closed public-package publication."""

from __future__ import annotations

import json
import os
import shutil
import subprocess  # nosec B404
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from evidenceops.domain import (
    EvidenceObject,
    EvidenceSchemaError,
    JsonValue,
    fingerprint,
    make_evidence_object,
    validate_evidence_object,
)
from evidenceops.sanitization import (
    DEFAULT_PUBLIC_POLICY,
    SanitizationPolicy,
    sanitize_document,
)


class PublicationError(ValueError):
    """Raised before a private or unsafe artifact can cross its boundary."""


def write_private_package(
    package: EvidenceObject,
    *,
    directory: Path,
    repository_root: Path,
) -> Path:
    """Write one normalized package with restrictive permissions to an ignored path."""
    validated = validate_evidence_object(package)
    if validated["object_type"] != "private_evidence_package":
        raise PublicationError("only a private evidence package can use the private writer")
    root = repository_root.resolve()
    destination = directory.resolve()
    if not destination.is_relative_to(root):
        raise PublicationError("private directory must be inside the selected repository")
    _assert_git_ignored(destination, root)
    destination.mkdir(mode=0o700, parents=True, exist_ok=True)
    destination.chmod(0o700)
    suffix = cast(str, validated["content_fingerprint"])[-16:]
    output = destination / f"private-evidence-{suffix}.json"
    _exclusive_json_write(output, validated, mode=0o600)
    return output


def publish_private_package(
    package: EvidenceObject,
    *,
    pseudonym_key: bytes,
    published_at_utc: str | None = None,
    policy: SanitizationPolicy = DEFAULT_PUBLIC_POLICY,
) -> EvidenceObject:
    """Validate, classify, sanitize, scan, fingerprint, and emit public evidence in memory."""
    validated = validate_evidence_object(package)
    if validated["object_type"] != "private_evidence_package":
        raise PublicationError("publication requires a private evidence package")
    sanitized = sanitize_document(validated, pseudonym_key=pseudonym_key, policy=policy)
    if "private_trace" in sanitized or "retention" in sanitized:
        raise PublicationError("private-only fields survived publication policy")
    source_type = (
        "curated-synthetic-fixture"
        if validated["synthetic"] is True
        else "sanitized-live-collection"
    )
    core: dict[str, JsonValue] = {
        "synthetic": validated["synthetic"],
        "source_type": source_type,
        "provider": sanitized["provider"],
        "collection": sanitized["collection"],
        "desired_state": sanitized["desired_state"],
        "observations": sanitized["observations"],
        "findings": sanitized["findings"],
        "evidence_references": sanitized["evidence_references"],
        "human_approval_status": sanitized["human_approval_status"],
    }
    publication_time = published_at_utc or datetime.now(UTC).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )
    core["publication"] = {
        "publication_policy_version": policy.version,
        "published_at_utc": publication_time,
        "source_private_fingerprint": validated["content_fingerprint"],
        "sanitized_content_fingerprint": fingerprint(core),
    }
    public = make_evidence_object("sanitized_public_evidence_package", core)
    _validate_reference_graph(public)
    # A second pass includes the publication metadata and rejects sensitive values
    # introduced by future code after the first transformation.
    rescanned = sanitize_document(public, pseudonym_key=pseudonym_key, policy=policy)
    if rescanned != public:
        raise PublicationError("public package changed during final content scan")
    return public


def write_public_package(package: EvidenceObject, *, output: Path) -> Path:
    """Write an already validated public package; existing files are never overwritten."""
    validated = validate_evidence_object(package)
    if validated["object_type"] != "sanitized_public_evidence_package":
        raise PublicationError("only a sanitized public package may use the public writer")
    output.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    _exclusive_json_write(output, validated, mode=0o644)
    return output


def load_evidence_package(path: Path) -> EvidenceObject:
    """Load JSON without logging its content and validate its identity."""
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublicationError("evidence package could not be read as JSON") from exc
    try:
        return validate_evidence_object(loaded)
    except EvidenceSchemaError as exc:
        raise PublicationError("evidence package failed schema validation") from exc


def _assert_git_ignored(destination: Path, root: Path) -> None:
    probe = destination / ".evidenceops-private-probe"
    relative = probe.relative_to(root)
    git_executable = shutil.which("git")
    if git_executable is None:
        raise PublicationError("git is required to verify the private output boundary")
    result = subprocess.run(  # noqa: S603  # nosec B603
        [git_executable, "check-ignore", "--quiet", "--no-index", "--", str(relative)],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise PublicationError(
            "selected private directory is not covered by repository ignore rules"
        )


def _exclusive_json_write(path: Path, value: EvidenceObject, *, mode: int) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, mode)
    except FileExistsError as exc:
        raise PublicationError(f"refusing to overwrite existing artifact: {path.name}") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _validate_reference_graph(package: EvidenceObject) -> None:
    provider = cast(EvidenceObject, package["provider"])
    collection = cast(EvidenceObject, package["collection"])
    desired = cast(list[EvidenceObject], package["desired_state"])
    observations = cast(list[EvidenceObject], package["observations"])
    findings = cast(list[EvidenceObject], package["findings"])
    references = cast(list[EvidenceObject], package["evidence_references"])
    objects = [provider, collection, *desired, *observations, *findings, *references]
    evidence_ids = {cast(str, item["evidence_id"]) for item in objects}
    if collection["provider_evidence_id"] not in evidence_ids:
        raise PublicationError("collection provider reference is outside the package")
    for observation in observations:
        if (
            observation["provider_evidence_id"] not in evidence_ids
            or observation["collection_evidence_id"] not in evidence_ids
        ):
            raise PublicationError("observation reference is outside the package")
    for finding in findings:
        linked = {
            cast(str, finding["collection_evidence_id"]),
            cast(str, finding["desired_state_evidence_id"]),
            *cast(list[str], finding["observation_evidence_ids"]),
        }
        if not linked.issubset(evidence_ids):
            raise PublicationError("finding reference is outside the package")
    for reference in references:
        if reference["referenced_evidence_id"] not in evidence_ids:
            raise PublicationError("evidence reference is outside the package")
