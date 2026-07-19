# Live Read-Only Collection

Live collection is an opt-in private operator action. It never publishes automatically and has no
Intune mutation command.

## Microsoft Graph contract

The machine-readable source of truth is
`manifests/microsoft-graph-permissions.v1.json`. The expanded Apple collector uses these resource
families, plus documented child `GET` requests for settings, assignments, and scheduled actions:

| API | GET resource family | Evidence purpose |
| --- | --- | --- |
| v1.0 | `deviceManagement/managedDevices` with a fixed `$select` | Aggregate Apple platform, management, compliance, encryption, supervision, registration, and freshness posture |
| v1.0 | `deviceManagement/deviceConfigurations` | Legacy/custom Apple configuration and assignments |
| beta | `deviceManagement/configurationPolicies` | Settings Catalog metadata, settings, and assignments |
| v1.0 | `deviceManagement/deviceCompliancePolicies` | Apple compliance policy, assignment, and scheduled-action metadata |
| v1.0 | `deviceAppManagement/mobileApps` | Managed Apple application type, safe version metadata, and assignment intent |
| v1.0 | `deviceAppManagement/mobileAppConfigurations` and `managedAppPolicies` | Application configuration/protection policy metadata |
| v1.0 | `deviceManagement/deviceEnrollmentConfigurations`, `deviceCategories`, and `depOnboardingSettings` | Enrollment restrictions, categories, and ADE connection health |
| v1.0 | `deviceAppManagement/vppTokens` | Apps and Books token health without token/account values |
| v1.0 | `deviceManagement/applePushNotificationCertificate` | APNs certificate state/expiry without certificate/account values |

Settings Catalog is the only beta dependency. The adapter attributes it as beta, validates beta
pagination separately, and records a visible gap if it is unavailable or changes shape. It does
not silently substitute another endpoint.

The Graph client supports complete pagination, concurrency bounded to four operations, exponential
retry with jitter, `Retry-After`, timeouts, and structured handling for 401, 403, 404, 409, 429,
transient 5xx, malformed responses, empty collections, and hostile next links. A failure in one
resource family becomes a collection gap; successful families remain usable.

