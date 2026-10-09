from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments" / "agentabstain" / "summarize_development_observations.py"

spec = importlib.util.spec_from_file_location("agentabstain_dev_summary", MODULE)
assert spec and spec.loader
summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary)


def test_summary_is_development_only_and_structural() -> None:
    observations = [
        {
            "case_id": "a",
            "pair_id": "p1",
            "tool": "records.lookup",
            "success": True,
            "result": {"status": "ok", "risk": "none"},
        },
        {
            "case_id": "b",
            "pair_id": "p1",
            "tool": "records.lookup",
            "success": False,
            "result": None,
        },
    ]
    labels = [
        {"case_id": "a", "pair_id": "p1", "task_type": "act"},
        {"case_id": "b", "pair_id": "p1", "task_type": "abstain"},
    ]

    report = summary.summarize(observations, labels)
    assert report["development_variants"] == 2
    assert report["development_pairs"] == 1
    assert report["holdout_payload_consumed"] is False
    assert report["success_by_label"]["act"]["true"] == 1
    assert report["success_by_label"]["abstain"]["false"] == 1
    assert ["risk", 1] in [list(x) for x in report["top_object_keys"]]
