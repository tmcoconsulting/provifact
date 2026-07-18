# Getting Started

Phase 0 runs entirely with synthetic data and requires no cloud account, tenant identifier, or API
key.

## Requirements

- Python 3.12 or later
- Git
- A shell capable of activating a Python virtual environment

## Install from a clean environment

```bash
git clone https://github.com/tmcoconsulting/evidenceops.git
cd evidenceops
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install --no-build-isolation --no-deps -e .
```

Direct development dependencies are exact-pinned in `pyproject.toml`, and their resolved
transitive environment is pinned in `requirements-dev.txt`. The core package has no runtime
dependency in Phase 0.

## Validate the foundation

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy
python -m pytest
python -m bandit -r evidenceops scripts -c pyproject.toml
python scripts/check_secrets.py
mkdocs build --strict
python scripts/check_public_artifacts.py site
python -m pip_audit
```

## Inspect the sanitizer

The raw synthetic fixtures intentionally contain obvious sensitive-looking test values. Tests
provide ephemeral pseudonymization keys at runtime, confirm that repeat input and key produce repeat
pseudonyms, confirm that cross-record relationships survive, and confirm that unknown fields stop
publication.

Do not add a real export to `fixtures/`. Synthetic fixtures must be constructed deliberately and
must carry an explicit notice.

## Run the site

```bash
mkdocs serve
```

The **Live Demo** and **Evidence Dashboard** are static shells. They do not make network requests or
claim a live collection has occurred.

## Before adding a provider

Read the [security model](security-model.md), [data-handling policy](data-handling.md), and
[future live collection procedure](operations/live-collection.md). A provider proposal must define
its exact read permissions, data inventory, normalization contract, retention, sanitization
classification, failure modes, and test plan before code is accepted.
