# Submission Checklist

This checklist is evidence support, not a statement of Build Week rules. Verify current competition
requirements from their authoritative source before submission.

## Public repository

- [x] Repository is public and owned by `tmcoconsulting`
- [x] Apache License 2.0 and `NOTICE` are present
- [x] `main` is protected and verified
- [x] Issues and Discussions are enabled; Wiki is disabled
- [x] CI passes with read-only repository permission
- [x] Confirm the retired GitHub Pages workflow is absent
- [x] Cloudflare runtime is locally and externally validated at the documented custom domain
- [x] Dependency security updates, secret scanning, and push protection supported by the plan are enabled

## Product and security evidence

- [x] Every demo surface clearly declares whether its evidence is synthetic or sanitized live data
- [x] Production reports the exact reviewed live snapshot and fixed `gpt-5.6-terra` mode; one
      bounded Copilot answer passes deterministic verification
- [x] No live tenant, person, device, group, or credential data is committed
- [x] Sanitizer fails closed on unknown fields
- [x] Generated site passes prohibited-pattern scanning
- [x] Read-only provider and human-approval boundaries are documented
- [x] Current limitations and rejected choices are visible
- [x] Commit hashes and exact validation commands are recorded

## Private submission metadata

- [ ] Run `/feedback` in the primary Codex thread
- [ ] Preserve the returned Session ID privately
- [ ] Do not commit the Session ID unless rules explicitly require public disclosure
- [ ] Verify any Devpost or competition fields against authoritative current instructions

## Media review

- [ ] Record only synthetic or successfully sanitized public demonstrations
- [ ] Review every frame for notifications, identities, secrets, and tenant/device data
- [ ] Distinguish implemented behavior from roadmap behavior
- [ ] Confirm asset and music usage rights
- [ ] Follow the [final video runbook](video-runbook.md) and keep the public recording under three
      minutes
