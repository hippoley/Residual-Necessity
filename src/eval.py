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
    correct = unnecessary = false_abstain = investigate = escalate = 0
    by_pair: dict[str, dict[str, bool]] = {}

    for record in records:
        expected = str(record.get("expected") or "").upper()
        actual = str(record.get("actual") or "").upper()

        if expected not in {"ACT", "ABSTAIN"}:
            raise ValueError(f"unsupported expected verdict: {expected!r}")
        if actual not in {"ACT", "ABSTAIN", "INVESTIGATE", "ESCALATE"}:
            raise ValueError(f"unsupported actual verdict: {actual!r}")

        correct += actual == expected
        unnecessary += expected == "ABSTAIN" and actual == "ACT"
        false_abstain += expected == "ACT" and actual == "ABSTAIN"
        investigate += actual == "INVESTIGATE"
        escalate += actual == "ESCALATE"

        pair_id = record.get("pair_id")
        if isinstance(pair_id, str) and pair_id:
            state = by_pair.setdefault(pair_id, {"act": False, "abstain": False})
            if expected == "ACT":
                state["act"] = actual == "ACT"
            else:
                state["abstain"] = actual == "ABSTAIN"

    pairs = list(by_pair.values())
    paired_correct = sum(1 for pair in pairs if pair["act"] and pair["abstain"])

    return {
        "total": total,
        "accuracy": correct / total,
        "unnecessary_intervention_rate": unnecessary / total,
        "false_abstention_rate": false_abstain / total,
        "investigate_rate": investigate / total,
        "escalate_rate": escalate / total,
        "pair_count": len(pairs),
        "paired_accuracy": paired_correct / len(pairs) if pairs else None,
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
