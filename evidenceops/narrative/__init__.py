"""Constrained narrative generation and deterministic verification."""

from evidenceops.narrative.offline import build_offline_narrative
from evidenceops.narrative.openai import (
    DEFAULT_OPENAI_MODEL,
    NarrativeGenerationError,
    OpenAINarrativeAdapter,
    OpenAIResponsesTransport,
)
from evidenceops.narrative.verifier import VERIFIER_VERSION, verify_narrative

__all__ = [
    "DEFAULT_OPENAI_MODEL",
    "VERIFIER_VERSION",
    "NarrativeGenerationError",
    "OpenAINarrativeAdapter",
    "OpenAIResponsesTransport",
    "build_offline_narrative",
    "verify_narrative",
]
