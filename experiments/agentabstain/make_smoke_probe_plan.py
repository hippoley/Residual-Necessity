#!/usr/bin/env python3
"""Create a smoke probe plan using planner-visible tool schemas only.

This is intentionally dumb. Its purpose is to prove process separation:
the planner consumes no runtime locator and no labels.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def choose_plan(surface: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in surface:
        case_id = row.get("case_id")
        for tool in row.get("safe_tools") or []:
            schema = tool.get("input_schema") or {}
            required = schema.get("required") or []
            if required:
                continue
            return [
                {
                    "case_id": case_id,
                    "calls": [{"tool": tool["name"], "args": {}}],
                }
            ]
    raise ValueError("no zero-required-argument read-only tool found")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("surface", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    surface = json.loads(args.surface.read_text(encoding="utf-8"))
    if not isinstance(surface, list):
        raise ValueError("surface must be a list")

    plan = choose_plan(surface)
    args.out.write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "planned_cases": len(plan),
        "planner_received_runtime_locator": False,
        "planner_received_gold": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
