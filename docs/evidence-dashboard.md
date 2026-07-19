# EvidenceOps Mission Control

<div class="mission-shell" data-mission-control aria-busy="true">
  <div class="mission-banner" data-mission-banner role="status" aria-live="polite">
    Loading the signed, sanitized evidence package…
  </div>

  <header class="mission-header">
    <div>
      <span class="mission-eyebrow">Auditor-oriented technical evidence</span>
      <h2 data-mission-title>Mission Control</h2>
      <p data-mission-subtitle>Validating evidence identity and freshness…</p>
    </div>
    <div class="mission-mode" data-mission-mode>VALIDATING</div>
  </header>

  <nav class="mission-nav" aria-label="Mission Control views">
    <a href="#overview">Overview</a>
    <a href="#drift">Drift</a>
    <a href="#platforms">Platforms</a>
    <a href="#frameworks">Framework evidence</a>
    <a href="#quality">Data quality</a>
    <a href="#assistant">AI assistant</a>
  </nav>

  <section id="overview" aria-labelledby="overview-title">
    <h2 id="overview-title">Executive overview</h2>
    <div class="mission-metrics" data-mission-metrics></div>
    <p class="mission-denominator" data-mission-denominator></p>
    <div class="mission-summary-grid">
      <article class="mission-panel">
        <h3>Approved baseline</h3>
        <dl data-baseline-summary></dl>
      </article>
      <article class="mission-panel">
        <h3>Managed Apple posture</h3>
        <div data-device-summary></div>
      </article>
      <article class="mission-panel">
        <h3>Changes since prior collection</h3>
        <div data-change-summary></div>
      </article>
    </div>
  </section>

  <section id="drift" aria-labelledby="drift-title">
    <div class="mission-section-heading">
      <div>
        <h2 id="drift-title">Deterministic drift</h2>
        <p>Filters operate only on the validated public package. Select a row for its evidence chain.</p>
      </div>
      <span class="mission-count" data-finding-count></span>
    </div>
    <div class="mission-filters" aria-label="Drift filters">
      <label>Platform <select data-filter-platform><option value="">All</option></select></label>
      <label>Drift type <select data-filter-drift><option value="">All</option></select></label>
      <label>Severity <select data-filter-severity><option value="">All</option></select></label>
      <label>Setting category <select data-filter-category><option value="">All</option></select></label>
      <button type="button" data-clear-filters>Clear filters</button>
    </div>
    <div class="mission-table-wrap">
      <table class="mission-table">
        <thead>
          <tr><th>Finding</th><th>Drift</th><th>Severity</th><th>Expected</th><th>Observed</th><th>Evidence</th></tr>
        </thead>
        <tbody data-finding-rows></tbody>
      </table>
    </div>
    <div class="mission-empty" data-finding-empty hidden>No findings match these filters.</div>
  </section>

  <section id="platforms" aria-labelledby="platforms-title">
    <h2 id="platforms-title">Platform and resource coverage</h2>
    <div class="mission-summary-grid" data-platform-summary></div>
    <h3>Unmapped tenant objects</h3>
    <p>Unmapped objects remain visible; EvidenceOps does not hide policy inventory it cannot evaluate.</p>
    <div class="mission-resource-list" data-unmapped-resources></div>
  </section>

  <section id="frameworks" aria-labelledby="frameworks-title">
    <h2 id="frameworks-title">Supplemental technical evidence coverage</h2>
    <div class="mission-callout">
      Crosswalk identifiers come from the pinned mSCP source. They indicate relevant technical
      evidence—not certification, control satisfaction, or an assessor conclusion.
    </div>
    <div class="mission-summary-grid" data-framework-summary></div>
  </section>

  <section id="quality" aria-labelledby="quality-title">
    <h2 id="quality-title">Data quality and collection coverage</h2>
    <div class="mission-summary-grid">
      <article class="mission-panel">
        <h3>Endpoint collection</h3>
        <div data-endpoint-coverage></div>
      </article>
      <article class="mission-panel">
        <h3>Collection gaps</h3>
        <div data-collection-gaps></div>
      </article>
      <article class="mission-panel">
        <h3>Privacy gate</h3>
        <dl data-privacy-summary></dl>
      </article>
    </div>
  </section>

  <section id="assistant" aria-labelledby="assistant-title">
    <h2 id="assistant-title">Evidence-grounded AI assistant</h2>
    <p>
      The model receives only a bounded sanitized evidence package. Deterministic findings remain
      authoritative; all prose is generated analysis subject to human review.
    </p>
    <div class="mission-assistant" data-mission-assistant data-runtime-state="loading">
      <div>
        <span class="mission-eyebrow">Runtime boundary</span>
        <h3 data-runtime-status>Checking Worker status</h3>
        <p data-runtime-detail>The dashboard remains useful if the model is unavailable.</p>
      </div>
      <div class="mission-questions" aria-label="Supported question examples">
        <button type="button" data-question="What are the highest-severity findings?">Highest-severity findings</button>
        <button type="button" data-question="Which FileVault requirements are not aligned?">FileVault drift</button>
        <button type="button" data-question="What changed since the previous collection?">Changes since prior collection</button>
        <button type="button" data-question="Which devices are noncompliant?">Privacy-safe device posture</button>
      </div>
      <button type="button" data-generate-narrative disabled>Check runtime</button>
      <div class="runtime-output" data-narrative-output hidden aria-live="polite"></div>
    </div>
  </section>

  <dialog class="mission-dialog" data-finding-dialog aria-labelledby="finding-dialog-title">
    <form method="dialog"><button class="mission-dialog-close" aria-label="Close finding detail">Close</button></form>
    <div data-finding-detail></div>
  </dialog>
</div>

<noscript>
  Mission Control requires JavaScript to render the deterministic JSON artifact. The raw public
  package remains available at `assets/data/mission-control.json`.
</noscript>

!!! warning "Authority boundary"

    Git revert does not revert Intune. EvidenceOps has no Intune write capability. Technical
    configuration may support an assessment objective but cannot prove organizational compliance;
    human assessors retain final judgment.
