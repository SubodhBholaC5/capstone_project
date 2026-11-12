"""Calibration loading."""

from pathlib import Path

from price_pack_copilot.models import Catalog


def load_catalog(path: Path) -> Catalog:
    """Load and validate the entire calibration catalog.

    Args:
        path: JSON catalog path.

    Returns:
        Validated catalog with unique product identifiers.

    Raises:
        OSError: If the catalog cannot be read.
        ValueError: If JSON or calibration values are invalid.
    """
    return Catalog.model_validate_json(path.read_text(encoding="utf-8"))
