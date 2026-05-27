#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent: Community Insights
===========================
Analisa padrões de issues/discussions para melhorar produto.
- Detecta padrões em issues fechadas
- Sugere FAQs
- Identifica categorias com mais dúvidas
- Alerta sobre issues antigas sem label

Uso:
    python scripts/agent_community_insights.py
    python scripts/agent_community_insights.py --create-pr  # Gera PR com sugestões
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent


def get_recent_issues(days: int = 30) -> list:
    """Obtém issues fechadas dos últimos N dias via GitHub CLI."""
    try:
        result = subprocess.run(
            [
                "gh", "issue", "list",
                "--state", "closed",
                f"--search", f"closed:>={datetime.now() - timedelta(days=days)}..",
                "--json", "title,body,labels",
                "--limit", "100",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.stdout:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as exc:
        # gh CLI ausente, timeout ou JSON inválido — retornamos lista vazia para não bloquear o agent
        print(f"[community_insights] Falha ao obter issues via gh CLI: {exc}", file=sys.stderr)
    
    return []


def analyze_issue_patterns(issues: list) -> dict:
    """Analisa padrões em issues."""
    keywords = Counter()
    categories = Counter()
    
    # Lista de palavras-chave PcD (do projeto)
    pcd_keywords = [
        "deficiência", "pessoa com deficiência", "autismo", "tea",
        "benefício", "direito", "lei", "formulário", "acesso",
        "acessibilidade", "bug", "erro", "não funciona", "dúvida",
        "legislação", "documentação", "interface"
    ]
    
    for issue in issues:
        title = issue.get("title", "").lower()
        body = issue.get("body", "").lower()
        labels = [l.get("name", "") for l in issue.get("labels", [])]
        
        # Extrair palavras-chave
        for kw in pcd_keywords:
            if kw in title or kw in body:
                keywords[kw] += 1
        
        # Contar labels como categorias
        for label in labels:
            categories[label] += 1
    
    return {
        "top_keywords": keywords.most_common(10),
        "top_categories": categories.most_common(10),
    }


def extract_faq_candidates(issues: list) -> list:
    """Extrai possíveis FAQs de issues com padrões similares."""
    candidates = []
    
    # Tópicos recorrentes
    patterns = {
        "formulários": r"formulário|form|preench",
        "acessibilidade": r"acessib|wcag|aria|leitor",
        "navegação": r"naveg|menu|botão|encontr",
        "beneficios": r"benefício|direito|como obter",
        "legislacao": r"lei|decreto|artigo|base legal",
    }
    
    for pattern_name, pattern_re in patterns.items():
        matching_issues = []
        for issue in issues:
            title = issue.get("title", "").lower()
            body = issue.get("body", "")[:200].lower()
            if re.search(pattern_re, title + " " + body):
                matching_issues.append(issue)
        
        if len(matching_issues) >= 2:  # Ao menos 2 issues similares
            candidates.append({
                "topic": pattern_name,
                "count": len(matching_issues),
                "example_title": matching_issues[0].get("title", ""),
            })
    
    return sorted(candidates, key=lambda x: x["count"], reverse=True)


def generate_report(patterns: dict, faq_candidates: list, old_issues: list) -> str:
    """Gera relatório de insights."""
    report = "# 👥 Community Insights Report\n\n"
    report += f"**Data:** {datetime.now().isoformat()}\n\n"
    
    # Top keywords
    report += "## 🔑 Top Keywords em Issues\n\n"
    for kw, count in patterns.get("top_keywords", [])[:5]:
        report += f"- **{kw}**: {count} mentions\n"
    report += "\n"
    
    # Top categories
    report += "## 📂 Top Categories\n\n"
    for cat, count in patterns.get("top_categories", [])[:5]:
        report += f"- **{cat}**: {count} issues\n"
    report += "\n"
    
    # FAQ candidates
    if faq_candidates:
        report += "## ❓ Sugestões de FAQ\n\n"
        for candidate in faq_candidates[:5]:
            report += f"- **{candidate['topic'].title()}**: {candidate['count']} issues similares\n"
            report += f"  > \"*{candidate['example_title']}*\"\n"
        report += "\n"
    
    # Old issues
    if old_issues:
        report += "## ⏰ Issues Antigas Sem Label\n\n"
        for issue in old_issues[:5]:
            created = issue.get("createdAt", "N/A")
            report += f"- **{issue.get('title', 'Unknown')}** (criada em {created})\n"
        if len(old_issues) > 5:
            report += f"\n... e mais {len(old_issues) - 5} issues antigas\n"
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Agent: Community Insights")
    parser.add_argument("--days", type=int, default=30, help="Últimos N dias")
    parser.add_argument("--create-pr", action="store_true", help="Criar PR com FAQ sugestões")
    args = parser.parse_args()
    
    print("=" * 80)
    print("👥 COMMUNITY INSIGHTS")
    print("=" * 80)
    
    # 1. Obter issues recentes
    print(f"\n📊 Analisando issues dos últimos {args.days} dias...")
    issues = get_recent_issues(args.days)
    print(f"  {len(issues)} issues encontradas")
    
    if not issues:
        print("  ℹ️ Nenhuma issue para analisar")
        return 0
    
    # 2. Analisar padrões
    print("\n🔍 Analisando padrões...")
    patterns = analyze_issue_patterns(issues)
    
    # 3. Extrair FAQ candidates
    print("\n❓ Extraindo FAQ candidates...")
    faq_candidates = extract_faq_candidates(issues)
    print(f"  {len(faq_candidates)} tópicos recorrentes")
    
    # 4. Gerar relatório
    report = generate_report(patterns, faq_candidates, [])
    
    # Salvar
    report_file = PROJECT_ROOT / "community_insights_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n✅ Relatório salvo em {report_file}")
    
    if args.create_pr and faq_candidates:
        print("📝 Sugestão: Criar PR com FAQ baseado em padrões recorrentes")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
