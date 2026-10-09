from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments" / "agentabstain" / "score_development_candidate.py"
SPLIT = ROOT / "experiments" / "agentabstain" / "freeze_pair_split.py"

spec = importlib.util.spec_from_file_location("agentabstain_dev_candidate_score", MODULE)
assert spec and spec.loader
scorer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer)

split_spec = importlib.util.spec_from_file_location("agentabstain_pair_split_for_score_test", SPLIT)
assert split_spec and split_spec.loader
splitter = importlib.util.module_from_spec(split_spec)
split_spec.loader.exec_module(splitter)


def _pair_for(partition: str) -> str:
    for i in range(10000):
        pair_id = f"pair_{i}"
        if splitter.assign(pair_id) == partition:
            return pair_id
    raise AssertionError(f"could not find {partition} pair")


def test_development_scorer_never_needs_holdout_labels() -> None:
    dev_pair = _pair_for("development")
    predictions = [
        {
            "case_id": "a",
            "pair_id": dev_pair,
            "binding_complete": True,
            "profile_id": "profile/v1",
            "proposition_specific": "ACT",
        },
        {
            "case_id": "b",
            "pair_id": dev_pair,
            "binding_complete": True,
            "profile_id": "profile/v1",
            "proposition_specific": "ABSTAIN",
        },
        {
            "case_id": "holdout-only",
            "pair_id": _pair_for("holdout"),
            "binding_complete": True,
            "profile_id": "profile/v1",
            "proposition_specific": "ACT",
        },
    ]
    labels = [
        {"case_id": "a", "pair_id": dev_pair, "task_type": "act"},
        {"case_id": "b", "pair_id": dev_pair, "task_type": "abstain"},
    ]

    report = scorer.score(predictions, labels)
    assert report["partition"] == "development"
    assert report["holdout_labels_consumed"] is False
    assert report["development_variants"] == 2
    assert report["development_pairs"] == 1
    assert report["paired_accuracy"] == 1.0
    assert report["profile_counts"] == {"profile/v1": 2}


def test_development_scorer_rejects_holdout_label() -> None:
    holdout_pair = _pair_for("holdout")
    predictions = [
        {
            "case_id": "h",
            "pair_id": holdout_pair,
            "binding_complete": True,
            "profile_id": "profile/v1",
            "proposition_specific": "ACT",
        }
    ]
    labels = [
        {"case_id": "h", "pair_id": holdout_pair, "task_type": "act"},
    ]

    with pytest.raises(ValueError, match="non-development pair leaked"):
        scorer.score(predictions, labels)
