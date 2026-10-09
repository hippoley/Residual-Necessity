#!/usr/bin/env python3
from __future__ import annotations

import random
from collections import defaultdict
from typing import Any, Callable


DEFAULT_SEED = 20261009
DEFAULT_SAMPLES = 5000
METRICS = (
    "accuracy",
    "unnecessary_intervention_rate",
    "missed_required_action_rate",
    "act_recall",
    "investigate_rate",
    "escalate_rate",
    "paired_accuracy",
)


def _quantile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("quantile requires values")
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    pos = (len(values) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(values) - 1)
    frac = pos - lo
    return values[lo] * (1.0 - frac) + values[hi] * frac


def _pair_blocks(records: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        pair_id = record.get("pair_id")
        if not isinstance(pair_id, str) or not pair_id:
            raise ValueError("pair bootstrap requires pair_id on every record")
        grouped[pair_id].append(record)

    blocks: list[list[dict[str, Any]]] = []
    for pair_id, rows in sorted(grouped.items()):
        expected = {str(row.get("expected") or "").upper() for row in rows}
        if expected != {"ACT", "ABSTAIN"} or len(rows) != 2:
            raise ValueError(
                f"pair {pair_id!r} must contain exactly one ACT and one ABSTAIN record"
            )
        blocks.append(rows)

    if not blocks:
        raise ValueError("pair bootstrap requires at least one complete pair")
    return blocks


def confidence_intervals(
    records: list[dict[str, Any]],
    *,
    evaluate_fn: Callable[[list[dict[str, Any]]], dict[str, Any]],
    samples: int = DEFAULT_SAMPLES,
    seed: int = DEFAULT_SEED,
    alpha: float = 0.05,
) -> dict[str, Any]:
    if samples < 100:
        raise ValueError("bootstrap samples must be >= 100")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be between 0 and 1")

    blocks = _pair_blocks(records)
    rng = random.Random(seed)
    distributions: dict[str, list[float]] = {metric: [] for metric in METRICS}

    for _ in range(samples):
        sampled: list[dict[str, Any]] = []
        for draw_index in range(len(blocks)):
            block = blocks[rng.randrange(len(blocks))]
            synthetic_pair_id = f"bootstrap_pair_{draw_index}"
            for row in block:
                copied = dict(row)
                copied["pair_id"] = synthetic_pair_id
                sampled.append(copied)
        report = evaluate_fn(sampled)
        for metric in METRICS:
            value = report.get(metric)
            if isinstance(value, (int, float)):
                distributions[metric].append(float(value))

    result: dict[str, Any] = {
        "method": "pair_bootstrap_percentile",
        "samples": samples,
        "seed": seed,
        "alpha": alpha,
        "pair_count": len(blocks),
        "intervals": {},
    }
    lower_q = alpha / 2.0
    upper_q = 1.0 - lower_q
    for metric, values in distributions.items():
        if not values:
            continue
        result["intervals"][metric] = {
            "lower": _quantile(values, lower_q),
            "upper": _quantile(values, upper_q),
        }
    return result
