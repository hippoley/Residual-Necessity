from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"audit"/"impact.py"
spec=importlib.util.spec_from_file_location("horizontal_impact",MODULE)
assert spec and spec.loader
impact=importlib.util.module_from_spec(spec)
spec.loader.exec_module(impact)

def test_core_semantic_change_expands_to_dependent_integrations() -> None:
    result=impact.impacted(["US-01"])
    assert "US-01" in result
    assert "US-18" in result
    assert "US-19" in result

def test_gold_firewall_change_retests_reality_gate() -> None:
    result=impact.impacted(["US-25"])
    assert "US-26" in result
    assert "US-27" in result
    assert "US-28" in result
    assert "US-37" in result
