import type { WorkerEnv } from "./env";
import { canonicalJson, isRecord, sha256 } from "./evidence";
import {
  classifyUpstreamFailure,
  readUpstreamErrorMetadata,
  type UpstreamFailure,
} from "./narrative";
import {
  assertMissionEgressSafe,
  hasUsableOpenAIKey,
  HttpError,
  OPENAI_TIMEOUT_MS,
  readBoundedPublicMissionResponse,
  readBoundedResponse,
} from "./security";
import type { JsonValue, RuntimeMode } from "./types";

const OPENAI_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses";
const MAX_QUESTION_LENGTH = 240;
const MAX_FINDINGS = 32;
const MAX_REQUIREMENTS = 128;
const MAX_OUTPUT_TOKENS = 700;
const VERIFIER_VERSION = "evidenceops-assistant-verifier-v1.0.0";
const INSUFFICIENT =
  "Provifact does not have sufficient collected evidence to answer this question.";
const VERDICT =
  /\b(?:compliant|certified|certification|control\s+(?:is\s+)?satisfied|assessment\s+(?:is\s+)?complete|risk\s+accepted|meets?\s+(?:the\s+)?(?:standard|framework|compliance))\b/i;
const REFERENCE = /\b(?:finding|req|gap|mission)-[0-9a-f]{24}\b/g;

type Intent =
  | "alignment"
  | "assignment_drift"
  | "attention"
  | "changes"
  | "collection_gaps"
  | "conflicts"
  | "device_posture"
  | "evidence"
  | "filevault"
  | "framework_meaning"
  | "high_severity"
  | "intune_review"
  | "insufficient"
  | "limitations"
  | "provenance"
  | "resolved"
  | "unevaluated";

const ASSISTANT_PAGES = [
  "overview",
  "findings",
  "settings",
  "changes",
  "evidence",
  "documentation",
] as const;

type AssistantPage = (typeof ASSISTANT_PAGES)[number];

interface AssistantInput {
  page: AssistantPage;
  question: string;
  selected_evidence_id?: string;
  snapshot_id: string;
}

interface MissionFinding {
  finding_id: string;
  rule_id: string;
  title: string;
  platform: string;
  drift_type: string;
  severity: string;
  expected_value: JsonValue;
  observed_value: JsonValue;
  assignment_summary: string;
  source_evidence_ids: string[];
}

interface MissionRequirement {
  requirement_id: string;
  rule_id: string;
  outcome: string;
  severity: string;
  title: string;
  expected_value?: JsonValue;
  observed_value?: JsonValue;
  assignment_summary?: string;
  source_evidence_ids?: string[];
  mappings?: Record<string, JsonValue>;
}

interface MissionDocument {
  schema_version: "2.1.0";
  snapshot_id: string;
  content_fingerprint: string;
  data_mode: string;
  collection: Record<string, JsonValue> & { collected_at_utc: string };
  baseline: Record<string, JsonValue> & { benchmark_version: string };
  metrics: Record<string, JsonValue>;
  devices: Record<string, JsonValue>;
  ai: Record<string, JsonValue>;
  requirements: MissionRequirement[];
  findings: MissionFinding[];
  collection_gaps: Array<{ [key: string]: JsonValue; gap_id: string }>;
  changes: Record<string, JsonValue>;
  framework_coverage: Record<string, JsonValue>;
  resources: Array<{ [key: string]: JsonValue }>;
  unmapped_objects: Array<{ [key: string]: JsonValue }>;
}

export interface MissionStatus {
  assistant_mode_declared: string;
  baseline_name: string;
  baseline_version: string;
  content_fingerprint: string;
  data_mode: string;
  evidence_timestamp: string;
  freshness_maximum_age_seconds: number;
  freshness_state: string;
  provider: string;
  snapshot_id: string;
}

interface AssistantClaim {
  claim_code: string;
  subject_id: string;
  claim_value: JsonValue;
}

interface AssistantOutput {
  direct_answer: string;
  claims: AssistantClaim[];
  evidence_references: string[];
  evidence_sufficiency: "insufficient" | "partial" | "verified";
  limitations: string[];
  additional_evidence_required: string[];
  suggested_human_review_questions: string[];
}

interface AssistantContext {
  intent: Intent;
  page: AssistantPage;
  evidence_timestamp: string;
  baseline_version: string;
  facts: JsonValue;
  expected_claims: AssistantClaim[];
  allowed_references: string[];
}

export interface AssistantResult {
  mode: RuntimeMode;
  ai_model_call_performed: boolean;
  human_review_required: true;
  source_snapshot_id: string;
  question_intent: Intent;
  answer: AssistantOutput & {
    ai_generated_analysis: boolean;
    evidence_timestamp: string;
    baseline_version: string;
    human_review_required: true;
  };
  verification: {
    status: "insufficient_evidence" | "rejected" | "typed_claims_verified";
    verifier_version: string;
    typed_claims_accepted: string[];
    typed_claims_rejected: string[];
    generated_prose_quarantined: true;
    reasons: string[];
    human_review_required: true;
  };
}

export interface AssistantDependencies {
  outboundFetch: typeof fetch;
}

export async function createAssistantAnswer(
  request: Request,
  env: WorkerEnv,
  body: unknown,
  dependencies: AssistantDependencies,
): Promise<AssistantResult> {
  const input = parseAssistantInput(body);
  assertMissionEgressSafe(input);
  const mission = await loadMission(request, env);
  if (input.snapshot_id !== mission.snapshot_id) {
    throw new HttpError(
      409,
      "mission_package_changed",
      "the selected evidence package is no longer current",
    );
  }
  const intent = classifyQuestion(input.question, input.selected_evidence_id);
  const context = selectContext(
    mission,
    intent,
    input.page,
    input.selected_evidence_id,
  );
  assertMissionEgressSafe(context);
  const mode = runtimeMode(env.EVIDENCEOPS_MODE);
  const output =
    mode === "fixture"
      ? fixtureOutput(input.question, context)
      : await openAIOutput(env, input.question, context, dependencies);
  assertMissionEgressSafe(output);
  const verification = verifyOutput(output, context);
  return {
    mode,
    ai_model_call_performed: mode === "openai",
    human_review_required: true,
    source_snapshot_id: mission.snapshot_id,
    question_intent: intent,
    answer: {
      ...output,
      ai_generated_analysis: mode === "openai",
      evidence_timestamp: context.evidence_timestamp,
      baseline_version: context.baseline_version,
      human_review_required: true,
    },
    verification,
  };
}

