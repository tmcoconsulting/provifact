# Getting Started

Python 3.12 or later is required. Public CI and the demo use no tenant or OpenAI credential.

## Install from a clean environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install --no-build-isolation --no-deps .
```

Dependencies are exactly pinned. The runtime evidence path uses the Python standard library;
`msal` is included only for attended live collection. The optional `ai` extra pins `certifi` for
Python installations that lack a usable platform CA bundle; the development lock already includes
it.

## Three-minute synthetic demonstration

```bash
python -m provifact run-mission-demo --output-dir build/mission-demo
python scripts/check_public_artifacts.py build/mission-demo
python -m provifact rebuild-static-demo
mkdocs build --strict
python scripts/check_public_artifacts.py site
```

Open `site/evidence-dashboard/index.html`. Mission Control shows the approved 98-rule inventory,
four reviewed macOS provider mappings, 25% technical alignment over the explicit four-rule
denominator, FileVault/firewall/assignment/conflict drift, a Mac/iPhone/iPad posture, unevaluated
resources, one collection gap, previous-versus-current changes, framework cross-references, and the
site-wide Provifact Copilot.
Every value comes from the tracked synthetic package; fixture assistant answers make no model
request.

To validate the same static artifact behind the local Cloudflare Worker boundary, install Node.js
22 or later and run:

```bash
npm ci --ignore-scripts --no-audit --no-fund
python -m provifact rebuild-static-demo
mkdocs build --strict
npm run validate:worker
npm run dev
```

`npm run dev` starts fixture mode and explicitly disables Wrangler `.env`/`.dev.vars` loading. The
Copilot enables `/api/ask` only after `/api/status` confirms a supported Worker mode. Fixture mode
makes no OpenAI request. Stop the local process when the review is complete.

## Command boundary

```text
run-demo                 credential-free synthetic schema-v1 proof
run-mission-demo         credential-free Apple Mission Control vertical slice
live-collect             original narrow GET-only collection (backward compatible)
live-collect-apple       expanded GET-only Apple collection into ignored private storage
publish                  validate, sanitize, scan, and emit a schema-v1 package
publish-mission          allowlist and scan an expanded private Apple collection
generate-narrative       optional GPT-5.6 call using only the public package
verify-narrative         deterministic acceptance or quarantine
rebuild-static-demo      regenerate tracked synthetic static-build data
```

There is deliberately no `apply`, remediation, assignment, profile, deployment, rollback, or
exception command. Live mode never falls back to synthetic mode.

## Optional live and GPT workflows

Live collection requires a separately approved Entra app and explicit authentication choice; see
[Live Collection](operations/live-collection.md). Publication requires a runtime-only
`EVIDENCEOPS_PSEUDONYM_KEY` of at least 32 bytes. Optional narrative generation reads
`OPENAI_API_KEY` and pins `gpt-5.6-terra` for the bounded cost-conscious runtime.

No successful paid model call is required or claimed by the static demo. Production has a dedicated
project-scoped service-account key dedicated to Provifact and stored only as the encrypted
Cloudflare Worker secret. The current OpenAI Platform project retains its legacy `evidenceops` name
until the coordinated infrastructure cutover. Its secret binding remains `OPENAI_API_KEY`; the value
is absent from the repository and GitHub. Production uses fixed
`gpt-5.6-terra` only after the same-origin request and sanitized evidence gates pass. It never
silently falls back to a fixture response when an OpenAI request fails.
Browser BYOK is rejected because it would create browser-storage, exfiltration, logging, and abuse
risks without improving the server-side least-privilege boundary.

Provifact does not load `.env` files. Environment-variable names appear in `.env.example`, but
operators must use a local process environment or managed secret store. Never add a real value to
the repository.

## Full validation

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy
python -m pytest
python -m bandit -r evidenceops scripts -c pyproject.toml
python scripts/check_company_name.py
python scripts/check_secrets.py
python -m pip_audit -r requirements-dev.txt
mkdocs build --strict
python scripts/check_public_artifacts.py site
npm run validate:worker
npm audit --audit-level=moderate
```

The test command enforces 90% branch-aware coverage. All public artifacts must pass the final scan.

## Static-build hosting compatibility

`mkdocs build --strict` produces `site/` with relative navigation and self-contained public assets.
The exact-pinned Wrangler configuration serves `site/` through Workers Static Assets and routes
only `/api/*` through Worker code first. Production is available at
`https://evidenceops.tmcoconsulting.com/`; it serves a separately reviewed live sanitized Mission
package and reports the actual fixed-model availability through `/api/status`.
