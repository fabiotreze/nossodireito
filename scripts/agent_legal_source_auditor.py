#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent: Legal Source Auditor
============================
Valida automaticamente fontes legais e URLs periodicamente.
Detecta:
  - Links quebrados
  - Certificados SSL inválidos
  - Websites redirecionados
  - Leis revogadas
  - Fontes desatualizadas (> 90 dias)

Uso:
    python scripts/agent_legal_source_auditor.py
    python scripts/agent_legal_source_auditor.py --create-issue  # Cria issue se achar problemas

Ambiente (GitHub Actions):
    GITHUB_TOKEN    — para criar/comentar issues
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Configurar encoding UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_JSON = PROJECT_ROOT / "data" / "direitos.json"


def run_validation() -> dict:
    """Executa validate_sources.py e captura output."""
    print("🔗 Executando validação de fontes...")
    
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "validate_sources.py"), "--json"],
        capture_output=True,
        text=True,
        timeout=600,
    )
    
    if result.returncode != 0:
        print(f"⚠️ Validação retornou: {result.returncode}")
    
    try:
        # validate_sources.py escreve para arquivo ou stdout
        output_file = PROJECT_ROOT / "validation_report.json"
        if output_file.exists():
            with open(output_file, encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as exc:
        # validation_report.json ausente ou corrompido — devolvemos estrutura vazia
        print(f"[legal_source_auditor] Falha ao ler validation_report.json: {exc}", file=sys.stderr)
    
    return {"sources": [], "summary": {"ok": 0, "errors": 0, "warnings": 0}}


def check_outdated_sources() -> list:
    """Detecta fontes não revisadas há > 90 dias."""
    issues = []
    
    try:
        with open(DATA_JSON, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return issues
    
    threshold = datetime.now() - timedelta(days=90)
    
    for categoria in data.get("categorias", []):
        cat_id = categoria.get("id", "unknown")
        
        for beneficio in categoria.get("beneficios", []):
            for fonte in beneficio.get("fontes", []):
                consultado = fonte.get("consultado_em")
                if not consultado:
                    continue
                
                try:
                    last_check = datetime.fromisoformat(consultado.replace("Z", "+00:00"))
                    if last_check < threshold:
                        issues.append({
                            "type": "outdated_source",
                            "categoria": cat_id,
                            "beneficio": beneficio.get("nome", "unknown"),
                            "fonte": fonte.get("url", "unknown"),
                            "last_checked": consultado,
                            "days_old": (datetime.now() - last_check.replace(tzinfo=None)).days,
                        })
                except (ValueError, AttributeError) as exc:
                    # consultado_em em formato inválido — ignoramos esta fonte
                    print(
                        f"[legal_source_auditor] Data inválida em consultado_em: "
                        f"categoria={cat_id}, beneficio={beneficio.get('nome', 'unknown')}, "
                        f"consultado_em={consultado!r} ({exc})",
                        file=sys.stderr,
                    )
    
    return issues


def check_revoked_laws() -> list:
    """Detecta leis que podem ter sido revogadas (simples pattern matching)."""
    issues = []
    
    try:
        with open(DATA_JSON, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return issues
    
    # Este é um check simples; uma análise completa requer integração com Senado API
    # Por agora, apenas lista leis que poderiam ter sido revogadas com base em comentários
    for categoria in data.get("categorias", []):
        for beneficio in categoria.get("beneficios", []):
            base_legal = beneficio.get("base_legal_referencia", "")
            if "revog" in base_legal.lower():
                issues.append({
                    "type": "possibly_revoked",
                    "categoria": categoria.get("id"),
                    "beneficio": beneficio.get("nome"),
                    "base_legal": base_legal,
                })
    
    return issues


def generate_issue_body(errors: list, outdated: list, revoked: list) -> str:
    """Gera body de issue com achados."""
    body = "# 🔗 Auditoria de Fontes Legais\n\n"
    body += f"Data: {datetime.now().isoformat()}\n\n"
    
    if errors:
        body += "## ❌ Erros Detectados\n\n"
        for err in errors[:10]:  # Mostrar só os 10 primeiros
            if isinstance(err, dict):
                body += f"- **{err.get('type', 'unknown')}**: {err.get('message', 'Erro desconhecido')}\n"
        if len(errors) > 10:
            body += f"\n... e mais {len(errors) - 10} erros\n"
    
    if outdated:
        body += "## ⏰ Fontes Desatualizadas (> 90 dias)\n\n"
        for src in outdated[:10]:
            body += f"- **{src.get('beneficio', 'unknown')}**: {src.get('days_old')} dias desde última revisão\n"
        if len(outdated) > 10:
            body += f"\n... e mais {len(outdated) - 10} fontes desatualizadas\n"
    
    if revoked:
        body += "## ⚖️ Leis Possivelmente Revogadas\n\n"
        for law in revoked[:5]:
            body += f"- **{law.get('beneficio')}**: {law.get('base_legal')}\n"
        if len(revoked) > 5:
            body += f"\n... e mais {len(revoked) - 5} leis a revisar\n"
    
    body += "\n---\n"
    body += "**Próximos passos:**\n"
    body += "1. Revisar cada link com `curl -I <url>` ou browser\n"
    body += "2. Atualizar `consultado_em` quando validado\n"
    body += "3. Se link quebrado, procurar alternativa em `planalto.gov.br` ou `senado.leg.br`\n"
    body += "4. Se lei revogada, atualizar `base_legal_referencia` com lei nova\n"
    
    return body


def create_github_issue(title: str, body: str) -> bool:
    """Cria issue no GitHub via API."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("⚠️ GITHUB_TOKEN não definido. Pulando criação de issue.")
        return False
    
    # Extrair owner/repo do GITHUB_REPOSITORY
    repo_full = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo_full:
        print("⚠️ GITHUB_REPOSITORY não definido.")
        return False
    
    owner, repo = repo_full.split("/")
    
    import urllib.request
    import urllib.error
    
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    payload = json.dumps({
        "title": title,
        "body": body,
        "labels": ["agent:legal-source-auditor", "⚖️ legal-sources"],
    }).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(f"✅ Issue criada: #{result.get('number', '?')}")
            return True
    except urllib.error.HTTPError as e:
        print(f"❌ Erro ao criar issue: {e.code} {e.reason}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Agent: Legal Source Auditor")
    parser.add_argument("--create-issue", action="store_true", help="Criar issue se achar problemas")
    args = parser.parse_args()
    
    print("=" * 80)
    print("🔗 LEGAL SOURCE AUDITOR")
    print("=" * 80)
    
    # 1. Validar fontes
    validation = run_validation()
    errors = validation.get("sources", [])
    
    # 2. Detectar fontes desatualizadas
    outdated = check_outdated_sources()
    
    # 3. Detectar leis revogadas
    revoked = check_revoked_laws()
    
    # 4. Relatório
    total_issues = len([e for e in errors if e.get("status") == "error"])
    total_warnings = len([e for e in errors if e.get("status") == "warning"])
    
    print(f"\n📊 RESULTADO:")
    print(f"  Fontes validadas: {len(errors)}")
    print(f"  ❌ Erros: {total_issues}")
    print(f"  ⚠️  Warnings: {total_warnings}")
    print(f"  ⏰ Desatualizadas: {len(outdated)}")
    print(f"  ⚖️  Possivelmente revogadas: {len(revoked)}")
    
    # 5. Criar issue se houver problemas e --create-issue foi passado
    if args.create_issue and (total_issues > 0 or len(outdated) > 0 or len(revoked) > 0):
        print("\n📝 Criando issue...")
        body = generate_issue_body(errors, outdated, revoked)
        create_github_issue("🔗 Auditoria de Fontes Legais", body)
    elif total_issues > 0 or len(outdated) > 0 or len(revoked) > 0:
        print("\n💡 Execute com --create-issue para gerar issue automaticamente")
    
    return 0 if total_issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
