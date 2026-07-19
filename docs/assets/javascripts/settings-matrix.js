(() => {
  "use strict";

  const root = document.querySelector("[data-settings-matrix]");
  if (!(root instanceof HTMLElement)) return;

  const banner = root.querySelector("[data-matrix-banner]");
  const summary = root.querySelector("[data-matrix-summary]");
  const table = root.querySelector("[data-matrix-table]");
  const search = root.querySelector("[data-matrix-search]");
  const outcome = root.querySelector("[data-matrix-outcome]");
  const framework = root.querySelector("[data-matrix-framework]");
  const mappedOnly = root.querySelector("[data-matrix-mapped-only]");
  const reset = root.querySelector("[data-matrix-reset]");
  const count = root.querySelector("[data-matrix-count]");
  const empty = root.querySelector("[data-matrix-empty]");

  if (
    !(banner instanceof HTMLElement) ||
    !(summary instanceof HTMLElement) ||
    !(table instanceof HTMLTableElement) ||
    !(search instanceof HTMLInputElement) ||
    !(outcome instanceof HTMLSelectElement) ||
    !(framework instanceof HTMLSelectElement) ||
    !(mappedOnly instanceof HTMLInputElement) ||
    !(reset instanceof HTMLButtonElement) ||
    !(count instanceof HTMLElement) ||
    !(empty instanceof HTMLElement)
  ) {
    return;
  }

  const frameworkColumns = [
    { key: "cis_benchmark", label: "CIS L1" },
    { key: "cis_lvl2", label: "CIS L2" },
    { key: "stig", label: "STIG" },
    { key: "nist_800_171r3", label: "NIST 800-171" },
    { key: "nist_800_53r5", label: "NIST 800-53" },
    { key: "cmmc", label: "CMMC" },
  ];

  const create = (tagName, className = "", text = "") => {
    const node = document.createElement(tagName);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  };

  const isRecord = (value) =>
    value !== null && typeof value === "object" && !Array.isArray(value);

  const formatValue = (value) => {
    if (typeof value === "string") return value;
    if (value === null || value === undefined) return "not available";
    if (Array.isArray(value)) return value.map(formatValue).join(" / ");
    if (isRecord(value)) return JSON.stringify(value);
    return String(value);
  };

  const stateClass = (value) => {
    if (value === "Aligned") return "matrix-state-aligned";
    if (value === "Conflicting policy") return "matrix-state-conflict";
    if (value === "Missing from tenant") return "matrix-state-missing";
    if (value === "Unsupported by provider")
      return "matrix-state-unsupported";
    if (value === "Human review required" || value === "Collection gap")
      return "matrix-state-review";
    return "matrix-state-drift";
  };

  const frameworkIds = (requirement, key) => {
    if (key === "cis_lvl2") return [];
    if (!isRecord(requirement.mappings)) return [];
    const values = requirement.mappings[key];
    return Array.isArray(values)
      ? values.filter((value) => typeof value === "string")
      : [];
  };

  const hasMappings = (requirement) =>
    frameworkColumns.some(
      ({ key }) =>
        key !== "cis_lvl2" && frameworkIds(requirement, key).length,
    );

  const buildRequiredChange = (row) => {
    const { requirement, finding, settingKey } = row;
    const expected = formatValue(requirement.expected_value);
    const observed = formatValue(requirement.observed_value);
    const key = settingKey || requirement.rule_id;

    switch (requirement.outcome) {
      case "Aligned":
        return `No setting-value change is indicated. Keep ${key} at ${expected}; verify intended scope and retain operating evidence.`;
      case "Value drift":
        return `Set ${key} to ${expected} in the approved Intune policy (observed: ${observed}), then re-collect and review the resulting assignment evidence.`;
      case "Assignment drift":
        return `Keep ${key} at ${expected}; assign the approved policy to the intended scope, review exclusions, then re-collect.`;
      case "Conflicting policy":
        return `Resolve overlapping Intune policies so the effective value of ${key} is ${expected} (observed conflict: ${observed}), then verify precedence and assignment.`;
      case "Missing from tenant":
        return `Create or identify an approved Intune policy that expresses ${key} = ${expected}, assign it to the intended scope, then re-collect.`;
      case "Collection gap":
        return "Restore the documented read-only collection path or provide alternate evidence before evaluating this setting.";
      case "Human review required":
        return `Have a qualified reviewer resolve the ambiguous value for ${key}; EvidenceOps will not infer or apply a change.`;
      case "Unsupported by provider":
        return "No automated comparison is available. Add and review a provider mapping before using this rule for technical alignment.";
      default:
        return finding && typeof finding.remediation_guidance === "string"
          ? finding.remediation_guidance
          : "Human review is required; EvidenceOps has no Intune write capability.";
    }
  };

  const renderState = (label) => {
    const badge = create(
      "span",
      `matrix-state ${stateClass(label)}`,
      label,
    );
    badge.setAttribute(
      "title",
      "Technical evidence state; not a framework verdict",
    );
    return badge;
  };

  const renderFrameworkCell = (requirement, key) => {
    const cell = create("td");
    if (key === "cis_lvl2") {
      cell.append(
        create(
          "span",
          "matrix-state matrix-state-not-loaded",
          "Baseline not loaded",
        ),
        create(
          "span",
          "matrix-cell-note",
          "No CIS Level 2 profile is approved in this package; no inference is made.",
        ),
      );
      return cell;
    }

    const ids = frameworkIds(requirement, key);
    if (!ids.length) {
      cell.append(
        create(
          "span",
          "matrix-state matrix-state-unsupported",
          "No reviewed mapping",
        ),
      );
      return cell;
    }

    cell.append(renderState(requirement.outcome));
    const values = create("div", "matrix-control-ids");
    for (const id of ids)
      values.append(create("code", "matrix-control-id", id));
    cell.append(values);
    return cell;
  };

  const renderValueCell = (value) => {
    const cell = create("td", "matrix-value");
    cell.append(create("code", "", formatValue(value)));
    return cell;
  };

  const validateMission = (value) => {
    if (
      !isRecord(value) ||
      value.schema_version !== "2.0.0" ||
      typeof value.snapshot_id !== "string" ||
      typeof value.data_mode !== "string" ||
      !Array.isArray(value.requirements) ||
      !Array.isArray(value.findings) ||
      !Array.isArray(value.resources) ||
      !isRecord(value.collection) ||
      typeof value.collection.collected_at_utc !== "string" ||
      !isRecord(value.baseline)
    ) {
      throw new Error("Mission package failed the matrix contract");
    }
    return value;
  };

  const initialize = async () => {
    try {
      const response = await fetch("/assets/data/mission-control.json", {
        credentials: "same-origin",
        headers: { Accept: "application/json" },
      });
      if (
        !response.ok ||
        !response.headers.get("Content-Type")?.includes("application/json")
      ) {
        throw new Error("Mission package could not be loaded");
      }

      const mission = validateMission(await response.json());
      const findingsByRequirement = new Map(
        mission.findings
          .filter(
            (item) =>
              isRecord(item) && typeof item.requirement_id === "string",
          )
          .map((item) => [item.requirement_id, item]),
      );
      const resourcesByEvidence = new Map(
        mission.resources
          .filter(
            (item) =>
              isRecord(item) && typeof item.source_evidence_id === "string",
          )
          .map((item) => [item.source_evidence_id, item]),
      );

      const rows = mission.requirements
        .filter(
          (item) =>
            isRecord(item) &&
            typeof item.requirement_id === "string" &&
            typeof item.rule_id === "string" &&
            typeof item.title === "string" &&
            typeof item.outcome === "string",
        )
        .map((requirement) => {
          const finding = findingsByRequirement.get(requirement.requirement_id);
          const evidenceIds = Array.isArray(requirement.source_evidence_ids)
            ? requirement.source_evidence_ids.filter(
                (value) => typeof value === "string",
              )
            : [];
          const evidence = evidenceIds.map((id) =>
            resourcesByEvidence.get(id),
          );
          const settingKey =
            isRecord(finding) && typeof finding.setting_key === "string"
              ? finding.setting_key
              : "not published for this row";
          const row = {
            requirement,
            finding,
            evidenceIds,
            evidence,
            settingKey,
          };
          return { ...row, requiredChange: buildRequiredChange(row) };
        });

      const outcomeValues = [
        ...new Set(rows.map(({ requirement }) => requirement.outcome)),
      ].sort();
      for (const value of outcomeValues) {
        const option = create("option", "", value);
        option.value = value;
        outcome.append(option);
      }

      const mapped = rows.filter(({ requirement }) =>
        hasMappings(requirement),
      );
      const aligned = mapped.filter(
        ({ requirement }) => requirement.outcome === "Aligned",
      ).length;
      const evaluated = mapped.filter(
        ({ requirement }) => requirement.evaluation_included === true,
      ).length;
      const drifted = evaluated - aligned;

      const summaryValues = [
        [String(rows.length), "Baseline rules visible"],
        [String(mapped.length), "Reviewed setting mappings"],
        [String(aligned), "Aligned technical settings"],
        [String(drifted), "Mapped settings needing review"],
        ["Not loaded", "CIS Level 2 baseline"],
      ];
      summary.replaceChildren();
      for (const [value, label] of summaryValues) {
        const card = create("article", "matrix-summary-card");
        card.append(
          create("strong", "", value),
          create("span", "", label),
        );
        summary.append(card);
      }

      const collected = Date.parse(mission.collection.collected_at_utc);
      const timestamp = Number.isFinite(collected)
        ? new Date(collected).toLocaleString()
        : mission.collection.collected_at_utc;
      banner.textContent = `${mission.data_mode} · ${mission.baseline.benchmark_version || "baseline version unavailable"} · collected ${timestamp} · tenant policy display names are intentionally not public`;
      banner.dataset.state = mission.data_mode.startsWith("LIVE")
        ? "live"
        : "fixture";

      const render = () => {
        const query = search.value.trim().toLowerCase();
        const selectedOutcome = outcome.value;
        const selectedFramework = framework.value;
        const onlyMapped = mappedOnly.checked;

        const filtered = rows.filter((row) => {
          const {
            requirement,
            evidenceIds,
            evidence,
            settingKey,
            requiredChange,
          } = row;
          if (onlyMapped && !hasMappings(requirement)) return false;
          if (selectedOutcome && requirement.outcome !== selectedOutcome)
            return false;
          if (
            selectedFramework &&
            selectedFramework !== "cis_lvl2" &&
            !frameworkIds(requirement, selectedFramework).length
          )
            return false;
          if (selectedFramework === "cis_lvl2") return false;
          if (!query) return true;

          const searchable = [
            requirement.title,
            requirement.rule_id,
            requirement.section,
            requirement.outcome,
            settingKey,
            formatValue(requirement.expected_value),
            formatValue(requirement.observed_value),
            requiredChange,
            ...evidenceIds,
            ...evidence.flatMap((item) =>
              isRecord(item)
                ? [
                    item.title,
                    item.resource_family,
                    item.source_api_version,
                  ]
                : [],
            ),
            ...frameworkColumns.flatMap(({ key }) =>
              frameworkIds(requirement, key),
            ),
          ]
            .filter((value) => typeof value === "string")
            .join(" ")
            .toLowerCase();
          return searchable.includes(query);
        });

        const head = table.tHead || table.createTHead();
        head.replaceChildren();
        const headerRow = head.insertRow();
        const headers = [
          "Intune policy / setting evidence",
          "Observed",
          "Approved target",
          "Technical state",
          ...frameworkColumns.map(({ label }) => label),
          "Required change",
        ];
        for (const label of headers)
          headerRow.append(create("th", "", label));

        const body = table.tBodies[0] || table.createTBody();
        body.replaceChildren();
        for (const row of filtered) {
          const {
            requirement,
            evidence,
            evidenceIds,
            settingKey,
            requiredChange,
          } = row;
          const tr = body.insertRow();
          const settingCell = create("td");
          settingCell.append(
            create("strong", "matrix-setting-title", requirement.title),
            create("code", "matrix-setting-meta", settingKey),
            create(
              "span",
              "matrix-setting-meta",
              `${requirement.section || "Unsectioned"} · ${requirement.rule_id}`,
            ),
          );

          if (evidenceIds.length) {
            const evidenceList = create("span", "matrix-evidence-list");
            const labels = evidenceIds.map((id, index) => {
              const resource = evidence[index];
              return isRecord(resource) && typeof resource.title === "string"
                ? `${resource.title} (${resource.source_api_version || "API version unavailable"})`
                : id;
            });
            evidenceList.textContent = `Public-safe evidence: ${labels.join("; ")}`;
            settingCell.append(evidenceList);
          } else {
            settingCell.append(
              create(
                "span",
                "matrix-evidence-list",
                "No normalized setting evidence linked.",
              ),
            );
          }

          tr.append(
            settingCell,
            renderValueCell(requirement.observed_value),
            renderValueCell(requirement.expected_value),
          );
          const stateCell = create("td");
          stateCell.append(
            renderState(requirement.outcome),
            create(
              "span",
              "matrix-cell-note",
              requirement.assignment_summary ||
                "Assignment state unavailable",
            ),
          );
          tr.append(stateCell);
          for (const { key } of frameworkColumns) {
            tr.append(renderFrameworkCell(requirement, key));
          }
          tr.append(
            create("td", "matrix-required-change", requiredChange),
          );
        }

        count.textContent = `${filtered.length} of ${rows.length} baseline requirements shown`;
        empty.hidden = filtered.length !== 0;
        if (!filtered.length) {
          empty.textContent =
            selectedFramework === "cis_lvl2"
              ? "No rows are shown because CIS Level 2 is not loaded in the current approved package. Add and review a Level 2 baseline before evaluating it."
              : "No requirements match the selected filters.";
        }
      };

      for (const control of [search, outcome, framework, mappedOnly]) {
        control.addEventListener("input", render);
        control.addEventListener("change", render);
      }
      reset.addEventListener("click", () => {
        search.value = "";
        outcome.value = "";
        framework.value = "";
        mappedOnly.checked = true;
        render();
      });

      render();
      root.setAttribute("aria-busy", "false");
    } catch (error) {
      banner.textContent =
        error instanceof Error
          ? `Matrix unavailable: ${error.message}`
          : "Matrix unavailable: the Mission package could not be validated";
      banner.dataset.state = "error";
      root.setAttribute("aria-busy", "false");
    }
  };

  void initialize();
})();
