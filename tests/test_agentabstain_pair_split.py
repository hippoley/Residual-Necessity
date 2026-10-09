from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments" / "agentabstain" / "freeze_pair_split.py"

spec = importlib.util.spec_from_file_location("agentabstain_pair_split", MODULE)
assert spec and spec.loader
splitter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(splitter)


def test_pair_split_is_deterministic_and_pair_level() -> None:
    rows = [
        {"pair_id": "pair_a"},
        {"pair_id": "pair_a"},
        {"pair_id": "pair_b"},
        {"pair_id": "pair_c"},
        {"pair_id": "pair_d"},
    ]
    first = splitter.build(rows)
    second = splitter.build(list(reversed(rows)))
    assert first == second
    assert first["pair_count"] == 4
    assert set(first["assignments"]) == {"pair_a", "pair_b", "pair_c", "pair_d"}


def test_assignment_uses_no_label_input() -> None:
    assert splitter.assign("pair_example") in {"development", "holdout"}
