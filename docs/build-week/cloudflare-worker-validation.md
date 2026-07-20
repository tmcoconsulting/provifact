# Cloudflare Worker Validation Record

> **Historical checkpoint.** This record preserves the original Worker rollout. Fixture-mode and
> deployment statements below are not the authority for the final live audit cockpit.

**Date:** 2026-07-18

**Branch:** `codex/cloudflare-worker-runtime`

**Starting commit:** `ccec44bd674c761fe3e4b335c56442f6ef7be912`

**Human-reviewed Worker checkpoint:** `7683c69f9eaca9f67ec220de5fb9f1a19fe9b3df`

**Runtime hardening commit:** `f8994d9`

**Protected workflow support:** `925e0f8`

**Externally validated egress/runtime fix:** `cfd9975`

**Reported branch checkpoint:** `27611c143f96311002441629d696047f60000240`

## Scope

This milestone added and deployed the Worker/static-assets runtime selected after Phase 1 security
remediation. At this checkpoint, live TMCO Consulting Intune validation and a successful generated OpenAI
narrative remained outstanding, and production intentionally served the synthetic fixture after
the first bounded OpenAI validation returned capacity unavailable. Later dated sections record the
successful model validation, protected GET-only audit, and reviewed sanitized publication.

Implemented runtime controls include:

- selective Worker-first `/api/*` routing with scanned `site/` static assets;
- explicit fixture and OpenAI modes with no silent fallback;
- same-origin, exact-method, JSON/content-encoding, request-size, rate, timeout, and response bounds;
- repeated publication/credential scanning before model egress;
- strict public-package and structured-output contracts;
- deterministic exact-coverage narrative verification and unrestricted-prose quarantine;
- allowlisted structured logging and static CSP/security headers; and
- exact-pinned Node tooling, workerd tests, binding drift checks, dry-run bundle, and credential-free CI.

## Local validation

The final credential-free run produced:

```text
npm ci --ignore-scripts --no-audit --no-fund
  PASS — 89 exact-lock packages installed

npm run validate:worker
  PASS — Prettier, type-aware Oxlint, strict runtime/test TypeScript,
         28 workerd contract tests, generated-binding check, and fixture/preview/production dry-runs

npm audit --audit-level=moderate
  PASS — 0 vulnerabilities

python -m ruff format --check .
  PASS — 40 Python files already formatted

python -m ruff check .
  PASS

python -m mypy
  PASS — no issues in 40 source files

python -m pytest
  PASS — 152 passed, 1 opt-in live test skipped, 91.13% branch-aware coverage

python -m bandit -r evidenceops scripts -c pyproject.toml
  PASS — no findings; 2,829 source lines scanned

python scripts/check_secrets.py
  PASS

python -m pip_audit -r requirements-dev.txt
  PASS — no known vulnerabilities

python -m evidenceops rebuild-static-demo
git diff --exit-code -- docs/assets/data
  PASS — synthetic data rebuilt byte-for-byte

python -m evidenceops run-demo --output-dir <clean-temporary-directory>/output
python scripts/check_public_artifacts.py <clean-temporary-directory>/output
  PASS — complete synthetic evidence flow and output scan

mkdocs build --strict
python scripts/check_public_artifacts.py site
  PASS — static artifact and Worker frontend built and scanned

python -m pip wheel --no-deps --no-build-isolation .
  PASS — wheel contains all three shared JSON policy/schema catalogs

git diff --check
  PASS
```

The final documentation build initially failed closed when this record included a Cloudflare
version UUID. The operational identifier was removed from public content, the site was rebuilt,
and the complete public-artifact scan then passed.

Local HTTP smoke validation used `wrangler dev --local` in fixture mode. `GET /api/status` and
`GET /live-demo/` returned HTTP 200. Posting the tracked public package to `/api/narrative`
returned HTTP 200 with `ai_model_call_performed: false`, four typed claims accepted, fourteen
generated-prose entries quarantined, and human review required. The local process then shut down.

The workerd corpus verifies same-origin and method enforcement, browser-key rejection, native rate
handling, compression/content-length/byte bounds, shared credential patterns, unknown fields,
tampered fingerprints, fixture identity, one fixed OpenAI request, no silent fallback, exact
finding coverage, unknown claims, unsupported verdicts, unrestricted-prose quarantine, and bounded
sanitized distinction between quota and request-rate 429 responses.

## Continuation validation after operator-control inspection

An isolated Python environment was created outside the repository from `requirements-dev.txt`, and
the package was installed with `--no-build-isolation --no-deps`. A clean `npm ci` installed the 89
exact-lock packages. The complete local matrix then passed:

