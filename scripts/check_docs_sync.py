#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_docs_sync.py — Bloqueia commits/PRs quando docs estão dessincronizadas.

Verifica:
  1. len(data/direitos.json["categorias"]) == número citado em README/docs
     ("N categorias", "(N+1) URLs", etc.)
  2. manifest.json["version"] == header "**Version:** X.Y.Z" em cada doc que
     declarar esse cabeçalho (docs/*.md, GOVERNANCE.md, SECURITY_AUDIT.md).
  3. CHANGELOG.md — a seção [versão_atual] NÃO contém boilerplate literal
     "(descrever mudanças aqui)" deixado pelo bump_version.py.
  4. (WARN) README não contém score hardcoded antigo (1109.7/1113.2 etc).

Exit codes:
  0 = tudo sincronizado
  1 = drift detectado (bloqueia commit no pre-commit hook)
  2 = erro de setup (arquivo essencial faltando)

Uso:
  python3 scripts/check_docs_sync.py            # roda todos os checks
  python3 scripts/check_docs_sync.py --quiet    # só mostra falhas
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Arquivos com cabeçalho "**Version:** X.Y.Z" obrigatório
VERSIONED_DOCS = [
    "docs/ARCHITECTURE.md",
    "docs/COST-ESTIMATE.md",
    "docs/OPERATIONS.md",
    "docs/SECURITY-LGPD.md",
    "docs/REPLICATION.md",
    "docs/README.md",
    "GOVERNANCE.md",
]

# Arquivos onde a contagem de categorias é citada e DEVE bater
COUNTED_FILES = [
    "README.md",
    "docs/ARCHITECTURE.md",
]

CHANGELOG = "CHANGELOG.md"
BOILERPLATE_MARKER = "- (descrever mudanças aqui)"

# Padrões de score antigo que NÃO devem aparecer mais (hardcoded de v1.21)
OBSOLETE_SCORE_PATTERNS = [
    r"1109\.7\s*/\s*1113\.2",
    r"99\.7%\s+across\s+30",
]

VERSION_HEADER_RE = re.compile(r"^\s*\*\*Version:\*\*\s*([0-9]+\.[0-9]+\.[0-9]+)", re.MULTILINE)
COUNT_PHRASES = [
    # (regex que captura o número, descrição)
    (re.compile(r"\b(\d+)\s+categorias?\b", re.IGNORECASE), "categorias"),
    (re.compile(r"\b(\d+)\s+rights\s+categor", re.IGNORECASE), "rights categories"),
    (re.compile(r"\((\d+)\s+categorias[^)]*\)"), "JSON line"),
    (re.compile(r"\b(\d+)\s+URLs\b"), "URLs (sitemap)"),
    (re.compile(r"\b(\d+)\s+paginas?\s+HTML", re.IGNORECASE), "páginas HTML"),
    (re.compile(r"home\s*\+\s*(\d+)\s+direitos", re.IGNORECASE), "home + N direitos"),
]


