(() => {
  "use strict";

  const STATUS_URL = "/api/status";
  const MISSION_URL = "/assets/data/mission-control.json";
  const HISTORY_KEY = "provifact-copilot-history-v1";
  const MAX_HISTORY = 12;
  const EVIDENCE_ID = /^(?:finding|req|gap|mission)-[0-9a-f]{24}$/;
  const operationalPaths = new Set([
    "/",
    "/evidence-dashboard/",
    "/settings-matrix/",
    "/live-demo/",
  ]);
  const suggestions = [
    "What requires my attention?",
    "Why is FileVault aligned or drifting?",
    "What changed since the previous collection?",
    "Which finding was resolved?",
    "What is not currently evaluated?",
    "What do the framework cross-references mean?",
    "Is this live tenant data?",
    "What can Provifact not conclude?",
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

  const loadStatus = async (fresh = false) => {
    const suffix = fresh ? `?check=${Date.now()}` : "";
    const { payload, response } = await fetchJson(`${STATUS_URL}${suffix}`);
    if (!response.ok) throw new Error("Worker status is unavailable");
    return validateStatus(payload);
  };

  let statusPromise = loadStatus();
  let currentStatus = null;

  const freshnessState = (status) => {
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
      const state =
        freshness === "stale"
          ? "stale"
          : status.data_mode.startsWith("LIVE")
            ? "live"
            : status.data_mode.startsWith("SYNTHETIC")
              ? "fixture"
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
        "Provifact Copilot",
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
            Array.isArray(item.references),
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

  const renderCopilot = async () => {
    const launcher = create(
      "button",
      "evidence-copilot-launcher",
      "Provifact Copilot",
    );
    launcher.type = "button";
    launcher.setAttribute("aria-haspopup", "dialog");
    launcher.setAttribute("aria-expanded", "false");

    const dialog = create("dialog", "evidence-copilot");
    dialog.id = "evidence-copilot";
    dialog.setAttribute("aria-labelledby", "evidence-copilot-title");
    launcher.setAttribute("aria-controls", dialog.id);

    const header = create("header", "evidence-copilot-header");
    const headingGroup = create("div");
    const eyebrow = create(
      "span",
      "evidence-copilot-eyebrow",
      "Bounded evidence assistant",
    );
    const heading = create("h2", "", "Provifact Copilot");
    heading.id = "evidence-copilot-title";
    const runtime = create(
      "p",
      "evidence-copilot-runtime",
      "Checking runtime…",
    );
    headingGroup.append(eyebrow, heading, runtime);
    const close = create("button", "evidence-copilot-close", "Close");
    close.type = "button";
    close.setAttribute("aria-label", "Close Provifact Copilot");
    header.append(headingGroup, close);

    const selected = create("div", "evidence-copilot-selected");
    selected.hidden = true;
    const selectedText = create("span");
    const clearSelected = create("button", "", "Clear selected evidence");
    clearSelected.type = "button";
    selected.append(selectedText, clearSelected);

    const transcript = create("div", "evidence-copilot-transcript");
    transcript.setAttribute("aria-live", "polite");
    transcript.setAttribute("aria-label", "Provifact Copilot conversation");
    const suggestionGroup = create("div", "evidence-copilot-suggestions");
    suggestionGroup.setAttribute("aria-label", "Suggested evidence questions");

    const form = create("form", "evidence-copilot-form");
    const label = create("label", "", "Ask about the published evidence");
    const input = create("textarea");
    input.name = "question";
    input.rows = 2;
    input.maxLength = 240;
    input.required = true;
    input.placeholder = "What requires my attention?";
    label.append(input);
    const submit = create("button", "", "Ask Provifact Copilot");
    submit.type = "submit";
    submit.disabled = true;
    const formStatus = create("p", "evidence-copilot-form-status");
    formStatus.setAttribute("role", "status");
    form.append(label, submit, formStatus);

    const boundary = create(
      "p",
      "evidence-copilot-boundary",
      "Only the question, page enum, snapshot ID, and optional selected evidence ID are sent. No DOM, tenant identities, or browser API key is sent. Answers remain subject to human review.",
    );
    dialog.append(
      header,
      selected,
      transcript,
      suggestionGroup,
      form,
      boundary,
    );
    document.body.append(launcher, dialog);

    let selectedEvidenceId = null;
    let history = readHistory();

    const appendMessage = (role, text, references = []) => {
      const article = create(
        "article",
        `evidence-copilot-message evidence-copilot-${role}`,
      );
      article.append(
        create("strong", "", role === "user" ? "You" : "Provifact Copilot"),
        create("p", "", text),
      );
      const links = references
        .filter(
          (reference) =>
            typeof reference === "string" && EVIDENCE_ID.test(reference),
        )
        .map((reference) => ({ reference, href: evidenceHref(reference) }))
        .filter((item) => item.href !== null);
      if (links.length) {
        const nav = create("nav", "evidence-copilot-links");
        nav.setAttribute("aria-label", "Evidence references");
        for (const { reference, href } of links) {
          const link = create("a", "", reference);
          link.href = href;
          nav.append(link);
        }
        article.append(nav);
      }
      transcript.append(article);
      transcript.scrollTop = transcript.scrollHeight;
    };

    for (const item of history) {
      appendMessage("user", item.question);
      appendMessage("assistant", item.answer, item.references);
    }

    for (const question of suggestions) {
      const button = create("button", "", question);
      button.type = "button";
      button.addEventListener("click", () => {
        input.value = question;
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

    const openCopilot = (options = {}) => {
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

    launcher.addEventListener("click", () => openCopilot());
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
      openCopilot({
        selectedEvidenceId: event.detail.evidenceId,
        question: event.detail.question,
      });
    });
    window.ProvifactCopilot = { open: openCopilot };

    let status;
    try {
      status = await statusPromise;
      currentStatus = status;
      runtime.textContent = `${status.data_mode} · ${new Date(status.evidence_timestamp).toLocaleString()} · ${status.source_snapshot_id} · ${status.model_call_available ? `${status.model} available` : status.narrative_mode === "fixture" ? "deterministic fixture" : "model unavailable"}`;
      submit.disabled = status.narrative_available !== true;
      formStatus.textContent =
        status.narrative_mode === "openai" && status.model_call_available
          ? "A fixed GPT-5.6 model may receive a bounded sanitized evidence subset."
          : status.narrative_mode === "fixture"
            ? "Fixture mode uses useful deterministic answers and makes no model call."
            : "The model is unavailable; the dashboard evidence remains authoritative.";
    } catch {
      runtime.textContent = "Worker runtime unavailable";
      formStatus.textContent =
        "Provifact Copilot is unavailable. No synthetic or model fallback was selected.";
      submit.disabled = true;
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const question = input.value.trim();
      if (!status || question.length < 4 || question.length > 240) return;
      submit.disabled = true;
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
        if (
          !isRecord(payload) ||
          !isRecord(payload.answer) ||
          !isRecord(payload.verification) ||
          !["typed_claims_verified", "insufficient_evidence"].includes(
            payload.verification.status,
          ) ||
          typeof payload.answer.direct_answer !== "string" ||
          !Array.isArray(payload.answer.evidence_references)
        ) {
          throw new Error(
            "The answer failed deterministic browser verification.",
          );
        }
        appendMessage(
          "assistant",
          payload.answer.direct_answer,
          payload.answer.evidence_references,
        );
        history.push({
          question,
          answer: payload.answer.direct_answer,
          references: payload.answer.evidence_references,
        });
        history = history.slice(-MAX_HISTORY);
        writeHistory(history);
        formStatus.textContent = `${payload.mode === "openai" ? "GPT-5.6 answer" : "Deterministic fixture answer"} · typed claims verified · prose subject to human review`;
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
        submit.disabled = status.narrative_available !== true;
      }
    });
  };

  void renderProvenance();
  void renderCopilot();
})();
