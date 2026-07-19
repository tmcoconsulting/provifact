"""Opt-in private contract probe; skipped in public CI and normal local tests."""

from __future__ import annotations

import os

import pytest

from evidenceops.providers import EnvironmentTokenProvider, GraphClient, IntuneProvider

pytestmark = pytest.mark.live


@pytest.mark.skipif(
    os.environ.get("EVIDENCEOPS_RUN_LIVE_INTUNE_TEST") != "1",
    reason="live Intune test requires explicit EVIDENCEOPS_RUN_LIVE_INTUNE_TEST=1",
)
def test_private_intune_read_contract() -> None:
    """Make only documented GET calls and retain no response or identifier."""
    token = os.environ.get("EVIDENCEOPS_GRAPH_ACCESS_TOKEN")
    if not token:
        pytest.fail("explicit live test requires EVIDENCEOPS_GRAPH_ACCESS_TOKEN")
    result = IntuneProvider(GraphClient(token_provider=EnvironmentTokenProvider(token))).collect(
        desired_state_git_commit_sha=None
    )
    assert result.provider["provider"] == "microsoft-intune"
    assert result.provider["source_api_version"] == "v1.0"
    assert result.private_trace["raw_response_persisted"] is False
