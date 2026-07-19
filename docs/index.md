<div class="evidence-hero">
  <div class="hero-kicker">Continuous compliance evidence</div>
  <h1>Make every approved change audit-ready.</h1>
  <p>
    EvidenceOps connects desired configuration, Git review history, read-only endpoint inventory,
    deterministic drift analysis, exceptions, compliance mappings, and grounded narrative into one
    traceable evidence lifecycle.
  </p>
  <div class="hero-actions">
    <a class="primary" href="live-demo/">Explore the synthetic demo</a>
    <a class="secondary" href="architecture/">Read the architecture</a>
  </div>
</div>

<div class="synthetic-banner">
Phase 1 is a bounded read-only Apple evidence proof. Mission Control is generated from a clearly
labeled synthetic Mac, iPhone, and iPad environment; no production tenant data is present. The
expanded collector and permission manifest are implemented and mocked, while the protected live
audit remains outstanding. Cloudflare serves this synthetic fixture at
`evidenceops.tmcoconsulting.com`; fixture mode makes no OpenAI request.
</div>

## The problem

Regulated endpoint teams often have the configuration they intended, the inventory they observe,
and the approvals they received—but in different systems and at different points in time. Before
an audit, they reconstruct the story manually. Screenshots, exports, tickets, and pull requests are
assembled after the fact, when context is already missing.

EvidenceOps starts from a different thesis:

> Every approved configuration change should produce traceable, audit-ready evidence.

## One evidence lifecycle

<div class="evidence-grid">
  <div class="evidence-card">
    <h3>1. Approve intent</h3>
    <p>Desired configuration and compliance mappings are reviewed through Git pull requests.</p>
  </div>
  <div class="evidence-card">
    <h3>2. Collect read-only</h3>
    <p>A provider adapter reads observed state without exposing create, update, or delete methods.</p>
  </div>
  <div class="evidence-card">
    <h3>3. Evaluate deterministically</h3>
    <p>Normalized desired and observed values produce reproducible drift findings and fingerprints.</p>
  </div>
  <div class="evidence-card">
    <h3>4. Sanitize before publishing</h3>
    <p>Explicit field classification, pseudonymization, and output scans stop unsafe public data.</p>
  </div>
  <div class="evidence-card">
    <h3>5. Explain with boundaries</h3>
    <p>Optional GPT-5.6 output is structured, evidence-referenced, and quarantined for human review.</p>
  </div>
</div>

## Evidence first, narrative second

| Layer | Authority | Phase 1 behavior |
| --- | --- | --- |
| Approved baseline and desired state | Git history, pinned mSCP revision, and TMCO demo approval | 98-rule macOS inventory; five rules mapped |
| Observed state | Read-only provider response | Expanded GET-only Apple/Intune adapter; live validation pending |
| Drift result | Deterministic comparison | Assignment, value, conflict, gap, and unsupported states |
| Public artifact | Sanitization policy and policy gate | Implemented and tested |
| Assistant | GPT-generated analysis grounded in prefiltered evidence | Deterministic fixture by default; fixed Terra model path is opt-in |
| Narrative claims | Typed deterministic claim codes | Verified; free prose quarantined |
| Acceptance | Human reviewer | Required boundary |

A model may help summarize why a set of deterministic findings matters. It cannot silently change
a finding, grant an exception, approve a control, or claim that an audit requirement is satisfied.

## Initial scope and vendor-neutral direction

The first live integration is Microsoft Intune with managed Apple platforms. The core
objects and provider interface do not contain Intune-specific write semantics, allowing later Jamf
and Omnissa Workspace ONE adapters to normalize into the same evidence engine.

## Who uses EvidenceOps?

- **Auditors** trace a claim to a deterministic finding, approved change, and collection boundary.
- **Engineers** review desired configuration and evidence-impacting changes in Git.
- **Security leaders** see control posture, drift, exceptions, provenance, and limitations together.
- **Endpoint administrators** investigate normalized drift without granting EvidenceOps mutation
  rights in the management plane.

## Privacy and operating guarantees

- No real tenant or device data is included in the repository or site.
- Microsoft Graph access is read-only and least-privilege.
- Raw live responses are never eligible for public static output.
- Unknown fields stop sanitization until a human classifies them.
- Pseudonymization key material stays outside the repository.
- Fork-originated workflows never receive privileged collection credentials.

Read the [data-handling policy](data-handling.md), [threat model](threat-model.md), and
[audit methodology](audit-methodology.md) for the precise boundary.

## Current limitations

- Live TMCO Microsoft Graph/Intune validation has not been performed.
- The site uses generated evidence objects derived only from curated synthetic input.
- Only five macOS rules have approved provider mappings; the remaining inventory is visible but unsupported.
- iOS/iPadOS has no approved baseline and is deliberately not scored against macOS CIS.
- Full exception persistence, signed manifests, and auditor exports are deferred.
- Cloudflare same-origin API routes are operational in production with synthetic fixture data only.
- A new project service-account key is installed as a Worker secret; bounded live response validation remains outstanding.
- GitHub Pages is disabled; local `site/` output is deployed as Cloudflare Workers Static Assets.
- Phase 0 was validated on Python 3.14 locally and targets Python 3.12 in CI; neither result is a
  production-readiness or compliance certification.

## Build Week contribution

Codex with the GPT-5.6 Sol execution profile established the Phase 0 code, tests, workflows, and
documentation in the primary implementation thread under human direction. Phase 1 adds a bounded
GPT-5.6 adapter, exact deterministic claim verification, and prose quarantine; the public demo uses
an offline fixture and makes no model request. See
[Codex collaboration](build-week/codex-collaboration.md).
