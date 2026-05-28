#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge de dois relatórios JSON do validate_sources.py em um único.

Uso:
    python scripts/merge_freshness_reports.py report1.json report2.json > combined.json
"""
from __future__ import annotations

import json
import sys
from datetime import date


def load(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"timestamp": "", "total": 0, "ok": 0, "warnings": 0, "errors": 0, "results": []}


def main() -> int:
    if len(sys.argv) < 2:
        print("uso: merge_freshness_reports.py <r1.json> [<r2.json> ...]", file=sys.stderr)
        return 2

    merged_results: list[dict] = []
    for path in sys.argv[1:]:
        r = load(path)
        merged_results.extend(r.get("results", []))

    combined = {
        "timestamp": date.today().isoformat(),
        "total": len(merged_results),
        "ok": sum(1 for r in merged_results if r.get("status") == "ok"),
        "warnings": sum(1 for r in merged_results if r.get("status") == "warning"),
        "errors": sum(1 for r in merged_results if r.get("status") == "error"),
        "results": merged_results,
    }
    print(json.dumps(combined, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
