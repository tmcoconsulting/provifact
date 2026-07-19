# Demo Mode

Demo mode is the only credential-free, fully validated operating mode in this Phase 1 checkpoint.

## Purpose

It demonstrates repository structure, deterministic evaluation, sanitization behavior, site
navigation, and evidence presentation without a tenant connection.

## Procedure

1. Create a clean Python virtual environment.
2. Install the exact-pinned direct development dependencies.
3. Run the full validation commands in `AGENTS.md`.
4. Build the site with `mkdocs build --strict`.
5. Run `python scripts/check_public_artifacts.py site`.
6. Serve locally with `mkdocs serve`; no public hosting deployment is claimed.

## Fixture rules

- Store synthetic input under `fixtures/synthetic/`.
- Include an explicit synthetic-data notice.
- Use obvious raw markers when proving sanitization.
- Never derive a fixture by lightly editing a tenant export.
- Keep public demonstration data separate under `docs/assets/data/`.
- Confirm raw markers do not appear in `site/`.

## Exit criteria

Demo mode is valid only when unit tests, the documentation build, secret scan, and public-artifact
scan all pass. The UI must identify the data as synthetic and must not imply that collection,
remediation or a live model call ran. The read-only collector exists but is not exercised by demo
mode.