```text
Ruff format/lint                         PASS
Mypy                                    PASS — 41 source files
Pytest                                  PASS — 152 passed, 1 live test skipped,
                                               91.13% branch-aware coverage
Bandit                                  PASS — 2,829 lines, no findings
repository secret scan                  PASS
pip-audit / npm audit                   PASS — no known vulnerabilities
Prettier / Oxlint / strict TypeScript    PASS
Worker contract tests                   PASS — 28 passed
generated bindings                      PASS
synthetic demo comparison               PASS — two independent outputs identical
synthetic/public-artifact scans          PASS
MkDocs strict build                     PASS — documented upstream warning only
fixture/preview/production dry-runs      PASS
git diff --check                        PASS
```

Production and preview status endpoints returned HTTPS success in explicit fixture mode with model
`gpt-5.6-terra`, no Intune write capability, and BYOK disabled. The production custom domain
returned CSP, HSTS, frame, MIME, referrer, permissions, and cross-origin headers. A production
fixture request used only the tracked synthetic package, performed no model call, accepted four
typed deterministic claims, quarantined fourteen generated-prose claims, required human review,
and passed the public-artifact scan. No deployment was made for this continuation patch.

## External validation

- Verified the authenticated TMCO Consulting Cloudflare account and active `tmcoconsulting.com`
  zone without modifying unrelated Workers or DNS.
- Deployed credential-free preview `evidenceops-preview` and production Worker `evidenceops`.
- Attached `evidenceops.tmcoconsulting.com` as a Worker Custom Domain; public DNS, TLS hostname
  coverage, HTTPS, CSP, HSTS, static assets, and API status returned success.
- Verified same-origin, method, browser-key, authorization, media-type, compression, publication,
  fingerprint, verifier, and native-rate boundaries. A ten-request preview burst returned six 429s.
- Created one key under the OpenAI Platform project now retained under the legacy `evidenceops`
  identifier and transferred it directly to
  the encrypted Worker secret `OPENAI_API_KEY`; no plaintext file remained.
- Confirmed the project key lists all three GPT-5.6 model identifiers and kept the fixed runtime pin
  at `gpt-5.6-terra` for balanced cost and capability.
- A bounded synthetic production request reached OpenAI and returned capacity unavailable. No model
  output was returned, accepted, logged, or published. Production was then returned to explicit
  fixture mode, where the verifier accepted four typed status claims and quarantined fourteen prose
  fields for human review.
- Disabled the legacy GitHub Pages site/environment. Created a branch-restricted GitHub production
  environment and nonsecret variables; Cloudflare deployment remains disabled pending a narrow
  environment token.
- Created and independently re-read the exact Entra federated credential
  `github-evidenceops-production` for the protected GitHub `production` environment. Added only the
  required application `DeviceManagementConfiguration.Read.All` permission and verified
  administrator consent. No client secret or Graph request was created.
- Re-read the protected GitHub environment: the four nonsecret variables are present,
  `CLOUDFLARE_DEPLOY_ENABLED` is `false`, and the secret name `CLOUDFLARE_API_TOKEN` is present.
  The secret value was not retrieved, printed, or stored, and its Cloudflare scope remains
  unverified.
- Re-read the production Worker secret names: `OPENAI_API_KEY` is present. The operator replaced
  its value with the only active key belonging to the project service account
  `evidenceops-cloudflare-production`; no key value was exposed to Codex, GitHub, or the repository.

## Gates that remained outstanding at this checkpoint

- No Microsoft Graph or Intune request had been made at this checkpoint. The trust and permission
  were configured, but the workflow remained restricted to protected `main` and could not run from
  the feature branch.
- OpenAI project controls were later verified in the authenticated Platform UI: the service account
  is the only nonhuman project member, the project allows only `gpt-5.6-terra`, the model limit is
  5 RPM/25,000 TPM, the monthly soft budget is `$5`, and alerts exist at 50%, 80%, and 100%.
  A project budget is a soft alert—not a hard spending cap. One bounded live response remained a
  separate validation gate.
- The service account is assigned only the custom `evidenceops-responses-runtime` role. That role
  grants Responses API model capability and no file, assistant, thread, eval, fine-tuning, vector,
  project-administration, usage-export, or key-management permission.
- The protected GitHub environment contained `CLOUDFLARE_API_TOKEN` by name only. Its ownership,
  validity, and Cloudflare resource scope had not yet been independently verified; deployment
  remained disabled through `CLOUDFLARE_DEPLOY_ENABLED=false`.
