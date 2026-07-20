(() => {
  "use strict";

  const root = document.querySelector("[data-mission-control]");
  if (!(root instanceof HTMLElement)) return;

  const select = (selector) => root.querySelector(selector);
  const all = (selector) => Array.from(root.querySelectorAll(selector));
  const create = (name, className = "", value = "") => {
    const node = document.createElement(name);
    if (className) node.className = className;
    if (value !== "") node.textContent = String(value);
    return node;
  };
  const isRecord = (value) =>
    value !== null && typeof value === "object" && !Array.isArray(value);
  const formatValue = (value) => {
    if (Array.isArray(value)) return value.map(formatValue).join(", ");
    if (value === null || value === undefined) return "Not available";
    if (isRecord(value)) return JSON.stringify(value);
    if (typeof value === "boolean") return value ? "Enabled" : "Disabled";
    return String(value);
  };
  const shortHash = (value) =>
    typeof value === "string" && value.length > 22
      ? `${value.slice(0, 20)}…`
      : formatValue(value);
  const titleCase = (value) =>
    String(value)
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  const text = (selector, value) => {
    const node = select(selector);
    if (node instanceof HTMLElement) node.textContent = String(value);
  };
  const missionUrl = () => {
    const url = new URL(
      "/assets/data/mission-control.json",
      window.location.origin,
    );
    const snapshot = new URL(window.location.href).searchParams.get("snapshot");
    if (snapshot && /^mission-[0-9a-f]{24}$/.test(snapshot))
      url.searchParams.set("snapshot", snapshot);
    return url;
  };

  let mission = null;

  const validateMission = (value) => {
    const modes = [
      "SYNTHETIC DEMO DATA",
      "LIVE SANITIZED TENANT DATA",
      "DEGRADED OR STALE DATA",
    ];
    if (
      !isRecord(value) ||
      value.schema_version !== "2.1.0" ||
      !modes.includes(value.data_mode) ||
      !/^mission-[0-9a-f]{24}$/.test(value.snapshot_id) ||
      !/^sha256:[0-9a-f]{64}$/.test(value.content_fingerprint) ||
      !isRecord(value.collection) ||
      !isRecord(value.baseline) ||
      !isRecord(value.metrics) ||
      !isRecord(value.devices) ||
      !isRecord(value.changes) ||
      !isRecord(value.framework_coverage) ||
      !isRecord(value.privacy) ||
      !Array.isArray(value.requirements) ||
      !Array.isArray(value.findings) ||
      !Array.isArray(value.resources) ||
      !Array.isArray(value.unmapped_objects) ||
      !Array.isArray(value.collection_gaps)
    ) {
      throw new Error("Mission package failed the dashboard contract");
    }
    const prohibited = new Set([
      "access_token",
      "api_key",
      "authorization",
      "device_name",
      "hostname",
      "managed_device_id",
      "private_display_name",
      "serial_number",
      "source_object_id",
      "user_principal_name",
    ]);
    const walk = (item) => {
      if (Array.isArray(item)) return item.forEach(walk);
      if (!isRecord(item)) return;
      for (const [key, nested] of Object.entries(item)) {
        if (prohibited.has(key.toLowerCase()))
          throw new Error("Mission package contains a prohibited field");
        walk(nested);
      }
    };
    walk(value);
    return value;
  };

  const addDetail = (list, label, value, code = false) => {
    const term = create("dt", "", label);
    const detail = create("dd");
    detail.append(create(code ? "code" : "span", "", formatValue(value)));
    list.append(term, detail);
  };

  const renderDefinitionList = (container, entries) => {
    if (!(container instanceof HTMLElement)) return;
    container.replaceChildren();
    for (const [label, value, code = false] of entries)
      addDetail(container, label, value, code);
  };

  const metricCard = (label, value, detail, tone = "neutral") => {
    const card = create("article", `mission-metric mission-tone-${tone}`);
    card.append(
      create("span", "mission-metric-label", label),
      create("strong", "mission-metric-value", value),
      create("span", "mission-metric-detail", detail),
    );
    return card;
  };

  const findingForRule = (identifier) =>
    mission.findings.find(
      (finding) =>
        finding.rule_id === identifier || finding.finding_id === identifier,
    );
  const requirementForRule = (identifier) =>
    mission.requirements.find(
      (requirement) =>
        requirement.rule_id === identifier ||
        requirement.requirement_id === identifier,
    );

  const deterministicGuidance = (finding) => {
    const key = finding.setting_key || finding.rule_id;
    const target = formatValue(finding.expected_value);
    const observed = formatValue(finding.observed_value);
    switch (finding.drift_type) {
      case "Value drift":
        return `Review ${key} in the approved Intune policy: observed ${observed}, approved target ${target}. If a human changes it, re-collect before calling it resolved.`;
      case "Assignment drift":
        return `Review intended scope and exclusions for ${key}; retain ${target}, then re-collect assignment evidence after any human change.`;
      case "Conflicting policy":
        return `Review overlapping policy sources for ${key}. Resolve precedence manually, then re-collect the effective value.`;
      case "Missing from tenant":
        return `Confirm every reviewed exact provider alias is absent before a human creates or assigns an approved policy for ${key}.`;
      default:
        return (
          finding.remediation_guidance ||
          "Human review is required; Provifact cannot change Intune."
        );
    }
  };

  const openFinding = (finding) => {
    const dialog = select("[data-finding-dialog]");
    const detail = select("[data-finding-detail]");
    if (
      !(dialog instanceof HTMLDialogElement) ||
      !(detail instanceof HTMLElement)
    )
      return;
    detail.replaceChildren();
    const heading = create("h2", "", finding.title);
    heading.id = "finding-dialog-title";
    const status = create(
      "p",
      "mission-dialog-status",
      `${finding.drift_type} · ${finding.severity} severity`,
    );
    const list = create("dl", "mission-detail-list");
    const requirement = requirementForRule(
      finding.requirement_id || finding.rule_id,
    );
    addDetail(list, "Requirement", `${finding.rule_id} — ${finding.title}`);
    addDetail(list, "Canonical setting", finding.setting_key, true);
    addDetail(
      list,
      "Exact provider definitions",
      finding.provider_definition_ids || [],
      true,
    );
    addDetail(
      list,
      "Matched provider definitions",
      finding.matched_provider_definition_ids || [],
      true,
    );
    addDetail(
      list,
      "Mapping review",
      finding.mapping_review_status || "Not published",
    );
    addDetail(
      list,
      "Mapping registry",
      finding.provider_mapping_registry_version || "Not published",
      true,
    );
    addDetail(
      list,
      "Public-safe parent policy",
      (finding.parent_resource_refs || []).join(", ") ||
        "No linked parent reference",
      true,
    );
    addDetail(list, "Observed", finding.observed_value, true);
    addDetail(list, "Approved target", finding.expected_value, true);
    addDetail(list, "Assignment", finding.assignment_summary);
    addDetail(
      list,
      "Framework cross-references",
      finding.mapped_controls || {},
    );
    addDetail(
      list,
      "Evidence IDs",
      finding.source_evidence_ids || requirement?.source_evidence_ids || [],
      true,
    );
    addDetail(list, "Finding fingerprint", finding.fingerprint, true);
    addDetail(
      list,
      "Baseline fingerprint",
      finding.baseline_rule_fingerprint,
      true,
    );

    const guidance = create("section", "mission-dialog-guidance");
    guidance.append(
      create("h3", "", "Read-only operator guidance"),
      create("p", "", deterministicGuidance(finding)),
    );
    const limitations = create("ul");
    for (const limitation of finding.limitations || [])
      limitations.append(create("li", "", limitation));
    guidance.append(create("h3", "", "Limitations"), limitations);
    const ask = create(
      "button",
      "md-button md-button--primary",
      "Ask Provifact Copilot about this finding",
    );
    ask.type = "button";
    ask.addEventListener("click", () => {
      dialog.close();
      window.dispatchEvent(
        new CustomEvent("provifact:select-evidence", {
          detail: {
            evidenceId: finding.finding_id,
            question:
              "Which evidence supports this finding and what should I review in Intune?",
          },
        }),
      );
    });
    detail.append(heading, status, list, guidance, ask);
    dialog.showModal();
  };

  const renderOverview = () => {
    const metrics = mission.metrics;
    const container = select("[data-mission-metrics]");
    if (container instanceof HTMLElement) {
      container.replaceChildren(
        metricCard(
          "Findings requiring review",
          metrics.drifted_requirements,
          `${metrics.high_severity_drift} high severity`,
          metrics.drifted_requirements ? "danger" : "good",
        ),
        metricCard(
          "New drift",
          mission.changes.new_drift.length,
          "Since the previous sanitized collection",
          mission.changes.new_drift.length ? "warning" : "good",
        ),
        metricCard(
          "Resolved",
          mission.changes.resolved_drift.length,
          "Requires later collected evidence",
          "good",
        ),
        metricCard(
          "Collection gaps",
          metrics.collection_gaps,
          "Additional evidence required",
          metrics.collection_gaps ? "warning" : "good",
        ),
        metricCard(
          "Evaluated settings",
          metrics.alignment_denominator,
          `${metrics.aligned_requirements} currently aligned`,
        ),
      );
    }
    text(
      "[data-mission-denominator]",
      metrics.alignment_denominator_explanation,
    );
    text("[data-mission-title]", mission.baseline.name);
    text(
      "[data-mission-subtitle]",
      `Collected ${mission.collection.collected_at_utc} · ${mission.collection.provider} ${mission.collection.provider_version}`,
    );
    text("[data-mission-mode]", mission.data_mode);
    text("[data-priority-count]", `${mission.findings.length} open`);

    const list = select("[data-attention-list]");
    if (list instanceof HTMLElement) {
      list.replaceChildren();
      const ordered = [...mission.findings].sort(
        (left, right) =>
          (({ high: 3, medium: 2, low: 1 })[right.severity] || 0) -
            ({ high: 3, medium: 2, low: 1 }[left.severity] || 0) ||
          left.title.localeCompare(right.title),
      );
      if (!ordered.length)
        list.append(
          create(
            "p",
            "mission-empty",
            "No current deterministic drift finding is published.",
          ),
        );
      for (const finding of ordered.slice(0, 5)) {
        const card = create("article", "mission-attention-card");
        const button = create(
          "button",
          "mission-attention-button",
          finding.title,
        );
        button.type = "button";
        button.addEventListener("click", () => openFinding(finding));
        card.append(
          create(
            "span",
            `mission-severity mission-severity-${finding.severity}`,
            finding.severity,
          ),
          button,
          create(
            "span",
            "",
            `${finding.drift_type} · ${formatValue(finding.observed_value)} → ${formatValue(finding.expected_value)}`,
          ),
          create("small", "", finding.assignment_summary),
        );
        list.append(card);
      }
    }

    renderDefinitionList(select("[data-baseline-summary]"), [
      ["Benchmark", mission.baseline.benchmark],
      ["Pinned version", mission.baseline.benchmark_version],
      [
        "Approved",
        `${mission.baseline.approval_date} · ${mission.baseline.approver}`,
      ],
      ["Inventory", `${mission.baseline.rule_count} rules`],
      ["Extracted hash", mission.baseline.extracted_baseline_sha256, true],
    ]);
  };

  const actionForRequirement = (requirement) => {
    switch (requirement.outcome) {
      case "Aligned":
        return "Monitor; no tenant change inferred.";
      case "Collection gap":
        return "Repair collection or parser coverage before changing Intune.";
      case "Missing from tenant":
        return "Confirm absence, then use the approved human change process.";
      case "Provider mapping not reviewed":
        return "Review an exact provider definition before evaluation.";
      case "Unsupported value shape":
        return "Review the provider shape; do not infer a value.";
      default:
        return "Human review in Intune; re-collect after any approved change.";
    }
  };

  const renderPostureRows = (lens) => {
    const body = select("[data-posture-rows]");
    if (!(body instanceof HTMLElement)) return;
    const requirements = mission.requirements.filter(
      (requirement) =>
        requirement.evaluation_included === true &&
        (lens !== "stig" ||
          (Array.isArray(requirement.mappings?.stig) &&
            requirement.mappings.stig.length > 0)),
    );
    body.replaceChildren();
    for (const requirement of requirements) {
      const row = document.createElement("tr");
      const objective = create("td");
      objective.append(
        create("strong", "", requirement.title),
        create(
          "small",
          "",
          lens === "stig"
            ? `STIG ${requirement.mappings.stig.join(", ")}`
            : requirement.setting_key,
        ),
      );
      const state = create(
        "span",
        `mission-state mission-state-${String(requirement.outcome)
          .toLowerCase()
          .replaceAll(" ", "-")}`,
        requirement.outcome,
      );
      const evidenceCount = Array.isArray(requirement.source_evidence_ids)
        ? requirement.source_evidence_ids.length
        : 0;
      const evidence = create("td");
      evidence.append(
        create(
          "strong",
          "",
          evidenceCount
            ? `${evidenceCount} linked record(s)`
            : "No linked observation",
        ),
        create(
          "small",
          "",
          `${requirement.mapping_review_status} mapping · ${requirement.assignment_summary}`,
        ),
      );
      const action = create("td", "", actionForRequirement(requirement));
      const finding = findingForRule(requirement.rule_id);
      if (finding) {
        const review = create("button", "mission-row-action", "Open evidence");
        review.type = "button";
        review.addEventListener("click", () => openFinding(finding));
        action.append(review);
      }
      const stateCell = create("td");
      stateCell.append(state);
      row.append(
        objective,
        create(
          "td",
          "mission-observed-target",
          formatValue(requirement.expected_value),
        ),
        create(
          "td",
          "mission-observed-target",
          formatValue(requirement.observed_value),
        ),
        stateCell,
        evidence,
        action,
      );
      body.append(row);
    }
    if (!requirements.length) {
      const row = document.createElement("tr");
      const cell = create(
        "td",
        "mission-empty",
        "No reviewed settings in the current package carry this technical cross-reference.",
      );
      cell.colSpan = 6;
      row.append(cell);
      body.append(row);
    }
  };

  const renderBaselineConsole = () => {
    const selector = select("[data-baseline-view]");
    const readout = select("[data-baseline-readout]");
    const next = select("[data-baseline-next]");
    if (
      !(selector instanceof HTMLSelectElement) ||
      !(readout instanceof HTMLElement) ||
      !(next instanceof HTMLElement)
    )
      return;
    const render = () => {
      const stig = selector.value === "stig";
      const framework = mission.framework_coverage.STIG || {
        identifiers: [],
        technical_evidence_identifier_count: 0,
      };
      const evaluated = mission.requirements.filter(
        (requirement) => requirement.evaluation_included === true,
      );
      const stigEvaluated = evaluated.filter(
        (requirement) =>
          Array.isArray(requirement.mappings?.stig) &&
          requirement.mappings.stig.length,
      );
      const aligned = (stig ? stigEvaluated : evaluated).filter(
        (requirement) => requirement.outcome === "Aligned",
      ).length;
      const scoped = stig ? stigEvaluated : evaluated;
      readout.replaceChildren(
        metricCard(
          stig ? "STIG-linked evaluated settings" : "Pinned baseline inventory",
          stig ? stigEvaluated.length : mission.baseline.rule_count,
          stig
            ? `${framework.technical_evidence_identifier_count} technical identifier(s)`
            : mission.baseline.benchmark_version,
        ),
        metricCard(
          "Deterministically evaluated",
          scoped.length,
          stig ? "Cross-reference lens only" : "Exact reviewed Intune mappings",
        ),
        metricCard(
          "Matches desired state",
          aligned,
          `${scoped.length - aligned} differ, are missing, or need evidence`,
          aligned === scoped.length ? "good" : "warning",
        ),
        metricCard(
          stig ? "STIG baseline status" : "Authority",
          stig ? "NOT LOADED" : "APPROVED",
          stig
            ? "No STIG assessment or score is produced"
            : mission.baseline.approval_status,
          stig ? "warning" : "good",
        ),
      );
      next.replaceChildren();
      if (stig) {
        next.append(
          create("strong", "", "What switching to STIG would require"),
          create(
            "p",
            "",
            "Provifact can reuse the same observations, but a real STIG evaluation requires a pinned authoritative STIG release, an approved desired-state profile, reviewed requirement-to-setting mappings, exact Intune definition mappings, and human acceptance of the new scope. The current view is only a technical cross-reference.",
          ),
          create(
            "p",
            "",
            `Current evidence references: ${Array.isArray(framework.identifiers) && framework.identifiers.length ? framework.identifiers.join(", ") : "none published"}.`,
          ),
        );
      } else {
        next.append(
          create("strong", "", mission.baseline.benchmark),
          create(
            "p",
            "",
            `${mission.baseline.rule_count} rules are inventoried; ${mission.metrics.alignment_denominator} currently have reviewed exact provider mappings and sufficient support for deterministic comparison. Open the baseline matrix to see every not-yet-evaluated rule.`,
          ),
        );
      }
      renderPostureRows(selector.value);
    };
    selector.addEventListener("change", render);
    render();
  };

  const renderCollectionPipeline = () => {
    const container = select("[data-collection-pipeline]");
    if (!(container instanceof HTMLElement)) return;
    const statuses = mission.collection.endpoint_statuses;
    const root = statuses.find((item) => item.key === "settings-catalog");
    const settingCount = mission.resources.filter(
      (item) => item.resource_family === "settings_catalog_settings",
    ).length;
    const assignmentCount = mission.resources.filter(
      (item) => item.resource_family === "settings_catalog_assignments",
    ).length;
    const steps = [
      [
        "01",
        "Git desired state",
        `${mission.baseline.rule_count} pinned rules`,
        "complete",
      ],
      [
        "02",
        "Settings Catalog",
        `${root?.record_count || 0} policy records`,
        root?.status || "unknown",
      ],
      [
        "03",
        "Normalized evidence",
        `${settingCount} settings · ${assignmentCount} assignments`,
        "complete",
      ],
      [
        "04",
        "Deterministic engine",
        `${mission.metrics.alignment_denominator} reviewed joins`,
        "complete",
      ],
      [
        "05",
        "Publication gate",
        `${mission.collection_gaps.length} collection gap(s)`,
        mission.collection_gaps.length ? "warning" : "complete",
      ],
    ];
    container.replaceChildren();
    for (const [index, label, detail, state] of steps) {
      const step = create(
        "div",
        `mission-pipeline-step mission-pipeline-${state}`,
      );
      step.append(
        create("span", "mission-pipeline-index", index),
        create("strong", "", label),
        create("small", "", detail),
      );
      container.append(step);
    }
  };

  const renderChanges = () => {
    const renderItems = (container, identifiers, emptyMessage) => {
      if (!(container instanceof HTMLElement)) return;
      container.replaceChildren();
      if (!identifiers.length) container.append(create("p", "", emptyMessage));
      for (const identifier of identifiers) {
        const finding = findingForRule(identifier);
        const requirement = requirementForRule(identifier);
        const item = create(
          "a",
          "mission-change-link",
          finding?.title || requirement?.title || identifier,
        );
        item.href = finding
          ? `#${finding.finding_id}`
          : requirement
            ? `../settings-matrix/?selected=${encodeURIComponent(requirement.requirement_id)}#settings-matrix`
            : "#evidence";
        if (finding)
          item.addEventListener("click", (event) => {
            event.preventDefault();
            openFinding(finding);
          });
        container.append(item);
      }
    };
    renderItems(
      select("[data-resolved-changes]"),
      mission.changes.resolved_drift,
      "No finding is recorded as resolved in this comparison.",
    );
    renderItems(
      select("[data-new-changes]"),
      mission.changes.new_drift,
      "No new drift is recorded in this comparison.",
    );
    text(
      "[data-change-count]",
      `${mission.changes.changed_requirements.length} changed`,
    );
    renderDefinitionList(select("[data-change-summary]"), [
      [
        "Previous snapshot",
        mission.changes.previous_snapshot_id || "No prior snapshot",
      ],
      [
        "Previous collection",
        mission.changes.previous_collection_timestamp_utc || "Not available",
      ],
      [
        "Current collection",
        mission.changes.current_collection_timestamp_utc ||
          mission.collection.collected_at_utc,
      ],
      [
        "Alignment change",
        mission.changes.alignment_change_points === null
          ? "Not calculated"
          : `${mission.changes.alignment_change_points} points`,
      ],
      [
        "Unchanged",
        `${(mission.changes.unchanged_requirements || []).length} evaluated requirements`,
      ],
    ]);
  };

  const addOptions = (selector, values) => {
    const node = select(selector);
    if (!(node instanceof HTMLSelectElement)) return;
    for (const value of [...new Set(values)].sort()) {
      const option = create("option", "", value);
      option.value = value;
      node.append(option);
    }
  };

  const renderFindings = () => {
    addOptions(
      "[data-filter-platform]",
      mission.findings.map((item) => item.platform),
    );
    addOptions(
      "[data-filter-drift]",
      mission.findings.map((item) => item.drift_type),
    );
    addOptions(
      "[data-filter-severity]",
      mission.findings.map((item) => item.severity),
    );
    addOptions(
      "[data-filter-category]",
      mission.findings.map((item) =>
        item.setting_key.split(".").slice(0, -1).join("."),
      ),
    );
    const render = () => {
      const filters = {
        platform: select("[data-filter-platform]")?.value || "",
        drift: select("[data-filter-drift]")?.value || "",
        severity: select("[data-filter-severity]")?.value || "",
        category: select("[data-filter-category]")?.value || "",
      };
      const filtered = mission.findings.filter(
        (item) =>
          (!filters.platform || item.platform === filters.platform) &&
          (!filters.drift || item.drift_type === filters.drift) &&
          (!filters.severity || item.severity === filters.severity) &&
          (!filters.category || item.setting_key.startsWith(filters.category)),
      );
      const body = select("[data-finding-rows]");
      if (!(body instanceof HTMLElement)) return;
      body.replaceChildren();
      for (const finding of filtered) {
        const row = document.createElement("tr");
        row.id = finding.finding_id;
        const setting = create("td");
        const button = create(
          "button",
          "mission-finding-button",
          finding.title,
        );
        button.type = "button";
        button.addEventListener("click", () => openFinding(finding));
        setting.append(button, create("small", "", finding.rule_id));
        row.append(
          setting,
          create("td", "", finding.drift_type),
          create(
            "td",
            `mission-severity mission-severity-${finding.severity}`,
            finding.severity,
          ),
          create(
            "td",
            "mission-observed-target",
            `${formatValue(finding.observed_value)} → ${formatValue(finding.expected_value)}`,
          ),
          create("td", "", finding.assignment_summary),
        );
        body.append(row);
      }
      text(
        "[data-finding-count]",
        `${filtered.length} of ${mission.findings.length}`,
      );
      const empty = select("[data-finding-empty]");
      if (empty instanceof HTMLElement) empty.hidden = filtered.length !== 0;
    };
    all(".mission-filters select").forEach((node) =>
      node.addEventListener("change", render),
    );
    select("[data-clear-filters]")?.addEventListener("click", () => {
      all(".mission-filters select").forEach((node) => {
        if (node instanceof HTMLSelectElement) node.value = "";
      });
      render();
    });
    render();
  };

  const renderPosture = () => {
    const devices = select("[data-device-summary]");
    if (devices instanceof HTMLElement) {
      devices.replaceChildren();
      for (const [label, values] of [
        ["Platform", mission.devices.by_platform],
        ["Compliance", mission.devices.by_compliance_state],
        ["Encryption", mission.devices.by_encryption_state],
        ["Supervision", mission.devices.by_supervision_state],
      ]) {
        const row = create("div", "mission-stat-row");
        row.append(
          create("strong", "", label),
          create(
            "span",
            "",
            Object.entries(values)
              .map(([key, value]) => `${key}: ${value}`)
              .join(" · "),
          ),
        );
        devices.append(row);
      }
    }
    const platform = select("[data-platform-summary]");
    if (platform instanceof HTMLElement) {
      platform.className = "mission-identity-boundary";
      platform.replaceChildren(
        create("h3", "", "Identity boundary"),
        create(
          "p",
          "",
          `${mission.devices.total} managed Apple device(s) are represented only as aggregates.`,
        ),
        create(
          "p",
          "",
          "Device names, serials, users, object IDs, and assignment identities are not public.",
        ),
      );
    }
  };

  const renderCoverage = () => {
    const resourcesByRef = new Map(
      mission.resources
        .filter(
          (item) => isRecord(item) && typeof item.resource_ref === "string",
        )
        .map((item) => [item.resource_ref, item]),
    );
    const groups = new Map();
    for (const resource of mission.unmapped_objects) {
      const reason = resource.evaluation_reason || "Collection or parser gap";
      const items = groups.get(reason) || [];
      items.push(resource);
      groups.set(reason, items);
    }
    const container = select("[data-unevaluated-groups]");
    if (container instanceof HTMLElement) {
      container.replaceChildren();
      for (const [reason, items] of [...groups.entries()].sort(
        ([left], [right]) => String(left).localeCompare(String(right)),
      )) {
        const detail = create("details", "mission-resource-group");
        const actionCount = items.filter(
          (item) =>
            item.action_expected &&
            item.action_expected !== "No action expected",
        ).length;
        detail.append(
          create(
            "summary",
            "",
            `${titleCase(reason)} · ${items.length} resource(s) · ${actionCount ? "review expected" : "no action expected"}`,
          ),
        );
        for (const item of items.slice(0, 20)) {
          const parent = item.parent_resource_ref
            ? resourcesByRef.get(item.parent_resource_ref)
            : null;
          const row = create("div", "mission-resource");
          row.append(
            create("strong", "", parent?.title || item.title),
            create(
              "span",
              "",
              `${item.resource_family} · ${item.action_expected || "Human review required"}`,
            ),
          );
          if (parent)
            row.append(
              create(
                "small",
                "",
                `Nested evidence: ${item.title} · parent ${item.parent_resource_ref}`,
              ),
            );
          detail.append(row);
        }
        container.append(detail);
      }
    }

    const frameworkKeys = {
      "CIS benchmark": "cis_benchmark",
      CMMC: "cmmc",
      "NIST SP 800-171": "nist_800_171r3",
      "NIST SP 800-53": "nist_800_53r5",
      STIG: "stig",
    };
    const body = select("[data-framework-summary]");
    if (body instanceof HTMLElement) {
      body.replaceChildren();
      for (const [name, coverage] of Object.entries(
        mission.framework_coverage,
      )) {
        const key = frameworkKeys[name];
        const evaluated = mission.requirements.filter(
          (requirement) =>
            requirement.evaluation_included === true &&
            key &&
            Array.isArray(requirement.mappings?.[key]) &&
            requirement.mappings[key].length,
        );
        const aligned = evaluated.filter(
          (item) => item.outcome === "Aligned",
        ).length;
        const identifiers = Array.isArray(coverage.identifiers)
          ? coverage.identifiers
          : [];
        const meaning = create("td");
        const detail = create("details");
        detail.append(
          create("summary", "", "Technical references only"),
          create(
            "p",
            "",
            "Not a compliance, certification, or assessor conclusion.",
          ),
          create(
            "code",
            "mission-framework-identifiers",
            identifiers.join(", ") || "No identifiers",
          ),
        );
        meaning.append(detail);
        const row = document.createElement("tr");
        row.append(
          create("td", "", name),
          create("td", "", evaluated.length),
          create("td", "", coverage.technical_evidence_identifier_count),
          create("td", "", aligned),
          create("td", "", evaluated.length - aligned),
          meaning,
        );
        body.append(row);
      }
    }
  };

  const renderEvidence = () => {
    const endpoint = select("[data-endpoint-coverage]");
    if (endpoint instanceof HTMLElement) {
      endpoint.replaceChildren();
      for (const item of mission.collection.endpoint_statuses) {
        const row = create("div", "mission-quality-row");
        row.append(
          create("span", `mission-dot mission-dot-${item.status}`),
          create("strong", "", item.key),
          create(
            "span",
            "",
            `${item.status} · ${item.source_api_version} · ${item.record_count} records`,
          ),
        );
        endpoint.append(row);
      }
    }
    const gaps = select("[data-collection-gaps]");
    if (gaps instanceof HTMLElement) {
      gaps.replaceChildren();
      if (!mission.collection_gaps.length)
        gaps.append(create("p", "", "No collection gaps are recorded."));
      for (const gap of mission.collection_gaps) {
        const row = create("div", "mission-gap");
        row.id = gap.gap_id;
        row.append(
          create("strong", "", titleCase(gap.resource_family)),
          create("span", "", `${gap.reason} · additional evidence required`),
        );
        gaps.append(row);
      }
    }
    renderDefinitionList(select("[data-privacy-summary]"), [
      ["Allowlist validation", mission.privacy.allowlist_validation],
      ["Raw response persisted", mission.privacy.raw_response_persisted],
      ["Identifiers public", mission.privacy.identifiers_public],
      ["Publication policy", mission.privacy.publication_policy_version],
      ["AI egress", mission.privacy.openai_egress_class],
      ["Intune write capability", "None"],
    ]);
  };

  const initialize = async () => {
    try {
      const response = await fetch(missionUrl(), {
        credentials: "same-origin",
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (
        !response.ok ||
        !response.headers.get("Content-Type")?.includes("application/json")
      )
        throw new Error("Mission evidence artifact could not be loaded");
      mission = validateMission(await response.json());
      const collected = Date.parse(mission.collection.collected_at_utc);
      const maximum =
        Number(mission.collection.freshness?.maximum_age_seconds || 0) * 1000;
      const stale =
        !Number.isFinite(collected) ||
        maximum <= 0 ||
        Date.now() - collected > maximum;
      const banner = select("[data-mission-banner]");
      if (banner instanceof HTMLElement) {
        banner.textContent = stale
          ? `DEGRADED / STALE · ${mission.data_mode} package exceeds its declared freshness window`
          : `${mission.data_mode} · fingerprint and publication gates passed · ${mission.snapshot_id}`;
        banner.dataset.state = stale
          ? "stale"
          : mission.data_mode.startsWith("LIVE")
            ? "live"
            : "fixture";
      }
      renderOverview();
      renderBaselineConsole();
      renderCollectionPipeline();
      renderChanges();
      renderFindings();
      renderPosture();
      renderCoverage();
      renderEvidence();
      text("[data-rail-state]", stale ? "DEGRADED" : "VERIFIED");
      const copilot = select("[data-open-copilot]");
      if (copilot instanceof HTMLButtonElement)
        copilot.addEventListener("click", () =>
          window.ProvifactCopilot?.open(),
        );
      root.setAttribute("aria-busy", "false");
      const linked = mission.findings.find(
        (finding) => `#${finding.finding_id}` === window.location.hash,
      );
      if (linked) openFinding(linked);
    } catch (error) {
      const banner = select("[data-mission-banner]");
      if (banner instanceof HTMLElement) {
        banner.textContent = `DEGRADED / STALE · ${error instanceof Error ? error.message : "the current evidence package could not be validated"}`;
        banner.dataset.state = "error";
      }
      root.setAttribute("aria-busy", "false");
    }
  };

  void initialize();
})();