class CheckResult:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def check_categoria_counts(r: CheckResult) -> None:
    direitos_path = ROOT / "data" / "direitos.json"
    if not direitos_path.exists():
        r.err(f"essencial faltando: {direitos_path}")
        return
    try:
        data = json.loads(direitos_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        r.err(f"data/direitos.json inválido: {e}")
        return
    n = len(data.get("categorias", []))
    if n == 0:
        r.err("data/direitos.json: 0 categorias (esperado >0)")
        return

    valid_counts = {n, n + 1}  # n = categorias, n+1 = URLs (home + N)
    # Contextos onde "N categorias" refere-se a checks/validação do Quality Gate,
    # NÃO a categorias de direitos — ignorar nesses casos.
    CHECK_CONTEXT_WORDS = (
        "quality gate", "master_compliance", "master compliance", "score",
        "compliance", "validação", "validacao", "validation", "checks",
        "ci/cd", "ci ", "cobertura", "auditoria",
    )

    for rel in COUNTED_FILES:
        path = ROOT / rel
        text = _read(path)
        if not text:
            continue
        for pattern, label in COUNT_PHRASES:
            for match in pattern.finditer(text):
                found = int(match.group(1))
                if found in valid_counts:
                    continue
                # plausibilidade: contagem de categorias é 10..100
                if not (10 <= found <= 100):
                    continue
                # janela de contexto ±120 chars
                ctx_start = max(0, match.start() - 120)
                ctx_end = min(len(text), match.end() + 120)
                ctx = text[ctx_start:ctx_end].lower()
                if any(w in ctx for w in CHECK_CONTEXT_WORDS):
                    continue  # refere-se a checks, não a direitos
                line_no = text[: match.start()].count("\n") + 1
                snippet = match.group(0)
                r.err(
                    f"{rel}:{line_no} — '{snippet}' ({label}) "
                    f"≠ atual ({n} categorias / {n + 1} URLs)"
                )


def check_version_headers(r: CheckResult) -> None:
    manifest_path = ROOT / "manifest.json"
    if not manifest_path.exists():
        r.err(f"essencial faltando: {manifest_path}")
        return
    try:
        current = json.loads(manifest_path.read_text(encoding="utf-8"))["version"]
    except (json.JSONDecodeError, KeyError) as e:
        r.err(f"manifest.json sem 'version' válida: {e}")
        return

    for rel in VERSIONED_DOCS:
        path = ROOT / rel
        text = _read(path)
        if not text:
            continue
        matches = VERSION_HEADER_RE.findall(text)
        if not matches:
            # Sem header — ok (não obrigatório existir). Só checa se existir.
            continue
        for found in matches:
            if found != current:
                r.err(
                    f"{rel} — '**Version:** {found}' "
                    f"≠ manifest.json ({current})"
                )


def check_changelog_boilerplate(r: CheckResult) -> None:
    path = ROOT / CHANGELOG
    text = _read(path)
    if not text:
        r.warn(f"{CHANGELOG} não encontrado")
        return
    # Pega a seção mais recente (primeira "## [")
    m = re.search(r"^## \[([0-9.]+)\][^\n]*\n", text, re.MULTILINE)
    if not m:
        r.warn(f"{CHANGELOG}: nenhuma seção '## [x.y.z]' encontrada")
        return
    start = m.end()
    # Próxima seção
    next_m = re.search(r"^## \[", text[start:], re.MULTILINE)
    end = start + next_m.start() if next_m else len(text)
    section = text[start:end]
    if BOILERPLATE_MARKER in section:
        r.err(
            f"{CHANGELOG} — seção [{m.group(1)}] ainda contém boilerplate "
            f"'{BOILERPLATE_MARKER}'. Edite manualmente antes de commitar."
        )


def check_obsolete_scores(r: CheckResult) -> None:
    text = _read(ROOT / "README.md")
    for pat in OBSOLETE_SCORE_PATTERNS:
        if re.search(pat, text):
            r.err(
                f"README.md contém score obsoleto hardcoded (padrão '{pat}'). "
                f"Atualize com `python3 scripts/master_compliance.py` (score atual) "
                f"ou remova o número fixo."
            )


def check_git_tag_sync(r: CheckResult) -> None:
    """WARN se tag git mais recente não bater com manifest.json.
    Não bloqueia (a tag só deve existir após deploy bem-sucedido)."""
    import subprocess
    try:
        tag = subprocess.run(
            ["git", "tag", "--sort=-v:refname", "--list", "v[0-9]*"],
            capture_output=True, text=True, cwd=ROOT, timeout=10,
        ).stdout.strip().splitlines()
        latest = tag[0] if tag else None
    except Exception:
        return  # git indisponível: ignora silencioso
    if not latest:
        return
    try:
        manifest_v = "v" + json.loads(
            (ROOT / "manifest.json").read_text(encoding="utf-8")
        )["version"]
    except Exception:
        return
    if latest != manifest_v:
        r.warn(
            f"git tag mais recente ({latest}) ≠ manifest.json ({manifest_v}). "
            f"Rode `git tag {manifest_v} && git push origin {manifest_v}` após deploy."
        )


def check_prerendered_version_sync(r: CheckResult) -> None:
    """ERRO se HTMLs pre-renderizados em direitos/*/index.html contiverem
    versao diferente da do manifest.json. Indica que bump_version.py rodou
    mas prerender_direitos.py nao foi executado depois."""
    try:
        manifest_v = json.loads(
            (ROOT / "manifest.json").read_text(encoding="utf-8")
        )["version"]
    except Exception:
        return
    pat = re.compile(r"Vers[ãa]o dos dados:\s*(\d+\.\d+\.\d+)")
    stale: list[tuple[str, str]] = []
    for html_file in (ROOT / "direitos").glob("*/index.html"):
        try:
            txt = html_file.read_text(encoding="utf-8")
        except Exception:
            continue
        m = pat.search(txt)
        if m and m.group(1) != manifest_v:
            stale.append((html_file.relative_to(ROOT).as_posix(), m.group(1)))
    if stale:
        sample = ", ".join(f"{p} ({v})" for p, v in stale[:3])
        r.err(
            f"{len(stale)} pagina(s) pre-renderizada(s) com versao stale "
            f"(manifest={manifest_v}). Ex: {sample}. "
            f"Rode `python3 scripts/prerender_direitos.py`."
        )


def check_workflow_references(r: CheckResult) -> None:
    """ERRO se README/docs referenciam workflows .yml inexistentes.

    Cobre o gap descoberto em v1.34.2: ao desativar workflows (rename para
    .yml.disabled), READMEs/badges/diagrams continuavam apontando para arquivos
    que nao existem mais, causando badges quebrados e instrucoes obsoletas.
    """
    wf_dir = ROOT / ".github" / "workflows"
    if not wf_dir.is_dir():
        return
    active = {p.name for p in wf_dir.glob("*.yml")}  # .disabled NAO conta

    # Padroes que indicam referencia ATIVA a um workflow:
    #   - badge.svg URL: actions/workflows/<file>.yml/badge.svg
    #   - workflow page link: actions/workflows/<file>.yml
    #   - inline mention: `.github/workflows/<file>.yml`
    pat = re.compile(
        r"(?:actions/workflows/|\.github/workflows/)([a-z0-9_-]+\.yml)\b",
        re.IGNORECASE,
    )

    targets = [
        "README.md",
        "docs/ARCHITECTURE.md",
        "docs/OPERATIONS.md",
        "docs/REPLICATION.md",
        "docs/SECURITY-LGPD.md",
        "docs/README.md",
        "GOVERNANCE.md",
        "SECURITY.md",
    ]
    stale: list[tuple[str, str, int]] = []
    for rel in targets:
        f = ROOT / rel
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        # Pula arquivos marcados explicitamente como historicos/depreciados
        if re.search(r"^\s*>?\s*\*?\*?(DEPRECATED|HIST[ÓO]RICO|OBSOLETO)",
                     text[:500], re.IGNORECASE | re.MULTILINE):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for match in pat.finditer(line):
                wf = match.group(1).lower()
                if wf not in active:
                    stale.append((rel, wf, lineno))
    if stale:
        sample = "; ".join(f"{p}:{ln} -> {wf}" for p, wf, ln in stale[:5])
        r.err(
            f"{len(stale)} referencia(s) a workflow inexistente em docs. "
            f"Ex: {sample}. "
            f"Atualize a doc OU reative o workflow movendo `.yml.disabled` -> `.yml`."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida sincronia docs ↔ código.")
    parser.add_argument("--quiet", action="store_true", help="Só mostra falhas")
    args = parser.parse_args()

    r = CheckResult()
    check_categoria_counts(r)
    check_version_headers(r)
    check_changelog_boilerplate(r)
    check_obsolete_scores(r)
    check_git_tag_sync(r)
    check_prerendered_version_sync(r)
    check_workflow_references(r)

    if not args.quiet:
        print("═" * 60)
        print("  check_docs_sync — drift entre código e documentação")
        print("═" * 60)

    if r.warnings:
        for w in r.warnings:
            print(f"  ⚠️  {w}")

    if r.errors:
        print("")
        for e in r.errors:
            print(f"  ❌ {e}")
        print("")
        print(f"  ❌ FALHA — {len(r.errors)} drift(s) bloqueando commit.")
        print(f"     Corrija manualmente OU rode `python3 scripts/bump_version.py X.Y.Z`")
        return 1

    if not args.quiet:
        print("  ✅ OK — docs sincronizados com código (categorias, versões, CHANGELOG).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
