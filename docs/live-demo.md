# Live Demo

<div class="synthetic-banner">
This is an honest static shell built from curated synthetic fixtures. It does not connect to
Microsoft Intune, Microsoft Graph, Apple services, or a production tenant.
</div>

## Synthetic posture snapshot

<div class="evidence-grid">
  <div class="evidence-card">
    <div class="evidence-metric">12</div>
    <div class="evidence-label">Controls evaluated</div>
  </div>
  <div class="evidence-card">
    <div class="evidence-metric">9</div>
    <div class="evidence-label">Compliant</div>
  </div>
  <div class="evidence-card">
    <div class="evidence-metric">2</div>
    <div class="evidence-label">Drifted</div>
  </div>
  <div class="evidence-card">
    <div class="evidence-metric">1</div>
    <div class="evidence-label">Approved exception</div>
  </div>
</div>

| Synthetic control | Deterministic state | What an operator would inspect |
| --- | --- | --- |
| Screen lock timeout | Compliant | Desired value, observed value, evidence fingerprint |
| Disk encryption required | Drifted | Normalized observation and collection timestamp |
| Operating system update window | Approved exception | Exception owner, expiry, approval history |

The machine-readable [demo summary](assets/data/demo-summary.json) contains only curated synthetic
records. The generated site is scanned for raw fixture markers, email-shaped values, network
addresses, UUID-shaped identifiers, key material, and bearer credentials.

## Run it locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install --no-build-isolation --no-deps -e .
python -m pytest
mkdocs serve
```

Open the local address printed by MkDocs and navigate to **Evidence Dashboard**.

## What is deliberately not simulated

- Tenant authentication or Microsoft Graph requests
- Device-level identity or real assignment data
- Automatic control certification
- GPT-generated evidence narrative
- Exception approval or configuration deployment

Those omissions preserve a clear line between a polished demonstration and implemented product
behavior.