Microsoft documents the [Graph permissions reference](https://learn.microsoft.com/en-us/graph/permissions-reference),
[managed-device list](https://learn.microsoft.com/en-us/graph/api/intune-devices-manageddevice-list?view=graph-rest-1.0),
[device configuration list](https://learn.microsoft.com/en-us/graph/api/intune-deviceconfig-deviceconfiguration-list?view=graph-rest-1.0),
[mobile app list](https://learn.microsoft.com/en-us/graph/api/intune-apps-mobileapp-list?view=graph-rest-1.0),
[Apps and Books tokens](https://learn.microsoft.com/en-us/graph/api/intune-onboarding-vpptoken-list?view=graph-rest-1.0),
[APNs certificate](https://learn.microsoft.com/en-us/graph/api/intune-devices-applepushnotificationcertificate-get?view=graph-rest-1.0),
[paging](https://learn.microsoft.com/en-us/graph/paging), and
[throttling](https://learn.microsoft.com/en-us/graph/throttling).

## Exact permissions

All four permissions require administrator consent for the profiles used here.

| Permission | Delegated ID | Application ID | Why it is required |
| --- | --- | --- | --- |
| `DeviceManagementConfiguration.Read.All` | `f1493658-876a-4c87-8fa7-edb559b3476a` | `dc377aa6-52d8-4e23-b271-2a7ae04cedf3` | Configuration, Settings Catalog, compliance, and their relationships |
| `DeviceManagementManagedDevices.Read.All` | `314874da-47d6-4978-88dc-cf0d37f0bb82` | `2f51be20-0bb4-4fed-bf7b-db946066c75e` | Aggregate managed-device posture |
| `DeviceManagementApps.Read.All` | `4edf5f54-4666-44af-9de9-0144fb4b6e8c` | `7a6ee1e7-141e-4cec-ae74-d9db155731ff` | Managed apps, app policies, assignments, and Apps and Books health |
| `DeviceManagementServiceConfig.Read.All` | `8696daa5-bce5-4b2e-83f9-51b6defc4e1e` | `06a5fe6d-c49d-46a7-b082-56b1b14103c7` | Enrollment, ADE, category, and APNs service metadata |

EvidenceOps does not request write scopes, privileged device operations, `Directory.Read.All`,
`Group.Read.All`, or `User.Read.All`. These four read scopes are broad tenant permissions even
though the collector requests and publishes a much smaller field set; application ownership and
admin consent remain meaningful security boundaries.

## Attended local setup

Use an approved public-client app with the four delegated scopes, tenant admin consent, and device
code enabled. Provide nonsecret IDs only to the current process:

```bash
export AZURE_TENANT_ID='operator-supplied-value'
export AZURE_CLIENT_ID='operator-supplied-value'
python -m evidenceops live-collect-apple --auth device-code \
  --private-dir artifacts/private --retention-days 1
```

MSAL uses an in-memory cache; EvidenceOps configures no persistent token storage. An already
acquired short-lived token can instead be supplied as `EVIDENCEOPS_GRAPH_ACCESS_TOKEN` with
`--auth environment-token`. EvidenceOps never writes the token.

## Publication

The live command writes a normalized, owner-only `private-apple-*.json` package to a Git-ignored
directory. Source IDs are retained only where needed for joins. Raw Graph responses are not
persisted. Publication requires a fresh runtime-only HMAC key:

```bash
export EVIDENCEOPS_PSEUDONYM_KEY='operator-generated-random-value-at-least-32-bytes'
python -m evidenceops publish-mission artifacts/private/private-apple-….json \
  --output build/live-public/mission-control.json
unset EVIDENCEOPS_PSEUDONYM_KEY
python scripts/check_public_artifacts.py build/live-public
```

The publisher reconstructs an allowlisted public package, validates its canonical fingerprint,
and performs the credential/content scan. Unknown fields fail closed. A human must inspect any live
sanitized package before it can replace the public synthetic artifact.

The protected workflow has an explicit `prepare_publication` input, disabled by default. When a
reviewer selects it, the workflow may retain exactly one already validated and scanned
`mission-control.json` as a one-day GitHub Actions artifact. It never uploads the private package,
Graph response, access token, pseudonym key, or containing directory. A separate reviewed
deployment accepts the exact successful audit run ID, downloads that named public artifact,
revalidates the schema, fingerprint, nested field allowlists, credential/content policy, and full
static site, then deploys only when the protected deployment gate is enabled. Collection and
deployment remain two separate human actions.

## GitHub OIDC workflow

`.github/workflows/intune-audit.yml` is manual, main-only, and targets the protected `production`
environment. It checks out trusted `main`, requests only `contents: read` and `id-token: write`,
uses the exact environment-scoped Entra federation, runs contract tests with repository-wide
coverage addopts explicitly disabled for that smoke step, collects privately, publishes and scans
the derived package, writes only aggregate counts to the job summary, and deletes private and
working evidence at job end. Its optional one-day handoff contains only the scanned public Mission
file. Pull requests and arbitrary branches cannot obtain the production identity.

## Validation status

Mocked provider and contract tests cover every configured resource family, pagination, retry,
partial failure, schema changes, and GET-only enforcement. All four required application
permissions show tenant administrator consent. Protected-main run `29701160503` acquired its token
through the exact environment-scoped OIDC trust, completed the expanded GET-only collection,
constructed and scanned the sanitized Mission package, wrote only its aggregate report, and ran
ephemeral cleanup successfully. It retained no artifact because publication preparation was not
selected. Production therefore continues to serve synthetic data pending the separate reviewed
publication handoff.

The Entra application retains pre-existing delegated permissions that are not used by the
application-permission workflow. EvidenceOps does not remove unrelated permissions automatically.
No client secret exists or is needed.

## Retention and deletion

- Private directories/files use `0700`/`0600` where supported.
- Existing packages are never overwritten and symlinks are not followed.
- Retention is explicit from 1–30 days; the operator must delete the package and backups at expiry.
- Public output contains only aggregates, approved technical values, hashes, and pseudonymous
  references.
- Graph tokens and pseudonymization keys remain process-scoped and must be unset after use.
