#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent: Content Freshness Monitor
==================================
Monitora a atualização de conteúdo e benefícios.
- Detecta direitos não revistos há > 90 dias
- Valida se leis ainda estão vigentes
- Sugere atualizações baseado em mudanças legislativas
- Integra com discover_benefits.py

Uso:
    python scripts/agent_content_freshness_monitor.py
    python scripts/agent_content_freshness_monitor.py --create-issue
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_JSON = PROJECT_ROOT / "data" / "direitos.json"


def check_outdated_beneficios(days_threshold: int = 90) -> list:
    """Detecta benefícios não revistos há mais de N dias."""
    outdated = []
    
    try:
        with open(DATA_JSON, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return outdated
    
    threshold = datetime.now() - timedelta(days=days_threshold)
    
    for categoria in data.get("categorias", []):
        for beneficio in categoria.get("beneficios", []):
            updated = beneficio.get("atualizado_em")
            if not updated:
                continue
            
            try:
                last_update = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                if last_update < threshold:
                    days_old = (datetime.now() - last_update.replace(tzinfo=None)).days
                    outdated.append({
                        "categoria_id": categoria.get("id"),
                        "categoria_nome": categoria.get("nome"),
                        "beneficio_id": beneficio.get("id"),
                        "beneficio_nome": beneficio.get("nome"),
                        "last_updated": updated,
                        "days_old": days_old,
                        "base_legal": beneficio.get("base_legal_referencia", ""),
                    })
            except (ValueError, AttributeError) as exc:
                # Data malformada em atualizado_em — ignoramos este benefício
                print(
                    f"[content_freshness] Data inválida em benefício "
                    f"{beneficio.get('id')} (cat={categoria.get('id')}): "
                    f"atualizado_em={updated!r} ({exc})",
                    file=sys.stderr,
                )
    
    return sorted(outdated, key=lambda x: x["days_old"], reverse=True)


def run_discover_benefits() -> dict:
    """Executa discover_benefits.py para detectar novos benefícios."""
    print("🔍 Executando descoberta de novos benefícios...")
    
    try:
        # Apenas dispara o script; o resultado é lido do arquivo discovery_report.json
        subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "discover_benefits.py"), "--since", "30", "--json"],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        
        # Tentar ler arquivo gerado
        report_file = PROJECT_ROOT / "data" / "discovery_report.json"
        if report_file.exists():
            with open(report_file, encoding="utf-8") as f:
                return json.load(f)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as exc:
        # discover_benefits.py ausente, timeout ou JSON inválido
        print(f"[content_freshness] discover_benefits falhou: {exc}", file=sys.stderr)
    
    return {"candidates_found": 0, "candidates": []}


def generate_issue_body(outdated: list, new_candidates: list) -> str:
    """Gera body de issue com achados."""
    body = "# 📚 Content Freshness Report\n\n"
    body += f"**Data:** {datetime.now().isoformat()}\n\n"
    
    if outdated:
        body += "## ⏰ Benefícios Desatualizados (> 90 dias)\n\n"
        body += f"Total: **{len(outdated)}** benefícios precisam revisão\n\n"
        
        # Top 10 mais antigos
        for item in outdated[:10]:
            body += f"- **{item['beneficio_nome']}** ({item['categoria_nome']})\n"
            body += f"  - Última atualização: {item['days_old']} dias atrás\n"
            body += f"  - Base legal: {item['base_legal']}\n"
        
        if len(outdated) > 10:
            body += f"\n... e mais {len(outdated) - 10} benefícios\n"
    
    if new_candidates:
        body += f"\n## 🆕 Novos Benefícios Candidatos\n\n"
        body += f"Total: **{len(new_candidates)}** candidatos encontrados\n\n"
        
        for candidate in new_candidates[:5]:
            body += f"- {candidate.get('titulo', 'Unknown')}\n"
            body += f"  - Fonte: {candidate.get('fonte', 'N/A')}\n"
            body += f"  - Prioridade: {candidate.get('prioridade', 'N/A')}\n"
        
        if len(new_candidates) > 5:
            body += f"\n... e mais {len(new_candidates) - 5} candidatos\n"
    
    body += "\n---\n"
    body += "**Próximos passos:**\n"
    body += "1. Revisar cada benefício desatualizado\n"
    body += "2. Verificar se base legal ainda é válida\n"
    body += "3. Atualizar `atualizado_em` com data de hoje\n"
    body += "4. Avaliar novos candidatos e adicionar se apropriado\n"
    
    return body


def create_github_issue(title: str, body: str) -> bool:
    """Cria issue no GitHub."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return False
    
    repo_full = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo_full:
        return False
    
    owner, repo = repo_full.split("/")
    
    import urllib.request
    import urllib.error
    
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    payload = json.dumps({
        "title": title,
        "body": body,
        "labels": ["agent:content-freshness", "📚 content"],
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
        print(f"❌ Erro: {e.code}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Agent: Content Freshness Monitor")
    parser.add_argument("--threshold", type=int, default=90, help="Dias para considerar desatualizado")
    parser.add_argument("--create-issue", action="store_true", help="Criar issue se houver problemas")
    args = parser.parse_args()
    
    print("=" * 80)
    print("📚 CONTENT FRESHNESS MONITOR")
    print("=" * 80)
    
    # 1. Verificar benefícios desatualizados
    print(f"\n⏰ Verificando conteúdo desatualizado (>{args.threshold} dias)...")
    outdated = check_outdated_beneficios(args.threshold)
    print(f"  {len(outdated)} benefícios desatualizados")
    
    # 2. Executar discover_benefits para detectar novos
    discovery = run_discover_benefits()
    new_candidates = discovery.get("candidates", [])
    print(f"  {len(new_candidates)} novos candidatos encontrados")
    
    # 3. Gerar relatório
    if outdated or new_candidates:
        print("\n📝 Gerando issue...")
        body = generate_issue_body(outdated, new_candidates)
        if args.create_issue:
            create_github_issue("📚 Content Freshness Report", body)
        else:
            print("\n💡 Execute com --create-issue para gerar issue")
    else:
        print("\n✅ Tudo atualizado!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
