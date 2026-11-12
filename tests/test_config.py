import pytest

from price_pack_copilot.config import load_settings


def test_environment_overrides_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PPA_API_URL", "http://localhost:8001")
    assert load_settings(".env.example")["api_url"] == "http://localhost:8001"


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "invalid"])
def test_invalid_budget_fails(value: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PPA_SIMULATION_BUDGET_MS", value)
    with pytest.raises(ValueError):
        load_settings()
