from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments" / "agentabstain" / "freeze_pair_split.py"

spec = importlib.util.spec_from_file_location("agentabstain_pair_split", MODULE)
assert spec and spec.loader
splitter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(splitter)


def _one_pair_from_each_split() -> tuple[str, str]:
    found: dict[str, str] = {}
    i = 0
    while set(found) != {"development", "holdout"}:
        pair_id = f"pair_{i}"
        found.setdefault(splitter.assign(pair_id), pair_id)
        i += 1
        assert i < 10000
    return found["development"], found["holdout"]


def test_pair_split_is_deterministic_and_pair_level() -> None:
    development_pair, holdout_pair = _one_pair_from_each_split()
    rows = [
        {"pair_id": development_pair},
        {"pair_id": development_pair},
        {"pair_id": holdout_pair},
    ]
    first = splitter.build(rows)
    second = splitter.build(list(reversed(rows)))

    assert first == second
    assert first["pair_count"] == 2
    assert first["assignments"][development_pair] == "development"
    assert first["assignments"][holdout_pair] == "holdout"


def test_assignment_uses_no_label_input() -> None:
    assert splitter.assign("pair_example") in {"development", "holdout"}
