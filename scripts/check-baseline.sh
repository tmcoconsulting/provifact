#!/usr/bin/env bash
# Fails if the repository drifts from the TMCO baseline.
# Safe to run locally: it only reads files.
set -uo pipefail
fail=0
note() { echo "FAIL: $*"; fail=1; }

# 1. Required files
for f in SECURITY.md .github/CODEOWNERS .github/dependabot.yml .gitignore; do
  [ -f "$f" ] || note "missing $f"
done

# 2. No secret-style files tracked in git
bad=$(git ls-files | grep -iE '(^|/)\.env($|\.)|(^|/)\.dev\.vars$|\.pem$|\.p12$|\.pfx$|(^|/)id_(rsa|ed25519)$' | grep -viE '\.(example|sample|template)$' || true)
[ -z "$bad" ] || note "secret-style files are tracked: $(echo "$bad" | tr '\n' ' ')"

# 3. Workflow rules
shopt -s nullglob
for w in .github/workflows/*.yml .github/workflows/*.yaml; do
  # every third-party action pinned to a full commit SHA
  unpinned=$(grep -nE '^\s*-?\s*uses:\s*[^.#]' "$w" | grep -vE '@[0-9a-f]{40}(\s|$)' || true)
  [ -z "$unpinned" ] || note "$w has actions not pinned to a commit SHA: $(echo "$unpinned" | tr '\n' ' ')"
  # explicit least-privilege token permissions
  grep -qE '^permissions:' "$w" || note "$w has no top-level permissions block"
  # triggers that run with secrets on untrusted input
  grep -qE '^\s*pull_request_target\s*:' "$w" && note "$w uses pull_request_target"
done

[ "$fail" -eq 0 ] && echo "Baseline check passed."
exit "$fail"
