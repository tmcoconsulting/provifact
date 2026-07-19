"""Small fail-safe operator interface for the bounded Phase 1 proof."""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess  # nosec B404
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final, cast

from evidenceops.demo import (
    DEFAULT_DESIRED_FIXTURE,
    FIXED_COLLECTION_TIME,
    build_synthetic_private_package,
    load_desired_state,
)
from evidenceops.domain import EvidenceObject, make_evidence_object
from evidenceops.evidence import (
    PublicationError,
    build_private_package,
    load_evidence_package,
    publish_private_package,
    write_private_package,
    write_public_package,
)
from evidenceops.evidence.mission import (
    build_public_mission_snapshot,
    validate_public_mission_snapshot,
)
from evidenceops.evidence.mission_storage import (
    collection_from_private_document,
    load_private_collection,
    private_collection_document,
    write_private_collection,
)
from evidenceops.mission_demo import build_mission_demo
from evidenceops.narrative import (
    DEFAULT_OPENAI_MODEL,
    NarrativeGenerationError,
    OpenAINarrativeAdapter,
    OpenAIResponsesTransport,
    build_offline_narrative,
    verify_narrative,
)
from evidenceops.providers import (
    AppleIntuneProvider,
    DeviceCodeTokenProvider,
    EnvironmentTokenProvider,
    GraphClient,
    GraphProviderError,
    IntuneProvider,
    TokenAcquisitionError,
    TokenProvider,
)
from evidenceops.sanitization import SanitizationError

REPOSITORY_ROOT: Final = Path(__file__).parents[1]
STATIC_DEMO_DATA_DIRECTORY: Final = REPOSITORY_ROOT / "docs" / "assets" / "data"
STATIC_DEMO_FILENAMES: Final = {
    "phase1-public-evidence.json",
    "phase1-fixture-narrative.json",
    "phase1-verification.json",
    "phase1-rejected-verification.json",
    "demo-summary.json",
    "mission-control.json",
}
APPLE_DELEGATED_SCOPES: Final = tuple(
    f"https://graph.microsoft.com/{permission}"
    for permission in (
        "DeviceManagementConfiguration.Read.All",
        "DeviceManagementManagedDevices.Read.All",
        "DeviceManagementApps.Read.All",
        "DeviceManagementServiceConfig.Read.All",
    )
)


