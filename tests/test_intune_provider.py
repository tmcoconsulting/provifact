from __future__ import annotations

import inspect
import json
from collections import defaultdict, deque
from collections.abc import Mapping
from typing import cast

import pytest

from evidenceops.domain import JsonValue, validate_evidence_object
from evidenceops.providers import (
    EnvironmentTokenProvider,
    GraphClient,
    GraphErrorCategory,
    GraphProviderError,
    HttpResponse,
    IntuneProvider,
)
from evidenceops.providers import intune as intune_module

POLICY_ID = "11111111-2222-4333-8444-555555555555"
ROOT = "https://graph.microsoft.com/v1.0/deviceManagement/deviceConfigurations"
ASSIGNMENTS = f"{ROOT}/{POLICY_ID}/assignments"


def _response(status: int, body: object, **headers: str) -> HttpResponse:
    return HttpResponse(status, headers, json.dumps(body).encode())


class FakeTransport:
    def __init__(self, responses: Mapping[str, list[HttpResponse]]) -> None:
        self.responses = {url: deque(items) for url, items in responses.items()}
        self.calls: list[tuple[str, Mapping[str, str], float]] = []

    def get(self, url: str, *, headers: Mapping[str, str], timeout_seconds: float) -> HttpResponse:
        self.calls.append((url, headers, timeout_seconds))
        return self.responses[url].popleft()


def _client(
    responses: Mapping[str, list[HttpResponse]], *, sleeps: list[float] | None = None
) -> tuple[GraphClient, FakeTransport]:
    transport = FakeTransport(responses)
    recorded_sleeps = sleeps if sleeps is not None else []
    client = GraphClient(
        token_provider=EnvironmentTokenProvider("synthetic-access-token"),
        transport=transport,
        timeout_seconds=7,
        sleeper=recorded_sleeps.append,
    )
    return client, transport


def _mac_policy(**updates: JsonValue) -> dict[str, JsonValue]:
    policy: dict[str, JsonValue] = {
        "@odata.type": "#microsoft.graph.macOSGeneralDeviceConfiguration",
        "id": POLICY_ID,
        "lastModifiedDateTime": "2026-07-18T12:00:00-06:00",
        "passwordRequired": True,
        "passwordMinutesOfInactivityBeforeScreenTimeout": 15,
    }
    policy.update(updates)
    return policy


def test_provider_paginates_normalizes_and_discards_assignment_ids() -> None:
    page_two = f"{ROOT}?$skiptoken=opaque"
    client, transport = _client(
        {
            ROOT: [
                _response(
                    200,
                    {
                        "value": [
                            {"@odata.type": "#microsoft.graph.windows10GeneralConfiguration"}
                        ],
                        "@odata.nextLink": page_two,
                    },
                )
            ],
            page_two: [_response(200, {"value": [_mac_policy()]})],
            ASSIGNMENTS: [
                _response(
                    200,
                    {
                        "value": [
                            {
                                "id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
                                "target": {
                                    "@odata.type": "#microsoft.graph.groupAssignmentTarget",
                                    "groupId": "bbbbbbbb-cccc-4ddd-8eee-ffffffffffff",
                                },
                            }
                        ]
                    },
                )
            ],
        }
    )
    result = IntuneProvider(client).collect(
        desired_state_git_commit_sha="a" * 40,
    )

    assert len(result.observations) == 2
    settings = {item["setting_key"]: item["observed_value"] for item in result.observations}
    assert settings == {
        "macos.screen_lock.require_password": True,
        "macos.screen_lock.max_idle_seconds": 900,
    }
    for observation in result.observations:
        validate_evidence_object(observation)
        assert "private_trace" not in observation
    traces = cast(list[dict[str, JsonValue]], result.private_trace["source_objects"])
    assert traces[0]["source_object_id"] == POLICY_ID
    assert traces[0]["assignment_count"] == 1
    assert "groupId" not in json.dumps(traces)
    assert result.private_trace["unsupported_policy_types"] == [
        {"policy_type": "#microsoft.graph.windows10GeneralConfiguration", "count": 1}
    ]
    assert [call[0] for call in transport.calls] == [ROOT, page_two, ASSIGNMENTS]
    assert all(
        call[1]["Authorization"] == "Bearer " + "synthetic-access-token" for call in transport.calls
    )
    assert all(call[2] == 7 for call in transport.calls)


