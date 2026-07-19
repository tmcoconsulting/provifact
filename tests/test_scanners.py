import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.check_public_artifacts import scan as scan_public
from scripts.check_secrets import scan as scan_secrets


@pytest.mark.parametrize("prefix", ["ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_"])
def test_scanners_report_every_github_token_family_without_value(
    tmp_path: Path, prefix: str
) -> None:
    leaked = tmp_path / "leak.txt"
    token = prefix + ("A" * 40)
    leaked.write_text(token, encoding="utf-8")

    secret_findings = scan_secrets(tmp_path)
    public_findings = scan_public(tmp_path)

    assert secret_findings == [(Path("leak.txt"), 1, "GitHub token")]
    assert public_findings == [(Path("leak.txt"), 1, "GitHub token")]
    assert token not in repr(secret_findings)
    assert token not in repr(public_findings)


def test_public_scanner_detects_raw_marker(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("RAW_FIXTURE_MARKER_DEVICE", encoding="utf-8")

    assert scan_public(tmp_path) == [(Path("index.html"), 1, "raw fixture marker")]


def test_public_scanner_accepts_safe_synthetic_output(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text(
        "Synthetic evidence: matches desired state for a demo setting",
        encoding="utf-8",
    )

    assert scan_public(tmp_path) == []


def test_public_scanner_checks_visible_text_but_ignores_svg_coordinates(tmp_path: Path) -> None:
    (tmp_path / "safe.html").write_text(
        '<svg><path d="M 2.41.44.82"></path></svg><p>Safe synthetic evidence</p>',
        encoding="utf-8",
    )
    (tmp_path / "unsafe.html").write_text(
        "<p>Observed network address: 192.0.2.10</p>",
        encoding="utf-8",
    )

    assert scan_public(tmp_path) == [(Path("unsafe.html"), 1, "IP address")]


def test_public_scanner_rejects_private_evidence_paths(tmp_path: Path) -> None:
    private = tmp_path / "assets" / "private"
    private.mkdir(parents=True)
    (private / "evidence.json").write_text("{}", encoding="utf-8")

    assert scan_public(tmp_path) == [
        (Path("assets/private/evidence.json"), 1, "private-evidence path")
    ]


def test_public_scanner_allows_only_documented_public_permission_ids(tmp_path: Path) -> None:
    (tmp_path / "permissions.txt").write_text(
        "dc377aa6-52d8-4e23-b271-2a7ae04cedf3",
        encoding="utf-8",
    )
    assert scan_public(tmp_path) == []

    (tmp_path / "tenant.txt").write_text(
        "11111111-2222-4333-8444-555555555555",
        encoding="utf-8",
    )
    assert scan_public(tmp_path) == [(Path("tenant.txt"), 1, "UUID-like identifier")]


def test_secret_scanner_respects_git_ignore_but_scans_untracked_files(tmp_path: Path) -> None:
    git = shutil.which("git")
    assert git is not None
    subprocess.run([git, "init", "--quiet"], cwd=tmp_path, check=True)  # noqa: S603
    (tmp_path / ".gitignore").write_text("ignored.env\n", encoding="utf-8")
    token = "gh" + "p_" + ("A" * 40)
    (tmp_path / "ignored.env").write_text(token, encoding="utf-8")
    (tmp_path / "visible.txt").write_text(token, encoding="utf-8")

    assert scan_secrets(tmp_path) == [(Path("visible.txt"), 1, "GitHub token")]


def test_secret_scanner_rejects_private_artifact_paths(tmp_path: Path) -> None:
    private = tmp_path / "artifacts"
    private.mkdir()
    (private / "evidence.json").write_text("{}", encoding="utf-8")
    assert scan_secrets(tmp_path) == [
        (Path("artifacts/evidence.json"), 1, "prohibited private artifact path")
    ]


def test_secret_scanner_rejects_bare_dotenv_path(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("PLACEHOLDER=not-a-secret", encoding="utf-8")
    assert scan_secrets(tmp_path) == [(Path(".env"), 1, "prohibited private artifact path")]
