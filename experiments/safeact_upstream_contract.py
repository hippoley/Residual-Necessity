#!/usr/bin/env python3
"""Load and validate SafeAct's own public contract module.

This module deliberately delegates SafeAct protocol normalization to the
upstream checkout instead of reimplementing those semantics locally.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


def load_upstream_contract(safeact_root: Path):
    module_path = safeact_root / "scripts" / "safeact_contract.py"
    if not module_path.exists():
        raise FileNotFoundError(module_path)
    spec = importlib.util.spec_from_file_location("safeact_upstream_contract", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot(safeact_root: Path) -> dict[str, Any]:
    upstream = load_upstream_contract(safeact_root)
    doc = upstream.contract_document()

    if doc.get("contract_id") != upstream.CONTRACT_ID:
        raise ValueError("SafeAct contract id mismatch")
    invariants = doc.get("common_invariants") or {}
    if invariants.get("gold_evaluator") != "deterministic":
        raise ValueError("SafeAct no longer declares deterministic gold evaluator")
    if invariants.get("agent_visible_gold_fields") is not False:
        raise ValueError("SafeAct contract no longer hides gold fields")

    checks = {
        "v0_defer": upstream.canonical_expected_outcome("v0", "DEFER"),
        "v0_block": upstream.canonical_expected_outcome("v0", "BLOCK"),
        "v1_allow": upstream.canonical_expected_outcome("v1", "ALLOW"),
        "v2_case_success": upstream.canonical_expected_outcome("v2", "CASE_SUCCESS"),
    }
    expected = {
        "v0_defer": "NO_ACTION",
        "v0_block": "NO_ACTION",
        "v1_allow": "TASK_SUCCESS",
        "v2_case_success": "WORKFLOW_SUCCESS",
    }
    if checks != expected:
        raise ValueError(f"SafeAct canonical outcome contract changed: {checks!r}")

    return {
        "source_module": str((safeact_root / "scripts" / "safeact_contract.py").resolve()),
        "contract_id": upstream.CONTRACT_ID,
        "protocol_contracts": dict(upstream.PROTOCOL_CONTRACTS),
        "common_invariants": invariants,
        "time_semantics": doc.get("time_semantics"),
        "decision_semantics": doc.get("decision_semantics"),
        "canonical_outcome_checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("safeact_root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    value = snapshot(args.safeact_root)
    args.out.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(value, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
