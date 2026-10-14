import assert from "node:assert/strict";
import { webcrypto } from "node:crypto";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const mission = JSON.parse(
  await readFile(
    new URL("../docs/assets/data/mission-control.json", import.meta.url),
  ),
);
const matrix = JSON.parse(
  await readFile(
    new URL("../docs/assets/data/settings-matrix.json", import.meta.url),
  ),
);
const context = vm.createContext({
  window: {},
  crypto: webcrypto,
  TextEncoder,
});
vm.runInContext(
  await readFile(
    new URL(
      "../docs/assets/javascripts/settings-matrix-contract.js",
      import.meta.url,
    ),
    "utf8",
  ),
  context,
);
const validate = context.window.ProvifactMatrix.validate;

test("accepts the Python-generated canonical matrix", async () => {
  const result = await validate(matrix, mission);
  assert.equal(result.rows.length, 98);
  assert.equal(result.source_snapshot_id, mission.snapshot_id);
});

for (const [name, mutate] of [
  [
    "stale snapshot",
    (value) => {
      value.source_snapshot_id = `mission-${"0".repeat(24)}`;
    },
  ],
  [
    "changed observation",
    (value) => {
      value.rows[0].requirement.observed_value = "forged";
    },
  ],
  [
    "missing row",
    (value) => {
      value.rows.pop();
    },
  ],
  [
    "duplicate row",
    (value) => {
      value.rows[1] = structuredClone(value.rows[0]);
    },
  ],
  [
    "private policy reference",
    (value) => {
      value.rows[0].parent_policy_ref = "policy-private-forged";
    },
  ],
  [
    "unapproved profile",
    (value) => {
      value.rows[0].baseline_profile_id = "cis_lvl2";
    },
  ],
  [
    "invented precedence",
    (value) => {
      value.rows[0].policy_precedence = "highest wins";
    },
  ],
]) {
  test(`rejects ${name} even with a recomputed matrix fingerprint`, async () => {
    const value = structuredClone(matrix);
    mutate(value);
    const canonical = (item) => {
      if (Array.isArray(item)) return `[${item.map(canonical).join(",")}]`;
      if (item !== null && typeof item === "object")
        return `{${Object.keys(item)
          .sort()
          .map((key) => `${JSON.stringify(key)}:${canonical(item[key])}`)
          .join(",")}}`;
      return JSON.stringify(item);
    };
    const unsigned = { ...value };
    delete unsigned.content_fingerprint;
    const digest = await webcrypto.subtle.digest(
      "SHA-256",
      new TextEncoder().encode(
        canonical(unsigned).replace(
          /[\u007f-\uffff]/g,
          (character) =>
            `\\u${character.charCodeAt(0).toString(16).padStart(4, "0")}`,
        ),
      ),
    );
    value.content_fingerprint = `sha256:${Buffer.from(digest).toString("hex")}`;
    await assert.rejects(validate(value, mission), /does not match/);
  });
}

test("rejects a tampered Mission even when the matrix still names its old identity", async () => {
  const value = structuredClone(mission);
  value.requirements[0].expected_value = "forged";
  await assert.rejects(validate(matrix, value), /does not match/);
});
