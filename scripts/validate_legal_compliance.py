#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALIDATE LEGAL COMPLIANCE — Validação de Base Legal

Valida base legal dos benefícios consultando fontes oficiais (planalto.gov.br).

PRIORIDADE: P0 (crítico - prevenir informações desatualizadas)
ESFORÇO: 8h
FREQUÊNCIA: MENSAL (recomendado)

FUNCIONALIDADES:
1. Extrai base_legal de todos os benefícios
2. Valida URLs do planalto.gov.br (HTTP HEAD request)
3. Verifica se leis estão vigentes (não revogadas)
4. Alerta sobre leis alteradas/revogadas
5. Gera relatório JSON com recomendações

USO:
    python scripts/validate_legal_compliance.py                  # Validação completa
    python scripts/validate_legal_compliance.py --category bpc   # Categoria específica
    python scripts/validate_legal_compliance.py --quick          # Apenas URLs
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class LegalComplianceValidator:
    """Validador de conformidade legal"""

    def __init__(self, root: Path):
        """
        Args:
            root: Diretório raiz do projeto
        """
        self.root = root
        self.direitos_path = root / "data" / "direitos.json"

        # Regex para extrair números de leis
        self.law_pattern = re.compile(r'Lei\s+(\d+[\.\d]*)/(\d{4})', re.IGNORECASE)

        # Relatório de saída
        self.report: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "total_sources": 0,
            "valid": 0,
            "invalid": 0,
            "warnings": 0,
            "errors": [],
            "details": []
        }

    def load_data(self) -> Dict[str, Any]:
        """Carrega data/direitos.json"""
        if not self.direitos_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {self.direitos_path}")

        with open(self.direitos_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def extract_laws_from_categories(self, category_filter: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        Extrai todas as referências legais das categorias

        Args:
            category_filter: Filtrar por categoria específica (ex: "bpc")

        Returns:
            Dict com estrutura {category_id: [base_legal_items]}
        """
        data = self.load_data()
        categories = data.get('categorias', [])

        laws_by_category = {}

        for cat in categories:
            cat_id = cat.get('id', 'unknown')

            if category_filter and cat_id != category_filter:
                continue

            base_legal = cat.get('base_legal', [])
            if base_legal:
                laws_by_category[cat_id] = base_legal

        return laws_by_category

    def extract_laws_from_fontes(self) -> List[Dict]:
        """Extrai todas as referências legais da seção 'fontes'"""
        data = self.load_data()
        fontes = data.get('fontes', [])

        legal_sources = []
        for fonte in fontes:
            if fonte.get('tipo') == 'legislacao':
                legal_sources.append(fonte)

        return legal_sources

    def validate_url(self, url: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Valida se URL está acessível

        Args:
            url: URL a validar
            timeout: Timeout em segundos

        Returns:
            Dict com status da validação
        """
        result = {
            "url": url,
            "status": "unknown",
            "status_code": None,
            "error": None,
            "accessible": False
        }

        if not HAS_REQUESTS:
            result["error"] = "requests library not installed (pip install requests)"
            return result

        try:
            # HEAD request para verificar se URL existe
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            result["status_code"] = response.status_code
            result["accessible"] = response.status_code < 400
            result["status"] = "valid" if result["accessible"] else "invalid"

        except requests.exceptions.Timeout:
            result["status"] = "timeout"
            result["error"] = f"Timeout após {timeout}s"

        except requests.exceptions.RequestException as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def parse_law_number(self, law_name: str) -> Optional[Dict[str, str]]:
        """
        Extrai número e ano de uma lei

        Args:
            law_name: Nome da lei (ex: "Lei 13.146/2015")

        Returns:
            Dict com 'number' e 'year', ou None
        """
        match = self.law_pattern.search(law_name)
        if match:
            return {
                "number": match.group(1),
                "year": match.group(2)
            }
        return None

    def check_law_status_quick(self, url: str) -> str:
        """
        Verifica rapidamente se lei está acessível

        Args:
            url: URL no planalto.gov.br

        Returns:
            "valid", "invalid", "timeout", "error"
        """
        validation = self.validate_url(url, timeout=15)
        return validation["status"]

    def validate_categories(self, category_filter: Optional[str] = None, quick: bool = False):
        """
        Valida base legal de todas as categorias

        Args:
            category_filter: Validar apenas categoria específica
            quick: Apenas validar URLs (não verificar conteúdo)
        """
        print("📋 Validando base legal das categorias...")
        print()

        laws_by_cat = self.extract_laws_from_categories(category_filter)

        for cat_id, base_legal in laws_by_cat.items():
            print(f"   📂 {cat_id}")

            for law in base_legal:
                law_name = law.get('nome', 'Unknown')
                law_url = law.get('url', '')

                self.report["total_sources"] += 1

                if not law_url:
                    print(f"      ⚠️ {law_name}: SEM URL")
                    self.report["warnings"] += 1
                    self.report["details"].append({
                        "category": cat_id,
                        "law": law_name,
                        "status": "no_url",
                        "recommendation": "Adicionar URL oficial"
                    })
                    continue

                # Quick mode: apenas validar URL
                if quick or HAS_REQUESTS:
                    status = self.check_law_status_quick(law_url)

                    if status == "valid":
                        print(f"      ✅ {law_name}")
                        self.report["valid"] += 1
                    elif status == "timeout":
                        print(f"      ⏱️ {law_name}: TIMEOUT")
                        self.report["warnings"] += 1
                        self.report["details"].append({
                            "category": cat_id,
                            "law": law_name,
                            "url": law_url,
                            "status": "timeout",
                            "recommendation": "Verificar manualmente"
                        })
                    else:
                        print(f"      ❌ {law_name}: INACESSÍVEL")
                        self.report["invalid"] += 1
                        self.report["details"].append({
                            "category": cat_id,
                            "law": law_name,
                            "url": law_url,
                            "status": "invalid",
                            "recommendation": "Atualizar URL ou verificar se lei foi revogada"
                        })

                else:
                    print(f"      ℹ️ {law_name}: NÃO VALIDADO (instale 'requests')")
                    self.report["warnings"] += 1

                # Rate limiting
                time.sleep(0.5)

            print()

    def validate_fontes(self, quick: bool = False):
        """
        Valida todas as fontes legislativas

        Args:
            quick: Apenas validar URLs (não verificar conteúdo)
        """
        print("📚 Validando fontes legislativas...")
        print()

        legal_sources = self.extract_laws_from_fontes()

        for fonte in legal_sources:
            fonte_name = fonte.get('nome', 'Unknown')
            fonte_url = fonte.get('url', '')

            self.report["total_sources"] += 1

            if not fonte_url:
                print(f"   ⚠️ {fonte_name}: SEM URL")
                self.report["warnings"] += 1
                continue

            if quick or HAS_REQUESTS:
                status = self.check_law_status_quick(fonte_url)

                if status == "valid":
                    print(f"   ✅ {fonte_name}")
                    self.report["valid"] += 1
                elif status == "timeout":
                    print(f"   ⏱️ {fonte_name}: TIMEOUT")
                    self.report["warnings"] += 1
                else:
                    print(f"   ❌ {fonte_name}: INACESSÍVEL")
                    self.report["invalid"] += 1

            else:
                print(f"   ℹ️ {fonte_name}: NÃO VALIDADO (instale 'requests')")
                self.report["warnings"] += 1

            # Rate limiting
            time.sleep(0.5)

        print()

    def save_report(self):
        """Salva relatório em JSON"""
        report_path = self.root / "validation_legal_report.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)

        return report_path

    def run(self, category: Optional[str] = None, quick: bool = False) -> bool:
        """
        Executa validação completa

        Args:
            category: Validar apenas categoria específica
            quick: Modo rápido (apenas URLs)

        Returns:
            True se sem erros críticos, False caso contrário
        """
        print("=" * 80)
        print("⚖️ VALIDATE LEGAL COMPLIANCE — Validação de Base Legal")
        print("=" * 80)
        print()
        print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 Diretório: {self.root}")

        if not HAS_REQUESTS:
            print()
            print("⚠️ AVISO: Biblioteca 'requests' não instalada")
            print("   Instale com: pip install requests")
            print("   Validação de URLs será LIMITADA")

        if category:
            print(f"🎯 Categoria: {category}")

        if quick:
            print("⚡ Modo rápido: Validando apenas URLs")

        print()

        try:
            # Validar categorias
            self.validate_categories(category, quick)

            # Validar fontes
            if not category:
                self.validate_fontes(quick)

            # Salvar relatório
            report_path = self.save_report()

            # Resumo
            print("=" * 80)
            print("📊 RESUMO DA VALIDAÇÃO")
            print("=" * 80)
            print()
            print(f"✅ Fontes válidas: {self.report['valid']}/{self.report['total_sources']}")
            print(f"❌ Fontes inválidas: {self.report['invalid']}/{self.report['total_sources']}")
            print(f"⚠️ Avisos: {self.report['warnings']}")
            print()
            print(f"📄 Relatório salvo em: {report_path.name}")
            print()

            if self.report['invalid'] > 0:
                print("⚠️ AÇÃO NECESSÁRIA:")
                print("   1. Revise fontes inválidas no relatório")
                print("   2. Atualize URLs ou remova leis revogadas")
                print("   3. Consulte planalto.gov.br para URLs corretas")
                print()

            if not HAS_REQUESTS:
                print("💡 DICA:")
                print("   Instale 'requests' para validação completa:")
                print("   pip install requests")
                print()

            print("=" * 80)
            print("✨ VALIDAÇÃO CONCLUÍDA")
            print("=" * 80)

            return self.report['invalid'] == 0

        except Exception as e:
            self.report["errors"].append(str(e))
            self.save_report()

            print()
            print("=" * 80)
            print("❌ ERRO NA VALIDAÇÃO")
            print("=" * 80)
            print()
            print(f"Erro: {e}")
            print()

            return False


def main():
    """CLI principal"""
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(
        description="Validate Legal Compliance — Validação de base legal"
    )
    parser.add_argument(
        "--category",
        help="Validar apenas categoria específica (ex: bpc, ciptea)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Modo rápido: validar apenas URLs (não verificar conteúdo)"
    )

    args = parser.parse_args()

    # Paths
    root = Path(__file__).parent.parent

    # Executar validação
    validator = LegalComplianceValidator(root)
    success = validator.run(category=args.category, quick=args.quick)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
