from pathlib import Path
from typing import Any

import httpx
import pytest
from streamlit.testing.v1 import AppTest

from price_pack_copilot.models import Catalog, ComparisonRequest
from price_pack_copilot.services.simulator import compare_scenarios


def test_api_unavailable_is_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(*args: Any, **kwargs: Any) -> httpx.Response:
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx.Client, "get", unavailable)
    app = AppTest.from_file(Path("src/price_pack_copilot/frontend.py").resolve(), default_timeout=60).run()
    assert not app.exception
    assert "Cannot load calibration" in app.error[0].value


def test_ui_displays_losses_refusals_and_assumptions(catalog: Catalog, monkeypatch: pytest.MonkeyPatch) -> None:
    def get_catalog(self: httpx.Client, path: str) -> httpx.Response:
        return httpx.Response(
            200, json=catalog.model_dump(mode="json"), request=httpx.Request("GET", "http://test/catalog")
        )

    def post_comparison(self: httpx.Client, path: str, json: dict[str, Any]) -> httpx.Response:
        result = compare_scenarios(ComparisonRequest.model_validate(json), catalog, 200)
        return httpx.Response(
            200, json=result.model_dump(mode="json"), request=httpx.Request("POST", "http://test/scenarios/compare")
        )

    monkeypatch.setattr(httpx.Client, "get", get_catalog)
    monkeypatch.setattr(httpx.Client, "post", post_comparison)
    app = AppTest.from_file(Path("src/price_pack_copilot/frontend.py").resolve(), default_timeout=60).run()
    app.text_input[0].input("9, 11, 15")
    app.button[0].click().run()
    assert not app.exception
    rows = app.dataframe[0].value
    assert len(rows) == 4
    assert rows.iloc[1]["gross_profit_delta"] < 0
    assert rows.iloc[3]["status"] == "refused"
    assert app.expander[0].label == "Assumptions and calibration"
