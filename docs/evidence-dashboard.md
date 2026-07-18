# Evidence Dashboard

<div class="synthetic-banner">
Demonstration data only. The values below are curated and synthetic; no collection workflow ran.
</div>

## Evidence posture

<div class="evidence-grid">
  <div class="evidence-card">
    <h3>Deterministic evidence</h3>
    <div class="evidence-metric">12</div>
    <div class="evidence-label">Evaluated controls</div>
    <p>Reproducible desired-versus-observed comparisons.</p>
  </div>
  <div class="evidence-card">
    <h3>Needs attention</h3>
    <div class="evidence-metric">2</div>
    <div class="evidence-label">Drift findings</div>
    <p>Findings are not remediated automatically.</p>
  </div>
  <div class="evidence-card">
    <h3>Human decisions</h3>
    <div class="evidence-metric">1</div>
    <div class="evidence-label">Approved exception</div>
    <p>Approval, owner, and expiry belong in evidence.</p>
  </div>
</div>

## Control detail shell

| Field | Synthetic example | Authority |
| --- | --- | --- |
| Control reference | `SYN-MAC-002` | Curated demo mapping |
| Desired value | Encryption required | Reviewed desired state |
| Observed value | Requirement not observed | Read-only normalized inventory |
| Status | Drifted | Deterministic comparison |
| Evidence narrative | Not generated in Phase 0 | Future labeled GPT-5.6 analysis |
| Disposition | Awaiting human review | Human approval boundary |

The dashboard will eventually let an auditor trace from a narrative sentence to its deterministic
evidence fingerprint, collection provenance, desired-state commit, approval, and exception. Phase
0 proves the publication and safety foundation, not that end-to-end feature.
