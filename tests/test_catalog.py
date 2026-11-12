from pathlib import Path

import pytest

from price_pack_copilot.services.catalog import load_catalog


def test_missing_catalog_fails() -> None:
    with pytest.raises(FileNotFoundError):
        load_catalog(Path("tests/fixtures/nonexistent_catalog.json"))


def test_malformed_catalog_fails() -> None:
    with pytest.raises(ValueError):
        load_catalog(Path("tests/fixtures/malformed_catalog.json"))
