#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALIDATE LEGAL COMPLIANCE — Validação de Base Legal (schema v1.19+)

Objetivos:
1. Validar conformidade legal sem falsos positivos de "SEM URL" em base_legal.
2. Mapear base_legal das categorias para fontes oficiais em data/fontes.
3. Emitir relatório auditável por camada:
   - federal
   - governamental
   - estadual_municipal
   - internacional

Uso:
    python scripts/validate_legal_compliance.py
    python scripts/validate_legal_compliance.py --category bpc
    python scripts/validate_legal_compliance.py --quick
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

UF_CODES = {
    "ac",
    "al",
    "ap",
    "am",
    "ba",
    "ce",
    "df",
    "es",
    "go",
    "ma",
    "mt",
    "ms",
    "mg",
    "pa",
    "pb",
    "pr",
    "pe",
    "pi",
    "rj",
    "rn",
    "rs",
    "ro",
    "rr",
    "sc",
    "sp",
    "se",
    "to",
}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def extract_law_number(value: str) -> Optional[Tuple[str, str]]:
    if not value:
        return None
    patterns = [
        r"lei\s+(\d+[\d\.]*)/(\d{4})",
        r"lei\s+complementar\s+(\d+[\d\.]*)/(\d{4})",
        r"decreto\s+(\d+[\d\.]*)/(\d{4})",
    ]
    value_norm = normalize_text(value)
    for pat in patterns:
        m = re.search(pat, value_norm, re.IGNORECASE)
        if m:
            return (m.group(1).replace(".", ""), m.group(2))
    return None