function parseAssistantInput(value: unknown): AssistantInput {
  if (!isRecord(value)) {
    throw new HttpError(
      422,
      "assistant_request_rejected",
      "assistant request has unexpected or missing fields",
    );
  }
  const fields = Object.keys(value).sort().join(",");
  if (
    fields !== "page,question,snapshot_id" &&
    fields !== "page,question,selected_evidence_id,snapshot_id"
  ) {
    throw new HttpError(
      422,
      "assistant_request_rejected",
      "assistant request has unexpected or missing fields",
    );
  }
  if (
    typeof value.question !== "string" ||
    value.question.length < 4 ||
    value.question.length > MAX_QUESTION_LENGTH ||
    Array.from(value.question).some((character) => {
      const code = character.charCodeAt(0);
      return code < 32 || code === 127;
    })
  ) {
    throw new HttpError(
      422,
      "assistant_question_rejected",
      "assistant question is outside the bounded contract",
    );
  }
  if (
    typeof value.snapshot_id !== "string" ||
    !/^mission-[0-9a-f]{24}$/.test(value.snapshot_id)
  ) {
    throw new HttpError(
      422,
      "assistant_request_rejected",
      "mission package ID is invalid",
    );
  }
  if (
    typeof value.page !== "string" ||
    !ASSISTANT_PAGES.includes(value.page as AssistantPage)
  ) {
    throw new HttpError(
      422,
      "assistant_request_rejected",
      "assistant page context is invalid",
    );
  }
  if (
    value.selected_evidence_id !== undefined &&
    (typeof value.selected_evidence_id !== "string" ||
      !/^(?:finding|req|gap|mission)-[0-9a-f]{24}$/.test(
        value.selected_evidence_id,
      ))
  ) {
    throw new HttpError(
      422,
      "assistant_request_rejected",
      "selected evidence reference is invalid",
    );
  }
  return {
    page: value.page as AssistantPage,
    question: value.question.trim(),
    snapshot_id: value.snapshot_id,
    ...(value.selected_evidence_id === undefined
      ? {}
      : { selected_evidence_id: value.selected_evidence_id }),
  };
}

async function loadMission(
  request: Request,
  env: WorkerEnv,
): Promise<MissionDocument> {
  const url = new URL("/assets/data/mission-control.json", request.url);
  const response = await env.ASSETS.fetch(new Request(url, { method: "GET" }));
  if (!response.ok) {
    throw new HttpError(
      503,
      "mission_unavailable",
      "mission evidence is unavailable",
    );
  }
  const value = await readBoundedPublicMissionResponse(response);
  const mission = validateMission(value);
  await verifyMissionIdentity(mission);
  assertMissionEgressSafe(mission);
  return mission;
}

export async function readMissionStatus(
  request: Request,
  env: WorkerEnv,
): Promise<MissionStatus> {
  const mission = await loadMission(request, env);
  return {
    assistant_mode_declared:
      isRecord(mission.ai) && typeof mission.ai.mode === "string"
        ? mission.ai.mode
        : "unavailable",
    baseline_name:
      typeof mission.baseline.name === "string"
        ? mission.baseline.name
        : "approved baseline unavailable",
    baseline_version: mission.baseline.benchmark_version,
    content_fingerprint: mission.content_fingerprint,
    data_mode: mission.data_mode,
    evidence_timestamp: mission.collection.collected_at_utc,
    freshness_maximum_age_seconds:
      isRecord(mission.collection.freshness) &&
      typeof mission.collection.freshness.maximum_age_seconds === "number"
        ? mission.collection.freshness.maximum_age_seconds
        : 0,
    freshness_state:
      isRecord(mission.collection.freshness) &&
      typeof mission.collection.freshness.state === "string"
        ? mission.collection.freshness.state
        : "unknown",
    provider:
      typeof mission.collection.provider === "string"
        ? mission.collection.provider
        : "provider unavailable",
    snapshot_id: mission.snapshot_id,
  };
}

