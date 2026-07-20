# EvidenceOps

[![CI](https://github.com/tmcoconsulting/evidenceops/actions/workflows/ci.yml/badge.svg)](https://github.com/tmcoconsulting/evidenceops/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

EvidenceOps is a continuous audit-evidence and configuration-lifecycle platform for regulated
endpoint-management teams. Every reviewed configuration change should produce traceable evidence;
teams should not have to reconstruct months of intent, observation, and approval history before an
audit.

The Build Week Phase 1 vertical slice connects a Git-approved macOS baseline to Microsoft Intune
through Microsoft Graph GET requests, normalizes only the evidence needed for deterministic drift,
publishes a fail-closed sanitized package, and serves an operational dashboard with a constrained
GPT-5.6 Evidence Copilot. The live application is
[evidenceops.tmcoconsulting.com](https://evidenceops.tmcoconsulting.com/).

The verified production record is in
[Final Live MVP Validation](docs/build-week/final-live-mvp-validation.md). Production currently
serves a scanned live package with an immediately prior live snapshot; one bounded
`gpt-5.6-terra` request passed typed-claim and evidence-reference verification. No Intune mutation
was performed.

## What the slice proves

- The approved baseline is **TMCO Consulting macOS CIS Level 1 Demo Baseline**, pinned to a reviewed
  mSCP revision and hashes. This approval supports technical drift detection; it is not CIS
  certification or an organizational compliance verdict.
- Four macOS settings have reviewed, exact Microsoft Intune provider-definition mappings. A fifth
  desired setting remains visibly **Provider mapping not reviewed** instead of being guessed.
- Exact provider IDs—not policy display names or substrings—join observed settings to desired state.
- A setting is called missing only when its mapping is reviewed and collection evidence is complete.
  Unsupported values, parser gaps, unreviewed mappings, and unevaluated resources remain distinct.
- Current and immediately prior sanitized live snapshots can show new, resolved, and unchanged
  technical drift without retaining a tenant data lake.
- Production deployment accepts only a reviewed sanitized artifact from a successful protected-main
  live audit and verifies its exact snapshot before and after deployment. Synthetic data has no
  production fallback path.
- Evidence Copilot uses fixed `gpt-5.6-terra` in production, bounded sanitized context, strict
  structured output, `store: false`, no tools, rate limits, and deterministic claim/reference
  verification. Generated prose remains generated analysis subject to human review.

The provider exposes no create, update, assign, delete, apply, remediation, or rollback operation. A
Git revert changes reviewed desired-state history; it does not change Intune.

## Run the credential-free demonstration

Python 3.12 or later and Node.js are required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install --no-build-isolation --no-deps .
npm ci --ignore-scripts --no-audit --no-fund
python -m evidenceops run-mission-demo --output-dir build/mission-demo
python -m evidenceops rebuild-static-demo
mkdocs build --strict
npm run validate:worker
npm run dev
```

Local and preview runtimes are explicitly fixture mode and need no tenant or OpenAI credential. The
tracked package under `docs/assets/data/` is deterministically generated synthetic data and is never
accepted by the production deployment workflow.

## Validate

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy
python -m pytest
python -m bandit -r evidenceops scripts -c pyproject.toml
python scripts/check_company_name.py
python scripts/check_secrets.py
python -m pip_audit -r requirements-dev.txt
mkdocs build --strict
python scripts/check_public_artifacts.py site
npm audit --audit-level=moderate
npm run validate:worker
git diff --check
```

Public CI uses no Microsoft or OpenAI credential. Live collection is a separately protected,
environment-bound workflow on trusted `main` using GitHub OIDC and the documented read-only Graph
permission.

## Safety and privacy boundaries

- Microsoft Graph access is GET-only and limited to the reviewed endpoint families.
- Raw tenant responses, Graph tokens, pseudonymization material, and private evidence are ephemeral
  and never enter the public artifact.
- Unknown public fields fail closed. Public and pre-model egress pass the shared credential and
  sensitive-value catalogs.
- Tenant, user, group, device, policy, assignment, and object identities are excluded or
  non-reversibly pseudonymized before publication.
- The deterministic evidence package is authoritative. AI cannot determine status, approve an
  exception, accept risk, publish, remediate, or decide compliance.
- Browser refresh checks only the current published snapshot; it never authenticates to Graph.

## Scope and limitations

The slice begins with Microsoft Intune and managed Apple platforms while keeping the provider and
evidence contracts vendor-neutral. The macOS inventory contains 98 pinned Level 1 rules, but only
four exact provider mappings are currently reviewed. iOS and iPadOS appear only as sanitized
aggregate posture and are not scored against the macOS baseline. Long-term history, multi-tenancy,
private policy-name presentation, CIS Level 2, broad rule mapping, Apple release intelligence, and
all Intune write capabilities remain deferred.

## Build Week provenance

Before Build Week, EvidenceOps had repository safety foundations and a small synthetic schema proof.
During Build Week, TJ Olnhausen made the product, security, baseline-approval, and external-system
decisions while Codex implemented and tested the provider contracts, live collection boundary,
versioned evidence, deterministic drift, sanitizer, Cloudflare runtime, dashboard, Copilot, and
deployment controls. GPT-5.6 is a bounded runtime explainer, not the evidence engine. The private
`/feedback` Session ID belongs only in submission metadata and must never be committed.

See [Getting Started](docs/getting-started.md), [Architecture](docs/architecture.md),
[Security Model](docs/security-model.md), and the [Build Week demo package](docs/build-week/demo-package.md).

Copyright 2026 TMCO Consulting, LLC. EvidenceOps is licensed under the
[Apache License 2.0](LICENSE). The pinned baseline is derived from the NIST macOS Security Compliance
Project under its upstream terms; see [NOTICE](NOTICE) and the recorded source hashes for attribution.
