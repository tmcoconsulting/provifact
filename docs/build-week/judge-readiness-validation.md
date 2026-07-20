# Judge-Readiness Validation

**Date:** 2026-07-20

**Protected-main product merge:** `0dd12dcac2511bdfeed51471baedc2f304741659`

**Validated product commit:** `0dd12dcac2511bdfeed51471baedc2f304741659`

**Human review:** required

**Data used locally:** synthetic only; production verification used only the scanned sanitized
public package and public-safe aggregates

This is the current validation record for the complete CIS Level 1 planning view, site-wide
operational design, original Provifact mark, Provifact Assistant naming, protected-main collection,
Cloudflare deployment, and judge path. It supersedes mutable counts in earlier checkpoint reports
without deleting their audit history.

The public cutover uses repository `tmcoconsulting/provifact` and custom domain
`provifact.tmcoconsulting.com`. Legacy Worker, OpenAI project/key, namespace, schema, environment,
and artifact names remain compatibility identifiers; this is intentional, not incomplete branding.

## Product evidence

- The approved inventory contains exactly 98 unique CIS Level 1 rule IDs from pinned NIST mSCP
  revision `11b5896e4f12f43410686024f543792742562c91`.
- Sixteen additional pinned public technical profiles are available for exact rule-ID membership
  comparison. They are planning references, never compliance scores or assessor conclusions.
- The one pinned upstream Safari rule-ID punctuation variance is explicitly canonicalized. Browser
  loading now fails closed unless the approved catalog and Mission requirement sets are exactly
  equal; the CIS Level 1 table renders 98 rows rather than a false 99th reference-only row.
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
  PASS — no issues in 65 source files

python -m pytest
  PASS — 245 passed, 1 skipped, 90.03% branch coverage

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
  PASS — Prettier, Oxlint, strict TypeScript, 57 Worker tests, generated bindings,
  and default/preview/production Wrangler dry-runs

mkdocs build --strict
  PASS — strict static build; 102 generated files; public-artifact scan passed

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

## Protected-main and production validation

PR #16 passed the required public CI job and both CodeQL language analyses, had no review threads,
and was squash-merged to protected `main` as
`48a67aea60e5759f54ed5aee1396f68274b57f3b`. Local `main` was then fast-forwarded to the same
commit.

