# Build Week Demo Package

Use the [final video runbook](video-runbook.md) for the production recording. This page retains the
submission description, technical summary, and backup material.

## Less-than-three-minute script

**0:00–0:20 — thesis.** Open Provifact Mission Control. “Regulated endpoint teams should not
reconstruct months of change history before an audit. Provifact turns approved configuration,
read-only observation, deterministic drift, and constrained AI explanation into one traceable
evidence chain.” Point out the `LIVE SANITIZED TENANT DATA` badge and explain that raw tenant data
never crossed the publication boundary.

**0:20–0:45 — approved baseline.** Show the 98-rule pinned macOS CIS Level 1 demo inventory, its
mSCP revision and hashes, and the four-rule alignment denominator. Explain that the internal TMCO Consulting
approval is for technical drift detection—not CIS certification.

**0:45–1:20 — deterministic drift.** Open the highest-priority genuine live finding; do not
predetermine its setting or state. Show expected/observed values, assignment summary, exact provider
definition, source evidence IDs, fingerprints, framework cross-references, limitations, and
read-only guidance.

**1:20–1:45 — complete evidence, honest gaps.** Show the Mac/iPhone/iPad aggregate, application
health, resources not currently evaluated, and collection gaps. Explain that iOS/iPadOS is visible but not scored
against a macOS baseline and that unavailable evidence remains visible.

**1:45–2:20 — constrained GPT-5.6.** Open the site-wide Provifact Copilot and ask “What requires my
attention?” Show cited evidence, typed-claim verification, prose quarantine, and human-review
language. Production uses fixed `gpt-5.6-terra`; local/preview fixture mode must be labeled as no
model call.

**2:20–2:45 — security boundary.** Show `/api/status`, then summarize GET-only Graph, GitHub OIDC,
private normalized evidence, allowlist publication, Cloudflare rate limits, server-side OpenAI
secret, `store: false`, no tools, and no BYOK.

**2:45–2:55 — close.** “Provifact does not change Intune and does not decide compliance. It makes
approved intent, observed state, drift, limitations, and evidence references reviewable before the
audit.”

## Click-by-click runbook

1. Open `https://evidenceops.tmcoconsulting.com/evidence-dashboard/`.
2. Confirm the data-mode badge says `LIVE SANITIZED TENANT DATA`, the assistant says OpenAI mode,
   and the banner does not indicate stale or invalid evidence.
3. Point to Findings requiring review, New drift, Resolved, Collection gaps, and Evaluated settings.
4. Read the denominator explanation immediately below the cards.
5. Under Findings requiring review, choose `high` in Severity.
6. Open one row with keyboard Enter or mouse click; close the dialog after showing its traceability
   chain.
7. Open Changes and show the truthful current/prior result.
8. Scroll to Managed Apple posture and Coverage and blind spots; show aggregate posture,
   collection coverage, and resources not currently evaluated.
9. Show Framework cross-references and read its non-certification warning.
10. Show Collection health, including endpoint API versions, the beta Settings Catalog label, and the
    collection gap.
11. Open Provifact Copilot, choose What requires my attention?, and inspect the evidence links and
    verifier state.
12. Ask the unsupported question from the backup card below and show insufficient evidence only if
    time permits.
13. Open `/api/status` in a second tab only if time permits; do not open Cloudflare live-tail.

## Suggested DevPost project description

Provifact is a continuous compliance-evidence platform for regulated endpoint teams. It connects
a Git-approved security baseline to read-only Microsoft Intune collection, deterministic drift,
privacy-safe evidence publication, a Cloudflare-hosted Mission Control dashboard, and GPT-5.6
explanations that remain subordinate to verified evidence and human judgment. The Build Week demo
focuses on managed Apple posture and a pinned macOS baseline while keeping provider contracts
vendor-neutral.

## Suggested DevPost technical description

Provifact uses a GET-only Python Microsoft Graph provider with bounded concurrency, pagination,
retry, and per-endpoint gaps. A pinned mSCP macOS CIS Level 1 inventory is hash-verified and four
settings are mapped through reviewed, deterministic identifiers. The engine emits stable evidence
IDs, canonical fingerprints, assignment/value/conflict findings, freshness, history deltas, and
framework crosswalks. A fail-closed allowlist creates the only public/model-visible package.
Cloudflare Workers Static Assets serves the dashboard; `/api/ask` prefilters the sanitized package,
calls only fixed `gpt-5.6-terra` with structured output and `store: false`, and rejects any answer
whose typed claims or citations disagree with deterministic evidence. Local/preview fixture mode
requires no model credential; production evidence is a separately reviewed live sanitized
projection with fixed-model OpenAI mode.

