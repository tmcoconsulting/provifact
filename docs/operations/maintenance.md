# Repository maintenance

Provifact's public CI runs on every main-branch push and pull request, daily on main, and on manual
dispatch. It uses no tenant or model credentials. The daily run detects newly published dependency
advisories and upstream tooling failures even when the repository has no new commits.

Dependabot checks Python, GitHub Actions, and npm weekly. Each ecosystem has one grouped update
because Python direct and resolved pins, CodeQL action references, and Worker testing dependencies
must remain compatible. Keep exact direct pins and regenerate the full resolved lock. Do not
disable vulnerability audits to make a PR pass.

## Review an update

1. Read the complete diff, current-head feedback, package requirements, and official migration
   notes for major changes. Check coupled direct and transitive dependencies together.
2. Install the exact locks from a clean environment, then run all checks in `AGENTS.md` and
   `npm run validate:worker`. Use Python 3.12 or later and Node 22.12 or later.
3. Run both dependency audits and `pip check`. Regenerate Worker declarations with the pinned
   Wrangler. Rebuild the synthetic demo and verify that unplanned data changes are absent.
4. Require the protected branch's validation checks for the exact head being merged. Never bypass
   protections or substitute old checks from an earlier commit.
5. Verify main-branch CI after merge and check that the expected security alerts resolve.

The daily Codex maintenance monitor investigates new issues, PR feedback, failed CI, and dependency
alerts. Routine validated Dependabot updates may be merged within its standing authorization;
other changes and major migrations are prepared for human review. It reports meaningful changes,
completed fixes, failures, and decisions needed, and stays quiet when nothing changes.

## Compatibility holds

Vitest remains at 4.1.12 with the supported `@cloudflare/vitest-plugin` integration. A test of
Vitest 5.0.4 failed inside workerd when the project path contained spaces: an encoded `%20` cache
path was treated as a filesystem path. Dependabot defers Vitest 5 until an upstream fix passes
the tests from the actual project path. Review this hold rather than assuming the ignored major
is safe indefinitely.

## Separate approval gates

CIS Level 2 remains an independently loaded comparison profile. Profile membership cannot change
the approved desired-state baseline or its evaluation denominator. Follow the
[approved-baseline procedure](approved-baseline.md) for a separate human decision.

Repository maintenance does not open a production deployment window, change security/account
configuration, run scheduled tenant collection, publish private policy names, or expand model
egress. Live collection and publication follow their protected manual workflows and the
[data-handling policy](../data-handling.md).
