#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


ALLOWED={"ACT","ABSTAIN","INVESTIGATE","ESCALATE"}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_case(command: list[str], receipt: dict[str, Any], timeout: float) -> dict[str, Any]:
    proc=subprocess.run(
        command,
        input=json.dumps(receipt,sort_keys=True)+"\n",
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        return {
            "protocol_ok":False,
            "error":"evaluator_nonzero_exit",
            "exit_code":proc.returncode,
            "stderr":proc.stderr[-2000:],
        }
    stdout=proc.stdout.strip()
    try:
        value=json.loads(stdout)
    except json.JSONDecodeError as exc:
        return {
            "protocol_ok":False,
            "error":"evaluator_stdout_not_json",
            "detail":str(exc),
            "stdout":stdout[-2000:],
        }
    if not isinstance(value,dict):
        return {"protocol_ok":False,"error":"evaluator_output_not_object"}
    verdict=value.get("verdict")
    if verdict not in ALLOWED:
        return {
            "protocol_ok":False,
            "error":"invalid_verdict",
            "verdict":verdict,
        }
    return {
        "protocol_ok":True,
        "verdict":verdict,
        "details":value.get("details"),
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",type=Path,default=Path(__file__).with_name("manifest.json"))
    parser.add_argument("--evaluator",required=True,help="command invoked once per vector")
    parser.add_argument("--timeout",type=float,default=10.0)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()

    manifest=_load(args.manifest)
    if manifest.get("schema_version")!="rn-conformance-pack/0.1":
        raise SystemExit("unsupported conformance manifest version")
    vector_path=args.manifest.parent / manifest["vectors"]
    vectors=_load(vector_path)
    if not isinstance(vectors,list) or not vectors:
        raise SystemExit("conformance vectors must be a non-empty list")

    command=shlex.split(args.evaluator)
    if not command:
        raise SystemExit("empty evaluator command")

    cases=[]
    passed=0
    for case in vectors:
        cid=case.get("id")
        expected=case.get("expected")
        receipt=case.get("receipt")
        if not isinstance(cid,str) or expected not in ALLOWED or not isinstance(receipt,dict):
            raise SystemExit(f"invalid conformance vector: {cid!r}")
        try:
            observed=run_case(command,receipt,args.timeout)
        except subprocess.TimeoutExpired:
            observed={"protocol_ok":False,"error":"evaluator_timeout"}
        ok=observed.get("protocol_ok") is True and observed.get("verdict")==expected
        passed += int(ok)
        cases.append({
            "id":cid,
            "expected":expected,
            "observed":observed.get("verdict"),
            "protocol_ok":observed.get("protocol_ok",False),
            "pass":ok,
            "error":observed.get("error"),
        })

    report={
        "schema_version":"rn-conformance-report/0.1",
        "pack_version":manifest["schema_version"],
        "receipt_schema_version":manifest["receipt_schema_version"],
        "total":len(cases),
        "passed":passed,
        "failed":len(cases)-passed,
        "cases":cases,
    }
    rendered=json.dumps(report,indent=2,sort_keys=True)+"\n"
    if args.out:
        args.out.write_text(rendered,encoding="utf-8")
    print(rendered,end="")
    return 0 if report["failed"]==0 else 1


if __name__=="__main__":
    raise SystemExit(main())
