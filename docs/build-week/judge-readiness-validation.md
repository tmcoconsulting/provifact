# Judge-Readiness Validation

**Date:** 2026-07-20

**Branch:** `codex/cis-planning-judge-ready`

**Validated product commit:** `cde773cdd0f3820a46cd59205e8b883706f0ae58`

**Human review:** required

**Data used locally:** synthetic only

This is the current pre-merge validation record for the complete CIS Level 1 planning view,
site-wide operational design, original Provifact mark, Provifact Assistant naming, and judge path.
It supersedes mutable counts in earlier checkpoint reports without deleting their audit history.

## Product evidence

- The approved inventory contains exactly 98 unique CIS Level 1 rule IDs from pinned NIST mSCP
  revision `11b5896e4f12f43410686024f543792742562c91`.
- All 98 rules have checked human-readable titles and are visible by default.
- Four rules have reviewed exact Intune provider joins and enter the deterministic denominator.
- One desired setting requires exact provider-mapping review; 93 rules require an approved
  management or evidence path. Together these form a visible 94-rule implementation backlog.
- The synthetic package produces three deterministic drift findings and one aligned result. The 94
  planning records do not become false findings or compliance verdicts.
- Mission Control, the baseline plan, and the rest of the documentation share one dark operational
  visual language. Early validation checkpoints are retained as history but removed from the main
  judge navigation.
- The original proof-chain Provifact SVG appears in the global navigation, favicon, landing page,
  and Mission Control. The bounded explainer is named Provifact Assistant; no Microsoft logo, icon,
  or product brand is used as a Provifact feature name.

## Clean-environment and security validation

The exact-pinned Python lock installed into a new temporary Python 3.14 environment, which exceeds
the Python 3.12 minimum. The project wheel then built and installed with `--no-deps
--no-build-isolation`. Commands and outcomes:

```text
python -m ruff format --check .
  PASS — 63 files formatted

python -m ruff check .
  PASS

python -m mypy
  PASS — no issues in 63 source files

python -m pytest
  PASS — 238 passed, 1 skipped, 90.03% branch coverage

python -m bandit -r evidenceops scripts -c pyproject.toml
  PASS — no findings

python scripts/check_secrets.py
  PASS

python scripts/check_company_name.py
  PASS

python -m pip_audit -r requirements-dev.txt
  PASS — no known vulnerabilities

npm ci --ignore-scripts --no-audit --no-fund
  PASS — 89 packages installed from lock

npm audit --audit-level=moderate
  PASS — 0 vulnerabilities

npm run validate:worker
  PASS — Prettier, Oxlint, strict TypeScript, 56 Worker tests, generated bindings,
  and default/preview/production Wrangler dry-runs

mkdocs build --strict
  PASS — 135 static assets

python scripts/check_public_artifacts.py site
  PASS

python -m provifact run-mission-demo --output-dir <temporary-a>
python -m provifact run-mission-demo --output-dir <temporary-b>
diff -qr <temporary-a> <temporary-b>
  PASS — identical synthetic outputs; public scan passed

git diff --check
  PASS
```

The one skipped test is the explicitly credential-gated local live Intune test. No tenant or OpenAI
credential was loaded, no paid model was called, no Cloudflare deployment occurred, and no Graph
request ran from this feature branch.

Bandit initially identified five public benchmark titles containing the word “password” as possible
credentials. Those exact title constants are scanner-reviewed and narrowly annotated; the Bandit
rule remains enabled for the rest of the repository.

## Browser validation

The locally built Worker/static artifact was inspected in a real browser. Verified:

- the original mark renders clearly at favicon, navigation, hero, and dashboard sizes;
- Mission Control labels synthetic fixed-time evidence as `FIXTURE`, not stale live evidence;
- the dashboard exposes 98 approved rules, four exact joins, 94 planning items, three drift
  findings, and one aligned result;
- the full implementation plan is the default comparison lens;
- Provifact Assistant opens from the site-wide launcher and remains labeled as bounded generated
  analysis subject to human review; and
- the global documentation shell uses the same operational visual system as Mission Control.

## Remaining production gate

This record does not claim the change is deployed. After review and protected merge, run the
protected-main GET-only Intune audit, publish only its scanned sanitized package, deploy that exact
snapshot through the protected Cloudflare workflow, and perform HTTPS/browser verification. Record
the resulting run IDs and public-safe aggregate counts here or in a follow-up validation commit.
