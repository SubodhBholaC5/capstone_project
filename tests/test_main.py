import pytest

from price_pack_copilot.main import main


def test_main_starts_application_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr("price_pack_copilot.main.uvicorn.run", lambda *args, **kwargs: calls.append((args, kwargs)))
    main()
    assert calls == [(("price_pack_copilot.api:create_app",), {"factory": True})]
