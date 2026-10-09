from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT / "src" / "eval.py"

spec = importlib.util.spec_from_file_location("residual_eval_runtime_baseline_test", EVAL_PATH)
assert spec and spec.loader
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)


def test_investigate_on_required_action_is_missed_action() -> None:
    report = metrics.evaluate([
        {"pair_id": "p1", "expected": "ACT", "actual": "INVESTIGATE"},
        {"pair_id": "p1", "expected": "ABSTAIN", "actual": "ABSTAIN"},
    ])
    assert report["false_abstention_rate"] == 1.0
    assert report["act_recall"] == 0.0
    assert report["paired_accuracy"] == 0.0


def test_successful_pair_requires_both_sides() -> None:
    report = metrics.evaluate([
        {"pair_id": "p1", "expected": "ACT", "actual": "ACT"},
        {"pair_id": "p1", "expected": "ABSTAIN", "actual": "ABSTAIN"},
    ])
    assert report["paired_accuracy"] == 1.0
    assert report["act_recall"] == 1.0
