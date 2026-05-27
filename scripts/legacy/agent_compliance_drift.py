#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent: Compliance Drift Detector
=================================
Monitora continuamente compliance com LGPD, Azure WAF e segurança.
Executa master_compliance.py periodicamente e alerta se score cair.

Uso:
    python scripts/agent_compliance_drift.py
    python scripts/agent_compliance_drift.py --threshold 5  # Alerta se < 5 pontos de queda
    python scripts/agent_compliance_drift.py --create-issue # Cria issue se drift detectado

Ambiente:
    GITHUB_TOKEN    — para criar/comentar issues
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
STATE_DIR = PROJECT_ROOT / ".github" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = STATE_DIR / "compliance_baseline.json"


def load_baseline() -> dict:
    """Carrega baseline anterior de compliance."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as exc:
            # Baseline corrompido — começamos do zero
            print(f"[compliance_drift] Baseline corrompido em {STATE_FILE}: {exc}", file=sys.stderr)
    
    return {"score": 0, "timestamp": None, "details": {}}


def run_compliance_check() -> dict:
    """Executa master_compliance.py e extrai score."""
    print("🔐 Executando verificação de compliance...")
    
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "master_compliance.py"), "--quick"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    
    output = result.stdout + result.stderr
    
    # Tentar extrair score do output (parse heurístico)
    # master_compliance.py escreve algo como "Score: 1095.5/1100"
    import re
    match = re.search(r'Score[:\s]+(\d+\.?\d*)\s*/', output)
    
    score = 0.0
    if match:
        score = float(match.group(1))
    
    # Tentar ler também do arquivo gerado
    report_file = PROJECT_ROOT / "validation_report.json"
    details = {}
    if report_file.exists():
        try:
            with open(report_file, encoding="utf-8") as f:
                report = json.load(f)
                details = report.get("summary", {})
        except json.JSONDecodeError as exc:
            # validation_report.json corrompido — seguimos com details vazio
            print(f"[compliance_drift] JSON inválido em {report_file}: {exc}", file=sys.stderr)
    
    return {
        "score": score,
        "timestamp": datetime.now().isoformat(),
        "details": details,
        "output": output[-500:],  # Últimos 500 chars
    }


def save_baseline(data: dict) -> None:
    """Salva baseline atual para próxima execução."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def detect_drift(baseline: dict, current: dict, threshold: float = 5.0) -> tuple:
    """Detecta se há drift significativo no score."""
    baseline_score = baseline.get("score", 0)
    current_score = current.get("score", 0)
    
    drift = baseline_score - current_score  # Positivo = queda
    
    is_drift = drift > threshold
    
    return is_drift, drift, baseline_score, current_score


def generate_issue_body(drift: float, baseline_score: float, current_score: float, details: dict) -> str:
    """Gera body de issue de drift."""
    body = "# 🚨 Compliance Drift Detectado\n\n"
    body += f"Data: {datetime.now().isoformat()}\n\n"
    body += f"## 📊 Métricas\n\n"
    body += f"- **Score anterior**: {baseline_score:.1f}\n"
    body += f"- **Score atual**: {current_score:.1f}\n"
    body += f"- **Queda**: {drift:.1f} pontos\n\n"
    
    body += "## ⚠️ Próximos passos\n\n"
    body += "1. Executar: `python scripts/master_compliance.py` para ver detalhes\n"
    body += "2. Revisar mudanças em:\n"
    body += "   - `js/app.js` — Código JavaScript\n"
    body += "   - `server.js` — Servidor Node.js\n"
    body += "   - `index.html` — Meta tags, CSP, HSTS\n"
    body += "   - `data/direitos.json` — Schema/estrutura\n"
    body += "3. Corrigir issues de compliance\n"
    body += "4. Re-executar validação até score >= baseline\n\n"
    
    body += "---\n"
    body += f"**Categorias com possível impacto:** (ver output acima)\n"
    
    return body


def create_github_issue(title: str, body: str) -> bool:
    """Cria issue no GitHub."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("⚠️ GITHUB_TOKEN não definido.")
        return False
    
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
        "labels": ["agent:compliance-drift", "🔐 compliance"],
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
    parser = argparse.ArgumentParser(description="Agent: Compliance Drift Detector")
    parser.add_argument("--threshold", type=float, default=5.0, help="Threshold de queda em pontos")
    parser.add_argument("--create-issue", action="store_true", help="Criar issue se drift detectado")
    args = parser.parse_args()
    
    print("=" * 80)
    print("🔐 COMPLIANCE DRIFT DETECTOR")
    print("=" * 80)
    
    # 1. Carregar baseline anterior
    baseline = load_baseline()
    print(f"\n📈 Baseline anterior: {baseline.get('score', 'N/A')}")
    
    # 2. Executar compliance check
    current = run_compliance_check()
    print(f"📊 Score atual: {current.get('score', 'N/A')}")
    
    # 3. Detectar drift
    is_drift, drift, baseline_score, current_score = detect_drift(baseline, current, args.threshold)
    
    print(f"\n🎯 Análise:")
    print(f"  Drift detectado: {'✅ Não' if not is_drift else '❌ Sim'}")
    print(f"  Mudança de score: {drift:+.1f} pontos")
    
    # 4. Salvar baseline atual
    save_baseline(current)
    print(f"✅ Baseline atualizado")
    
    # 5. Criar issue se houver drift
    if is_drift and args.create_issue:
        print("\n📝 Criando issue...")
        body = generate_issue_body(drift, baseline_score, current_score, current.get("details", {}))
        create_github_issue("🚨 Compliance Drift Detectado", body)
    elif is_drift:
        print("\n💡 Execute com --create-issue para gerar issue automaticamente")
    
    return 0 if not is_drift else 1


if __name__ == "__main__":
    sys.exit(main())
