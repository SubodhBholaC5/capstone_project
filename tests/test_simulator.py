import pytest

from price_pack_copilot.models import Catalog, ComparisonRequest, Scenario
from price_pack_copilot.services.simulator import compare_scenarios, simulate_scenario


def test_baseline_accounting_identity(catalog: Catalog) -> None:
    product = catalog.products[0]
    result = simulate_scenario(Scenario(label="Baseline", product_id=product.product_id, price=10), product)
    assert result.units == 10000
    assert result.revenue == 100000
    assert result.gross_profit == 40000
    assert result.margin_pct == 40
    assert result.gross_profit_delta == 0


@pytest.mark.parametrize("price", [8.5, 11.5])
def test_calibration_boundaries_are_inclusive(price: float, catalog: Catalog) -> None:
    product = catalog.products[0]
    assert (
        simulate_scenario(Scenario(label="Boundary", product_id=product.product_id, price=price), product).status
        == "accepted"
    )


@pytest.mark.parametrize("price", [8.49, 11.51])
def test_extrapolation_refused(price: float, catalog: Catalog) -> None:
    product = catalog.products[0]
    result = simulate_scenario(Scenario(label="Outside", product_id=product.product_id, price=price), product)
    assert result.status == "refused"
    assert result.units is None
    assert result.gross_profit is None
    assert "extrapolation refused" in result.reason


def test_comparison_retains_losses_and_is_reproducible(catalog: Catalog) -> None:
    product_id = catalog.products[0].product_id
    request = ComparisonRequest(
        scenarios=[Scenario(label=str(price), product_id=product_id, price=price) for price in [9, 11, 15]]
    )
    first = compare_scenarios(request, catalog, 200)
    second = compare_scenarios(request, catalog, 200)
    assert first.scenarios == second.scenarios
    assert len(first.scenarios) == 3
    assert first.scenarios[0].gross_profit_delta < 0
    assert first.scenarios[1].gross_profit_delta > 0
    assert first.scenarios[1].units == pytest.approx(8667.841720414475)
    assert first.scenarios[2].status == "refused"
    assert len(first.baselines) == 1
    assert first.assumptions
    assert first.elapsed_ms >= 0


def test_unknown_product_fails(catalog: Catalog) -> None:
    request = ComparisonRequest(scenarios=[Scenario(label="A", product_id="missing", price=10)])
    with pytest.raises(ValueError, match="Unknown product"):
        compare_scenarios(request, catalog, 200)