function validateMission(value: unknown): MissionDocument {
  if (!isRecord(value)) invalidMission();
  const required = new Set([
    "ai",
    "baseline",
    "changes",
    "collection",
    "collection_gaps",
    "content_fingerprint",
    "data_mode",
    "devices",
    "findings",
    "framework_coverage",
    "generated_at_utc",
    "human_approval_status",
    "metrics",
    "privacy",
    "requirements",
    "resources",
    "schema_version",
    "snapshot_id",
    "unmapped_objects",
  ]);
  if (
    Object.keys(value).length !== required.size ||
    Object.keys(value).some((key) => !required.has(key)) ||
    value.schema_version !== "2.1.0" ||
    typeof value.snapshot_id !== "string" ||
    !/^mission-[0-9a-f]{24}$/.test(value.snapshot_id) ||
    typeof value.content_fingerprint !== "string" ||
    !/^sha256:[0-9a-f]{64}$/.test(value.content_fingerprint) ||
    !isRecord(value.collection) ||
    typeof value.collection.collected_at_utc !== "string" ||
    typeof value.collection.provider !== "string" ||
    !isRecord(value.collection.freshness) ||
    typeof value.collection.freshness.state !== "string" ||
    typeof value.collection.freshness.maximum_age_seconds !== "number" ||
    !isRecord(value.baseline) ||
    typeof value.baseline.benchmark_version !== "string" ||
    typeof value.baseline.name !== "string" ||
    !isRecord(value.ai) ||
    typeof value.ai.mode !== "string" ||
    !isRecord(value.metrics) ||
    !isRecord(value.devices) ||
    !isRecord(value.changes) ||
    !Array.isArray(value.requirements) ||
    value.requirements.length > MAX_REQUIREMENTS ||
    !Array.isArray(value.findings) ||
    value.findings.length > MAX_FINDINGS ||
    !Array.isArray(value.collection_gaps) ||
    !isRecord(value.framework_coverage) ||
    !Array.isArray(value.resources) ||
    !Array.isArray(value.unmapped_objects)
  ) {
    invalidMission();
  }
  for (const requirement of value.requirements) {
    if (
      !isRecord(requirement) ||
      typeof requirement.requirement_id !== "string" ||
      !/^req-[0-9a-f]{24}$/.test(requirement.requirement_id) ||
      typeof requirement.rule_id !== "string" ||
      typeof requirement.outcome !== "string" ||
      typeof requirement.severity !== "string" ||
      typeof requirement.title !== "string"
    )
      invalidMission();
  }
  for (const finding of value.findings) {
    if (
      !isRecord(finding) ||
      typeof finding.finding_id !== "string" ||
      !/^finding-[0-9a-f]{24}$/.test(finding.finding_id) ||
      typeof finding.rule_id !== "string" ||
      typeof finding.title !== "string" ||
      typeof finding.platform !== "string" ||
      typeof finding.drift_type !== "string" ||
      typeof finding.severity !== "string" ||
      typeof finding.assignment_summary !== "string" ||
      !Array.isArray(finding.source_evidence_ids) ||
      finding.source_evidence_ids.some((id) => typeof id !== "string")
    )
      invalidMission();
  }
  return value as unknown as MissionDocument;
}

function invalidMission(): never {
  throw new HttpError(
    503,
    "mission_schema_rejected",
    "mission evidence failed validation",
  );
}

async function verifyMissionIdentity(mission: MissionDocument): Promise<void> {
  const unsigned: Record<string, JsonValue> = {};
  for (const [key, value] of Object.entries(mission)) {
    if (key !== "snapshot_id" && key !== "content_fingerprint")
      unsigned[key] = value;
  }
  const digest = await sha256(canonicalJson(unsigned));
  if (
    mission.content_fingerprint !== `sha256:${digest}` ||
    mission.snapshot_id !== `mission-${digest.slice(0, 24)}`
  )
    invalidMission();
}

function classifyQuestion(
  question: string,
  selectedEvidenceId?: string,
): Intent {
  const normalized = question.toLowerCase();
  if (
    selectedEvidenceId !== undefined &&
    /evidence|support|this (?:finding|setting|requirement)|explain/.test(
      normalized,
    )
  )
    return "evidence";
  if (/filevault|encryption/.test(normalized)) return "filevault";
  if (/resolved|closed since|no longer drift/.test(normalized))
    return "resolved";
  if (/what changed|since (?:the )?(?:last|previous)|trend/.test(normalized))
    return "changes";
  if (/review in intune|what.*intune|next step/.test(normalized))
    return "intune_review";
  if (
    /requires? (?:my )?attention|what should i review|needs? review|priority/.test(
      normalized,
    )
  )
    return "attention";
  if (/not (?:currently )?evaluated|unevaluated|unmapped/.test(normalized))
    return "unevaluated";
  if (/framework|cross[- ]reference|nist|cmmc|stig/.test(normalized))
    return "framework_meaning";
  if (
    /live tenant|live data|data provenance|when was.*collected/.test(normalized)
  )
    return "provenance";
  if (
    /cannot conclude|not conclude|can(?:not|'t) prove|limitations?/.test(
      normalized,
    )
  )
    return "limitations";
  if (/highest|high(?:est)?[- ]severity|critical/.test(normalized))
    return "high_severity";
  if (/unassign|assignment gap/.test(normalized)) return "assignment_drift";
  if (/conflict|overlap/.test(normalized)) return "conflicts";
  if (/could not|unavailable|collection gap|permission gap/.test(normalized))
    return "collection_gaps";
  if (
    /device.*noncompliant|noncompliant.*device|device posture/.test(normalized)
  )
    return "device_posture";
  if (/overall|alignment|cis level 1/.test(normalized)) return "alignment";
  return "insufficient";
}

