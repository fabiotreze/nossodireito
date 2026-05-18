#!/usr/bin/env python3
"""Verifica frescor das fontes jurídicas em data/direitos.json.

Política:
  - Fontes consultadas >= 90 dias: WARNING (não bloqueia commit)
  - Fontes consultadas >= 180 dias: FAIL (bloqueia se --strict)

Retorna exit code 0 (ok), 1 (warnings), 2 (strict-fail).
"""
import json
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "direitos.json"
WARN_DAYS = 90
FAIL_DAYS = 180


def main():
    strict = "--strict" in sys.argv
    if not DATA.exists():
        print(f"::error::{DATA} não encontrado")
        return 2

    payload = json.loads(DATA.read_text(encoding="utf-8"))
    fontes = payload.get("fontes", [])
    if not fontes:
        print("::warning::Nenhuma fonte registrada em data/direitos.json")
        return 1

    today = date.today()
    warnings = []
    failures = []
    fresh = 0

    for f in fontes:
        nome = f.get("nome", "<sem nome>")
        consultado = f.get("consultado_em")
        if not consultado:
            warnings.append((nome, "sem data 'consultado_em'"))
            continue
        try:
            d = datetime.strptime(consultado, "%Y-%m-%d").date()
        except ValueError:
            warnings.append((nome, f"data inválida: {consultado}"))
            continue
        age = (today - d).days
        if age >= FAIL_DAYS:
            failures.append((nome, age, consultado))
        elif age >= WARN_DAYS:
            warnings.append((nome, f"{age} dias (consultado em {consultado})"))
        else:
            fresh += 1

    print(f"\n📚 Frescor de fontes (referência: hoje = {today.isoformat()})")
    print(f"   ✅ Frescas (< {WARN_DAYS}d): {fresh}/{len(fontes)}")
    print(f"   ⚠️  Para revisar (>= {WARN_DAYS}d): {len(warnings)}")
    print(f"   ❌ Críticas (>= {FAIL_DAYS}d): {len(failures)}")

    if warnings:
        print("\n⚠️  Fontes a revisar:")
        for nome, motivo in warnings[:10]:
            print(f"   • {nome}: {motivo}")
        if len(warnings) > 10:
            print(f"   ... e mais {len(warnings) - 10}")

    if failures:
        print("\n❌ Fontes críticas (>= 180 dias):")
        for nome, age, dt in failures[:10]:
            print(f"   • {nome}: {age} dias (última consulta {dt})")

    if failures and strict:
        return 2
    if warnings or failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
