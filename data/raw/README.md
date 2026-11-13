# Synthetic CPG price-pack POC data

All data, brands, elasticity estimates and calibration metadata are fictional. This bundle supports the **Price Pack Architecture Copilot** in the supplied screenshot and the simulator already in `capstone_project`. It is reference simulation data, not a validated market forecast.

## File

| File | Contents |
|---|---|
| `cpg_price_pack_poc.xlsx` | Overview, 4,800-row master, 100 labelled questions/answers/tool calls, field dictionary |
| `master_data.csv` | Same complete master, suitable for application/database ingestion |
| `catalog.json` | 400 October 2026 context-specific packs, conforming to the existing app's `Catalog` model |
| `golden_questions.jsonl` | 100 evaluation records with full-precision expected tool results and assumptions |
| `golden_questions.csv` | Same golden records; nested fields are JSON strings |
| `data_dictionary.csv` | Definitions, types, units, nullability and examples for every CSV field |
| `manifest.json` | Seed, version and catalog/simulator hashes |
| `validation_report.json` | Integrity and deterministic replay results |

## Master grain and variability

One row represents **one physical SKU x region x channel x calendar month**. There are 25 fixed-pack SKUs across sparkling beverages, fruit drinks, potato snacks, laundry detergent and biscuits; four regions (North/South/East/West); four channels (general trade/modern trade/ecommerce/wholesale); and 12 months (2025-11 through 2026-10). Total: **25 x 4 x 4 x 12 = 4,800 records**.

`record_id` is the unique row key. `product_id` identifies a SKU-region-channel combination and repeats across months. `sku_id` identifies the physical selling pack. The active catalog includes **only October 2026**, where each of its 400 `product_id` values is unique. Join it to master on `product_id` **and** filter master to `month = '2026-10'`. Joining on product alone duplicates rows 12 times.

Prices/costs are **INR per complete selling pack**; volume is **packs per month**, including for multipacks. `pack_size` is one inner unit; `units_per_pack` is the number of those units in a selling pack. One beverage SKU is a six-pack. Prices represent manufacturer net realization excluding taxes, not shelf MRP. Cost is variable COGS excluding overhead. Gross profit is not net profit. `baseline_margin_pct = 25` means 25%, not 0.25.

The seeded generator varies pack sizes, price tiers, channel discounts, regional prices, volume, seasonal beverage demand, own-price elasticities, variable costs and supported bounds. Monthly observations are fabricated independently with modest synthetic seasonality and price trends; **do not fit elasticity from this panel or treat metadata as statistical evidence**. There are no intentional missing values or duplicate primary keys. Variation in costs and volumes is synthetic, not evidence of causal price response.

## Simulator contract

The current tool is `compare_scenarios`, with exactly this argument shape:

```json
{"scenarios": [{"label": "Candidate", "product_id": "SKU001_north_general_trade", "price": 21.66}]}
```

Use an actual proposed price from the question or golden set; the example illustrates schema only. Each call accepts 1–20 ordered scenarios. Product and cost calibration are server-side. The tool adds one baseline per distinct requested `product_id`.

For baseline price P0, baseline monthly packs Q0, proposed price P, elasticity E and cost C:

- `units = Q0 * (P / P0) ** E`
- `revenue = P * units`
- `gross_profit = (P - C) * units`
- `margin_pct = 100 * gross_profit / revenue`
- `gross_profit_delta = gross_profit - (P0 - C) * Q0`

Accept only `P0 * min_price_ratio <= P <= P0 * max_price_ratio`, with **inclusive, full-precision bounds**. Do not round a boundary before comparing; displayed two-decimal prices can hide a fractional-paise bound. For percent-change questions explicitly instructing rounding, round the proposed price to two decimals before calling the tool. Out-of-range positive prices must reach the simulator, which returns `status = refused`, a reason, and **null** projected metrics, never zero. Invalid non-positive prices violate the request schema.

Model assumptions: constant own-price elasticity, fixed pack, fixed cost, fixed period, no cross-pack substitution, competition, promotions, taxes or inventory constraints. Comparing two packs shows independent outcomes against each pack's own baseline; it does not predict switching or a portfolio response. All projected pack counts are continuous expected values, not integer-rounded orders.

### Result dictionary (nested golden fields)

`expected_tool_calls` is an array of `{name, arguments}`; arguments contain `scenarios`, an ordered array of `{label: string, product_id: string, price: positive number}`. No-tool rows contain `[]`.

`expected_result` contains `dataset_id`, `currency`, `period`, `baselines`, `scenarios`, and `assumptions`. Baselines/scenarios are arrays of outcomes:

