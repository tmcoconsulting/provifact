import { assertJsonValue, canonicalJson, isRecord, sha256 } from "./evidence";
import { HttpError } from "./security";
import {
  EVIDENCE_STATUSES,
  type DesiredStateRecord,
  type DriftFinding,
  type EvidenceIdentity,
  type EvidenceStatus,
  type JsonValue,
  type Observation,
  type PublicEvidencePackage,
} from "./types";

const EVIDENCE_ID = /^ev1-[0-9a-f]{24}$/;
const FINGERPRINT = /^sha256:[0-9a-f]{64}$/;
const GIT_SHA = /^(?:[0-9a-f]{40}|[0-9a-f]{64}|synthetic-[a-z0-9-]+)$/;
const MAX_RECORDS = 32;
const MAX_REFERENCES = 160;

const IDENTITY_KEYS = [
  "schema_version",
  "object_type",
  "evidence_id",
  "content_fingerprint",
];

export function validatePublicPackage(value: unknown): PublicEvidencePackage {
  try {
    assertPublicPackage(value);
  } catch (error) {
    if (error instanceof HttpError) {
      throw error;
    }
    throw new HttpError(
      422,
      "package_schema_rejected",
      "public evidence schema rejected",
    );
  }
  return value;
}

export async function verifyPublicPackageIdentity(
  packageDocument: PublicEvidencePackage,
): Promise<void> {
  const identities: EvidenceIdentity[] = [
    packageDocument,
    packageDocument.provider,
    packageDocument.collection,
    ...packageDocument.desired_state,
    ...packageDocument.observations,
    ...packageDocument.findings,
    ...packageDocument.evidence_references,
  ];
  for (const identity of identities) {
    await verifyIdentity(identity);
  }
  const publicationCore = {
    synthetic: packageDocument.synthetic,
    source_type: packageDocument.source_type,
    provider: packageDocument.provider,
    collection: packageDocument.collection,
    desired_state: packageDocument.desired_state,
    observations: packageDocument.observations,
    findings: packageDocument.findings,
    evidence_references: packageDocument.evidence_references,
    human_approval_status: packageDocument.human_approval_status,
  };
  const expected = `sha256:${await sha256(canonicalJson(publicationCore))}`;
  if (packageDocument.publication.sanitized_content_fingerprint !== expected) {
    fail("sanitized publication fingerprint does not match package content");
  }
}

async function verifyIdentity(identity: EvidenceIdentity): Promise<void> {
  const unsigned: { [key: string]: JsonValue } = {};
  for (const [field, value] of Object.entries(identity)) {
    if (field !== "evidence_id" && field !== "content_fingerprint") {
      assertJsonValue(value);
      unsigned[field] = value;
    }
  }
  const digest = await sha256(canonicalJson(unsigned));
  if (
    identity.content_fingerprint !== `sha256:${digest}` ||
    identity.evidence_id !== `ev1-${digest.slice(0, 24)}`
  ) {
    fail(`evidence identity mismatch for ${identity.object_type}`);
  }
}