Protected audit run
[`29772311614`](https://github.com/tmcoconsulting/evidenceops/actions/runs/29772311614)
completed in 43 seconds. It verified the prior sanitized-package provenance, authenticated through
the production-environment GitHub OIDC trust, ran the approved GET-only collector, sanitized and
scanned the publication, uploaded the one-day public artifact, and passed the unconditional
ephemeral-evidence cleanup. No private response was downloaded or inspected during this validation.

The independently re-scanned public package had snapshot ID
`mission-7b5fad138c9b5bb3a643a781` and reported only these public-safe aggregates:

- 98 approved rules;
- four deterministically evaluated rules;
- one aligned rule and three missing-from-tenant findings;
- three collection gaps;
- 13 policies evaluated; and
- 82 collected but unmapped objects.

Protected deployment run
[`29772466732`](https://github.com/tmcoconsulting/evidenceops/actions/runs/29772466732)
completed in 1 minute 42 seconds. It reran the complete public validation, selected only audit run
`29772311614`, required the exact snapshot ID above, rebuilt and scanned the static artifact,
rechecked the snapshot immediately before upload, deployed the Worker, and verified the active
Cloudflare version through the authenticated control plane. The temporary production window was
then reset and independently verified as `CLOUDFLARE_DEPLOY_ENABLED=false`.

Independent production verification confirmed:

- `https://provifact.tmcoconsulting.com/`, Mission Control, the baseline plan, judge guide,
  logo, `/api/status`, and `/api/ready` return HTTP 200 with successful TLS verification;
- every one of the 32 URLs in the production sitemap returns HTTP 200;
- HSTS, CSP, frame denial, no-sniff, referrer, permissions, cross-origin opener, and cross-origin
  resource headers are present;
- `/api/status` reports `gpt-5.6-terra`, OpenAI Responses mode, current live sanitized evidence,
  the exact snapshot ID, `intune_write_capability=false`, and `byok_supported=false`;
- Mission Control renders 98 posture rows and five implementation-plan sections; and
- the baseline plan shows `98 of 98 baseline requirements shown` by default with its evaluated-only
  filter disabled.

The earlier presentation-only deployment made no paid request. The later cutover proof below made
exactly one bounded live Terra request. Final human review still covers product copy, the original
mark, and submission materials; it is not an unmet automated security or deployment gate.

## Provifact repository and production cutover proof

The repository was renamed to `tmcoconsulting/provifact` without changing its immutable repository
ID. GitHub's default immutable-subject template produces the production-environment subject for the
renamed repository. Entra credential `github-provifact-production` matches that subject, issuer
`https://token.actions.githubusercontent.com`, and audience `api://AzureADTokenExchange`.

Protected-main audit
[`29780265224`](https://github.com/tmcoconsulting/provifact/actions/runs/29780265224)
completed the new OIDC exchange, GET-only collection, publication-policy application, public scan,
artifact upload, and unconditional ephemeral cleanup. Only after that proof was the obsolete
repository-name federated credential removed. The app has zero client secrets. Four application
permissions are present, all read-only and admin-consented:

- `DeviceManagementApps.Read.All`;
- `DeviceManagementConfiguration.Read.All`;
- `DeviceManagementManagedDevices.Read.All`; and
- `DeviceManagementServiceConfig.Read.All`.

The app also retains pre-existing delegated read permissions. They are not used by the production
federated workflow and were not silently removed during this cutover.

The independently rescanned public package reported snapshot
`mission-c62d533f8d58f76cef9afb1a`, 98 approved requirements, 13 evaluated policies, one aligned
requirement, three deterministic missing findings, three collection gaps, and 82 deliberately
unmapped objects. No raw response, policy name, assignment name, object ID, user, device, or tenant
identifier entered this record.

Cloudflare custom domain `provifact.tmcoconsulting.com` was attached without deleting the old
rollback hostname. Protected deployment
[`29780852414`](https://github.com/tmcoconsulting/provifact/actions/runs/29780852414)
selected only the audit artifact and exact snapshot above, reran the complete public gate, deployed
the merged `9dae1363c0019022062c844a3725e0b537de658c` source, and verified the active version through
Cloudflare's authenticated control plane. The environment variable was then independently verified
as `CLOUDFLARE_DEPLOY_ENABLED=false`.

Independent HTTPS checks proved the new hostname, TLS, root, health/readiness/status endpoints,
dashboard, profile catalog, and social image. The response includes HSTS, CSP, frame denial,
no-sniff, referrer, permissions, cross-origin opener, and cross-origin resource policy. The status
endpoint reports fixed `gpt-5.6-terra`, OpenAI mode, no Intune writes, and no browser BYOK.

One bounded live production question was submitted after deployment. The structured Terra response
parsed, exact finding coverage and evidence references passed, typed claims matched deterministic
evidence, generated prose remained quarantined, and the UI retained human-review language. The
question, evidence input, prose, authorization data, and model output were not retained in this
repository record and no second paid request was made.

The first browser session retained a stale `force-cache` catalog after the exact rule-ID fix. The
page failed closed instead of presenting an inconsistent matrix. The catalog URL is now bound to
its expected fingerprint, the browser requires the recomputed fingerprint and exact Mission/
TMCO Consulting rule-set equality, and protected deployment
[`29782874960`](https://github.com/tmcoconsulting/provifact/actions/runs/29782874960) published the
final product commit above. Post-deployment browser verification showed all 98 TMCO Consulting
requirements in CIS Level 1 and, as a separate planning comparison, 73 company-profile overlaps
plus 142
reference-only candidates for the 215-rule CMMC Level 2 profile. Those figures describe catalog
membership and planning scope, not compliance.
