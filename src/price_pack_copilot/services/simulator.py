"""Deterministic fixed-pack constant-elasticity simulator."""

import logging
from time import perf_counter

from price_pack_copilot.models import Catalog, Comparison, ComparisonRequest, Outcome, Product, Scenario

logger = logging.getLogger(__name__)


def simulate_scenario(scenario: Scenario, product: Product) -> Outcome:
    """Compute units, revenue and gross profit within calibrated bounds.

    Args:
        scenario: Proposed price for a fixed pack.
        product: Calibration for the same pack.

    Returns:
        Accepted numeric output or refusal with no projected outcomes.

    Raises:
        ValueError: If the scenario and calibration refer to different packs.
    """
    if scenario.product_id != product.product_id:
        raise ValueError("Scenario and calibration product identifiers differ")
    minimum = product.baseline_price * product.min_price_ratio
    maximum = product.baseline_price * product.max_price_ratio
    if not minimum <= scenario.price <= maximum:
        return Outcome(
            **scenario.model_dump(),
            status="refused",
            reason=f"Price outside supported interval [{minimum:g}, {maximum:g}]; extrapolation refused.",
        )
    units = product.baseline_units * (scenario.price / product.baseline_price) ** product.elasticity
    revenue = scenario.price * units
    gross_profit = (scenario.price - product.unit_cost) * units
    baseline_profit = (product.baseline_price - product.unit_cost) * product.baseline_units
    return Outcome(
        **scenario.model_dump(),
        status="accepted",
        units=units,
        revenue=revenue,
        gross_profit=gross_profit,
        margin_pct=100 * gross_profit / revenue,
        gross_profit_delta=gross_profit - baseline_profit,
    )


def compare_scenarios(request: ComparisonRequest, catalog: Catalog, budget_ms: float) -> Comparison:
    """Compare candidates with baselines without hiding losses or refusals.

    Args:
        request: Candidate list in display order.
        catalog: Versioned elasticity calibration.
        budget_ms: Positive computation-time target; excludes HTTP and LLM time.

    Returns:
        Reproducible outcomes and explicit assumptions, plus measured timing.

    Raises:
        ValueError: If a pack is unknown or the timing target is invalid.
    """
    if not 0 < budget_ms < float("inf"):
        raise ValueError("Simulation budget must be finite and positive")
    started = perf_counter()
    products = {product.product_id: product for product in catalog.products}
    unknown = {scenario.product_id for scenario in request.scenarios} - products.keys()
    if unknown:
        raise ValueError(f"Unknown product identifiers: {sorted(unknown)}")
    baselines = []
    for product_id in dict.fromkeys(scenario.product_id for scenario in request.scenarios):
        product = products[product_id]
        baseline = Scenario(label="Baseline", product_id=product_id, price=product.baseline_price)
        baselines.append(simulate_scenario(baseline, product))
    results = [simulate_scenario(scenario, products[scenario.product_id]) for scenario in request.scenarios]
    elapsed_ms = (perf_counter() - started) * 1000
    logger.info("Compared %d scenarios in %.3f ms", len(results), elapsed_ms)
    assumptions = [
        "Synthetic demonstration calibration; not a validated demand forecast.",
        "Units = baseline units * (price / baseline price) ** own-price elasticity.",
        "Pack size, unit cost and own-price elasticity are held constant.",
        "No cross-pack substitution, competition, promotions, taxes or inventory constraints.",
        "Gross profit = (price - unit cost) * units; margin = gross profit / revenue.",
        "Bounds are inclusive; unsupported prices are refused without projection.",
    ]
    for product_id in dict.fromkeys(scenario.product_id for scenario in request.scenarios):
        product = products[product_id]
        assumptions.append(f"Calibration for {product_id}: {product.model_dump_json()}")
    return Comparison(
        dataset_id=catalog.dataset_id,
        currency=catalog.currency,
        period=catalog.period,
        baselines=baselines,
        scenarios=results,
        assumptions=assumptions,
        elapsed_ms=elapsed_ms,
        budget_exceeded=elapsed_ms > budget_ms,
    )
