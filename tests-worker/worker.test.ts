import { describe, expect, it, vi } from "vitest";

import fixtureNarrative from "../docs/assets/data/phase1-fixture-narrative.json";
import fixturePackage from "../docs/assets/data/phase1-public-evidence.json";
import worker from "../worker/src/index";
import { validatePublicPackage } from "../worker/src/contracts";
import type { StaticAssetBinding, WorkerEnv } from "../worker/src/env";
import {
  buildNarrativeEvidence,
  parseNarrativeModelOutput,
  verifyNarrative,
} from "../worker/src/verifier";
import { handleRequest } from "../worker/src/router";
import { assertPublicSafe, HttpError } from "../worker/src/security";
import type {
  NarrativeModelOutput,
  PublicEvidencePackage,
  RuntimeMode,
} from "../worker/src/types";

const ORIGIN = "https://evidenceops.example";
const FIXTURE_MODEL = "deterministic-offline-fixture-not-a-model-call";
const TEST_API_KEY = `sk-test_${"A".repeat(32)}`;

function packageDocument(): PublicEvidencePackage {
  return validatePublicPackage(structuredClone(fixturePackage));
}

function modelOutput(): NarrativeModelOutput {
  return parseNarrativeModelOutput({
    executive_summary: fixtureNarrative.executive_summary,
    drift_explanations: fixtureNarrative.drift_explanations,
    limitations: fixtureNarrative.limitations,
    additional_evidence_required: fixtureNarrative.additional_evidence_required,
    suggested_human_review_questions:
      fixtureNarrative.suggested_human_review_questions,
  });
}

function assetBinding(): StaticAssetBinding {
  return {
    async fetch(input: RequestInfo | URL): Promise<Response> {
      const url = new URL(
        input instanceof Request ? input.url : input.toString(),
        ORIGIN,
      );
      if (url.pathname === "/assets/data/phase1-public-evidence.json") {
        return Response.json(fixturePackage);
      }
      if (url.pathname === "/assets/data/phase1-fixture-narrative.json") {
        return Response.json(fixtureNarrative);
      }
      return new Response("static asset", { status: 200 });
    },
  };
}

function environment(
  mode: RuntimeMode = "fixture",
  options: {
    apiKey?: string;
    globalRateLimitSuccess?: boolean;
    rateLimitSuccess?: boolean;
  } = {},
): WorkerEnv {
  return {
    ASSETS: assetBinding(),
    EVIDENCEOPS_MODE: mode,
    NARRATIVE_GLOBAL_RATE_LIMITER: {
      async limit(): Promise<{ success: boolean }> {
        return { success: options.globalRateLimitSuccess ?? true };
      },
    },
    NARRATIVE_RATE_LIMITER: {
      async limit(): Promise<{ success: boolean }> {
        return { success: options.rateLimitSuccess ?? true };
      },
    },
    OPENAI_MODEL: "gpt-5.6-terra",
    ...(options.apiKey === undefined ? {} : { OPENAI_API_KEY: options.apiKey }),
  };
}

function narrativeRequest(document: unknown = packageDocument()): Request {
  return new Request(`${ORIGIN}/api/narrative`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Origin: ORIGIN,
      "Sec-Fetch-Site": "same-origin",
    },
    body: JSON.stringify(document),
  });
}

function responseEnvelope(output: NarrativeModelOutput): object {
  return {
    output: [
      {
        type: "message",
        content: [{ type: "output_text", text: JSON.stringify(output) }],
      },
    ],
  };
}

