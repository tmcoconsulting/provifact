# Codex Collaboration

## Project record

- **Project:** Provifact
- **Track:** Developer Tools
- **Project start:** 2026-07-18
- **Phase:** Phase 1 — narrow read-only Intune-to-verified-narrative proof
- **Primary implementation thread:** This OpenAI Build Week Codex task
- **Supporting implementation threads:** None during Phase 0 or this Phase 1 implementation

## Human decisions

The human operator established the product thesis, Intune/Apple starting scope, vendor-neutral
direction, public-repository requirement, Apache License preference, TMCO Consulting, LLC ownership
intent, read-only security posture, synthetic/public-data constraint, human-approval boundary, and
Phase 0 completion criteria.

## Codex contributions

Codex, using the requested GPT-5.6 Sol execution profile, implemented Phase 0 in this primary thread.
In Phase 1 it inspected and validated the existing repository, researched official Microsoft and
OpenAI contracts, implemented schema/provider/publication/narrative/verifier/CLI code, extended the
synthetic static demo, updated the threat model, and executed the validation recorded in the Phase
1 document. It then remediated four validated Codex Security findings in place and recorded the
Cloudflare-next deployment decision. After TJ reviewed and committed that checkpoint, Codex added
the separately reviewable Worker/static-assets runtime, same-origin API contracts, workerd tests,
CI validation, protected workflow support, Cloudflare preview/production deployments, custom
domain, secure OpenAI-to-Worker key transfer, and external validation. No supporting agent or
unrelated repository supplied project code.

The local Codex CLI reported version `0.145.0-alpha.18`. A current official Codex manual fetched
during Phase 0 documented the GPT-5.6 Sol family and Extra High/Max reasoning controls. The manual
also makes clear that model availability is selected in the Codex surface; this repository does not
attempt to prove account-wide API entitlement.

## Runtime contribution

The optional adapter asks GPT-5.6 to draft concise structured analysis from a bounded sanitized
package. It has no tools and cannot collect, publish, remediate, change a status, approve an
exception, or decide compliance. A deterministic verifier checks exact finding coverage and typed
status claims; it quarantines all unrestricted prose before human review. Public CI and the local
static demo use an offline fixture and require no API key. The Worker OpenAI transport is mocked in
tests. An initial bounded production attempt returned capacity unavailable; a later single bounded
request succeeded against fixed `gpt-5.6-terra`, passed exact typed-claim verification, quarantined
all generated prose, and required human review. Production was then returned to fixture narrative
mode. The deployed evidence package is now a separately reviewed, fail-closed sanitized live
projection; deterministic evidence remains authoritative.

## Authorship and ownership

Codex is an implementation tool, not the legal author or copyright owner. TMCO Consulting, LLC
asserts copyright only in its original Provifact work. The project does not claim ownership of
Apple, Microsoft, NIST, CIS, CMMC, mSCP, or third-party repositories, standards, baselines, or
documentation.

## Session metadata

**Primary `/feedback` Session ID:** PRIVATE SUBMISSION METADATA — intentionally not stored in public
source control.

At the end of Phase 0, the operator should run `/feedback` in the primary Codex thread and preserve
the returned identifier in the private Build Week submission record unless the competition rules
explicitly require public disclosure.

## Commit trailers

Build Week milestone commits use:

```text
Codex-Assisted: GPT-5.6 Sol / Max
Build-Week-Phase: Phase-1
Human-Reviewed: TJ Olnhausen
```

Autonomous changes made after the authorized Worker checkpoint use `Human-Review: Required` until
TJ completes final pull-request review.

The trailers record the collaboration process; they do not transfer copyright or replace human
review.
