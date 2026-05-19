#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALIDATE ALL — Validação Completa e Profunda do NossoDireito
Executa TODAS as 11 verificações do projeto em sequência:

  FASE 1  — Pré-Validações (estrutura de arquivos + sintaxe JSON)
  FASE 2  — Schema (JSON Schema Draft 7)
  FASE 3  — Conteúdo Profundo (30 categorias, matching engine, IPVA, semântica)
  FASE 4  — Master Compliance (21 categorias, 1104.7 pts)
  FASE 5  — Análise 360° (cobertura benefícios implementados vs pesquisados)
  FASE 6  — Fontes Oficiais (URLs gov.br, planalto)
  FASE 7  — URLs gov.br PcD (serviços específicos)
  FASE 8  — Base Legal (compliance, leis vigentes/revogadas)
  FASE 9  — Fontes Legais (acesso HTTP fontes oficiais)
  FASE 10 — Auditoria de Automação (gaps, recomendações)
  FASE 11 — Pytest (unit tests: JSON, campos, base_legal, versão)

Nota: FASEs removidas (scripts deletados — cobertura migrada para tests/):
  - analise_funcionalidades.py → tests/test_comprehensive.py
  - audit_content.py → tests/test_comprehensive_validation.py
  - test_analysis_scripts.py → tests/test_comprehensive.py
  - test_complete_validation.py → tests/test_comprehensive_validation.py
  - test_e2e_automated.py → tests/test_e2e_playwright.py

Uso:
    python scripts/validate_all.py                    # Validação completa (11 fases)
    python scripts/validate_all.py --quick            # Apenas fases críticas (1-4)
    python scripts/validate_all.py --fix              # Auto-corrige problemas
    python scripts/validate_all.py --notify           # Envia notificações
    python scripts/validate_all.py --fix --notify     # Ambos

Configuração (variáveis de ambiente):
    SLACK_WEBHOOK_URL    - URL do webhook Slack para notificações
    EMAIL_RECIPIENT      - Email para receber relatórios
    AUTO_BACKUP=1        - Ativa backup automático antes de validações
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Configurar encoding UTF-8 para saída (Windows compatibility)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class ValidationResult:
    """Resultado de uma validação individual"""

    def __init__(self, name: str, success: bool, message: str = "", details: str = "", is_timeout: bool = False):
        self.name = name
        self.success = success
        self.message = message
        self.details = details
        self.is_timeout = is_timeout
        self.timestamp = datetime.now()


