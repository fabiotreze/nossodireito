#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALIDATE SCHEMA — Validação de JSON Schema

Valida data/direitos.json contra schemas/direitos.schema.json.
Também valida que todas as URLs externas em data/direitos.json pertencem à
allowlist de fontes oficiais declarada em data/fontes_oficiais.json (G1).

PRIORIDADE: P1 (alto - prevenir estrutura divergente)
ESFORÇO: 6h (já implementado!)
FREQUÊNCIA: Sempre que modificar dados

USO:
    python scripts/validate_schema.py              # Validação completa
    python scripts/validate_schema.py --verbose    # Modo detalhado
    python scripts/validate_schema.py --skip-allowlist  # Pula G1
"""

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
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
    sys.stdout.reconfigure(encoding='utf-8')
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


# ──────────────────────────────────────────────────────────────────────────
# G1: URL allowlist validator (consome data/fontes_oficiais.json)
# ──────────────────────────────────────────────────────────────────────────

URL_FIELD_HINTS = ("link", "url", "sefaz", "fonte")
# Esquemas que não são fonte (tel:, mailto:, etc) — ignorados pelo validator
_SKIP_SCHEMES = {"mailto", "tel", "sms", "javascript", ""}


def _walk_urls(node, path=""):
    """Generator: produz (json_path, url) para todo valor string que pareça URL externa."""
    if isinstance(node, dict):
        for key, value in node.items():
            sub_path = f"{path}.{key}" if path else key
            if isinstance(value, str) and any(h in key.lower() for h in URL_FIELD_HINTS):
                if value.startswith(("http://", "https://")):
                    yield sub_path, value
            else:
                yield from _walk_urls(value, sub_path)
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            yield from _walk_urls(item, f"{path}[{idx}]")


def _compile_allowlist(allowlist_path: Path):
    """Lê data/fontes_oficiais.json e retorna lista de regex compilados para host."""
    with open(allowlist_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    patterns = []
    for entry in data.get("dominios", []):
        padrao = entry["padrao"].strip().lower()
        if padrao.startswith("*."):
            # qualquer subdomínio (ou o próprio domínio raiz)
            tail = re.escape(padrao[2:])
            patterns.append(re.compile(rf"^([a-z0-9-]+\.)*{tail}$"))
        else:
            patterns.append(re.compile(rf"^{re.escape(padrao)}$"))
    return patterns


def validate_url_allowlist(data_path: Path, allowlist_path: Path, verbose: bool = False) -> bool:
    """G1: valida que todo URL externo em direitos.json casa com a allowlist."""
    print()
    print("=" * 80)
    print("🔒 G1 — Validação de Allowlist de Fontes Oficiais")
    print("=" * 80)
    print()
    if not allowlist_path.exists():
        print(f"❌ ERRO: {allowlist_path} não encontrado")
        return False

    patterns = _compile_allowlist(allowlist_path)
    print(f"📋 Allowlist: {allowlist_path.name} ({len(patterns)} padrões)")

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    violations = []
    seen_urls = set()
    for json_path, url in _walk_urls(data):
        try:
            host = (urlparse(url).hostname or "").lower()
        except ValueError:
            violations.append((json_path, url, "URL inválida"))
            continue
        if not host or urlparse(url).scheme in _SKIP_SCHEMES:
            continue
        seen_urls.add(host)
        if not any(p.match(host) for p in patterns):
            violations.append((json_path, url, host))

    print(f"🌐 URLs externas únicas encontradas: {len(seen_urls)} hosts")

    if not violations:
        print("✅ Todas as URLs estão dentro da allowlist (.gov.br/.jus.br/.def.br/.leg.br/.mp.br/icd.who.int/...)")
        return True

    print()
    print(f"❌ {len(violations)} URL(s) FORA da allowlist:")
    print()
    for jpath, url, host in violations[:50]:
        print(f"   • {jpath}")
        print(f"     URL : {url}")
        print(f"     Host: {host}")
        print()
    if len(violations) > 50 and not verbose:
        print(f"   ... e mais {len(violations) - 50} violação(ões). Use --verbose para ver tudo.")
    elif verbose and len(violations) > 50:
        for jpath, url, host in violations[50:]:
            print(f"   • {jpath}\n     URL : {url}\n     Host: {host}\n")
    print()
    print("💡 Adicione o domínio em data/fontes_oficiais.json (com justificativa) ou troque a URL por fonte oficial.")
    return False


# ──────────────────────────────────────────────────────────────────────────
# G2: Coerência entre `aplicabilidade` e (`cids_relacionados`, `aplicavel_a_todas_deficiencias`)
# ──────────────────────────────────────────────────────────────────────────
#
# Regras determinísticas espelham scripts/classify_aplicabilidade.py:
#   - condicao_medica          : exige cids_relacionados ≥ 1
#   - publico_fechado          : exige cids_relacionados ≥ 1 E aplicavel_a_todas_deficiencias=False
#   - documento_administrativo : exige cids_relacionados=[] E aplicavel_a_todas_deficiencias=True
#   - servico_universal        : exige aplicavel_a_todas_deficiencias=True
#
# Previne regressão silenciosa: edits manuais em data/direitos.json não podem
# invalidar a convenção do enum sem disparar erro de schema.

_APLICAB_RULES = {
    "condicao_medica": {
        "cids_min": 1,
        "todas_must_be": None,  # qualquer valor é aceitável
        "msg_cids": "exige `cids_relacionados` ≥ 1 (direito restrito por CIDs específicos).",
    },
    "publico_fechado": {
        "cids_min": 1,
        "todas_must_be": False,
        "msg_cids": "exige `cids_relacionados` ≥ 1 (CID público da OMS para o grupo legal específico).",
    },
    "documento_administrativo": {
        "cids_max": 0,
        "todas_must_be": True,
        "msg_cids": "exige `cids_relacionados` vazio (é documento, não condição médica).",
    },
    "servico_universal": {
        "todas_must_be": True,
        "msg_cids": None,
    },
}


def validate_aplicabilidade_coherence(data_path: Path, verbose: bool = False) -> bool:
    """G2: valida coerência semântica do enum `aplicabilidade` com cids+flag universal."""
    print()
    print("=" * 80)
    print("🧭 G2 — Coerência `aplicabilidade` × `cids_relacionados` × `aplicavel_a_todas_deficiencias`")
    print("=" * 80)
    print()

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cats = data.get("categorias") or data
    items = list(cats.items()) if isinstance(cats, dict) else [
        (c.get("id") or c.get("slug") or "?", c) for c in cats
    ]

    violations = []
    for slug, cat in items:
        apl = cat.get("aplicabilidade")
        if apl is None:
            violations.append((slug, "aplicabilidade ausente — rode scripts/classify_aplicabilidade.py"))
            continue
        rule = _APLICAB_RULES.get(apl)
        if rule is None:
            violations.append((slug, f"aplicabilidade='{apl}' fora do enum (válidos: {list(_APLICAB_RULES)})"))
            continue

        cids = cat.get("cids_relacionados") or []
        todas = cat.get("aplicavel_a_todas_deficiencias")

        if "cids_min" in rule and len(cids) < rule["cids_min"]:
            violations.append((slug, f"aplicabilidade='{apl}' {rule['msg_cids']} (atual: {len(cids)})"))
        if "cids_max" in rule and len(cids) > rule["cids_max"]:
            violations.append((slug, f"aplicabilidade='{apl}' {rule['msg_cids']} (atual: {len(cids)})"))
        if rule["todas_must_be"] is not None and todas is not rule["todas_must_be"]:
            violations.append((
                slug,
                f"aplicabilidade='{apl}' exige `aplicavel_a_todas_deficiencias`={rule['todas_must_be']} (atual: {todas})",
            ))

    print(f"📊 Categorias inspecionadas: {len(items)}")

    if not violations:
        print("✅ Todas as categorias são coerentes com o enum `aplicabilidade`.")
        return True

    print()
    print(f"❌ {len(violations)} categoria(s) com incoerência:")
    print()
    for slug, msg in violations[:50]:
        print(f"   • {slug}: {msg}")
    if len(violations) > 50 and not verbose:
        print(f"   ... e mais {len(violations) - 50}. Use --verbose para ver tudo.")
    elif verbose and len(violations) > 50:
        for slug, msg in violations[50:]:
            print(f"   • {slug}: {msg}")
    print()
    print("💡 Re-rode `python scripts/classify_aplicabilidade.py` ou ajuste manualmente.")
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
    parser.add_argument(
        "--skip-allowlist",
        action="store_true",
        help="Pula a validação G1 de allowlist de fontes oficiais"
    )
    parser.add_argument(
        "--skip-aplicabilidade",
        action="store_true",
        help="Pula a validação G2 de coerência do enum `aplicabilidade`"
    )

    args = parser.parse_args()

    # Paths
    root = Path(__file__).parent.parent
    data_path = root / "data" / "direitos.json"
    schema_path = root / "schemas" / "direitos.schema.json"
    allowlist_path = root / "data" / "fontes_oficiais.json"

    # Verificar arquivos
    if not data_path.exists():
        print(f"❌ ERRO: {data_path} não encontrado")
        return 1

    if not schema_path.exists():
        print(f"❌ ERRO: {schema_path} não encontrado")
        print("   Crie o schema primeiro!")
        return 1

    # Validar
    schema_ok = validate_json_schema(data_path, schema_path, verbose=args.verbose)

    allowlist_ok = True
    if not args.skip_allowlist:
        allowlist_ok = validate_url_allowlist(data_path, allowlist_path, verbose=args.verbose)

    aplicab_ok = True
    if not args.skip_aplicabilidade:
        aplicab_ok = validate_aplicabilidade_coherence(data_path, verbose=args.verbose)

    return 0 if (schema_ok and allowlist_ok and aplicab_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
