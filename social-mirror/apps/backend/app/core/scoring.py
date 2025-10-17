"""Scoring utilities for aggregating detector outputs."""

from collections.abc import Mapping


def aggregate_scores(signals: Mapping[str, float]) -> float:
    """Average detector scores while ignoring missing values."""
    values = [value for value in signals.values() if value is not None]
    if not values:
        return 0.0
    return sum(values) / len(values)
