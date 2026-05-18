#!/usr/bin/env python3
"""check_semver_bump.py — pre-push gate.

Falha se HEAD contem commits 'feat:' ou 'BREAKING CHANGE' desde a ultima tag
mas manifest.json.version NAO foi bumpado em relacao a essa tag.

Logica:
  1. Pega ultima tag (git describe --tags --abbrev=0). Se nao houver, exit 0.
  2. Le manifest.json -> version_now.
  3. Le manifest.json @ tag -> version_tag (via git show).
  4. Se version_now == version_tag E ha 'feat'/'BREAKING' nos commits desde a
     tag -> FALHA com instrucao de rodar bump_version.py.
  5. Caso contrario, exit 0.

CI-safe: skip gracioso se git history/tags nao disponiveis.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return r.returncode, (r.stdout or "").strip()
    except FileNotFoundError:
        return 127, ""


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    manifest = repo / "manifest.json"
    if not manifest.exists():
        print("⚠️  check_semver_bump: manifest.json nao encontrado — skip.")
        return 0

    # 1. Ultima tag
    rc, last_tag = run(["git", "describe", "--tags", "--abbrev=0"])
    if rc != 0 or not last_tag:
        print("ℹ️  check_semver_bump: sem tags ainda — skip (release inicial).")
        return 0

    # 2. Versao atual
    try:
        version_now = json.loads(manifest.read_text(encoding="utf-8")).get("version")
    except (OSError, json.JSONDecodeError) as exc:
        print(f"❌ check_semver_bump: manifest.json invalido: {exc}")
        return 1
    if not version_now:
        print("❌ check_semver_bump: manifest.json sem campo 'version'.")
        return 1

    # 3. Versao na tag
    rc, manifest_at_tag = run(["git", "show", f"{last_tag}:manifest.json"])
    if rc != 0:
        print(f"⚠️  check_semver_bump: nao consegui ler manifest.json @ {last_tag} — skip.")
        return 0
    try:
        version_tag = json.loads(manifest_at_tag).get("version")
    except json.JSONDecodeError:
        print(f"⚠️  check_semver_bump: manifest.json @ {last_tag} invalido — skip.")
        return 0

    # 4. Commits desde tag
    rc, log_out = run(["git", "log", f"{last_tag}..HEAD", "--format=%s%n%b", "--no-merges"])
    if rc != 0:
        print(f"⚠️  check_semver_bump: git log {last_tag}..HEAD falhou — skip.")
        return 0
    if not log_out.strip():
        # Nenhum commit novo: nada a verificar.
        return 0

    feat_re = re.compile(r"^(feat)(\([a-z0-9_-]+\))?!?:", re.MULTILINE)
    breaking_re = re.compile(r"BREAKING[ -]CHANGE", re.IGNORECASE)
    has_feat = bool(feat_re.search(log_out))
    has_breaking = bool(breaking_re.search(log_out))

    if (has_feat or has_breaking) and version_now == version_tag:
        kind = "BREAKING CHANGE" if has_breaking else "feat:"
        print("❌ check_semver_bump: commits novos contem", kind)
        print(f"   ultima tag: {last_tag} (version={version_tag})")
        print(f"   manifest.json atual: {version_now}  (NAO bumpado)")
        print()
        print("   → rode: python3 scripts/bump_version.py X.Y.Z")
        if has_breaking:
            print("     (BREAKING CHANGE = bump MAJOR)")
        elif has_feat:
            print("     (feat: = bump MINOR)")
        print()
        print("   Bypass (NAO recomendado): git push --no-verify")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
