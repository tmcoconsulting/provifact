import narrativeSchema from "../../evidenceops/narrative/narrative-model-output.schema.json";

import type { WorkerEnv } from "./env";
import { isRecord } from "./evidence";
import {
  assertPublicSafe,
  hasUsableOpenAIKey,
  HttpError,
  OPENAI_TIMEOUT_MS,
  readBoundedResponse,
} from "./security";
import type {
  NarrativeEvidence,
  NarrativeModelOutput,
  PublicEvidencePackage,
  RuntimeMode,
  VerificationEvidence,
} from "./types";
import {
  buildNarrativeEvidence,
  parseNarrativeModelOutput,
  verifyNarrative,
} from "./verifier";

const OPENAI_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses";
const FIXTURE_MODEL = "deterministic-offline-fixture-not-a-model-call";
const MAX_OUTPUT_TOKENS = 1600;
const MAX_UPSTREAM_ERROR_BYTES = 16 * 1024;
const SAFE_UPSTREAM_ERROR_TOKEN = /^[a-z][a-z0-9_]{0,63}$/;

interface UpstreamErrorMetadata {
  code: string | null;
  type: string | null;
}

export type UpstreamFailure =
  | "capacity"
  | "configuration"
  | "model"
  | "quota"
  | "rate"
  | "request"
  | "service";

export interface NarrativeApiResult {
  mode: RuntimeMode;
  ai_model_call_performed: boolean;
  human_review_required: true;
  source_package_evidence_id: string;
  narrative: NarrativeEvidence;
  verification: VerificationEvidence;
}

export interface NarrativeDependencies {
  outboundFetch: typeof fetch;
}

export async function createNarrative(
  request: Request,
  env: WorkerEnv,
  packageDocument: PublicEvidencePackage,
  dependencies: NarrativeDependencies,
): Promise<NarrativeApiResult> {
  const mode = runtimeMode(env.EVIDENCEOPS_MODE);
  if (mode === "fixture") {
    return createFixtureNarrative(request, env, packageDocument);
  }
  return createOpenAINarrative(env, packageDocument, dependencies);
}

async function createFixtureNarrative(
  request: Request,
  env: WorkerEnv,
  packageDocument: PublicEvidencePackage,
): Promise<NarrativeApiResult> {
  const expectedPackage = await loadAssetJson(
    request,
    env,
    "/assets/data/phase1-public-evidence.json",
  );
  if (
    !isRecord(expectedPackage) ||
    expectedPackage.content_fingerprint !==
      packageDocument.content_fingerprint ||
    expectedPackage.evidence_id !== packageDocument.evidence_id
  ) {
    throw new HttpError(
      409,
      "fixture_package_required",
      "fixture mode accepts only the tracked synthetic public package",
    );
  }
  const fixture = await loadAssetJson(
    request,
    env,
    "/assets/data/phase1-fixture-narrative.json",
  );
  if (!isRecord(fixture) || fixture.model !== FIXTURE_MODEL) {
    throw new HttpError(
      503,
      "fixture_unavailable",
      "fixture narrative is unavailable",
    );
  }
  const output = parseNarrativeModelOutput({
    executive_summary: fixture.executive_summary,
    drift_explanations: fixture.drift_explanations,
    limitations: fixture.limitations,
    additional_evidence_required: fixture.additional_evidence_required,
    suggested_human_review_questions: fixture.suggested_human_review_questions,
  });
  assertPublicSafe(output);
  const narrative = await buildNarrativeEvidence(
    output,
    packageDocument,
    FIXTURE_MODEL,
  );
  const verification = await verifyNarrative(narrative, packageDocument);
  return {
    mode: "fixture",
    ai_model_call_performed: false,
    human_review_required: true,
    source_package_evidence_id: packageDocument.evidence_id,
    narrative,
    verification,
  };
}

