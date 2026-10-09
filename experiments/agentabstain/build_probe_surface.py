#!/usr/bin/env python3
"""Build planner-visible read-only tool surfaces from executor-only locators."""

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
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    runtime_map = fw.load_json(args.runtime_map)
    if not isinstance(runtime_map, list):
        raise ValueError("runtime map must be a list")

    rows = []
    selected = runtime_map[: args.limit] if args.limit > 0 else runtime_map
    for locator in selected:
        if not isinstance(locator, dict):
            raise ValueError("runtime locator must be an object")
        case_id = locator.get("case_id")
        if not isinstance(case_id, str):
            raise ValueError("runtime locator missing case_id")

        _, menv, allowed = fw.load_agentabstain_case(
            agentabstain_root=args.agentabstain_root,
            data_dir=args.data_dir,
            locator=locator,
        )
        rows.append(
            {
                "case_id": case_id,
                "safe_tools": fw.sanitized_safe_surface(menv, allowed),
                "raw_state_exposed": False,
                "runtime_locator_exposed": False,
            }
        )

    fw.write_json(args.out, rows)
    print(f"PROBE_SURFACE_CASES={len(rows)}")
    print(f"PROBE_SURFACE_TOOLS={sum(len(row['safe_tools']) for row in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
