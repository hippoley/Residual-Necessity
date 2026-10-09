#!/usr/bin/env python3
"""Mine development-only provider-profile gaps for AgentAbstain.

This tool does not create authority. It ranks observed tools by coverage and
structural stability so humans can decide which mature external tool surfaces
are worth a narrow provider profile.

Holdout data is intentionally unsupported.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _load(path: Path) -> list[dict[str, Any]]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,list) or not all(isinstance(x,dict) for x in value):
        raise ValueError(f"{path} must contain a JSON list of objects")
    return value


def _shape(value: Any) -> str:
    if value is None: return "null"
    if isinstance(value,bool): return "bool"
    if isinstance(value,(int,float)) and not isinstance(value,bool): return "number"
    if isinstance(value,str): return "string"
    if isinstance(value,list): return "array"
    if isinstance(value,dict): return "object"
    return type(value).__name__


def mine(
    observations: list[dict[str,Any]],
    labels: list[dict[str,Any]],
    registry: dict[str,Any],
) -> dict[str,Any]:
    labels_by_case={row["case_id"]:row for row in labels}
    if set(labels_by_case)!={row["case_id"] for row in observations}:
        raise ValueError("development observation/label mismatch")

    existing: dict[str,list[str]]=defaultdict(list)
    for profile in registry.get("profiles") or []:
        if isinstance(profile,dict) and isinstance(profile.get("tool"),str):
            existing[profile["tool"]].append(str(profile.get("profile_id") or ""))

    agg: dict[str,dict[str,Any]]={}
    for row in observations:
        tool=str(row.get("tool") or "<none>")
        rec=agg.setdefault(tool,{
            "tool":tool,
            "tool_kind":row.get("tool_kind"),
            "variants":0,
            "pairs":set(),
            "act":0,
            "abstain":0,
            "success":0,
            "binding_complete":0,
            "shapes":Counter(),
            "object_keys":Counter(),
            "profile_ids":existing.get(tool,[]),
        })
        rec["variants"]+=1
        rec["pairs"].add(str(row.get("pair_id")))
        label=labels_by_case[row["case_id"]]["task_type"]
        rec[label]+=1
        if row.get("success") is True: rec["success"]+=1
        if row.get("binding_complete") is True: rec["binding_complete"]+=1
        result=row.get("result")
        rec["shapes"][_shape(result)]+=1
        if isinstance(result,dict):
            for key in result:
                rec["object_keys"][str(key)]+=1

    ranked=[]
    for rec in agg.values():
        variants=rec["variants"]
        pair_count=len(rec["pairs"])
        both_sides=min(rec["act"],rec["abstain"])
        dominant_shape=rec["shapes"].most_common(1)[0][1] if rec["shapes"] else 0
        structural_stability=dominant_shape/variants if variants else 0.0
        binding_rate=rec["binding_complete"]/variants if variants else 0.0
        success_rate=rec["success"]/variants if variants else 0.0

        # Ranking is triage only, never authority.
        score=pair_count*(0.5+0.5*structural_stability)*(0.5+0.5*binding_rate)
        if both_sides==0:
            score*=0.25
        if rec["profile_ids"]:
            score*=0.2

        ranked.append({
            "tool":rec["tool"],
            "tool_kind":rec["tool_kind"],
            "development_variants":variants,
            "development_pairs":pair_count,
            "act_variants":rec["act"],
            "abstain_variants":rec["abstain"],
            "both_label_sides_present":rec["act"]>0 and rec["abstain"]>0,
            "success_rate":success_rate,
            "binding_complete_rate":binding_rate,
            "result_shapes":dict(rec["shapes"]),
            "structural_stability":structural_stability,
            "top_object_keys":rec["object_keys"].most_common(30),
            "existing_profile_ids":rec["profile_ids"],
            "triage_score":score,
            "authority_granted":False,
        })

    ranked.sort(key=lambda x:(-x["triage_score"],-x["development_pairs"],x["tool"]))
    return {
        "schema_version":"provider-gap-report/0.1",
        "development_variants":len(observations),
        "development_pairs":len({row["pair_id"] for row in observations}),
        "profiles_currently_registered":sum(bool(x["existing_profile_ids"]) for x in ranked),
        "tools_observed":len(ranked),
        "candidates":ranked,
        "holdout_consumed":False,
        "authority_granted":False,
        "purpose":"triage_external_tool_surfaces_for_manual_provider_profile_design",
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--observations",type=Path,required=True)
    parser.add_argument("--labels",type=Path,required=True)
    parser.add_argument("--registry",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()

    registry=json.loads(args.registry.read_text(encoding="utf-8"))
    report=mine(_load(args.observations),_load(args.labels),registry)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
