# Local Demo Mode

Local demo mode is the credential-free way to reproduce Provifact from curated synthetic input.
It is separate from the production Cloudflare deployment, which serves a reviewed sanitized live
Mission package while keeping the assistant in fixture narrative mode by default.

## Purpose

Use local demo mode to inspect repository structure, deterministic evaluation, the settings and
baseline matrix, sanitization behavior, site navigation, and evidence presentation without a tenant
connection or OpenAI key.

## Procedure

1. Create a clean Python virtual environment and install the exact locked dependencies.
2. Run `python -m provifact run-mission-demo --output-dir build/mission-demo`.
3. Run `python scripts/check_public_artifacts.py build/mission-demo`.
4. Run `python -m provifact rebuild-static-demo`.
5. Build with `mkdocs build --strict` and scan `site/`.
6. Serve the full Worker boundary with `npm run dev`; open **Mission Control**, **Settings &
   Baselines**, and **Runtime Demo**.

A simple `mkdocs serve` or `python -m http.server` process can display static pages, but same-origin
API routes such as `/api/status` and `/api/ask` require the local Worker.

## Fixture rules

- Store synthetic input under `fixtures/synthetic/`.
- Include an explicit synthetic-data notice.
- Use obvious raw markers only when proving sanitization.
- Never derive a fixture by lightly editing a tenant export.
- Keep public demonstration data under `docs/assets/data/` and regenerate it through the CLI.
- Confirm raw markers, private paths, tenant values, and credentials do not appear in `site/`.
- Never replace the production live sanitized Mission package with synthetic output unless a
  separately reviewed deployment explicitly intends that rollback.

## Exit criteria

Demo mode is valid only when Python and Worker tests, the strict documentation build, repository
secret scan, and public-artifact scan pass. The local UI must identify the package as synthetic and
must not imply that live collection, Intune mutation, or a live model call ran.

The read-only collector exists but is not exercised by demo mode. Production operating status must
be read from the deployed `/api/status` and `/api/ready` routes rather than inferred from a local
build.
