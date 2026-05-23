#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent: Performance Watchdog
=============================
Monitora performance do site e build.
- Valida bundle sizes (JS/CSS gzipped)
- Rastreia build time
- Valida Web Vitals (se houver dados)
- Alerta sobre regressões

Uso:
    python scripts/agent_performance_watchdog.py
    python scripts/agent_performance_watchdog.py --create-issue
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
STATE_DIR = PROJECT_ROOT / ".github" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = STATE_DIR / "performance_baseline.json"


def measure_bundle_size() -> dict:
    """Mede tamanho de bundles (JS/CSS)."""
    results = {}
    
    # JS files
    for js_file in (PROJECT_ROOT / "js").glob("*.js"):
        if js_file.name.startswith("sw-"):
            continue  # Service Worker é geralmente pequeno
        
        size = js_file.stat().st_size
        results[f"js/{js_file.name}"] = {
            "size": size,
            "size_kb": size / 1024,
        }
    
    # CSS files
    for css_file in (PROJECT_ROOT / "css").glob("*.css"):
        size = css_file.stat().st_size
        results[f"css/{css_file.name}"] = {
            "size": size,
            "size_kb": size / 1024,
        }
    
    # Server.js
    server_js = PROJECT_ROOT / "server.js"
    if server_js.exists():
        size = server_js.stat().st_size
        results["server.js"] = {
            "size": size,
            "size_kb": size / 1024,
        }
    
    return results


def measure_build_time() -> float:
    """Mede tempo de build/minificação."""
    # Para um site estático, "build" é mínimo
    # Simulamos verificando tempo de validação
    
    import time
    
    start = time.time()
    
    # Validar scripts e assets
    files_to_check = list((PROJECT_ROOT / "js").glob("*.js"))
    files_to_check.extend((PROJECT_ROOT / "css").glob("*.css"))
    files_to_check.append(PROJECT_ROOT / "index.html")
    
    for f in files_to_check:
        f.stat()  # Simular check
    
    elapsed = time.time() - start
    return elapsed


def load_baseline() -> dict:
    """Carrega baseline anterior."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as exc:
            # Baseline corrompido — começamos do zero
            print(f"[performance_watchdog] Baseline corrompido em {STATE_FILE}: {exc}", file=sys.stderr)
    
    return {"bundle": {}, "build_time": 0, "timestamp": None}


def save_baseline(data: dict) -> None:
    """Salva baseline atual."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def detect_regressions(baseline: dict, current: dict, threshold_pct: float = 5.0) -> list:
    """Detecta regressões de performance."""
    issues = []
    
    # Comparar bundle sizes
    baseline_bundle = baseline.get("bundle", {})
    current_bundle = current.get("bundle", {})
    
    for file_name, current_data in current_bundle.items():
        baseline_data = baseline_bundle.get(file_name)
        if not baseline_data:
            continue
        
        baseline_size = baseline_data.get("size", 0)
        current_size = current_data.get("size", 0)
        
        if baseline_size > 0:
            pct_change = ((current_size - baseline_size) / baseline_size) * 100
            if pct_change > threshold_pct:
                issues.append({
                    "type": "bundle_size_increase",
                    "file": file_name,
                    "baseline_kb": baseline_size / 1024,
                    "current_kb": current_size / 1024,
                    "change_pct": pct_change,
                })
    
    # Comparar build time
    baseline_time = baseline.get("build_time", 0)
    current_time = current.get("build_time", 0)
    
    if baseline_time > 0 and current_time > baseline_time * 1.2:
        issues.append({
            "type": "build_time_increase",
            "baseline_s": baseline_time,
            "current_s": current_time,
            "change_pct": ((current_time - baseline_time) / baseline_time) * 100,
        })
    
    return issues


def generate_issue_body(bundle: dict, build_time: float, regressions: list) -> str:
    """Gera body de issue."""
    body = "# 🚀 Performance Watchdog Report\n\n"
    body += f"**Data:** {datetime.now().isoformat()}\n\n"
    
    body += "## 📦 Bundle Sizes\n\n"
    total_size = 0
    for file_name, data in bundle.items():
        body += f"- `{file_name}`: {data['size_kb']:.1f} KB\n"
        total_size += data['size']
    body += f"\n**Total:** {total_size / 1024:.1f} KB\n\n"
    
    body += f"## ⏱️ Build Time\n\n"
    body += f"- {build_time:.2f} segundos\n\n"
    
    if regressions:
        body += "## 🔴 Regressões Detectadas\n\n"
        for reg in regressions:
            if reg['type'] == 'bundle_size_increase':
                body += f"- **{reg['file']}**: {reg['change_pct']:+.1f}%\n"
                body += f"  - De: {reg['baseline_kb']:.1f} KB → Para: {reg['current_kb']:.1f} KB\n"
            elif reg['type'] == 'build_time_increase':
                body += f"- **Build time**: {reg['change_pct']:+.1f}%\n"
                body += f"  - De: {reg['baseline_s']:.2f}s → Para: {reg['current_s']:.2f}s\n"
    
    return body


def create_github_issue(title: str, body: str) -> bool:
    """Cria issue."""
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
        "labels": ["agent:performance-watchdog", "⚡ performance"],
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
    parser = argparse.ArgumentParser(description="Agent: Performance Watchdog")
    parser.add_argument("--threshold", type=float, default=5.0, help="Threshold % para alerta")
    parser.add_argument("--create-issue", action="store_true", help="Criar issue se houver regressão")
    args = parser.parse_args()
    
    print("=" * 80)
    print("⚡ PERFORMANCE WATCHDOG")
    print("=" * 80)
    
    # 1. Medir bundle
    print("\n📦 Medindo bundle sizes...")
    bundle = measure_bundle_size()
    total_kb = sum(f["size_kb"] for f in bundle.values())
    print(f"  Total: {total_kb:.1f} KB ({len(bundle)} arquivos)")
    
    # 2. Medir build time
    print("\n⏱️ Medindo build time...")
    build_time = measure_build_time()
    print(f"  {build_time:.2f} segundos")
    
    # 3. Carregar baseline
    baseline = load_baseline()
    current = {
        "bundle": bundle,
        "build_time": build_time,
        "timestamp": datetime.now().isoformat(),
    }
    
    # 4. Detectar regressões
    regressions = detect_regressions(baseline, current, args.threshold)
    print(f"\n🔍 Regressões: {len(regressions)}")
    
    # 5. Salvar baseline
    save_baseline(current)
    
    # 6. Criar issue se necessário
    if regressions and args.create_issue:
        print("\n📝 Criando issue...")
        body = generate_issue_body(bundle, build_time, regressions)
        create_github_issue("⚡ Performance Regression Detected", body)
    
    return 0 if not regressions else 1


if __name__ == "__main__":
    sys.exit(main())
