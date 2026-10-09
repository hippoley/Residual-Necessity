#!/usr/bin/env python3
"""Issue-derived bounded oracle for P3 cave-story-md issue #169.

External issue discussion establishes the relevant invariant before the final
fix: special bosses use <BSL0000>, and zero should resolve through bossEntity.
The probe inspects only the current revision's CMD_BSL zero branch.

It does not compare against the final patch and does not use the P3
classification while deciding the predicate.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PREDICATE_ID="bsl0000_special_boss_lookup_still_broken"
TARGET_ID="repo:andwn/cave-story-md:src/tsc.c:CMD_BSL"
ISSUE_REF="github:andwn/cave-story-md#169"


def _balanced_block(text: str, brace: int) -> str | None:
    depth=0
    for i in range(brace,len(text)):
        if text[i]=="{":
            depth+=1
        elif text[i]=="}":
            depth-=1
            if depth==0:
                return text[brace:i+1]
    return None


def inspect_source(text: str) -> tuple[str,str]:
    start=text.find("case CMD_BSL")
    if start < 0:
        return "UNKNOWN","CMD_BSL case not found"

    case=text[start:start+5000]
    match=re.search(r"if\s*\(\s*!\s*args\s*\[\s*0\s*\]\s*\)",case)
    if not match:
        return "UNKNOWN","zero-argument branch not found"

    brace=case.find("{",match.end())
    if brace < 0:
        return "UNKNOWN","zero-argument branch has no block"

    block=_balanced_block(case,brace)
    if block is None:
        return "UNKNOWN","zero-argument branch is syntactically incomplete"

    binds_special=bool(re.search(r"bossBarEntity\s*=\s*bossEntity\b",block))
    clears_bar=bool(re.search(r"bossBarEntity\s*=\s*NULL\b",block))

    if binds_special:
        return "FALSE","<BSL0000 branch resolves bossBarEntity from bossEntity"
    if clears_bar:
        return "TRUE","<BSL0000 branch clears bossBarEntity instead of selecting bossEntity"
    return "UNKNOWN","zero branch does not establish bounded special-boss behavior"


def receipt(status: str, reason: str, revision: str, source_path: str) -> dict[str,Any]:
    observation: dict[str,Any]={
        "status":status,
        "source":ISSUE_REF,
        "details":{
            "bounded_oracle":"CMD_BSL zero branch",
            "reason":reason,
            "source_path":source_path,
            "issue_basis":[
                "<BSL0000 is used for the special-boss path",
                "maintainer proposed checking bossEntity when event lookup cannot identify the special boss",
            ],
        },
    }
    authority={
        "scope":{
            "predicate_id":PREDICATE_ID,
            "target_identity":TARGET_ID,
            "target_revision":revision,
        },
        "basis":"issue_derived_bounded_static_source_probe",
        "evidence_ref":f"github:andwn/cave-story-md@{revision}:src/tsc.c#CMD_BSL",
    }
    if status=="TRUE":
        observation["positive_authority"]=authority
    elif status=="FALSE":
        observation["negative_authority"]=authority

    return {
        "schema_version":"0.3",
        "intervention":{
            "id":"repair-bsl0000-special-boss-healthbar",
            "kind":"modify_code",
            "description":"repair <BSL0000 special-boss health-bar resolution",
            "justified_by":[PREDICATE_ID],
        },
        "target":{
            "identity":TARGET_ID,
            "revision":revision,
            "environment":{"external_issue":ISSUE_REF},
        },
        "predicates":[
            {
                "id":PREDICATE_ID,
                "required":True,
                "kind":"reality",
                "role":"necessity",
            }
        ],
        "observations":{PREDICATE_ID:observation},
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("source",type=Path)
    parser.add_argument("--revision",required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()

    text=args.source.read_text(encoding="utf-8",errors="replace")
    status,reason=inspect_source(text)
    value=receipt(status,reason,args.revision,str(args.source))
    args.out.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":status,"reason":reason,"revision":args.revision},sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
