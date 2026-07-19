<div class="evidence-hero">
  <div class="hero-kicker">Continuous endpoint evidence</div>
  <h1>Connect approved intent to observed Intune state.</h1>
  <p>
    EvidenceOps collects managed-Apple configuration read-only, evaluates mapped settings
    deterministically, and publishes a sanitized evidence package that reviewers can trace without
    granting the product Intune write authority.
  </p>
  <div class="hero-actions">
    <a class="primary" href="evidence-dashboard/">Open Mission Control</a>
    <a class="secondary" href="settings-matrix/">Compare settings and baselines</a>
  </div>
</div>

<div class="synthetic-banner">
Production serves a reviewed package labeled `LIVE SANITIZED TENANT DATA`. Tenant, device, user,
group, assignment, and credential identities are not public. The assistant remains in fixture mode
by default, so ordinary public use makes no OpenAI model request.
</div>

## Choose the view that answers your question

<div class="evidence-grid">
  <div class="evidence-card">
    <h3>Mission Control</h3>
    <p>Start with alignment, drift, collection gaps, device aggregates, changes, and evidence traces.</p>
    <p><a href="evidence-dashboard/">Open the dashboard →</a></p>
  </div>
  <div class="evidence-card">
    <h3>Settings &amp; Baselines</h3>
    <p>Compare each mapped Intune setting with CIS, STIG, NIST, and CMMC identifiers and see the required technical change.</p>
    <p><a href="settings-matrix/">Open the matrix →</a></p>
  </div>
  <div class="evidence-card">
    <h3>Runtime Demo</h3>
    <p>Inspect Worker readiness, narrative mode, model-call status, and the bounded API behavior.</p>
    <p><a href="live-demo/">Open the runtime demo →</a></p>
  </div>
</div>

## What the current project does

1. **Approves intent in Git.** A pinned macOS baseline, explicit provider mappings, and approval
   metadata define the technical target.
2. **Collects Microsoft Intune read-only.** The Apple provider uses documented Microsoft Graph GET
   paths and records partial collection failures as visible gaps.
3. **Evaluates deterministically.** Value, assignment, conflict, missing, unsupported, and collection
   states are calculated without a model.
4. **Publishes by allowlist.** A public package is reconstructed from approved fields, fingerprinted,
   scanned, and reviewed before deployment.
5. **Explains within evidence boundaries.** The optional GPT-5.6 path receives only a small sanitized
   context. Typed claims and references are verified; free prose remains subject to human review.

## Current capability at a glance

| Capability | Current state | Important limit |
| --- | --- | --- |
| macOS baseline inventory | 98 pinned CIS Level 1 rules | Five settings have reviewed provider mappings |
| Intune collection | Comprehensive GET-only managed-Apple resource families | No create, update, assign, remediate, or rollback method exists |
| Settings matrix | Observed value, target, state, framework IDs, and required change | CIS Level 2 is not loaded and is never inferred |
| Public dashboard | Live sanitized aggregate package on Cloudflare | Tenant policy display names and object identities are intentionally excluded |
| Assistant | Bounded `/api/ask`, exact typed-claim verification, prose quarantine | Fixture mode is the public default; it cannot decide compliance |
| History | Current/prior sanitized snapshot delta | No persistent D1/KV/R2 history store yet |

## What the framework columns mean

A mapped setting can support technical evidence for several framework identifiers. For example, a
FileVault setting may be linked to CIS, STIG, NIST, and CMMC identifiers while sharing one observed
Intune value. EvidenceOps reports whether that **setting-level evidence** matches the approved target.
It does not convert that result into a framework-wide pass, certification, or assessor conclusion.

The [settings matrix](settings-matrix.md) makes three distinctions visible:

- **Mapped and aligned:** collected technical evidence matches the approved target.
- **Mapped and drifting:** a deterministic value, assignment, conflict, or collection condition
  requires review, with an exact non-mutating change instruction.
- **Not loaded or not mapped:** EvidenceOps says so directly rather than asking AI to fill the gap.

## Security and privacy boundaries

- Microsoft Graph access is GET-only and limited to four documented read permission families.
- Raw Graph responses are not eligible for public output.
- Public and pre-model packages fail closed on unknown fields, credentials, identity values, and
  invalid fingerprints.
- GitHub OIDC supplies a short-lived Entra identity only to a protected main-branch workflow.
- The OpenAI key exists only as a Cloudflare Worker secret; browser BYOK is rejected.
- Every result remains technical evidence subject to human review.

Read the [architecture](architecture.md), [audit methodology](audit-methodology.md), and
[security model](security-model.md) for the full trust boundaries.

## Current limitations and next priorities

EvidenceOps is a technically complete Phase 1 vertical slice, not a finished enterprise compliance
platform. The highest-value next work is to preserve an approved parent-policy reference in the
private model, load and review additional baselines such as CIS Level 2, expand provider mappings
beyond five settings, improve evidence-grounded assistant answers, and add authenticated sanitized
history only after retention and access-control design.

The existing Cloudflare Worker plus Static Assets architecture is sufficient for the present
read-mostly product. A dedicated application frontend and D1-backed history become justified when
EvidenceOps adds authenticated users, private policy names, multi-tenant state, approvals, or
long-running workflows—not merely because GitHub Pages was retired.