describe("Worker routes", () => {
  it("reports a non-secret fixture status", async () => {
    const secret = `sk-proj_${"A".repeat(48)}`;
    const response = await worker.fetch(
      new Request(`${ORIGIN}/api/status`),
      environment("fixture", { apiKey: secret }),
    );
    expect(response.status).toBe(200);
    expect(response.headers.get("X-Request-ID")).toMatch(/^[0-9a-f-]+$/);
    const text = await response.text();
    expect(text).not.toContain(secret);
    const status = JSON.parse(text);
    expect(status).toMatchObject({
      narrative_mode: "fixture",
      narrative_available: true,
      model_configured: true,
      byok_supported: false,
      intune_write_capability: false,
    });
    expect(status).not.toHaveProperty("ai_model_call_performed");
  });

  it("reports an unavailable live model without silently selecting fixture mode", async () => {
    const response = await worker.fetch(
      new Request(`${ORIGIN}/api/status`),
      environment("openai"),
    );
    await expect(response.json()).resolves.toMatchObject({
      narrative_mode: "openai",
      narrative_available: false,
      model_configured: false,
    });
  });

  it("logs only allowlisted route and method labels", async () => {
    const credential = `ghp_${"A".repeat(40)}`;
    const log = vi.spyOn(console, "log").mockImplementation(() => undefined);
    try {
      const response = await worker.fetch(
        new Request(`${ORIGIN}/${credential}`, { method: "PUT" }),
        environment(),
      );
      expect(response.status).toBe(200);
      const serializedLogs = log.mock.calls.flat().join(" ");
      expect(serializedLogs).not.toContain(credential);
      expect(serializedLogs).toContain('"method":"OTHER"');
      expect(serializedLogs).toContain('"path":"static"');
    } finally {
      log.mockRestore();
    }
  });

  it("serves static assets through the assets binding", async () => {
    const response = await worker.fetch(
      new Request(`${ORIGIN}/architecture/`),
      environment(),
    );
    expect(response.status).toBe(200);
    expect(response.headers.get("X-Request-ID")).toMatch(/^[0-9a-f-]+$/);
    expect(await response.text()).toBe("static asset");
  });

  it("runs the tracked synthetic narrative without an outbound model call", async () => {
    const outboundFetch = vi.fn<typeof fetch>();
    const result = await handleRequest(narrativeRequest(), environment(), {
      outboundFetch: outboundFetch as typeof fetch,
    });
    expect(result.status).toBe(200);
    expect(outboundFetch).not.toHaveBeenCalled();
    const payload = await result.json();
    expect(payload).toMatchObject({
      mode: "fixture",
      ai_model_call_performed: false,
      human_review_required: true,
      narrative: { model: FIXTURE_MODEL, ai_generated_analysis: true },
      verification: { accepted: false, human_review_required: true },
    });
  });

  it("rejects cross-origin, BYOK, compressed, and oversized requests", async () => {
    const crossOrigin = narrativeRequest();
    crossOrigin.headers.set("Origin", "https://attacker.example");
    await expect(
      handleRequest(crossOrigin, environment()),
    ).rejects.toMatchObject({
      code: "origin_rejected",
      status: 403,
    });

    const byok = narrativeRequest();
    byok.headers.set("X-OpenAI-Key", "browser-key");
    await expect(handleRequest(byok, environment())).rejects.toMatchObject({
      code: "byok_not_supported",
      status: 400,
    });

    const compressed = narrativeRequest();
    compressed.headers.set("Content-Encoding", "gzip");
    await expect(
      handleRequest(compressed, environment()),
    ).rejects.toMatchObject({
      code: "content_encoding_rejected",
      status: 415,
    });

    const oversized = narrativeRequest();
    oversized.headers.set("Content-Length", String(64 * 1024 + 1));
    await expect(handleRequest(oversized, environment())).rejects.toMatchObject(
      {
        code: "request_too_large",
        status: 413,
      },
    );

    const malformedLength = narrativeRequest();
    malformedLength.headers.set("Content-Length", "1e6");
    await expect(
      handleRequest(malformedLength, environment()),
    ).rejects.toMatchObject({
      code: "invalid_content_length",
      status: 400,
    });
  });

  it("rate limits before reading evidence and returns deterministic API errors", async () => {
    const response = await worker.fetch(
      narrativeRequest({ should_not_be_read: true }),
      environment("fixture", { rateLimitSuccess: false }),
    );
    expect(response.status).toBe(429);
    await expect(response.json()).resolves.toMatchObject({
      error: "rate_limited",
      human_review_required: true,
    });
  });

  it("enforces the global narrative limiter before client-specific processing", async () => {
    const response = await worker.fetch(
      narrativeRequest({ should_not_be_read: true }),
      environment("fixture", { globalRateLimitSuccess: false }),
    );
    expect(response.status).toBe(429);
    await expect(response.json()).resolves.toMatchObject({
      error: "rate_limited",
    });
  });

  it("rejects unknown public fields and credentials before any model transport", async () => {
    const unknown = structuredClone(fixturePackage) as Record<string, unknown>;
    unknown.unclassified_nested_value = { safe_looking: "value" };
    await expect(
      handleRequest(narrativeRequest(unknown), environment()),
    ).rejects.toMatchObject({
      code: "publication_policy_rejected",
    });

    const credential = structuredClone(fixturePackage) as Record<
      string,
      unknown
    >;
    credential.human_approval_status = `ghp_${"A".repeat(40)}`;
    const outboundFetch = vi.fn<typeof fetch>();
    await expect(
      handleRequest(
        narrativeRequest(credential),
        environment("openai", { apiKey: "unused" }),
        {
          outboundFetch: outboundFetch as typeof fetch,
        },
      ),
    ).rejects.toMatchObject({ code: "publication_policy_rejected" });
    expect(outboundFetch).not.toHaveBeenCalled();
  });

  it("rejects tampered deterministic evidence before any model transport", async () => {
    const tampered = structuredClone(fixturePackage);
    tampered.findings[0]!.status = "not evaluated";
    const outboundFetch = vi.fn<typeof fetch>();
    await expect(
      handleRequest(
        narrativeRequest(tampered),
        environment("openai", { apiKey: "unused" }),
        { outboundFetch },
      ),
    ).rejects.toMatchObject({
      code: "package_schema_rejected",
      message: expect.stringMatching(/^evidence identity mismatch/),
    });
    expect(outboundFetch).not.toHaveBeenCalled();
  });

  it("calls the fixed Responses API contract once in OpenAI mode", async () => {
    const output = modelOutput();
    const outboundFetch = vi.fn<typeof fetch>(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const inputUrl =
          typeof input === "string"
            ? input
            : input instanceof URL
              ? input.href
              : input.url;
        expect(inputUrl).toBe("https://api.openai.com/v1/responses");
        expect(init?.method).toBe("POST");
        if (typeof init?.body !== "string") {
          throw new Error("OpenAI request body was not JSON text");
        }
        const body = JSON.parse(init.body) as Record<string, unknown>;
        expect(body).toMatchObject({
          model: "gpt-5.6-terra",
          store: false,
          max_output_tokens: 1600,
          reasoning: { effort: "low" },
        });
        expect(body).not.toHaveProperty("tools");
        return Response.json(responseEnvelope(output));
      },
    );
    const response = await handleRequest(
      narrativeRequest(),
      environment("openai", { apiKey: TEST_API_KEY }),
      { outboundFetch: outboundFetch as typeof fetch },
    );
    expect(outboundFetch).toHaveBeenCalledTimes(1);
    expect(await response.json()).toMatchObject({
      mode: "openai",
      ai_model_call_performed: true,
      human_review_required: true,
    });
  });

  it("never silently falls back to fixture output after an upstream failure", async () => {
    const outboundFetch = vi.fn<typeof fetch>(
      async () => new Response("limited", { status: 429 }),
    );
    await expect(
      handleRequest(
        narrativeRequest(),
        environment("openai", { apiKey: TEST_API_KEY }),
        { outboundFetch: outboundFetch as typeof fetch },
      ),
    ).rejects.toMatchObject({
      code: "narrative_capacity_unavailable",
      status: 503,
    });
  });

  it.each([
    [
      "insufficient_quota",
      "narrative_quota_unavailable",
      "narrative quota is unavailable",
    ],
    [
      "rate_limit_exceeded",
      "narrative_upstream_rate_limited",
      "the narrative service rate limit was reached",
    ],
  ])(
    "distinguishes sanitized OpenAI 429 code %s without exposing its body",
    async (upstreamCode, errorCode, message) => {
      const privateDetail = `ghp_${"A".repeat(40)}`;
      await expect(
        handleRequest(
          narrativeRequest(),
          environment("openai", { apiKey: TEST_API_KEY }),
          {
            outboundFetch: async () =>
              Response.json(
                {
                  error: {
                    code: upstreamCode,
                    message: privateDetail,
                    type: "invalid_request_error",
                  },
                },
                { status: 429 },
              ),
          },
        ),
      ).rejects.toMatchObject({ code: errorCode, message, status: 503 });
    },
  );

  it("fails safely when an upstream error body exceeds the metadata bound", async () => {
    await expect(
      handleRequest(
        narrativeRequest(),
        environment("openai", { apiKey: TEST_API_KEY }),
        {
          outboundFetch: async () =>
            Response.json(
              {
                error: {
                  code: "insufficient_quota",
                  message: "x".repeat(17 * 1024),
                },
              },
              { status: 429 },
            ),
        },
      ),
    ).rejects.toMatchObject({
      code: "narrative_capacity_unavailable",
      message: "narrative capacity is unavailable",
      status: 503,
    });
  });

  it("classifies transport failure without exposing exception text", async () => {
    await expect(
      handleRequest(
        narrativeRequest(),
        environment("openai", { apiKey: TEST_API_KEY }),
        {
          outboundFetch: async () => {
            throw new Error(`ghp_${"A".repeat(40)}`);
          },
        },
      ),
    ).rejects.toMatchObject({
      code: "upstream_connection_failed",
      message: "the narrative service connection failed",
      status: 502,
    });
  });

  it.each([
    [400, "upstream_request_rejected", 502],
    [404, "narrative_model_unavailable", 503],
    [500, "upstream_service_unavailable", 502],
  ])(
    "classifies upstream HTTP %i without exposing its body",
    async (upstreamStatus, errorCode, status) => {
      const sensitiveBody = `ghp_${"A".repeat(40)}`;
      await expect(
        handleRequest(
          narrativeRequest(),
          environment("openai", { apiKey: TEST_API_KEY }),
          {
            outboundFetch: async () =>
              new Response(sensitiveBody, { status: upstreamStatus }),
          },
        ),
      ).rejects.toMatchObject({ code: errorCode, status });
    },
  );
});

