#!/usr/bin/env python3
"""Project SafeAct rule evidence into Residual Necessity constraint observations.

SafeAct establishes whether an action is supported by required evidence.
Residual Necessity asks a different question: whether a current violated
condition makes the proposed state transition necessary.

This adapter therefore emits only role=constraint predicates. It never emits a
role=necessity predicate and never grants negative authority from SafeAct
MISSING/DEFER-style outcomes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _status(trace: dict[str, Any]) -> str:
    status=str(trace.get("status") or "").upper()
    result=str(trace.get("predicate_result") or "").upper()
    reason=str(trace.get("reason") or "").upper()

    if status=="SUPPORTED" and result=="TRUE":
        return "TRUE"
    if "CONFLICT" in status or "CONFLICT" in reason:
        return "CONFLICTED"
    if "STALE" in status or "STALE" in reason:
        return "STALE"
    return "UNKNOWN"


def project(
    document: dict[str, Any],
    *,
    target_identity: str,
    target_revision: str,
) -> dict[str, Any]:
    case_id=str(document.get("case_id") or "")
    if not case_id:
        raise ValueError("SafeAct document missing case_id")
    if not isinstance(target_identity, str) or not target_identity:
        raise ValueError("target_identity must be a non-empty string")
    if not isinstance(target_revision, str) or not target_revision:
        raise ValueError("target_revision must be a non-empty string")

    traces=document.get("rule_execution_trace")
    if not isinstance(traces,list) or not traces:
        raise ValueError("SafeAct document missing rule_execution_trace")

    predicates=[]
    observations={}
    seen_rule_ids: set[str]=set()

    for index, trace in enumerate(traces):
        if not isinstance(trace,dict):
            raise ValueError("SafeAct rule_execution_trace must contain objects")
        rule_id=str(trace.get("rule_id") or f"rule-{index}")
        if rule_id in seen_rule_ids:
            raise ValueError(f"duplicate SafeAct rule_id: {rule_id}")
        seen_rule_ids.add(rule_id)
        predicate_id=f"safeact:{case_id}:{rule_id}"
        status=_status(trace)

        predicates.append(
            {
                "id":predicate_id,
                "required":True,
                "kind":"reality",
                "role":"constraint",
            }
        )

        observation: dict[str, Any]={
            "status":status,
            "source":"SafeAct rule_execution_trace",
            "details":{
                "case_id":case_id,
                "rule_id":rule_id,
                "safeact_status":trace.get("status"),
                "safeact_predicate_result":trace.get("predicate_result"),
                "safeact_reason":trace.get("reason"),
                "management_effect":trace.get("management_effect"),
            },
        }
        if status=="TRUE":
            observation["positive_authority"]={
                "scope":{
                    "predicate_id":predicate_id,
                    "target_identity":target_identity,
                    "target_revision":target_revision,
                },
                "basis":"safeact_deterministic_rule_trace",
                "evidence_ref":f"safeact:{case_id}:{rule_id}",
            }
        observations[predicate_id]=observation

    return {
        "source":"SafeAct",
        "case_id":case_id,
        "target":{
            "identity":target_identity,
            "revision":target_revision,
        },
        "predicates":predicates,
        "observations":observations,
        "semantic_boundary":{
            "provides_action_support_constraints":True,
            "provides_residual_necessity":False,
            "missing_does_not_grant_negative_authority":True,
        },
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("safeact_document",type=Path)
    parser.add_argument("--target-identity",required=True)
    parser.add_argument("--target-revision",required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()

    document=json.loads(args.safeact_document.read_text(encoding="utf-8"))
    if not isinstance(document,dict):
        raise ValueError("SafeAct document must be an object")
    value=project(
        document,
        target_identity=args.target_identity,
        target_revision=args.target_revision,
    )
    args.out.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(value,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
