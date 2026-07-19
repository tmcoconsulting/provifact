import credentialCatalog from "../../evidenceops/sanitization/credential-patterns.v1.json";
import publicationPolicy from "../../evidenceops/sanitization/publication-policy.v1.json";
import publicValueCatalog from "../../evidenceops/sanitization/public-value-patterns.v1.json";

import { isRecord, sha256 } from "./evidence";

export const MAX_REQUEST_BYTES = 64 * 1024;
export const MAX_UPSTREAM_BYTES = 256 * 1024;
export const OPENAI_TIMEOUT_MS = 20_000;

interface CompiledPattern {
  label: string;
  pattern: RegExp;
}

export class HttpError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "HttpError";
    this.status = status;
    this.code = code;
  }
}

function compilePatterns(
  entries: ReadonlyArray<{ label: string; expression: string; flags: string }>,
): CompiledPattern[] {
  if (entries.length === 0) {
    throw new Error("sensitive-value pattern catalog must not be empty");
  }
  return entries.map((entry) => {
    if (
      !entry.label ||
      !entry.expression ||
      (entry.flags !== "" && entry.flags !== "i")
    ) {
      throw new Error("sensitive-value pattern catalog entry is invalid");
    }
    return {
      label: entry.label,
      pattern: new RegExp(entry.expression, entry.flags),
    };
  });
}

const SENSITIVE_VALUE_PATTERNS = [
  ...compilePatterns(credentialCatalog.patterns),
  ...compilePatterns(publicValueCatalog.patterns),
];

const FIELD_ACTIONS = new Map<string, string>(
  Object.entries(publicationPolicy.fields),
);

export function hasUsableOpenAIKey(value: unknown): value is string {
  return typeof value === "string" && /^sk-[A-Za-z0-9_-]{20,}$/.test(value);
}

export function assertPublicSafe(value: unknown, depth = 0): void {
  if (depth > 16) {
    throw new HttpError(
      422,
      "publication_policy_rejected",
      "public package nesting is too deep",
    );
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      assertPublicSafe(item, depth + 1);
    }
    return;
  }
  if (isRecord(value)) {
    for (const [field, item] of Object.entries(value)) {
      const action = FIELD_ACTIONS.get(field);
      if (action !== "allow") {
        throw new HttpError(
          422,
          "publication_policy_rejected",
          action === undefined
            ? `unclassified public field: ${field}`
            : `non-public field reached Worker egress: ${field}`,
        );
      }
      assertPublicSafe(item, depth + 1);
    }
    return;
  }
  if (typeof value !== "string") {
    return;
  }
  for (const entry of SENSITIVE_VALUE_PATTERNS) {
    entry.pattern.lastIndex = 0;
    if (entry.pattern.test(value)) {
      throw new HttpError(
        422,
        "publication_policy_rejected",
        `prohibited ${entry.label} reached Worker egress`,
      );
    }
  }
}

export function assertSameOrigin(request: Request): void {
  const expected = new URL(request.url).origin;
  const origin = request.headers.get("Origin");
  if (origin !== expected) {
    throw new HttpError(
      403,
      "origin_rejected",
      "narrative requests must be same-origin",
    );
  }
  const fetchSite = request.headers.get("Sec-Fetch-Site");
  if (fetchSite !== null && fetchSite !== "same-origin") {
    throw new HttpError(
      403,
      "origin_rejected",
      "cross-site narrative requests are denied",
    );
  }
  if (
    request.headers.has("Authorization") ||
    request.headers.has("X-OpenAI-Key")
  ) {
    throw new HttpError(
      400,
      "byok_not_supported",
      "browser-supplied API keys are not accepted",
    );
  }
}

