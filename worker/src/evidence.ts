import type { EvidenceIdentity, JsonValue } from "./types";

const RESERVED_FIELDS = new Set([
  "schema_version",
  "object_type",
  "evidence_id",
  "content_fingerprint",
]);

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function canonicalJson(value: JsonValue): string {
  const sorted = sortJson(value);
  const encoded = JSON.stringify(sorted);
  return encoded.replace(/[\u007f-\uffff]/g, (character) => {
    return `\\u${character.charCodeAt(0).toString(16).padStart(4, "0")}`;
  });
}

function sortJson(value: JsonValue): JsonValue {
  if (Array.isArray(value)) {
    return value.map((item) => sortJson(item));
  }
  if (typeof value !== "object" || value === null) {
    return value;
  }
  const result: { [key: string]: JsonValue } = {};
  for (const key of Object.keys(value).sort()) {
    const item = value[key];
    if (item !== undefined) {
      result[key] = sortJson(item);
    }
  }
  return result;
}

export async function sha256(value: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

export async function makeEvidenceObject(
  objectType: string,
  payload: { [key: string]: JsonValue },
): Promise<EvidenceIdentity> {
  for (const key of Object.keys(payload)) {
    if (RESERVED_FIELDS.has(key)) {
      throw new Error(`reserved evidence field supplied: ${key}`);
    }
  }
  const unsigned: { [key: string]: JsonValue } = {
    schema_version: "1.0.0",
    object_type: objectType,
    ...payload,
  };
  const digest = await sha256(canonicalJson(unsigned));
  return {
    ...unsigned,
    schema_version: "1.0.0",
    object_type: objectType,
    evidence_id: `ev1-${digest.slice(0, 24)}`,
    content_fingerprint: `sha256:${digest}`,
  };
}

export function assertJsonValue(
  value: unknown,
  depth = 0,
): asserts value is JsonValue {
  if (depth > 16) {
    throw new Error("JSON nesting exceeds the EvidenceOps limit");
  }
  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "boolean"
  ) {
    return;
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new Error("JSON number must be finite");
    }
    return;
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      assertJsonValue(item, depth + 1);
    }
    return;
  }
  if (isRecord(value)) {
    for (const item of Object.values(value)) {
      assertJsonValue(item, depth + 1);
    }
    return;
  }
  throw new Error("value is not JSON serializable");
}