def test_empty_and_unsupported_collections_are_explicit() -> None:
    client, _ = _client({ROOT: [_response(200, {"value": []})]})
    empty = IntuneProvider(client).collect(desired_state_git_commit_sha=None)
    assert empty.observations == ()
    assert empty.private_trace["supported_policy_count"] == 0

    client, _ = _client(
        {
            ROOT: [
                _response(
                    200,
                    {"value": [{"@odata.type": "#microsoft.graph.iosGeneralDeviceConfiguration"}]},
                )
            ]
        }
    )
    unsupported = IntuneProvider(client).collect(desired_state_git_commit_sha=None)
    assert unsupported.observations == ()
    assert unsupported.private_trace["unsupported_policy_types"] == [
        {"policy_type": "#microsoft.graph.iosGeneralDeviceConfiguration", "count": 1}
    ]


@pytest.mark.parametrize(
    ("status", "category"),
    [
        (401, GraphErrorCategory.AUTHENTICATION),
        (403, GraphErrorCategory.AUTHORIZATION),
        (404, GraphErrorCategory.NOT_FOUND),
        (400, GraphErrorCategory.MALFORMED_RESPONSE),
    ],
)
def test_graph_errors_are_structured_and_do_not_echo_response(
    status: int, category: GraphErrorCategory
) -> None:
    sensitive = "private-response-marker"
    client, _ = _client(
        {ROOT: [_response(status, {"error": {"code": "SafeCode", "message": sensitive}})]}
    )
    with pytest.raises(GraphProviderError) as caught:
        client.get_collection("/v1.0/deviceManagement/deviceConfigurations")
    assert caught.value.category is category
    assert caught.value.graph_code == "SafeCode"
    assert sensitive not in str(caught.value)


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_retry_is_bounded_and_honors_retry_after(status: int) -> None:
    sleeps: list[float] = []
    client, transport = _client(
        {
            ROOT: [
                _response(status, {"error": {"code": "Transient"}}, **{"retry-after": "2"}),
                _response(200, {"value": []}),
            ]
        },
        sleeps=sleeps,
    )
    assert client.get_collection("/v1.0/deviceManagement/deviceConfigurations") == []
    assert sleeps == [2.0]
    assert len(transport.calls) == 2


def test_retry_exhaustion_is_reported() -> None:
    client, _ = _client({ROOT: [_response(503, {}), _response(503, {}), _response(503, {})]})
    with pytest.raises(GraphProviderError) as caught:
        client.get_collection("/v1.0/deviceManagement/deviceConfigurations")
    assert caught.value.category is GraphErrorCategory.TRANSIENT


def test_client_rejects_invalid_bounds_and_non_v1_path() -> None:
    with pytest.raises(ValueError, match="positive"):
        GraphClient(token_provider=EnvironmentTokenProvider("token"), timeout_seconds=0)
    client, _ = _client({})
    with pytest.raises(ValueError, match="v1.0"):
        client.get_collection("/beta/deviceManagement/deviceConfigurations")


@pytest.mark.parametrize("retry_after", ["invalid-date", "-5", "999"])
def test_retry_after_fallback_and_bounds(retry_after: str) -> None:
    sleeps: list[float] = []
    client, _ = _client(
        {
            ROOT: [
                _response(429, {}, **{"retry-after": retry_after}),
                _response(200, {"value": []}),
            ]
        },
        sleeps=sleeps,
    )
    client.get_collection("/v1.0/deviceManagement/deviceConfigurations")
    assert 0 <= sleeps[0] <= 60


@pytest.mark.parametrize(
    "body",
    [b"not-json", json.dumps({"wrong": []}).encode(), json.dumps({"value": [1]}).encode()],
)
def test_malformed_collection_response_fails_closed(body: bytes) -> None:
    transport = FakeTransport({ROOT: [HttpResponse(200, {}, body)]})
    client = GraphClient(
        token_provider=EnvironmentTokenProvider("synthetic-access-token"), transport=transport
    )
    with pytest.raises(GraphProviderError, match="malformed_response"):
        client.get_collection("/v1.0/deviceManagement/deviceConfigurations")


