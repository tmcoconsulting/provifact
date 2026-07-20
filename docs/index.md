<div class="evidence-hero">
  <div class="hero-kicker"><img src="assets/images/provifact-mark.svg" alt="" width="42" height="42"> Provifact™ by TMCO Consulting</div>
  <h1>From approved change to audit-ready proof.</h1>
  <p>
    Provifact collects managed-Apple configuration read-only, evaluates mapped settings
    deterministically, and publishes a sanitized evidence package that reviewers can trace without
    granting the product Intune write authority.
  </p>
  <div class="hero-actions">
    <a class="primary" href="evidence-dashboard/">Open Mission Control</a>
    <a class="secondary" href="settings-matrix/">Compare settings and baselines</a>
  </div>
</div>

<p class="provifact-brand-note">Continuous, deterministic endpoint evidence—without granting the product Intune write authority.</p>

<div class="synthetic-banner">
Production serves a reviewed package labeled `LIVE SANITIZED TENANT DATA`. Tenant, device, user,
group, assignment, and credential identities are not public. Production Provifact Assistant uses only
fixed `gpt-5.6-terra` with bounded sanitized context; local and preview builds remain fixture mode.
</div>

## Choose the view that answers your question

<div class="evidence-grid">
  <div class="evidence-card">
    <h3>Mission Control</h3>
    <p>Start with alignment, drift, collection gaps, device aggregates, changes, and evidence traces.</p>
    <p><a href="evidence-dashboard/">Open the dashboard →</a></p>
  </div>
  <div class="evidence-card">
    <h3>Baseline Implementation Plan</h3>
    <p>See all 98 approved Level 1 rules, the four exact Intune joins, deterministic drift, and every management path still to plan.</p>
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
| macOS baseline inventory | 98 pinned CIS Level 1 rules with authoritative mSCP titles | Four settings have reviewed exact provider mappings; 94 remain visible implementation work |
| Intune collection | Comprehensive GET-only managed-Apple resource families | No create, update, assign, remediate, or rollback method exists |
| Baseline implementation plan | All 98 rules by default, plus observed value, target, state, evidence, and required action | Planning work is not mislabeled as drift or a failed control |
| Public dashboard | Live sanitized aggregate package on Cloudflare | Tenant policy display names and object identities are intentionally excluded |
| Assistant | Site-wide bounded `/api/ask`, exact typed-claim verification, prose quarantine | Production is fixed-model OpenAI mode; local/preview are fixture mode; neither can decide compliance |
| History | Current/prior sanitized snapshot delta | No persistent D1/KV/R2 history store yet |

## What the framework columns mean

A mapped setting can support technical evidence for several framework identifiers. For example, a
FileVault setting may be linked to CIS, STIG, NIST, and CMMC identifiers while sharing one observed
Intune value. Provifact reports whether that **setting-level evidence** matches the approved target.
It does not convert that result into a framework-wide pass, certification, or assessor conclusion.

The [baseline implementation plan](settings-matrix.md) makes four distinctions visible:

- **Mapped and aligned:** collected technical evidence matches the approved target.
- **Mapped and drifting:** a deterministic value, assignment, conflict, or collection condition
  requires review, with an exact non-mutating change instruction.
- **Not loaded or not mapped:** Provifact says so directly rather than asking AI to fill the gap.
- **Implementation planning required:** the rule is approved inventory, but the team must still
  choose and approve a Settings Catalog, custom-profile, script/agent, or alternate-evidence path.

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

Provifact is a technically complete Phase 1 vertical slice, not a finished enterprise compliance
platform. The highest-value next work is to work down the now-visible 94-rule implementation
backlog, preserve an approved parent-policy reference in the private model, load and review
additional baselines such as CIS Level 2, expand evaluated evidence safely, and add authenticated
sanitized history only after retention and access-control design.

The existing Cloudflare Worker plus Static Assets architecture is sufficient for the present
read-mostly product. A dedicated application frontend and D1-backed history become justified when
Provifact adds authenticated users, private policy names, multi-tenant state, approvals, or
long-running workflows—not merely because GitHub Pages was retired.
