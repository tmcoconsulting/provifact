(() => {
  "use strict";

  const root = document.querySelector("[data-provifact-runtime]");
  if (!(root instanceof HTMLElement)) {
    return;
  }

  const statusElement = root.querySelector("[data-runtime-status]");
  const detailElement = root.querySelector("[data-runtime-detail]");
  const action = root.querySelector("[data-generate-narrative]");
  const output = root.querySelector("[data-narrative-output]");
  if (
    !(statusElement instanceof HTMLElement) ||
    !(detailElement instanceof HTMLElement) ||
    !(action instanceof HTMLButtonElement) ||
    !(output instanceof HTMLElement)
  ) {
    return;
  }

  let runtimeMode = "unavailable";

  const setStatus = (label, detail, state) => {
    statusElement.textContent = label;
    detailElement.textContent = detail;
    root.dataset.runtimeState = state;
  };

  const appendLine = (container, label, value) => {
    const paragraph = document.createElement("p");
    const strong = document.createElement("strong");
    strong.textContent = `${label}: `;
    paragraph.append(strong, document.createTextNode(value));
    container.append(paragraph);
  };

  const renderNarrative = (payload) => {
    output.replaceChildren();
    const mode =
      payload.mode === "openai" ? "OpenAI model" : "deterministic fixture";
    appendLine(output, "Execution", mode);
    appendLine(
      output,
      "Model call performed",
      payload.ai_model_call_performed === true ? "yes" : "no",
    );
    appendLine(
      output,
      "Generated summary",
      payload.narrative.executive_summary,
    );
    appendLine(
      output,
      "Typed deterministic claims accepted",
      String(payload.verification.accepted_claims.length),
    );
    appendLine(
      output,
      "Generated prose quarantined",
      String(payload.verification.rejected_claims.length),
    );
    appendLine(output, "Human review", "required");
    output.hidden = false;
  };

  const renderError = (message) => {
    output.replaceChildren();
    appendLine(output, "Request not completed", message);
    output.hidden = false;
  };

  const loadStatus = async () => {
    try {
      const response = await fetch("/api/status", {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      });
      if (
        !response.ok ||
        !response.headers.get("Content-Type")?.includes("application/json")
      ) {
        throw new Error("Worker API is not attached to this static build");
      }
      const status = await response.json();
      if (
        status.status !== "ok" ||
        !["fixture", "openai"].includes(status.narrative_mode)
      ) {
        throw new Error("Worker reported an unsupported runtime state");
      }
      runtimeMode = status.narrative_mode;
      const label =
        runtimeMode === "fixture"
          ? "Fixture runtime ready"
          : status.narrative_available === true
            ? "OpenAI runtime ready"
            : "OpenAI runtime unavailable";
      const detail =
        runtimeMode === "fixture"
          ? "The Worker will return the tracked deterministic narrative without an API charge."
          : status.narrative_available === true
            ? "The Worker may call the configured Provifact model after all publication gates pass."
            : "The Worker has no usable server-side model credential and will not fall back to fixture output.";
      setStatus(
        label,
        detail,
        status.narrative_available === true ? runtimeMode : "unavailable",
      );
      action.disabled = status.narrative_available !== true;
      action.textContent =
        runtimeMode === "fixture"
          ? "Run bounded fixture narrative"
          : status.narrative_available === true
            ? "Generate bounded narrative"
            : "Narrative unavailable";
    } catch {
      runtimeMode = "unavailable";
      setStatus(
        "Static artifact only",
        "No Worker API is attached. The tracked evidence and narrative below remain available for review.",
        "static",
      );
      action.disabled = true;
    }
  };

  action.addEventListener("click", async () => {
    if (runtimeMode === "unavailable") {
      return;
    }
    action.disabled = true;
    output.hidden = true;
    setStatus(
      "Validating evidence",
      "The Worker is applying the public-package boundary.",
      "busy",
    );
    try {
      const evidenceResponse = await fetch(
        "/assets/data/phase1-public-evidence.json",
        {
          headers: { Accept: "application/json" },
          credentials: "same-origin",
        },
      );
      if (!evidenceResponse.ok) {
        throw new Error("The synthetic package could not be loaded");
      }
      const evidence = await evidenceResponse.json();
      const response = await fetch("/api/narrative", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(evidence),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(
          typeof payload.message === "string"
            ? payload.message
            : "Narrative request was rejected",
        );
      }
      renderNarrative(payload);
      setStatus(
        "Verification complete",
        "Typed claims were checked; generated prose remains subject to human review.",
        "complete",
      );
    } catch (error) {
      renderError(
        error instanceof Error
          ? error.message
          : "The narrative request failed safely",
      );
      setStatus(
        "Request stopped safely",
        "No fallback or publication occurred.",
        "error",
      );
    } finally {
      action.disabled = false;
    }
  });

  void loadStatus();
})();