function assertPublicPackage(
  value: unknown,
): asserts value is PublicEvidencePackage {
  const root = exactRecord(
    value,
    [
      ...IDENTITY_KEYS,
      "synthetic",
      "source_type",
      "provider",
      "collection",
      "desired_state",
      "observations",
      "findings",
      "evidence_references",
      "publication",
      "human_approval_status",
    ],
    "sanitized public evidence package",
  );
  assertIdentity(root, "sanitized_public_evidence_package");
  if (typeof root.synthetic !== "boolean") {
    fail("synthetic must be a boolean");
  }
  if (
    root.source_type !== "curated-synthetic-fixture" &&
    root.source_type !== "sanitized-live-collection"
  ) {
    fail("source_type is unsupported");
  }
  if (
    (root.source_type === "curated-synthetic-fixture" &&
      root.synthetic !== true) ||
    (root.source_type === "sanitized-live-collection" &&
      root.synthetic !== false)
  ) {
    fail("source_type and synthetic flag disagree");
  }
  if (root.human_approval_status !== "human review required") {
    fail("public evidence must require human review");
  }

  const provider = validateProvider(root.provider);
  const collection = validateCollection(root.collection);
  const desired = validateArray(
    root.desired_state,
    MAX_RECORDS,
    validateDesired,
    "desired_state",
  );
  const observations = validateArray(
    root.observations,
    MAX_RECORDS,
    validateObservation,
    "observations",
  );
  const findings = validateArray(
    root.findings,
    MAX_RECORDS,
    validateFinding,
    "findings",
  );
  const references = validateArray(
    root.evidence_references,
    MAX_REFERENCES,
    validateReference,
    "evidence_references",
  );
  validatePublication(root.publication);

  if (collection.provider_evidence_id !== provider.evidence_id) {
    fail("collection provider evidence ID does not match provider metadata");
  }
  const identityObjects: EvidenceIdentity[] = [
    root as PublicEvidencePackage,
    provider,
    collection,
    ...desired,
    ...observations,
    ...findings,
    ...references,
  ];
  const ids = identityObjects.map((item) => item.evidence_id);
  if (new Set(ids).size !== ids.length) {
    fail("evidence IDs must be unique within the package");
  }
  const desiredIds = new Set(desired.map((item) => item.evidence_id));
  const observationIds = new Set(observations.map((item) => item.evidence_id));
  const packageIds = new Set(ids);
  for (const observation of observations) {
    if (
      observation.collection_evidence_id !== collection.evidence_id ||
      observation.provider_evidence_id !== provider.evidence_id
    ) {
      fail("observation provenance does not match package metadata");
    }
  }
  for (const finding of findings) {
    if (
      finding.collection_evidence_id !== collection.evidence_id ||
      finding.deterministic_algorithm_version !==
        collection.deterministic_algorithm_version ||
      finding.desired_state_git_commit_sha !==
        collection.desired_state_git_commit_sha
    ) {
      fail("finding provenance does not match collection metadata");
    }
    if (!desiredIds.has(finding.desired_state_evidence_id)) {
      fail("finding references an unknown desired-state record");
    }
    if (
      finding.observation_evidence_ids.some((id) => !observationIds.has(id))
    ) {
      fail("finding references an unknown observation");
    }
  }
  for (const reference of references) {
    const referenced = requireString(
      reference.referenced_evidence_id,
      "referenced_evidence_id",
    );
    if (!packageIds.has(referenced)) {
      fail("evidence reference points outside the supplied package");
    }
  }
}

function validateProvider(value: unknown): EvidenceIdentity {
  const record = exactRecord(
    value,
    [...IDENTITY_KEYS, "provider", "provider_version", "source_api_version"],
    "provider metadata",
  );
  assertIdentity(record, "provider_metadata");
  requireString(record.provider, "provider");
  requireString(record.provider_version, "provider_version");
  requireString(record.source_api_version, "source_api_version");
  return record as EvidenceIdentity;
}

function validateCollection(
  value: unknown,
): PublicEvidencePackage["collection"] {
  const record = exactRecord(
    value,
    [
      ...IDENTITY_KEYS,
      "collection_timestamp_utc",
      "provider_evidence_id",
      "desired_state_git_commit_sha",
      "deterministic_algorithm_version",
      "freshness",
    ],
    "collection metadata",
  );
  assertIdentity(record, "collection_metadata");
  requireUtc(record.collection_timestamp_utc, "collection_timestamp_utc");
  requireEvidenceId(record.provider_evidence_id, "provider_evidence_id");
  requireGitSha(
    record.desired_state_git_commit_sha,
    "desired_state_git_commit_sha",
  );
  requireString(
    record.deterministic_algorithm_version,
    "deterministic_algorithm_version",
  );
  validateFreshness(record.freshness);
  return record as PublicEvidencePackage["collection"];
}