def test_response_field_type_change_fails_closed() -> None:
    changed_policy = _mac_policy(passwordRequired="yes")
    client, _ = _client(
        {
            ROOT: [_response(200, {"value": [changed_policy]})],
            ASSIGNMENTS: [_response(200, {"value": []})],
        }
    )
    with pytest.raises(GraphProviderError, match="malformed_response"):
        IntuneProvider(client).collect(desired_state_git_commit_sha=None)


@pytest.mark.parametrize(
    "policy",
    [
        {"id": POLICY_ID},
        _mac_policy(id=None),
        _mac_policy(lastModifiedDateTime="not-a-timestamp"),
        _mac_policy(lastModifiedDateTime="2026-07-18T12:00:00"),
        _mac_policy(passwordMinutesOfInactivityBeforeScreenTimeout=True),
    ],
)
def test_policy_metadata_and_exact_setting_types_fail_closed(
    policy: dict[str, JsonValue],
) -> None:
    client, _ = _client(
        {
            ROOT: [_response(200, {"value": [policy]})],
            ASSIGNMENTS: [_response(200, {"value": []})],
        }
    )
    with pytest.raises(GraphProviderError, match="malformed_response"):
        IntuneProvider(client).collect(desired_state_git_commit_sha=None)


@pytest.mark.parametrize(
    "assignment",
    [{}, {"target": "wrong"}, {"target": {}}, {"target": {"@odata.type": ""}}],
)
def test_assignment_shape_change_fails_closed(assignment: dict[str, JsonValue]) -> None:
    client, _ = _client(
        {
            ROOT: [_response(200, {"value": [_mac_policy()]})],
            ASSIGNMENTS: [_response(200, {"value": [assignment]})],
        }
    )
    with pytest.raises(GraphProviderError, match="malformed_response"):
        IntuneProvider(client).collect(desired_state_git_commit_sha=None)


def test_assignment_404_is_not_silently_ignored() -> None:
    client, _ = _client(
        {
            ROOT: [_response(200, {"value": [_mac_policy()]})],
            ASSIGNMENTS: [_response(404, {"error": {"code": "NotFound"}})],
        }
    )
    with pytest.raises(GraphProviderError) as caught:
        IntuneProvider(client).collect(desired_state_git_commit_sha=None)
    assert caught.value.category is GraphErrorCategory.NOT_FOUND


def test_next_link_must_remain_on_graph_v1() -> None:
    client, _ = _client(
        {
            ROOT: [
                _response(
                    200,
                    {"value": [], "@odata.nextLink": "https://example.invalid/v1.0/data"},
                )
            ]
        }
    )
    with pytest.raises(GraphProviderError, match="malformed_response"):
        client.get_collection("/v1.0/deviceManagement/deviceConfigurations")


def test_duplicate_next_link_is_rejected() -> None:
    client, _ = _client(
        {
            ROOT: [_response(200, {"value": [], "@odata.nextLink": ROOT})],
        }
    )
    with pytest.raises(GraphProviderError, match="malformed_response"):
        client.get_collection("/v1.0/deviceManagement/deviceConfigurations")


def test_provider_contract_contains_only_read_operation() -> None:
    public_methods = {
        name
        for name in dir(IntuneProvider)
        if not name.startswith("_") and callable(getattr(IntuneProvider, name))
    }
    assert public_methods == {"collect"}
    transport_methods = {
        name
        for name in dir(intune_module.GraphTransport)
        if not name.startswith("_") and callable(getattr(intune_module.GraphTransport, name))
    }
    assert transport_methods == {"get"}
    source = inspect.getsource(intune_module)
    verbs: dict[str, int] = defaultdict(int)
    for verb in ("GET", "POST", "PATCH", "PUT", "DELETE"):
        verbs[verb] = source.count(f'connection.request("{verb}"')
    assert verbs == {"GET": 1, "POST": 0, "PATCH": 0, "PUT": 0, "DELETE": 0}
