from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from price_pack_copilot.api import create_app
from price_pack_copilot.config import Settings, load_settings
from price_pack_copilot.models import Catalog
from price_pack_copilot.services.catalog import load_catalog


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENAI_MODEL", "")
    monkeypatch.setenv("PPA_CATALOG_PATH", str(Path("configs/catalog.json").resolve()))
    return load_settings()


@pytest.fixture
def catalog(settings: Settings) -> Catalog:
    return load_catalog(settings["catalog_path"])


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client
