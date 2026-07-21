# Provifact™ by TMCO Consulting

**From approved change to audit-ready proof.**

<p align="center">
  <img src="docs/assets/images/provifact-social-card.png" alt="Provifact — from approved change to audit-ready proof" width="900">
</p>

[![CI](https://github.com/tmcoconsulting/provifact/actions/workflows/ci.yml/badge.svg)](https://github.com/tmcoconsulting/provifact/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**Provifact turns approved endpoint changes into traceable audit evidence—continuously,
read-only, and without letting AI become the authority.**

Regulated teams can manage thousands of endpoint settings and still spend weeks before an audit
reconstructing what was intended, what was observed, who approved it, what changed, and which
evidence supports the conclusion. Provifact joins those facts into one reviewable chain:

> **Git-approved intent → Microsoft Graph GET-only observation → deterministic drift → sanitized
> proof → bounded GPT-5.6 explanation → human judgment**

[**Open the live Mission Control**](https://provifact.tmcoconsulting.com/evidence-dashboard/) ·
[**Follow the judge path**](docs/judge-guide.md) ·
[**Inspect the architecture**](docs/architecture.md) ·
[**Run it locally**](#run-the-credential-free-demonstration)

## Why enterprises need this

| Enterprise problem | Provifact response |
| --- | --- |
| Audit evidence is assembled after the fact from MDM consoles, tickets, screenshots, Git history, spreadsheets, and memory | Produce a versioned evidence chain as approved configuration and observed state change |
| A dashboard score can hide unsupported controls, incomplete collection, or guessed mappings | Keep aligned, drifting, unsupported, unreviewed, unevaluated, and collection-gap states distinct |
| Granting an evidence tool write authority expands operational and security risk | Use Microsoft Graph GET-only collection; no create, update, assign, remediate, or rollback method exists |
| Sending raw tenant context to a model creates privacy and authority problems | Publish through an allowlist, scan the sanitized package, and send GPT-5.6 only bounded evidence |
| AI-generated prose can sound authoritative even when it is wrong | Keep deterministic findings authoritative, verify typed claims and references, quarantine prose, and require human review |

Provifact is designed for endpoint engineering, security, GRC, managed-service, and assessment-support
teams that need to answer a simple question quickly: **What proof do we have for this approved
configuration state?**

## See the product in 90 seconds

1. Open [Mission Control](https://provifact.tmcoconsulting.com/evidence-dashboard/) and confirm the
   evidence-mode banner, approved baseline, freshness, deterministic denominator, drift, backlog, and
   collection gaps.
2. Open a finding and follow the approved target, observed value, exact provider definition,
   assignment evidence, evidence IDs, fingerprint, and read-only operator guidance.
3. Open the [Baseline Plan](https://provifact.tmcoconsulting.com/settings-matrix/) to see all 98
   approved Level 1 rules. Four exact Intune joins are currently evaluated; the other 94 remain
   visible implementation work rather than fabricated failures.
4. Ask Provifact Assistant **“What requires my attention?”** The Worker selects a small sanitized
   context for fixed `gpt-5.6-terra`, attaches authoritative claims and references, rejects unsupported
   verdict language, and keeps generated prose subject to human review.
5. Finish with [Evidence health and privacy](https://provifact.tmcoconsulting.com/evidence-dashboard/#evidence):
   raw tenant responses are not public, production has no synthetic fallback, and Provifact has no
   Intune write capability.

## What makes Provifact different

- **Deterministic before generative.** A model never selects finding status, calculates drift,
  approves an exception, accepts risk, publishes evidence, or decides compliance.
- **Honest coverage.** The current macOS plan shows all 98 approved rules, evaluates only four exact
  reviewed provider mappings, and exposes the 94-rule mapping and implementation backlog.
- **Read-only by construction.** The provider and transport expose collection and `GET` only. A Git
  revert changes reviewed desired-state history; it does not change Microsoft Intune.
- **Privacy-safe publication.** Public output is reconstructed from approved fields, fingerprinted,
  scanned, reviewed, and deployed only from an exact protected-main audit artifact.
- **Evidence-bounded AI.** Production pins `gpt-5.6-terra`, uses `store: false`, no tools, bounded
  context and output, rate limits, structured output, and deterministic post-verification.
- **Vendor-neutral core.** Microsoft Intune and managed Apple platforms are the first implemented
  provider slice; the evidence, publication, and verification contracts are designed for additional
  endpoint platforms.

## Current Build Week proof

The Phase 1 vertical slice connects the **TMCO Consulting macOS CIS Level 1 Demo Baseline** in Git to
read-only Microsoft Intune collection, deterministic technical drift, a reviewed live sanitized
Mission package, current/prior snapshot comparison, a Cloudflare-hosted operational dashboard, and
Provifact Assistant.

The approved baseline is pinned to a reviewed NIST macOS Security Compliance Project revision and
hashes. That approval supports technical drift detection; it is **not** CIS certification, a CMMC
assessment result, a C3PAO conclusion, or an organizational compliance verdict.

The verified production record is in
[Judge-Readiness Validation](docs/build-week/judge-readiness-validation.md). Production serves a
scanned package labeled `LIVE SANITIZED TENANT DATA`; tenant, device, user, policy, group,
assignment, credential, and raw Graph identities are excluded. One bounded live `gpt-5.6-terra`
request passed typed-claim and evidence-reference verification, and no Intune mutation was performed.

## What the slice proves

- Four macOS settings have reviewed, exact Microsoft Intune provider-definition mappings. A fifth
  desired setting remains visibly **Provider mapping not reviewed** instead of being guessed.
- Exact provider IDs—not policy display names or substrings—join observed settings to desired state.
- A setting is called missing only when its mapping is reviewed and collection evidence is complete.
  Unsupported values, parser gaps, unreviewed mappings, and unevaluated resources remain distinct.
- Current and immediately prior sanitized live snapshots can show new, resolved, and unchanged
  technical drift without retaining a tenant data lake.
- Production deployment accepts only a reviewed sanitized artifact from a successful protected-main
  live audit and verifies its exact snapshot before and after deployment.
- Synthetic data has no production fallback path.

## Run the credential-free demonstration

Python 3.12 or later and Node.js are required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install --no-build-isolation --no-deps .
npm ci --ignore-scripts --no-audit --no-fund
python -m provifact run-mission-demo --output-dir build/mission-demo
python -m provifact rebuild-static-demo
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
permissions.

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
evidence contracts vendor-neutral. The macOS inventory contains 98 pinned Level 1 rules with titles
from the recorded mSCP revision; four exact provider mappings are currently reviewed. The remaining
94 are a visible onboarding and implementation backlog. iOS and iPadOS appear only as sanitized
aggregate posture and are not scored against the macOS baseline. Long-term history, multi-tenancy,
private policy-name presentation, broader exact provider mapping, Apple release intelligence, and all
Intune write capabilities remain deferred.

External technical profiles—including CIS Level 2, DISA STIG, NIST, and CMMC-oriented mSCP
profiles—are comparison and planning references only. Profile membership is not an approved company
target, framework score, control-satisfaction result, completed assessment, or certification.

## Build Week provenance

Provifact began during Build Week with repository safety foundations and a small synthetic schema
proof. TJ Olnhausen retained the product, security, baseline-approval, external-system, review, and
merge decisions. Codex implemented and tested the provider contracts, live collection boundary,
versioned evidence, deterministic drift, sanitizer, Cloudflare runtime, dashboard, Assistant, and
deployment controls. GPT-5.6 is a bounded runtime explainer, not the evidence engine. The private
`/feedback` Session ID belongs only in submission metadata and must never be committed.

See [Getting Started](docs/getting-started.md), [Architecture](docs/architecture.md),
[Security Model](docs/security-model.md), and the
[Build Week demo package](docs/build-week/demo-package.md).

## Brand and compatibility identifiers

The public product is **Provifact™ by TMCO Consulting**. Phase 1 retains the existing `evidenceops`
Python import, `evidenceops` console command, schema/algorithm identifiers, `EVIDENCEOPS_*`
environment variables, Worker resource name, OpenAI project/key labels, and artifact prefixes as
compatibility identifiers. New operator documentation uses the `provifact` command. The public
repository and hostname are `tmcoconsulting/provifact` and `provifact.tmcoconsulting.com`. The cutover
was proven through the renamed immutable GitHub OIDC subject before the old repository-name trust was
retired. The internal Worker name keeps its encrypted secrets and deployment history.

Copyright 2026 TMCO Consulting, LLC. Provifact™ is a trademark of TMCO Consulting, LLC. The software
is licensed under the [Apache License 2.0](LICENSE). The pinned baseline is derived from the
[NIST macOS Security Compliance Project](https://github.com/usnistgov/macos_security) under its
upstream terms; see [NOTICE](NOTICE) and the recorded source hashes for attribution.
