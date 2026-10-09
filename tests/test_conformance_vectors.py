from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "src" / "gate.py"

spec = importlib.util.spec_from_file_location("residual_gate_conformance", GATE_PATH)
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def test_core_conformance_vectors() -> None:
    cases = json.loads((ROOT / "conformance" / "core-cases.json").read_text(encoding="utf-8"))
    assert cases

    for case in cases:
        verdict, reason = gate.evaluate(case["receipt"])
        assert verdict == case["expected"], f"{case['id']}: {verdict} ({reason})"
