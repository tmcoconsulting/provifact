# Settings and Baseline Matrix

<div class="matrix-intro">
  <div>
    <p class="matrix-kicker">Setting-level technical evidence</p>
    <h2>See what Intune expresses, which framework identifiers it supports, and what must change.</h2>
    <p>
      This view joins the current sanitized evidence package to the reviewed baseline mappings.
      It reports technical alignment for each mapped macOS setting; it does not issue a framework,
      certification, or organizational-compliance verdict.
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
      <input type="checkbox" data-matrix-mapped-only checked>
      <span>Show reviewed provider mappings only</span>
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

The default table stays compact: setting, observed-to-target value, state, assignment, framework
summary, and action. Select **Review details** for the exact provider definition ID, public-safe
parent policy reference, cross-reference identifiers, evidence IDs and fingerprints, deterministic
operator guidance, and limitations.

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

- The complete 98-rule CIS Level 1 inventory remains visible when **Show reviewed provider mappings
  only** is cleared, but only explicitly reviewed provider mappings enter the technical-alignment
  denominator.
- CIS Level 2 is not loaded in the current repository and is never inferred.
- STIG, NIST, and CMMC cells are cross-reference identifiers associated with the setting. They are
  supporting technical evidence, not independent baseline scores.
- Unsupported rules say so directly. AI does not create missing mappings or fill evidence gaps.
- Provifact remains GET-only and cannot change, assign, or remediate an Intune policy.
