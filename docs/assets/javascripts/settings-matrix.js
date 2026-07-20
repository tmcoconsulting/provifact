(() => {
  "use strict";

  const root = document.querySelector("[data-settings-matrix]");
  if (!(root instanceof HTMLElement)) return;

  const CATALOG_FINGERPRINT =
    "sha256:2c30e3996b6070dc8a748aa84701689a3d813933682a66222b4afd1960b14e47";
  const CATALOG_URL =
    "/assets/data/baseline-catalog.json?v=2c30e3996b6070dc8a748aa84701689a3d813933682a66222b4afd1960b14e47";
  const banner = root.querySelector("[data-matrix-banner]");
  const summary = root.querySelector("[data-matrix-summary]");
  const table = root.querySelector("[data-matrix-table]");
  const search = root.querySelector("[data-matrix-search]");
  const outcome = root.querySelector("[data-matrix-outcome]");
  const section = root.querySelector("[data-matrix-section]");
  const framework = root.querySelector("[data-matrix-framework]");
  const mappedOnly = root.querySelector("[data-matrix-mapped-only]");
  const reset = root.querySelector("[data-matrix-reset]");
  const count = root.querySelector("[data-matrix-count]");
  const empty = root.querySelector("[data-matrix-empty]");
  const dialog = root.querySelector("[data-matrix-dialog]");
  const detail = root.querySelector("[data-matrix-detail]");
  const plan = root.querySelector("[data-matrix-plan]");
  const profile = root.querySelector("[data-matrix-profile]");
  const comparisonSummary = root.querySelector(
    "[data-matrix-comparison-summary]",
  );
  const comparisonGaps = root.querySelector("[data-matrix-comparison-gaps]");

  if (
    !(banner instanceof HTMLElement) ||
    !(summary instanceof HTMLElement) ||
    !(table instanceof HTMLTableElement) ||
    !(search instanceof HTMLInputElement) ||
    !(outcome instanceof HTMLSelectElement) ||
    !(section instanceof HTMLSelectElement) ||
    !(framework instanceof HTMLSelectElement) ||
    !(mappedOnly instanceof HTMLInputElement) ||
    !(reset instanceof HTMLButtonElement) ||
    !(count instanceof HTMLElement) ||
    !(empty instanceof HTMLElement) ||
    !(dialog instanceof HTMLDialogElement) ||
    !(detail instanceof HTMLElement) ||
    !(plan instanceof HTMLElement) ||
    !(profile instanceof HTMLSelectElement) ||
    !(comparisonSummary instanceof HTMLElement) ||
    !(comparisonGaps instanceof HTMLElement)
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
  const canonicalJson = (value) => {
    if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
    if (isRecord(value))
      return `{${Object.keys(value)
        .sort()
        .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
        .join(",")}}`;
    return JSON.stringify(value);
  };
  const sha256 = async (value) => {
    const digest = await crypto.subtle.digest(
      "SHA-256",
      new TextEncoder().encode(value),
    );
    return [...new Uint8Array(digest)]
      .map((byte) => byte.toString(16).padStart(2, "0"))
      .join("");
  };
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
  const implementationState = (requirement) => {
    if (requirement.reference_only === true)
      return "Not in TMCO Consulting approved baseline";
    if (requirement.evaluation_included === true) return requirement.outcome;
    if (
      requirement.mapping_review_status === "not reviewed" &&
      requirement.setting_key &&
      requirement.setting_key !== "not mapped"
    )
      return "Provider mapping review required";
    return "Implementation planning required";
  };
  const implementationTarget = (requirement) =>
    requirement.reference_only === true
      ? "Reference profile membership; target not approved"
      : requirement.setting_key && requirement.setting_key !== "not mapped"
        ? formatValue(requirement.expected_value)
        : "Target pending approved mapping";
  const implementationObserved = (requirement) =>
    requirement.reference_only === true
      ? "Not evaluated"
      : requirement.evaluation_included === true
        ? formatValue(requirement.observed_value)
        : "Not deterministically collected";
  const stateClass = (value) => {
    if (value === "Aligned") return "matrix-state-aligned";
    if (value === "Conflicting policy") return "matrix-state-conflict";
    if (value === "Missing from tenant") return "matrix-state-missing";
    if (value === "Unsupported by provider") return "matrix-state-unsupported";
    if (
      value === "Human review required" ||
      value === "Collection gap" ||
      value === "Provider mapping not reviewed" ||
      value === "Provider mapping review required" ||
      value === "Not in TMCO Consulting approved baseline" ||
      value === "Implementation planning required" ||
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
    if (requirement.reference_only === true)
      return "Baseline owner review: decide whether this reference-profile rule belongs in the TMCO Consulting-approved baseline. If adopted, approve its target, management path, and evidence source before evaluation.";
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
        return requirement.setting_key &&
          requirement.setting_key !== "not mapped"
          ? "Review and approve the exact Intune setting definition ID before this rule enters deterministic evaluation."
          : "Classify the approved implementation path: Intune Settings Catalog, custom profile, script or agent, or alternate evidence. Then approve a typed target and exact collector mapping.";
      case "Unsupported by provider":
        return "Document an approved alternate implementation or evidence path; do not infer provider support.";
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
    const { requirement, finding, resources, referenceProfile } = row;
    detail.replaceChildren();
    const heading = create("h2", "", requirement.title);
    heading.id = "matrix-dialog-title";
    const label = create(
      "p",
      "matrix-dialog-status",
      `${implementationState(requirement)} · ${requirement.severity} severity`,
    );
    const list = create("dl", "matrix-detail-list");
    addDetail(list, "Planning state", implementationState(requirement));
    addDetail(list, "Raw deterministic state", requirement.outcome);
    if (requirement.reference_only === true)
      addDetail(
        list,
        "Reference membership",
        `${referenceProfile?.label || "Selected profile"}; not currently in the TMCO Consulting-approved baseline`,
      );
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
    detail.append(heading, label, list, action);
    if (
      requirement.reference_only !== true &&
      typeof requirement.requirement_id === "string"
    ) {
      const ask = create(
        "button",
        "md-button md-button--primary",
        "Ask Provifact Assistant about this setting",
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
      detail.append(ask);
    }
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

  const validateCatalog = async (value, mission) => {
    if (
      !isRecord(value) ||
      Object.keys(value).sort().join(",") !==
        "catalog_fingerprint,comparison_boundary,metadata_fallback_rule_ids,profiles,rules,schema_version,source" ||
      value.schema_version !== "1.0.0" ||
      !/^sha256:[0-9a-f]{64}$/.test(value.catalog_fingerprint) ||
      value.catalog_fingerprint !== CATALOG_FINGERPRINT ||
      !isRecord(value.source) ||
      Object.keys(value.source).sort().join(",") !==
        "attribution,license,platform,repository,revision" ||
      typeof value.source.repository !== "string" ||
      typeof value.source.attribution !== "string" ||
      value.source.revision !== mission.baseline.source_revision ||
      !Array.isArray(value.profiles) ||
      !Array.isArray(value.rules) ||
      !Array.isArray(value.metadata_fallback_rule_ids) ||
      value.metadata_fallback_rule_ids.length !== 0 ||
      typeof value.comparison_boundary !== "string"
    )
      throw new Error("Baseline catalog failed its source and schema contract");
    const unsigned = { ...value };
    delete unsigned.catalog_fingerprint;
    if (
      value.catalog_fingerprint !==
      `sha256:${await sha256(canonicalJson(unsigned))}`
    )
      throw new Error("Baseline catalog fingerprint did not verify");
    const ruleIds = new Set(
      value.rules
        .filter(
          (item) =>
            isRecord(item) &&
            typeof item.rule_id === "string" &&
            typeof item.title === "string" &&
            typeof item.section === "string" &&
            Array.isArray(item.profile_ids) &&
            item.profile_ids.every(
              (profileId) => typeof profileId === "string",
            ),
        )
        .map((item) => item.rule_id),
    );
    const profiles = value.profiles.filter(
      (item) =>
        isRecord(item) &&
        typeof item.profile_id === "string" &&
        typeof item.label === "string" &&
        typeof item.family === "string" &&
        Array.isArray(item.rule_ids) &&
        item.rule_ids.every((ruleId) => typeof ruleId === "string") &&
        item.rule_ids.length === item.rule_count &&
        new Set(item.rule_ids).size === item.rule_ids.length &&
        item.rule_ids.every((ruleId) => ruleIds.has(ruleId)),
    );
    if (profiles.length !== value.profiles.length)
      throw new Error("Baseline catalog contains an invalid profile");
    const tmco = profiles.find((item) => item.profile_id === "tmco_approved");
    const missionRuleIds = new Set(
      mission.requirements
        .filter((item) => isRecord(item) && typeof item.rule_id === "string")
        .map((item) => item.rule_id),
    );
    if (
      !tmco ||
      tmco.rule_count !== mission.baseline.rule_count ||
      tmco.source_sha256 !== mission.baseline.extracted_baseline_sha256 ||
      missionRuleIds.size !== tmco.rule_ids.length ||
      !tmco.rule_ids.every((ruleId) => missionRuleIds.has(ruleId))
    )
      throw new Error("Baseline catalog does not match the approved baseline");
    return { ...value, profiles };
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
      const [response, catalogResponse] = await Promise.all([
        fetch(url, {
          credentials: "same-origin",
          cache: "no-store",
          headers: { Accept: "application/json" },
        }),
        fetch(CATALOG_URL, {
          credentials: "same-origin",
          cache: "force-cache",
          headers: { Accept: "application/json" },
        }),
      ]);
      if (
        !response.ok ||
        !response.headers.get("Content-Type")?.includes("application/json") ||
        !catalogResponse.ok ||
        !catalogResponse.headers
          .get("Content-Type")
          ?.includes("application/json")
      )
        throw new Error(
          "Mission package or baseline catalog could not be loaded",
        );
      const mission = validateMission(await response.json());
      const catalog = await validateCatalog(
        await catalogResponse.json(),
        mission,
      );
      const catalogRules = new Map(
        catalog.rules.map((item) => [item.rule_id, item]),
      );
      const catalogProfiles = new Map(
        catalog.profiles.map((item) => [item.profile_id, item]),
      );
      const tmcoProfile = catalogProfiles.get("tmco_approved");
      if (!tmcoProfile)
        throw new Error(
          "TMCO Consulting approved profile is missing from the catalog",
        );
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
          referenceProfile: null,
        }));

      const profileGroups = new Map();
      for (const catalogProfile of catalog.profiles) {
        if (catalogProfile.profile_id === "tmco_approved") continue;
        const group = profileGroups.get(catalogProfile.family) || [];
        group.push(catalogProfile);
        profileGroups.set(catalogProfile.family, group);
      }
      for (const [family, catalogProfilesInFamily] of profileGroups) {
        const optionGroup = create("optgroup");
        optionGroup.label = family;
        for (const catalogProfile of catalogProfilesInFamily) {
          const option = create(
            "option",
            "",
            `${catalogProfile.label} · ${catalogProfile.rule_count} rules`,
          );
          option.value = catalogProfile.profile_id;
          optionGroup.append(option);
        }
        profile.append(optionGroup);
      }
      profile.value = "cis_lvl1";
      const requestedProfile = new URL(window.location.href).searchParams.get(
        "profile",
      );
      if (
        requestedProfile &&
        requestedProfile !== "tmco_approved" &&
        catalogProfiles.has(requestedProfile)
      )
        profile.value = requestedProfile;

      for (const value of [
        ...new Set([
          ...rows.map(({ requirement }) => implementationState(requirement)),
          "Not in TMCO Consulting approved baseline",
        ]),
      ].sort()) {
        const option = create("option", "", value);
        option.value = value;
        outcome.append(option);
      }
      for (const value of [
        ...new Set([
          ...rows.map(({ requirement }) => requirement.section),
          ...catalog.rules.map((rule) => rule.section),
        ]),
      ].sort()) {
        const option = create("option", "", value);
        option.value = value;
        section.append(option);
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
      const planning = rows.filter(
        ({ requirement }) => requirement.evaluation_included !== true,
      );
      const providerReview = planning.filter(
        ({ requirement }) =>
          requirement.setting_key && requirement.setting_key !== "not mapped",
      ).length;
      const summaryValues = [
        [rows.length, "TMCO Consulting-approved rules"],
        [mapped.length, "Exact Intune joins"],
        [planning.length, "Implementation backlog"],
        [evaluated.length - aligned, "Deterministic drift"],
        [aligned, "Matches desired state"],
      ];
      summary.replaceChildren();
      for (const [value, label] of summaryValues) {
        const card = create("article", "matrix-summary-card");
        card.append(create("strong", "", value), create("span", "", label));
        summary.append(card);
      }
      plan.replaceChildren();
      const sectionGroups = new Map();
      for (const row of rows) {
        const values = sectionGroups.get(row.requirement.section) || [];
        values.push(row.requirement);
        sectionGroups.set(row.requirement.section, values);
      }
      for (const [sectionName, requirements] of sectionGroups) {
        const evaluatedCount = requirements.filter(
          (requirement) => requirement.evaluation_included === true,
        ).length;
        const card = create("article", "matrix-plan-card");
        card.append(
          create("strong", "", sectionName),
          create(
            "span",
            "",
            `${requirements.length - evaluatedCount} to plan · ${evaluatedCount} evaluated`,
          ),
        );
        plan.append(card);
      }
      const planNote = create("p", "matrix-plan-note");
      planNote.textContent = `${providerReview} rule has an approved desired value but still needs an exact Intune definition review; ${planning.length - providerReview} rules need an approved management and evidence path.`;
      plan.append(planNote);
      banner.textContent = `${mission.data_mode} · ${mission.baseline.name} · collected ${new Date(mission.collection.collected_at_utc).toLocaleString()} · public-safe evidence only`;
      banner.dataset.state = mission.data_mode.startsWith("LIVE")
        ? "live"
        : "fixture";

      const tmcoRuleIds = new Set(tmcoProfile.rule_ids);
      const missionRowsByRule = new Map(
        rows.map((row) => [row.requirement.rule_id, row]),
      );

      const selectedProfile = () => {
        const value = catalogProfiles.get(profile.value);
        if (!value || value.profile_id === "tmco_approved")
          throw new Error("Selected comparison profile is unavailable");
        return value;
      };

      const rowsForProfile = (referenceProfile) => {
        const referenceIds = new Set(referenceProfile.rule_ids);
        const combined = rows.map((row) => ({
          ...row,
          referenceProfile,
          inReferenceProfile: referenceIds.has(row.requirement.rule_id),
        }));
        for (const ruleId of referenceProfile.rule_ids) {
          if (missionRowsByRule.has(ruleId)) continue;
          const rule = catalogRules.get(ruleId);
          if (!rule) continue;
          combined.push({
            requirement: {
              reference_only: true,
              rule_id: rule.rule_id,
              title: rule.title,
              section: rule.section,
              outcome: "Not evaluated",
              severity: "not evaluated",
              setting_key: "not mapped",
              mapping_review_status: "not reviewed",
              provider_definition_ids: [],
              matched_provider_definition_ids: [],
              source_evidence_ids: [],
              evaluation_included: false,
              assignment_summary: "No company evidence scope approved",
            },
            finding: null,
            resources: [],
            referenceProfile,
            inReferenceProfile: true,
          });
        }
        return combined;
      };

      const renderComparison = (referenceProfile, combinedRows) => {
        const referenceIds = new Set(referenceProfile.rule_ids);
        const overlap = [...tmcoRuleIds].filter((ruleId) =>
          referenceIds.has(ruleId),
        );
        const referenceGaps = referenceProfile.rule_ids.filter(
          (ruleId) => !tmcoRuleIds.has(ruleId),
        );
        const tmcoOnly = [...tmcoRuleIds].filter(
          (ruleId) => !referenceIds.has(ruleId),
        );
        const overlapEvaluated = combinedRows.filter(
          ({ requirement, inReferenceProfile }) =>
            inReferenceProfile && requirement.evaluation_included === true,
        ).length;
        const percent = referenceProfile.rule_count
          ? Math.round((overlap.length / referenceProfile.rule_count) * 100)
          : 0;
        comparisonSummary.replaceChildren();
        for (const [value, label] of [
          [
            `${overlap.length}/${referenceProfile.rule_count}`,
            "Reference rules included",
          ],
          [`${percent}%`, "Technical membership overlap"],
          [referenceGaps.length, "Reference rules to consider"],
          [tmcoOnly.length, "TMCO Consulting-only rules"],
          [overlapEvaluated, "Overlap rules with deterministic evidence"],
        ]) {
          const card = create("article", "matrix-comparison-card");
          card.append(create("strong", "", value), create("span", "", label));
          comparisonSummary.append(card);
        }
        comparisonGaps.replaceChildren();
        const progress = create("div", "matrix-overlap-meter");
        const fill = create("span");
        fill.style.width = `${percent}%`;
        progress.append(fill);
        comparisonGaps.append(
          create(
            "p",
            "matrix-comparison-caption",
            `${referenceProfile.label}: ${overlap.length} of ${referenceProfile.rule_count} rule IDs are present in the TMCO Consulting-approved baseline.`,
          ),
          progress,
        );
        const provenance = create("p", "matrix-comparison-source");
        provenance.append(
          "Pinned source: ",
          (() => {
            const link = create("a", "", catalog.source.attribution);
            link.href = catalog.source.repository;
            link.rel = "noopener noreferrer";
            return link;
          })(),
          ` · revision ${catalog.source.revision.slice(0, 12)} · catalog ${catalog.catalog_fingerprint.slice(0, 19)}…`,
        );
        comparisonGaps.append(provenance);
        if (referenceGaps.length) {
          const heading = create(
            "strong",
            "matrix-comparison-gap-heading",
            `${referenceGaps.length} reference-profile rule${referenceGaps.length === 1 ? "" : "s"} not in the company baseline`,
          );
          const list = create("div", "matrix-comparison-gap-list");
          for (const ruleId of referenceGaps.slice(0, 8)) {
            const rule = catalogRules.get(ruleId);
            if (!rule) continue;
            const item = create("span");
            item.append(
              create("strong", "", rule.title),
              create("code", "", rule.rule_id),
            );
            list.append(item);
          }
          comparisonGaps.append(heading, list);
          if (referenceGaps.length > 8)
            comparisonGaps.append(
              create(
                "p",
                "matrix-comparison-more",
                `${referenceGaps.length - 8} more reference-only rules are included in the searchable table below.`,
              ),
            );
        } else {
          comparisonGaps.append(
            create(
              "p",
              "matrix-comparison-complete",
              "Every rule ID in this reference profile is present in the TMCO Consulting-approved baseline. Implementation and observed evidence remain separate questions.",
            ),
          );
        }
      };

      const render = () => {
        const referenceProfile = selectedProfile();
        const comparisonRows = rowsForProfile(referenceProfile);
        renderComparison(referenceProfile, comparisonRows);
        const query = search.value.trim().toLowerCase();
        const selectedOutcome = outcome.value;
        const selectedSection = section.value;
        const selectedFramework = framework.value;
        const filtered = comparisonRows.filter(
          ({ requirement, resources: evidence }) => {
            if (mappedOnly.checked && !hasReviewedProviderMapping(requirement))
              return false;
            if (
              selectedOutcome &&
              implementationState(requirement) !== selectedOutcome
            )
              return false;
            if (selectedSection && requirement.section !== selectedSection)
              return false;
            if (
              selectedFramework === "cis_benchmark" &&
              requirement.reference_only === true
            )
              return false;
            if (
              selectedFramework &&
              selectedFramework !== "cis_benchmark" &&
              !frameworkIds(requirement, selectedFramework).length
            )
              return false;
            if (!query) return true;
            return [
              requirement.title,
              requirement.rule_id,
              requirement.setting_key,
              requirement.outcome,
              implementationState(requirement),
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
          },
        );

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
          if (typeof requirement.requirement_id === "string")
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
            create("code", "", implementationObserved(requirement)),
            create("span", "", "→"),
            create("code", "", implementationTarget(requirement)),
          );
          const stateCell = create("td");
          stateCell.append(state(implementationState(requirement)));
          const frameworks = create("td", "matrix-framework-chips");
          if (requirement.reference_only === true) {
            frameworks.append(
              create(
                "span",
                "matrix-membership-reference",
                `${row.referenceProfile.label} only`,
              ),
            );
          } else {
            frameworks.append(
              create(
                "span",
                "matrix-membership-tmco",
                "TMCO Consulting Approved",
              ),
            );
            frameworks.append(
              create(
                "span",
                row.inReferenceProfile
                  ? "matrix-membership-shared"
                  : "matrix-membership-tmco-only",
                row.inReferenceProfile
                  ? `Also in ${row.referenceProfile.label}`
                  : `Not in ${row.referenceProfile.label}`,
              ),
            );
          }
          for (const { key, label } of frameworkColumns) {
            const ids = frameworkIds(requirement, key);
            if (ids.length)
              frameworks.append(create("span", "", `${label} ${ids.length}`));
          }
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
        count.textContent = `${filtered.length} of ${comparisonRows.length} visible rules shown · ${rows.length} TMCO Consulting Approved + ${comparisonRows.length - rows.length} ${referenceProfile.label}-only`;
        empty.hidden = filtered.length !== 0;
        if (!filtered.length)
          empty.textContent = "No settings match the selected filters.";
      };

      for (const control of [
        search,
        outcome,
        section,
        framework,
        mappedOnly,
        profile,
      ]) {
        control.addEventListener("input", render);
        control.addEventListener("change", render);
      }
      profile.addEventListener("change", () => {
        const next = new URL(window.location.href);
        next.searchParams.set("profile", profile.value);
        window.history.replaceState(null, "", next);
      });
      reset.addEventListener("click", () => {
        search.value = "";
        outcome.value = "";
        section.value = "";
        framework.value = "";
        profile.value = "cis_lvl1";
        mappedOnly.checked = false;
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