function selectContext(
  mission: MissionDocument,
  intent: Intent,
  page: AssistantPage,
  selectedEvidenceId?: string,
): AssistantContext {
  const base = {
    intent,
    page,
    evidence_timestamp: mission.collection.collected_at_utc,
    baseline_version: mission.baseline.benchmark_version,
  };
  const selectedEvidence = resolveSelectedEvidence(mission, selectedEvidenceId);
  let facts: JsonValue;
  let references: string[] = [mission.snapshot_id];
  let claims: AssistantClaim[] = [];
  if (intent === "alignment") {
    facts = {
      alignment_percent: mission.metrics.alignment_percent ?? null,
      denominator: mission.metrics.alignment_denominator ?? null,
      explanation: mission.metrics.alignment_denominator_explanation ?? null,
    };
    claims = [
      claim(
        "alignment_percent",
        mission.snapshot_id,
        facts.alignment_percent ?? null,
      ),
    ];
  } else if (intent === "device_posture") {
    const state = mission.devices.by_compliance_state;
    facts = { aggregate_only: true, by_compliance_state: state ?? {} };
    const noncompliant =
      isRecord(state) && typeof state.noncompliant === "number"
        ? state.noncompliant
        : 0;
    claims = [claim("device_aggregate", "noncompliant", noncompliant)];
  } else if (intent === "changes") {
    const changedIds = stringArray(mission.changes.changed_requirements);
    const newIds = stringArray(mission.changes.new_drift);
    const resolvedIds = stringArray(mission.changes.resolved_drift);
    const changed = changedIds.length;
    facts = {
      previous_snapshot_id: stringOrNull(mission.changes.previous_snapshot_id),
      previous_collection_timestamp_utc: stringOrNull(
        mission.changes.previous_collection_timestamp_utc,
      ),
      current_collection_timestamp_utc:
        stringOrNull(mission.changes.current_collection_timestamp_utc) ??
        mission.collection.collected_at_utc,
      alignment_change_points: mission.changes.alignment_change_points ?? null,
      changed_requirements: changedIds.map((identifier) =>
        requirementOrFindingSummary(mission, identifier),
      ),
      new_drift: newIds.map((identifier) =>
        requirementOrFindingSummary(mission, identifier),
      ),
      resolved_drift: resolvedIds.map((identifier) =>
        requirementOrFindingSummary(mission, identifier),
      ),
      unchanged_requirement_count: stringArray(
        mission.changes.unchanged_requirements,
      ).length,
    };
    references = [
      mission.snapshot_id,
      ...changedIds.flatMap((identifier) =>
        evidenceReferencesForIdentifier(mission, identifier),
      ),
    ];
    claims = [claim("change_count", mission.snapshot_id, changed)];
  } else if (intent === "resolved") {
    const resolved = stringArray(mission.changes.resolved_drift);
    facts = {
      previous_snapshot_id: stringOrNull(mission.changes.previous_snapshot_id),
      previous_collection_timestamp_utc: stringOrNull(
        mission.changes.previous_collection_timestamp_utc,
      ),
      current_collection_timestamp_utc:
        stringOrNull(mission.changes.current_collection_timestamp_utc) ??
        mission.collection.collected_at_utc,
      resolved_findings: resolved.map((identifier) =>
        requirementOrFindingSummary(mission, identifier),
      ),
    };
    references = [
      mission.snapshot_id,
      ...resolved.flatMap((identifier) =>
        evidenceReferencesForIdentifier(mission, identifier),
      ),
    ];
    claims = [
      claim("resolved_drift_count", mission.snapshot_id, resolved.length),
    ];
  } else if (intent === "attention" || intent === "intune_review") {
    const ordered = [...mission.findings].sort(
      (left, right) =>
        severityRank(right.severity) - severityRank(left.severity) ||
        left.title.localeCompare(right.title),
    );
    const selectedFindings =
      selectedEvidence?.kind === "finding" ? [selectedEvidence.value] : ordered;
    facts = selectedFindings.map(findingFact);
    references = [
      mission.snapshot_id,
      ...selectedFindings.flatMap((finding) => [
        finding.finding_id,
        ...requirementReferenceForFinding(mission, finding),
      ]),
    ];
    claims = selectedFindings.map((finding) =>
      claim("finding_outcome", finding.finding_id, finding.drift_type),
    );
  } else if (intent === "unevaluated") {
    facts = {
      total: mission.unmapped_objects.length,
      groups: groupUnevaluatedResources(mission.unmapped_objects),
      meaning:
        "These collected resources are visible but do not enter the approved macOS alignment denominator.",
    };
    claims = [
      claim(
        "unevaluated_resource_count",
        mission.snapshot_id,
        mission.unmapped_objects.length,
      ),
    ];
  } else if (intent === "framework_meaning") {
    facts = {
      framework_cross_references: frameworkFacts(mission.framework_coverage),
      meaning:
        "Distinct identifiers referenced by evaluated settings; not passed controls, coverage scores, certifications, or completed assessments.",
    };
    claims = [
      claim(
        "framework_reference_set_count",
        mission.snapshot_id,
        Object.keys(mission.framework_coverage).length,
      ),
    ];
  } else if (intent === "provenance") {
    facts = {
      data_mode: mission.data_mode,
      collected_at_utc: mission.collection.collected_at_utc,
      provider: mission.collection.provider ?? null,
      snapshot_id: mission.snapshot_id,
      baseline_name: mission.baseline.name ?? null,
      baseline_version: mission.baseline.benchmark_version,
    };
    claims = [claim("data_mode", mission.snapshot_id, mission.data_mode)];
  } else if (intent === "limitations") {
    facts = {
      cannot_conclude: [
        "organizational compliance",
        "certification",
        "control satisfaction",
        "assessment completion",
        "risk acceptance",
        "approved exception",
        "successful Intune remediation without a later collection",
      ],
      intune_write_capability: false,
      human_assessor_judgment_required: true,
    };
    claims = [claim("intune_write_capability", mission.snapshot_id, false)];
  } else if (intent === "evidence") {
    if (selectedEvidence === undefined) {
      facts = {
        evidence_missing:
          "Select a finding or requirement before asking for its evidence chain.",
      };
    } else {
      facts = selectedEvidence.fact;
      references = [mission.snapshot_id, ...selectedEvidence.references];
      claims = selectedEvidence.claims;
    }
  } else if (intent === "collection_gaps") {
    facts = mission.collection_gaps;
    references = [
      mission.snapshot_id,
      ...mission.collection_gaps.map((gap) => gap.gap_id),
    ];
    claims = [
      claim(
        "collection_gap_count",
        mission.snapshot_id,
        mission.collection_gaps.length,
      ),
    ];
  } else {
    const selectedFindings = mission.findings.filter((finding) => {
      if (intent === "filevault") return finding.rule_id.includes("filevault");
      if (intent === "high_severity") return finding.severity === "high";
      if (intent === "assignment_drift")
        return finding.drift_type === "Assignment drift";
      if (intent === "conflicts")
        return finding.drift_type === "Conflicting policy";
      return false;
    });
    const fileVaultRequirements =
      intent === "filevault" && selectedFindings.length === 0
        ? mission.requirements.filter((requirement) =>
            requirement.rule_id.includes("filevault"),
          )
        : [];
    if (fileVaultRequirements.length > 0) {
      facts = fileVaultRequirements.map(requirementFact);
      references = [
        mission.snapshot_id,
        ...fileVaultRequirements.map((item) => item.requirement_id),
      ];
      claims = fileVaultRequirements.map((item) =>
        claim("requirement_outcome", item.requirement_id, item.outcome),
      );
    } else {
      facts = selectedFindings.map(findingFact);
      references = [
        mission.snapshot_id,
        ...selectedFindings.flatMap((finding) => [
          finding.finding_id,
          ...requirementReferenceForFinding(mission, finding),
        ]),
      ];
      claims = selectedFindings.map((finding) =>
        claim("finding_outcome", finding.finding_id, finding.drift_type),
      );
    }
  }
  if (intent === "insufficient") {
    facts = { supported_intent: false };
    claims = [];
  }
  return {
    ...base,
    facts,
    expected_claims: claims,
    allowed_references: references,
  };
}

