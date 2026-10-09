#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MATRIX=ROOT/"audit"/"user_story_horizontal_matrix.json"

def load():
    return json.loads(MATRIX.read_text(encoding="utf-8"))

def impacted(story_ids: list[str]) -> list[str]:
    data=load()
    known={s["id"] for s in data["stories"]}
    unknown=sorted(set(story_ids)-known)
    if unknown:
        raise ValueError(f"unknown story ids: {unknown}")

    reverse: dict[str,set[str]]=defaultdict(set)
    for story in data["stories"]:
        for dep in story.get("dependencies",[]):
            reverse[dep].add(story["id"])

    seen=set(story_ids)
    q=deque(story_ids)
    while q:
        current=q.popleft()
        for child in sorted(reverse.get(current,set())):
            if child not in seen:
                seen.add(child)
                q.append(child)
    return sorted(seen)

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("story_ids", nargs="+")
    parser.add_argument("--json", action="store_true")
    args=parser.parse_args()
    result=impacted(args.story_ids)
    if args.json:
        print(json.dumps({"changed":args.story_ids,"regression_scope":result},indent=2))
    else:
        print("\n".join(result))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
