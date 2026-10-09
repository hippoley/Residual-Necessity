#!/usr/bin/env python3
"""Gold-blind prediction baselines over one tool-visible runtime observation.

This module has no AgentAbstain imports and receives only the sanitized
observation produced after the trusted harness executes one lookup/verify
probe. It intentionally implements weak baselines for falsification.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def predict(observation: dict[str, Any]) -> dict[str, str]:
    probed = observation.get("probed")
    if probed is False:
        return {
            "failure_only": "INVESTIGATE",
            "probe_success": "INVESTIGATE",
        }
    if probed is not True:
        raise ValueError("observation.probed must be boolean")

    success = observation.get("success")
    if not isinstance(success, bool):
        raise ValueError("observation.success must be boolean when probed")

    if success is False:
        return {
            "failure_only": "ABSTAIN",
            "probe_success": "ABSTAIN",
        }

    return {
        "failure_only": "INVESTIGATE",
        "probe_success": "ACT",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--observation", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    observation = json.loads(args.observation.read_text(encoding="utf-8"))
    if not isinstance(observation, dict):
        raise ValueError("observation must be a JSON object")

    args.out.write_text(
        json.dumps(predict(observation), sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
