"""Run the Provifact CLI while preserving the Phase 1 engine namespace."""

from evidenceops.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
