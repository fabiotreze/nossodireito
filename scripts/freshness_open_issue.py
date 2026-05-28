#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Abre (ou atualiza) issue automática quando o validador de fontes detecta drift.

Idempotente: se existir issue aberta com o label 'content-stale', atualiza o
corpo (em vez de criar duplicata). Se não houver erros/warnings, fecha issue
aberta existente com comentário.

Uso:
    python scripts/freshness_open_issue.py validation_combined.json

Requer:
    - GH_TOKEN no environment (GitHub Actions já injeta GITHUB_TOKEN)
    - `gh` CLI disponível no PATH
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

LABEL = "content-stale"
TITLE = "[Auto] Drift de fontes oficiais detectado"
MAX_LIST = 30  # truncar listas longas no corpo


def gh(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=check)


def ensure_label_exists() -> None:
    result = gh("label", "list", "--limit", "200", "--json", "name", check=False)
    if result.returncode == 0:
        names = {x.get("name") for x in json.loads(result.stdout or "[]")}
        if LABEL in names:
            return
    gh(
        "label", "create", LABEL,
        "--description", "Conteúdo desatualizado detectado por content-freshness.yml",
        "--color", "fbca04",
        check=False,
    )


def find_open_issue() -> int | None:
    result = gh(
        "issue", "list",
        "--state", "open",
        "--label", LABEL,
        "--limit", "5",
        "--json", "number,title",
    )
    items = json.loads(result.stdout or "[]")
    for it in items:
        if it.get("title") == TITLE:
            return int(it["number"])
    return None


def render_body(report: dict, repo: str, run_id: str) -> str:
    by_source: dict[str, list[dict]] = {}
    for r in report.get("results", []):
        if r.get("status") in {"warning", "error"}:
            by_source.setdefault(r.get("source", "?"), []).append(r)

    lines: list[str] = [
        "> Issue auto-gerada por `.github/workflows/content-freshness.yml`.",
        "> Idempotente: este corpo é reescrito a cada execução semanal.",
        "",
        f"**Última execução:** {report.get('timestamp', date.today().isoformat())}  ",
        f"**Resumo:** {report.get('ok', 0)} ok · {report.get('warnings', 0)} warnings · {report.get('errors', 0)} errors  ",
        f"**Run completo:** https://github.com/{repo}/actions/runs/{run_id}",
        "",
        "---",
        "",
    ]

    if not by_source:
        lines += [
            "✅ **Nenhum drift detectado nesta execução.**",
            "",
            "Esta issue pode ser fechada manualmente, ou aguarde — o workflow fechará",
            "automaticamente na próxima execução limpa.",
        ]
        return "\n".join(lines)

    icons = {"error": "🔴", "warning": "🟡"}
    source_labels = {
        "url": "URLs quebradas",
        "legislacao": "Legislação (Senado Federal)",
        "cid": "Códigos CID (OMS ICD API)",
    }

    for source, items in sorted(by_source.items()):
        label = source_labels.get(source, source)
        lines.append(f"## {label} ({len(items)})")
        lines.append("")
        for r in items[:MAX_LIST]:
            icon = icons.get(r.get("status"), "·")
            item = r.get("item", "?")
            msg = r.get("message", "")
            url = r.get("url", "")
            code = r.get("http_code", 0)
            extra = f" — HTTP {code}" if code else ""
            link = f" — {url}" if url else ""
            lines.append(f"- {icon} **{item}**{extra}: {msg}{link}")
        if len(items) > MAX_LIST:
            lines.append(f"- _…{len(items) - MAX_LIST} item(ns) adicional(is) — ver artifact do run_")
        lines.append("")

    lines += [
        "---",
        "",
        "## Como agir",
        "",
        "1. **URL quebrada** → atualizar `data/direitos.json` (campo `links` ou `base_legal.link`) e rodar `python scripts/validate_sources.py --urls`.",
        "2. **Lei revogada/inexistente no Senado** → conferir vigência no Planalto e ajustar `base_legal`.",
        "3. **CID inválido na OMS** → revisar `cids_relacionados` da categoria afetada; se for CID-11, confirmar mapeamento contra `id.who.int/icd`.",
        "",
        "Após correção, re-rodar manualmente o workflow ou aguardar próxima execução (segunda 05:00 UTC).",
    ]
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 2:
        print("uso: freshness_open_issue.py <combined.json>", file=sys.stderr)
        return 2

    report_path = Path(sys.argv[1])
    if not report_path.exists():
        print(f"relatório não encontrado: {report_path}", file=sys.stderr)
        return 2

    with report_path.open(encoding="utf-8") as f:
        report = json.load(f)

    has_drift = report.get("errors", 0) > 0 or report.get("warnings", 0) > 0
    repo = os.environ.get("GITHUB_REPOSITORY", "fabiotreze/nossodireito")
    run_id = os.environ.get("GITHUB_RUN_ID", "")

    ensure_label_exists()
    existing = find_open_issue()
    body = render_body(report, repo, run_id)

    if has_drift:
        if existing:
            print(f"Atualizando issue #{existing} (drift ainda presente)")
            gh("issue", "edit", str(existing), "--body", body)
        else:
            print("Abrindo nova issue (drift novo)")
            gh(
                "issue", "create",
                "--title", TITLE,
                "--body", body,
                "--label", LABEL,
            )
    else:
        if existing:
            print(f"Fechando issue #{existing} (drift resolvido)")
            gh(
                "issue", "comment", str(existing),
                "--body", "✅ Execução semanal sem drift. Fechando automaticamente.",
            )
            gh("issue", "close", str(existing), "--reason", "completed")
        else:
            print("Sem drift e sem issue existente — nada a fazer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
