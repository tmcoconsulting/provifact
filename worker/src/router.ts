import {
  validatePublicPackage,
  verifyPublicPackageIdentity,
} from "./contracts";
import {
  createAssistantAnswer,
  readMissionStatus,
  type AssistantDependencies,
} from "./assistant";
import type { WorkerEnv } from "./env";
import { createNarrative, type NarrativeDependencies } from "./narrative";
import {
  assertPublicSafe,
  assertSameOrigin,
  hasUsableOpenAIKey,
  HttpError,
  jsonResponse,
  rateLimitKey,
  readBoundedJson,
} from "./security";

export async function handleRequest(
  request: Request,
  env: WorkerEnv,
  dependencies?: NarrativeDependencies,
): Promise<Response> {
  const url = new URL(request.url);
  if (url.pathname === "/api/health") {
    if (request.method !== "GET") {
      return methodNotAllowed("GET");
    }
    return jsonResponse({
      schema_version: "1.0.0",
      service: "EvidenceOps Worker",
      status: "ok",
    });
  }
  if (url.pathname === "/api/ready") {
    if (request.method !== "GET") {
      return methodNotAllowed("GET");
    }
    const mode = modeLabel(env.EVIDENCEOPS_MODE);
    if (mode === "openai" && !hasUsableOpenAIKey(env.OPENAI_API_KEY)) {
      throw new HttpError(
        503,
        "runtime_not_ready",
        "the configured narrative runtime is unavailable",
      );
    }
    const mission = await readMissionStatus(request, env);
    return jsonResponse({
      schema_version: "1.0.0",
      service: "EvidenceOps Worker",
      status: "ready",
      narrative_mode: mode,
      mission,
    });
  }
  if (url.pathname === "/api/status") {
    if (request.method !== "GET") {
      return methodNotAllowed("GET");
    }
    const mode = modeLabel(env.EVIDENCEOPS_MODE);
    const modelConfigured =
      mode === "fixture" || hasUsableOpenAIKey(env.OPENAI_API_KEY);
    const mission = await readMissionStatus(request, env);
    return jsonResponse({
      schema_version: "1.0.0",
      service: "EvidenceOps narrative boundary",
      status: "ok",
      narrative_mode: mode,
      model: env.OPENAI_MODEL,
      model_configured: modelConfigured,
      narrative_available: modelConfigured,
      public_data_boundary: "synthetic-or-fail-closed-sanitized-only",
      human_review_required: true,
      data_mode: mission.data_mode,
      evidence_timestamp: mission.evidence_timestamp,
      source_snapshot_id: mission.snapshot_id,
      live_intune_collection_performed:
        mission.data_mode === "LIVE SANITIZED TENANT DATA",
      intune_write_capability: false,
      byok_supported: false,
      assistant_endpoint: "/api/ask",
    });
  }
  if (url.pathname === "/api/ask") {
    if (request.method !== "POST") {
      return methodNotAllowed("POST");
    }
    assertSameOrigin(request);
    const globalResult = await env.NARRATIVE_GLOBAL_RATE_LIMITER.limit({
      key: "assistant-global",
    });
    if (!globalResult.success) {
      throw new HttpError(
        429,
        "rate_limited",
        "assistant request rate limit exceeded",
      );
    }
    const { success } = await env.NARRATIVE_RATE_LIMITER.limit({
      key: await rateLimitKey(request),
    });
    if (!success) {
      throw new HttpError(
        429,
        "rate_limited",
        "assistant request rate limit exceeded",
      );
    }
    const untrusted = await readBoundedJson(request);
    const assistantDependencies: AssistantDependencies = dependencies ?? {
      outboundFetch: (input, init) => fetch(input, init),
    };
    return jsonResponse(
      await createAssistantAnswer(
        request,
        env,
        untrusted,
        assistantDependencies,
      ),
    );
  }
  if (url.pathname === "/api/narrative") {
    if (request.method !== "POST") {
      return methodNotAllowed("POST");
    }
    assertSameOrigin(request);
    const globalResult = await env.NARRATIVE_GLOBAL_RATE_LIMITER.limit({
      key: "narrative-global",
    });
    if (!globalResult.success) {
      throw new HttpError(
        429,
        "rate_limited",
        "narrative request rate limit exceeded",
      );
    }
    const { success } = await env.NARRATIVE_RATE_LIMITER.limit({
      key: await rateLimitKey(request),
    });
    if (!success) {
      throw new HttpError(
        429,
        "rate_limited",
        "narrative request rate limit exceeded",
      );
    }
    const untrusted = await readBoundedJson(request);
    assertPublicSafe(untrusted);
    const packageDocument = validatePublicPackage(untrusted);
    await verifyPublicPackageIdentity(packageDocument);
    const result = await createNarrative(
      request,
      env,
      packageDocument,
      dependencies ?? {
        outboundFetch: (input, init) => fetch(input, init),
      },
    );
    return jsonResponse(result);
  }
  if (url.pathname.startsWith("/api/")) {
    return jsonResponse({ error: "not_found" }, 404);
  }
  return env.ASSETS.fetch(request);
}

function methodNotAllowed(allow: string): Response {
  return jsonResponse({ error: "method_not_allowed" }, 405, { Allow: allow });
}

function modeLabel(value: string): "fixture" | "openai" {
  if (value !== "fixture" && value !== "openai") {
    throw new HttpError(
      503,
      "runtime_mode_invalid",
      "narrative runtime mode is invalid",
    );
  }
  return value;
}
