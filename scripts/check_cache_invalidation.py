#!/usr/bin/env python3
"""check_cache_invalidation.py — pre-push gate.

Falha se ha mudancas em js/app.js ou data/*.json em relacao a origin/main
SEM bump correspondente em sw.js (linha CACHE_VERSION).

Logica:
  1. Resolve base de comparacao: origin/main se disponivel, fallback HEAD~1.
  2. Lista arquivos alterados via git diff --name-only base...HEAD.
  3. Se nenhum match em {js/app.js, data/*.json}, exit 0.
  4. Verifica se sw.js tambem mudou E se a linha CACHE_VERSION foi alterada.
  5. Falha se ha mudanca em cache-relevant mas CACHE_VERSION nao bumpou.

CI-safe: skip se git diff nao consegue calcular base.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


CACHE_RELEVANT = re.compile(r"^(js/app\.js|data/[^/]+\.json)$")
CACHE_VERSION_LINE = re.compile(r"^[+-]const CACHE_VERSION\s*=", re.MULTILINE)


def run(cmd: list[str]) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return r.returncode, (r.stdout or "")
    except FileNotFoundError:
        return 127, ""


def resolve_base() -> str | None:
    """Tenta origin/main; fallback HEAD~1; senao None."""
    rc, _ = run(["git", "rev-parse", "--verify", "origin/main"])
    if rc == 0:
        return "origin/main"
    rc, _ = run(["git", "rev-parse", "--verify", "HEAD~1"])
    if rc == 0:
        return "HEAD~1"
    return None


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    sw = repo / "sw.js"
    if not sw.exists():
        print("⚠️  check_cache_invalidation: sw.js nao encontrado — skip.")
        return 0

    base = resolve_base()
    if not base:
        print("ℹ️  check_cache_invalidation: sem base (origin/main ou HEAD~1) — skip.")
        return 0

    rc, names_raw = run(["git", "diff", "--name-only", f"{base}...HEAD"])
    if rc != 0:
        print(f"⚠️  check_cache_invalidation: git diff {base}...HEAD falhou — skip.")
        return 0

    names = [n for n in names_raw.splitlines() if n.strip()]
    cache_relevant_changed = [n for n in names if CACHE_RELEVANT.match(n)]
    if not cache_relevant_changed:
        return 0  # Nada relevante mudou.

    # Verifica se sw.js esta no diff E se a linha CACHE_VERSION foi alterada.
    sw_changed = "sw.js" in names
    cache_line_bumped = False
    if sw_changed:
        rc, diff_sw = run(["git", "diff", f"{base}...HEAD", "--", "sw.js"])
        if rc == 0 and CACHE_VERSION_LINE.search(diff_sw):
            cache_line_bumped = True

    if not cache_line_bumped:
        print("❌ check_cache_invalidation: arquivos relevantes para cache mudaram")
        print("   mas CACHE_VERSION em sw.js NAO foi bumpado.")
        print()
        print("   Arquivos modificados que requerem invalidacao:")
        for n in cache_relevant_changed[:10]:
            print(f"     • {n}")
        if len(cache_relevant_changed) > 10:
            print(f"     ... e mais {len(cache_relevant_changed) - 10}")
        print()
        print("   → Edite sw.js e bump da linha:")
        print("       const CACHE_VERSION = 'nossodireito-vX.Y.Z';")
        print("     Em geral, alinhe com manifest.json (use bump_version.py).")
        print()
        print("   Bypass (NAO recomendado): git push --no-verify")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