def build_parser() -> argparse.ArgumentParser:
    """Create the complete, intentionally small command surface."""
    parser = argparse.ArgumentParser(prog="evidenceops")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("run-demo", help="run the credential-free synthetic flow")
    demo.add_argument("--output-dir", type=Path, default=Path("build/synthetic-demo"))

    mission_demo = subparsers.add_parser(
        "run-mission-demo", help="build the credential-free Mission Control vertical slice"
    )
    mission_demo.add_argument("--output-dir", type=Path, default=Path("build/mission-demo"))

    live = subparsers.add_parser("live-collect", help="collect the narrow Intune slice read-only")
    live.add_argument("--private-dir", type=Path, default=Path("artifacts/private"))
    live.add_argument("--desired-state", type=Path, default=DEFAULT_DESIRED_FIXTURE)
    live.add_argument("--retention-days", type=int, default=7)
    live.add_argument("--auth", choices=("device-code", "environment-token"), required=True)

    live_apple = subparsers.add_parser(
        "live-collect-apple", help="collect normalized Apple Intune evidence read-only"
    )
    live_apple.add_argument("--private-dir", type=Path, default=Path("artifacts/private"))
    live_apple.add_argument("--retention-days", type=int, default=1)
    live_apple.add_argument("--auth", choices=("device-code", "environment-token"), required=True)

    publish = subparsers.add_parser("publish", help="sanitize a selected private package")
    publish.add_argument("private_package", type=Path)
    publish.add_argument("--output", type=Path, required=True)

    publish_mission = subparsers.add_parser(
        "publish-mission", help="sanitize a normalized private Apple collection"
    )
    publish_mission.add_argument("private_collection", type=Path)
    publish_mission.add_argument("--output", type=Path, required=True)

    generate = subparsers.add_parser(
        "generate-narrative", help="opt in to GPT-5.6 analysis of sanitized evidence"
    )
    generate.add_argument("public_package", type=Path)
    generate.add_argument("--output", type=Path, required=True)
    generate.add_argument(
        "--model", default=os.environ.get("EVIDENCEOPS_OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    )

    verify = subparsers.add_parser("verify-narrative", help="verify an untrusted narrative")
    verify.add_argument("public_package", type=Path)
    verify.add_argument("narrative", type=Path)
    verify.add_argument("--output", type=Path, required=True)

    subparsers.add_parser(
        "rebuild-static-demo", help="rebuild tracked static-demo data from synthetic fixtures"
    )
    subparsers.add_parser("rebuild-pages-demo", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Dispatch one command and suppress sensitive response content on expected failure."""
    args = build_parser().parse_args(argv)
    try:
        if args.command == "run-demo":
            _run_demo(args.output_dir)
        elif args.command == "run-mission-demo":
            _run_mission_demo(args.output_dir)
        elif args.command == "live-collect":
            _live_collect(
                args.private_dir,
                args.desired_state,
                retention_days=args.retention_days,
                auth=args.auth,
            )
        elif args.command == "publish":
            _publish(args.private_package, args.output)
        elif args.command == "live-collect-apple":
            _live_collect_apple(
                args.private_dir,
                retention_days=args.retention_days,
                auth=args.auth,
            )
        elif args.command == "publish-mission":
            _publish_mission(args.private_collection, args.output)
        elif args.command == "generate-narrative":
            _generate_narrative(args.public_package, args.output, model=args.model)
        elif args.command == "verify-narrative":
            _verify(args.public_package, args.narrative, args.output)
        elif args.command in {"rebuild-static-demo", "rebuild-pages-demo"}:
            _rebuild_static_demo()
        else:  # pragma: no cover - argparse enforces a known command
            raise AssertionError("unknown command")
    except (
        GraphProviderError,
        NarrativeGenerationError,
        PublicationError,
        SanitizationError,
        TokenAcquisitionError,
        ValueError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


def _run_demo(output_directory: Path) -> None:
    destination = output_directory.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("demo output directory must not exist or must be empty")
    destination.mkdir(mode=0o755, parents=True, exist_ok=True)
    for filename, document in _synthetic_artifacts().items():
        _write_new_json(destination / filename, document)
    print(f"synthetic demo complete: {destination}")


def _run_mission_demo(output_directory: Path) -> None:
    destination = output_directory.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Mission demo output directory must not exist or must be empty")
    destination.mkdir(mode=0o755, parents=True, exist_ok=True)
    _write_new_json(destination / "mission-control.json", build_mission_demo())
    print(f"synthetic Mission Control demo complete: {destination}")


def _live_collect(
    private_directory: Path,
    desired_state_path: Path,
    *,
    retention_days: int,
    auth: str,
) -> None:
    if retention_days < 1 or retention_days > 90:
        raise ValueError("retention-days must be between 1 and 90")
    git_sha = _git_commit_sha()
    desired_state = load_desired_state(desired_state_path, git_commit_sha=git_sha)
    token_provider: TokenProvider
    if auth == "environment-token":
        token_provider = EnvironmentTokenProvider(
            _required_environment("EVIDENCEOPS_GRAPH_ACCESS_TOKEN")
        )
    else:
        token_provider = DeviceCodeTokenProvider(
            tenant_id=_required_environment("AZURE_TENANT_ID"),
            client_id=_required_environment("AZURE_CLIENT_ID"),
        )
    collected = IntuneProvider(GraphClient(token_provider=token_provider)).collect(
        desired_state_git_commit_sha=git_sha
    )
    delete_after = datetime.now(UTC) + timedelta(days=retention_days)
    package = build_private_package(
        synthetic=False,
        provider=collected.provider,
        collection=collected.collection,
        desired_state=desired_state,
        observations=collected.observations,
        retention={
            "policy": "operator-managed-private-evidence",
            "delete_after_utc": delete_after.isoformat(timespec="seconds").replace("+00:00", "Z"),
        },
        private_trace=collected.private_trace,
    )
    output = write_private_package(
        package,
        directory=private_directory,
        repository_root=REPOSITORY_ROOT,
    )
    print(f"private read-only collection written: {output}")


def _publish(private_path: Path, output: Path) -> None:
    key = _required_environment("EVIDENCEOPS_PSEUDONYM_KEY").encode("utf-8")
    public = publish_private_package(load_evidence_package(private_path), pseudonym_key=key)
    written = write_public_package(public, output=output)
    print(f"sanitized package written: {written.resolve()}")


def _live_collect_apple(private_directory: Path, *, retention_days: int, auth: str) -> None:
    if retention_days < 1 or retention_days > 30:
        raise ValueError("retention-days must be between 1 and 30")
    token_provider: TokenProvider
    if auth == "environment-token":
        token_provider = EnvironmentTokenProvider(
            _required_environment("EVIDENCEOPS_GRAPH_ACCESS_TOKEN")
        )
    else:
        token_provider = DeviceCodeTokenProvider(
            tenant_id=_required_environment("AZURE_TENANT_ID"),
            client_id=_required_environment("AZURE_CLIENT_ID"),
            scopes=APPLE_DELEGATED_SCOPES,
        )
    collection = AppleIntuneProvider(GraphClient(token_provider=token_provider)).collect()
    delete_after = datetime.now(UTC) + timedelta(days=retention_days)
    document = private_collection_document(
        collection,
        delete_after_utc=delete_after.isoformat(timespec="seconds").replace("+00:00", "Z"),
    )
    output = write_private_collection(
        document,
        directory=private_directory,
        repository_root=REPOSITORY_ROOT,
    )
    print(f"normalized private Apple collection written: {output}")


def _publish_mission(private_path: Path, output: Path) -> None:
    document = load_private_collection(private_path)
    collection = collection_from_private_document(document)
    key = _required_environment("EVIDENCEOPS_PSEUDONYM_KEY").encode("utf-8")
    public = build_public_mission_snapshot(
        collection,
        pseudonym_key=key,
        synthetic=False,
        source_git_commit=_git_commit_sha(),
    )
    validate_public_mission_snapshot(public)
    _write_new_json(output, public)
    print(f"sanitized Mission Control package written: {output.resolve()}")


def _generate_narrative(public_path: Path, output: Path, *, model: str) -> None:
    public = load_evidence_package(public_path)
    narrative = OpenAINarrativeAdapter(transport=OpenAIResponsesTransport(), model=model).generate(
        public, api_key=_required_environment("OPENAI_API_KEY")
    )
    _write_new_json(output, narrative)
    print(f"unverified AI-generated narrative written: {output.resolve()}")


def _verify(public_path: Path, narrative_path: Path, output: Path) -> None:
    result = verify_narrative(
        load_evidence_package(narrative_path), load_evidence_package(public_path)
    )
    _write_new_json(output, result)
    typed_claim_count = len(cast(list[str], result["accepted_claims"]))
    print(
        f"narrative quarantined for human review; {typed_claim_count} typed claims verified: "
        f"{output.resolve()}"
    )


def _rebuild_static_demo() -> None:
    for filename, document in _synthetic_artifacts().items():
        if filename not in STATIC_DEMO_FILENAMES:
            raise AssertionError("unapproved static-demo data filename")
        _atomic_json_replace(STATIC_DEMO_DATA_DIRECTORY / filename, document)
    print("synthetic static-demo data rebuilt")


def _synthetic_artifacts() -> dict[str, EvidenceObject]:
    public = publish_private_package(
        build_synthetic_private_package(),
        pseudonym_key=bytes(range(32)),
        published_at_utc=FIXED_COLLECTION_TIME,
    )
    narrative = build_offline_narrative(public)
    verification = verify_narrative(narrative, public)
    rejected_verification = verify_narrative(_rejected_fixture(narrative), public)
    return {
        "phase1-public-evidence.json": public,
        "phase1-fixture-narrative.json": narrative,
        "phase1-verification.json": verification,
        "phase1-rejected-verification.json": rejected_verification,
        "demo-summary.json": _demo_summary(public, narrative, verification, rejected_verification),
        "mission-control.json": build_mission_demo(),
    }


def _rejected_fixture(narrative: EvidenceObject) -> EvidenceObject:
    payload = {
        key: value
        for key, value in copy.deepcopy(narrative).items()
        if key not in {"schema_version", "object_type", "evidence_id", "content_fingerprint"}
    }
    payload["executive_summary"] = (
        "REJECTED EXAMPLE: the model incorrectly declared the environment compliant."
    )
    return make_evidence_object("generated_narrative", payload)


def _demo_summary(
    public: EvidenceObject,
    narrative: EvidenceObject,
    verification: EvidenceObject,
    rejected_verification: EvidenceObject,
) -> EvidenceObject:
    finding_count = len(cast(list[EvidenceObject], public["findings"]))
    verified_claim_count = len(cast(list[str], verification["accepted_claims"]))
    quarantined_prose_count = len(cast(list[str], verification["rejected_claims"]))
    return make_evidence_object(
        "evidence_reference",
        {
            "referenced_evidence_id": public["evidence_id"],
            "reference_kind": "phase1_synthetic_demo",
            "label": (
                f"{finding_count} deterministic findings; {verified_claim_count} typed claims "
                f"verified; {quarantined_prose_count} generated fields quarantined; "
                f"adversarial policy rejection={not rejected_verification['accepted']}; "
                f"narrative={narrative['evidence_id']}"
            ),
        },
    )


def _required_environment(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"required environment variable is not set: {name}")
    return value


def _git_commit_sha() -> str:
    git_executable = shutil.which("git")
    if git_executable is None:
        raise ValueError("git is required to resolve desired-state provenance")
    result = subprocess.run(  # noqa: S603  # nosec B603
        [git_executable, "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    sha = result.stdout.strip()
    if result.returncode != 0 or len(sha) not in {40, 64}:
        raise ValueError("desired-state Git commit SHA could not be resolved")
    return sha


def _write_new_json(path: Path, document: EvidenceObject) -> None:
    path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(document, stream, indent=2, sort_keys=True)
        stream.write("\n")


def _atomic_json_replace(path: Path, document: EvidenceObject) -> None:
    path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(document, stream, indent=2, sort_keys=True)
            stream.write("\n")
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
