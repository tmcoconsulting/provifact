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
  const dialog = root.querySelector("[data-matrix-dialog]");
  const detail = root.querySelector("[data-matrix-detail]");

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
    !(empty instanceof HTMLElement) ||
    !(dialog instanceof HTMLDialogElement) ||
    !(detail instanceof HTMLElement)
  )
    return;

  const frameworkColumns = [
    { key: "cis_benchmark", label: "CIS Level 1" },
    { key: "stig", label: "STIG" },
    { key: "nist_800_171r3", label: "NIST SP 800-171" },
    { key: "nist_800_53r5", label: "NIST SP 800-53" },
    { key: "cmmc", label: "CMMC" },
  ];
  const create = (tagName, className = "", text = "") => {
    const node = document.createElement(tagName);
    if (className) node.className = className;
    if (text !== "") node.textContent = String(text);
    return node;
  };
  const isRecord = (value) =>
    value !== null && typeof value === "object" && !Array.isArray(value);
  const formatValue = (value) => {
    if (typeof value === "boolean") return value ? "Enabled" : "Disabled";
    if (typeof value === "string" || typeof value === "number")
      return String(value);
    if (value === null || value === undefined) return "Not available";
    if (Array.isArray(value)) return value.map(formatValue).join(", ");
    return JSON.stringify(value);
  };
  const frameworkIds = (requirement, key) => {
    if (!isRecord(requirement.mappings)) return [];
    const values = requirement.mappings[key];
    return Array.isArray(values)
      ? values.filter((value) => typeof value === "string")
      : [];
  };
  const hasMappings = (requirement) =>
    frameworkColumns.some(({ key }) => frameworkIds(requirement, key).length);
  const hasReviewedProviderMapping = (requirement) =>
    requirement.mapping_review_status === "reviewed" &&
    Array.isArray(requirement.provider_definition_ids) &&
    requirement.provider_definition_ids.length > 0;
  const stateClass = (value) => {
    if (value === "Aligned") return "matrix-state-aligned";
    if (value === "Conflicting policy") return "matrix-state-conflict";
    if (value === "Missing from tenant") return "matrix-state-missing";
    if (value === "Unsupported by provider") return "matrix-state-unsupported";
    if (
      value === "Human review required" ||
      value === "Collection gap" ||
      value === "Provider mapping not reviewed" ||
      value === "Unsupported value shape"
    )
      return "matrix-state-review";
    return "matrix-state-drift";
  };
  const state = (label) => {
    const badge = create("span", `matrix-state ${stateClass(label)}`, label);
    badge.title = "Technical evidence state; not a framework verdict";
    return badge;
  };

  const buildAction = (requirement) => {
    const key = requirement.setting_key || requirement.rule_id;
    const target = formatValue(requirement.expected_value);
    const observed = formatValue(requirement.observed_value);
    switch (requirement.outcome) {
      case "Aligned":
        return `No value change indicated. Retain ${key} at ${target}; review scope and operating evidence.`;
      case "Value drift":
        return `Human review in Intune: ${key} is ${observed}; the approved target is ${target}. Re-collect after any change.`;
      case "Assignment drift":
        return `Review intended assignments and exclusions for ${key}; re-collect after any human change.`;
      case "Conflicting policy":
        return `Review overlapping policy sources and effective precedence for ${key}; Provifact will not choose or apply a policy.`;
      case "Missing from tenant":
        return `Confirm every reviewed exact provider alias is absent before treating ${key} as missing.`;
      case "Collection gap":
        return "Restore the approved read-only evidence source or provide alternate evidence before evaluating this setting.";
      case "Unsupported value shape":
        return "Review the collected value shape and add a deterministic parser before evaluating it.";
      case "Provider mapping not reviewed":
      case "Unsupported by provider":
        return "Review and approve an exact provider definition mapping before this rule enters technical alignment.";
      default:
        return "Human review is required; Provifact has no Intune write capability.";
    }
  };

  const addDetail = (list, label, value, code = false) => {
    list.append(
      create("dt", "", label),
      (() => {
        const item = create("dd");
        item.append(create(code ? "code" : "span", "", formatValue(value)));
        return item;
      })(),
    );
  };

  const openDetail = (row) => {
    const { requirement, finding, resources } = row;
    detail.replaceChildren();
    const heading = create("h2", "", requirement.title);
    heading.id = "matrix-dialog-title";
    const label = create(
      "p",
      "matrix-dialog-status",
      `${requirement.outcome} · ${requirement.severity} severity`,
    );
    const list = create("dl", "matrix-detail-list");
    addDetail(
      list,
      "Requirement",
      `${requirement.rule_id} — ${requirement.title}`,
    );
    addDetail(
      list,
      "Canonical setting",
      requirement.setting_key || "Not evaluated",
      true,
    );
    addDetail(
      list,
      "Exact provider definition ID",
      requirement.provider_definition_ids || [],
      true,
    );
    addDetail(
      list,
      "Matched provider definition ID",
      requirement.matched_provider_definition_ids || [],
      true,
    );
    addDetail(
      list,
      "Mapping review status",
      requirement.mapping_review_status || "Not reviewed",
    );
    addDetail(
      list,
      "Mapping registry",
      requirement.provider_mapping_registry_version || "Not available",
      true,
    );
    addDetail(
      list,
      "Public-safe parent policy",
      requirement.parent_resource_refs || [],
      true,
    );
    addDetail(list, "Observed value", requirement.observed_value, true);
    addDetail(list, "Approved target", requirement.expected_value, true);
    addDetail(
      list,
      "Assignment state",
      requirement.assignment_summary || "Not available",
    );
    for (const { key, label: frameworkLabel } of frameworkColumns)
      addDetail(list, frameworkLabel, frameworkIds(requirement, key), true);
    addDetail(
      list,
      "Evidence IDs",
      requirement.source_evidence_ids || [],
      true,
    );
    addDetail(list, "Requirement fingerprint", requirement.fingerprint, true);
    if (finding)
      addDetail(list, "Finding fingerprint", finding.fingerprint, true);
    if (resources.length)
      addDetail(
        list,
        "Evidence resources",
        resources.map(
          (resource) => `${resource.title} · ${resource.source_api_version}`,
        ),
      );
    const action = create("section", "matrix-detail-action");
    action.append(
      create("h3", "", "Read-only operator guidance"),
      create("p", "", buildAction(requirement)),
      create("h3", "", "Limitations"),
      create(
        "p",
        "",
        "This setting-level evidence does not establish organizational compliance or control satisfaction. Provifact cannot write, assign, or remediate Intune. Human review is required.",
      ),
    );
    const ask = create(
      "button",
      "md-button md-button--primary",
      "Ask Provifact Copilot about this setting",
    );
    ask.type = "button";
    ask.addEventListener("click", () => {
      dialog.close();
      window.dispatchEvent(
        new CustomEvent("provifact:select-evidence", {
          detail: {
            evidenceId: requirement.requirement_id,
            question:
              "Explain this setting evidence and the read-only Intune review step.",
          },
        }),
      );
    });
    detail.append(heading, label, list, action, ask);
    dialog.showModal();
  };

  const validateMission = (value) => {
    if (
      !isRecord(value) ||
      value.schema_version !== "2.1.0" ||
      !/^mission-[0-9a-f]{24}$/.test(value.snapshot_id) ||
      !isRecord(value.collection) ||
      typeof value.collection.collected_at_utc !== "string" ||
      !isRecord(value.baseline) ||
      !Array.isArray(value.requirements) ||
      !Array.isArray(value.findings) ||
      !Array.isArray(value.resources)
    )
      throw new Error("Mission package failed the settings contract");
    return value;
  };

  const initialize = async () => {
    try {
      const url = new URL(
        "/assets/data/mission-control.json",
        window.location.origin,
      );
      const requestedSnapshot = new URL(window.location.href).searchParams.get(
        "snapshot",
      );
      if (requestedSnapshot && /^mission-[0-9a-f]{24}$/.test(requestedSnapshot))
        url.searchParams.set("snapshot", requestedSnapshot);
      const response = await fetch(url, {
        credentials: "same-origin",
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (
        !response.ok ||
        !response.headers.get("Content-Type")?.includes("application/json")
      )
        throw new Error("Mission package could not be loaded");
      const mission = validateMission(await response.json());
      const findings = new Map(
        mission.findings
          .filter(
            (item) => isRecord(item) && typeof item.requirement_id === "string",
          )
          .map((item) => [item.requirement_id, item]),
      );
      const resources = new Map(
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
        .map((requirement) => ({
          requirement,
          finding: findings.get(requirement.requirement_id),
          resources: (requirement.source_evidence_ids || [])
            .map((id) => resources.get(id))
            .filter(Boolean),
        }));

      for (const value of [
        ...new Set(rows.map(({ requirement }) => requirement.outcome)),
      ].sort()) {
        const option = create("option", "", value);
        option.value = value;
        outcome.append(option);
      }
      const mapped = rows.filter(({ requirement }) =>
        hasReviewedProviderMapping(requirement),
      );
      const evaluated = mapped.filter(
        ({ requirement }) => requirement.evaluation_included === true,
      );
      const aligned = evaluated.filter(
        ({ requirement }) => requirement.outcome === "Aligned",
      ).length;
      const summaryValues = [
        [rows.length, "Baseline rules"],
        [mapped.length, "Reviewed mappings"],
        [evaluated.length, "Evaluated settings"],
        [aligned, "Aligned"],
        [evaluated.length - aligned, "Require review"],
      ];
      summary.replaceChildren();
      for (const [value, label] of summaryValues) {
        const card = create("article", "matrix-summary-card");
        card.append(create("strong", "", value), create("span", "", label));
        summary.append(card);
      }
      banner.textContent = `${mission.data_mode} · ${mission.baseline.name} · collected ${new Date(mission.collection.collected_at_utc).toLocaleString()} · public-safe evidence only`;
      banner.dataset.state = mission.data_mode.startsWith("LIVE")
        ? "live"
        : "fixture";

      const render = () => {
        const query = search.value.trim().toLowerCase();
        const selectedOutcome = outcome.value;
        const selectedFramework = framework.value;
        const filtered = rows.filter(({ requirement, resources: evidence }) => {
          if (mappedOnly.checked && !hasReviewedProviderMapping(requirement))
            return false;
          if (selectedOutcome && requirement.outcome !== selectedOutcome)
            return false;
          if (selectedFramework === "cis_lvl2") return false;
          if (
            selectedFramework &&
            !frameworkIds(requirement, selectedFramework).length
          )
            return false;
          if (!query) return true;
          return [
            requirement.title,
            requirement.rule_id,
            requirement.setting_key,
            requirement.outcome,
            formatValue(requirement.observed_value),
            formatValue(requirement.expected_value),
            buildAction(requirement),
            ...(requirement.provider_definition_ids || []),
            ...(requirement.source_evidence_ids || []),
            ...frameworkColumns.flatMap(({ key }) =>
              frameworkIds(requirement, key),
            ),
            ...evidence.flatMap((item) => [item.title, item.resource_family]),
          ]
            .filter((value) => typeof value === "string")
            .join(" ")
            .toLowerCase()
            .includes(query);
        });

        const head = table.tHead || table.createTHead();
        head.replaceChildren();
        const header = head.insertRow();
        for (const label of [
          "Setting",
          "Observed → target",
          "State",
          "Assignment",
          "Frameworks",
          "Action",
        ])
          header.append(create("th", "", label));
        const body = table.tBodies[0] || table.createTBody();
        body.replaceChildren();
        for (const row of filtered) {
          const requirement = row.requirement;
          const tr = body.insertRow();
          tr.id = requirement.requirement_id;
          const setting = create("td");
          const open = create(
            "button",
            "matrix-setting-button",
            requirement.title,
          );
          open.type = "button";
          open.addEventListener("click", () => openDetail(row));
          setting.append(
            open,
            create(
              "code",
              "matrix-setting-meta",
              requirement.setting_key || requirement.rule_id,
            ),
            create(
              "span",
              "matrix-setting-meta",
              `${requirement.section || "Unsectioned"} · ${requirement.rule_id}`,
            ),
          );
          const observedTarget = create("td", "matrix-observed-target");
          observedTarget.append(
            create("code", "", formatValue(requirement.observed_value)),
            create("span", "", "→"),
            create("code", "", formatValue(requirement.expected_value)),
          );
          const stateCell = create("td");
          stateCell.append(state(requirement.outcome));
          const frameworks = create("td", "matrix-framework-chips");
          for (const { key, label } of frameworkColumns) {
            const ids = frameworkIds(requirement, key);
            if (ids.length)
              frameworks.append(create("span", "", `${label} ${ids.length}`));
          }
          if (!frameworks.childElementCount)
            frameworks.append(
              create("span", "matrix-muted", "No reviewed cross-reference"),
            );
          const actionCell = create("td");
          const action = create(
            "button",
            "matrix-action-button",
            "Review details",
          );
          action.type = "button";
          action.addEventListener("click", () => openDetail(row));
          actionCell.append(action);
          tr.append(
            setting,
            observedTarget,
            stateCell,
            create("td", "", requirement.assignment_summary || "Not available"),
            frameworks,
            actionCell,
          );
        }
        count.textContent = `${filtered.length} of ${rows.length} baseline requirements shown`;
        empty.hidden = filtered.length !== 0;
        if (!filtered.length)
          empty.textContent =
            selectedFramework === "cis_lvl2"
              ? "CIS Level 2 is not loaded. Provifact does not infer it from Level 1 or a framework cross-reference."
              : "No settings match the selected filters.";
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
      const selected = new URL(window.location.href).searchParams.get(
        "selected",
      );
      const selectedRow = rows.find(
        ({ requirement }) => requirement.requirement_id === selected,
      );
      if (selectedRow) openDetail(selectedRow);
    } catch (error) {
      banner.textContent = `Matrix unavailable: ${error instanceof Error ? error.message : "the Mission package could not be validated"}`;
      banner.dataset.state = "error";
      root.setAttribute("aria-busy", "false");
    }
  };

  void initialize();
})();
