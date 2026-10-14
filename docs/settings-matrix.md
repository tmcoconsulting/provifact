# Baseline Comparison & Implementation Plan

Rows come from the canonical public matrix projection bound to the displayed Mission snapshot.
Every approved row preserves its baseline profile and benchmark version. Private policy names and
stable private policy lineage remain excluded; see the
[lineage and authorization contract](operations/private-policy-lineage.md).

<div class="matrix-intro">
  <div>
    <p class="matrix-kicker">Setting-level technical evidence</p>
    <h2>Compare the approved company baseline to public technical profiles—without inventing a compliance score.</h2>
    <p>
      Begin with all 98 TMCO Consulting-approved rules, then switch among the pinned CIS, DISA STIG, NIST,
      CMMC, CNSSI, HICP, and NLLMAP technical profiles. Exact rule-ID overlap shows what the company
      baseline includes and what it would need to consider; only reviewed Intune joins produce
      deterministic posture. A profile comparison is not a certification or organizational verdict.
    </p>
  </div>
  <div class="matrix-intro-actions">
    <a class="md-button md-button--primary" href="../evidence-dashboard/">Open Mission Control</a>
    <a class="md-button" href="../audit-methodology/">Read the methodology</a>
    <a class="md-button" href="../operations/approved-baseline/">Change the approved target safely</a>
  </div>
</div>

<div class="matrix-scope-note">
  <strong>Current approved baseline:</strong> the pinned TMCO Consulting macOS 26 technical baseline.
  Reference profiles come from the same pinned public NIST mSCP revision. The comparison is exact
  profile membership—not a CIS, NIST, DoD, CMMC, HHS, or assessor score.
</div>

<div id="settings-matrix" data-settings-matrix aria-busy="true">
  <div class="matrix-banner" data-matrix-banner data-state="loading">
    Loading the fingerprint-verified Mission package…
  </div>

  <div class="matrix-summary" data-matrix-summary aria-live="polite"></div>
  <section class="matrix-comparison" aria-labelledby="matrix-comparison-title">
    <div class="matrix-comparison-heading">
      <div>
        <p class="matrix-kicker">Approved baseline versus reference profile</p>
        <h2 id="matrix-comparison-title">Technical profile overlap</h2>
      </div>
      <label>
        <span>Compare TMCO Consulting Approved to</span>
        <select data-matrix-profile aria-describedby="matrix-comparison-boundary"></select>
      </label>
    </div>
    <div class="matrix-comparison-summary" data-matrix-comparison-summary aria-live="polite"></div>
    <div class="matrix-comparison-gaps" data-matrix-comparison-gaps></div>
    <p id="matrix-comparison-boundary" class="matrix-comparison-boundary">
      Exact rule-ID membership only. “Included” does not mean implemented, observed, satisfied,
      compliant, or assessed. Deterministic Intune evidence remains a separate state.
    </p>
  </section>
  <div class="matrix-plan" data-matrix-plan aria-label="Implementation backlog by baseline section"></div>

  <form class="matrix-controls" data-matrix-controls>
    <label>
      <span>Search settings, controls, or evidence</span>
      <input type="search" data-matrix-search placeholder="FileVault, SC-28, APPL-26…" autocomplete="off">
    </label>
    <label>
      <span>Technical state</span>
      <select data-matrix-outcome>
        <option value="">All states</option>
      </select>
    </label>
    <label>
      <span>Baseline section</span>
      <select data-matrix-section>
        <option value="">All sections</option>
      </select>
    </label>
    <label>
      <span>Evidence cross-reference</span>
      <select data-matrix-framework>
        <option value="">All cross-references</option>
        <option value="cis_benchmark">CIS Level 1</option>
        <option value="stig">STIG</option>
        <option value="nist_800_171r3">NIST SP 800-171</option>
        <option value="nist_800_53r5">NIST SP 800-53</option>
        <option value="cmmc">CMMC</option>
      </select>
    </label>
    <label class="matrix-checkbox">
      <input type="checkbox" data-matrix-mapped-only>
      <span>Limit to deterministically evaluated rules</span>
    </label>
    <button type="button" class="md-button" data-matrix-reset>Reset filters</button>
  </form>

  <p class="matrix-result-count" data-matrix-count aria-live="polite"></p>

  <div class="matrix-table-wrap" tabindex="0" aria-label="Compact Intune setting and baseline matrix">
    <table class="settings-matrix" data-matrix-table>
      <thead></thead>
      <tbody></tbody>
    </table>
  </div>

  <div class="matrix-empty" data-matrix-empty hidden></div>

  <dialog class="matrix-dialog" data-matrix-dialog aria-labelledby="matrix-dialog-title">
    <form method="dialog"><button class="matrix-dialog-close" aria-label="Close setting detail">Close</button></form>
    <div data-matrix-detail></div>
  </dialog>
</div>

<noscript>
  JavaScript is required to render the matrix from the current Mission package. The raw public-safe
  package remains available at <code>/assets/data/mission-control.json</code>.
</noscript>

## How to read the matrix

The default table shows every TMCO Consulting-approved rule. Changing the comparison profile also adds its
reference-only rules so the adoption gap is visible rather than hidden. Select **Review details** for the exact
provider definition ID when one is approved, public-safe policy references, evidence IDs,
fingerprints, deterministic guidance, and limitations. Use **Limit to deterministically evaluated
rules** to reduce the view to the four exact Intune joins.

A green technical-evidence state means the collected setting matched the approved target and had
normalized assignment evidence. It does **not** prove the organization satisfies the mapped control.
A drift state means the setting-level evidence needs review; interviews, procedures, scope,
operating effectiveness, and assessor judgment may still be required for every framework.

## Why the public site does not show tenant policy names

The production package is deliberately sanitized. Tenant display names, object IDs, group names,
and assignment identities are excluded or pseudonymized before publication. The matrix therefore
shows public-safe setting/evidence references rather than claiming to expose the tenant's actual
Intune display names.

The private collector preserves a stable parent-policy reference and friendly name under the
documented classification and retention boundary. Authenticated name presentation still requires
a separately reviewed deployment. The public matrix never guesses lineage from a display name.

## Coverage limits

- The complete 98-rule TMCO Consulting-approved inventory is visible by default. Only explicitly reviewed exact
  provider mappings enter the technical-alignment denominator.
- Sixteen pinned public mSCP reference profiles are loaded for exact rule-membership comparison,
  including CIS Levels 1 and 2, DISA STIG, NIST SP 800-171 and SP 800-53 impact levels, CMMC Levels
  1 and 2, CNSSI impact levels, HICP, NLLMAP, and CIS Controls v8.
- **Implementation planning required** means the rule belongs to the approved inventory but its
  Intune Settings Catalog, custom-profile, script/agent, or alternate-evidence path has not been
  approved. It is a backlog state—not a failed control.
- **Provider mapping review required** means desired metadata exists but an exact Intune definition
  ID has not yet passed review.
- STIG, NIST, CMMC, and other profile membership is loaded from the pinned mSCP source. Separate
  cross-reference cells are identifiers associated with an evaluated setting. Both are supporting
  technical evidence, not independent baseline scores.
- Unsupported rules say so directly. AI does not create missing mappings or fill evidence gaps.
- Provifact remains GET-only and cannot change, assign, or remediate an Intune policy.
