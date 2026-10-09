#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",type=Path,default=Path(__file__).with_name("manifest.json"))
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()

    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    vectors=args.manifest.parent/manifest["vectors"]
    receipt_schema=args.manifest.parent.parent/"schema"/"necessity.schema.json"
    value={
        "schema_version":"rn-conformance-lock/0.1",
        "pack_version":manifest["schema_version"],
        "receipt_schema_version":manifest["receipt_schema_version"],
        "files":{
            str(vectors.relative_to(args.manifest.parent.parent)):f"sha256:{sha256(vectors)}",
            str(receipt_schema.relative_to(args.manifest.parent.parent)):f"sha256:{sha256(receipt_schema)}",
            str(args.manifest.relative_to(args.manifest.parent.parent)):f"sha256:{sha256(args.manifest)}",
        },
    }
    args.out.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(value,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