type SelectedEvidence =
  | {
      claims: AssistantClaim[];
      fact: JsonValue;
      kind: "finding";
      references: string[];
      value: MissionFinding;
    }
  | {
      claims: AssistantClaim[];
      fact: JsonValue;
      kind: "gap" | "requirement" | "snapshot";
      references: string[];
    };

function resolveSelectedEvidence(
  mission: MissionDocument,
  selectedEvidenceId?: string,
): SelectedEvidence | undefined {
  if (selectedEvidenceId === undefined) return undefined;
  if (selectedEvidenceId === mission.snapshot_id) {
    return {
      kind: "snapshot",
      fact: {
        data_mode: mission.data_mode,
        collected_at_utc: mission.collection.collected_at_utc,
        snapshot_id: mission.snapshot_id,
      },
      references: [mission.snapshot_id],
      claims: [claim("data_mode", mission.snapshot_id, mission.data_mode)],
    };
  }
  const finding = mission.findings.find(
    (item) => item.finding_id === selectedEvidenceId,
  );
  if (finding !== undefined) {
    const requirementReferences = requirementReferenceForFinding(
      mission,
      finding,
    );
    return {
      kind: "finding",
      value: finding,
      fact: findingFact(finding),
      references: [finding.finding_id, ...requirementReferences],
      claims: [
        claim("finding_outcome", finding.finding_id, finding.drift_type),
      ],
    };
  }
  const requirement = mission.requirements.find(
    (item) => item.requirement_id === selectedEvidenceId,
  );
  if (requirement !== undefined) {
    return {
      kind: "requirement",
      fact: requirementFact(requirement),
      references: [requirement.requirement_id],
      claims: [
        claim(
          "requirement_outcome",
          requirement.requirement_id,
          requirement.outcome,
        ),
      ],
    };
  }
  const gap = mission.collection_gaps.find(
    (item) => item.gap_id === selectedEvidenceId,
  );
  if (gap !== undefined) {
    return {
      kind: "gap",
      fact: gap,
      references: [gap.gap_id],
      claims: [claim("collection_gap_present", gap.gap_id, true)],
    };
  }
  throw new HttpError(
    422,
    "assistant_evidence_rejected",
    "selected evidence reference is outside the current package",
  );
}

function findingFact(finding: MissionFinding): JsonValue {
  return {
    finding_id: finding.finding_id,
    rule_id: finding.rule_id,
    title: finding.title,
    platform: finding.platform,
    drift_type: finding.drift_type,
    severity: finding.severity,
    expected_value: finding.expected_value,
    observed_value: finding.observed_value,
    assignment_summary: finding.assignment_summary,
    read_only_review:
      "Review the published setting and assignment evidence in Intune; Provifact cannot make the change.",
  };
}

function requirementFact(requirement: MissionRequirement): JsonValue {
  return {
    requirement_id: requirement.requirement_id,
    rule_id: requirement.rule_id,
    title: requirement.title,
    outcome: requirement.outcome,
    expected_value: requirement.expected_value ?? null,
    observed_value: requirement.observed_value ?? null,
    assignment_summary: requirement.assignment_summary ?? "not available",
    mappings: requirement.mappings ?? {},
  };
}

function requirementReferenceForFinding(
  mission: MissionDocument,
  finding: MissionFinding,
): string[] {
  const requirement = mission.requirements.find(
    (item) => item.rule_id === finding.rule_id,
  );
  return requirement === undefined ? [] : [requirement.requirement_id];
}

function evidenceReferencesForIdentifier(
  mission: MissionDocument,
  identifier: string,
): string[] {
  const finding = mission.findings.find(
    (item) =>
      item.finding_id === identifier ||
      item.rule_id === identifier ||
      requirementReferenceForFinding(mission, item).includes(identifier),
  );
  if (finding !== undefined) {
    return [
      finding.finding_id,
      ...requirementReferenceForFinding(mission, finding),
    ];
  }
  const requirement = mission.requirements.find(
    (item) => item.requirement_id === identifier || item.rule_id === identifier,
  );
  return requirement === undefined ? [] : [requirement.requirement_id];
}

function requirementOrFindingSummary(
  mission: MissionDocument,
  identifier: string,
): JsonValue {
  const finding = mission.findings.find(
    (item) => item.finding_id === identifier || item.rule_id === identifier,
  );
  if (finding !== undefined) return findingFact(finding);
  const requirement = mission.requirements.find(
    (item) => item.requirement_id === identifier || item.rule_id === identifier,
  );
  return requirement === undefined
    ? { identifier, evidence_state: "referenced by the change set" }
    : requirementFact(requirement);
}

function severityRank(value: string): number {
  return value === "high"
    ? 3
    : value === "medium"
      ? 2
      : value === "low"
        ? 1
        : 0;
}

function stringArray(value: JsonValue | undefined): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function stringOrNull(value: JsonValue | undefined): string | null {
  return typeof value === "string" ? value : null;
}

function groupUnevaluatedResources(
  resources: Array<{ [key: string]: JsonValue }>,
): JsonValue {
  const groups = new Map<string, Array<{ [key: string]: JsonValue }>>();
  for (const resource of resources) {
    const reason =
      typeof resource.evaluation_reason === "string"
        ? resource.evaluation_reason
        : "Reason not classified in the package";
    const items = groups.get(reason) ?? [];
    items.push({
      resource_ref: resource.resource_ref ?? null,
      resource_family: resource.resource_family ?? null,
      title: resource.title ?? null,
      action_expected: resource.action_expected ?? "Human review required",
    });
    groups.set(reason, items);
  }
  return [...groups.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([reason, items]) => ({ reason, count: items.length, items }));
}

