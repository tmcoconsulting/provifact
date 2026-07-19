# EvidenceOps

[![CI](https://github.com/tmcoconsulting/evidenceops/actions/workflows/ci.yml/badge.svg)](https://github.com/tmcoconsulting/evidenceops/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

EvidenceOps is a continuous audit-evidence and configuration-lifecycle platform for regulated
endpoint-management teams. Its thesis is simple: every reviewed configuration change should
produce traceable, audit-ready evidence.

Phase 1 proves one narrow path end to end: versioned desired state in Git, a GET-only Microsoft
Intune adapter for two macOS general-configuration settings, deterministic drift findings, a
private evidence package, fail-closed publication, optional GPT-5.6 structured analysis, and a
deterministic narrative verifier. The verifier checks exact finding coverage and typed status
claims; generated prose remains quarantined for human review. The public demo remains synthetic.
Nothing in this repository
can create, assign, update, delete, deploy, remediate, or roll back an Intune configuration.

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
python -m evidenceops run-demo
mkdocs build --strict
npm ci --ignore-scripts --no-audit --no-fund
npm run validate:worker
npm run dev
```

The complete demonstration is credential-free and writes only synthetic public artifacts under
`build/synthetic-demo/`. The tracked static-demo data under `docs/assets/data/` is also synthetic.
See the [getting-started guide](docs/getting-started.md) and
[security model](docs/security-model.md) before adding a provider.

## Project status

EvidenceOps is an early **Phase 1 proof**, not a compliance product or autonomous endpoint manager.
Live collection is opt-in and private. The environment-bound Entra federation and required Graph
application permission now have administrator consent, but no live tenant request has run: the
manual audit remains restricted to reviewed `main` through the protected `production` environment.
GitHub Pages has been disabled. The Cloudflare Worker now serves the synthetic site at
[evidenceops.tmcoconsulting.com](https://evidenceops.tmcoconsulting.com/) with bounded same-origin
`/api/status` and `/api/narrative` routes. Production is deliberately in fixture mode because the
bounded OpenAI validation reached the API but returned capacity unavailable. See the
[Worker runbook](docs/operations/cloudflare-worker.md) and [roadmap](docs/roadmap.md).

Copyright 2026 TMCO Consulting, LLC. Licensed under the [Apache License 2.0](LICENSE).
