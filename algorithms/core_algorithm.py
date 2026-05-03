"""
core_algorithm.py
~~~~~~~~~~~~~~~~~
Core algorithmic primitives for the Sovereign Architecture platform.

All functions in this module are **pure**: they are stateless, cause no side
effects, and return deterministic results for a given set of inputs.  Agents
call these functions as tools; they must not call I/O or mutate shared state.

Provided algorithms
-------------------
- :func:`score_and_rank`  – rank items by a numeric score.
- :func:`weighted_select` – probabilistically select an item by weight.
- :func:`normalise`       – min-max normalise a list of floats.
- :func:`moving_average`  – compute a simple moving average over a sequence.
- :func:`threshold_filter`– filter items whose score exceeds a threshold.
"""

from __future__ import annotations

import random
from typing import Any, TypeVar

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------


def score_and_rank(
    items: list[dict[str, Any]],
    score_key: str,
    descending: bool = True,
) -> list[dict[str, Any]]:
    """Return *items* sorted by the value at *score_key*.

    Args:
        items:      A list of dicts, each containing at least *score_key*.
        score_key:  The dict key whose numeric value is used for sorting.
        descending: If ``True`` (default), highest score appears first.

    Returns:
        A new list sorted by the specified score.  The original list is not
        modified.

    Raises:
        KeyError: If any item does not contain *score_key*.
        TypeError: If the score value is not numeric.

    Example::

        >>> items = [{"name": "a", "score": 3}, {"name": "b", "score": 7}]
        >>> score_and_rank(items, "score")
        [{'name': 'b', 'score': 7}, {'name': 'a', 'score': 3}]
    """
    return sorted(items, key=lambda item: item[score_key], reverse=descending)


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------


def weighted_select(
    items: list[T],
    weights: list[float],
    seed: int | None = None,
) -> T:
    """Select one item from *items* using *weights* as selection probabilities.

    Args:
        items:   Non-empty list of candidates.
        weights: Corresponding non-negative weights.  Need not sum to 1.
        seed:    Optional random seed for reproducibility.

    Returns:
        A single selected item.

    Raises:
        ValueError: If *items* and *weights* have different lengths or are empty.

    Example::

        >>> weighted_select(["a", "b", "c"], [1, 2, 1], seed=42)
        'b'
    """
    if not items:
        raise ValueError("items must not be empty.")
    if len(items) != len(weights):
        raise ValueError("items and weights must have the same length.")

    rng = random.Random(seed)
    (selected,) = rng.choices(items, weights=weights, k=1)
    return selected


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------


def normalise(values: list[float]) -> list[float]:
    """Min-max normalise *values* to the range [0, 1].

    Args:
        values: A non-empty list of numeric values.

    Returns:
        A new list where the minimum maps to 0.0 and the maximum to 1.0.
        If all values are equal, returns a list of 0.0s.

    Raises:
        ValueError: If *values* is empty.

    Example::

        >>> normalise([1.0, 2.0, 3.0])
        [0.0, 0.5, 1.0]
    """
    if not values:
        raise ValueError("values must not be empty.")
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.0] * len(values)
    span = hi - lo
    return [(v - lo) / span for v in values]


# ---------------------------------------------------------------------------
# Moving average
# ---------------------------------------------------------------------------


def moving_average(values: list[float], window: int) -> list[float]:
    """Compute a simple moving average of *values* with the given *window* size.

    The first ``window - 1`` positions are populated with the cumulative
    average of all available values up to that position (expanding window).

    Args:
        values: A list of numeric observations in time order.
        window: Number of observations per window.  Must be >= 1.

    Returns:
        A list of the same length as *values* containing averaged values.

    Raises:
        ValueError: If *window* < 1 or *values* is empty.

    Example::

        >>> moving_average([1, 2, 3, 4, 5], window=3)
        [1.0, 1.5, 2.0, 3.0, 4.0]
    """
    if not values:
        raise ValueError("values must not be empty.")
    if window < 1:
        raise ValueError("window must be >= 1.")

    result: list[float] = []
    for i, _ in enumerate(values):
        start = max(0, i - window + 1)
        chunk = values[start : i + 1]
        result.append(sum(chunk) / len(chunk))
    return result


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def threshold_filter(
    items: list[dict[str, Any]],
    score_key: str,
    threshold: float,
    inclusive: bool = True,
) -> list[dict[str, Any]]:
    """Return items whose score satisfies the threshold condition.

    Args:
        items:      A list of dicts each containing *score_key*.
        score_key:  The dict key whose numeric value is compared.
        threshold:  The cut-off value.
        inclusive:  If ``True`` (default), include items whose score equals
                    the threshold.

    Returns:
        A filtered list preserving the original order.

    Example::

        >>> items = [{"id": 1, "score": 0.8}, {"id": 2, "score": 0.4}]
        >>> threshold_filter(items, "score", 0.5)
        [{'id': 1, 'score': 0.8}]
    """
    if inclusive:
        return [item for item in items if item[score_key] >= threshold]
    return [item for item in items if item[score_key] > threshold]
