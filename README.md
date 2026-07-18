# EvidenceOps

[![CI](https://github.com/tmcoconsulting/evidenceops/actions/workflows/ci.yml/badge.svg)](https://github.com/tmcoconsulting/evidenceops/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

EvidenceOps is an early-stage continuous compliance evidence and
configuration-lifecycle platform for regulated endpoint-management teams. Its goal is simple:
every approved configuration change should produce traceable, audit-ready evidence.

The Phase 0 repository contains a vendor-neutral Python domain model, deterministic drift
comparison, a fail-closed public-artifact sanitizer, synthetic fixtures, and a static
documentation/demo site. It does **not** contain a live Microsoft Graph collector, Intune write
operations, production tenant data, or an operational AI narrative generator.

## Safety model

- Source integrations are read-only by contract.
- Deterministic evidence is computed before any future model-generated narrative.
- Generated analysis must be labeled and remain subject to human approval.
- Public output accepts synthetic data or a package that passed the fail-closed sanitizer.
- Pseudonymization key material never belongs in source control.

## Quick start

Python 3.12 or later is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install --no-build-isolation --no-deps -e .
python -m pytest
mkdocs serve
```

The demonstration at `docs/assets/data/demo-summary.json` is intentionally synthetic. See the
[getting-started guide](https://tmcoconsulting.github.io/evidenceops/getting-started/) and
[security model](https://tmcoconsulting.github.io/evidenceops/security-model/) before adding a
provider.

## Project status

EvidenceOps is in **Phase 0**: repository, security boundaries, documentation, and validation
foundation. See the [roadmap](https://tmcoconsulting.github.io/evidenceops/roadmap/) for explicitly
deferred work.

Copyright 2026 TMCO Consulting, LLC. Licensed under the [Apache License 2.0](LICENSE).
