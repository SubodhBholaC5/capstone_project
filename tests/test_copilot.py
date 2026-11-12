import json

import httpx
import pytest

from price_pack_copilot.config import Settings
from price_pack_copilot.models import Catalog
from price_pack_copilot.services.copilot import answer_question


def test_missing_credentials_fail(catalog: Catalog, settings: Settings) -> None:
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        answer_question("Compare prices", catalog, settings)


def test_tool_roundtrip_executes_python_and_returns_all_outputs(
    catalog: Catalog, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings["openai_api_key"] = "test-key"
    settings["openai_model"] = "test-model"
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        requests.append(payload)
        if len(requests) == 1:
            assert payload["tools"][0]["strict"] is True
            return httpx.Response(
                200,
                json={
                    "status": "completed",
                    "output": [
                        {
                            "type": "function_call",
                            "name": "compare_scenarios",
                            "call_id": "call-1",
                            "arguments": json.dumps(
                                {"scenarios": [{"label": "Low", "product_id": "demo_330ml_6pk", "price": 9}]}
                            ),
                        }
                    ],
                },
            )
        output = json.loads(payload["input"][-1]["output"])
        assert output["scenarios"][0]["gross_profit_delta"] < 0
        assert output["assumptions"]
        assert payload["tool_choice"] == "none"
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": "This candidate loses gross profit versus baseline."}
                        ],
                    }
                ],
            },
        )

    original_client = httpx.Client
    monkeypatch.setattr(
        "price_pack_copilot.services.copilot.httpx.Client",
        lambda **kwargs: original_client(transport=httpx.MockTransport(respond), **kwargs),
    )
    result = answer_question("Compare demo_330ml_6pk at 9", catalog, settings)
    assert len(requests) == 2
    assert result.comparison.scenarios[0].status == "accepted"
    assert "loses" in result.explanation
