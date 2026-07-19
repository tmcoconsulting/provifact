# Live Demo

<div class="synthetic-banner">
SYNTHETIC DEMO DATA. This deployment never calls Microsoft Graph. Fixture mode makes no OpenAI
request; any future live model response must be labeled separately and pass the deterministic
verifier.
</div>

The primary Build Week demonstration is the dynamic [EvidenceOps Mission Control](evidence-dashboard.md).
It renders entirely from the validated
[Mission package](assets/data/mission-control.json), so dashboard metrics, findings, history,
platform posture, gaps, and assistant references have one deterministic source.

## What the fixture proves

| Stage | Demonstrated result | Authority boundary |
| --- | --- | --- |
| Approved baseline | Pinned 98-rule macOS CIS Level 1 inventory with TMCO demo approval | Internal technical intent, not external certification |
| Read-only collection | Synthetic Mac, iPhone, iPad, policies, apps, assignments, and service health | Same normalized shape as the GET-only provider |
| Deterministic evaluation | One aligned rule, two value drifts, one assignment drift, one conflict | Model-independent algorithm |
| Platform boundary | iOS/iPadOS posture visible but excluded from macOS CIS scoring | No false cross-platform baseline claim |
| Publication | Allowlisted package with policy version, stable IDs, and SHA-256 fingerprint | Public/model-safe derivative |
| History | Current and prior sanitized snapshots with changed/new/resolved findings | No raw tenant persistence |
| Assistant | Supported answers cite the package; unsupported questions return the exact insufficient-evidence sentence | Fixture mode is not a model call |
| Verification | Typed claims must exactly match evidence; prose remains generated and quarantined | Human review required |

The alignment score is intentionally 20%: one aligned rule divided by five explicitly mapped and
evaluable rules. The other 93 baseline rules remain visible as unsupported and do not inflate or
deflate the denominator.

## Representative states

- FileVault value drift (high severity)
- Firewall value drift (high severity)
- Missing assignment for screen-lock password enforcement
- Conflicting screen-lock timeout values
- Firewall stealth mode aligned
- One iOS/iPadOS policy observation
- Application deployment health and one failure aggregate
- One explicit synthetic collection gap
- Previous-versus-current drift changes
- Deterministic CIS, STIG, NIST, and CMMC crosswalk identifiers where available

These are technical evidence states. They are not certification, control satisfaction, assessment
completion, or organizational compliance.

## Reproduce it

```bash
python -m evidenceops run-mission-demo --output-dir build/mission-demo
python scripts/check_public_artifacts.py build/mission-demo
python -m evidenceops rebuild-static-demo
mkdocs build --strict
python scripts/check_public_artifacts.py site
```

The legacy schema-v1 narrative proof remains tracked under `docs/assets/data/phase1-*` so judges can
also inspect an intentionally rejected compliance-verdict narrative. Mission Control adds the
interactive `/api/ask` boundary without weakening that verifier.

There is no automatic remediation. A Git revert changes desired-state history only; it does not
revert Intune. Human assessors retain final judgment.
