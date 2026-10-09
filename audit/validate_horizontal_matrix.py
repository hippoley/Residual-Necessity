#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"audit"/"user_story_horizontal_matrix.json"
VALID={"verified","partial","open","blocked","not_applicable"}

def validate(data: dict) -> list[str]:
    errors=[]
    dims=data["dimensions"]
    ids=set()
    for story in data["stories"]:
        sid=story["id"]
        if sid in ids: errors.append(f"duplicate story id: {sid}")
        ids.add(sid)
        missing=set(dims)-set(story["dimensions"])
        extra=set(story["dimensions"])-set(dims)
        if missing: errors.append(f"{sid}: missing dimensions {sorted(missing)}")
        if extra: errors.append(f"{sid}: unknown dimensions {sorted(extra)}")
        for name in dims:
            item=story["dimensions"].get(name,{})
            status=item.get("status")
            if status not in VALID: errors.append(f"{sid}/{name}: invalid status {status!r}")
            if status=="not_applicable" and not item.get("reason"):
                errors.append(f"{sid}/{name}: not_applicable requires reason")
            if status!="not_applicable" and not item.get("evidence"):
                errors.append(f"{sid}/{name}: {status} requires evidence")
        for dep in story.get("dependencies",[]):
            if dep==sid: errors.append(f"{sid}: self dependency")
    for story in data["stories"]:
        for dep in story.get("dependencies",[]):
            if dep not in ids: errors.append(f"{story['id']}: unknown dependency {dep}")
        if story["vertical_status"]=="closed":
            blockers=[
                name for name,item in story["dimensions"].items()
                if item["status"] in {"open","blocked"}
            ]
            if blockers:
                errors.append(f"{story['id']}: closed vertically but horizontal blockers remain: {blockers}")
    return errors

if __name__=="__main__":
    data=json.loads(PATH.read_text(encoding="utf-8"))
    errors=validate(data)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"HORIZONTAL_COMPLETENESS_MATRIX=PASS stories={len(data['stories'])}")