async function createOpenAINarrative(
  env: WorkerEnv,
  packageDocument: PublicEvidencePackage,
  dependencies: NarrativeDependencies,
): Promise<NarrativeApiResult> {
  if (!hasUsableOpenAIKey(env.OPENAI_API_KEY)) {
    throw new HttpError(
      503,
      "narrative_not_configured",
      "OpenAI narrative mode is unavailable",
    );
  }
  const model = requireModel(env.OPENAI_MODEL);
  let response: Response;
  try {
    response = await dependencies.outboundFetch(OPENAI_RESPONSES_ENDPOINT, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(openAIRequest(packageDocument, model)),
      signal: AbortSignal.timeout(OPENAI_TIMEOUT_MS),
    });
  } catch (error) {
    const timedOut =
      error instanceof DOMException && error.name === "TimeoutError";
    throw new HttpError(
      timedOut ? 504 : 502,
      timedOut ? "upstream_timeout" : "upstream_connection_failed",
      timedOut
        ? "the narrative request timed out"
        : "the narrative service connection failed",
    );
  }
  if (!response.ok) {
    const metadata = await readUpstreamErrorMetadata(response);
    const failure = classifyUpstreamFailure(response.status, metadata);
    if (failure === "configuration") {
      throw new HttpError(
        503,
        "narrative_not_configured",
        "OpenAI narrative mode is unavailable",
      );
    }
    if (failure === "capacity") {
      throw new HttpError(
        503,
        "narrative_capacity_unavailable",
        "narrative capacity is unavailable",
      );
    }
    if (failure === "quota") {
      throw new HttpError(
        503,
        "narrative_quota_unavailable",
        "narrative quota is unavailable",
      );
    }
    if (failure === "rate") {
      throw new HttpError(
        503,
        "narrative_upstream_rate_limited",
        "the narrative service rate limit was reached",
      );
    }
    if (failure === "model") {
      throw new HttpError(
        503,
        "narrative_model_unavailable",
        "the configured narrative model is unavailable",
      );
    }
    if (failure === "request") {
      throw new HttpError(
        502,
        "upstream_request_rejected",
        "the bounded model request was rejected",
      );
    }
    throw new HttpError(
      502,
      "upstream_service_unavailable",
      "the narrative service is unavailable",
    );
  }
  const upstream = await readBoundedResponse(response);
  const output = extractStructuredOutput(upstream);
  assertPublicSafe(output);
  const narrative = await buildNarrativeEvidence(
    output,
    packageDocument,
    model,
  );
  const verification = await verifyNarrative(narrative, packageDocument);
  return {
    mode: "openai",
    ai_model_call_performed: true,
    human_review_required: true,
    source_package_evidence_id: packageDocument.evidence_id,
    narrative,
    verification,
  };
}

export function classifyUpstreamFailure(
  status: number,
  metadata: UpstreamErrorMetadata,
): UpstreamFailure {
  const discriminators = new Set(
    [metadata.code, metadata.type].filter(
      (value): value is string => value !== null,
    ),
  );
  if (
    discriminators.has("model_not_found") ||
    discriminators.has("model_not_supported")
  ) {
    return "model";
  }
  if (
    discriminators.has("insufficient_quota") ||
    discriminators.has("billing_hard_limit_reached")
  ) {
    return "quota";
  }
  if (discriminators.has("rate_limit_exceeded")) {
    return "rate";
  }
  if (status === 401 || status === 403) {
    return "configuration";
  }
  if (status === 404) {
    return "model";
  }
  if (status === 429) {
    return "capacity";
  }
  if (status === 400 || status === 409 || status === 422) {
    return "request";
  }
  return "service";
}

export async function readUpstreamErrorMetadata(
  response: Response,
): Promise<UpstreamErrorMetadata> {
  if (response.body === null) {
    return { code: null, type: null };
  }
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  try {
    while (true) {
      const result = await reader.read();
      if (result.done) {
        break;
      }
      total += result.value.byteLength;
      if (total > MAX_UPSTREAM_ERROR_BYTES) {
        await cancelUpstreamErrorBody(
          reader,
          "EvidenceOps suppresses oversized error bodies",
        );
        return { code: null, type: null };
      }
      chunks.push(result.value);
    }
  } catch {
    await cancelUpstreamErrorBody(
      reader,
      "EvidenceOps suppresses unreadable error bodies",
    );
    return { code: null, type: null };
  }
  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(
      new TextDecoder("utf-8", { fatal: true, ignoreBOM: false }).decode(bytes),
    );
  } catch {
    return { code: null, type: null };
  }
  if (!isRecord(parsed) || !isRecord(parsed.error)) {
    return { code: null, type: null };
  }
  return {
    code: safeUpstreamErrorToken(parsed.error.code),
    type: safeUpstreamErrorToken(parsed.error.type),
  };
}

