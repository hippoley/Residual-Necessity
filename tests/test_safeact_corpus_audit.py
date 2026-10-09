from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments" / "safeact_corpus_audit.py"

spec = importlib.util.spec_from_file_location("safeact_corpus_audit_test", MODULE)
assert spec and spec.loader
audit_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_mod)


def test_corpus_audit_accepts_supported_and_missing_without_negative_authority(
    tmp_path: Path,
) -> None:
    evidence_dir = tmp_path / "domain" / "materialized_evidence"
    evidence_dir.mkdir(parents=True)

    supported = {
        "case_id": "S1",
        "rule_execution_trace": [
            {
                "rule_id": "r1",
                "status": "SUPPORTED",
                "predicate_result": "TRUE",
                "reason": "ok",
                "management_effect": "permit_action",
            }
        ],
    }
    missing = {
        "case_id": "S2",
        "rule_execution_trace": [
            {
                "rule_id": "r2",
                "status": "MISSING",
                "predicate_result": "FALSE",
                "reason": "required record absent",
                "management_effect": "defer",
            }
        ],
    }
    (evidence_dir / "supported.json").write_text(json.dumps(supported), encoding="utf-8")
    (evidence_dir / "missing.json").write_text(json.dumps(missing), encoding="utf-8")

    report = audit_mod.audit(tmp_path)
    assert report["materialized_files"] == 2
    assert report["corpus_audit_pass"] is True
    assert report["negative_authority_count"] == 0
    assert report["status_counts"]["TRUE"] == 1
    assert report["status_counts"]["UNKNOWN"] == 1
