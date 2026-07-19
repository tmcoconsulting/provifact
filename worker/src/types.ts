export type JsonPrimitive = boolean | number | string | null;
export type JsonValue =
  JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };

export const EVIDENCE_STATUSES = [
  "observed",
  "matches desired state",
  "differs from desired state",
  "additional evidence required",
  "human review required",
  "not evaluated",
] as const;

export type EvidenceStatus = (typeof EVIDENCE_STATUSES)[number];
export type RuntimeMode = "fixture" | "openai";

export interface EvidenceIdentity {
  [key: string]: JsonValue;
  schema_version: "1.0.0";
  object_type: string;
  evidence_id: string;
  content_fingerprint: string;
}

export interface DesiredStateRecord extends EvidenceIdentity {
  object_type: "desired_state_record";
  desired_state_git_commit_sha: string | null;
  desired_value: JsonValue;
  description: string;
  evaluation_mode: string;
  platform: string;
  record_key: string;
  setting_key: string;
  title: string;
}

export interface Observation extends EvidenceIdentity {
  object_type: "normalized_configuration_observation";
  collection_evidence_id: string;
  freshness: {
    [key: string]: JsonValue;
    as_of_utc: string;
    max_age_seconds: number;
    state: "current" | "stale" | "unknown";
  };
  observation_state: string;
  observed_value: JsonValue;
  platform: string;
  provider_evidence_id: string;
  setting_key: string;
  source_modified_at_utc: string | null;
}

export interface DriftFinding extends EvidenceIdentity {
  object_type: "deterministic_drift_finding";
  additional_evidence_required: string[];
  collection_evidence_id: string;
  desired_state_evidence_id: string;
  desired_state_git_commit_sha: string | null;
  deterministic_algorithm_version: string;
  input_fingerprints: string[];
  observation_evidence_ids: string[];
  status: EvidenceStatus;
}

export interface PublicEvidencePackage extends EvidenceIdentity {
  object_type: "sanitized_public_evidence_package";
  synthetic: boolean;
  source_type: "curated-synthetic-fixture" | "sanitized-live-collection";
  provider: EvidenceIdentity;
  collection: EvidenceIdentity & {
    collection_timestamp_utc: string;
    desired_state_git_commit_sha: string | null;
    deterministic_algorithm_version: string;
    provider_evidence_id: string;
  };
  desired_state: DesiredStateRecord[];
  observations: Observation[];
  findings: DriftFinding[];
  evidence_references: EvidenceIdentity[];
  publication: {
    [key: string]: JsonValue;
    publication_policy_version: string;
    published_at_utc: string;
    sanitized_content_fingerprint: string;
    source_private_fingerprint: string;
  };
  human_approval_status: "human review required";
}

export interface DeterministicClaim {
  [key: string]: JsonValue;
  claim_code: "finding_status";
  claim_value: EvidenceStatus;
}

export interface DriftExplanation {
  [key: string]: JsonValue;
  finding_evidence_id: string;
  deterministic_status: EvidenceStatus;
  deterministic_claim: DeterministicClaim;
  change_or_drift_explanation: string;
  technical_impact: string;
  evidence_references: string[];
}

export interface NarrativeModelOutput {
  [key: string]: JsonValue;
  executive_summary: string;
  drift_explanations: DriftExplanation[];
  limitations: string[];
  additional_evidence_required: string[];
  suggested_human_review_questions: string[];
}

export interface NarrativeEvidence
  extends EvidenceIdentity, NarrativeModelOutput {
  object_type: "generated_narrative";
  ai_generated_analysis: true;
  human_review_required: true;
  model: string;
  source_package_evidence_id: string;
}

export interface VerificationEvidence extends EvidenceIdentity {
  object_type: "narrative_verification_result";
  accepted: boolean;
  accepted_claims: string[];
  human_review_required: true;
  narrative_evidence_id: string;
  reasons: string[];
  rejected_claims: string[];
  source_package_evidence_id: string;
  verifier_version: string;
}
