import {
  validatePublicPackage,
  verifyPublicPackageIdentity,
} from "./contracts";
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
  if (url.pathname === "/api/status") {
    if (request.method !== "GET") {
      return methodNotAllowed("GET");
    }
    const mode = modeLabel(env.EVIDENCEOPS_MODE);
    const modelConfigured =
      mode === "fixture" || hasUsableOpenAIKey(env.OPENAI_API_KEY);
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
      live_intune_collection_performed: false,
      intune_write_capability: false,
      byok_supported: false,
    });
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
