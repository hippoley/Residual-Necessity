from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments" / "agentabstain" / "score_development_candidate.py"

spec = importlib.util.spec_from_file_location("agentabstain_dev_candidate_score", MODULE)
assert spec and spec.loader
scorer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer)


def test_development_scorer_never_needs_holdout_labels() -> None:
    predictions = [
        {
            "case_id": "a",
            "pair_id": "p1",
            "binding_complete": True,
            "profile_id": "profile/v1",
            "proposition_specific": "ACT",
        },
        {
            "case_id": "b",
            "pair_id": "p1",
            "binding_complete": True,
            "profile_id": "profile/v1",
            "proposition_specific": "ABSTAIN",
        },
        {
            "case_id": "holdout-only",
            "pair_id": "p2",
            "binding_complete": True,
            "profile_id": "profile/v1",
            "proposition_specific": "ACT",
        },
    ]
    labels = [
        {"case_id": "a", "pair_id": "p1", "task_type": "act"},
        {"case_id": "b", "pair_id": "p1", "task_type": "abstain"},
    ]

    report = scorer.score(predictions, labels)
    assert report["partition"] == "development"
    assert report["holdout_labels_consumed"] is False
    assert report["development_variants"] == 2
    assert report["development_pairs"] == 1
    assert report["paired_accuracy"] == 1.0
    assert report["profile_counts"] == {"profile/v1": 2}
