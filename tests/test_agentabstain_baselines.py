from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments" / "agentabstain" / "baselines.py"

spec = importlib.util.spec_from_file_location("agentabstain_baselines", MODULE)
assert spec and spec.loader
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)


LABELS = [
    {"pair_id": "p1", "task_type": "act"},
    {"pair_id": "p1", "task_type": "abstain"},
    {"pair_id": "p2", "task_type": "act"},
    {"pair_id": "p2", "task_type": "abstain"},
]


def test_always_act_exposes_unnecessary_intervention():
    report = baseline.score(LABELS, "act")
    assert report["accuracy"] == 0.5
    assert report["unnecessary_intervention_rate"] == 1.0
    assert report["false_abstention_rate"] == 0.0
    assert report["paired_accuracy"] == 0.0


def test_always_abstain_exposes_false_abstention():
    report = baseline.score(LABELS, "abstain")
    assert report["accuracy"] == 0.5
    assert report["unnecessary_intervention_rate"] == 0.0
    assert report["false_abstention_rate"] == 1.0
    assert report["paired_accuracy"] == 0.0


def test_always_investigate_exposes_missed_required_action():
    report = baseline.score(LABELS, "investigate")
    assert report["accuracy"] == 0.0
    assert report["unnecessary_intervention_rate"] == 0.0
    assert report["missed_required_action_rate"] == 1.0
    assert report["act_recall"] == 0.0
    assert report["investigate_rate"] == 1.0
    assert report["paired_accuracy"] == 0.0
