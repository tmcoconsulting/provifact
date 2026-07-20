from __future__ import annotations

import tomllib
from pathlib import Path

import evidenceops
import provifact
from evidenceops.cli import build_parser

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_provifact_public_brand_and_tagline_are_consistent() -> None:
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    landing = (REPOSITORY_ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    dashboard = (REPOSITORY_ROOT / "docs" / "evidence-dashboard.md").read_text(encoding="utf-8")
    mkdocs = (REPOSITORY_ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    assert readme.startswith("# Provifact™ by TMCO Consulting\n")
    assert "**From approved change to audit-ready proof.**" in readme
    assert '<div class="hero-kicker">Provifact™ by TMCO Consulting</div>' in landing
    assert "<h1>From approved change to audit-ready proof.</h1>" in landing
    assert "<strong>Provifact™</strong><small>by TMCO Consulting</small>" in dashboard
    assert "site_name: Provifact™ by TMCO Consulting" in mkdocs
    assert "site_description: From approved change to audit-ready proof." in mkdocs


def test_prior_product_name_is_absent_from_current_public_copy() -> None:
    paths = [REPOSITORY_ROOT / "README.md", *sorted((REPOSITORY_ROOT / "docs").rglob("*.md"))]
    for path in paths:
        if "private" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        assert "EvidenceOps" not in text, path
        assert "Evidence Ops" not in text, path


def test_provifact_cli_alias_preserves_the_phase1_engine_namespace() -> None:
    metadata = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["name"] == "provifact"
    assert metadata["project"]["scripts"] == {
        "provifact": "evidenceops.cli:main",
        "evidenceops": "evidenceops.cli:main",
    }
    assert provifact.__version__ == evidenceops.__version__
    assert build_parser().prog == "provifact"
