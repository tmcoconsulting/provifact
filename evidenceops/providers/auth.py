"""Pluggable token acquisition that never persists credentials."""

from __future__ import annotations

import importlib
from collections.abc import Callable, Sequence
from threading import Lock
from typing import Final, Protocol, cast

DEFAULT_DELEGATED_SCOPES: Final = (
    "https://graph.microsoft.com/DeviceManagementConfiguration.Read.All",
)


class TokenAcquisitionError(RuntimeError):
    """Raised without embedding access tokens or identity-provider response bodies."""


class TokenProvider(Protocol):
    """Return a short-lived bearer token held only by the current process."""

    def get_token(self) -> str:
        """Acquire a token without writing it to disk."""
        ...


class _MsalPublicClient(Protocol):
    def initiate_device_flow(self, *, scopes: list[str]) -> dict[str, object]: ...

    def acquire_token_by_device_flow(self, flow: dict[str, object]) -> dict[str, object]: ...


class DeviceCodeTokenProvider:
    """Attended delegated authentication backed by MSAL's in-memory default cache."""

    def __init__(
        self,
        *,
        tenant_id: str,
        client_id: str,
        scopes: Sequence[str] = DEFAULT_DELEGATED_SCOPES,
        prompt: Callable[[str], None] = print,
    ) -> None:
        if not tenant_id or not client_id or not scopes:
            raise ValueError("tenant_id, client_id, and scopes are required")
        if any(
            not scope.startswith("https://graph.microsoft.com/")
            or not scope.endswith(".Read.All")
            or "ReadWrite" in scope
            for scope in scopes
        ):
            raise ValueError("device-code scopes must be explicit Microsoft Graph read scopes")
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._prompt = prompt
        self._scopes = tuple(dict.fromkeys(scopes))
        self._token: str | None = None
        self._acquisition_lock = Lock()

    def get_token(self) -> str:
        """Run a device-code flow once and retain the token only in process memory."""
        if self._token is not None:
            return self._token
        with self._acquisition_lock:
            if self._token is not None:
                return self._token
            self._token = self._acquire_token()
            return self._token

    def _acquire_token(self) -> str:
        """Acquire exactly one token while the caller holds the process-local lock."""
        try:
            msal = importlib.import_module("msal")
        except ModuleNotFoundError as exc:
            raise TokenAcquisitionError(
                "live Intune collection requires the exact-pinned 'live' optional dependency"
            ) from exc
        factory = cast(Callable[..., _MsalPublicClient], msal.__dict__["PublicClientApplication"])
        application = factory(
            self._client_id,
            authority=f"https://login.microsoftonline.com/{self._tenant_id}",
            token_cache=None,
        )
        flow = application.initiate_device_flow(scopes=list(self._scopes))
        user_code = flow.get("user_code")
        verification_uri = flow.get("verification_uri") or flow.get("verification_uri_complete")
        if not isinstance(user_code, str) or not isinstance(verification_uri, str):
            raise TokenAcquisitionError(
                "Microsoft identity platform did not start device-code flow"
            )
        self._prompt(f"Open {verification_uri} and enter the one-time code: {user_code}")
        result = application.acquire_token_by_device_flow(flow)
        token = result.get("access_token")
        if not isinstance(token, str) or not token:
            error = result.get("error")
            safe_error = error if isinstance(error, str) else "unknown_error"
            raise TokenAcquisitionError(f"device-code authentication failed: {safe_error}")
        return token


class EnvironmentTokenProvider:
    """Read a short-lived externally acquired token from process memory."""

    def __init__(self, token: str) -> None:
        if not token:
            raise ValueError("a non-empty token is required")
        self._token = token

    def get_token(self) -> str:
        return self._token
