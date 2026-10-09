#!/usr/bin/env python3
"""Reference stdio adapter for the language-neutral conformance protocol."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("rn_reference_gate",ROOT/"src"/"gate.py")
assert spec and spec.loader
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def main() -> int:
    try:
        receipt=json.load(sys.stdin)
    except Exception as exc:
        print(json.dumps({"error":f"invalid_input:{type(exc).__name__}"}))
        return 2
    if not isinstance(receipt,dict):
        print(json.dumps({"error":"receipt_not_object"}))
        return 2
    verdict,reason=gate.evaluate(receipt)
    print(json.dumps({"verdict":verdict,"details":{"reason":reason}},sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
