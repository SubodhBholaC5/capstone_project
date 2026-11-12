# Architecture and scope

Streamlit calls FastAPI over HTTP. FastAPI loads a versioned calibration catalog once per application instance.
The Python simulator alone computes outcomes. The optional model interprets questions into validated function arguments
and explains the returned results; it cannot set elasticity, cost, baseline units or bounds.

## Serving contracts

| Route | Behavior |
| --- | --- |
| `GET /health` | Readiness and dataset ID after successful catalog validation |
| `GET /catalog` | Supported fixed packs and calibration bounds |
| `POST /scenarios/compare` | `{"scenarios":[{"label":"A","product_id":"demo_330ml_6pk","price":11}]}` |
| `POST /copilot` | `{"question":"Compare demo_330ml_6pk at prices 9 and 11"}` |

The comparison response includes baselines, every candidate, dataset ID, currency, period, assumptions,
elapsed simulator milliseconds and a budget-exceeded flag. Out-of-range prices return a `refused` row
with a reason and null outcome fields; invalid input/unknown packs return HTTP 422.
Missing model configuration returns 503; provider timeouts return 504 and provider failures return 502.
An ambiguous model response without a usable tool call requests more explicit inputs through HTTP 422.

## Deterministic economics

For each fixed pack: `units = baseline_units * (price / baseline_price) ** elasticity`.
`revenue = price * units`; `gross_profit = (price - unit_cost) * units`;
`margin_pct = 100 * gross_profit / revenue`. Gross profit delta is against the same pack's baseline.
Price bounds are inclusive and calculated from baseline price times configured supported ratios.
Values retain full floating-point precision; no random state or model arithmetic affects results.

No pack-size changes, cross-elasticities, promotion, competition or substitution are modeled.
Comparing two packs produces independent scenarios, not a portfolio forecast. Calibrated real data is required
before making commercial decisions. Included synthetic bounds illustrate refusal behavior, not empirical support.

## Optional model boundary

The integration uses Responses API strict function calling with the Pydantic-generated comparison schema,
rejects unknown arguments, and executes only `compare_scenarios`. Tool outputs are returned via `call_id`.
There are at most two provider calls: interpretation and explanation, with tools disabled for explanation.
Model text remains untrusted and may contain errors; the UI always renders the authoritative comparison first.
Provider responses are mocked in tests; live account/model compatibility is not verified by the test suite.

Reference: [official OpenAI function-calling guide](https://developers.openai.com/api/docs/guides/function-calling).

## Success metrics

| Metric | Scaffold support and next validation |
| --- | --- |
| Scenario computation time | Measured per comparison against configurable 200 ms demo target; benchmark p50/p95 on representative data before agreeing an SLO |
| Out-of-range refusal correctness | Tests cover both inclusive bounds and prices outside them |
| Tool-call argument accuracy | Mocked transport checks tool dispatch; add a business-labeled question set and live evaluation before reporting accuracy |
| Reproducibility | Identical catalog and input produce identical economic outcomes; timing naturally varies |
| Assumption display coverage | Every API comparison includes full assumptions and pack calibration; UI displays them expanded |

This is a local development POC without authentication, persistence or deployment configuration.
Bind locally; introduce authentication and approved secret storage when preparing a shared deployment.
The performance budget is reported, not a hard request cancellation deadline. LLM/network latency is separate.
