#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIRS = ("src", "schema", "examples", "conformance", "experiments")
FORBIDDEN = ('"schema_version": "0.2"', "'schema_version': '0.2'")

def main() -> int:
    violations: list[str] = []
    for dirname in RUNTIME_DIRS:
        base = ROOT / dirname
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".json", ".md", ".yaml", ".yml"}:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for token in FORBIDDEN:
                if token in text:
                    violations.append(f"{path.relative_to(ROOT)} contains legacy receipt token {token}")
    if violations:
        raise SystemExit("\n".join(sorted(violations)))
    print("RECEIPT_SCHEMA_03_MIGRATION=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