class MasterValidator:
    """
    Orquestrador de todas as validações do projeto
    Executa scripts em ordem de prioridade e consolida resultados
    """

    def __init__(self, auto_fix: bool = False, notify: bool = False, verbose: bool = True):
        self.auto_fix = auto_fix
        self.notify = notify
        self.verbose = verbose
        self.results: List[ValidationResult] = []
        self.root = Path(__file__).parent.parent

    def log(self, message: str):
        """Log condicional baseado em verbose"""
        if self.verbose:
            print(message)

    def run_script(self, name: str, script_path: str, timeout: int = 60,
                   timeout_as_warning: bool = False,
                   extra_args: list[str] | None = None) -> ValidationResult:
        """Executa um script Python e retorna resultado"""
        self.log(f"▶️  {name}...")

        cmd = [sys.executable, str(script_path)]
        if extra_args:
            cmd.extend(extra_args)

        try:
            result = subprocess.run(
                cmd,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )

            success = result.returncode == 0

            if success:
                self.log(f"   ✅ {name}: OK")
                return ValidationResult(name, True, "Validation passed", result.stdout)
            else:
                self.log(f"   ❌ {name}: FAILED")
                error_msg = result.stderr[:500] if result.stderr else "Unknown error"
                self.log(f"      Error: {error_msg}")
                return ValidationResult(name, False, "Validation failed", error_msg)

        except subprocess.TimeoutExpired:
            if timeout_as_warning:
                self.log(f"   ⏱️ {name}: TIMEOUT ({timeout}s) — rede lenta (warning)")
                return ValidationResult(name, True, f"Timeout after {timeout}s (rede)", is_timeout=True)
            else:
                self.log(f"   ⏱️ {name}: TIMEOUT ({timeout}s)")
                return ValidationResult(name, False, f"Timeout after {timeout}s")
        except Exception as e:
            self.log(f"   ❌ {name}: EXCEPTION")
            self.log(f"      {str(e)}")
            return ValidationResult(name, False, f"Exception: {str(e)}")

    def validate_structure(self) -> ValidationResult:
        """Valida estrutura de arquivos e pastas"""
        self.log("▶️  Validando estrutura de arquivos...")

        required_files = [
            'data/direitos.json',
            'data/dicionario_pcd.json',
            'data/matching_engine.json',
            'index.html',
            'manifest.json',
            'sw.js',
            'README.md',
            'LICENSE',
            'CHANGELOG.md'
        ]

        missing = []
        for file_path in required_files:
            if not (self.root / file_path).exists():
                missing.append(file_path)

        if missing:
            return ValidationResult(
                "Estrutura de Arquivos",
                False,
                f"Arquivos faltando: {', '.join(missing)}"
            )

        self.log("   ✅ Estrutura de Arquivos: OK")
        return ValidationResult("Estrutura de Arquivos", True, "Todos os arquivos essenciais presentes")

    def validate_workspace_hygiene(self) -> ValidationResult:
        """Verifica higiene do workspace: temp files, CSS duplicados, scripts soltos, dirs vazios"""
        self.log("▶️  Validando higiene do workspace...")

        issues: list[str] = []

        # 1) Arquivos temporários na raiz
        for f in self.root.iterdir():
            if not f.is_file():
                continue
            name = f.name.lower()
            if name.startswith('_temp_') or name.startswith('temp_'):
                issues.append(f"Temp na raiz: {f.name}")

        # 2) index.backup_* na raiz
        for f in self.root.glob('index.backup_*'):
            if f.is_file():
                issues.append(f"Backup na raiz: {f.name}")

        # 3) Relatórios JSON gerados na raiz (exceto validation_report.json que
        #    é gerado pelo próprio validate_all — master_compliance já cobre)
        for report in ['quality_report.json', 'validation_legal_report.json']:
            if (self.root / report).is_file():
                issues.append(f"Report gerado na raiz: {report}")

        # 4) CSS duplicados
        css_dir = self.root / 'css'
        if css_dir.is_dir():
            for css_file in css_dir.iterdir():
                if css_file.is_file() and css_file.suffix == '.css' \
                   and css_file.name != 'styles.css':
                    issues.append(f"CSS duplicado: css/{css_file.name}")

        # 5) Python de teste solto na raiz
        for f in self.root.iterdir():
            if f.is_file() and f.suffix == '.py' and f.name.startswith('test_'):
                issues.append(
                    f"Python na raiz (mover para scripts/ ou tests/): {f.name}")

        # 6) Diretórios vazios
        for d in ['backups']:
            dp = self.root / d
            if dp.is_dir() and not any(dp.iterdir()):
                issues.append(f"Diretório vazio: {d}/")

        # 7) Arquivos genéricos órfãos (*.bak, *.old, *.swp, *.tmp)
        for pattern in ['*.bak', '*.old', '*.swp', '*.tmp']:
            for f in self.root.rglob(pattern):
                if f.is_file() and '.git' not in str(f):
                    issues.append(f"Órfão: {f.relative_to(self.root)}")

        if issues:
            detail = "; ".join(issues[:5])
            if len(issues) > 5:
                detail += f" (+{len(issues) - 5} mais)"
            return ValidationResult(
                "Higiene do Workspace", False,
                f"{len(issues)} problema(s): {detail}")

        self.log("   ✅ Higiene do Workspace: OK")
        return ValidationResult(
            "Higiene do Workspace", True,
            "Sem arquivos temporários, duplicados ou órfãos")

    def validate_json_files(self) -> ValidationResult:
        """Valida sintaxe de arquivos JSON"""
        self.log("▶️  Validando arquivos JSON...")

        json_files = [
            'data/direitos.json',
            'data/dicionario_pcd.json',
            'data/matching_engine.json',
            'manifest.json'
        ]

        errors = []
        for file_path in json_files:
            try:
                with open(self.root / file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                errors.append(f"{file_path}: {str(e)}")

        if errors:
            return ValidationResult(
                "JSON Syntax",
                False,
                f"Erros de sintaxe: {'; '.join(errors)}"
            )

        self.log("   ✅ JSON Syntax: OK")
        return ValidationResult("JSON Syntax", True, "Todos os JSONs válidos")

    def backup_before_fixes(self):
        """Cria backup antes de executar auto-fixes"""
        if not self.auto_fix:
            return

        self.log("\n💾 Criando backup antes de auto-fixes...")

        backup_dir = self.root / 'backups' / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup de arquivos críticos
        import shutil
        critical_files = [
            'data/direitos.json',
            'data/dicionario_pcd.json',
            'data/matching_engine.json'
        ]

        for file_path in critical_files:
            src = self.root / file_path
            dst = backup_dir / Path(file_path).name
            shutil.copy2(src, dst)

        self.log(f"   ✅ Backup criado em: {backup_dir}")

    def run_pytest(self, name: str, test_path: str, timeout: int = 120) -> ValidationResult:
        """Executa pytest e retorna resultado"""
        self.log(f"▶️  {name}...")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short"],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )

            success = result.returncode == 0

            if success:
                self.log(f"   ✅ {name}: OK")
                return ValidationResult(name, True, "All tests passed", result.stdout[-500:])
            else:
                self.log(f"   ❌ {name}: FAILED")
                error_msg = result.stdout[-500:] if result.stdout else result.stderr[:500]
                self.log(f"      {error_msg}")
                return ValidationResult(name, False, "Some tests failed", error_msg)

        except subprocess.TimeoutExpired:
            self.log(f"   ⏱️ {name}: TIMEOUT ({timeout}s)")
            return ValidationResult(name, False, f"Timeout after {timeout}s")
        except Exception as e:
            self.log(f"   ❌ {name}: EXCEPTION — {str(e)}")
            return ValidationResult(name, False, f"Exception: {str(e)}")

    def _print_summary(self):
        """Imprime consolidação de resultados"""
        print()
        print("=" * 100)
        print("📊 CONSOLIDAÇÃO DE RESULTADOS")
        print("=" * 100)

        passed = sum(1 for r in self.results if r.success)
        total = len(self.results)
        timeouts = [r for r in self.results if r.is_timeout]
        failures = [r for r in self.results if not r.success]
        real_passed = passed - len(timeouts)
        percentage = (passed / total * 100) if total > 0 else 0

        print()
        if timeouts:
            print(f"✅ Passed: {real_passed}/{total} ({percentage:.1f}%) + ⏱️ {len(timeouts)} timeout(s) de rede")
        else:
            print(f"✅ Passed: {passed}/{total} ({percentage:.1f}%)")
        print()

        if passed == total and not timeouts:
            print("🎉 PERFEITO! Todas as 16 fases passaram!")
        elif passed == total and timeouts:
            print("✅ EXCELENTE! Sem falhas reais. Timeouts são de verificação de rede (aceitável offline).")
        elif percentage >= 80:
            print("✅ EXCELENTE! Maioria das validações OK.")
        elif percentage >= 60:
            print("⚠️ BOM, mas há problemas que precisam atenção.")
        else:
            print("❌ CRÍTICO! Múltiplas validações falharam.")

        # Listar falhas reais
        if failures:
            print()
            print("❌ FALHAS DETECTADAS:")
            for r in failures:
                print(f"   • {r.name}: {r.message}")

        # Listar timeouts de rede
        if timeouts:
            print()
            print("⏱️ TIMEOUTS DE REDE (não-bloqueantes):")
            for r in timeouts:
                print(f"   • {r.name}: {r.message}")

        # Listar sucessos
        successes = [r for r in self.results if r.success and not r.is_timeout]
        if successes:
            print()
            print("✅ VALIDAÇÕES OK:")
            for r in successes:
                print(f"   • {r.name}")

        print()
        print("=" * 100)

    def run_all_validations(self, quick: bool = False) -> Tuple[int, int]:
        """
        Executa todas as validações em ordem de prioridade.
        quick=True: apenas fases 1-4 (sem rede, sem testes longos).
        Retorna: (passed, total)
        """
        print("=" * 100)
        print("🔄 VALIDAÇÃO COMPLETA — NOSSODIREITO (16 FASES)")
        print("=" * 100)
        print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Modo: {'AUTO-FIX ✨' if self.auto_fix else 'READ-ONLY 📖'}")
        print(f"📢 Notificações: {'ATIVADAS ✅' if self.notify else 'DESATIVADAS ❌'}")
        print(f"⚡ Quick: {'SIM (fases 1-4)' if quick else 'NÃO (todas as 16 fases)'}")
        print()

        # Backup preventivo se auto-fix ativo
        if self.auto_fix:
            self.backup_before_fixes()
            print()

        # ====================
        # FASE 1: PRÉ-VALIDAÇÕES (Estrutura & Sintaxe)
        # ====================
        print("=" * 100)
        print("📋 FASE 1/11: PRÉ-VALIDAÇÕES (Estrutura & Sintaxe)")
        print("=" * 100)

        self.results.append(self.validate_structure())
        self.results.append(self.validate_json_files())
        self.results.append(self.validate_workspace_hygiene())

        # ====================
        # FASE 2: SCHEMA (JSON Schema Draft 7)
        # ====================
        print()
        print("=" * 100)
        print("📐 FASE 2/11: VALIDAÇÃO DE SCHEMA (JSON Schema Draft 7)")
        print("=" * 100)

        self.results.append(self.run_script(
            "JSON Schema (direitos.json vs schema)",
            self.root / "scripts" / "validate_schema.py",
            timeout=30
        ))

        # ====================
        # FASE 3: CONTEÚDO PROFUNDO (30 categorias, matching, IPVA, semântica)
        # ====================
        print()
        print("=" * 100)
        print("🔬 FASE 3/11: VALIDAÇÃO DE CONTEÚDO PROFUNDO (147 checks)")
        print("=" * 100)

        self.results.append(self.run_script(
            "Conteúdo Profundo (categorias, matching engine, IPVA, semântica)",
            self.root / "scripts" / "validate_content.py",
            timeout=60
        ))

        # ====================
        # FASE 4: MASTER COMPLIANCE (21 categorias, 1104.7 pts)
        # ====================
        print()
        print("=" * 100)
        print("🏆 FASE 4/11: MASTER COMPLIANCE (21 categorias, 1104.7 pts)")
        print("=" * 100)

        self.results.append(self.run_script(
            "Master Compliance (21 cats — HTML, CSS, JS, PWA, ARIA, SEO, órfãs...)",
            self.root / "scripts" / "master_compliance.py",
            timeout=120
        ))

        # No modo quick, parar aqui — master_compliance (fase 4) já inclui
        # validate_analise_360() internamente, então fase 5 seria redundante.
        if quick:
            self._print_summary()
            return sum(1 for r in self.results if r.success), len(self.results)

        # ====================
        # FASE 5: ANÁLISE 360° (Cobertura & Completude)
        # ====================
        # No modo completo, roda analise360.py como script separado
        # para gerar relatório detalhado (é mais verbose que o embutido no master).
        print()
        print("=" * 100)
        print("🌐 FASE 5/11: ANÁLISE 360° (Cobertura de Benefícios)")
        print("=" * 100)

        self.results.append(self.run_script(
            "Análise 360° (benefícios implementados vs pesquisados)",
            self.root / "scripts" / "analise360.py",
            timeout=30
        ))

        # ====================
        # FASE 6: FONTES OFICIAIS (URLs gov.br, planalto)
        # ====================
        print()
        print("=" * 100)
        print("🔗 FASE 6/11: VALIDAÇÃO DE FONTES OFICIAIS (URLs)")
        print("=" * 100)

        if (self.root / "scripts" / "validate_sources.py").exists():
            self.results.append(self.run_script(
                "Fontes Oficiais (gov.br, planalto)",
                self.root / "scripts" / "validate_sources.py",
                timeout=180,
                timeout_as_warning=True
            ))
        else:
            self.log("   ⚠️ validate_sources.py: NÃO ENCONTRADO")

        # ====================
        # FASE 7: URLs GOV.BR PcD (Serviços específicos)
        # ====================
        print()
        print("=" * 100)
        print("🏠️ FASE 7/11: URLS GOV.BR PcD (via validate_url_policy --check-live)")
        print("=" * 100)

        self.results.append(self.run_script(
            "URLs gov.br PcD (validate_url_policy --check-live)",
            self.root / "scripts" / "validate_url_policy.py",
            extra_args=["--check-live"],
            timeout=120
        ))

        # ====================
        # FASE 8: BASE LEGAL (Compliance, leis vigentes)
        # ====================
        print()
        print("=" * 100)
        print("⚖️ FASE 8/11: BASE LEGAL (Compliance, Vigência)")
        print("=" * 100)

        if (self.root / "scripts" / "validate_legal_compliance.py").exists():
            self.results.append(self.run_script(
                "Base Legal (compliance, vigência de leis)",
                self.root / "scripts" / "validate_legal_compliance.py",
                timeout=240,
                timeout_as_warning=True
            ))
        else:
            self.log("   ⚠️ validate_legal_compliance.py: NÃO ENCONTRADO")

        # ====================
        # FASE 9: FONTES LEGAIS (acesso HTTP)
        # ====================
        print()
        print("=" * 100)
        print("📜 FASE 9/11: FONTES LEGAIS (Acesso HTTP)")
        print("=" * 100)

        if (self.root / "scripts" / "validate_legal_sources.py").exists():
            self.results.append(self.run_script(
                "Fontes Legais (acesso HTTP a fontes oficiais)",
                self.root / "scripts" / "validate_legal_sources.py",
                timeout=180
            ))
        else:
            self.log("   ⚠️ validate_legal_sources.py: NÃO ENCONTRADO")

        # ====================
        # FASE 10: AUDITORIA DE AUTOMAÇÃO (Gaps & Recomendações)
        # ====================
        print()
        print("=" * 100)
        print("📈 FASE 10/11: AUDITORIA DE AUTOMAÇÃO (Gaps & Recomendações)")
        print("=" * 100)

        if (self.root / "scripts" / "audit_automation.py").exists():
            self.results.append(self.run_script(
                "Auditoria de Automação (gaps, recomendações)",
                self.root / "scripts" / "audit_automation.py",
                timeout=30
            ))
        else:
            self.log("   ⚠️ audit_automation.py: NÃO ENCONTRADO")

        # ====================
        # FASE 11: PYTEST (Unit Tests)
        # ====================
        print()
        print("=" * 100)
        print("🧪 FASE 11/11: PYTEST (Unit Tests — JSON, campos, base_legal)")
        print("=" * 100)

        self.results.append(self.run_pytest(
            "Pytest (tests/test_master_compliance.py)",
            "tests/"
        ))

        # ====================
        # FASE BÔNUS: AUTO-CORREÇÃO (SE --fix)
        # ====================
        if self.auto_fix:
            print()
            print("=" * 100)
            print("🔧 BÔNUS: AUTO-CORREÇÃO (Complete Benefícios)")
            print("=" * 100)

            if (self.root / "scripts" / "complete_beneficios.py").exists():
                self.results.append(self.run_script(
                    "Complete Benefícios (auto-fix)",
                    self.root / "scripts" / "complete_beneficios.py",
                    timeout=60
                ))

        # ====================
        # CONSOLIDAÇÃO DE RESULTADOS
        # ====================
        self._print_summary()

        return sum(1 for r in self.results if r.success), len(self.results)

    def generate_report(self):
        """Gera relatório JSON consolidado"""
        report_path = self.root / "validation_report.json"

        report = {
            'timestamp': datetime.now().isoformat(),
            'mode': 'auto-fix' if self.auto_fix else 'read-only',
            'summary': {
                'total': len(self.results),
                'passed': sum(1 for r in self.results if r.success),
                'failed': sum(1 for r in self.results if not r.success),
                'percentage': (sum(1 for r in self.results if r.success) / len(self.results) * 100) if self.results else 0
            },
            'results': [
                {
                    'name': r.name,
                    'success': r.success,
                    'is_timeout': r.is_timeout,
                    'message': r.message,
                    'timestamp': r.timestamp.isoformat()
                }
                for r in self.results
            ]
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.log(f"📄 Relatório salvo em: {report_path}")

        return report

    def send_notifications(self, report: Dict):
        """Envia notificações via Slack/Email"""
        if not self.notify:
            return

        failed = [r for r in self.results if not r.success]

        # Notificação Slack
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if webhook_url:
            try:
                import requests

                if failed:
                    message = f"❌ NossoDireito: {len(failed)} validações falharam!"
                    color = "danger"
                else:
                    message = f"✅ NossoDireito: Todas as validações passaram! ({report['summary']['total']}/{report['summary']['total']})"
                    color = "good"

                payload = {
                    "attachments": [{
                        "color": color,
                        "title": "Validação Automática",
                        "text": message,
                        "fields": [
                            {"title": "Passed", "value": str(report['summary']['passed']), "short": True},
                            {"title": "Failed", "value": str(report['summary']['failed']), "short": True},
                            {"title": "Percentage", "value": f"{report['summary']['percentage']:.1f}%", "short": True},
                        ],
                        "footer": "NossoDireito Master Validator",
                        "ts": int(datetime.now().timestamp())
                    }]
                }

                requests.post(webhook_url, json=payload, timeout=10)
                self.log("📢 Notificação Slack enviada!")

            except Exception as e:
                self.log(f"⚠️ Erro ao enviar notificação Slack: {e}")

        # Notificação Email (placeholder)
        email_recipient = os.getenv('EMAIL_RECIPIENT')
        if email_recipient:
            self.log(f"📧 Email notification to {email_recipient} (NOT IMPLEMENTED YET)")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Validação completa do projeto NossoDireito (16 fases)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python scripts/validate_all.py                    # Validação completa (16 fases)
  python scripts/validate_all.py --quick            # Apenas fases críticas (1-4)
  python scripts/validate_all.py --fix              # Validar e corrigir
  python scripts/validate_all.py --notify           # Validar e notificar
  python scripts/validate_all.py --fix --notify     # Tudo junto

FASES:
   1 Estrutura & Sintaxe     9  Base Legal
   2 JSON Schema             10 Fontes Legais (HTTP)
   3 Conteúdo Profundo       11 Auditoria Conteúdo
   4 Master Compliance       12 Auditoria Automação
   5 Análise 360°            13 Pytest
   6 Funcionalidades         14 Análise Scripts
   7 Fontes Oficiais         15 Validação Completa
   8 URLs gov.br PcD         16 E2E Automatizado

Variáveis de ambiente:
  SLACK_WEBHOOK_URL    - URL do webhook Slack
  EMAIL_RECIPIENT      - Email para relatórios
  AUTO_BACKUP=1        - Backup automático
        """
    )

    parser.add_argument('--fix', action='store_true', help='Auto-corrigir problemas quando possível')
    parser.add_argument('--notify', action='store_true', help='Enviar notificações (Slack/Email)')
    parser.add_argument('--quiet', action='store_true', help='Modo silencioso (menos output)')
    parser.add_argument('--quick', action='store_true', help='Apenas fases críticas 1-4 (sem rede)')

    args = parser.parse_args()

    validator = MasterValidator(
        auto_fix=args.fix,
        notify=args.notify,
        verbose=not args.quiet
    )

    # Executar validações
    passed, total = validator.run_all_validations(quick=args.quick)

    # Gerar relatório
    report = validator.generate_report()

    # Enviar notificações
    if args.notify:
        validator.send_notifications(report)

    # Exit code: 0 se tudo OK, 1 se houve falhas
    sys.exit(0 if passed == total else 1)


if __name__ == '__main__':
    main()
