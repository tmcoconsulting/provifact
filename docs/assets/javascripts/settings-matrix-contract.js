(() => {
  "use strict";
  const isRecord = (value) =>
    value !== null && typeof value === "object" && !Array.isArray(value);
  const canonicalJson = (value) => {
    if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
    if (isRecord(value))
      return `{${Object.keys(value)
        .sort()
        .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
        .join(",")}}`;
    return JSON.stringify(value);
  };
  const same = (left, right) => canonicalJson(left) === canonicalJson(right);
  const exactKeys = (value, keys) =>
    isRecord(value) &&
    Object.keys(value).sort().join(",") === keys.sort().join(",");
  const fingerprint = async (value) => {
    const digest = await crypto.subtle.digest(
      "SHA-256",
      new TextEncoder().encode(
        canonicalJson(value).replace(
          /[\u007f-\uffff]/g,
          (character) =>
            `\\u${character.charCodeAt(0).toString(16).padStart(4, "0")}`,
        ),
      ),
    );
    return `sha256:${[...new Uint8Array(digest)]
      .map((byte) => byte.toString(16).padStart(2, "0"))
      .join("")}`;
  };
  const reject = () => {
    throw new Error("Canonical matrix does not match this Mission snapshot");
  };
  const validate = async (value, mission) => {
    if (
      !exactKeys(value, [
        "schema_version",
        "source_snapshot_id",
        "source_content_fingerprint",
        "content_fingerprint",
        "rows",
      ]) ||
      value.schema_version !== "1.0.0" ||
      value.source_snapshot_id !== mission.snapshot_id ||
      value.source_content_fingerprint !== mission.content_fingerprint ||
      !Array.isArray(value.rows) ||
      value.rows.length !== mission.requirements.length
    )
      reject();
    const unsignedMission = { ...mission };
    delete unsignedMission.snapshot_id;
    delete unsignedMission.content_fingerprint;
    const missionFingerprint = await fingerprint(unsignedMission);
    if (
      missionFingerprint !== mission.content_fingerprint ||
      mission.snapshot_id !== `mission-${missionFingerprint.slice(7, 31)}`
    )
      reject();
    const unsigned = { ...value };
    delete unsigned.content_fingerprint;
    if (value.content_fingerprint !== (await fingerprint(unsigned))) reject();
    const requirements = new Map(
      mission.requirements.map((item) => [item.requirement_id, item]),
    );
    const findings = new Map(
      mission.findings.map((item) => [item.requirement_id, item]),
    );
    const resources = new Map(
      mission.resources.map((item) => [item.source_evidence_id, item]),
    );
    const seen = new Set();
    for (const row of value.rows) {
      if (
        !exactKeys(row, [
          "baseline_profile_id",
          "benchmark",
          "benchmark_version",
          "requirement",
          "finding",
          "resources",
          "change_guidance",
          "limitations",
          "policy_precedence",
        ]) ||
        row.baseline_profile_id !== "tmco_approved" ||
        row.benchmark !== mission.baseline.benchmark ||
        row.benchmark_version !== mission.baseline.benchmark_version ||
        row.policy_precedence !== "unknown" ||
        !isRecord(row.requirement) ||
        typeof row.change_guidance !== "string" ||
        row.change_guidance.length > 400 ||
        !Array.isArray(row.limitations) ||
        row.limitations.length !== 4 ||
        !row.limitations.every(
          (item) => typeof item === "string" && item.length <= 200,
        )
      )
        reject();
      const id = row.requirement.requirement_id;
      const requirement = requirements.get(id);
      if (
        !requirement ||
        seen.has(id) ||
        !same(row.requirement, requirement) ||
        !same(row.finding, findings.get(id) || null) ||
        !same(
          row.resources,
          requirement.source_evidence_ids
            .map((identifier) => resources.get(identifier))
            .filter(Boolean),
        )
      )
        reject();
      seen.add(id);
    }
    return value;
  };
  window.ProvifactMatrix = Object.freeze({ validate });
})();
