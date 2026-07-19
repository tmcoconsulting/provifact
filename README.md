# EvidenceOps

[![CI](https://github.com/tmcoconsulting/evidenceops/actions/workflows/ci.yml/badge.svg)](https://github.com/tmcoconsulting/evidenceops/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

EvidenceOps is a continuous audit-evidence and configuration-lifecycle platform for regulated
endpoint-management teams. Its thesis is simple: every reviewed configuration change should
produce traceable, audit-ready evidence.

The Build Week Phase 1 slice now joins a pinned, internally approved mSCP macOS CIS Level 1 demo
inventory to a bounded GET-only Microsoft Intune Apple collector, deterministic drift evidence,
fail-closed publication, a dynamic Mission Control dashboard, and a constrained GPT-5.6 assistant.
The 98-rule baseline is visible in full; five settings have explicit deterministic demo mappings,
and unsupported rules remain visible instead of being guessed. iOS and iPadOS posture is shown but
is never scored against the macOS baseline. The public deployment remains synthetic even though a
trusted-main live audit has now passed; publishing its sanitized projection still requires a
separate human-reviewed deployment. Nothing in this repository can create,
assign, update, delete, deploy, remediate, or roll back an Intune configuration.

## Safety model

- Source integrations are read-only by contract.
- Deterministic evidence is computed before any future model-generated narrative.
- Generated analysis must be labeled and remain subject to human approval.
- Public output accepts synthetic data or a package that passed the fail-closed sanitizer.
- Pseudonymization key material never belongs in source control.
- Model output is untrusted and may be quarantined before human review.
- A Git revert changes reviewed intent; it does not revert Microsoft Intune.

## Quick start

Python 3.12 or later is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install --no-build-isolation --no-deps .
python -m pytest
python -m evidenceops run-mission-demo
python -m evidenceops rebuild-static-demo
mkdocs build --strict
npm ci --ignore-scripts --no-audit --no-fund
npm run validate:worker
npm run dev
```

The complete demonstration is credential-free and writes only synthetic public artifacts under
`build/mission-demo/`. The tracked Mission Control package under `docs/assets/data/` is generated
deterministically from code-owned fixtures and contains no TMCO tenant data.
See the [getting-started guide](docs/getting-started.md) and
[security model](docs/security-model.md) before adding a provider.

## Project status

EvidenceOps is a **Phase 1 technical proof**, not a compliance product or autonomous endpoint
manager. The expanded collector and four-permission application identity completed a protected,
trusted-main GET-only audit; its private package was deleted and production remains synthetic.
GitHub Pages is disabled. Cloudflare serves
the scanned synthetic application at
[evidenceops.tmcoconsulting.com](https://evidenceops.tmcoconsulting.com/) with bounded same-origin
`/api/status`, `/api/narrative`, and `/api/ask` routes. A bounded service-account Terra response
passed deterministic verification, but production remains fixture-first until the sanitized live
Mission package passes the separate publication-review gate. See the
[live-collection guide](docs/operations/live-collection.md), [demo package](docs/build-week/demo-package.md),
and [roadmap](docs/roadmap.md).

Copyright 2026 TMCO Consulting, LLC. Licensed under the [Apache License 2.0](LICENSE).
