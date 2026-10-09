#!/usr/bin/env python3
"""Gold-blind prediction baselines over tool-visible runtime observations.

Historical generic baselines are retained for falsification. The
`proposition_specific` strategy is stricter: it delegates to an explicit
provider profile and otherwise remains INVESTIGATE.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

MODULE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(MODULE_DIR))

from proposition_evidence import classify as classify_propositions
from proposition_evidence import decision_for


def predict(observation: dict[str, Any]) -> dict[str, str]:
    probed = observation.get("probed")
    if probed is False:
        historical = {
            "failure_only": "INVESTIGATE",
            "probe_success": "INVESTIGATE",
        }
    elif probed is True:
        success = observation.get("success")
        if not isinstance(success, bool):
            raise ValueError("observation.success must be boolean when probed")
        if success is False:
            historical = {
                "failure_only": "ABSTAIN",
                "probe_success": "ABSTAIN",
            }
        else:
            historical = {
                "failure_only": "INVESTIGATE",
                "probe_success": "ACT",
            }
    else:
        raise ValueError("observation.probed must be boolean")

    semantic = classify_propositions(
        observation,
        observation.get("provider_profile"),
    )
    historical["proposition_specific"] = decision_for(semantic["status"])
    return historical


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
