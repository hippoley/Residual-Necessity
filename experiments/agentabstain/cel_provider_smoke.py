#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT=Path(__file__).resolve().parents[2]
MODULE=ROOT/"experiments"/"agentabstain"/"proposition_evidence.py"

spec=importlib.util.spec_from_file_location("rn_proposition_evidence_cel_smoke",MODULE)
assert spec and spec.loader
provider=importlib.util.module_from_spec(spec)
spec.loader.exec_module(provider)


PROFILE={
    "profile_id":"cel-smoke/v1",
    "tool":"demo.lookup",
    "propositions":[
        {
            "id":"change_needed",
            "kind":"cel",
            "expression":'result["current"] != result["desired"]',
            "authority":"complete_result_field",
        }
    ],
    "decision_scope":{
        "intervention":"demo_change",
        "task_coverage":"complete",
    },
}


def classify(result):
    return provider.classify(
        {
            "probed":True,
            "binding_complete":True,
            "tool_kind":"lookup",
            "success":True,
            "tool":"demo.lookup",
            "profile_id":"cel-smoke/v1",
            "result":result,
        },
        PROFILE,
    )


def main() -> int:
    true_case=classify({"current":"old","desired":"new"})
    assert true_case["status"]=="TRUE",true_case

    false_case=classify({"current":"same","desired":"same"})
    assert false_case["status"]=="FALSE",false_case

    missing=classify({"current":"old"})
    assert missing["status"]=="UNKNOWN",missing
    assert missing["propositions"]["change_needed"]["reason"]=="cel_no_boolean_result"

    non_bool_profile={
        **PROFILE,
        "propositions":[
            {
                "id":"bad_type",
                "kind":"cel",
                "expression":'result["current"]',
                "authority":"complete_result_field",
            }
        ],
    }
    non_bool=provider.classify(
        {
            "probed":True,
            "binding_complete":True,
            "tool_kind":"lookup",
            "success":True,
            "tool":"demo.lookup",
            "profile_id":"cel-smoke/v1",
            "result":{"current":"text"},
        },
        non_bool_profile,
    )
    assert non_bool["status"]=="UNKNOWN",non_bool
    assert non_bool["propositions"]["bad_type"]["reason"]=="cel_no_boolean_result"

    print("CEL_PROVIDER_RUNTIME=PASS")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
