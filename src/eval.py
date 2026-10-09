#!/usr/bin/env python3
"""Two-sided metrics for Residual Necessity evaluation."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def evaluate(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        raise ValueError("at least one evaluation record is required")

    total = len(records)
    correct = investigate = escalate = 0
    decisive = decisive_correct = 0
    predicted_act = predicted_abstain = 0
    correct_act = correct_abstain = 0
    unnecessary = false_abstain = 0
    expected_abstain = expected_act = 0
    correct_expected_abstain = 0
    by_pair: dict[str, dict[str, bool | None]] = {}

    for record in records:
        expected = str(record.get("expected") or "").upper()
        actual = str(record.get("actual") or "").upper()

        if expected not in {"ACT", "ABSTAIN"}:
            raise ValueError(f"unsupported expected verdict: {expected!r}")
        if actual not in {"ACT", "ABSTAIN", "INVESTIGATE", "ESCALATE"}:
            raise ValueError(f"unsupported actual verdict: {actual!r}")

        is_correct = actual == expected
        correct += is_correct
        investigate += actual == "INVESTIGATE"
        escalate += actual == "ESCALATE"

        if actual in {"ACT", "ABSTAIN"}:
            decisive += 1
            decisive_correct += is_correct
        if actual == "ACT":
            predicted_act += 1
            correct_act += expected == "ACT"
        elif actual == "ABSTAIN":
            predicted_abstain += 1
            correct_abstain += expected == "ABSTAIN"

        if expected == "ABSTAIN":
            expected_abstain += 1
            unnecessary += actual == "ACT"
            correct_expected_abstain += actual == "ABSTAIN"
        else:
            expected_act += 1
            # Any non-ACT outcome withholds a required intervention.
            # Counting only explicit ABSTAIN would let an always-INVESTIGATE
            # system report zero false-abstention while never acting.
            false_abstain += actual != "ACT"

        pair_id = record.get("pair_id")
        if isinstance(pair_id, str) and pair_id:
            state = by_pair.setdefault(pair_id, {"act": None, "abstain": None})
            key = "act" if expected == "ACT" else "abstain"
            if state[key] is not None:
                raise ValueError(f"duplicate {expected} member for pair {pair_id!r}")
            state[key] = actual == expected

    complete_pairs = [
        pair for pair in by_pair.values()
        if pair["act"] is not None and pair["abstain"] is not None
    ]
    paired_correct = sum(
        1 for pair in complete_pairs
        if pair["act"] is True and pair["abstain"] is True
    )
    pair_outcomes = {
        "both_correct": 0,
        "act_only_correct": 0,
        "abstain_only_correct": 0,
        "neither_correct": 0,
    }
    for pair in complete_pairs:
        act_ok = pair["act"] is True
        abstain_ok = pair["abstain"] is True
        if act_ok and abstain_ok:
            pair_outcomes["both_correct"] += 1
        elif act_ok:
            pair_outcomes["act_only_correct"] += 1
        elif abstain_ok:
            pair_outcomes["abstain_only_correct"] += 1
        else:
            pair_outcomes["neither_correct"] += 1

    return {
        "total": total,
        "accuracy": correct / total,
        "expected_act_count": expected_act,
        "expected_abstain_count": expected_abstain,
        "unnecessary_intervention_rate": (
            unnecessary / expected_abstain if expected_abstain else None
        ),
        "missed_required_action_rate": (
            false_abstain / expected_act if expected_act else None
        ),
        # Backward-compatible alias. Semantically this now means any
        # non-ACT outcome on an expected-ACT case, not only explicit ABSTAIN.
        "false_abstention_rate": (
            false_abstain / expected_act if expected_act else None
        ),
        "act_recall": (
            (expected_act - false_abstain) / expected_act if expected_act else None
        ),
        "abstain_recall": (
            correct_expected_abstain / expected_abstain if expected_abstain else None
        ),
        "investigate_rate": investigate / total,
        "escalate_rate": escalate / total,
        "decision_coverage": decisive / total,
        "decisive_accuracy": (
            decisive_correct / decisive if decisive else None
        ),
        "act_precision": (
            correct_act / predicted_act if predicted_act else None
        ),
        "abstain_precision": (
            correct_abstain / predicted_abstain if predicted_abstain else None
        ),
        "pair_count": len(by_pair),
        "complete_pair_count": len(complete_pairs),
        "paired_accuracy": (
            paired_correct / len(complete_pairs) if complete_pairs else None
        ),
        "pair_outcomes": pair_outcomes,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: eval.py RECORDS.json", file=sys.stderr)
        return 2
    try:
        records = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        if not isinstance(records, list) or not all(isinstance(x, dict) for x in records):
            raise ValueError("records file must contain a JSON list of objects")
        print(json.dumps(evaluate(records), indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
