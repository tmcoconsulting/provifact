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
  "EvidenceOps does not have sufficient collected evidence to answer this question.";
const VERDICT =
  /\b(?:compliant|certified|certification|control\s+(?:is\s+)?satisfied|assessment\s+(?:is\s+)?complete|risk\s+accepted|meets?\s+(?:the\s+)?(?:standard|framework|compliance))\b/i;
const REFERENCE = /\b(?:finding|req|gap|mission)-[0-9a-f]{24}\b/g;

type Intent =
  | "alignment"
  | "assignment_drift"
  | "changes"
  | "collection_gaps"
  | "conflicts"
  | "device_posture"
  | "filevault"
  | "high_severity"
  | "insufficient";

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
}

interface MissionDocument {
  schema_version: "2.0.0";
  snapshot_id: string;
  content_fingerprint: string;
  data_mode: string;
  collection: Record<string, JsonValue> & { collected_at_utc: string };
  baseline: Record<string, JsonValue> & { benchmark_version: string };
  metrics: Record<string, JsonValue>;
  devices: Record<string, JsonValue>;
  requirements: MissionRequirement[];
  findings: MissionFinding[];
  collection_gaps: Array<{ [key: string]: JsonValue; gap_id: string }>;
  changes: Record<string, JsonValue>;
}

export interface MissionStatus {
  baseline_version: string;
  content_fingerprint: string;
  data_mode: string;
  evidence_timestamp: string;
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
  const intent = classifyQuestion(input.question);
  const context = selectContext(mission, intent);
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

function parseAssistantInput(value: unknown): {
  question: string;
  snapshot_id: string;
} {
  if (
    !isRecord(value) ||
    Object.keys(value).sort().join(",") !== "question,snapshot_id"
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
  return { question: value.question.trim(), snapshot_id: value.snapshot_id };
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
  const value = await readBoundedResponse(response);
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
    baseline_version: mission.baseline.benchmark_version,
    content_fingerprint: mission.content_fingerprint,
    data_mode: mission.data_mode,
    evidence_timestamp: mission.collection.collected_at_utc,
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
    value.schema_version !== "2.0.0" ||
    typeof value.snapshot_id !== "string" ||
    !/^mission-[0-9a-f]{24}$/.test(value.snapshot_id) ||
    typeof value.content_fingerprint !== "string" ||
    !/^sha256:[0-9a-f]{64}$/.test(value.content_fingerprint) ||
    !isRecord(value.collection) ||
    typeof value.collection.collected_at_utc !== "string" ||
    !isRecord(value.baseline) ||
    typeof value.baseline.benchmark_version !== "string" ||
    !isRecord(value.metrics) ||
    !isRecord(value.devices) ||
    !isRecord(value.changes) ||
    !Array.isArray(value.requirements) ||
    value.requirements.length > MAX_REQUIREMENTS ||
    !Array.isArray(value.findings) ||
    value.findings.length > MAX_FINDINGS ||
    !Array.isArray(value.collection_gaps)
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
      typeof requirement.severity !== "string"
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

function classifyQuestion(question: string): Intent {
  const normalized = question.toLowerCase();
  if (/filevault|encryption/.test(normalized)) return "filevault";
  if (/what changed|since (?:the )?(?:last|previous)|trend/.test(normalized))
    return "changes";
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
): AssistantContext {
  const base = {
    intent,
    evidence_timestamp: mission.collection.collected_at_utc,
    baseline_version: mission.baseline.benchmark_version,
  };
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
    facts = mission.changes;
    const changed = Array.isArray(mission.changes.changed_requirements)
      ? mission.changes.changed_requirements.length
      : 0;
    claims = [claim("change_count", mission.snapshot_id, changed)];
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
    const selected = mission.findings.filter((finding) => {
      if (intent === "filevault") return finding.rule_id.includes("filevault");
      if (intent === "high_severity") return finding.severity === "high";
      if (intent === "assignment_drift")
        return finding.drift_type === "Assignment drift";
      if (intent === "conflicts")
        return finding.drift_type === "Conflicting policy";
      return false;
    });
    facts = selected.map((finding) => ({
      finding_id: finding.finding_id,
      rule_id: finding.rule_id,
      title: finding.title,
      platform: finding.platform,
      drift_type: finding.drift_type,
      severity: finding.severity,
      expected_value: finding.expected_value,
      observed_value: finding.observed_value,
      assignment_summary: finding.assignment_summary,
    }));
    references = [
      mission.snapshot_id,
      ...selected.map((finding) => finding.finding_id),
    ];
    claims = selected.map((finding) =>
      claim("finding_outcome", finding.finding_id, finding.drift_type),
    );
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
        "The question is outside the bounded collected-evidence intents.",
      ],
      additional_evidence_required: [
        "Human review or another evidence source is required.",
      ],
      suggested_human_review_questions: [
        "What evidence source should answer this question?",
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
    return `${count} mapped requirements changed since the previous sanitized evidence package.`;
  }
  if (context.intent === "collection_gaps" && Array.isArray(context.facts)) {
    return `${context.facts.length} collection gap is recorded and requires additional evidence.`;
  }
  if (Array.isArray(context.facts)) {
    return `${context.facts.length} deterministic finding(s) match the selected evidence question.`;
  }
  return INSUFFICIENT;
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
      "Answer only from the supplied sanitized EvidenceOps facts. Copy every expected typed claim exactly. " +
      "Cite only allowed references. Do not infer identities, request identifiers, claim compliance, " +
      "certification, control satisfaction, assessment completion, exception, remediation, or risk acceptance. " +
      "If evidence is insufficient, use the exact supplied insufficient-evidence sentence. State limitations " +
      "and human-review questions. Free prose is AI-generated analysis subject to human review.",
    input: JSON.stringify({
      question,
      intent: context.intent,
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
        name: "evidenceops_assistant_v1",
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
