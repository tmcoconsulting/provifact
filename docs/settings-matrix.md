# CIS Level 1 Implementation Plan

<div class="matrix-intro">
  <div>
    <p class="matrix-kicker">Setting-level technical evidence</p>
    <h2>Start with all 98 approved rules, then separate proven drift from work still to plan.</h2>
    <p>
      This view begins with the complete pinned CIS Level 1 inventory. Exact reviewed Intune joins
      produce deterministic technical states; every other rule remains visible as implementation or
      provider-mapping work. It does not issue a certification or organizational-compliance verdict.
    </p>
  </div>
  <div class="matrix-intro-actions">
    <a class="md-button md-button--primary" href="../evidence-dashboard/">Open Mission Control</a>
    <a class="md-button" href="../audit-methodology/">Read the methodology</a>
  </div>
</div>

<div class="matrix-scope-note">
  <strong>Current approved baseline:</strong> the pinned macOS 26 CIS Level 1 demo profile.
  CIS Level 2 is shown explicitly as <em>not loaded</em>; Provifact does not infer Level 2 coverage
  from Level 1 or from another framework's cross-reference.
</div>

<div id="settings-matrix" data-settings-matrix aria-busy="true">
  <div class="matrix-banner" data-matrix-banner data-state="loading">
    Loading the fingerprint-verified Mission package…
  </div>

  <div class="matrix-summary" data-matrix-summary aria-live="polite"></div>
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
      <span>Framework mapping</span>
      <select data-matrix-framework>
        <option value="">All frameworks</option>
        <option value="cis_benchmark">CIS Level 1</option>
        <option value="cis_lvl2">CIS Level 2</option>
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

The default table shows every approved Level 1 rule. Select **Review details** for the exact
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

A private, access-controlled deployment can preserve a reviewed parent-policy reference and friendly
name after a separate data-classification and authorization review. That parent-policy join is the
next data-model priority; the public matrix never guesses it from a display name.

## Coverage limits

- The complete 98-rule CIS Level 1 inventory is visible by default. Only explicitly reviewed exact
  provider mappings enter the technical-alignment denominator.
- **Implementation planning required** means the rule belongs to the approved inventory but its
  Intune Settings Catalog, custom-profile, script/agent, or alternate-evidence path has not been
  approved. It is a backlog state—not a failed control.
- **Provider mapping review required** means desired metadata exists but an exact Intune definition
  ID has not yet passed review.
- CIS Level 2 is not loaded in the current repository and is never inferred.
- STIG, NIST, and CMMC cells are cross-reference identifiers associated with the setting. They are
  supporting technical evidence, not independent baseline scores.
- Unsupported rules say so directly. AI does not create missing mappings or fill evidence gaps.
- Provifact remains GET-only and cannot change, assign, or remediate an Intune policy.
