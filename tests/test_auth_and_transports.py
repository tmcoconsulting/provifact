from __future__ import annotations

import io
import time
import urllib.error
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from email.message import Message
from threading import Event
from types import SimpleNamespace

import pytest

from evidenceops.domain import JsonValue
from evidenceops.narrative.openai import (
    MAX_RESPONSE_BYTES,
    NarrativeGenerationError,
    OpenAIResponsesTransport,
    _extract_structured_output,
)
from evidenceops.providers import (
    DeviceCodeTokenProvider,
    EnvironmentTokenProvider,
    GraphErrorCategory,
    GraphProviderError,
    HttpsGraphTransport,
    TokenAcquisitionError,
)


class FakeOpenAIResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> FakeOpenAIResponse:
        return self

    def __exit__(self, *args: object) -> None:
        del args

    def read(self, limit: int) -> bytes:
        return self.body[:limit]


def test_openai_http_transport_success_and_key_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[tuple[object, float]] = []

    def fake_urlopen(request: object, *, timeout: float, context: object) -> FakeOpenAIResponse:
        assert context is not None
        captured.append((request, timeout))
        return FakeOpenAIResponse(b'{"output": []}')

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = OpenAIResponsesTransport(timeout_seconds=4).create(
        api_key="test-key", request={"model": "fixture"}
    )
    request = captured[0][0]
    assert result == {"output": []}
    assert captured[0][1] == 4
    assert request.get_method() == "POST"  # type: ignore[attr-defined]
    assert request.get_header("Authorization") == "Bearer test-key"  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (b"not-json", "not valid JSON"),
        (b"[]", "not an object"),
        (b"{" + (b"x" * MAX_RESPONSE_BYTES) + b"}", "size limit"),
    ],
)
def test_openai_http_transport_rejects_bad_responses(
    body: bytes, message: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: FakeOpenAIResponse(body))
    with pytest.raises(NarrativeGenerationError, match=message):
        OpenAIResponsesTransport().create(api_key="test-key", request={"model": "fixture"})


def test_openai_http_transport_suppresses_http_body_and_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = urllib.error.HTTPError(
        "https://api.openai.com/v1/responses",
        429,
        "sensitive-body-not-safe",
        Message(),
        io.BytesIO(b"private-response"),
    )
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(error)
    )
    with pytest.raises(NarrativeGenerationError) as caught:
        OpenAIResponsesTransport().create(api_key="test-key", request={})
    assert "429" in str(caught.value)
    assert "private-response" not in str(caught.value)

    network_error = urllib.error.URLError("private-network-detail")
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(network_error)
    )
    with pytest.raises(NarrativeGenerationError, match="request failed"):
        OpenAIResponsesTransport().create(api_key="test-key", request={})


def test_openai_http_transport_reports_only_safe_error_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = urllib.error.HTTPError(
        "https://api.openai.com/v1/responses",
        429,
        "sensitive-body-not-safe",
        Message(),
        io.BytesIO(b'{"error":{"code":"insufficient_quota","message":"private billing detail"}}'),
    )
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(error)
    )
    with pytest.raises(NarrativeGenerationError) as caught:
        OpenAIResponsesTransport().create(api_key="test-key", request={})
    assert "insufficient_quota" in str(caught.value)
    assert "private billing detail" not in str(caught.value)


def test_openai_http_transport_requires_key() -> None:
    with pytest.raises(NarrativeGenerationError, match="key is required"):
        OpenAIResponsesTransport().create(api_key="", request={})


@pytest.mark.parametrize(
    "response",
    [
        {},
        {"output": [1, {"type": "message", "content": "wrong"}]},
        {"output": [{"type": "message", "content": [1, {"type": "other"}]}]},
        {"output": [{"type": "message", "content": [{"type": "output_text", "text": "[1]"}]}]},
    ],
)
def test_structured_output_parser_fails_closed(response: dict[str, JsonValue]) -> None:
    with pytest.raises(NarrativeGenerationError):
        _extract_structured_output(response)