function frameworkFacts(coverage: Record<string, JsonValue>): JsonValue {
  return Object.entries(coverage)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([framework, value]) => ({
      framework,
      referenced_identifier_count:
        isRecord(value) &&
        typeof value.technical_evidence_identifier_count === "number"
          ? value.technical_evidence_identifier_count
          : 0,
      assessment_conclusion: "not evaluated",
    }));
}

function claim(
  code: string,
  subject: string,
  value: JsonValue,
): AssistantClaim {
  return { claim_code: code, subject_id: subject, claim_value: value };
}

function fixtureOutput(
  question: string,
  context: AssistantContext,
): AssistantOutput {
  void question;
  if (context.intent === "insufficient") {
    return {
      direct_answer: INSUFFICIENT,
      claims: [],
      evidence_references: [],
      evidence_sufficiency: "insufficient",
      limitations: [
        `The question is outside the bounded collected-evidence intents for the ${context.page} page.`,
      ],
      additional_evidence_required: [
        "Ask about findings requiring attention, FileVault, changes, resolved drift, collected resources not evaluated, framework cross-references, provenance, evidence links, Intune review, or Provifact limitations.",
        "Human review or another classified evidence source is required for other conclusions.",
      ],
      suggested_human_review_questions: [
        "Which reviewed evidence source should answer this question?",
      ],
    };
  }
  return {
    direct_answer: fixtureDirectAnswer(context),
    claims: context.expected_claims,
    evidence_references: context.allowed_references,
    evidence_sufficiency: "verified",
    limitations: [
      "This is technical evidence only and does not establish organizational compliance.",
      "Generated explanation remains subject to human review.",
    ],
    additional_evidence_required: [
      "Review assignment, scope, process, and operating-effectiveness evidence where applicable.",
    ],
    suggested_human_review_questions: [
      "Does the deterministic evidence match the intended scope and approved baseline?",
    ],
  };
}

function fixtureDirectAnswer(context: AssistantContext): string {
  if (context.intent === "alignment" && isRecord(context.facts)) {
    const alignment =
      typeof context.facts.alignment_percent === "number"
        ? context.facts.alignment_percent
        : "unknown";
    const denominator =
      typeof context.facts.denominator === "number"
        ? context.facts.denominator
        : "unknown";
    return `The mapped macOS technical alignment is ${alignment}% across ${denominator} evaluated requirements.`;
  }
  if (context.intent === "device_posture" && isRecord(context.facts)) {
    return "The evidence package contains aggregate compliance posture only; individual device identities are not available to the assistant.";
  }
  if (context.intent === "changes" && isRecord(context.facts)) {
    const count = Array.isArray(context.facts.changed_requirements)
      ? context.facts.changed_requirements.length
      : 0;
    const began = stringArray(context.facts.new_drift).length;
    const resolved = stringArray(context.facts.resolved_drift).length;
    return `${count} evaluated requirement(s) changed since the previous sanitized package: ${began} began drifting and ${resolved} resolved. Open Changes for the fingerprint-verified snapshot comparison.`;
  }
  if (context.intent === "resolved" && isRecord(context.facts)) {
    const resolved = Array.isArray(context.facts.resolved_findings)
      ? context.facts.resolved_findings
      : [];
    if (resolved.length === 0) {
      return "No resolved finding is recorded in the current sanitized comparison. A later collection, not a browser refresh or Git revert, is required to prove a setting changed.";
    }
    return `${resolved.length} finding(s) resolved since the previous sanitized collection. ${summarizeFindingFacts(resolved)}`;
  }
  if (context.intent === "collection_gaps" && Array.isArray(context.facts)) {
    return `${context.facts.length} collection gap(s) are recorded. Each remains additional evidence required; Provifact does not convert an unavailable endpoint into a missing tenant setting.`;
  }
  if (context.intent === "unevaluated" && isRecord(context.facts)) {
    const groups = Array.isArray(context.facts.groups)
      ? context.facts.groups
      : [];
    const labels = groups
      .filter(isJsonRecord)
      .slice(0, 4)
      .map(
        (group) => `${displayFact(group.reason)} (${displayFact(group.count)})`,
      )
      .join("; ");
    return `${displayFact(context.facts.total)} collected resource(s) are not currently evaluated. ${labels || "The package does not classify their evaluation reason."} These objects do not enter the alignment denominator.`;
  }
  if (context.intent === "framework_meaning") {
    return "Framework cross-references are distinct identifiers linked to evaluated technical settings. They are navigation aids for human review and do not determine a framework verdict or completed assessment.";
  }
  if (context.intent === "provenance" && isRecord(context.facts)) {
    return `This package is labeled ${displayFact(context.facts.data_mode)}. It was collected at ${displayFact(context.facts.collected_at_utc)} through ${displayFact(context.facts.provider)} and published as ${displayFact(context.facts.snapshot_id)} against ${displayFact(context.facts.baseline_name)}.`;
  }
  if (context.intent === "limitations") {
    return "Provifact is limited to collected configuration evidence and deterministic drift. It does not provide organizational or assessor verdicts, accept risk, approve exceptions, or confirm a human change without a later collection. Human review is required.";
  }
  if (context.intent === "evidence" && isRecord(context.facts)) {
    if (typeof context.facts.evidence_missing === "string") {
      return `${context.facts.evidence_missing} Open a finding or setting detail and choose Ask Provifact Copilot.`;
    }
    return `The selected evidence chain is: ${summarizeFindingFacts([context.facts])} Open the linked finding or requirement for identifiers and fingerprints.`;
  }
  if (Array.isArray(context.facts)) {
    if (context.facts.length === 0) {
      return "No deterministic finding matches this bounded question in the current sanitized package. Review the Settings view for aligned, unsupported, or unevaluated requirements.";
    }
    return `${context.facts.length} deterministic finding(s) match. ${summarizeFindingFacts(context.facts)}`;
  }
  return INSUFFICIENT;
}

