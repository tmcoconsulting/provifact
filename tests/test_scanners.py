from pathlib import Path

from scripts.check_public_artifacts import scan as scan_public
from scripts.check_secrets import scan as scan_secrets


def test_secret_scanner_reports_location_without_value(tmp_path: Path) -> None:
    leaked = tmp_path / "leak.txt"
    token = "gh" + "p_" + ("A" * 40)
    leaked.write_text(token, encoding="utf-8")

    findings = scan_secrets(tmp_path)

    assert findings == [(Path("leak.txt"), 1, "GitHub token")]
    assert token not in repr(findings)


def test_public_scanner_detects_raw_marker(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("RAW_FIXTURE_MARKER_DEVICE", encoding="utf-8")

    assert scan_public(tmp_path) == [(Path("index.html"), 1, "raw fixture marker")]


def test_public_scanner_accepts_safe_synthetic_output(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text(
        "Synthetic evidence: compliant control SYN-MAC-001",
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
