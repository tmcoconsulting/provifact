# Contributing to Provifact

Thank you for helping make audit evidence safer and easier to operate.

## Before opening a pull request

1. Open an issue for security-sensitive, architectural, or provider-permission changes.
2. Create a focused branch and keep unrelated changes out of the pull request.
3. Use synthetic fixtures only. Never paste tenant exports into issues, discussions, tests, or
   pull requests.
4. Run every command listed in `AGENTS.md`.
5. Explain data-flow, permission, and public-output effects in the pull request template.

Contributions must be original or compatible with Apache License 2.0. Identify third-party code,
data, or standards text and its license; do not submit Apple, Microsoft, CIS, NIST, CMMC, or other
material merely because it is publicly readable.

By contributing, you agree that your contribution is licensed under Apache License 2.0. You retain
copyright in your contribution. TMCO Consulting, LLC does not claim ownership of third-party
baselines or repositories.

## Security changes

Do not open a public issue for a suspected vulnerability or accidentally exposed sensitive data.
Follow `SECURITY.md` and use GitHub private vulnerability reporting when available.

## Commit messages

Use a short imperative subject. Build Week milestone commits also include the project trailers
documented in `docs/build-week/codex-collaboration.md`.
