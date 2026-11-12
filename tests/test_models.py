import pytest
from pydantic import ValidationError

from price_pack_copilot.models import Catalog, ComparisonRequest, Product, Scenario


@pytest.mark.parametrize("price", [0, -1, float("nan"), float("inf")])
def test_invalid_price_rejected(price: float) -> None:
    with pytest.raises(ValidationError):
        Scenario(label="Invalid", product_id="demo", price=price)


def test_unknown_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        Scenario.model_validate({"label": "A", "product_id": "demo", "price": 10, "elasticity": -10})


def test_empty_comparison_rejected() -> None:
    with pytest.raises(ValidationError):
        ComparisonRequest(scenarios=[])


def test_duplicate_products_rejected(catalog: Catalog) -> None:
    with pytest.raises(ValidationError):
        Catalog.model_validate({**catalog.model_dump(), "products": [catalog.products[0]] * 2})


def test_invalid_calibration_range_rejected(catalog: Catalog) -> None:
    with pytest.raises(ValidationError):
        Product.model_validate({**catalog.products[0].model_dump(), "min_price_ratio": 1.2})
