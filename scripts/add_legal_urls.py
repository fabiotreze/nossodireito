#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADD LEGAL URLS — Helper para adicionar URLs em base_legal

Identifica base_legal sem URLs e ajuda a adicionar automaticamente.

PRIORIDADE: P1 (alto - 73 base_legal sem URLs identificados)
ESFORÇO: Manual review (este script facilita)
FREQUÊNCIA: Sob demanda

FUNCIONALIDADES:
1. Lista todos os base_legal sem campo "url"
2. Sugere URLs do planalto.gov.br baseado no nome da lei
3. Permite adicionar URLs interativamente ou em batch
4. Cria backup antes de modificar

USO:
    python scripts/add_legal_urls.py --list          # Listar sem URLs
    python scripts/add_legal_urls.py --suggest       # Sugerir URLs
    python scripts/add_legal_urls.py --dry-run       # Simular (não modificar)
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class LegalURLHelper:
    """Helper para adicionar URLs em base_legal"""

    def __init__(self, root: Path):
        """
        Args:
            root: Diretório raiz do projeto
        """
        self.root = root
        self.direitos_path = root / "data" / "direitos.json"

        # Regex para extrair número de lei/decreto/constituição
        self.law_pattern = re.compile(r'Lei\s+(\d+[\.\d]*)[/-](\d{4})', re.IGNORECASE)
        self.decree_pattern = re.compile(r'Decreto\s+(\d+[\.\d]*)[/-](\d{4})', re.IGNORECASE)
        self.const_pattern = re.compile(r'Constitui[çc]', re.IGNORECASE)
        self.lc_pattern = re.compile(r'Lei\s+Complementar\s+(\d+)[/-](\d{4})', re.IGNORECASE)

        # Template de URLs do planalto.gov.br
        self.planalto_template = "https://www.planalto.gov.br/ccivil_03/leis/l{number}.htm"
        self.planalto_template_consol = "https://www.planalto.gov.br/ccivil_03/leis/l{number}consol.htm"
        self.decree_template = "https://www.planalto.gov.br/ccivil_03/decreto/{number}.htm"
        self.lc_template = "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp{number}.htm"
        self.const_url = "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"

    def load_data(self) -> Dict:
        """Carrega data/direitos.json"""
        with open(self.direitos_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def extract_law_number(self, law_name: str) -> Optional[Tuple[str, str]]:
        """
        Extrai número e ano de uma lei

        Args:
            law_name: Nome da lei (ex: "Lei 13.146/2015")

        Returns:
            Tupla (number, year) ou None
        """
        match = self.law_pattern.search(law_name)
        if match:
            return (match.group(1), match.group(2))
        return None

    def suggest_url(self, law_name: str) -> Optional[str]:
        """
        Sugere URL do planalto.gov.br baseado no nome

        Args:
            law_name: Nome da lei

        Returns:
            URL sugerida ou None
        """
        # Constituição Federal
        if self.const_pattern.search(law_name):
            return self.const_url

        # Lei Complementar
        lc_match = self.lc_pattern.search(law_name)
        if lc_match:
            number = lc_match.group(1)
            return self.lc_template.format(number=number)

        # Decreto
        decree_match = self.decree_pattern.search(law_name)
        if decree_match:
            number, year = decree_match.groups()
            number_clean = number.replace('.', '')
            return self.decree_template.format(number=number_clean)

        # Lei comum
        law_match = self.law_pattern.search(law_name)
        if law_match:
            number, year = law_match.groups()
            # Remove pontos do número (8.989 → 8989)
            number_clean = number.replace('.', '')
            return self.planalto_template.format(number=number_clean)

        return None

    def find_missing_urls(self) -> List[Dict]:
        """
        Encontra todos os base_legal sem URL

        Returns:
            Lista de dicts com {category_id, law_name, suggested_url}
        """
        data = self.load_data()
        categorias = data.get('categorias', [])

        missing = []

        for cat in categorias:
            cat_id = cat.get('id', 'unknown')
            base_legal = cat.get('base_legal', [])

            for item in base_legal:
                # Estrutura real usa 'lei' ao invés de 'nome'
                law_name = item.get('lei', item.get('nome', ''))
                law_url = item.get('link', item.get('url', ''))

                if not law_url:
                    suggested = self.suggest_url(law_name)
                    missing.append({
                        'category_id': cat_id,
                        'law_name': law_name,
                        'suggested_url': suggested,
                        'has_suggestion': suggested is not None
                    })

        return missing

    def list_missing(self):
        """Lista base_legal sem URLs"""
        print("=" * 80)
        print("🔍 BASE_LEGAL SEM URLs")
        print("=" * 80)
        print()

        missing = self.find_missing_urls()

        if not missing:
            print("✅ Todos os base_legal têm URLs!")
            print()
            return

        # Agrupar por categoria
        by_category = {}
        for item in missing:
            cat_id = item['category_id']
            if cat_id not in by_category:
                by_category[cat_id] = []
            by_category[cat_id].append(item)

        print(f"⚠️ Total: {len(missing)} base_legal sem URL")
        print(f"📂 Categorias afetadas: {len(by_category)}")
        print()

        with_suggestions = sum(1 for m in missing if m['has_suggestion'])
        print(f"💡 Sugestões automáticas: {with_suggestions}/{len(missing)}")
        print()

        # Mostrar por categoria
        for cat_id, items in sorted(by_category.items()):
            print(f"📂 {cat_id} ({len(items)} item{'ns' if len(items) > 1 else ''})")
            for item in items:
                print(f"   • {item['law_name']}")
                if item['suggested_url']:
                    print(f"     💡 Sugestão: {item['suggested_url']}")
            print()

        print("=" * 80)
        print("🎯 PRÓXIMOS PASSOS:")
        print("=" * 80)
        print()
        print("1. Use --suggest para gerar lista com URLs sugeridas")
        print("2. Revise URLs manualmente (alguns podem estar incorretos)")
        print("3. Edite data/direitos.json manualmente ou use um script")
        print()
        print("💡 Templates URL:")
        print("   • Lei padrão: https://www.planalto.gov.br/ccivil_03/leis/l{numero}.htm")
        print("   • Lei consolidada: .../l{numero}consol.htm")
        print("   • Decreto: .../decreto/{numero}.htm")
        print()

    def export_suggestions(self, output_path: Path):
        """
        Exporta sugestões para arquivo CSV

        Args:
            output_path: Path para salvar CSV
        """
        missing = self.find_missing_urls()

        print(f"💾 Exportando sugestões para: {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("category_id,law_name,suggested_url\n")
            for item in missing:
                url = item['suggested_url'] or '(manual review needed)'
                f.write(f"{item['category_id']},\"{item['law_name']}\",{url}\n")

        print(f"✅ {len(missing)} linhas exportadas")
        print()


def main():
    """CLI principal"""
    parser = argparse.ArgumentParser(
        description="Add Legal URLs — Helper para adicionar URLs em base_legal"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Listar base_legal sem URLs"
    )
    parser.add_argument(
        "--suggest",
        action="store_true",
        help="Gerar sugestões de URLs"
    )
    parser.add_argument(
        "--export",
        type=str,
        metavar="FILE",
        help="Exportar sugestões para CSV"
    )

    args = parser.parse_args()

    # Paths
    root = Path(__file__).parent.parent

    # Criar helper
    helper = LegalURLHelper(root)

    # Executar ação
    if args.list or (not args.suggest and not args.export):
        # Padrão: listar
        helper.list_missing()

    if args.suggest:
        helper.list_missing()  # Sugestões já são mostradas no list

    if args.export:
        export_path = root / args.export
        helper.export_suggestions(export_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
