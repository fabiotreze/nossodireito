#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Classifica cada categoria pelo tipo de direito (`aplicabilidade`).

Política determinística em código versionado. Edita regra → re-roda → schema valida.
Coerente com classify_consulta_especializada.py (issue #193, PR #201).

4 valores possíveis (enum no schema):
    - condicao_medica         : restrito por CIDs (`cids_relacionados` ≥ 1)
    - documento_administrativo: é documento, não condição (cids vazio por design)
    - publico_fechado         : grupo legal específico (talidomida/hanseníase/zika)
    - servico_universal       : atende qualquer PcD do dicionário PcD

Uso:
    python scripts/classify_aplicabilidade.py            # aplica e salva
    python scripts/classify_aplicabilidade.py --dry-run  # mostra mudanças sem salvar
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIREITOS_JSON = ROOT / "data" / "direitos.json"

# --- regras determinísticas (precedência por ordem) ---

DOCUMENTOS_ADMINISTRATIVOS = {
    # Documentos genéricos para qualquer PcD (não restringem por CID).
    # CIPTEA NÃO entra aqui — é documento específico para TEA (CIDs F84.x),
    # então cai naturalmente em `condicao_medica`.
    "certificado_pcd_inss",
    "carteira_identificacao_pcd",
}

PUBLICO_FECHADO_LEGAL = {
    "pensao_talidomida",
    "pensao_hanseniase",
    "pensao_zika",
}


def classify(cat: dict) -> tuple[str, list[str]]:
    """Retorna (aplicabilidade, sinais) para uma categoria. Determinístico."""
    cid = cat["id"]
    sinais: list[str] = []

    # Regra 1 — documentos administrativos (não condições médicas)
    if cid in DOCUMENTOS_ADMINISTRATIVOS:
        sinais.append(f"id={cid} ∈ DOCUMENTOS_ADMINISTRATIVOS")
        return "documento_administrativo", sinais

    # Regra 2 — públicos fechados legais (lei específica + CID público da OMS)
    if cid in PUBLICO_FECHADO_LEGAL:
        sinais.append(f"id={cid} ∈ PUBLICO_FECHADO_LEGAL")
        return "publico_fechado", sinais

    # Regra 3 — restrito por CIDs específicos
    cids = cat.get("cids_relacionados") or []
    if cids:
        sinais.append(f"cids_relacionados=[{len(cids)} CID(s)]")
        return "condicao_medica", sinais

    # Regra 4 — universal explícito (sem CIDs porque atende todos)
    if cat.get("aplicavel_a_todas_deficiencias") is True:
        sinais.append("aplicavel_a_todas_deficiencias=True")
        return "servico_universal", sinais

    # Default — universal (fallback seguro: amplia público em vez de restringir)
    sinais.append("default: sem CIDs e sem flag universal explícita")
    return "servico_universal", sinais


def reorder_keys(cat: dict, aplicab: str) -> "OrderedDict[str, object]":
    """Preserva ordem das chaves e injeta `aplicabilidade` logo após `aplicavel_a_todas_deficiencias`."""
    new = OrderedDict()
    inserted = False
    for k, v in cat.items():
        if k == "aplicabilidade":
            continue  # vai ser re-inserido
        new[k] = v
        if k == "aplicavel_a_todas_deficiencias" and not inserted:
            new["aplicabilidade"] = aplicab
            inserted = True
    if not inserted:
        # categoria não tinha `aplicavel_a_todas_deficiencias` — insere antes de `tags`
        out = OrderedDict()
        for k, v in new.items():
            if k == "tags":
                out["aplicabilidade"] = aplicab
            out[k] = v
        return out
    return new


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Mostra mudanças sem salvar")
    args = parser.parse_args()

    data = json.loads(DIREITOS_JSON.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)

    changed = 0
    by_type: dict[str, int] = {}
    diffs: list[str] = []

    for i, cat in enumerate(data["categorias"]):
        aplicab, sinais = classify(cat)
        by_type[aplicab] = by_type.get(aplicab, 0) + 1

        if cat.get("aplicabilidade") != aplicab:
            diffs.append(f"  {cat['id']:40} {cat.get('aplicabilidade', '∅'):26} → {aplicab:26} ({sinais[0]})")
            changed += 1

        new_cat = reorder_keys(cat, aplicab)
        data["categorias"][i] = new_cat

    print(f"Categorias: {len(data['categorias'])}")
    print(f"Mudanças  : {changed}")
    print("Distribuição:")
    for k, v in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {k:30} {v:3}")
    if diffs:
        print("\nDiffs:")
        for d in diffs:
            print(d)

    if args.dry_run:
        print("\n[dry-run] arquivo não foi salvo.")
        return 0

    DIREITOS_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n✔ salvo: {DIREITOS_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
