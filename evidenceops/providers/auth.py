"""Pluggable token acquisition that never persists credentials."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Protocol, cast


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
        prompt: Callable[[str], None] = print,
    ) -> None:
        if not tenant_id or not client_id:
            raise ValueError("tenant_id and client_id are required")
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._prompt = prompt
        self._token: str | None = None

    def get_token(self) -> str:
        """Run a device-code flow once and retain the token only in process memory."""
        if self._token is not None:
            return self._token
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
        scopes = ["https://graph.microsoft.com/DeviceManagementConfiguration.Read.All"]
        flow = application.initiate_device_flow(scopes=scopes)
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
        self._token = token
        return token


class EnvironmentTokenProvider:
    """Read a short-lived externally acquired token from process memory."""

    def __init__(self, token: str) -> None:
        if not token:
            raise ValueError("a non-empty token is required")
        self._token = token

    def get_token(self) -> str:
        return self._token
