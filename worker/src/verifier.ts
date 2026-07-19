import { isRecord, makeEvidenceObject } from "./evidence";
import { HttpError } from "./security";
import {
  EVIDENCE_STATUSES,
  type DriftExplanation,
  type EvidenceStatus,
  type NarrativeEvidence,
  type NarrativeModelOutput,
  type PublicEvidencePackage,
  type VerificationEvidence,
} from "./types";

export const WORKER_VERIFIER_VERSION =
  "evidenceops-worker-narrative-verifier-v1.0.0";

const VERDICT =
  /\b(?:compliant|certified|control\s+(?:is\s+)?satisfied|MET|meets?\s+compliance)\b/i;
const FRAMEWORK_ID =
  /\b(?:(?:CMMC|NIST|CIS|STIG|ISO)\s*[-: ]?[A-Z]*\d+(?:\.\d+)*|[A-Z]{2}-\d+)\b/gi;
const EVIDENCE_MENTION = /\bev1-[0-9a-f]{24}\b/g;
const EVIDENCE_ID = /^ev1-[0-9a-f]{24}$/;

export function parseNarrativeModelOutput(
  value: unknown,
): NarrativeModelOutput {
  const root = exactRecord(
    value,
    [
      "executive_summary",
      "drift_explanations",
      "limitations",
      "additional_evidence_required",
      "suggested_human_review_questions",
    ],
    "narrative model output",
  );
  const executiveSummary = requireString(
    root.executive_summary,
    "executive_summary",
  );
  if (
    !Array.isArray(root.drift_explanations) ||
    root.drift_explanations.length > 100
  ) {
    invalid("drift_explanations must be a bounded array");
  }
  const explanations = root.drift_explanations.map((item) =>
    parseExplanation(item),
  );
  const limitations = requireNonEmptyStringArray(
    root.limitations,
    "limitations",
  );
  const additionalEvidence = requireNonEmptyStringArray(
    root.additional_evidence_required,
    "additional_evidence_required",
  );
  const questions = requireNonEmptyStringArray(
    root.suggested_human_review_questions,
    "suggested_human_review_questions",
  );
  return {
    executive_summary: executiveSummary,
    drift_explanations: explanations,
    limitations,
    additional_evidence_required: additionalEvidence,
    suggested_human_review_questions: questions,
  };
}

function parseExplanation(value: unknown): DriftExplanation {
  const record = exactRecord(
    value,
    [
      "finding_evidence_id",
      "deterministic_status",
      "deterministic_claim",
      "change_or_drift_explanation",
      "technical_impact",
      "evidence_references",
    ],
    "drift explanation",
  );
  const findingId = requireEvidenceId(
    record.finding_evidence_id,
    "finding_evidence_id",
  );
  const status = requireStatus(
    record.deterministic_status,
    "deterministic_status",
  );
  const claim = exactRecord(
    record.deterministic_claim,
    ["claim_code", "claim_value"],
    "deterministic claim",
  );
  if (claim.claim_code !== "finding_status") {
    invalid("deterministic claim code is unsupported");
  }
  const claimValue = requireStatus(claim.claim_value, "claim_value");
  const references = requireStringArray(
    record.evidence_references,
    "evidence_references",
  );
  for (const reference of references) {
    requireEvidenceId(reference, "evidence_references");
  }
  return {
    finding_evidence_id: findingId,
    deterministic_status: status,
    deterministic_claim: {
      claim_code: "finding_status",
      claim_value: claimValue,
    },
    change_or_drift_explanation: requireString(
      record.change_or_drift_explanation,
      "change_or_drift_explanation",
    ),
    technical_impact: requireString(
      record.technical_impact,
      "technical_impact",
    ),
    evidence_references: references,
  };
}

export async function buildNarrativeEvidence(
  output: NarrativeModelOutput,
  packageDocument: PublicEvidencePackage,
  model: string,
): Promise<NarrativeEvidence> {
  const document = await makeEvidenceObject("generated_narrative", {
    ai_generated_analysis: true,
    human_review_required: true,
    model,
    source_package_evidence_id: packageDocument.evidence_id,
    ...output,
  });
  return document as NarrativeEvidence;
}

