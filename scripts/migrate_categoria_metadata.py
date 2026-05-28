#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migração one-shot: adiciona em cada categoria os campos
    - data_ultima_verificacao (placeholder = ultima_atualizacao global)
    - canal_de_atendimento_oficial (alias do campo `onde`)

Refs: #193 item 6 + virada estratégica de governança editorial.

Idempotente: se o campo já existe, NÃO sobrescreve. Roda quantas vezes quiser.

Uso:
    python scripts/migrate_categoria_metadata.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "direitos.json"


def migrate(payload: dict, *, dry_run: bool) -> tuple[int, int]:
    """Retorna (added_data_verif, added_canal)."""
    placeholder = payload["ultima_atualizacao"]
    added_data = 0
    added_canal = 0

    for cat in payload.get("categorias", []):
        # data_ultima_verificacao: placeholder global
        if "data_ultima_verificacao" not in cat:
            cat["data_ultima_verificacao"] = placeholder
            added_data += 1

        # canal_de_atendimento_oficial: alias de `onde` (sem normalização — PR C tratará)
        if "canal_de_atendimento_oficial" not in cat:
            onde = cat.get("onde")
            if onde and isinstance(onde, str) and len(onde.strip()) >= 5:
                cat["canal_de_atendimento_oficial"] = onde.strip()
                added_canal += 1

    if not dry_run:
        # Mantém ordem dos campos existentes; novos vão ao final naturalmente
        DATA.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return added_data, added_canal


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Não escreve o arquivo")
    args = parser.parse_args()

    payload = json.loads(DATA.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)
    total_cats = len(payload.get("categorias", []))

    added_data, added_canal = migrate(payload, dry_run=args.dry_run)

    print(f"Categorias totais:                 {total_cats}")
    print(f"data_ultima_verificacao adicionada: {added_data}")
    print(f"canal_de_atendimento_oficial adic.: {added_canal}")
    print(f"Placeholder usado:                  {payload['ultima_atualizacao']}")
    if args.dry_run:
        print("\n[DRY-RUN] Nenhuma escrita realizada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
