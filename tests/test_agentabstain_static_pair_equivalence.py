from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "benchmark" / "audit_agentabstain_static_pair_equivalence.py"

spec = importlib.util.spec_from_file_location("pair_equivalence_audit", MODULE)
assert spec and spec.loader
audit_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_mod)


def test_identical_blind_pair_passes() -> None:
    rows = [
        {"pair_id": "p1", "instruction": "x", "system_prompt": "s"},
        {"pair_id": "p1", "instruction": "x", "system_prompt": "s"},
    ]
    report = audit_mod.audit(rows)
    assert report["static_pair_equivalence_pass"] is True
    assert report["differing_pair_count"] == 0


def test_static_metadata_difference_is_detected() -> None:
    rows = [
        {"pair_id": "p1", "instruction": "x", "action_type": "write"},
        {"pair_id": "p1", "instruction": "x", "action_type": "delete"},
    ]
    report = audit_mod.audit(rows)
    assert report["static_pair_equivalence_pass"] is False
    assert report["field_diff_counts"] == {"action_type": 1}
