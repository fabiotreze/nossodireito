#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NossoDireito — Bump Version Script
Atualiza a versão em TODOS os arquivos do projeto de uma só vez.

Uso:
    python scripts/bump_version.py 1.2.0
    python scripts/bump_version.py 1.2.0 --dry-run   # apenas mostra o que faria

Arquivos atualizados:
    1. package.json             → "version": "x.y.z"
    2. data/direitos.json       → "versao": "x.y.z"
    3. manifest.json            → "version": "x.y.z"
    4. sw.js                    → CACHE_VERSION = 'nossodireito-vx.y.z'
    5. index.html               → cache-bust ?v=x.y.z (CSS + JS refs)
    6. README.md                → badge Version-x.y.z
    6. GOVERNANCE.md            → **Versão:** x.y.z
    7. SECURITY_AUDIT.md        → título + referências
    8. docs/SECURITY-LGPD.md    → **Version:** x.y.z
    9. docs/ARCHITECTURE.md     → Versao: x.y.z
   10. master_compliance.py     → self.version = "x.y.z"
   11. CHANGELOG.md             → insere seção [x.y.z] (se não existir)
   12. scripts Python           → docstrings/banners "NossoDireito vx.y.z"
   13. docs/*.md consolidados   → **Versão:** x.y.z | **Atualizado:** data
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

# ── Configuração ──────────────────────────────────────────────────
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
ROOT = Path(__file__).resolve().parent.parent
TODAY = date.today().isoformat()


def validate_semver(version: str) -> str:
    """Valida formato semver x.y.z."""
    if not SEMVER_RE.match(version):
        print(f"❌ Versão inválida: '{version}' — use formato x.y.z (ex: 1.2.0)")
        sys.exit(1)
    return version


# ── Helpers ───────────────────────────────────────────────────────
def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str, *, dry_run: bool = False) -> None:
    if dry_run:
        return
    path.write_text(content, encoding="utf-8", newline="\n")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    """Substitui exatamente uma ocorrência ou avisa."""
    count = text.count(old)
    if count == 0:
        print(f"  ⚠️  Padrão não encontrado em {label}: {old!r}")
        return text
    if count > 1:
        print(f"  ⚠️  Múltiplas ocorrências ({count}) em {label} — substituindo todas")
    return text.replace(old, new)


# ── Atualizações por arquivo ──────────────────────────────────────
def bump_package_json(new: str, old: str, *, dry_run: bool) -> bool:
    path = ROOT / "package.json"
    data = json.loads(read_text(path))
    if data.get("version") == new:
        print(f"  ✅ package.json já está em {new}")
        return False
    data["version"] = new
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n", dry_run=dry_run)
    print(f"  ✅ package.json: {old} → {new}")
    return True


def bump_direitos_json(new: str, old: str, *, dry_run: bool) -> bool:
    path = ROOT / "data" / "direitos.json"
    text = read_text(path)
    old_pattern = f'"versao": "{old}"'
    new_pattern = f'"versao": "{new}"'
    if old_pattern not in text:
        if f'"versao": "{new}"' in text:
            print(f"  ✅ direitos.json já está em {new}")
            return False
        print(f"  ⚠️  direitos.json: padrão '{old_pattern}' não encontrado")
        return False
    # Também atualiza ultima_atualizacao
    text = text.replace(old_pattern, new_pattern)
    old_date_re = re.compile(r'"ultima_atualizacao":\s*"\d{4}-\d{2}-\d{2}"')
    text = old_date_re.sub(f'"ultima_atualizacao": "{TODAY}"', text)
    write_text(path, text, dry_run=dry_run)
    print(f"  ✅ direitos.json: {old} → {new} (data: {TODAY})")
    return True


def bump_dicionario_pcd_json(new: str, old: str, *, dry_run: bool) -> bool:
    """Atualiza versao e atualizado_em no dicionario_pcd.json."""
    path = ROOT / "data" / "dicionario_pcd.json"
    text = read_text(path)
    old_pattern = f'"versao": "{old}"'
    new_pattern = f'"versao": "{new}"'
    if old_pattern not in text:
        if f'"versao": "{new}"' in text:
            print(f"  ✅ dicionario_pcd.json já está em {new}")
            return False
        print(f"  ⚠️  dicionario_pcd.json: padrão '{old_pattern}' não encontrado")
        return False
    text = text.replace(old_pattern, new_pattern)
    old_date_re = re.compile(r'"atualizado_em":\s*"\d{4}-\d{2}-\d{2}"')
    text = old_date_re.sub(f'"atualizado_em": "{TODAY}"', text)
    write_text(path, text, dry_run=dry_run)
    print(f"  ✅ dicionario_pcd.json: {old} → {new} (data: {TODAY})")
    return True


def bump_sw_js(new: str, old: str, *, dry_run: bool) -> bool:
    path = ROOT / "sw.js"
    text = read_text(path)
    old_cache = f"'nossodireito-v{old}'"
    new_cache = f"'nossodireito-v{new}'"
    if old_cache not in text:
        if new_cache in text:
            print(f"  ✅ sw.js já está em {new}")
            return False
        print(f"  ⚠️  sw.js: padrão '{old_cache}' não encontrado")
        return False
    text = text.replace(old_cache, new_cache)
    write_text(path, text, dry_run=dry_run)
    print(f"  ✅ sw.js: CACHE_VERSION → nossodireito-v{new}")
    return True


def bump_index_html(new: str, old: str, *, dry_run: bool) -> bool:
    """Atualiza cache-bust query strings ?v=x.y.z no index.html."""
    path = ROOT / "index.html"
    text = read_text(path)
    old_qs = f"?v={old}"
    new_qs = f"?v={new}"
    if old_qs not in text:
        if new_qs in text:
            print(f"  ✅ index.html já está em {new}")
            return False
        print(f"  ⚠️  index.html: padrão '{old_qs}' não encontrado")
        return False
    text = text.replace(old_qs, new_qs)
    write_text(path, text, dry_run=dry_run)
    count = text.count(new_qs)
    print(f"  ✅ index.html: cache-bust ?v={old} → ?v={new} ({count} refs)")
    return True


def bump_readme(new: str, old: str, *, dry_run: bool) -> bool:
    path = ROOT / "README.md"
    text = read_text(path)
    changed = False

    # 1) Shields.io badge "Version-X.Y.Z"
    old_badge = f"Version-{old}"
    new_badge = f"Version-{new}"
    if old_badge in text:
        text = text.replace(old_badge, new_badge)
        changed = True
        print(f"  ✅ README.md: badge → {new}")
    elif new_badge not in text:
        print(f"  ⚠️  README.md: badge '{old_badge}' não encontrado")

    # 2) Headings com versao embutida (evita drift apontado em PR #101)
    #    "## 📘 Documentação consolidada (vX.Y.Z)"
    #    "## 🎉 NOVIDADES vX.Y.Z (...) — ..."
    import re as _re
    pat_doc = _re.compile(r"(Documentação consolidada \(v)" + _re.escape(old) + r"(\))")
    new_text, n = pat_doc.subn(r"\g<1>" + new + r"\g<2>", text)
    if n:
        text = new_text
        changed = True
        print(f"  ✅ README.md: heading 'Documentação consolidada' → v{new}")

    pat_nov = _re.compile(r"(NOVIDADES v)" + _re.escape(old) + r"(\s)")
    new_text, n = pat_nov.subn(r"\g<1>" + new + r"\g<2>", text)
    if n:
        text = new_text
        changed = True
        print(f"  ✅ README.md: heading 'NOVIDADES' → v{new}")

    if changed:
        write_text(path, text, dry_run=dry_run)
    else:
        print(f"  ℹ️  README.md: nenhuma mudança (já em {new}?)")
    return changed


def bump_changelog(new: str, old: str, *, dry_run: bool) -> bool:
    path = ROOT / "CHANGELOG.md"
    text = read_text(path)
    section_header = f"## [{new}]"
    if section_header in text:
        print(f"  ✅ CHANGELOG.md já tem seção [{new}]")
        return False
    # Insere nova seção após o header do changelog
    old_section = f"## [{old}]"
    if old_section not in text:
        print(f"  ⚠️  CHANGELOG.md: seção [{old}] não encontrada")
        return False
    new_section = (
        f"## [{new}] - {TODAY}\n"
        f"\n"
        f"### Adicionado\n"
        f"\n"
        f"- (descrever mudanças aqui)\n"
        f"\n"
        f"---\n"
        f"\n"
    )
    text = text.replace(old_section, new_section + old_section)
    write_text(path, text, dry_run=dry_run)
    print(f"  ✅ CHANGELOG.md: seção [{new}] inserida")
    return True


def bump_manifest_json(new: str, old: str, *, dry_run: bool) -> bool:
    path = ROOT / "manifest.json"
    data = json.loads(read_text(path))
    if data.get("version") == new:
        print(f"  ✅ manifest.json já está em {new}")
        return False
    data["version"] = new
    write_text(path, json.dumps(data, indent=4, ensure_ascii=False) + "\n", dry_run=dry_run)
    print(f"  ✅ manifest.json: {old} → {new}")
    return True


VERSIONED_DOCS = [
    "docs/ARCHITECTURE.md",
    "docs/COST-ESTIMATE.md",
    "docs/OPERATIONS.md",
    "docs/SECURITY-LGPD.md",
    "docs/REPLICATION.md",
    "docs/README.md",
    "GOVERNANCE.md",
]


def bump_docs_headers(new: str, *, dry_run: bool) -> bool:
    """Atualiza '**Version:** X.Y.Z' e '**Updated:** YYYY-MM-DD' em docs/*.md
    que já possuem esses cabeçalhos. Também aceita variante '**Versão:**'
    e 'Versao:' (sem markdown). Idempotente.
    """
    import re as _re
    any_changed = False
    ver_pat = _re.compile(r"(\*\*(?:Version|Vers[aã]o):\*\*\s*)[0-9]+\.[0-9]+\.[0-9]+", _re.IGNORECASE)
    upd_pat = _re.compile(r"(\*\*(?:Updated|Atualizado):\*\*\s*)\d{4}-\d{2}-\d{2}", _re.IGNORECASE)
    # tambem atualiza '**Última revisão:** YYYY-MM-DD' / '**Last review:** YYYY-MM-DD'
    rev_pat = _re.compile(r"(\*\*(?:Última revisão|Ultima revisao|Last review):\*\*\s*)\d{4}-\d{2}-\d{2}", _re.IGNORECASE)
    for rel in VERSIONED_DOCS:
        path = ROOT / rel
        if not path.exists():
            continue
        text = read_text(path)
        new_text, n_ver = ver_pat.subn(r"\g<1>" + new, text)
        new_text, n_upd = upd_pat.subn(r"\g<1>" + TODAY, new_text)
        new_text, n_rev = rev_pat.subn(r"\g<1>" + TODAY, new_text)
        if n_ver or n_upd or n_rev:
            write_text(path, new_text, dry_run=dry_run)
            print(f"  ✅ {rel}: Version→{new} (n={n_ver}), Updated→{TODAY} (n={n_upd}), Revisão→{TODAY} (n={n_rev})")
            any_changed = True
    return any_changed


# ── Detecção da versão atual ──────────────────────────────────────
def detect_current_version() -> str:
    """Lê a versão atual de package.json."""
    path = ROOT / "package.json"
    data = json.loads(read_text(path))
    version = data.get("version", "")
    if not SEMVER_RE.match(version):
        print(f"❌ package.json contém versão inválida: '{version}'")
        sys.exit(1)
    return version


# ── Main ──────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bump versão do NossoDireito em todos os arquivos.",
        epilog="Ex: python scripts/bump_version.py 1.2.0",
    )
    parser.add_argument("version", help="Nova versão (semver x.y.z)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas mostra o que seria alterado, sem gravar",
    )
    args = parser.parse_args()

    new_version = validate_semver(args.version)
    old_version = detect_current_version()

    if new_version == old_version:
        print(f"ℹ️  Versão já é {new_version} — nada a fazer.")
        sys.exit(0)

    mode = " (DRY RUN)" if args.dry_run else ""
    print(f"\n🔄 Bump: {old_version} → {new_version}{mode}")
    print(f"📅 Data: {TODAY}")
    print("─" * 50)

    results = [
        bump_package_json(new_version, old_version, dry_run=args.dry_run),
        bump_direitos_json(new_version, old_version, dry_run=args.dry_run),
        bump_dicionario_pcd_json(new_version, old_version, dry_run=args.dry_run),
        bump_manifest_json(new_version, old_version, dry_run=args.dry_run),
        bump_sw_js(new_version, old_version, dry_run=args.dry_run),
        bump_index_html(new_version, old_version, dry_run=args.dry_run),
        bump_readme(new_version, old_version, dry_run=args.dry_run),
        bump_changelog(new_version, old_version, dry_run=args.dry_run),
        bump_docs_headers(new_version, dry_run=args.dry_run),
    ]

    print("─" * 50)
    changed = sum(results)
    if args.dry_run:
        print(f"🔍 Dry run: {changed} arquivo(s) seriam alterados.")
    else:
        print(f"✅ {changed} arquivo(s) atualizado(s) para v{new_version}.")

        # Regenera HTMLs pre-renderizados em direitos/*/index.html
        # (cada arquivo contem "Versao dos dados: X.Y.Z" hardcoded vindo
        # de data/direitos.json; sem este passo, ficam dessincronizados)
        print("\n🔁 Regenerando paginas pre-renderizadas (direitos/*/index.html)...")
        import subprocess
        try:
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "prerender_direitos.py")],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  prerender_direitos.py falhou (rc={e.returncode}). "
                  f"Rode manualmente apos verificar.")

        print(f"\n📝 Lembre-se de editar CHANGELOG.md com as mudanças reais.")


if __name__ == "__main__":
    main()
