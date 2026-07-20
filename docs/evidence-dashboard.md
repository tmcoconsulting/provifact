---
hide:
  - navigation
  - toc
---

<h1 class="mission-visually-hidden">Provifact™ Mission Control</h1>

<div class="mission-shell" data-mission-control aria-busy="true">
  <header class="mission-commandbar">
    <a class="mission-brand" href="../" aria-label="Provifact home">
      <img class="mission-brand-mark" src="../assets/images/provifact-mark.svg" alt="" width="40" height="40">
      <span><strong>Provifact™</strong><small>by TMCO Consulting</small></span>
    </a>
    <div class="mission-command-status">
      <span class="mission-readonly">READ-ONLY</span>
      <span>Approved change</span><i aria-hidden="true"></i>
      <span>Graph evidence</span><i aria-hidden="true"></i>
      <span>Audit-ready proof</span>
    </div>
    <div class="mission-command-actions">
      <a href="../settings-matrix/">Baseline matrix</a>
      <button type="button" data-open-assistant>Ask Provifact Assistant</button>
    </div>
  </header>

  <div class="mission-console">
    <aside class="mission-rail" aria-label="Mission Control sections">
      <div class="mission-rail-state">
        <span class="mission-pulse" aria-hidden="true"></span>
        <span><strong data-rail-state>VALIDATING</strong><small>Publication gate</small></span>
      </div>
      <nav>
        <a href="#overview"><span>01</span>Command view</a>
        <a href="#posture"><span>02</span>Baseline posture</a>
        <a href="#findings"><span>03</span>Findings</a>
        <a href="#changes"><span>04</span>Change watch</a>
        <a href="#coverage"><span>05</span>Coverage</a>
        <a href="#evidence"><span>06</span>Evidence health</a>
      </nav>
      <div class="mission-rail-boundary">
        <strong>Authority boundary</strong>
        <span>No Intune writes</span>
        <span>No automatic exceptions</span>
        <span>Human judgment required</span>
      </div>
    </aside>

    <div class="mission-stage">
      <div data-provenance-slot></div>

      <div class="mission-banner" data-mission-banner role="status" aria-live="polite">
        Loading the fingerprint-verified sanitized evidence package…
      </div>

      <section id="overview" class="mission-hero-panel" aria-labelledby="overview-title">
        <div class="mission-header">
          <div>
            <span class="mission-eyebrow">TMCO Consulting · Apple fleet control plane</span>
            <h2 id="overview-title" data-mission-title>Mission Control</h2>
            <p data-mission-subtitle>Validating evidence identity and freshness…</p>
          </div>
          <div class="mission-header-state">
            <span>Evidence state</span>
            <strong data-mission-mode>VALIDATING</strong>
          </div>
        </div>
        <div class="mission-metrics" data-mission-metrics></div>
        <p class="mission-denominator" data-mission-denominator></p>
      </section>

      <section class="mission-grid mission-grid-command" aria-label="Immediate operational view">
        <article class="mission-panel mission-panel-priority">
          <div class="mission-section-heading">
            <div>
              <span class="mission-eyebrow">Priority queue</span>
              <h2>What requires attention now</h2>
            </div>
            <span class="mission-count" data-priority-count></span>
          </div>
          <p>Every state below comes from deterministic comparison. Open an item for its evidence chain.</p>
          <div class="mission-attention-list" data-attention-list></div>
        </article>

        <article class="mission-panel mission-panel-pipeline">
          <div class="mission-section-heading">
            <div>
              <span class="mission-eyebrow">Collection path</span>
              <h2>Read-only signal flow</h2>
            </div>
          </div>
          <div class="mission-pipeline" data-collection-pipeline></div>
        </article>
      </section>

      <section id="posture" class="mission-panel mission-baseline-console" aria-labelledby="posture-title">
        <div class="mission-section-heading">
          <div>
            <span class="mission-eyebrow">Desired state versus observed state</span>
            <h2 id="posture-title">Baseline posture</h2>
            <p>All 98 approved rules stay visible. Only reviewed exact provider mappings enter the deterministic denominator.</p>
          </div>
          <label class="mission-baseline-selector">
            <span>Comparison lens</span>
            <select data-baseline-view>
              <option value="active">CIS Level 1 · full implementation plan</option>
              <option value="evaluated">CIS Level 1 · evaluated rules only</option>
              <option value="stig">STIG · technical cross-reference only</option>
            </select>
          </label>
        </div>
        <div class="mission-baseline-readout" data-baseline-readout></div>
        <div class="mission-table-wrap mission-posture-table-wrap">
          <table class="mission-table mission-posture-table">
            <thead>
              <tr><th>Control objective</th><th>Desired</th><th>Observed</th><th>Deterministic state</th><th>Evidence</th><th>Action</th></tr>
            </thead>
            <tbody data-posture-rows></tbody>
          </table>
        </div>
        <div class="mission-baseline-next" data-baseline-next></div>
      </section>

      <section id="findings" class="mission-panel" aria-labelledby="findings-title">
        <div class="mission-section-heading">
          <div>
            <span class="mission-eyebrow">Deterministic drift queue</span>
            <h2 id="findings-title">Current findings</h2>
            <p>Filters operate only on the validated package; they do not trigger collection.</p>
          </div>
          <span class="mission-count" data-finding-count></span>
        </div>
        <div class="mission-filters" aria-label="Finding filters">
          <label>Platform <select data-filter-platform><option value="">All</option></select></label>
          <label>State <select data-filter-drift><option value="">All</option></select></label>
          <label>Severity <select data-filter-severity><option value="">All</option></select></label>
          <label>Setting category <select data-filter-category><option value="">All</option></select></label>
          <button type="button" data-clear-filters>Clear filters</button>
        </div>
        <div class="mission-table-wrap">
          <table class="mission-table">
            <thead>
              <tr><th>Setting</th><th>State</th><th>Severity</th><th>Observed → target</th><th>Assignment</th></tr>
            </thead>
            <tbody data-finding-rows></tbody>
          </table>
        </div>
        <div class="mission-empty" data-finding-empty hidden>No findings match these filters.</div>
      </section>

      <section id="changes" class="mission-panel" aria-labelledby="changes-title">
        <div class="mission-section-heading">
          <div>
            <span class="mission-eyebrow">Current versus prior sanitized snapshot</span>
            <h2 id="changes-title">Change watch</h2>
          </div>
          <span class="mission-count" data-change-count></span>
        </div>
        <div class="mission-summary-grid">
          <article class="mission-subpanel"><h3>Resolved findings</h3><div data-resolved-changes></div></article>
          <article class="mission-subpanel"><h3>New drift</h3><div data-new-changes></div></article>
          <article class="mission-subpanel"><h3>Comparison provenance</h3><dl data-change-summary></dl></article>
        </div>
      </section>

      <section id="coverage" class="mission-grid mission-grid-coverage" aria-labelledby="coverage-title">
        <article class="mission-panel mission-panel-wide">
          <div class="mission-section-heading">
            <div><span class="mission-eyebrow">Approved inventory versus implementation</span><h2 id="coverage-title">Baseline implementation backlog</h2></div>
          </div>
          <p>These are planning gaps, not failed controls. Each rule needs an approved Intune, custom-profile, script/agent, or alternate-evidence path before deterministic evaluation.</p>
          <div class="mission-resource-list mission-planning-list" data-planning-groups></div>
        </article>
        <article class="mission-panel">
          <div class="mission-section-heading">
            <div><span class="mission-eyebrow">Collected resources versus parser</span><h2>Collection coverage and blind spots</h2></div>
          </div>
          <p>Inventory-only records are visible but do not change alignment. Parser or exact-mapping gaps require engineering review.</p>
          <div class="mission-resource-list" data-unevaluated-groups></div>
        </article>
        <article class="mission-panel">
          <div class="mission-section-heading">
            <div><span class="mission-eyebrow">Cross-framework view</span><h2>Assessment support</h2></div>
          </div>
          <div class="mission-callout">Technical references are not passed controls, framework scores, certifications, or assessor conclusions.</div>
          <div class="mission-table-wrap">
            <table class="mission-table mission-framework-table">
              <thead><tr><th>Framework</th><th>Evaluated</th><th>References</th><th>Aligned</th><th>Drifting</th><th>Boundary</th></tr></thead>
              <tbody data-framework-summary></tbody>
            </table>
          </div>
        </article>
      </section>

      <section id="evidence" class="mission-panel" aria-labelledby="evidence-title">
        <div class="mission-section-heading">
          <div><span class="mission-eyebrow">Chain of custody</span><h2 id="evidence-title">Evidence health and privacy</h2></div>
        </div>
        <div class="mission-summary-grid">
          <article class="mission-subpanel"><h3>Approved baseline</h3><dl data-baseline-summary></dl></article>
          <article class="mission-subpanel" id="collection-health"><h3>Collection health</h3><div data-endpoint-coverage></div><div data-collection-gaps></div></article>
          <article class="mission-subpanel"><h3>Private → public gate</h3><dl data-privacy-summary></dl></article>
          <article class="mission-subpanel"><h3>Managed Apple aggregate</h3><div data-device-summary></div><div data-platform-summary></div></article>
        </div>
      </section>

      <details class="mission-methodology">
        <summary>Authority boundary and methodology</summary>
        <p>Git revert changes reviewed desired-state history; it does not revert Intune. Provifact has no Intune write capability. Technical configuration may support an assessment objective but cannot establish organizational compliance. Human assessors retain final judgment.</p>
        <p><a href="../audit-methodology/">Deterministic audit methodology</a> · <a href="../data-handling/">Data handling</a> · <a href="../settings-matrix/">Complete baseline inventory</a></p>
      </details>
    </div>

  </div>

  <dialog class="mission-dialog" data-finding-dialog aria-labelledby="finding-dialog-title">
    <form method="dialog"><button class="mission-dialog-close" aria-label="Close finding detail">Close</button></form>
    <div data-finding-detail></div>
  </dialog>
</div>

<noscript>
  Mission Control requires JavaScript to render the deterministic JSON artifact. The raw public-safe
  package remains available at <code>/assets/data/mission-control.json</code>.
</noscript>
