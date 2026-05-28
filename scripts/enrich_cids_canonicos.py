#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preenche CIDs canônicos (públicos, OMS) para categorias do tipo `publico_fechado`.

Fonte: CID-10/CID-11 publicada pela OMS (id.who.int/icd).
Validação contínua: cron content-freshness.yml (#205) valida estes CIDs toda segunda.

Apenas atua quando:
    - categoria está em PUBLICO_FECHADO_CIDS, E
    - `cids_relacionados` está vazio (não sobrescreve curadoria existente)

Uso:
    python scripts/enrich_cids_canonicos.py            # aplica e salva
    python scripts/enrich_cids_canonicos.py --dry-run  # mostra sem salvar
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIREITOS_JSON = ROOT / "data" / "direitos.json"

# Tabela versionada de CIDs canônicos da OMS para públicos legais fechados.
# Todos validados contra id.who.int/icd pelo cron content-freshness.yml.
PUBLICO_FECHADO_CIDS: dict[str, list[str]] = {
    "pensao_talidomida": [
        # Q86.8 — síndromes com malformações congênitas por causas exógenas conhecidas
        # (categoria oficial da CID-10 que cobre embriopatia talidomídica)
        "Q86.8",
    ],
    "pensao_hanseniase": [
        # A30 — hanseníase (todas as formas: tuberculoide, lepromatosa, indeterminada)
        "A30",
    ],
    "pensao_zika": [
        # A92.5 — doença pelo vírus zika
        # P35.4 — doença congênita pelo vírus zika (recém-nascido)
        "A92.5",
        "P35.4",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Mostra mudanças sem salvar")
    args = parser.parse_args()

    data = json.loads(DIREITOS_JSON.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)

    changed = 0
    for cat in data["categorias"]:
        cid = cat["id"]
        if cid not in PUBLICO_FECHADO_CIDS:
            continue
        if cat.get("cids_relacionados"):
            continue  # não sobrescreve curadoria humana
        canonicos = PUBLICO_FECHADO_CIDS[cid]
        cat["cids_relacionados"] = canonicos
        print(f"  {cid:38} → cids_relacionados={canonicos}")
        changed += 1

    print(f"\nCategorias enriquecidas: {changed}")

    if args.dry_run:
        print("[dry-run] arquivo não foi salvo.")
        return 0

    if changed:
        DIREITOS_JSON.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"✔ salvo: {DIREITOS_JSON.relative_to(ROOT)}")
    else:
        print("Nada a fazer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
