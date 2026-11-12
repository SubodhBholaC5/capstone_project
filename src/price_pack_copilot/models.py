"""API and synthetic calibration contracts."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

PositiveNumber = Annotated[float, Field(gt=0, allow_inf_nan=False)]
FiniteNumber = Annotated[float, Field(allow_inf_nan=False)]


class Contract(BaseModel):
    """Reject unknown fields and nonfinite numbers on all contracts."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Product(Contract):
    """One fixed pack and its supported own-price elasticity range."""

    product_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    baseline_price: PositiveNumber
    baseline_units: PositiveNumber
    unit_cost: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    elasticity: Annotated[float, Field(le=0, allow_inf_nan=False)]
    min_price_ratio: PositiveNumber
    max_price_ratio: PositiveNumber

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        """Require the calibration range to include the baseline."""
        if not self.min_price_ratio <= 1 <= self.max_price_ratio:
            raise ValueError("Price ratio bounds must include the baseline ratio of 1")
        return self


class Catalog(Contract):
    """Versioned calibration data and business units."""

    dataset_id: str = Field(min_length=1)
    currency: str = Field(min_length=1)
    period: str = Field(min_length=1)
    products: list[Product] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_products(self) -> Self:
        """Reject ambiguous product identifiers."""
        identifiers = [product.product_id for product in self.products]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("Product identifiers must be unique")
        return self


class Scenario(Contract):
    """A price change for an existing fixed pack."""

    label: str = Field(min_length=1, max_length=80)
    product_id: str = Field(min_length=1)
    price: PositiveNumber


class ComparisonRequest(Contract):
    """Ordered candidate scenarios; the service adds each pack's baseline."""

    scenarios: list[Scenario] = Field(min_length=1, max_length=20)


class Outcome(Contract):
    """Authoritative simulator output or an explicit refusal."""

    label: str
    product_id: str
    price: PositiveNumber
    status: Literal["accepted", "refused"]
    reason: str | None = None
    units: FiniteNumber | None = None
    revenue: FiniteNumber | None = None
    gross_profit: FiniteNumber | None = None
    margin_pct: FiniteNumber | None = None
    gross_profit_delta: FiniteNumber | None = None


class Comparison(Contract):
    """Comparison including losing/refused cases, assumptions and timing."""

    dataset_id: str
    currency: str
    period: str
    baselines: list[Outcome]
    scenarios: list[Outcome]
    assumptions: list[str]
    elapsed_ms: float
    budget_exceeded: bool


class CopilotRequest(Contract):
    """A planner question interpreted by the optional language model."""

    question: str = Field(min_length=1, max_length=4000)


class CopilotResponse(Contract):
    """Model explanation alongside authoritative numerical results."""

    comparison: Comparison
    explanation: str
