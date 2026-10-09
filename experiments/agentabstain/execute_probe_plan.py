#!/usr/bin/env python3
"""Execute a planner-produced probe plan behind the read-only firewall."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIREWALL = ROOT / "experiments" / "agentabstain" / "probe_firewall.py"

spec = importlib.util.spec_from_file_location("agentabstain_probe_firewall", FIREWALL)
assert spec and spec.loader
fw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fw)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agentabstain-root", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--runtime-map", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    runtime_map = fw.load_json(args.runtime_map)
    plan = fw.load_json(args.plan)
    if not isinstance(runtime_map, list) or not isinstance(plan, list):
        raise ValueError("runtime map and plan must be lists")

    by_case = {}
    for locator in runtime_map:
        case_id = locator.get("case_id")
        if not isinstance(case_id, str) or case_id in by_case:
            raise ValueError("runtime map contains missing/duplicate case_id")
        by_case[case_id] = locator

    out = []
    for planned in plan:
        if not isinstance(planned, dict):
            raise ValueError("plan item must be an object")
        case_id = planned.get("case_id")
        calls = planned.get("calls")
        if not isinstance(case_id, str) or not isinstance(calls, list):
            raise ValueError("plan item requires case_id and calls")

        locator = by_case.get(case_id)
        if locator is None:
            raise ValueError(f"unknown case_id: {case_id}")

        _, menv, allowed = fw.load_agentabstain_case(
            agentabstain_root=args.agentabstain_root,
            data_dir=args.data_dir,
            locator=locator,
        )
        observations = fw.execute_case_plan(
            menv=menv,
            allowed=allowed,
            calls=calls,
        )

        out.append(
            {
                "case_id": case_id,
                "observations": observations,
                "runtime_locator_exposed": False,
                "gold_exposed": False,
                "raw_state_read": False,
            }
        )

    fw.write_json(args.out, out)
    print(f"EXECUTED_PROBE_CASES={len(out)}")
    print(f"EXECUTED_PROBE_CALLS={sum(len(x['observations']) for x in out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
