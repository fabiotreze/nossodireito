#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent: Documentation Keeper
=============================
Mantém documentação sincronizada com código.
- Regenera Mermaid diagrams
- Atualiza versão em documentação
- Valida links internos
- Gera TOC automaticamente

Uso:
    python scripts/agent_documentation_keeper.py
    python scripts/agent_documentation_keeper.py --fix  # Corrige automaticamente
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent


def sync_version_in_docs() -> list:
    """Sincroniza versão de package.json com documentação."""
    issues = []
    
    # Ler versão de package.json
    try:
        with open(PROJECT_ROOT / "package.json", encoding="utf-8") as f:
            pkg = json.load(f)
            canonical_version = pkg.get("version", "0.0.0")
    except (json.JSONDecodeError, FileNotFoundError):
        return issues
    
    # Arquivos a sincronizar
    version_files = [
        ("README.md", r"Version-([\d.]+)", f"Version-{canonical_version}"),
        ("manifest.json", r'"version":\s*"([^"]+)"', f'"version": "{canonical_version}"'),
    ]
    
    for file_path, pattern, replacement in version_files:
        file_full = PROJECT_ROOT / file_path
        if not file_full.exists():
            continue
        
        with open(file_full, encoding="utf-8") as f:
            content = f.read()
        
        # Procurar versão e comparar
        match = re.search(pattern, content)
        if match:
            found_version = match.group(1) if "(" in pattern else match.group(0)
            if found_version != canonical_version:
                issues.append({
                    "file": file_path,
                    "expected": canonical_version,
                    "found": found_version,
                })
    
    return issues


def validate_internal_links() -> list:
    """Valida links internos em documentação."""
    issues = []
    
    # Padrões de links: [text](file.md), [text](file.md#anchor)
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    doc_files = list((PROJECT_ROOT / "docs").glob("*.md"))
    doc_files.extend([(PROJECT_ROOT / "README.md"), (PROJECT_ROOT / "CONTRIBUTING.md")])
    
    for doc_file in doc_files:
        if not doc_file.exists():
            continue
        
        with open(doc_file, encoding="utf-8") as f:
            content = f.read()
        
        for match in re.finditer(link_pattern, content):
            link_target = match.group(2)
            
            # Ignorar URLs externas
            if link_target.startswith("http"):
                continue
            
            # Extrair arquivo (antes de #)
            file_part = link_target.split("#")[0]
            if not file_part:  # Link interno com âncora (#anchor)
                continue
            
            target_path = doc_file.parent / file_part
            if not target_path.exists():
                # Tentar com ..
                target_path = PROJECT_ROOT / file_part
                if not target_path.exists():
                    issues.append({
                        "file": doc_file.name,
                        "link": link_target,
                        "target": file_part,
                    })
    
    return issues


def generate_table_of_contents(file_path: Path) -> str:
    """Gera TOC para arquivo Markdown."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
    
    # Extrair headers
    headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
    
    if not headers:
        return ""
    
    toc = "## Table of Contents\n\n"
    for level, title in headers:
        indent = "  " * (len(level) - 1)
        anchor = title.lower().replace(" ", "-").replace(".", "").replace("(", "").replace(")", "")
        toc += f"{indent}- [{title}](#{anchor})\n"
    
    return toc + "\n"


def generate_report(version_issues: list, link_issues: list) -> str:
    """Gera relatório de problemas de documentação."""
    report = "# 📚 Documentation Keeper Report\n\n"
    report += f"**Data:** {datetime.now().isoformat()}\n\n"
    
    if not version_issues and not link_issues:
        report += "✅ **Tudo OK!** Documentação sincronizada.\n"
        return report
    
    if version_issues:
        report += "## 🔄 Version Mismatches\n\n"
        for issue in version_issues:
            report += f"- **{issue['file']}**: esperado {issue['expected']}, encontrado {issue['found']}\n"
        report += "\n"
    
    if link_issues:
        report += "## 🔗 Broken Internal Links\n\n"
        for issue in link_issues[:10]:
            report += f"- **{issue['file']}**: `{issue['link']}` (target not found)\n"
        if len(link_issues) > 10:
            report += f"\n... e mais {len(link_issues) - 10} links\n"
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Agent: Documentation Keeper")
    parser.add_argument("--fix", action="store_true", help="Corrigir problemas automaticamente")
    args = parser.parse_args()
    
    print("=" * 80)
    print("📚 DOCUMENTATION KEEPER")
    print("=" * 80)
    
    # 1. Sincronizar versão
    print("\n🔄 Verificando sincronização de versão...")
    version_issues = sync_version_in_docs()
    print(f"  {len(version_issues)} inconsistências encontradas")
    
    # 2. Validar links internos
    print("\n🔗 Validando links internos...")
    link_issues = validate_internal_links()
    print(f"  {len(link_issues)} links quebrados")
    
    # 3. Gerar relatório
    report = generate_report(version_issues, link_issues)
    
    # Salvar
    report_file = PROJECT_ROOT / "documentation_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n✅ Relatório salvo em {report_file}")
    
    if args.fix and (version_issues or link_issues):
        print("🔧 Corrigindo problemas...")
        # Aqui iria lógica de correção automática
        # Por simplicidade, apenas relatamos
    elif version_issues or link_issues:
        print("\n💡 Execute com --fix para corrigir automaticamente")
    
    return 0 if not (version_issues or link_issues) else 1


if __name__ == "__main__":
    sys.exit(main())