export async function verifyNarrative(
  narrative: NarrativeEvidence,
  packageDocument: PublicEvidencePackage,
): Promise<VerificationEvidence> {
  const reasons: string[] = [];
  const acceptedClaims = new Set<string>();
  const rejectedClaims = new Set<string>();
  if (narrative.source_package_evidence_id !== packageDocument.evidence_id) {
    reasons.push(
      "narrative source package ID does not match the supplied package",
    );
  }

  const packageIds = packageEvidenceIds(packageDocument);
  const findings = new Map(
    packageDocument.findings.map((finding) => [finding.evidence_id, finding]),
  );
  const prose = narrativeText(narrative);
  const ungroundedMentions = [...new Set(prose.match(EVIDENCE_MENTION) ?? [])]
    .filter((id) => !packageIds.has(id))
    .sort();
  if (ungroundedMentions.length > 0) {
    reasons.push(
      `nonexistent evidence IDs in narrative text: ${ungroundedMentions.join(", ")}`,
    );
  }
  if (VERDICT.test(prose)) {
    reasons.push("unsupported compliance or certification verdict");
  }
  const packageText = JSON.stringify(packageDocument);
  const unsupportedFrameworks = [...new Set(prose.match(FRAMEWORK_ID) ?? [])]
    .filter((identifier) => !packageText.includes(identifier))
    .sort();
  if (unsupportedFrameworks.length > 0) {
    reasons.push(
      `unsupported control or framework ID: ${unsupportedFrameworks.join(", ")}`,
    );
  }
  if (!/\bhuman (?:review|reviewer|assessor)\b/i.test(prose)) {
    reasons.push("required human-review language is missing");
  }

  const explanationIds = narrative.drift_explanations.map(
    (item) => item.finding_evidence_id,
  );
  const counts = new Map<string, number>();
  for (const id of explanationIds) {
    counts.set(id, (counts.get(id) ?? 0) + 1);
  }
  const duplicates = [...counts.entries()]
    .filter(([, count]) => count > 1)
    .map(([id]) => id)
    .sort();
  const narrativeIds = new Set(explanationIds);
  const expectedIds = new Set(findings.keys());
  const missing = [...expectedIds].filter((id) => !narrativeIds.has(id)).sort();
  const unknown = [...narrativeIds].filter((id) => !expectedIds.has(id)).sort();
  if (duplicates.length > 0) {
    reasons.push(`duplicate finding explanation IDs: ${duplicates.join(", ")}`);
  }
  if (missing.length > 0) {
    reasons.push(
      `missing deterministic finding explanations: ${missing.join(", ")}`,
    );
  }
  if (unknown.length > 0) {
    reasons.push(`unknown finding explanation IDs: ${unknown.join(", ")}`);
  }

  for (const explanation of narrative.drift_explanations) {
    const finding = findings.get(explanation.finding_evidence_id);
    const claimReasons: string[] = [];
    if (finding === undefined) {
      claimReasons.push(
        "typed deterministic claim references an unknown finding",
      );
    } else {
      if (explanation.deterministic_status !== finding.status) {
        claimReasons.push(
          "narrative contradicts the deterministic finding status",
        );
      }
      if (
        explanation.deterministic_claim.claim_code !== "finding_status" ||
        explanation.deterministic_claim.claim_value !== finding.status ||
        explanation.deterministic_claim.claim_value !==
          explanation.deterministic_status
      ) {
        claimReasons.push(
          "typed deterministic claim contradicts the finding status",
        );
      }
      const permitted = new Set([
        finding.evidence_id,
        finding.collection_evidence_id,
        finding.desired_state_evidence_id,
        ...finding.observation_evidence_ids,
      ]);
      const unrelated = [...new Set(explanation.evidence_references)]
        .filter((id) => !permitted.has(id))
        .sort();
      if (unrelated.length > 0) {
        claimReasons.push("claim cites evidence unrelated to its finding");
      }
    }
    const outside = [...new Set(explanation.evidence_references)]
      .filter((id) => !packageIds.has(id))
      .sort();
    if (outside.length > 0) {
      claimReasons.push(
        `evidence references outside supplied package: ${outside.join(", ")}`,
      );
    }
    const label = `${explanation.finding_evidence_id}:finding_status=${explanation.deterministic_status}`;
    if (
      claimReasons.length > 0 ||
      duplicates.includes(explanation.finding_evidence_id) ||
      finding === undefined
    ) {
      rejectedClaims.add(label);
      reasons.push(...claimReasons);
    } else {
      acceptedClaims.add(label);
    }
  }

  for (const generatedField of generatedProseClaims(narrative)) {
    rejectedClaims.add(generatedField);
  }
  reasons.push(
    "free-form generated analysis is not machine-verifiable and remains quarantined for human review",
  );
  const deduplicatedReasons = [...new Set(reasons)];
  const document = await makeEvidenceObject("narrative_verification_result", {
    narrative_evidence_id: narrative.evidence_id,
    source_package_evidence_id: packageDocument.evidence_id,
    verifier_version: WORKER_VERIFIER_VERSION,
    accepted: deduplicatedReasons.length === 0 && rejectedClaims.size === 0,
    accepted_claims: [...acceptedClaims].sort(),
    rejected_claims: [...rejectedClaims].sort(),
    reasons: deduplicatedReasons,
    human_review_required: true,
  });
  return document as VerificationEvidence;
}