describe("narrative verification", () => {
  it("requires unique, exact finding-set coverage", async () => {
    const document = packageDocument();
    const valid = await buildNarrativeEvidence(
      modelOutput(),
      document,
      FIXTURE_MODEL,
    );

    const duplicate = structuredClone(valid);
    duplicate.drift_explanations[1] = structuredClone(
      duplicate.drift_explanations[0]!,
    );
    const duplicateResult = await verifyNarrative(duplicate, document);
    expect(duplicateResult.reasons).toEqual(
      expect.arrayContaining([
        expect.stringMatching(/^duplicate finding explanation IDs:/),
        expect.stringMatching(/^missing deterministic finding explanations:/),
      ]),
    );

    const missing = structuredClone(valid);
    missing.drift_explanations.pop();
    const missingResult = await verifyNarrative(missing, document);
    expect(missingResult.reasons).toEqual(
      expect.arrayContaining([
        expect.stringMatching(/^missing deterministic finding explanations:/),
      ]),
    );

    const unknown = structuredClone(valid);
    unknown.drift_explanations[0]!.finding_evidence_id = `ev1-${"f".repeat(24)}`;
    const unknownResult = await verifyNarrative(unknown, document);
    expect(unknownResult.reasons).toEqual(
      expect.arrayContaining([
        expect.stringMatching(/^unknown finding explanation IDs:/),
      ]),
    );
  });

  it("quarantines unrestricted evaluative prose even when synonyms evade phrase lists", async () => {
    const document = packageDocument();
    const output = modelOutput();
    output.executive_summary =
      "The assessor can conclude the configuration fully conforms to all mandates and needs no further judgment.";
    const narrative = await buildNarrativeEvidence(
      output,
      document,
      FIXTURE_MODEL,
    );
    const result = await verifyNarrative(narrative, document);
    expect(result.accepted).toBe(false);
    expect(result.accepted_claims).toHaveLength(document.findings.length);
    expect(
      result.accepted_claims.every((claim) =>
        claim.includes(":finding_status="),
      ),
    ).toBe(true);
    expect(result.rejected_claims).toContain(
      "generated prose quarantined: executive_summary",
    );
  });

  it("rejects unknown structured claim codes and unexpected fields", () => {
    const unknownClaim = structuredClone(modelOutput()) as unknown as Record<
      string,
      unknown
    >;
    const explanations = unknownClaim.drift_explanations as Array<
      Record<string, unknown>
    >;
    explanations[0]!.deterministic_claim = {
      claim_code: "control_satisfaction",
      claim_value: "matches desired state",
    };
    expect(() => parseNarrativeModelOutput(unknownClaim)).toThrow(HttpError);

    const unexpected = structuredClone(modelOutput()) as unknown as Record<
      string,
      unknown
    >;
    unexpected.compliance_verdict = "approved";
    expect(() => parseNarrativeModelOutput(unexpected)).toThrow(HttpError);
  });
});

describe("shared credential catalog", () => {
  it.each(["ghp_", "gho_", "ghu_", "ghs_", "ghr_"])(
    "rejects the %s underscore-form GitHub token",
    (prefix) => {
      expect(() => assertPublicSafe(`${prefix}${"A".repeat(40)}`)).toThrow(
        HttpError,
      );
    },
  );

  it("rejects fine-grained GitHub tokens", () => {
    expect(() => assertPublicSafe(`github_pat_${"A".repeat(82)}`)).toThrow(
      HttpError,
    );
  });
});
