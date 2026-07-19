(() => {
  "use strict";

  const root = document.querySelector("[data-mission-control]");
  if (!(root instanceof HTMLElement)) return;

  const select = (selector) => root.querySelector(selector);
  const all = (selector) => Array.from(root.querySelectorAll(selector));
  const text = (selector, value) => {
    const node = select(selector);
    if (node instanceof HTMLElement) node.textContent = String(value);
  };
  const element = (name, className, value) => {
    const node = document.createElement(name);
    if (className) node.className = className;
    if (value !== undefined) node.textContent = String(value);
    return node;
  };
  const formatValue = (value) => {
    if (Array.isArray(value)) return value.join(", ");
    if (value === null || value === undefined) return "Not available";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
  };
  const shortHash = (value) =>
    typeof value === "string" && value.length > 20
      ? `${value.slice(0, 18)}…`
      : formatValue(value);

  let mission = null;

  const validateMission = (value) => {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      throw new Error("Mission package is not an object");
    }
    const modes = [
      "SYNTHETIC DEMO DATA",
      "LIVE SANITIZED TENANT DATA",
      "DEGRADED OR STALE DATA",
    ];
    if (
      value.schema_version !== "2.0.0" ||
      !modes.includes(value.data_mode) ||
      !/^mission-[0-9a-f]{24}$/.test(value.snapshot_id) ||
      !/^sha256:[0-9a-f]{64}$/.test(value.content_fingerprint) ||
      !Array.isArray(value.requirements) ||
      !Array.isArray(value.findings) ||
      !Array.isArray(value.resources) ||
      !Array.isArray(value.collection_gaps)
    ) {
      throw new Error("Mission package failed its browser contract");
    }
    const prohibited = new Set([
      "device_name",
      "hostname",
      "user_principal_name",
      "serial_number",
      "managed_device_id",
      "source_object_id",
      "private_display_name",
      "authorization",
      "access_token",
      "api_key",
    ]);
    const walk = (item) => {
      if (Array.isArray(item)) return item.forEach(walk);
      if (!item || typeof item !== "object") return;
      for (const [key, nested] of Object.entries(item)) {
        if (prohibited.has(key.toLowerCase())) {
          throw new Error("Mission package contains a prohibited field");
        }
        walk(nested);
      }
    };
    walk(value);
    return value;
  };

  const renderDefinitionList = (container, entries) => {
    if (!(container instanceof HTMLElement)) return;
    container.replaceChildren();
    for (const [label, value] of entries) {
      const term = element("dt", "", label);
      const detail = element("dd", "", formatValue(value));
      container.append(term, detail);
    }
  };

  const metricCard = (label, value, detail, tone = "neutral") => {
    const card = element("article", `mission-metric mission-tone-${tone}`);
    card.append(
      element("span", "mission-metric-label", label),
      element("strong", "mission-metric-value", value),
      element("span", "mission-metric-detail", detail),
    );
    return card;
  };

  const renderOverview = () => {
    const metrics = mission.metrics;
    const collection = mission.collection;
    const container = select("[data-mission-metrics]");
    if (container instanceof HTMLElement) {
      container.replaceChildren(
        metricCard(
          "Technical alignment",
          `${metrics.alignment_percent}%`,
          `${metrics.aligned_requirements} of ${metrics.alignment_denominator} evaluated`,
          metrics.alignment_percent >= 80 ? "good" : "warning",
        ),
        metricCard(
          "Drifted requirements",
          metrics.drifted_requirements,
          `${metrics.high_severity_drift} high severity`,
          "danger",
        ),
        metricCard(
          "Managed Apple devices",
          mission.devices.total,
          Object.entries(mission.devices.by_platform)
            .map(([key, value]) => `${key} ${value}`)
            .join(" · "),
        ),
        metricCard(
          "Collection gaps",
          metrics.collection_gaps,
          `${metrics.unmapped_objects} unmapped normalized objects`,
          metrics.collection_gaps ? "warning" : "good",
        ),
        metricCard(
          "AI service",
          mission.ai.mode,
          `${mission.ai.model} · ${mission.ai.authoritative ? "authoritative" : "explanatory only"}`,
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
      `Collected ${collection.collected_at_utc} · ${collection.provider} ${collection.provider_version}`,
    );
    text("[data-mission-mode]", mission.data_mode);
    renderDefinitionList(select("[data-baseline-summary]"), [
      ["Benchmark", mission.baseline.benchmark],
      ["Pinned version", mission.baseline.benchmark_version],
      [
        "Approved",
        `${mission.baseline.approval_date} · ${mission.baseline.approver}`,
      ],
      ["Inventory", `${mission.baseline.rule_count} rules`],
      ["Extracted hash", shortHash(mission.baseline.extracted_baseline_sha256)],
    ]);
    const devices = select("[data-device-summary]");
    if (devices instanceof HTMLElement) {
      devices.replaceChildren();
      for (const [label, values] of [
        ["Platform", mission.devices.by_platform],
        ["Compliance", mission.devices.by_compliance_state],
        ["Encryption", mission.devices.by_encryption_state],
        ["Supervision", mission.devices.by_supervision_state],
      ]) {
        const row = element("div", "mission-stat-row");
        row.append(element("strong", "", label));
        row.append(
          element(
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
    const changes = select("[data-change-summary]");
    if (changes instanceof HTMLElement) {
      changes.replaceChildren(
        element(
          "p",
          "mission-change-value",
          mission.changes.alignment_change_points === null
            ? "No prior score"
            : `${mission.changes.alignment_change_points > 0 ? "+" : ""}${mission.changes.alignment_change_points} points`,
        ),
        element(
          "p",
          "",
          `${mission.changes.changed_requirements.length} requirements changed · ${mission.changes.new_drift.length} began drifting · ${mission.changes.resolved_drift.length} resolved`,
        ),
      );
    }
  };

  const options = (selector, values) => {
    const node = select(selector);
    if (!(node instanceof HTMLSelectElement)) return;
    for (const value of [...new Set(values)].sort()) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      node.append(option);
    }
  };

  const renderFindingDetail = (finding) => {
    const dialog = select("[data-finding-dialog]");
    const detail = select("[data-finding-detail]");
    if (
      !(dialog instanceof HTMLDialogElement) ||
      !(detail instanceof HTMLElement)
    )
      return;
    detail.replaceChildren();
    const heading = element("h2", "", finding.title);
    heading.id = "finding-dialog-title";
    detail.append(
      heading,
      element(
        "p",
        "mission-dialog-status",
        `${finding.drift_type} · ${finding.severity}`,
      ),
    );
    const chain = element("ol", "mission-trace-chain");
    const steps = [
      [
        "Pinned baseline",
        `${finding.rule_id} · ${mission.baseline.benchmark_version}`,
      ],
      ["Deterministic mappings", formatValue(finding.mapped_controls)],
      [
        "Desired state",
        `${finding.setting_key} = ${formatValue(finding.expected_value)}`,
      ],
      ["Tenant observation", formatValue(finding.observed_value)],
      ["Assignment scope", finding.assignment_summary],
      [
        "Evidence provenance",
        finding.source_evidence_ids.map(shortHash).join(", ") ||
          "No source observation",
      ],
      ["Finding fingerprint", finding.fingerprint],
      ["Repository provenance", mission.collection.source_git_commit],
    ];
    for (const [label, value] of steps) {
      const item = element("li", "");
      item.append(element("strong", "", label), element("span", "", value));
      chain.append(item);
    }
    detail.append(
      chain,
      element("h3", "", "Human-reviewed next step"),
      element("p", "", finding.remediation_guidance),
    );
    const limits = element("ul", "");
    for (const limitation of finding.limitations)
      limits.append(element("li", "", limitation));
    detail.append(element("h3", "", "Limitations"), limits);
    dialog.showModal();
  };

  const renderFindings = () => {
    options(
      "[data-filter-platform]",
      mission.findings.map((item) => item.platform),
    );
    options(
      "[data-filter-drift]",
      mission.findings.map((item) => item.drift_type),
    );
    options(
      "[data-filter-severity]",
      mission.findings.map((item) => item.severity),
    );
    options(
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
        const titleCell = document.createElement("td");
        const button = element(
          "button",
          "mission-finding-button",
          finding.title,
        );
        button.type = "button";
        button.addEventListener("click", () => renderFindingDetail(finding));
        titleCell.append(button, element("small", "", finding.rule_id));
        row.append(
          titleCell,
          element("td", "", finding.drift_type),
          element(
            "td",
            `mission-severity mission-severity-${finding.severity}`,
            finding.severity,
          ),
          element("td", "", formatValue(finding.expected_value)),
          element("td", "", formatValue(finding.observed_value)),
          element("td", "mission-hash", shortHash(finding.fingerprint)),
        );
        body.append(row);
      }
      text(
        "[data-finding-count]",
        `${filtered.length} of ${mission.findings.length} findings`,
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

  const renderCoverage = () => {
    const platformContainer = select("[data-platform-summary]");
    const grouped = new Map();
    for (const resource of mission.resources) {
      for (const platform of resource.platforms) {
        const entry = grouped.get(platform) || { resources: 0, assigned: 0 };
        entry.resources += 1;
        if (resource.assignment_count > 0) entry.assigned += 1;
        grouped.set(platform, entry);
      }
    }
    if (platformContainer instanceof HTMLElement) {
      platformContainer.replaceChildren();
      for (const [platform, values] of [...grouped.entries()].sort()) {
        const panel = element("article", "mission-panel");
        panel.append(
          element("h3", "", platform),
          element(
            "p",
            "mission-platform-value",
            `${values.resources} normalized objects`,
          ),
          element("p", "", `${values.assigned} with normalized assignments`),
        );
        platformContainer.append(panel);
      }
    }
    const unmapped = select("[data-unmapped-resources]");
    if (unmapped instanceof HTMLElement) {
      unmapped.replaceChildren();
      for (const resource of mission.unmapped_objects.slice(0, 12)) {
        const item = element("div", "mission-resource");
        item.append(
          element("strong", "", resource.title),
          element(
            "span",
            "",
            `${resource.resource_family} · ${resource.platforms.join(", ")} · ${resource.source_api_version}`,
          ),
        );
        unmapped.append(item);
      }
    }
    const frameworks = select("[data-framework-summary]");
    if (frameworks instanceof HTMLElement) {
      frameworks.replaceChildren();
      for (const [name, coverage] of Object.entries(
        mission.framework_coverage,
      )) {
        const panel = element("article", "mission-panel");
        panel.append(
          element("h3", "", name),
          element(
            "p",
            "mission-platform-value",
            `${coverage.technical_evidence_identifier_count} identifiers`,
          ),
          element("p", "", "Assessment conclusion: not evaluated"),
        );
        frameworks.append(panel);
      }
    }
  };

  const renderQuality = () => {
    const endpoint = select("[data-endpoint-coverage]");
    if (endpoint instanceof HTMLElement) {
      endpoint.replaceChildren();
      for (const item of mission.collection.endpoint_statuses) {
        const row = element("div", "mission-quality-row");
        row.append(
          element("span", `mission-dot mission-dot-${item.status}`, ""),
          element("strong", "", item.key),
          element(
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
        gaps.append(element("p", "", "No collection gaps recorded."));
      for (const gap of mission.collection_gaps) {
        const row = element("div", "mission-gap");
        row.append(
          element("strong", "", gap.resource_family.replaceAll("_", " ")),
          element(
            "span",
            "",
            `${gap.reason} · ${gap.required_permission} · additional evidence required`,
          ),
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
    ]);
  };

  const renderAssistant = () => {
    const assistant = select("[data-mission-assistant]");
    const statusNode = select("[data-runtime-status]");
    const detailNode = select("[data-runtime-detail]");
    const action = select("[data-generate-narrative]");
    const output = select("[data-narrative-output]");
    if (
      !(assistant instanceof HTMLElement) ||
      !(statusNode instanceof HTMLElement) ||
      !(detailNode instanceof HTMLElement) ||
      !(action instanceof HTMLButtonElement) ||
      !(output instanceof HTMLElement)
    )
      return;
    let selectedQuestion = "What are the highest-severity findings?";
    for (const button of all("[data-question]")) {
      if (!(button instanceof HTMLButtonElement)) continue;
      button.addEventListener("click", () => {
        selectedQuestion = button.dataset.question || selectedQuestion;
        all("[data-question]").forEach((item) =>
          item.removeAttribute("aria-pressed"),
        );
        button.setAttribute("aria-pressed", "true");
        action.textContent = "Ask the bounded assistant";
      });
    }
    const appendLine = (label, value) => {
      const row = element("p", "");
      row.append(
        element("strong", "", `${label}: `),
        document.createTextNode(formatValue(value)),
      );
      output.append(row);
    };
    const checkStatus = async () => {
      try {
        const response = await fetch("/api/status", {
          credentials: "same-origin",
        });
        const status = await response.json();
        if (!response.ok || status.status !== "ok") throw new Error();
        statusNode.textContent =
          status.narrative_mode === "fixture"
            ? "Fixture assistant ready"
            : "GPT-5.6 assistant ready";
        detailNode.textContent =
          status.narrative_mode === "fixture"
            ? "Answers are generated deterministically from the tracked sanitized package; no API charge occurs."
            : "A bounded sanitized evidence subset may be sent to the fixed project model.";
        action.disabled = status.narrative_available !== true;
        action.textContent = "Ask the bounded assistant";
        assistant.dataset.runtimeState = status.narrative_mode;
      } catch {
        statusNode.textContent = "Assistant unavailable";
        detailNode.textContent =
          "The deterministic dashboard remains operational without AI.";
        action.disabled = true;
        assistant.dataset.runtimeState = "unavailable";
      }
    };
    action.addEventListener("click", async () => {
      action.disabled = true;
      output.hidden = true;
      output.replaceChildren();
      statusNode.textContent = "Verifying bounded evidence";
      try {
        const response = await fetch("/api/ask", {
          method: "POST",
          credentials: "same-origin",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: selectedQuestion,
            snapshot_id: mission.snapshot_id,
          }),
        });
        const payload = await response.json();
        if (!response.ok)
          throw new Error(payload.message || "Assistant request was rejected");
        if (
          !["insufficient_evidence", "typed_claims_verified"].includes(
            payload.verification?.status,
          )
        ) {
          throw new Error(
            "Assistant response failed deterministic verification",
          );
        }
        appendLine("Question", selectedQuestion);
        appendLine("Answer", payload.answer.direct_answer);
        appendLine("Evidence sufficiency", payload.answer.evidence_sufficiency);
        appendLine(
          "Evidence references",
          payload.answer.evidence_references.join(", "),
        );
        appendLine("Verifier", payload.verification.status);
        appendLine("Generated prose", "quarantined for human review");
        output.hidden = false;
        statusNode.textContent =
          "Answer verified against deterministic evidence";
        detailNode.textContent = `${payload.mode} mode · human review remains required`;
      } catch (error) {
        appendLine(
          "Request stopped safely",
          error instanceof Error ? error.message : "Unknown error",
        );
        output.hidden = false;
        statusNode.textContent = "Assistant request rejected";
        detailNode.textContent =
          "No fallback, publication, or tenant change occurred.";
      } finally {
        action.disabled = false;
      }
    });
    void checkStatus();
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
        throw new Error("Mission evidence artifact could not be loaded");
      }
      mission = validateMission(await response.json());
      const collected = Date.parse(mission.collection.collected_at_utc);
      const stale =
        !Number.isFinite(collected) || Date.now() - collected > 86_400_000;
      const banner = select("[data-mission-banner]");
      if (banner instanceof HTMLElement) {
        banner.textContent = stale
          ? `${mission.data_mode} · evidence is stale or collection time is unavailable`
          : `${mission.data_mode} · allowlist and prohibited-pattern scans passed`;
        banner.dataset.state = stale
          ? "stale"
          : mission.data_mode.startsWith("LIVE")
            ? "live"
            : "fixture";
      }
      renderOverview();
      renderFindings();
      renderCoverage();
      renderQuality();
      renderAssistant();
      root.setAttribute("aria-busy", "false");
    } catch {
      const banner = select("[data-mission-banner]");
      if (banner instanceof HTMLElement) {
        banner.textContent =
          "DEGRADED OR STALE DATA · the public evidence package failed to load or validate";
        banner.dataset.state = "error";
      }
      root.setAttribute("aria-busy", "false");
    }
  };

  void initialize();
})();