| Field | Meaning / type |
|---|---|
| `label`, `product_id` | Scenario display label and exact context-specific product identifier (strings) |
| `price` | Proposed INR per complete pack (positive number) |
| `status` | `accepted` or `refused` |
| `reason` | Refusal explanation string; null when accepted |
| `units` | Expected packs for October 2026; number or null on refusal |
| `revenue` | INR/month; number or null on refusal |
| `gross_profit` | INR/month; number or null on refusal |
| `margin_pct` | Percentage points; number or null on refusal |
| `gross_profit_delta` | INR/month difference from the same product baseline; number or null on refusal |

`assumptions` includes the six simulator-wide disclosures followed by calibration details for requested products. `required_assumptions` lists the six disclosures for semantic explanation scoring. Golden results exclude `elapsed_ms` and `budget_exceeded` because those are runtime measurements, not reproducible business outputs. No-tool rows have `expected_result = null`.

The catalog has `dataset_id`, `currency`, `period`, `products`. Each product includes `product_id`, `name`, `baseline_price`, `baseline_units`, `unit_cost`, `elasticity`, `min_price_ratio`, `max_price_ratio`; their meanings match the master dictionary. Catalog `name` additionally displays region and channel.

## Golden-set coverage and evaluation

There are 100 questions: 20 percentage-price changes, 20 absolute-price changes, 20 inclusive-boundary tests, 20 comparisons (10 same-pack, five cross-pack, five mixed accepted/refused), 10 standalone out-of-range requests and 10 no-tool cases. Across the 90 calls there are **110 candidate outcomes: 95 accepted, 15 refused**. Comparisons retain losing scenarios. Ten personas have 10 questions each, spanning revenue growth, pricing, brand/category, sales, key accounts, finance, demand planning, commercial leadership and QA.

Twenty records are marked validation and 80 test. These are convenient partitions of template-generated fixtures with overlapping language families, **not an independent generalization benchmark**. Keep answer/result columns out of the user/model prompt; give the model the question and trusted catalog only.

Recommended scores, reported separately:

1. **Action accuracy, all 100 rows:** correct `call_tool`, `clarify` or `explain_unsupported`; zero calls on the 10 no-tool rows.
2. **Tool accuracy, 90 call rows:** exactly one `compare_scenarios` call; exact product IDs and scenario order/count; ignore JSON key order and arbitrary display labels. Compare price arguments with absolute tolerance `1e-8` INR and no relative tolerance. Do not accept price rounding that changes a boundary status.
3. **Numeric accuracy:** compare full-precision JSON outcomes with tolerance `max(1e-6, 1e-9 * abs(expected))` for accepted metrics. Require exact statuses, null refusal metrics and semantically correct refusal reasons. Round only for display; `expected_answer` is a human-readable guide.
4. **Refusal correctness:** score 15 refused candidate outcomes plus valid boundary acceptance; do not count no-tool capability explanations as elasticity refusals. Report false acceptance and false refusal separately.
5. **Comparison/explanation coverage:** retain every candidate including losers and refusals, compare with its own baseline, and show the model assumptions. For same-pack comparisons identify the highest gross profit including baseline, rather than assuming a price rise wins.
6. **Reproducibility:** rerun the same arguments against the catalog hash in `manifest.json`; exclude timing from equality. All 90 stored golden calls have been replayed against the existing application simulator with exact equality.
7. **Performance:** measure simulator-only elapsed time and end-to-end LLM latency separately on target hardware. The app's default 200 ms simulator budget is a target, not a dataset guarantee. Report p50/p95 and budget-exceeded rate; baseline timings are deliberately not golden labels.

No live LLM/tool-routing accuracy has been measured. All expected numeric outcomes were generated by the existing deterministic simulator and validated by replay; master financial identities and uniqueness were checked separately. Replays verify fixture consistency, not independent validation of the demand model.

## Using the bundle with the existing POC

From `capstone_project`, set `PPA_CATALOG_PATH=../data/catalog.json` in the process environment (or its `.env`) and start the app normally. If launching from the workspace root instead, set `PPA_CATALOG_PATH=data/catalog.json`. This bundle does not replace the existing small demo catalog or modify application code.

The existing `answer_question` implementation requires exactly one tool call and raises an error when none is returned. The 10 no-tool rows are **target behavior tests** requiring application handling for clarifications and unsupported requests; they are not claimed to pass the current app. The 90 numeric rows use its existing schema and simulator. The 400-product catalog is larger than the original demo; measure prompt size and latency when evaluating it.

For each golden JSONL row, submit `question` through the copilot and score the emitted call **before execution** against `expected_tool_calls`. Execute that call using the trusted catalog; compare deterministic results to `expected_result`. Evaluate the final explanation semantically against `expected_answer` and `required_assumptions`. Never have the LLM compute the golden numeric metrics itself.