def test_structured_output_parser_handles_refusal_and_invalid_json() -> None:
    with pytest.raises(NarrativeGenerationError, match="refused"):
        _extract_structured_output(
            {"output": [{"type": "message", "content": [{"type": "refusal"}]}]}
        )
    with pytest.raises(NarrativeGenerationError, match="not valid JSON"):
        _extract_structured_output(
            {
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "not-json"}],
                    }
                ]
            }
        )


class FakeMsalApplication:
    def __init__(self, flow: dict[str, object], result: dict[str, object]) -> None:
        self.flow = flow
        self.result = result
        self.scopes: list[str] = []

    def initiate_device_flow(self, *, scopes: list[str]) -> dict[str, object]:
        self.scopes = scopes
        return self.flow

    def acquire_token_by_device_flow(self, flow: dict[str, object]) -> dict[str, object]:
        assert flow == self.flow
        return self.result


class BlockingFakeMsalApplication(FakeMsalApplication):
    def __init__(self, flow: dict[str, object], result: dict[str, object]) -> None:
        super().__init__(flow, result)
        self.started = Event()
        self.release = Event()
        self.acquire_calls = 0

    def acquire_token_by_device_flow(self, flow: dict[str, object]) -> dict[str, object]:
        self.acquire_calls += 1
        self.started.set()
        if not self.release.wait(timeout=2):
            raise AssertionError("test device-code acquisition was not released")
        return super().acquire_token_by_device_flow(flow)


def _install_fake_msal(
    monkeypatch: pytest.MonkeyPatch, application: FakeMsalApplication
) -> list[tuple[object, object, object]]:
    calls: list[tuple[object, object, object]] = []

    def factory(
        client_id: object, *, authority: object, token_cache: object
    ) -> FakeMsalApplication:
        calls.append((client_id, authority, token_cache))
        return application

    module = SimpleNamespace(PublicClientApplication=factory)
    monkeypatch.setattr("importlib.import_module", lambda name: module)
    return calls


def test_device_code_provider_uses_memory_and_caches_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FakeMsalApplication(
        {"user_code": "SAFE-CODE", "verification_uri": "https://microsoft.com/devicelogin"},
        {"access_token": "short-lived-test-token"},
    )
    calls = _install_fake_msal(monkeypatch, app)
    prompts: list[str] = []
    provider = DeviceCodeTokenProvider(
        tenant_id="tenant-placeholder", client_id="client-placeholder", prompt=prompts.append
    )
    assert provider.get_token() == "short-lived-test-token"
    assert provider.get_token() == "short-lived-test-token"
    assert len(calls) == 1
    assert calls[0][2] is None
    assert app.scopes == ["https://graph.microsoft.com/DeviceManagementConfiguration.Read.All"]
    assert "SAFE-CODE" in prompts[0]


def test_device_code_provider_serializes_concurrent_token_acquisition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = BlockingFakeMsalApplication(
        {"user_code": "SAFE-CODE", "verification_uri": "https://microsoft.com/devicelogin"},
        {"access_token": "short-lived-test-token"},
    )
    calls = _install_fake_msal(monkeypatch, app)
    prompts: list[str] = []
    provider = DeviceCodeTokenProvider(
        tenant_id="tenant-placeholder", client_id="client-placeholder", prompt=prompts.append
    )
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(provider.get_token)]
        assert app.started.wait(timeout=1)
        futures.extend(pool.submit(provider.get_token) for _ in range(3))
        time.sleep(0.05)
        assert app.acquire_calls == 1
        app.release.set()
        assert [future.result(timeout=1) for future in futures] == ["short-lived-test-token"] * 4
    assert len(calls) == 1
    assert len(prompts) == 1