async function cancelUpstreamErrorBody(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  reason: string,
): Promise<void> {
  try {
    await reader.cancel(reason);
  } catch {
    // A failed cancellation must not expose or change upstream error handling.
  }
}

function safeUpstreamErrorToken(value: unknown): string | null {
  return typeof value === "string" && SAFE_UPSTREAM_ERROR_TOKEN.test(value)
    ? value
    : null;
}

function openAIRequest(
  packageDocument: PublicEvidencePackage,
  model: string,
): object {
  return {
    model,
    store: false,
    max_output_tokens: MAX_OUTPUT_TOKENS,
    reasoning: { effort: "low" },
    instructions:
      "Produce evidence-grounded analysis only. Preserve every deterministic status. " +
      "Do not declare compliance, certification, control satisfaction, an exception, risk " +
      "acceptance, or remediation. Emit exactly one explanation for each unique supplied " +
      "finding ID. Use only the finding_status claim code and copy its claim value exactly " +
      "from the deterministic finding. Cite only supplied evidence IDs. State limitations " +
      "and human-review questions. All prose is AI-generated analysis subject to human review.",
    input:
      "Create the bounded narrative from this sanitized EvidenceOps package:\n" +
      JSON.stringify(packageDocument),
    text: {
      verbosity: "low",
      format: {
        type: "json_schema",
        name: "evidenceops_narrative_v1",
        strict: true,
        schema: narrativeSchema,
      },
    },
  };
}

function extractStructuredOutput(value: unknown): NarrativeModelOutput {
  if (!isRecord(value) || !Array.isArray(value.output)) {
    throw new HttpError(
      502,
      "model_output_rejected",
      "OpenAI response lacked output items",
    );
  }
  for (const item of value.output) {
    if (
      !isRecord(item) ||
      item.type !== "message" ||
      !Array.isArray(item.content)
    ) {
      continue;
    }
    for (const part of item.content) {
      if (!isRecord(part)) {
        continue;
      }
      if (part.type === "refusal") {
        throw new HttpError(
          422,
          "model_refusal",
          "OpenAI refused narrative generation",
        );
      }
      if (part.type === "output_text" && typeof part.text === "string") {
        let parsed: unknown;
        try {
          parsed = JSON.parse(part.text);
        } catch {
          throw new HttpError(
            502,
            "model_output_rejected",
            "structured output was invalid JSON",
          );
        }
        return parseNarrativeModelOutput(parsed);
      }
    }
  }
  throw new HttpError(
    502,
    "model_output_rejected",
    "OpenAI response lacked output text",
  );
}

async function loadAssetJson(
  request: Request,
  env: WorkerEnv,
  path: string,
): Promise<unknown> {
  const url = new URL(path, request.url);
  const response = await env.ASSETS.fetch(new Request(url, { method: "GET" }));
  if (!response.ok || response.body === null) {
    if (response.body !== null) {
      await response.body.cancel("fixture asset was unavailable");
    }
    throw new HttpError(
      503,
      "fixture_unavailable",
      "fixture asset is unavailable",
    );
  }
  return readBoundedResponse(response);
}

function runtimeMode(value: string): RuntimeMode {
  if (value !== "fixture" && value !== "openai") {
    throw new HttpError(
      503,
      "runtime_mode_invalid",
      "narrative runtime mode is invalid",
    );
  }
  return value;
}

function requireModel(value: string): string {
  if (value !== "gpt-5.6-terra") {
    throw new HttpError(
      503,
      "model_configuration_rejected",
      "configured model is not approved",
    );
  }
  return value;
}