function validateDesired(value: unknown): DesiredStateRecord {
  const record = exactRecord(
    value,
    [
      ...IDENTITY_KEYS,
      "record_key",
      "platform",
      "setting_key",
      "desired_value",
      "evaluation_mode",
      "title",
      "description",
      "desired_state_git_commit_sha",
    ],
    "desired-state record",
  );
  assertIdentity(record, "desired_state_record");
  for (const field of [
    "record_key",
    "platform",
    "setting_key",
    "evaluation_mode",
    "title",
    "description",
  ]) {
    requireString(record[field], field);
  }
  assertJsonValue(record.desired_value);
  requireGitSha(
    record.desired_state_git_commit_sha,
    "desired_state_git_commit_sha",
  );
  return record as DesiredStateRecord;
}

function validateObservation(value: unknown): Observation {
  const record = exactRecord(
    value,
    [
      ...IDENTITY_KEYS,
      "collection_evidence_id",
      "provider_evidence_id",
      "platform",
      "setting_key",
      "observed_value",
      "observation_state",
      "source_modified_at_utc",
      "freshness",
    ],
    "normalized observation",
  );
  assertIdentity(record, "normalized_configuration_observation");
  requireEvidenceId(record.collection_evidence_id, "collection_evidence_id");
  requireEvidenceId(record.provider_evidence_id, "provider_evidence_id");
  requireString(record.platform, "platform");
  requireString(record.setting_key, "setting_key");
  assertJsonValue(record.observed_value);
  requireString(record.observation_state, "observation_state");
  if (record.source_modified_at_utc !== null) {
    requireUtc(record.source_modified_at_utc, "source_modified_at_utc");
  }
  validateFreshness(record.freshness);
  return record as Observation;
}

function validateFinding(value: unknown): DriftFinding {
  const record = exactRecord(
    value,
    [
      ...IDENTITY_KEYS,
      "collection_evidence_id",
      "desired_state_evidence_id",
      "observation_evidence_ids",
      "status",
      "desired_state_git_commit_sha",
      "deterministic_algorithm_version",
      "input_fingerprints",
      "additional_evidence_required",
    ],
    "deterministic finding",
  );
  assertIdentity(record, "deterministic_drift_finding");
  requireEvidenceId(record.collection_evidence_id, "collection_evidence_id");
  requireEvidenceId(
    record.desired_state_evidence_id,
    "desired_state_evidence_id",
  );
  requireStringArray(
    record.observation_evidence_ids,
    "observation_evidence_ids",
  ).forEach((id) => requireEvidenceId(id, "observation_evidence_ids"));
  requireStatus(record.status);
  requireGitSha(
    record.desired_state_git_commit_sha,
    "desired_state_git_commit_sha",
  );
  requireString(
    record.deterministic_algorithm_version,
    "deterministic_algorithm_version",
  );
  const fingerprints = requireStringArray(
    record.input_fingerprints,
    "input_fingerprints",
  );
  if (
    fingerprints.length === 0 ||
    fingerprints.some((item) => !FINGERPRINT.test(item))
  ) {
    fail("input_fingerprints must contain fingerprints");
  }
  requireStringArray(
    record.additional_evidence_required,
    "additional_evidence_required",
  );
  return record as DriftFinding;
}

function validateReference(value: unknown): EvidenceIdentity {
  const record = exactRecord(
    value,
    [...IDENTITY_KEYS, "referenced_evidence_id", "reference_kind", "label"],
    "evidence reference",
  );
  assertIdentity(record, "evidence_reference");
  requireEvidenceId(record.referenced_evidence_id, "referenced_evidence_id");
  requireString(record.reference_kind, "reference_kind");
  requireString(record.label, "label");
  return record as EvidenceIdentity;
}

