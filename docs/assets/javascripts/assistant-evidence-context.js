(() => {
  "use strict";

  const STATUS_URL = "/api/status";
  const HISTORY_KEY = "provifact-assistant-history-v2";
  const MAX_HISTORY = 12;
  const EVIDENCE_ID = /^(?:finding|req|gap|mission)-[0-9a-f]{24}$/;
  const CLAIM_CODES = new Set([
    "alignment_percent",
    "change_count",
    "collection_gap_count",
    "collection_gap_present",
    "data_mode",
    "device_aggregate",
    "finding_outcome",
    "framework_reference_set_count",
    "intune_write_capability",
    "requirement_outcome",
    "resolved_drift_count",
    "unevaluated_resource_count",
  ]);
  const operationalPaths = new Set([
    "/",
    "/evidence-dashboard/",
    "/settings-matrix/",
    "/live-demo/",
  ]);
  const suggestions = [
    { label: "Priority queue", question: "What requires my attention?" },
    {
      label: "FileVault evidence",
      question: "Why is FileVault aligned or drifting?",
    },
    {
      label: "Change watch",
      question: "What changed since the previous collection?",
    },
    {
      label: "Coverage gaps",
      question: "What is not currently evaluated?",
    },
    {
      label: "Evidence boundary",
      question: "What can Provifact not conclude?",
    },
    { label: "Data provenance", question: "Is this live tenant data?" },
  ];

  const create = (tagName, className = "", text = "") => {
    const node = document.createElement(tagName);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  };

  const isRecord = (value) =>
    value !== null && typeof value === "object" && !Array.isArray(value);

  const currentPage = () => {
    const path = window.location.pathname;
    if (path === "/" || path.endsWith("/index.html")) return "overview";
    if (window.location.hash === "#changes") return "changes";
    if (path.includes("evidence-dashboard")) return "findings";
    if (path.includes("settings-matrix")) return "settings";
    if (path.includes("live-demo")) return "evidence";
    return "documentation";
  };

  const fetchJson = async (url, options = {}) => {
    const response = await fetch(url, {
      credentials: "same-origin",
      headers: { Accept: "application/json" },
      cache: "no-store",
      ...options,
    });
    const contentType = response.headers.get("Content-Type") || "";
    if (!contentType.includes("application/json")) {
      throw new Error("Provifact returned an unexpected response type");
    }
    const payload = await response.json();
    return { payload, response };
  };

  const validateStatus = (value) => {
    if (
      !isRecord(value) ||
      value.status !== "ok" ||
      !["fixture", "openai"].includes(value.narrative_mode) ||
      typeof value.narrative_available !== "boolean" ||
      typeof value.model_call_available !== "boolean" ||
      typeof value.data_mode !== "string" ||
      typeof value.evidence_timestamp !== "string" ||
      typeof value.source_snapshot_id !== "string" ||
      !EVIDENCE_ID.test(value.source_snapshot_id) ||
      typeof value.provider !== "string" ||
      typeof value.approved_baseline !== "string"
    ) {
      throw new Error("Worker status failed its browser contract");
    }
    return value;
  };

  const stringArray = (value, maximum = 40) =>
    Array.isArray(value) &&
    value.length <= maximum &&
    value.every((item) => typeof item === "string");

  const jsonValue = (value, depth = 0) => {
    if (depth > 8) return false;
    if (
      value === null ||
      typeof value === "string" ||
      typeof value === "boolean"
    )
      return true;
    if (typeof value === "number") return Number.isFinite(value);
    if (Array.isArray(value))
      return (
        value.length <= 128 && value.every((item) => jsonValue(item, depth + 1))
      );
    if (!isRecord(value) || Object.keys(value).length > 64) return false;
    return Object.entries(value).every(
      ([key, item]) => key.length <= 96 && jsonValue(item, depth + 1),
    );
  };

  const canonicalJson = (value) => {
    if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
    if (isRecord(value))
      return `{${Object.keys(value)
        .sort()
        .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
        .join(",")}}`;
    return JSON.stringify(value);
  };

  const claimArray = (value) =>
    Array.isArray(value) &&
    value.length <= 32 &&
    value.every(
      (item) =>
        isRecord(item) &&
        Object.keys(item).sort().join(",") ===
          "claim_code,claim_value,subject_id" &&
        typeof item.claim_code === "string" &&
        CLAIM_CODES.has(item.claim_code) &&
        typeof item.subject_id === "string" &&
        item.subject_id.length <= 96 &&
        jsonValue(item.claim_value),
    );

  const validateAssistantPayload = (value, status) => {
    if (
      !isRecord(value) ||
      !["fixture", "openai"].includes(value.mode) ||
      value.human_review_required !== true ||
      value.source_snapshot_id !== status.source_snapshot_id ||
      !isRecord(value.answer) ||
      !isRecord(value.verification) ||
      !["typed_claims_verified", "insufficient_evidence"].includes(
        value.verification.status,
      ) ||
      value.verification.generated_prose_quarantined !== true ||
      value.verification.human_review_required !== true ||
      typeof value.verification.verifier_version !== "string" ||
      !stringArray(value.verification.typed_claims_accepted, 32) ||
      !stringArray(value.verification.typed_claims_rejected, 32) ||
      !stringArray(value.verification.reasons, 16) ||
      typeof value.answer.direct_answer !== "string" ||
      value.answer.direct_answer.length < 1 ||
      value.answer.direct_answer.length > 1200 ||
      value.answer.human_review_required !== true ||
      typeof value.answer.ai_generated_analysis !== "boolean" ||
      !["verified", "partial", "insufficient"].includes(
        value.answer.evidence_sufficiency,
      ) ||
      !claimArray(value.answer.claims) ||
      !stringArray(value.answer.evidence_references) ||
      !value.answer.evidence_references.every((reference) =>
        EVIDENCE_ID.test(reference),
      ) ||
      !stringArray(value.answer.limitations, 8) ||
      !stringArray(value.answer.additional_evidence_required, 8) ||
      !stringArray(value.answer.suggested_human_review_questions, 8)
    ) {
      throw new Error("The answer failed deterministic browser verification.");
    }
    const accepted = value.verification.typed_claims_accepted;
    const claims = value.answer.claims.map(canonicalJson).sort();
    if (
      value.verification.typed_claims_rejected.length !== 0 ||
      value.verification.reasons.length !== 0 ||
      accepted.length !== claims.length ||
      accepted.some((item, index) => item !== claims[index])
    )
      throw new Error("The answer failed deterministic browser verification.");
    return value;
  };

  const loadStatus = async (fresh = false) => {
    const suffix = fresh ? `?check=${Date.now()}` : "";
    const { payload, response } = await fetchJson(`${STATUS_URL}${suffix}`);
    if (!response.ok) throw new Error("Worker status is unavailable");
    return validateStatus(payload);
  };

  let statusPromise = loadStatus();
  let currentStatus = null;

  const freshnessState = (status) => {
    if (status.data_mode.startsWith("SYNTHETIC")) return "fixed fixture";
    const collected = Date.parse(status.evidence_timestamp);
    const maximum = Number(status.evidence_maximum_age_seconds);
    if (
      !Number.isFinite(collected) ||
      !Number.isFinite(maximum) ||
      maximum <= 0
    )
      return "stale";
    return Date.now() - collected > maximum * 1000 ? "stale" : "current";
  };

  const renderProvenance = async () => {
    const path = window.location.pathname;
    if (!operationalPaths.has(path)) return;
    const content = document.querySelector(".md-content__inner");
    if (!(content instanceof HTMLElement)) return;
    const missionSlot = document.querySelector("[data-provenance-slot]");

    const panel = create("section", "evidence-provenance");
    panel.setAttribute("aria-label", "Current evidence provenance");
    panel.dataset.state = "loading";
    const statusLabel = create(
      "strong",
      "evidence-provenance-state",
      "VALIDATING",
    );
    const facts = create("dl", "evidence-provenance-facts");
    const detail = create(
      "p",
      "evidence-provenance-detail",
      "Checking the current public package and Worker runtime…",
    );
    const refresh = create(
      "button",
      "evidence-provenance-refresh",
      "Check for newer published snapshot",
    );
    refresh.type = "button";
    const refreshNote = create(
      "span",
      "evidence-provenance-refresh-note",
      "Checks published evidence only; it never triggers Microsoft Graph collection.",
    );
    panel.append(statusLabel, facts, detail, refresh, refreshNote);
    if (missionSlot instanceof HTMLElement) missionSlot.append(panel);
    else content.prepend(panel);

    const addFact = (label, value) => {
      facts.append(create("dt", "", label), create("dd", "", value));
    };

    const render = (status) => {
      currentStatus = status;
      facts.replaceChildren();
      const freshness = freshnessState(status);
      const state = status.data_mode.startsWith("SYNTHETIC")
        ? "fixture"
        : freshness === "stale"
          ? "stale"
          : status.data_mode.startsWith("LIVE")
            ? "live"
            : "stale";
      panel.dataset.state = state;
      statusLabel.textContent =
        state === "stale" ? "DEGRADED / STALE" : status.data_mode;
      addFact(
        "Collected",
        new Date(status.evidence_timestamp).toLocaleString(),
      );
      addFact("Freshness", freshness);
      addFact("Provider", status.provider);
      addFact("Snapshot", status.source_snapshot_id);
      addFact("Approved baseline", status.approved_baseline);
      addFact(
        "Provifact Assistant",
        status.model_call_available
          ? `${status.model} via OpenAI`
          : status.narrative_mode === "fixture"
            ? "deterministic fixture; no model call"
            : "model unavailable",
      );
      detail.textContent =
        state === "live"
          ? "This page is derived from the current fail-closed sanitized tenant package."
          : state === "fixture"
            ? "This page is a synthetic demonstration and is not tenant posture."
            : "Do not rely on posture conclusions until a current valid package is published.";
    };

    try {
      render(await statusPromise);
    } catch {
      panel.dataset.state = "stale";
      statusLabel.textContent = "DEGRADED / STALE";
      detail.textContent =
        "The Worker could not prove the current package. Provifact did not substitute synthetic findings.";
      refresh.disabled = true;
    }

    refresh.addEventListener("click", async () => {
      refresh.disabled = true;
      refresh.textContent = "Checking published evidence…";
      try {
        const latest = await loadStatus(true);
        if (
          currentStatus !== null &&
          latest.source_snapshot_id !== currentStatus.source_snapshot_id
        ) {
          refresh.disabled = false;
          refresh.textContent = "Load newer published snapshot";
          detail.textContent = `A newer sanitized snapshot is available: ${latest.source_snapshot_id}. Loading it does not collect from Intune.`;
          refresh.addEventListener(
            "click",
            () => {
              const url = new URL(window.location.href);
              url.searchParams.set("snapshot", latest.source_snapshot_id);
              window.location.assign(url);
            },
            { once: true },
          );
          return;
        }
        render(latest);
        refresh.textContent = "Current snapshot confirmed";
      } catch {
        refresh.textContent = "Snapshot check unavailable";
        detail.textContent =
          "The published snapshot could not be revalidated. No collection or fallback occurred.";
      } finally {
        if (refresh.textContent !== "Load newer published snapshot") {
          window.setTimeout(() => {
            refresh.disabled = false;
            refresh.textContent = "Check for newer published snapshot";
          }, 1800);
        }
      }
    });
  };

  const readHistory = () => {
    try {
      const parsed = JSON.parse(sessionStorage.getItem(HISTORY_KEY) || "[]");
      if (!Array.isArray(parsed)) return [];
      return parsed
        .filter(
          (item) =>
            isRecord(item) &&
            typeof item.question === "string" &&
            typeof item.answer === "string" &&
            stringArray(item.references) &&
            isRecord(item.analysis) &&
            typeof item.analysis.aiGenerated === "boolean" &&
            stringArray(item.analysis.limitations, 8) &&
            stringArray(item.analysis.additionalEvidence, 8) &&
            stringArray(item.analysis.reviewQuestions, 8),
        )
        .slice(-MAX_HISTORY);
    } catch {
      return [];
    }
  };

  const writeHistory = (history) => {
    try {
      sessionStorage.setItem(
        HISTORY_KEY,
        JSON.stringify(history.slice(-MAX_HISTORY)),
      );
    } catch {
      // Session-only history is optional; the assistant remains usable without storage.
    }
  };

  const evidenceHref = (reference) => {
    if (reference.startsWith("finding-"))
      return `/evidence-dashboard/#${reference}`;
    if (reference.startsWith("req-"))
      return `/settings-matrix/?selected=${encodeURIComponent(reference)}#settings-matrix`;
    if (reference.startsWith("gap-"))
      return `/evidence-dashboard/#collection-health`;
    if (reference.startsWith("mission-"))
      return "/evidence-dashboard/#overview";
    return null;
  };

  const renderAssistant = async () => {
    const launcher = create(
      "button",
      "provifact-assistant-launcher",
      "Provifact Assistant",
    );
    launcher.type = "button";
    launcher.setAttribute("aria-haspopup", "dialog");
    launcher.setAttribute("aria-expanded", "false");

    const dialog = create("dialog", "provifact-assistant");
    dialog.id = "provifact-assistant";
    dialog.setAttribute("aria-labelledby", "provifact-assistant-title");
    launcher.setAttribute("aria-controls", dialog.id);

    const header = create("header", "provifact-assistant-header");
    const headingGroup = create("div");
    const eyebrow = create(
      "span",
      "provifact-assistant-eyebrow",
      "Bounded evidence assistant",
    );
    const heading = create("h2", "", "Provifact Assistant");
    heading.id = "provifact-assistant-title";
    const runtime = create(
      "p",
      "provifact-assistant-runtime",
      "Checking runtime…",
    );
    headingGroup.append(eyebrow, heading, runtime);
    const close = create("button", "provifact-assistant-close", "Close");
    close.type = "button";
    close.setAttribute("aria-label", "Close Provifact Assistant");
    header.append(headingGroup, close);

    const selected = create("div", "provifact-assistant-selected");
    selected.hidden = true;
    const selectedText = create("span");
    const clearSelected = create("button", "", "Clear selected evidence");
    clearSelected.type = "button";
    selected.append(selectedText, clearSelected);

    const transcript = create("div", "provifact-assistant-transcript");
    transcript.setAttribute("aria-live", "polite");
    transcript.setAttribute("aria-label", "Provifact Assistant conversation");
    const emptyState = create("section", "provifact-assistant-welcome");
    emptyState.append(
      create("span", "provifact-assistant-welcome-mark", "P"),
      create("strong", "", "Ask the evidence, not the tenant"),
      create(
        "p",
        "",
        "Provifact sends a bounded sanitized evidence subset to the fixed model, then verifies deterministic claims and evidence references before showing the answer.",
      ),
    );
    transcript.append(emptyState);
    const suggestionSection = create(
      "section",
      "provifact-assistant-suggestion-section",
    );
    const suggestionHeading = create(
      "strong",
      "provifact-assistant-suggestion-heading",
      "Start with a focused evidence question",
    );
    suggestionHeading.id = "provifact-assistant-suggestion-heading";
    const suggestionGroup = create("div", "provifact-assistant-suggestions");
    suggestionGroup.setAttribute("aria-label", "Suggested evidence questions");
    suggestionGroup.setAttribute(
      "aria-labelledby",
      "provifact-assistant-suggestion-heading",
    );
    suggestionSection.append(suggestionHeading, suggestionGroup);

    const form = create("form", "provifact-assistant-form");
    const label = create("label", "", "Ask about the published evidence");
    const input = create("textarea");
    input.name = "question";
    input.rows = 2;
    input.maxLength = 240;
    input.required = true;
    input.placeholder = "What requires my attention?";
    label.append(input);
    const submit = create("button", "", "Ask Provifact Assistant");
    submit.type = "submit";
    submit.disabled = true;
    const formStatus = create("p", "provifact-assistant-form-status");
    formStatus.setAttribute("role", "status");
    form.append(label, submit, formStatus);

    const boundary = create(
      "p",
      "provifact-assistant-boundary",
      "Only the question, page enum, snapshot ID, and optional selected evidence ID are sent. No DOM, tenant identities, or browser API key is sent. Answers remain subject to human review.",
    );
    dialog.append(
      header,
      selected,
      transcript,
      suggestionSection,
      form,
      boundary,
    );
    document.body.append(launcher, dialog);

    let selectedEvidenceId = null;
    let history = readHistory();

    const appendMessage = (role, text, references = [], analysis = null) => {
      emptyState.hidden = true;
      const article = create(
        "article",
        `provifact-assistant-message provifact-assistant-${role}`,
      );
      const messageHeader = create("div", "provifact-assistant-message-header");
      messageHeader.append(
        create("strong", "", role === "user" ? "You" : "Provifact Assistant"),
      );
      if (role === "assistant" && isRecord(analysis)) {
        messageHeader.append(
          create(
            "span",
            "provifact-assistant-generated-label",
            analysis.aiGenerated
              ? "AI-GENERATED · REVIEW REQUIRED"
              : "DETERMINISTIC FIXTURE",
          ),
        );
      }
      article.append(messageHeader, create("p", "", text));
      const links = references
        .filter(
          (reference) =>
            typeof reference === "string" && EVIDENCE_ID.test(reference),
        )
        .map((reference) => ({ reference, href: evidenceHref(reference) }))
        .filter((item) => item.href !== null);
      if (links.length) {
        const nav = create("nav", "provifact-assistant-links");
        nav.setAttribute("aria-label", "Evidence references");
        for (const { reference, href } of links) {
          const link = create("a", "", reference);
          link.href = href;
          nav.append(link);
        }
        article.append(nav);
      }
      if (role === "assistant" && isRecord(analysis)) {
        const details = create(
          "details",
          "provifact-assistant-analysis-details",
        );
        const detailSummary = create(
          "summary",
          "",
          "Evidence boundary and next review",
        );
        details.append(detailSummary);
        for (const [label, values] of [
          ["Limitations", analysis.limitations],
          ["Additional evidence", analysis.additionalEvidence],
          ["Human review questions", analysis.reviewQuestions],
        ]) {
          if (!Array.isArray(values) || !values.length) continue;
          const section = create("section");
          section.append(create("strong", "", label));
          const list = create("ul");
          for (const value of values) list.append(create("li", "", value));
          section.append(list);
          details.append(section);
        }
        article.append(details);
      }
      transcript.append(article);
      transcript.scrollTop = transcript.scrollHeight;
    };

    for (const item of history) {
      appendMessage("user", item.question);
      appendMessage("assistant", item.answer, item.references, item.analysis);
    }

    for (const suggestion of suggestions) {
      const button = create("button");
      button.type = "button";
      button.append(
        create("strong", "", suggestion.label),
        create("span", "", suggestion.question),
      );
      button.addEventListener("click", () => {
        input.value = suggestion.question;
        input.dispatchEvent(new Event("input"));
        input.focus();
      });
      suggestionGroup.append(button);
    }

    const setSelected = (evidenceId) => {
      selectedEvidenceId = evidenceId;
      selected.hidden = evidenceId === null;
      selectedText.textContent =
        evidenceId === null ? "" : `Selected evidence: ${evidenceId}`;
    };

    const openAssistant = (options = {}) => {
      if (
        typeof options.selectedEvidenceId === "string" &&
        EVIDENCE_ID.test(options.selectedEvidenceId)
      ) {
        setSelected(options.selectedEvidenceId);
      }
      if (
        typeof options.question === "string" &&
        options.question.length <= 240
      ) {
        input.value = options.question;
      }
      if (!dialog.open) dialog.showModal();
      launcher.setAttribute("aria-expanded", "true");
      input.focus();
    };

    launcher.addEventListener("click", () => openAssistant());
    close.addEventListener("click", () => dialog.close());
    dialog.addEventListener("close", () => {
      launcher.setAttribute("aria-expanded", "false");
      launcher.focus();
    });
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
    clearSelected.addEventListener("click", () => setSelected(null));
    window.addEventListener("provifact:select-evidence", (event) => {
      if (!(event instanceof CustomEvent) || !isRecord(event.detail)) return;
      openAssistant({
        selectedEvidenceId: event.detail.evidenceId,
        question: event.detail.question,
      });
    });
    window.ProvifactAssistant = { open: openAssistant };

    let status;
    let requestPending = false;
    const updateSubmit = () => {
      const questionLength = input.value.trim().length;
      submit.disabled =
        requestPending ||
        !status ||
        status.narrative_available !== true ||
        questionLength < 4 ||
        questionLength > 240;
    };
    input.addEventListener("input", updateSubmit);
    try {
      status = await statusPromise;
      currentStatus = status;
      runtime.textContent = `${status.data_mode} · ${new Date(status.evidence_timestamp).toLocaleString()} · ${status.source_snapshot_id} · ${status.model_call_available ? `${status.model} available` : status.narrative_mode === "fixture" ? "deterministic fixture" : "model unavailable"}`;
      updateSubmit();
      formStatus.textContent =
        status.narrative_mode === "openai" && status.model_call_available
          ? "A fixed GPT-5.6 model may receive a bounded sanitized evidence subset."
          : status.narrative_mode === "fixture"
            ? "Fixture mode uses useful deterministic answers and makes no model call."
            : "The model is unavailable; the dashboard evidence remains authoritative.";
    } catch {
      runtime.textContent = "Worker runtime unavailable";
      formStatus.textContent =
        "Provifact Assistant is unavailable. No synthetic or model fallback was selected.";
      submit.disabled = true;
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const question = input.value.trim();
      if (!status || question.length < 4 || question.length > 240) return;
      requestPending = true;
      form.dataset.busy = "true";
      updateSubmit();
      formStatus.textContent = "Selecting and verifying bounded evidence…";
      appendMessage("user", question);
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 22_000);
      try {
        const body = {
          page: currentPage(),
          question,
          snapshot_id: status.source_snapshot_id,
          ...(selectedEvidenceId === null
            ? {}
            : { selected_evidence_id: selectedEvidenceId }),
        };
        const { payload, response } = await fetchJson("/api/ask", {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(body),
          signal: controller.signal,
        });
        if (!response.ok) {
          const code = isRecord(payload) ? payload.error : "request_rejected";
          if (response.status === 409) {
            throw new Error(
              "A newer snapshot was published. Use Check for newer published snapshot before asking again.",
            );
          }
          if (response.status === 429) {
            throw new Error(
              "The public assistant rate limit was reached. Try again later.",
            );
          }
          throw new Error(
            code === "assistant_not_configured"
              ? "The model runtime is not configured. No fixture fallback occurred."
              : "The request stopped at an evidence or verification boundary.",
          );
        }
        validateAssistantPayload(payload, status);
        appendMessage(
          "assistant",
          payload.answer.direct_answer,
          payload.answer.evidence_references,
          {
            aiGenerated: payload.answer.ai_generated_analysis,
            limitations: payload.answer.limitations,
            additionalEvidence: payload.answer.additional_evidence_required,
            reviewQuestions: payload.answer.suggested_human_review_questions,
          },
        );
        history.push({
          question,
          answer: payload.answer.direct_answer,
          references: payload.answer.evidence_references,
          analysis: {
            aiGenerated: payload.answer.ai_generated_analysis,
            limitations: payload.answer.limitations,
            additionalEvidence: payload.answer.additional_evidence_required,
            reviewQuestions: payload.answer.suggested_human_review_questions,
          },
        });
        history = history.slice(-MAX_HISTORY);
        writeHistory(history);
        formStatus.textContent = `${payload.mode === "openai" ? "GPT-5.6 explanation" : "Deterministic fixture answer"} · deterministic claims and references verified · generated prose quarantined · human review required`;
        input.value = "";
      } catch (error) {
        const message =
          error instanceof DOMException && error.name === "AbortError"
            ? "The assistant timed out safely. No retry or fallback was performed."
            : error instanceof Error
              ? error.message
              : "The assistant request failed safely.";
        appendMessage("assistant", message);
        formStatus.textContent = message;
      } finally {
        window.clearTimeout(timeout);
        requestPending = false;
        delete form.dataset.busy;
        updateSubmit();
      }
    });
  };

  void renderProvenance();
  void renderAssistant();
})();