function summarizeFindingFacts(facts: JsonValue[]): string {
  return facts
    .filter(isJsonRecord)
    .slice(0, 3)
    .map((finding) => {
      const title =
        typeof finding.title === "string"
          ? finding.title
          : typeof finding.rule_id === "string"
            ? finding.rule_id
            : "Selected evidence";
      const state =
        typeof finding.drift_type === "string"
          ? finding.drift_type
          : typeof finding.outcome === "string"
            ? finding.outcome
            : "state unavailable";
      const observed = displayFact(finding.observed_value);
      const target = displayFact(finding.expected_value);
      const assignment =
        typeof finding.assignment_summary === "string"
          ? finding.assignment_summary
          : "assignment evidence unavailable";
      return `${title}: ${state}; observed ${observed}, target ${target}; assignment ${assignment}.`;
    })
    .join(" ");
}

function isJsonRecord(value: JsonValue): value is { [key: string]: JsonValue } {
  return isRecord(value);
}

function displayFact(value: unknown): string {
  if (value === undefined || value === null) return "not available";
  if (typeof value === "string" || typeof value === "number")
    return String(value);
  if (typeof value === "boolean") return value ? "enabled" : "disabled";
  return canonicalJson(value as JsonValue);
}

async function openAIOutput(
  env: WorkerEnv,
  question: string,
  context: AssistantContext,
  dependencies: AssistantDependencies,
): Promise<AssistantOutput> {
  if (!hasUsableOpenAIKey(env.OPENAI_API_KEY)) {
    throw new HttpError(
      503,
      "assistant_not_configured",
      "OpenAI assistant mode is unavailable",
    );
  }
  let response: Response;
  try {
    response = await dependencies.outboundFetch(OPENAI_RESPONSES_ENDPOINT, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(openAIRequest(env.OPENAI_MODEL, question, context)),
      signal: AbortSignal.timeout(OPENAI_TIMEOUT_MS),
    });
  } catch (error) {
    const timeout =
      error instanceof DOMException && error.name === "TimeoutError";
    throw new HttpError(
      timeout ? 504 : 502,
      timeout ? "upstream_timeout" : "upstream_connection_failed",
      timeout
        ? "the assistant request timed out"
        : "the assistant service connection failed",
    );
  }
  if (!response.ok) {
    const failure = classifyUpstreamFailure(
      response.status,
      await readUpstreamErrorMetadata(response),
    );
    const classified = assistantUpstreamFailure(failure);
    throw new HttpError(classified.status, classified.code, classified.message);
  }
  return parseOutput(extractOutput(await readBoundedResponse(response)));
}

function assistantUpstreamFailure(failure: UpstreamFailure): {
  status: number;
  code: string;
  message: string;
} {
  const failures: Record<
    UpstreamFailure,
    { status: number; code: string; message: string }
  > = {
    configuration: {
      status: 503,
      code: "assistant_not_configured",
      message: "OpenAI assistant mode is unavailable",
    },
    capacity: {
      status: 503,
      code: "assistant_capacity_unavailable",
      message: "assistant capacity is unavailable",
    },
    quota: {
      status: 503,
      code: "assistant_quota_unavailable",
      message: "assistant quota is unavailable",
    },
    rate: {
      status: 503,
      code: "assistant_upstream_rate_limited",
      message: "the assistant service rate limit was reached",
    },
    model: {
      status: 503,
      code: "assistant_model_unavailable",
      message: "the configured assistant model is unavailable",
    },
    request: {
      status: 502,
      code: "assistant_upstream_request_rejected",
      message: "the bounded assistant request was rejected",
    },
    service: {
      status: 502,
      code: "assistant_upstream_unavailable",
      message: "the assistant service is unavailable",
    },
  };
  return failures[failure];
}

function openAIRequest(
  model: "gpt-5.6-terra",
  question: string,
  context: AssistantContext,
): object {
  return {
    model,
    store: false,
    max_output_tokens: MAX_OUTPUT_TOKENS,
    reasoning: { effort: "low" },
    instructions:
      "Answer only from the supplied sanitized Provifact facts. Copy every expected typed claim exactly. " +
      "Cite only allowed references. Do not infer identities, request identifiers, claim compliance, " +
      "certification, control satisfaction, assessment completion, exception, remediation, or risk acceptance. " +
      "If evidence is insufficient, use the exact supplied insufficient-evidence sentence. State limitations " +
      "and human-review questions. Free prose is AI-generated analysis subject to human review.",
    input: JSON.stringify({
      question,
      intent: context.intent,
      page: context.page,
      evidence_timestamp: context.evidence_timestamp,
      baseline_version: context.baseline_version,
      facts: context.facts,
      expected_claims: context.expected_claims,
      allowed_references: context.allowed_references,
      insufficient_evidence_sentence: INSUFFICIENT,
    }),
    text: {
      verbosity: "low",
      format: {
        type: "json_schema",
        name: "provifact_assistant_v1",
        strict: true,
        schema: assistantSchema(),
      },
    },
  };
}

function assistantSchema(): object {
  return {
    type: "object",
    additionalProperties: false,
    required: [
      "direct_answer",
      "claims",
      "evidence_references",
      "evidence_sufficiency",
      "limitations",
      "additional_evidence_required",
      "suggested_human_review_questions",
    ],
    properties: {
      direct_answer: { type: "string", minLength: 1, maxLength: 1200 },
      claims: {
        type: "array",
        maxItems: 32,
        items: {
          type: "object",
          additionalProperties: false,
          required: ["claim_code", "subject_id", "claim_value"],
          properties: {
            claim_code: { type: "string" },
            subject_id: { type: "string" },
            claim_value: { type: ["string", "number", "boolean", "null"] },
          },
        },
      },
      evidence_references: {
        type: "array",
        maxItems: 40,
        items: { type: "string" },
      },
      evidence_sufficiency: {
        type: "string",
        enum: ["verified", "partial", "insufficient"],
      },
      limitations: {
        type: "array",
        minItems: 1,
        maxItems: 6,
        items: { type: "string" },
      },
      additional_evidence_required: {
        type: "array",
        minItems: 1,
        maxItems: 6,
        items: { type: "string" },
      },
      suggested_human_review_questions: {
        type: "array",
        minItems: 1,
        maxItems: 6,
        items: { type: "string" },
      },
    },
  };
}

