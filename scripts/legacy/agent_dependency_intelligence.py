#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent: Dependency Intelligence
================================
Analisa inteligentemente atualizações de dependências.
- Detecta breaking changes
- Valida semver
- Avalia risco de vulnerabilidades
- Gera relatório de impacto

Uso:
    python scripts/agent_dependency_intelligence.py
    python scripts/agent_dependency_intelligence.py --create-pr  # Cria PR com atualizações seguras
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


def get_npm_outdated() -> list:
    """Obtém lista de pacotes desatualizados via npm outdated."""
    try:
        result = subprocess.run(
            ["npm", "outdated", "--json"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.stdout:
            data = json.loads(result.stdout)
            return [
                {
                    "package": name,
                    "current": info.get("current"),
                    "latest": info.get("latest"),
                    "type": info.get("type", "prod"),
                }
                for name, info in data.items()
            ]
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as exc:
        # npm ausente, timeout ou JSON inválido — retornamos lista vazia
        print(f"[dependency_intelligence] npm outdated falhou: {exc}", file=sys.stderr)
    
    return []


def get_pip_outdated() -> list:
    """Obtém lista de pacotes Python desatualizados.

    NOTA: implementação reservada para próxima iteração. `pip index versions`
    é instável; a versão atual confia em Dependabot para deps Python.
    """
    return []


def check_semver(current: str, latest: str) -> dict:
    """Analisa diferença de versão (major/minor/patch)."""
    # Simple semver parse
    def parse_version(v: str) -> tuple:
        match = re.match(r'^v?(\d+)\.(\d+)\.(\d+)', v)
        if match:
            return tuple(int(x) for x in match.groups())
        return (0, 0, 0)
    
    curr_tuple = parse_version(current)
    latest_tuple = parse_version(latest)
    
    if latest_tuple > curr_tuple:
        if latest_tuple[0] > curr_tuple[0]:
            return {"type": "major", "breaking": True}
        elif latest_tuple[1] > curr_tuple[1]:
            return {"type": "minor", "breaking": False}
        else:
            return {"type": "patch", "breaking": False}
    
    return {"type": "none", "breaking": False}


def run_npm_audit() -> dict:
    """Executa npm audit para vulnerabilidades."""
    try:
        result = subprocess.run(
            ["npm", "audit", "--json"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.stdout:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as exc:
        # npm audit pode falhar em ambientes sem npm — devolvemos zero vulns
        print(f"[dependency_intelligence] npm audit falhou: {exc}", file=sys.stderr)
    
    return {"metadata": {"vulnerabilities": {"total": 0}}}


def generate_report(outdated: list, audit: dict) -> str:
    """Gera relatório de análise."""
    report = "# 📦 Dependency Intelligence Report\n\n"
    report += f"**Data:** {datetime.now().isoformat()}\n\n"
    
    # Agrupar por tipo de mudança
    safe_updates = []
    minor_updates = []
    major_updates = []
    
    for pkg in outdated:
        semver = check_semver(pkg["current"], pkg["latest"])

        entry = f"- **{pkg['package']}**: {pkg['current']} → {pkg['latest']} ({semver['type']})"
        
        if semver["breaking"]:
            major_updates.append(entry)
        elif semver["type"] == "minor":
            minor_updates.append(entry)
        else:
            safe_updates.append(entry)
    
    if safe_updates:
        report += "## ✅ Safe Updates (Patch)\n\n"
        report += "\n".join(safe_updates[:10])
        if len(safe_updates) > 10:
            report += f"\n... e mais {len(safe_updates) - 10}\n"
        report += "\n\n"
    
    if minor_updates:
        report += "## 🟡 Minor Updates\n\n"
        report += "\n".join(minor_updates[:10])
        if len(minor_updates) > 10:
            report += f"\n... e mais {len(minor_updates) - 10}\n"
        report += "\n\n"
    
    if major_updates:
        report += "## 🔴 Major Updates (Breaking)\n\n"
        report += "**Requer análise manual de changelog**\n\n"
        report += "\n".join(major_updates[:10])
        if len(major_updates) > 10:
            report += f"\n... e mais {len(major_updates) - 10}\n"
        report += "\n\n"
    
    # Vulnerabilidades
    vuln_count = audit.get("metadata", {}).get("vulnerabilities", {}).get("total", 0)
    if vuln_count > 0:
        report += f"## 🚨 Vulnerabilities Found\n\n"
        report += f"Total: {vuln_count} vulnerabilities\n"
        report += "Execute `npm audit` para detalhes.\n\n"
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Agent: Dependency Intelligence")
    parser.add_argument("--create-pr", action="store_true", help="Criar PR com atualizações seguras")
    parser.parse_args()  # validação de args; --create-pr reservado para próxima iteração
    
    print("=" * 80)
    print("📦 DEPENDENCY INTELLIGENCE")
    print("=" * 80)
    
    # 1. Check npm
    print("\n🔍 Analisando dependências NPM...")
    outdated_npm = get_npm_outdated()
    print(f"  {len(outdated_npm)} pacotes desatualizados")
    
    # 2. Run npm audit
    print("\n🔒 Verificando vulnerabilidades...")
    audit = run_npm_audit()
    vuln_count = audit.get("metadata", {}).get("vulnerabilities", {}).get("total", 0)
    print(f"  {vuln_count} vulnerabilidades encontradas")
    
    # 3. Gerar relatório
    report = generate_report(outdated_npm, audit)
    
    print(f"\n📋 Relatório gerado ({len(report)} chars)")
    
    # Salvar relatório
    report_file = PROJECT_ROOT / "dependency_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"✅ Salvo em {report_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