@pytest.mark.parametrize(
    ("flow", "result", "message"),
    [
        ({}, {}, "did not start"),
        (
            {"user_code": "SAFE", "verification_uri_complete": "https://microsoft.com/device"},
            {"error": "authorization_pending"},
            "authorization_pending",
        ),
    ],
)
def test_device_code_provider_reports_safe_failures(
    flow: dict[str, object],
    result: dict[str, object],
    message: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_msal(monkeypatch, FakeMsalApplication(flow, result))
    provider = DeviceCodeTokenProvider(
        tenant_id="tenant", client_id="client", prompt=lambda _: None
    )
    with pytest.raises(TokenAcquisitionError, match=message):
        provider.get_token()


def test_token_provider_constructor_and_missing_dependency_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="tenant_id"):
        DeviceCodeTokenProvider(tenant_id="", client_id="client")
    with pytest.raises(ValueError, match="non-empty token"):
        EnvironmentTokenProvider("")

    def missing(name: str) -> object:
        del name
        raise ModuleNotFoundError

    monkeypatch.setattr("importlib.import_module", missing)
    with pytest.raises(TokenAcquisitionError, match="optional dependency"):
        DeviceCodeTokenProvider(tenant_id="tenant", client_id="client").get_token()


class FakeHttpResponse:
    status = 200

    def __init__(self, body: bytes) -> None:
        self.body = body

    def read(self, limit: int) -> bytes:
        return self.body[:limit]

    def getheaders(self) -> list[tuple[str, str]]:
        return [("Retry-After", "2")]


class FakeConnection:
    instances: list[FakeConnection] = []
    body = b'{"value": []}'
    fail = False

    def __init__(self, host: str, *, timeout: float) -> None:
        self.host = host
        self.timeout = timeout
        self.request_data: tuple[str, str, Mapping[str, str]] | None = None
        self.closed = False
        self.__class__.instances.append(self)

    def request(self, method: str, target: str, *, headers: Mapping[str, str]) -> None:
        if self.fail:
            raise OSError("private transport detail")
        self.request_data = (method, target, headers)

    def getresponse(self) -> FakeHttpResponse:
        return FakeHttpResponse(self.body)

    def close(self) -> None:
        self.closed = True


def test_https_graph_transport_is_get_only_and_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeConnection.instances.clear()
    FakeConnection.body = b'{"value": []}'
    FakeConnection.fail = False
    monkeypatch.setattr("http.client.HTTPSConnection", FakeConnection)
    result = HttpsGraphTransport().get(
        "https://graph.microsoft.com/v1.0/items?$top=1",
        headers={"Accept": "application/json"},
        timeout_seconds=3,
    )
    connection = FakeConnection.instances[0]
    assert result.status_code == 200
    assert result.headers == {"retry-after": "2"}
    assert connection.request_data == (
        "GET",
        "/v1.0/items?$top=1",
        {"Accept": "application/json"},
    )
    assert connection.closed is True


def test_https_graph_transport_rejects_url_size_and_transport_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(GraphProviderError) as caught:
        HttpsGraphTransport().get(
            "http://graph.microsoft.com/v1.0/items", headers={}, timeout_seconds=1
        )
    assert caught.value.category is GraphErrorCategory.TRANSPORT

    monkeypatch.setattr("http.client.HTTPSConnection", FakeConnection)
    FakeConnection.body = b"x" * 4_000_001
    with pytest.raises(GraphProviderError) as caught:
        HttpsGraphTransport().get(
            "https://graph.microsoft.com/v1.0/items", headers={}, timeout_seconds=1
        )
    assert caught.value.category is GraphErrorCategory.MALFORMED_RESPONSE

    FakeConnection.body = b"{}"
    FakeConnection.fail = True
    with pytest.raises(GraphProviderError) as caught:
        HttpsGraphTransport().get(
            "https://graph.microsoft.com/v1.0/items", headers={}, timeout_seconds=1
        )
    assert caught.value.category is GraphErrorCategory.TRANSPORT
    assert "private transport detail" not in str(caught.value)
    FakeConnection.fail = False
