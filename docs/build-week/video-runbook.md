# Final Video Runbook

Use the production custom domain only after `/api/status` and the Mission package both report the
reviewed live snapshot. The recording must be shorter than three minutes and may use voice-over
only; TJ does not need to appear on camera.

## Pre-recording gate

The verified production package at the end of finalization is
`mission-2626272a6ea65343eee5302c`, collected `2026-07-20T16:24:36Z`, with prior live snapshot
`mission-283e1b9be457b76d104a0e8a`. It contains a real unchanged comparison and no resolved finding
because no manual Intune change occurred. Recheck these values immediately before recording and use
whatever newer reviewed production snapshot is actually reported.

1. Open `https://evidenceops.tmcoconsulting.com/api/status` in a clean browser profile. Confirm
   `data_mode` is `LIVE SANITIZED TENANT DATA`, `narrative_mode` is `openai`, `model` is
   `gpt-5.6-terra`, and `model_call_available` is `true`.
2. Open `/assets/data/mission-control.json` and compare its `snapshot_id` with `/api/status` and the
   reviewed audit artifact. Do not show the raw JSON in the final video.
3. Confirm the package is current, the public scanner passed, and the browser console has no error.
4. Close notifications, password managers, account menus, terminals, cloud consoles, and unrelated
   tabs. Use only public-safe pages.
5. Ask one short Copilot question before recording to confirm the bounded live path. Avoid repeated
   chargeable calls.

## Narrated script — target 2:45

**0:00–0:20 — problem and provenance.** Open Mission Control at the top. “Regulated endpoint teams
should not reconstruct months of configuration history before every audit. Provifact joins
approved intent in Git to read-only Intune observation, deterministic drift, sanitized publication,
and evidence-grounded explanation.” Point to the live-data badge, collection time, snapshot, and
fixed-model availability.

**0:20–0:55 — action-first findings.** Point to **Findings requiring review**, **New drift**,
**Resolved**, and **Collection gaps**. Read the current live values exactly as displayed; never use
fixture counts in narration. Open the highest-priority genuine finding. Show observed value, approved
target, assignment state, exact reviewed provider definition, evidence IDs, fingerprint, and
read-only operator guidance.

**0:55–1:20 — baseline and honest limits.** Open **Settings**. “The approved demo baseline contains
98 pinned macOS Level 1 rules, but only four Microsoft Intune provider mappings are currently
reviewed. Provifact does not guess the rest.” Show the compact six-column matrix and one detail
dialog. Mention that framework identifiers are cross-references, not a score or assessment verdict.

**1:20–1:45 — change history.** Return to **Changes**. If the current live package has a prior
snapshot, show its exact new/resolved/unchanged result. If no manual Intune change was completed,
say: “The workflow is ready for a later human change and second read-only collection; Provifact
will not fabricate a resolved finding.” Explain that browser refresh checks only a newer published
snapshot and never calls Microsoft Graph.

**1:45–2:20 — actual GPT-5.6 answer.** Open Provifact Copilot and ask **What requires my attention?**
Show the direct answer and click one evidence reference. “The Worker—not the browser—selects bounded
sanitized facts for fixed `gpt-5.6-terra`. Typed claims and evidence references are checked against
the deterministic package. Free prose remains generated analysis subject to human review.”

**2:20–2:42 — security boundary.** “Microsoft Graph is GET-only through GitHub OIDC. Raw tenant
responses and tokens are ephemeral. Production cannot fall back to synthetic evidence. The OpenAI
key is server-side, requests use `store: false` and no tools, and Provifact has no apply or Intune
write command.”

**2:42–2:50 — close.** “Provifact does not decide organizational compliance. It makes approved
intent, observed state, drift, limitations, and evidence references reviewable before the audit.”

## Exact click sequence

1. `/evidence-dashboard/` — point to the global provenance strip.
2. Select the first item under **What requires attention now**.
3. In the dialog, point to observed → target, assignment, provider ID, evidence, fingerprint, and
   guidance; choose **Close**.
4. Select **Settings** in product navigation.
5. Choose **Review details** on a reviewed provider mapping; close the dialog.
6. Return to Mission Control and select **Changes**.
7. Choose **Check for newer published snapshot** and state that it does not collect from Intune.
8. Open the lower-right **Provifact Copilot** launcher.
9. Choose **What requires my attention?**, submit once, then open one returned evidence link.
10. Close with the visible human-review/no-write methodology boundary.

## Drift-to-resolution option

Use this only when TJ completed the separately approved low-risk Intune change and a second protected
audit used snapshot A as `prior_sanitized_audit_run_id`. Show snapshot B’s **Resolved** item, then ask
Copilot **Which finding was resolved?** The answer must cite current deterministic evidence. Never
describe an Intune change as resolved based only on the human action or Git history.

## Privacy review checklist

- [ ] No tenant ID, client/object ID, policy/group/device name, serial, user, email, private domain,
      notification, account menu, browser history, API key, token, or cloud-console content is visible.
- [ ] The public snapshot ID and evidence pseudonyms are shown only from the scanned public site.
- [ ] The recording says **TMCO Consulting**; legal/approval copy uses **TMCO Consulting, LLC**.
- [ ] Live and fixture modes are never confused.
- [ ] No framework cross-reference is described as a pass, certification, or completed assessment.
- [ ] The Copilot answer shows human-review language and links back to deterministic evidence.
- [ ] The final video is public, under three minutes, and uses only authorized media.

## Backup procedure

If the custom domain is temporarily unavailable, record the already reviewed production capture if
one exists. Otherwise demonstrate the credential-free local build below and label every frame
`SYNTHETIC DEMO DATA`; do not imply that the backup proves live Intune or OpenAI operation.

```bash
python -m evidenceops run-mission-demo --output-dir build/mission-demo
python -m evidenceops rebuild-static-demo
mkdocs build --strict
npm run dev
```

After recording, run `/feedback` in the primary Codex task and preserve its identifier privately.
Never commit the Session ID.
