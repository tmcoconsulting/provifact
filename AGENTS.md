# EvidenceOps agent guidance

These rules apply to all work in this repository.

## Non-negotiable safety boundaries

- Never commit credentials, tokens, tenant identifiers, device identifiers, raw exports, or real
  Microsoft Intune data.
- Microsoft Graph integrations are read-only. Do not request or implement write permissions.
- Public output must use synthetic data or pass the fail-closed sanitizer and public-artifact scan.
- Do not persist pseudonymization key material.
- Keep deterministic evidence separate from generated analysis. Label generated analysis and keep
  a human approval step.
- Do not copy code or content with unclear licensing.
- Never commit a Codex Session ID; treat it as private submission metadata.

## Required checks

Run these before proposing a change:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy
python -m pytest
python -m bandit -r evidenceops scripts -c pyproject.toml
python scripts/check_secrets.py
mkdocs build --strict
python scripts/check_public_artifacts.py site
python -m pip_audit -r requirements-dev.txt
```

Use Python 3.12 or later. Keep direct dependencies exact-pinned in `pyproject.toml`, keep the
resolved environment pinned in `requirements-dev.txt`, and update dependency rationale in
`docs/build-week/decision-log.md`.

## Design constraints

- Provider interfaces must remain vendor-neutral and expose collection only.
- Drift results must be reproducible without a language model.
- Unknown fields stop public sanitization until explicitly classified.
- Prefer small, typed modules and tests that a new engineer can explain.

## Build Week finalization constraints

- Production must use live sanitized tenant data. Synthetic data is limited to local and preview
  demonstrations and must never be a production fallback.
- Do not implement, request, or perform any Intune write operation.
- Provider mappings must be exact and explicitly reviewed; do not guess mappings or match tenant
  display names.
- Use plain language first and expose detailed technical evidence on demand.
- Use `TMCO Consulting` in ordinary product copy and `TMCO Consulting, LLC` for legal, approval,
  ownership, and copyright contexts.
- Keep Material for MkDocs for the submission; do not migrate frontend frameworks during this
  milestone.
- Complete the reviewed merge, protected live collection, production deployment, and public
  verification rather than stopping at an open pull request.