function validatePublication(value: unknown): void {
  const record = exactRecord(
    value,
    [
      "publication_policy_version",
      "published_at_utc",
      "source_private_fingerprint",
      "sanitized_content_fingerprint",
    ],
    "publication metadata",
  );
  requireString(
    record.publication_policy_version,
    "publication_policy_version",
  );
  requireUtc(record.published_at_utc, "published_at_utc");
  for (const field of [
    "source_private_fingerprint",
    "sanitized_content_fingerprint",
  ]) {
    const item = requireString(record[field], field);
    if (!FINGERPRINT.test(item)) {
      fail(`${field} must be a fingerprint`);
    }
  }
}

function validateFreshness(value: unknown): void {
  const record = exactRecord(
    value,
    ["as_of_utc", "max_age_seconds", "state"],
    "freshness",
  );
  requireUtc(record.as_of_utc, "freshness.as_of_utc");
  if (
    !Number.isSafeInteger(record.max_age_seconds) ||
    typeof record.max_age_seconds !== "number" ||
    record.max_age_seconds < 0
  ) {
    fail("freshness.max_age_seconds must be a non-negative integer");
  }
  if (
    record.state !== "current" &&
    record.state !== "stale" &&
    record.state !== "unknown"
  ) {
    fail("freshness.state is unsupported");
  }
}

function assertIdentity(
  record: Record<string, unknown>,
  expectedType: string,
): void {
  if (
    record.schema_version !== "1.0.0" ||
    record.object_type !== expectedType
  ) {
    fail(`evidence identity must describe ${expectedType}`);
  }
  requireEvidenceId(record.evidence_id, "evidence_id");
  const fingerprint = requireString(
    record.content_fingerprint,
    "content_fingerprint",
  );
  if (!FINGERPRINT.test(fingerprint)) {
    fail("content_fingerprint is invalid");
  }
}

function exactRecord(
  value: unknown,
  keys: string[],
  label: string,
): Record<string, unknown> {
  if (!isRecord(value)) {
    fail(`${label} must be an object`);
  }
  const expected = new Set(keys);
  const actual = Object.keys(value);
  if (
    actual.length !== expected.size ||
    actual.some((key) => !expected.has(key))
  ) {
    fail(`${label} has unexpected or missing fields`);
  }
  return value;
}

function validateArray<T>(
  value: unknown,
  maximum: number,
  validator: (item: unknown) => T,
  field: string,
): T[] {
  if (!Array.isArray(value) || value.length > maximum) {
    fail(`${field} must be a bounded array`);
  }
  return value.map((item) => validator(item));
}

function requireString(value: unknown, field: string): string {
  if (typeof value !== "string" || value.length === 0) {
    fail(`${field} must be a non-empty string`);
  }
  return value;
}

function requireStringArray(value: unknown, field: string): string[] {
  if (
    !Array.isArray(value) ||
    value.length > MAX_REFERENCES ||
    value.some((item) => typeof item !== "string" || item.length === 0)
  ) {
    fail(`${field} must be a bounded array of non-empty strings`);
  }
  return value;
}

function requireEvidenceId(value: unknown, field: string): string {
  const result = requireString(value, field);
  if (!EVIDENCE_ID.test(result)) {
    fail(`${field} must be an evidence ID`);
  }
  return result;
}

function requireStatus(value: unknown): EvidenceStatus {
  if (
    typeof value !== "string" ||
    !EVIDENCE_STATUSES.includes(value as EvidenceStatus)
  ) {
    fail("status is unsupported");
  }
  return value as EvidenceStatus;
}

function requireGitSha(value: unknown, field: string): void {
  if (value !== null && (typeof value !== "string" || !GIT_SHA.test(value))) {
    fail(`${field} must be a Git SHA, synthetic marker, or null`);
  }
}

function requireUtc(value: unknown, field: string): void {
  if (
    typeof value !== "string" ||
    !value.endsWith("Z") ||
    Number.isNaN(Date.parse(value))
  ) {
    fail(`${field} must be a UTC timestamp`);
  }
}

function fail(message: string): never {
  throw new HttpError(422, "package_schema_rejected", message);
}
