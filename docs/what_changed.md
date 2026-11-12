# What Changed

No notebook was supplied. This is a new scaffold, so there is no cell-to-function mapping to report.

| Requirement / logical block | Source file and entry points | Tests |
| --- | --- | --- |
| Environment configuration | `config.py`: `load_settings` | `test_config.py` |
| Typed request, calibration and output contracts | `models.py` | `test_models.py` |
| Data loading | `services/catalog.py`: `load_catalog` | `test_catalog.py` |
| Deterministic simulation, refusals and comparisons | `services/simulator.py`: `simulate_scenario`, `compare_scenarios` | `test_simulator.py` |
| Optional question interpretation and explanation | `services/copilot.py`: `answer_question` | `test_copilot.py` |
| FastAPI serving | `api.py`: `create_app` | `test_api.py` |
| Streamlit comparison workflow | `frontend.py`: `main`, `display_comparison` | `test_frontend.py` |
| Logging and server entry point | `main.py`: `main` | `test_main.py` |
| Package imports | `__init__.py`, `services/__init__.py` | `test_package.py` |

Each source file is independently available under `src/price_pack_copilot`; dependency/tool setup is in `pyproject.toml`.
The full folder layout and run commands are in the root `readme.md`. Exploratory notebooks belong in `notebook/`.