function packageEvidenceIds(
  packageDocument: PublicEvidencePackage,
): Set<string> {
  return new Set([
    packageDocument.evidence_id,
    packageDocument.provider.evidence_id,
    packageDocument.collection.evidence_id,
    ...packageDocument.desired_state.map((item) => item.evidence_id),
    ...packageDocument.observations.map((item) => item.evidence_id),
    ...packageDocument.findings.map((item) => item.evidence_id),
    ...packageDocument.evidence_references.map((item) => item.evidence_id),
  ]);
}

function narrativeText(narrative: NarrativeEvidence): string {
  return [
    narrative.executive_summary,
    ...narrative.limitations,
    ...narrative.additional_evidence_required,
    ...narrative.suggested_human_review_questions,
    ...narrative.drift_explanations.flatMap((item) => [
      item.change_or_drift_explanation,
      item.technical_impact,
    ]),
  ].join("\n");
}

function generatedProseClaims(narrative: NarrativeEvidence): string[] {
  const claims = ["generated prose quarantined: executive_summary"];
  for (const field of [
    "limitations",
    "additional_evidence_required",
    "suggested_human_review_questions",
  ] as const) {
    narrative[field].forEach((_value, index) => {
      claims.push(`generated prose quarantined: ${field}[${index}]`);
    });
  }
  narrative.drift_explanations.forEach((_value, index) => {
    claims.push(
      `generated prose quarantined: drift_explanations[${index}].change_or_drift_explanation`,
    );
    claims.push(
      `generated prose quarantined: drift_explanations[${index}].technical_impact`,
    );
  });
  return claims;
}

function exactRecord(
  value: unknown,
  keys: string[],
  label: string,
): Record<string, unknown> {
  if (!isRecord(value)) {
    invalid(`${label} must be an object`);
  }
  const expected = new Set(keys);
  const actual = Object.keys(value);
  if (
    actual.length !== expected.size ||
    actual.some((key) => !expected.has(key))
  ) {
    invalid(`${label} has unexpected or missing fields`);
  }
  return value;
}

function requireString(value: unknown, field: string): string {
  if (typeof value !== "string" || value.length === 0) {
    invalid(`${field} must be a non-empty string`);
  }
  return value;
}

function requireStringArray(value: unknown, field: string): string[] {
  if (
    !Array.isArray(value) ||
    value.length > 500 ||
    value.some((item) => typeof item !== "string" || item.length === 0)
  ) {
    invalid(`${field} must be a bounded array of non-empty strings`);
  }
  return value;
}

function requireNonEmptyStringArray(value: unknown, field: string): string[] {
  const result = requireStringArray(value, field);
  if (result.length === 0) {
    invalid(`${field} must not be empty`);
  }
  return result;
}

function requireEvidenceId(value: unknown, field: string): string {
  const result = requireString(value, field);
  if (!EVIDENCE_ID.test(result)) {
    invalid(`${field} must be an evidence ID`);
  }
  return result;
}

function requireStatus(value: unknown, field: string): EvidenceStatus {
  if (
    typeof value !== "string" ||
    !EVIDENCE_STATUSES.includes(value as EvidenceStatus)
  ) {
    invalid(`${field} is unsupported`);
  }
  return value as EvidenceStatus;
}

function invalid(message: string): never {
  throw new HttpError(502, "model_output_rejected", message);
}