## How Codex was used

Codex served as the primary implementation collaborator: inspecting the existing architecture,
implementing typed provider/evidence boundaries, adding adversarial tests, integrating the pinned
baseline, building Mission Control and Worker contracts, running the validation suites, and
recording decisions and limitations. TJ retained product, security, approval, external-account,
and merge authority. A private `/feedback` Session ID must be preserved for submission and must not
be committed.

## How GPT-5.6 is used at runtime

GPT-5.6 Terra receives only an intent-specific subset of a sanitized evidence package. It may
explain deterministic findings in plain language and suggest human-review questions. It receives no
raw Graph data, identifiers, credentials, or tools; it cannot modify Intune, select finding status,
grant an exception, publish, or determine compliance. Its structured output is verified against
exact typed claims and allowlisted evidence references. Free prose is always labeled generated and
quarantined.

## Before and after Build Week

| Before | Build Week extension |
| --- | --- |
| Secure repository and schema-v1 synthetic proof | Comprehensive GET-only Apple resource-family collector |
| Two normalized macOS fields | Pinned 98-rule baseline with four exact reviewed mappings, one explicit unreviewed mapping, and assignment/conflict drift |
| Static walkthrough | Dynamic responsive Mission Control generated from a strict public package |
| One full-package narrative contract | Prefiltered natural-language assistant with exact typed-claim verification |
| Local/static hosting plan | Cloudflare Worker, custom domain, CSP, rate limits, and encrypted project key |
| No history view | Current/prior sanitized snapshot delta without adding a database |

## Screenshot checklist

- [ ] Mission Control header with live sanitized data badge and OpenAI narrative label
- [ ] Executive overview and denominator explanation
- [ ] FileVault traceability dialog
- [ ] Assignment or conflict finding
- [ ] Mac/iPhone/iPad aggregate posture
- [ ] Unmapped objects and collection gap
- [ ] Framework technical-evidence warning
- [ ] Verified live `gpt-5.6-terra` answer with citations
- [ ] Insufficient-evidence answer
- [ ] Mobile viewport showing responsive cards/table
- [ ] `/api/status` live sanitized response with OpenAI narrative mode and no administrative
      metadata

## Backup synthetic-demo procedure

If the custom domain or external service is unavailable:

```bash
python -m evidenceops run-mission-demo --output-dir build/mission-demo
python scripts/check_public_artifacts.py build/mission-demo
python -m evidenceops rebuild-static-demo
mkdocs build --strict
python -m http.server 8000 --directory site
```

Open `http://localhost:8000/evidence-dashboard/`. The dashboard remains deterministic. The
assistant’s static fixture presentation is available, but same-origin Worker API calls require
`npm run dev` instead of the simple file server.

## Final submission checklist

- [x] CI and Worker validation pass on the reviewed pull request
- [x] Public artifact scan passes over the exact deployed `site/`
- [x] Custom domain, TLS, headers, desktop, and mobile behavior are rechecked
- [x] Production data mode and model-call label match reality
- [x] No private/raw artifact or secret appears in Git, Actions logs, or public assets
- [x] Expanded Graph application permissions and admin consent are independently verified
- [x] Protected trusted-main Intune audit succeeds, or the live limitation is disclosed
- [x] One bounded GPT-5.6 response succeeds, or fixture-only status is disclosed
- [ ] TJ reviews all commits after the last human-reviewed checkpoint
- [ ] Demo video and screenshots use no tenant identifiers
- [ ] DevPost text avoids certification or compliance-verdict claims
- [ ] Run `/feedback` in the primary Codex task and preserve the returned Session ID privately
- [ ] Do not put the Session ID in public source control unless competition rules explicitly require it

## Backup unsupported question

Ask: “Who approved the annual corporate risk assessment?” The expected response is exactly:

> Provifact does not have sufficient collected evidence to answer this question.
