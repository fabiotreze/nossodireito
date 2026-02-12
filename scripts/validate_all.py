#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALIDATE ALL — Rotina Geral de Revalidação Automática
Executa todas as validações do projeto em sequência
Detecta falhas, bugs, regressões automaticamente

Uso:
    python scripts/validate_all.py                    # Modo read-only
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


class ValidationResult:
    """Resultado de uma validação individual"""

    def __init__(self, name: str, success: bool, message: str = "", details: str = ""):
        self.name = name
        self.success = success
        self.message = message
        self.details = details
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

    def run_script(self, name: str, script_path: str, timeout: int = 60) -> ValidationResult:
        """Executa um script Python e retorna resultado"""
        self.log(f"▶️  {name}...")

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
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
            'data/ipva_pcd_estados.json',
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

    def validate_json_files(self) -> ValidationResult:
        """Valida sintaxe de arquivos JSON"""
        self.log("▶️  Validando arquivos JSON...")

        json_files = [
            'data/direitos.json',
            'data/ipva_pcd_estados.json',
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
            'data/ipva_pcd_estados.json'
        ]

        for file_path in critical_files:
            src = self.root / file_path
            dst = backup_dir / Path(file_path).name
            shutil.copy2(src, dst)

        self.log(f"   ✅ Backup criado em: {backup_dir}")

    def run_all_validations(self) -> Tuple[int, int]:
        """
        Executa todas as validações em ordem de prioridade
        Retorna: (passed, total)
        """
        print("=" * 100)
        print("🔄 VALIDAÇÃO COMPLETA — NOSSODIREITO")
        print("=" * 100)
        print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Modo: {'AUTO-FIX ✨' if self.auto_fix else 'READ-ONLY 📖'}")
        print(f"📢 Notificações: {'ATIVADAS ✅' if self.notify else 'DESATIVADAS ❌'}")
        print()

        # Backup preventivo se auto-fix ativo
        if self.auto_fix:
            self.backup_before_fixes()
            print()

        # ====================
        # FASE 1: PRÉ-VALIDAÇÕES
        # ====================
        print("=" * 100)
        print("📋 FASE 1: PRÉ-VALIDAÇÕES (Estrutura & Sintaxe)")
        print("=" * 100)

        self.results.append(self.validate_structure())
        self.results.append(self.validate_json_files())

        # ====================
        # FASE 2: VALIDAÇÕES PRINCIPAIS
        # ====================
        print()
        print("=" * 100)
        print("🔍 FASE 2: VALIDAÇÕES PRINCIPAIS (Master Compliance)")
        print("=" * 100)

        # Master Compliance (20 categorias, 973.9 pts)
        self.results.append(self.run_script(
            "Master Compliance",
            self.root / "scripts" / "master_compliance.py",
            timeout=120
        ))

        # ====================
        # FASE 3: ANÁLISE DE CONTEÚDO
        # ====================
        print()
        print("=" * 100)
        print("📊 FASE 3: ANÁLISE DE CONTEÚDO (Cobertura & Completude)")
        print("=" * 100)

        # Análise 360° (cobertura, completude, IPVA)
        self.results.append(self.run_script(
            "Análise 360°",
            self.root / "scripts" / "analise360.py",
            timeout=30
        ))

        # ====================
        # FASE 4: VALIDAÇÃO DE FONTES
        # ====================
        print()
        print("=" * 100)
        print("🔗 FASE 4: VALIDAÇÃO DE FONTES (URLs & Conectividade)")
        print("=" * 100)

        # Validate Sources (URLs .gov.br)
        if (self.root / "scripts" / "validate_sources.py").exists():
            self.results.append(self.run_script(
                "Validação de Fontes",
                self.root / "scripts" / "validate_sources.py",
                timeout=60
            ))
        else:
            self.log("   ⚠️ Validação de Fontes: SCRIPT NÃO ENCONTRADO")

        # ====================
        # FASE 5: VALIDAÇÃO LEGAL (SE IMPLEMENTADO)
        # ====================
        print()
        print("=" * 100)
        print("⚖️ FASE 5: VALIDAÇÃO LEGAL (Base Legal)")
        print("=" * 100)

        if (self.root / "scripts" / "validate_legal_compliance.py").exists():
            self.results.append(self.run_script(
                "Validação de Base Legal",
                self.root / "scripts" / "validate_legal_compliance.py",
                timeout=120
            ))
        else:
            self.log("   ⚠️ Validação de Base Legal: NÃO IMPLEMENTADO AINDA")
            self.log("      Recomendação: Implementar validate_legal_compliance.py (P0)")

        # ====================
        # FASE 6: AUTO-CORREÇÃO (SE --fix)
        # ====================
        if self.auto_fix:
            print()
            print("=" * 100)
            print("🔧 FASE 6: AUTO-CORREÇÃO (Complete Benefícios)")
            print("=" * 100)

            if (self.root / "scripts" / "complete_beneficios.py").exists():
                self.results.append(self.run_script(
                    "Complete Benefícios",
                    self.root / "scripts" / "complete_beneficios.py",
                    timeout=60
                ))
            else:
                self.log("   ⚠️ Complete Benefícios: SCRIPT NÃO ENCONTRADO")

        # ====================
        # FASE 7: AUDITORIA DE AUTOMAÇÃO
        # ====================
        print()
        print("=" * 100)
        print("📈 FASE 7: AUDITORIA DE AUTOMAÇÃO (Gaps & Recomendações)")
        print("=" * 100)

        if (self.root / "scripts" / "audit_automation.py").exists():
            self.results.append(self.run_script(
                "Auditoria de Automação",
                self.root / "scripts" / "audit_automation.py",
                timeout=30
            ))
        else:
            self.log("   ⚠️ Auditoria de Automação: SCRIPT NÃO ENCONTRADO")

        # ====================
        # CONSOLIDAÇÃO DE RESULTADOS
        # ====================
        print()
        print("=" * 100)
        print("📊 CONSOLIDAÇÃO DE RESULTADOS")
        print("=" * 100)

        passed = sum(1 for r in self.results if r.success)
        total = len(self.results)
        percentage = (passed / total * 100) if total > 0 else 0

        print()
        print(f"✅ Passed: {passed}/{total} ({percentage:.1f}%)")
        print()

        if passed == total:
            print("🎉 PERFEITO! Todas as validações passaram!")
        elif percentage >= 80:
            print("✅ EXCELENTE! Maioria das validações OK.")
        elif percentage >= 60:
            print("⚠️ BOM, mas há problemas que precisam atenção.")
        else:
            print("❌ CRÍTICO! Múltiplas validações falharam.")

        # Listar falhas
        failures = [r for r in self.results if not r.success]
        if failures:
            print()
            print("❌ FALHAS DETECTADAS:")
            for r in failures:
                print(f"   • {r.name}: {r.message}")

        print()
        print("=" * 100)

        return passed, total

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
        description='Validação completa do projeto NossoDireito',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python scripts/validate_all.py                    # Apenas validar
  python scripts/validate_all.py --fix              # Validar e corrigir
  python scripts/validate_all.py --notify           # Validar e notificar
  python scripts/validate_all.py --fix --notify     # Tudo junto

Variáveis de ambiente:
  SLACK_WEBHOOK_URL    - URL do webhook Slack
  EMAIL_RECIPIENT      - Email para relatórios
  AUTO_BACKUP=1        - Backup automático
        """
    )

    parser.add_argument('--fix', action='store_true', help='Auto-corrigir problemas quando possível')
    parser.add_argument('--notify', action='store_true', help='Enviar notificações (Slack/Email)')
    parser.add_argument('--quiet', action='store_true', help='Modo silencioso (menos output)')

    args = parser.parse_args()

    validator = MasterValidator(
        auto_fix=args.fix,
        notify=args.notify,
        verbose=not args.quiet
    )

    # Executar validações
    passed, total = validator.run_all_validations()

    # Gerar relatório
    report = validator.generate_report()

    # Enviar notificações
    if args.notify:
        validator.send_notifications(report)

    # Exit code: 0 se tudo OK, 1 se houve falhas
    sys.exit(0 if passed == total else 1)


if __name__ == '__main__':
    main()
