# Evidence Dashboard

<div class="synthetic-banner">
Synthetic evidence only. No tenant, user, group, or managed-device identifier is present.
</div>

<div class="evidence-grid">
  <div class="evidence-card">
    <h3>Deterministic findings</h3>
    <div class="evidence-metric">4</div>
    <div class="evidence-label">schema-v1 records</div>
    <p>One match, one difference, one missing observation, one unevaluated setting.</p>
  </div>
  <div class="evidence-card">
    <h3>Narrative gate</h3>
    <div class="evidence-metric">4 / 0</div>
    <div class="evidence-label">typed claims verified / prose trusted</div>
    <p>Every finding is covered exactly; all generated prose remains quarantined.</p>
  </div>
  <div class="evidence-card">
    <h3>Human authority</h3>
    <div class="evidence-metric">Required</div>
    <div class="evidence-label">approval status</div>
    <p>Verification does not approve evidence or grant an exception.</p>
  </div>
</div>

## Trace one drift result

| Field | Synthetic value | Authority |
| --- | --- | --- |
| Desired-state record | Limit the idle interval; `900` seconds | Reviewed Git fixture |
| Observation | `1800` seconds | Synthetic normalized observation |
| Status | differs from desired state | `evidenceops-drift-v1.0.0` |
| Finding evidence ID | `ev1-81658eeb2a8d8930d646dcaf` | Canonical content identity |
| Collection | `2026-07-18T18:00:00Z`; freshness `unknown` | Fixed fixture metadata |
| Narrative | AI-shaped offline fixture; human review required | Narrative layer |
| Narrative prose | Quarantined, including synonym-based evaluative language | Human review only |
| Final judgment | Not made | Human assessor |

## What each role gets

| Role | Primary view |
| --- | --- |
| Auditor | Evidence IDs, timestamps, fingerprints, limitations, and source links |
| Endpoint engineer | Desired/observed values and deterministic differences |
| Security leader | Scope, freshness, additional evidence, and unresolved human decisions |
| Endpoint administrator | Read-only source trace in the private package; no remediation control |

Configurations may support an assessment objective, but this package does not prove organizational
compliance. Device state, process evidence, scope, operating effectiveness, and assessor judgment
may still be required.
