from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

metrics = _load("rn_eval_bootstrap_test", ROOT / "src" / "eval.py")
bootstrap = _load("rn_bootstrap_test", ROOT / "src" / "bootstrap.py")


def test_pair_bootstrap_covers_two_sided_recall_metrics() -> None:
    records = [
        {"pair_id": "p1", "expected": "ACT", "actual": "ACT"},
        {"pair_id": "p1", "expected": "ABSTAIN", "actual": "ABSTAIN"},
        {"pair_id": "p2", "expected": "ACT", "actual": "INVESTIGATE"},
        {"pair_id": "p2", "expected": "ABSTAIN", "actual": "ABSTAIN"},
        {"pair_id": "p3", "expected": "ACT", "actual": "ACT"},
        {"pair_id": "p3", "expected": "ABSTAIN", "actual": "ACT"},
    ]
    result = bootstrap.confidence_intervals(
        records,
        evaluate_fn=metrics.evaluate,
        samples=200,
        seed=7,
    )
    intervals = result["intervals"]
    for name in (
        "act_recall",
        "abstain_recall",
        "two_sided_recall_geomean",
        "paired_accuracy",
    ):
        assert name in intervals
        assert 0.0 <= intervals[name]["lower"] <= intervals[name]["upper"] <= 1.0
