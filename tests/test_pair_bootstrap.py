from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(name: str, path: Path):
    spec=importlib.util.spec_from_file_location(name,path)
    assert spec and spec.loader
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

bootstrap=load("rn_bootstrap_test",ROOT/"src"/"bootstrap.py")
metrics=load("rn_eval_bootstrap_test",ROOT/"src"/"eval.py")


def records() -> list[dict]:
    return [
        {"pair_id":"p1","expected":"ACT","actual":"ACT"},
        {"pair_id":"p1","expected":"ABSTAIN","actual":"ABSTAIN"},
        {"pair_id":"p2","expected":"ACT","actual":"ACT"},
        {"pair_id":"p2","expected":"ABSTAIN","actual":"ACT"},
        {"pair_id":"p3","expected":"ACT","actual":"INVESTIGATE"},
        {"pair_id":"p3","expected":"ABSTAIN","actual":"ABSTAIN"},
    ]


def test_pair_bootstrap_is_deterministic() -> None:
    a=bootstrap.confidence_intervals(records(),evaluate_fn=metrics.evaluate,samples=500,seed=7)
    b=bootstrap.confidence_intervals(records(),evaluate_fn=metrics.evaluate,samples=500,seed=7)
    assert a==b
    assert a["pair_count"]==3
    assert 0.0 <= a["intervals"]["paired_accuracy"]["lower"] <= 1.0
    assert 0.0 <= a["intervals"]["paired_accuracy"]["upper"] <= 1.0


def test_pair_bootstrap_rejects_incomplete_pairs() -> None:
    bad=[
        {"pair_id":"p1","expected":"ACT","actual":"ACT"},
    ]
    try:
        bootstrap.confidence_intervals(bad,evaluate_fn=metrics.evaluate,samples=100)
    except ValueError as exc:
        assert "exactly one ACT and one ABSTAIN" in str(exc)
    else:
        raise AssertionError("incomplete pairs must be rejected")
