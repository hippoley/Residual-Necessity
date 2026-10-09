#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"audit"/"user_story_horizontal_matrix.json"
AUDIT_PATH=ROOT/"docs"/"USER_STORY_AUDIT.md"
VALID={"verified","partial","open","blocked","not_applicable"}


def _audit_story_ids() -> set[str]:
    text=AUDIT_PATH.read_text(encoding="utf-8")
    return set(re.findall(r"\|\s*(US-\d+[a-z]?)\s*\|", text))


def _dependency_cycle(stories: list[dict]) -> list[str] | None:
    graph={story["id"]: list(story.get("dependencies",[])) for story in stories}
    visiting:set[str]=set()
    visited:set[str]=set()
    stack:list[str]=[]

    def visit(node: str) -> list[str] | None:
        if node in visiting:
            i=stack.index(node)
            return stack[i:]+[node]
        if node in visited:
            return None
        visiting.add(node)
        stack.append(node)
        for dep in graph.get(node,[]):
            cycle=visit(dep)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for node in sorted(graph):
        cycle=visit(node)
        if cycle:
            return cycle
    return None


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

        statuses=[item["status"] for item in story["dimensions"].values()]
        if "blocked" in statuses:
            expected_horizontal="blocked"
        elif "open" in statuses:
            expected_horizontal="open"
        elif "partial" in statuses:
            expected_horizontal="partial"
        else:
            expected_horizontal="verified"

        if story.get("horizontal_status") != expected_horizontal:
            errors.append(
                f"{sid}: horizontal_status={story.get('horizontal_status')!r} "
                f"expected {expected_horizontal!r}"
            )

        if story["vertical_status"]=="closed" and expected_horizontal=="verified":
            expected_closure="verified_closed"
        elif story["vertical_status"]=="blocked" or expected_horizontal=="blocked":
            expected_closure="blocked"
        elif story["vertical_status"]=="open" or expected_horizontal=="open":
            expected_closure="open"
        else:
            expected_closure="partial"

        if story.get("closure_status") != expected_closure:
            errors.append(
                f"{sid}: closure_status={story.get('closure_status')!r} "
                f"expected {expected_closure!r}"
            )
    matrix_ids={story["id"] for story in data["stories"]}
    audit_ids=_audit_story_ids()
    if matrix_ids != audit_ids:
        missing=sorted(audit_ids-matrix_ids)
        extra=sorted(matrix_ids-audit_ids)
        errors.append(f"story ledger mismatch: missing_from_matrix={missing} extra_in_matrix={extra}")

    cycle=_dependency_cycle(data["stories"])
    if cycle:
        errors.append("dependency cycle: " + " -> ".join(cycle))

    for story in data["stories"]:
        for dep in story.get("dependencies",[]):
            if dep not in ids: errors.append(f"{story['id']}: unknown dependency {dep}")
        if story.get("closure_status")=="verified_closed":
            nonverified=[
                name for name,item in story["dimensions"].items()
                if item["status"] not in {"verified","not_applicable"}
            ]
            if nonverified:
                errors.append(
                    f"{story['id']}: verified_closed with nonverified dimensions: {nonverified}"
                )
    return errors

if __name__=="__main__":
    data=json.loads(PATH.read_text(encoding="utf-8"))
    errors=validate(data)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"HORIZONTAL_COMPLETENESS_MATRIX=PASS stories={len(data['stories'])}")