function extractOutput(value: unknown): unknown {
  if (!isRecord(value) || !Array.isArray(value.output)) modelRejected();
  for (const item of value.output) {
    if (
      !isRecord(item) ||
      item.type !== "message" ||
      !Array.isArray(item.content)
    )
      continue;
    for (const part of item.content) {
      if (!isRecord(part)) continue;
      if (part.type === "refusal") {
        throw new HttpError(
          422,
          "model_refusal",
          "OpenAI refused the assistant request",
        );
      }
      if (part.type === "output_text" && typeof part.text === "string") {
        try {
          return JSON.parse(part.text);
        } catch {
          modelRejected();
        }
      }
    }
  }
  modelRejected();
}

function parseOutput(value: unknown): AssistantOutput {
  if (!isRecord(value)) modelRejected();
  const fields = [
    "additional_evidence_required",
    "claims",
    "direct_answer",
    "evidence_references",
    "evidence_sufficiency",
    "limitations",
    "suggested_human_review_questions",
  ];
  if (Object.keys(value).sort().join(",") !== fields.join(",")) modelRejected();
  if (
    typeof value.direct_answer !== "string" ||
    !Array.isArray(value.claims) ||
    !Array.isArray(value.evidence_references) ||
    !["verified", "partial", "insufficient"].includes(
      String(value.evidence_sufficiency),
    )
  )
    modelRejected();
  const claims = value.claims.map((item) => {
    if (
      !isRecord(item) ||
      Object.keys(item).sort().join(",") !==
        "claim_code,claim_value,subject_id" ||
      typeof item.claim_code !== "string" ||
      typeof item.subject_id !== "string" ||
      (typeof item.claim_value === "object" && item.claim_value !== null)
    )
      modelRejected();
    return item as unknown as AssistantClaim;
  });
  const strings = (item: unknown): string[] => {
    if (
      !Array.isArray(item) ||
      item.length < 1 ||
      item.some((entry) => typeof entry !== "string")
    ) {
      modelRejected();
    }
    return item as string[];
  };
  return {
    direct_answer: value.direct_answer,
    claims,
    evidence_references: value.evidence_references as string[],
    evidence_sufficiency:
      value.evidence_sufficiency as AssistantOutput["evidence_sufficiency"],
    limitations: strings(value.limitations),
    additional_evidence_required: strings(value.additional_evidence_required),
    suggested_human_review_questions: strings(
      value.suggested_human_review_questions,
    ),
  };
}

function modelRejected(): never {
  throw new HttpError(
    502,
    "model_output_rejected",
    "assistant structured output was rejected",
  );
}

function verifyOutput(
  output: AssistantOutput,
  context: AssistantContext,
): AssistantResult["verification"] {
  const reasons: string[] = [];
  const expected = new Map(
    context.expected_claims.map((item) => [
      canonicalJson(item as unknown as JsonValue),
      item,
    ]),
  );
  const observed = output.claims.map((item) =>
    canonicalJson(item as unknown as JsonValue),
  );
  const duplicates = observed.filter(
    (item, index) => observed.indexOf(item) !== index,
  );
  const rejected = [
    ...new Set(observed.filter((item) => !expected.has(item))),
  ].sort();
  const accepted = [
    ...new Set(observed.filter((item) => expected.has(item))),
  ].sort();
  const missing = [...expected.keys()]
    .filter((item) => !observed.includes(item))
    .sort();
  if (duplicates.length) reasons.push("duplicate typed claims were rejected");
  if (rejected.length)
    reasons.push("unknown or contradictory typed claims were rejected");
  if (missing.length)
    reasons.push("required deterministic typed claims were missing");
  const permitted = new Set(context.allowed_references);
  const outside = output.evidence_references.filter(
    (reference) => !permitted.has(reference),
  );
  if (outside.length)
    reasons.push(
      "evidence references outside the selected context were rejected",
    );
  const prose = [
    output.direct_answer,
    ...output.limitations,
    ...output.additional_evidence_required,
    ...output.suggested_human_review_questions,
  ].join("\n");
  if (VERDICT.test(prose))
    reasons.push("unsupported compliance or assessor conclusion was rejected");
  const mentioned = prose.match(REFERENCE) ?? [];
  if (mentioned.some((reference) => !permitted.has(reference))) {
    reasons.push("uncited or unknown tenant evidence assertion was rejected");
  }
  if (!/human review/i.test(prose))
    reasons.push("required human-review language was missing");
  if (
    context.intent === "insufficient" &&
    output.direct_answer !== INSUFFICIENT
  ) {
    reasons.push(
      "insufficient evidence response did not use the required statement",
    );
  }
  let status: AssistantResult["verification"]["status"] =
    "typed_claims_verified";
  if (context.intent === "insufficient" && reasons.length === 0)
    status = "insufficient_evidence";
  else if (reasons.length > 0) status = "rejected";
  return {
    status,
    verifier_version: VERIFIER_VERSION,
    typed_claims_accepted: accepted,
    typed_claims_rejected: [...new Set([...rejected, ...missing])].sort(),
    generated_prose_quarantined: true,
    reasons,
    human_review_required: true,
  };
}

function runtimeMode(value: string): RuntimeMode {
  if (value !== "fixture" && value !== "openai") {
    throw new HttpError(
      503,
      "runtime_mode_invalid",
      "assistant runtime mode is invalid",
    );
  }
  return value;
}
