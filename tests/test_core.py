from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load_module("residual_gate", ROOT / "src" / "gate.py")
metrics = load_module("residual_eval", ROOT / "src" / "eval.py")


def test_partial_fix_still_acts_on_residual_violation() -> None:
    receipt = gate.load(ROOT / "examples" / "residual-act.json")
    assert receipt["observations"]["historical_failure_still_reproduces"]["status"] == "FALSE"
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "ACT"


def test_missing_required_evidence_never_defaults_to_act() -> None:
    receipt = gate.load(ROOT / "examples" / "residual-act.json")
    del receipt["observations"]["residual_failure_exists"]
    verdict, _ = gate.evaluate(receipt)
    assert verdict == "INVESTIGATE"


def test_metrics_penalize_both_failure_directions() -> None:
    result = metrics.evaluate([
        {"expected": "ABSTAIN", "actual": "ACT"},
        {"expected": "ACT", "actual": "ABSTAIN"},
    ])
    assert result["unnecessary_intervention_rate"] == 0.5
    assert result["false_abstention_rate"] == 0.5


def test_investigate_does_not_count_as_success() -> None:
    result = metrics.evaluate([
        {"expected": "ABSTAIN", "actual": "INVESTIGATE"},
        {"expected": "ACT", "actual": "ACT"},
    ])
    assert result["accuracy"] == 0.5