def classify_layer(url: str, orgao: str, tipo: str, nome: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    orgao_norm = normalize_text(orgao)
    tipo_norm = normalize_text(tipo)
    nome_norm = normalize_text(nome)

    if host.endswith("who.int") or "oms" in nome_norm:
        return "internacional"

    # Ex.: capital.sp.gov.br, prefeitura.rio.rj.gov.br
    for uf in UF_CODES:
        if host.endswith(f".{uf}.gov.br"):
            return "estadual_municipal"

    if any(token in orgao_norm for token in ["prefeitura", "governo do estado", "detran", "sefaz", "secretaria de estado"]):
        return "estadual_municipal"

    if tipo_norm == "legislacao" and (
        "planalto.gov.br" in host or "presidência da república" in orgao_norm
    ):
        return "federal"

    if host.endswith("gov.br") or host.endswith("leg.br") or host.endswith("jus.br") or host.endswith("mp.br") or host.endswith("def.br"):
        return "governamental"

    return "governamental"


class LegalComplianceValidator:
    def __init__(self, root: Path):
        self.root = root
        self.direitos_path = root / "data" / "direitos.json"
        self.report: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "schema_version": "v1.19+",
            "summary": {
                "total_base_legal_items": 0,
                "mapped_to_official_source": 0,
                "unmapped_base_legal_items": 0,
                "validated_sources": 0,
                "valid": 0,
                "invalid": 0,
                "warnings": 0,
            },
            "layers": {
                "federal": {"total": 0, "valid": 0, "invalid": 0, "warnings": 0},
                "governamental": {"total": 0, "valid": 0, "invalid": 0, "warnings": 0},
                "estadual_municipal": {"total": 0, "valid": 0, "invalid": 0, "warnings": 0},
                "internacional": {"total": 0, "valid": 0, "invalid": 0, "warnings": 0},
            },
            "details": [],
            "unmapped_base_legal": [],
            "errors": [],
        }

    def load_data(self) -> Dict[str, Any]:
        if not self.direitos_path.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {self.direitos_path}")
        with open(self.direitos_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _index_legal_sources(self, fontes: List[Dict[str, Any]]) -> Tuple[Dict[Tuple[str, str], Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        by_number: Dict[Tuple[str, str], Dict[str, Any]] = {}
        by_name: Dict[str, Dict[str, Any]] = {}
        for fonte in fontes:
            if normalize_text(fonte.get("tipo", "")) != "legislacao":
                continue
            nome = fonte.get("nome", "")
            if nome:
                by_name[normalize_text(nome)] = fonte
            law_num = extract_law_number(nome)
            if law_num:
                by_number[law_num] = fonte
        return by_number, by_name

    def _map_base_legal(self, categories: List[Dict[str, Any]], category_filter: Optional[str], by_number: Dict[Tuple[str, str], Dict[str, Any]], by_name: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        mapped: List[Dict[str, Any]] = []
        for cat in categories:
            cat_id = cat.get("id", "unknown")
            if category_filter and cat_id != category_filter:
                continue
            for item in cat.get("base_legal", []):
                self.report["summary"]["total_base_legal_items"] += 1
                lei = item.get("lei", "")
                artigo = item.get("artigo", "")
                source = None

                law_num = extract_law_number(lei)
                if law_num:
                    source = by_number.get(law_num)
                if source is None:
                    source = by_name.get(normalize_text(lei))

                if source:
                    self.report["summary"]["mapped_to_official_source"] += 1
                    mapped.append(
                        {
                            "category": cat_id,
                            "lei": lei,
                            "artigo": artigo,
                            "source": source,
                        }
                    )
                else:
                    self.report["summary"]["unmapped_base_legal_items"] += 1
                    self.report["unmapped_base_legal"].append(
                        {
                            "category": cat_id,
                            "lei": lei,
                            "artigo": artigo,
                            "status": "unmapped",
                            "recommendation": "Associar esta base_legal a uma entrada oficial em data/fontes (tipo=legislacao)",
                        }
                    )
        return mapped

    def _validate_url(self, url: str, timeout: int) -> Tuple[str, Optional[int], Optional[str]]:
        if not HAS_REQUESTS:
            return ("warning", None, "requests não instalado")
        try:
            # GET é mais robusto para portais gov.br que bloqueiam HEAD.
            resp = requests.get(url, timeout=timeout, allow_redirects=True)
            if resp.status_code < 400:
                return ("valid", resp.status_code, None)
            return ("invalid", resp.status_code, f"HTTP {resp.status_code}")
        except requests.exceptions.Timeout:
            return ("warning", None, f"timeout após {timeout}s")
        except requests.exceptions.RequestException as ex:
            return ("warning", None, str(ex))

    def run(self, category: Optional[str], quick: bool) -> bool:
        data = self.load_data()
        categorias = data.get("categorias", [])
        fontes = data.get("fontes", [])

        by_number, by_name = self._index_legal_sources(fontes)
        mapped_items = self._map_base_legal(
            categorias, category, by_number, by_name)

        # Deduplicar fontes a validar por URL para evitar custo/rede desnecessário.
        sources_to_validate: Dict[str, Dict[str, Any]] = {}
        for item in mapped_items:
            src = item["source"]
            url = src.get("url", "")
            if not url:
                continue
            sources_to_validate[url] = src

        timeout = 8 if quick else 15
        print("=" * 80)
        print("⚖️ VALIDATE LEGAL COMPLIANCE — Schema v1.19+")
        print("=" * 80)
        print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 Diretório: {self.root}")
        if category:
            print(f"🎯 Categoria: {category}")
        print(f"⚡ Modo rápido: {'sim' if quick else 'não'}")
        print()

        print("📚 Validando fontes legais mapeadas...")
        for url, src in sorted(sources_to_validate.items()):
            nome = src.get("nome", "Unknown")
            orgao = src.get("orgao", "")
            tipo = src.get("tipo", "")
            layer = classify_layer(url, orgao, tipo, nome)

            self.report["summary"]["validated_sources"] += 1
            self.report["layers"][layer]["total"] += 1

            status, status_code, error = self._validate_url(url, timeout)
            if status == "valid":
                self.report["summary"]["valid"] += 1
                self.report["layers"][layer]["valid"] += 1
                print(f"   ✅ [{layer}] {nome}")
            elif status == "invalid":
                self.report["summary"]["invalid"] += 1
                self.report["layers"][layer]["invalid"] += 1
                print(f"   ❌ [{layer}] {nome}: {error}")
            else:
                self.report["summary"]["warnings"] += 1
                self.report["layers"][layer]["warnings"] += 1
                print(f"   ⚠️ [{layer}] {nome}: {error}")

            self.report["details"].append(
                {
                    "name": nome,
                    "type": tipo,
                    "organization": orgao,
                    "url": url,
                    "layer": layer,
                    "status": status,
                    "status_code": status_code,
                    "error": error,
                }
            )

        report_path = self.root / "validation_legal_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)

        print()
        print("=" * 80)
        print("📊 RESUMO")
        print("=" * 80)
        print(
            f"Base legal mapeada: {self.report['summary']['mapped_to_official_source']}/"
            f"{self.report['summary']['total_base_legal_items']}"
        )
        print(
            f"Fontes validadas: {self.report['summary']['validated_sources']} "
            f"(✅ {self.report['summary']['valid']} | ❌ {self.report['summary']['invalid']} | ⚠️ {self.report['summary']['warnings']})"
        )
        print()
        print("Camadas:")
        for layer in ["federal", "governamental", "estadual_municipal", "internacional"]:
            layer_data = self.report["layers"][layer]
            print(
                f"- {layer}: total={layer_data['total']}, "
                f"valid={layer_data['valid']}, invalid={layer_data['invalid']}, warnings={layer_data['warnings']}"
            )

        if self.report["summary"]["unmapped_base_legal_items"] > 0:
            print()
            print(
                f"⚠️ Itens base_legal sem mapeamento oficial: "
                f"{self.report['summary']['unmapped_base_legal_items']}"
            )
            print(
                "   Ver relatório: validation_legal_report.json (campo unmapped_base_legal)")

        print(f"\n📄 Relatório salvo em: {report_path.name}")
        print("=" * 80)

        # Critério de sucesso: sem links inválidos (warnings de timeout não quebram)
        return self.report["summary"]["invalid"] == 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Legal Compliance — Validação de base legal por camadas"
    )
    parser.add_argument(
        "--category", help="Validar apenas categoria específica (ex: bpc)")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Modo rápido com timeout reduzido",
    )
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    validator = LegalComplianceValidator(root)
    ok = validator.run(category=args.category, quick=args.quick)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
