#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALIDATE SCHEMA — Validação de JSON Schema

Valida data/direitos.json contra schemas/direitos.schema.json.

PRIORIDADE: P1 (alto - prevenir estrutura divergente)
ESFORÇO: 6h (já implementado!)
FREQUÊNCIA: Sempre que modificar dados

USO:
    python scripts/validate_schema.py              # Validação completa
    python scripts/validate_schema.py --verbose    # Modo detalhado
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import jsonschema
    from jsonschema import Draft7Validator
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


def validate_json_schema(data_path: Path, schema_path: Path, verbose: bool = False) -> bool:
    """
    Valida JSON contra schema

    Args:
        data_path: Path para data/direitos.json
        schema_path: Path para schemas/direitos.schema.json
        verbose: Mostrar erros detalhados

    Returns:
        True se válido, False caso contrário
    """
    print("=" * 80)
    print("✅ VALIDATE SCHEMA — Validação Formal JSON Schema")
    print("=" * 80)
    print()

    if not HAS_JSONSCHEMA:
        print("❌ ERRO: Biblioteca 'jsonschema' não instalada")
        print()
        print("Instale com:")
        print("   pip install jsonschema")
        print()
        return False

    # Carregar dados
    print(f"📄 Carregando dados: {data_path.name}")
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Carregar schema
    print(f"📋 Carregando schema: {schema_path.name}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    print()
    print("🔍 Validando...")
    print()

    # Criar validador
    validator = Draft7Validator(schema)

    # Validar
    errors = list(validator.iter_errors(data))

    if not errors:
        print("=" * 80)
        print("✅ VALIDAÇÃO COMPLETA — 100% CONFORME!")
        print("=" * 80)
        print()
        print(f"✅ {data_path.name} está conforme com {schema_path.name}")
        print()
        print(f"📊 Estatísticas:")
        print(f"   • Categorias: {len(data.get('categorias', []))}")
        print(f"   • Fontes: {len(data.get('fontes', []))}")
        print(f"   • Documentos mestre: {len(data.get('documentos_mestre', []))}")
        print()
        return True

    else:
        print("=" * 80)
        print(f"❌ VALIDAÇÃO FALHOU — {len(errors)} ERRO(S) ENCONTRADO(S)")
        print("=" * 80)
        print()

        # Agrupar erros por tipo
        errors_by_path = {}
        for error in errors:
            path = ".".join(str(p) for p in error.path) or "root"
            if path not in errors_by_path:
                errors_by_path[path] = []
            errors_by_path[path].append(error)

        # Mostrar resumo
        print(f"📊 Resumo: {len(errors_by_path)} campo(s) com problemas")
        print()

        # Mostrar erros
        for i, (path, path_errors) in enumerate(errors_by_path.items(), 1):
            print(f"{i}. Campo: {path}")
            for error in path_errors:
                print(f"   ❌ {error.message}")
                if verbose:
                    print(f"      Validator: {error.validator}")
                    print(f"      Schema path: {'.'.join(str(p) for p in error.schema_path)}")
            print()

        if not verbose:
            print("💡 Use --verbose para ver detalhes completos")
            print()

        return False


def main():
    """CLI principal"""
    parser = argparse.ArgumentParser(
        description="Validate Schema — Validação formal JSON Schema"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Mostrar erros detalhados"
    )

    args = parser.parse_args()

    # Paths
    root = Path(__file__).parent.parent
    data_path = root / "data" / "direitos.json"
    schema_path = root / "schemas" / "direitos.schema.json"

    # Verificar arquivos
    if not data_path.exists():
        print(f"❌ ERRO: {data_path} não encontrado")
        return 1

    if not schema_path.exists():
        print(f"❌ ERRO: {schema_path} não encontrado")
        print("   Crie o schema primeiro!")
        return 1

    # Validar
    success = validate_json_schema(data_path, schema_path, verbose=args.verbose)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