export async function readBoundedJson(request: Request): Promise<unknown> {
  const contentType = request.headers
    .get("Content-Type")
    ?.split(";", 1)[0]
    ?.trim();
  if (contentType !== "application/json") {
    throw new HttpError(
      415,
      "unsupported_media_type",
      "Content-Type must be application/json",
    );
  }
  const contentEncoding = request.headers.get("Content-Encoding");
  if (contentEncoding !== null && contentEncoding !== "identity") {
    throw new HttpError(
      415,
      "content_encoding_rejected",
      "compressed request bodies are denied",
    );
  }
  const declaredLength = request.headers.get("Content-Length");
  if (declaredLength !== null) {
    if (!/^(?:0|[1-9]\d*)$/.test(declaredLength)) {
      throw new HttpError(
        400,
        "invalid_content_length",
        "Content-Length is invalid",
      );
    }
    const parsedLength = Number.parseInt(declaredLength, 10);
    if (!Number.isSafeInteger(parsedLength) || parsedLength < 0) {
      throw new HttpError(
        400,
        "invalid_content_length",
        "Content-Length is invalid",
      );
    }
    if (parsedLength > MAX_REQUEST_BYTES) {
      throw new HttpError(
        413,
        "request_too_large",
        "evidence package exceeds the size limit",
      );
    }
  }
  if (request.body === null) {
    throw new HttpError(
      400,
      "body_required",
      "a JSON evidence package is required",
    );
  }
  const bytes = await readBoundedStream(request.body, MAX_REQUEST_BYTES, {
    code: "request_too_large",
    message: "evidence package exceeds the size limit",
    status: 413,
  });
  let text: string;
  try {
    text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: false }).decode(
      bytes,
    );
  } catch {
    throw new HttpError(
      400,
      "invalid_utf8",
      "request body must be valid UTF-8",
    );
  }
  try {
    return JSON.parse(text);
  } catch {
    throw new HttpError(400, "invalid_json", "request body must be valid JSON");
  }
}

export async function readBoundedResponse(
  response: Response,
): Promise<unknown> {
  if (response.body === null) {
    throw new HttpError(
      502,
      "upstream_response_invalid",
      "upstream response body was missing",
    );
  }
  const bytes = await readBoundedStream(response.body, MAX_UPSTREAM_BYTES, {
    code: "upstream_response_too_large",
    message: "upstream response exceeded the byte limit",
    status: 502,
  });
  try {
    return JSON.parse(
      new TextDecoder("utf-8", { fatal: true, ignoreBOM: false }).decode(bytes),
    );
  } catch {
    throw new HttpError(
      502,
      "upstream_response_invalid",
      "upstream response was not valid JSON",
    );
  }
}

async function readBoundedStream(
  stream: ReadableStream<Uint8Array>,
  maximumBytes: number,
  error: { code: string; message: string; status: number },
): Promise<Uint8Array> {
  const reader = stream.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  while (true) {
    const result = await reader.read();
    if (result.done) {
      break;
    }
    total += result.value.byteLength;
    if (total > maximumBytes) {
      await reader.cancel("EvidenceOps byte limit exceeded");
      throw new HttpError(error.status, error.code, error.message);
    }
    chunks.push(result.value);
  }
  const combined = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    combined.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return combined;
}

export async function rateLimitKey(request: Request): Promise<string> {
  const actor =
    request.headers.get("CF-Connecting-IP") ?? "anonymous-public-client";
  return sha256(`${new URL(request.url).origin}|narrative|${actor}`);
}

export function jsonResponse(
  payload: unknown,
  status = 200,
  extraHeaders?: HeadersInit,
): Response {
  const headers = new Headers(extraHeaders);
  headers.set("Cache-Control", "no-store");
  headers.set("Content-Type", "application/json; charset=utf-8");
  headers.set("Cross-Origin-Resource-Policy", "same-origin");
  headers.set(
    "Permissions-Policy",
    "camera=(), geolocation=(), microphone=(), payment=()",
  );
  headers.set("Referrer-Policy", "no-referrer");
  headers.set("X-Content-Type-Options", "nosniff");
  headers.set("X-Frame-Options", "DENY");
  return new Response(JSON.stringify(payload), { status, headers });
}
