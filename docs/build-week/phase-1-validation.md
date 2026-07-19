# Phase 1 Validation Record

**Date:** 2026-07-18

**Branch:** `codex/phase-1-read-only-proof`

**Starting commit:** `29ea77ebfb84f39b3a8e7bd4972ce55a2d0b2f24`
**Security-remediated review commit:** `ccec44bd674c761fe3e4b335c56442f6ef7be912`

## Starting evidence

Before Phase 1 edits, formatting, lint, strict typing, 13 tests with 91.03% coverage, Bandit,
committed-tree secret scanning, MkDocs strict build, public-site scanning, and dependency audit
passed. The workspace scanner also revealed that an ignored `.env.local` was being scanned and
that MkDocs discovered ignored `docs/private/`; both boundaries were corrected in Phase 1.

## Implemented proof

- Ten strict schema-v1 evidence objects with stable IDs/fingerprints
- Graph v1.0 GET-only provider for two macOS general-configuration properties and assignments
- Explicit single-permission manifest and in-memory authentication providers
- Restrictive private writer and field-manifest/publication policy
- Four-outcome deterministic desired-state fixture
- Optional fixed-model Responses API adapter and deterministic verifier (production pin now
  `gpt-5.6-terra`)
- Six-command operator surface and synthetic local-static artifacts

## Security-remediation baseline

Before the four confirmed findings were changed, the full checkpoint produced 118 passing tests,
one opt-in live test skipped, and 92.27% coverage. Formatting, linting, strict typing, Bandit,
repository secret scanning, MkDocs strict build, static-artifact scanning, and dependency audit all
passed. The dependency audit required approved package-index access after its first sandboxed
attempt could not upgrade its temporary audit environment.

The Codex Security scan reported one high and three medium findings:

1. an untrusted-SHA path into the privileged GitHub Pages workflow;
2. inconsistent credential patterns that missed underscore-form GitHub tokens;
3. duplicate finding IDs satisfying a count-only narrative coverage check; and
4. unrestricted contradictory prose bypassing a finite status-phrase matcher.

The remediation removes the deployment sink, centralizes credential detection at four gates,
requires exact unique finding-ID coverage, verifies only typed deterministic claims, and
quarantines all generated prose for human review. Cloudflare Workers Static Assets was documented
as the next milestone and was not provisioned or deployed in this commit. The follow-on runtime
work has a separate validation record.

## Local validation

The remediation was validated from the existing isolated exact-pinned environment after
reinstalling the current package wheel with `--no-deps`:

```text
python -m pip install --no-build-isolation --no-deps .  PASS — wheel built and installed
python -m ruff format --check .                         PASS — 40 files already formatted
python -m ruff check .                                  PASS — all checks passed
python -m mypy                                          PASS — no issues in 40 source files
python -m pytest                                        PASS — 147 passed, 1 live skipped;
                                                               92.29% coverage
python -m bandit -r evidenceops scripts -c pyproject.toml PASS — no issues identified
python scripts/check_secrets.py                         PASS — shared-catalog scan passed
python -m pip_audit -r requirements-dev.txt             PASS — no known vulnerabilities
python -m evidenceops run-demo --output-dir <temp>/demo PASS — synthetic flow completed
python scripts/check_public_artifacts.py <temp>/demo    PASS — public scan passed
python -m evidenceops rebuild-static-demo               PASS — tracked synthetic data rebuilt
mkdocs build --strict                                   PASS — local static site built
python scripts/check_public_artifacts.py site           PASS — public scan passed
```

The focused security corpus contains regression cases for all six GitHub token prefixes, all four
credential gates, duplicate/missing/unknown narrative finding IDs, typed-claim mismatch and unknown
claim code, contradictory status synonyms, removal of privileged Pages permissions/workflow
chaining, and the legitimate synthetic controls. Follow-on tests verify read-only public CI plus
main-only, protected-environment audit/deployment workflows; every referenced action is pinned to a
40-character commit SHA.

The MkDocs command continues to print the upstream Material/MkDocs 2.0 warning already recorded in
the decision log; it exits successfully under the exact-pinned MkDocs 1.6.1 toolchain.

## External validation

- **TMCO Intune:** not executed as of this record because no approved tenant/client configuration
  or short-lived Graph token was present. No live endpoint result is claimed.
- **OpenAI:** the adapter and transport contract are mocked and the demo narrative is fixture-based.
  No paid model call is performed or claimed in this remediation.
- **Intune mutations:** none. The provider transport exposes only GET, and no apply command exists.

No real TMCO configuration, identity, device, group, tenant, or credential value is recorded here.
The later Cloudflare/OpenAI external results are recorded separately in
[Cloudflare Worker Validation](cloudflare-worker-validation.md); they do not retroactively change
the claims of this security-remediation checkpoint.