- No production rollback was executed because earlier versions used live model mode; the CLI
  deployment history and rollback command were verified instead.

## 2026-07-19 post-merge operational update

After TJ reviewed PR #2 through `0220b2cf19a5dd019f1d18f90a2e45acc99242df`, the reviewed Worker
and static assets were deployed to the production custom domain in explicit fixture mode. HTTPS,
status, readiness, static assets, TLS, and repository-controlled browser security headers passed.

Exactly one bounded synthetic request was then made in fixed `gpt-5.6-terra` mode. It returned HTTP
success, parsed under the strict schema, accepted two deterministic typed claims and rejected none,
quarantined every generated prose field, and retained the human-review requirement. The response
text, prompt, evidence values, key, and upstream body were not printed or retained. Production was
immediately redeployed from the reviewed configuration and independently verified in fixture mode.

This later success supersedes only the earlier capacity-unavailable operational result. It does not
alter the historical validation record or make generated analysis authoritative.

## 2026-07-19 protected collection and live sanitized publication

Protected-main audit `29701160503` completed the environment-scoped OIDC exchange, all configured
GET-only collection families, fail-closed publication, aggregate reporting, and ephemeral cleanup.
It retained no artifact. A separately reviewed publication handoff was then merged as
`b966cd0a5b20580b046c6ed3bb31057f7682bda7`; protected run `29702128497` retained exactly one
scanned public Mission file for one day and no private package.

The selected artifact was independently revalidated and deployed. Production now reports live
sanitized evidence while keeping narrative mode explicitly fixture-based. The status endpoint and
Mission asset matched the selected snapshot; the dashboard, fixture assistant, TLS, and browser/API
security headers passed. No secret, raw Graph response, tenant identifier, assignment identity, or
private package was logged, committed, deployed, or retained.

Cloudflare UI inspection independently verified that `evidenceops-github-deploy` is an active
account token with only Workers Scripts write access on the TMCO Consulting account. Protected
deployment run `29702213181` proved that the GitHub environment secret is bound to that working
token without exposing the value: validation and upload succeeded. Wrangler then made an
unnecessary zone-route inspection because the existing custom domain was still declarative; the
narrow token correctly denied it after activation. The pending routine-deployment fix treats the
custom domain as a separately provisioned control-plane resource, removes route management from
routine uploads, and adds an exact deployed-snapshot check. `CLOUDFLARE_DEPLOY_ENABLED` remains
`false` outside the bounded retry window.

PR #5 was later reviewed and squash-merged as
`3e4954dfe50ddaaa06e5f38114abe26591fe10ea`. Its protected-main retry passed every validation and
publication step and uploaded the reviewed bundle without route-management access. The final curl
was managed-challenged by Bot Fight Mode; Cloudflare Security Analytics correlated the exact event
and time. Independent HTTPS checks returned the exact expected live sanitized snapshot with the
required headers. The follow-up does not weaken Bot Fight Mode: it binds the expected snapshot to
the Worker version message and verifies that version is the sole active 100%-traffic deployment
through the authenticated Cloudflare control plane. Public HTTP and browser verification remain an
independent operator gate.

## 2026-07-19 final deployment verification

TJ reviewed and merged the Bot-Fight-safe active-version proof as
`f1dd37be822c07677621907168fc372c6ccc0ae0`. Protected-main deployment `29703512007` completed in
success: the reviewed-window guard, locked installs, complete public matrix, exact artifact
selector, sanitized-package download, repeated publication scan, staging, snapshot pin, Worker
upload, and control-plane verifier all passed. `CLOUDFLARE_DEPLOY_ENABLED` was restored and re-read
as `false`.

A fresh read-only Wrangler query independently confirmed the expected snapshot-bound version is
the sole active deployment at 100% traffic. Unauthenticated HTTPS checks passed for the root,
dashboard, live demo, Mission asset, status, health, and readiness routes. The runtime reported live
sanitized tenant data and fixture narrative mode. TLS, CSP, HSTS, frame, MIME, referrer,
permissions, cache, and cross-origin headers passed. The exact downloaded Mission package passed
schema/fingerprint validation and public-artifact scanning.

The fixture assistant answered a supported question with two accepted typed claims, no rejected
claims, three evidence references, prose quarantine, and required human review while making no
model call. An unsupported question returned the exact insufficient-evidence response. Production
remains in fixture narrative mode; the separate single bounded Terra success remains the proof of
the operational model path.
