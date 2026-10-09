#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: inspect_blind_shape.py BLIND.json", file=sys.stderr)
        return 2

    rows = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise SystemExit("expected non-empty blind list")

    keys = sorted({key for row in rows if isinstance(row, dict) for key in row})
    first = rows[0]
    shape = {key: type(first.get(key)).__name__ for key in keys}
    print(json.dumps({
        "rows": len(rows),
        "keys": keys,
        "first_row_value_types": shape,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
