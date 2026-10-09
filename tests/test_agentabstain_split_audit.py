from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"benchmark"/"audit_agentabstain_split.py"

spec=importlib.util.spec_from_file_location("split_audit",MODULE)
assert spec and spec.loader
audit_mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_mod)


def test_split_audit_requires_every_category_in_both_partitions() -> None:
    labels=[]
    assignments={}
    for category in ("a","b","c"):
        for index, partition in enumerate(("development","holdout")):
            pair=f"pair_{category}_{index}"
            assignments[pair]=partition
            for task_type in ("act","abstain"):
                labels.append({
                    "pair_id":pair,
                    "source_pair_id":f"{category}/task_{index}",
                    "task_type":task_type,
                })
    report=audit_mod.audit(labels,{"assignments":assignments})
    assert report["missing_category_coverage"]=={}
    assert report["partition_counts"]=={"development":3,"holdout":3}
    assert report["inference_view_exposed_category"] is False


def test_split_audit_rejects_missing_holdout_category() -> None:
    labels=[
        {"pair_id":"p1","source_pair_id":"a/x","task_type":"act"},
        {"pair_id":"p1","source_pair_id":"a/x","task_type":"abstain"},
        {"pair_id":"p2","source_pair_id":"b/y","task_type":"act"},
        {"pair_id":"p2","source_pair_id":"b/y","task_type":"abstain"},
    ]
    try:
        audit_mod.audit(
            labels,
            {"assignments":{"p1":"development","p2":"holdout"}},
        )
    except ValueError as exc:
        assert "lacks category coverage" in str(exc)
    else:
        raise AssertionError("missing category coverage must fail")
