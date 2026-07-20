"""Opt-in OpenAI Responses API adapter for sanitized evidence only."""

from __future__ import annotations

import importlib
import json
import ssl
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol, cast

from evidenceops.domain import (
    EvidenceObject,
    JsonValue,
    canonical_json,
    make_evidence_object,
    validate_evidence_object,
)
from evidenceops.sanitization import SensitiveValueError, assert_public_safe

DEFAULT_OPENAI_MODEL: Final = "gpt-5.6-terra"
RESPONSES_ENDPOINT: Final = "https://api.openai.com/v1/responses"
MAX_PACKAGE_BYTES: Final = 64 * 1024
MAX_RESPONSE_BYTES: Final = 256 * 1024
MODEL_OUTPUT_SCHEMA_PATH: Final = Path(__file__).with_name("narrative-model-output.schema.json")


class NarrativeGenerationError(ValueError):
    """Raised without exposing API response bodies or credentials."""


class ResponsesTransport(Protocol):
    """Small injectable boundary used by the live adapter and contract tests."""

    def create(self, *, api_key: str, request: dict[str, JsonValue]) -> dict[str, JsonValue]:
        """Create one response without persisting credentials or request bodies."""


@dataclass(frozen=True, slots=True)
class OpenAIResponsesTransport:
    """Standard-library HTTPS transport with a bounded response and timeout."""

    timeout_seconds: float = 20.0

    def create(self, *, api_key: str, request: dict[str, JsonValue]) -> dict[str, JsonValue]:
        if not api_key:
            raise NarrativeGenerationError("an OpenAI API key is required for opt-in generation")
        body = canonical_json(request).encode("utf-8")
        http_request = urllib.request.Request(  # noqa: S310 - constant HTTPS endpoint
            RESPONSES_ENDPOINT,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(  # noqa: S310  # nosec B310
                http_request,
                timeout=self.timeout_seconds,
                context=_tls_context(),
            ) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            safe_code = _safe_api_error_code(exc.read(64 * 1024))
            code_suffix = f" ({safe_code})" if safe_code is not None else ""
            raise NarrativeGenerationError(
                f"OpenAI Responses API returned HTTP {exc.code}{code_suffix}; "
                "response content was suppressed"
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise NarrativeGenerationError("OpenAI Responses API request failed") from exc
        if len(raw) > MAX_RESPONSE_BYTES:
            raise NarrativeGenerationError("OpenAI response exceeded the size limit")
        try:
            parsed = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise NarrativeGenerationError("OpenAI response was not valid JSON") from exc
        if not isinstance(parsed, dict) or not all(isinstance(key, str) for key in parsed):
            raise NarrativeGenerationError("OpenAI response was not an object")
        return cast(dict[str, JsonValue], parsed)


def _tls_context() -> ssl.SSLContext:
    """Use an installed pinned CA bundle, otherwise the platform trust store."""
    try:
        certifi = importlib.import_module("certifi")
    except ModuleNotFoundError:
        return ssl.create_default_context()
    where = cast(Callable[[], str], certifi.__dict__["where"])
    return ssl.create_default_context(cafile=where())


def _safe_api_error_code(body: bytes) -> str | None:
    try:
        decoded = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(decoded, dict) or not isinstance(decoded.get("error"), dict):
        return None
    error = cast(dict[str, object], decoded["error"])
    for field in ("code", "type"):
        value = error.get(field)
        if isinstance(value, str) and 0 < len(value) <= 100:
            return value
    return None


@dataclass(frozen=True, slots=True)
class OpenAINarrativeAdapter:
    """Generate a strict narrative from one sanitized public package."""

    transport: ResponsesTransport
    model: str = DEFAULT_OPENAI_MODEL

    def generate(self, package: EvidenceObject, *, api_key: str) -> EvidenceObject:
        public = validate_evidence_object(package)
        if public["object_type"] != "sanitized_public_evidence_package":
            raise NarrativeGenerationError("only a sanitized public package may reach OpenAI")
        try:
            assert_public_safe(public)
        except SensitiveValueError as exc:
            raise NarrativeGenerationError(
                "sanitized evidence package failed the pre-model credential and content scan"
            ) from exc
        serialized = canonical_json(public)
        if len(serialized.encode("utf-8")) > MAX_PACKAGE_BYTES:
            raise NarrativeGenerationError("sanitized evidence package exceeds the input limit")
        request = self._request(public, serialized)
        response = self.transport.create(api_key=api_key, request=request)
        model_output = _extract_structured_output(response)
        model_output["model"] = self.model
        model_output["source_package_evidence_id"] = public["evidence_id"]
        model_output["ai_generated_analysis"] = True
        model_output["human_review_required"] = True
        try:
            return make_evidence_object("generated_narrative", model_output)
        except (TypeError, ValueError) as exc:
            raise NarrativeGenerationError("model output failed the narrative schema") from exc

    def _request(self, package: EvidenceObject, serialized: str) -> dict[str, JsonValue]:
        del package
        return {
            "model": self.model,
            "store": False,
            "max_output_tokens": 1600,
            "reasoning": {"effort": "low"},
            "instructions": (
                "Produce evidence-grounded analysis only. Preserve every deterministic status. "
                "Do not declare compliance, certification, control satisfaction, an exception, or "
                "remediation. Emit exactly one explanation for each unique supplied finding ID. "
                "Use only the finding_status claim code and copy its claim value exactly from the "
                "deterministic finding. Cite only supplied evidence IDs. State limitations and "
                "human-review questions. All prose is AI-generated analysis subject to human "
                "review."
            ),
            "input": (
                "Create the bounded narrative from this sanitized Provifact package:\n" + serialized
            ),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "provifact_narrative_v1",
                    "strict": True,
                    "schema": _model_output_schema(),
                }
            },
        }


def _model_output_schema() -> dict[str, JsonValue]:
    try:
        loaded = json.loads(MODEL_OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NarrativeGenerationError("narrative model-output schema could not be loaded") from exc
    if not isinstance(loaded, dict) or not all(isinstance(key, str) for key in loaded):
        raise NarrativeGenerationError("narrative model-output schema was not an object")
    return cast(dict[str, JsonValue], loaded)


def _extract_structured_output(response: dict[str, JsonValue]) -> dict[str, JsonValue]:
    output = response.get("output")
    if not isinstance(output, list):
        raise NarrativeGenerationError("OpenAI response did not contain structured output")
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "refusal":
                raise NarrativeGenerationError("OpenAI refused narrative generation")
            if part.get("type") != "output_text" or not isinstance(part.get("text"), str):
                continue
            try:
                parsed = json.loads(cast(str, part["text"]))
            except json.JSONDecodeError as exc:
                raise NarrativeGenerationError("structured output text was not valid JSON") from exc
            if not isinstance(parsed, dict) or not all(isinstance(key, str) for key in parsed):
                raise NarrativeGenerationError("structured model output was not an object")
            return cast(dict[str, JsonValue], parsed)
    raise NarrativeGenerationError("OpenAI response did not contain an output_text item")
