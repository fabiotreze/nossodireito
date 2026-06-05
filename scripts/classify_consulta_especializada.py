#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Classificador determinístico: requer_consulta_especializada.

Lógica versionada (não-IA, sem black-box). A REGRA é a auditoria.
Re-rodável quantas vezes quiser. Idempotente.

Política: marca True quando a obtenção/manutenção do direito frequentemente
DEPENDE de advogado, defensor público ou perito jurídico, OU quando há
risco real do leigo se ferir tentando sozinho (perda de prazo, prescrição,
caracterização criminal incorreta).

Como manter:
  - Adicione/remova entradas em RULES (precedência top-down).
  - Cada regra retorna (matched: bool, sinais: list[str]).
  - Primeira regra que casa fixa o resultado.
  - Categoria sem regra casada → False (default seguro).

Refs: #193 estratégia de auto-classificação.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "direitos.json"


# ---------- Predicados auxiliares ------------------------------------------

def _text_blob(cat: dict) -> str:
    """Concatena todos os campos de texto da categoria, em lowercase."""
    parts: list[str] = [
        cat.get("titulo", ""),
        cat.get("resumo", ""),
        cat.get("valor", ""),
        cat.get("onde", ""),
        " ".join(cat.get("requisitos", [])),
        " ".join(cat.get("passo_a_passo", [])),
        " ".join(cat.get("dicas", [])),
        " ".join(cat.get("tags", [])),
    ]
    for bl in cat.get("base_legal", []):
        parts.append(bl.get("lei", ""))
        parts.append(bl.get("artigo", ""))
    return " ".join(parts).lower()


def _regex_any(blob: str, patterns: list[str]) -> list[str]:
    hits: list[str] = []
    for p in patterns:
        m = re.search(p, blob, re.IGNORECASE)
        if m:
            hits.append(m.group(0)[:60])
    return hits


# ---------- Regras ordenadas por precedência -------------------------------
# Cada regra: (nome, descrição, predicate_fn)
# predicate_fn(cat, blob) -> (matched: bool, sinais: list[str])

def _rule_capacidade_legal(cat: dict, blob: str) -> tuple[bool, list[str]]:
    """Curatela, decisão apoiada, capacidade civil — sempre exige jurídico."""
    if cat["id"] in {"capacidade_legal", "curatela_decisao_apoiada"}:
        return True, ["id_pre_classificado"]
    return False, []


def _rule_crimes(cat: dict, blob: str) -> tuple[bool, list[str]]:
    """Crimes contra PcD — denúncia formal, ação penal, prazos prescricionais."""
    if cat["id"] == "crimes_contra_pcd":
        return True, ["id_pre_classificado"]
    return False, []


def _rule_pensoes_especiais(cat: dict, blob: str) -> tuple[bool, list[str]]:
    """Pensões hereditárias com lei específica — habilitação burocrática complexa."""
    if cat["id"] in {"pensao_zika", "pensao_talidomida", "pensao_hanseniase"}:
        return True, ["id_pre_classificado"]
    return False, []


def _rule_prioridade_judicial(cat: dict, blob: str) -> tuple[bool, list[str]]:
    """Prioridade processual judicial — só faz sentido com advogado/defensor."""
    if cat["id"] == "prioridade_judicial":
        return True, ["id_pre_classificado"]
    return False, []


def _rule_indeferimento_recurso(cat: dict, blob: str) -> tuple[bool, list[str]]:
    """Direitos que historicamente sofrem indeferimento + necessitam recurso."""
    patterns = [
        r"indeferi(do|mento|r)",
        r"contestar.{0,30}indeferimento",
        r"recurso administrativo",
        r"a[çc][ãa]o judicial",
        r"defensoria p[úu]blica",
        r"procurar advogado",
    ]
    hits = _regex_any(blob, patterns)
    # exige >= 2 sinais distintos para evitar falso-positivo de menção isolada
    if len(hits) >= 2:
        return True, hits[:3]
    return False, []


def _rule_pericia_medica_inss(cat: dict, blob: str) -> tuple[bool, list[str]]:
    """Perícia médica INSS controvertida — leigos perdem prazo de revisão."""
    if re.search(r"per[íi]cia m[ée]dica", blob, re.IGNORECASE):
        # combinar com sinal de benefício INSS
        if re.search(r"\b(inss|bpc|aposentadoria|aux[íi]lio|reabilita[çc][ãa]o)\b", blob, re.IGNORECASE):
            return True, ["pericia_medica", "vinculo_inss"]
    return False, []


def _rule_isencao_tributaria(cat: dict, blob: str) -> tuple[bool, list[str]]:
    """Isenções fiscais (IR, IPI, IPVA, ICMS) — perícia + laudo + recurso CARF."""
    if cat["id"] in {"isencao_ir", "isencoes_tributarias"}:
        return True, ["id_pre_classificado_tributario"]
    return False, []


def _rule_aposentadoria_pcd(cat: dict, blob: str) -> tuple[bool, list[str]]:
    """Aposentadoria especial PcD — LC 142/2013 + cálculo previdenciário complexo."""
    if cat["id"] == "aposentadoria_especial_pcd":
        return True, ["id_pre_classificado_previdenciario"]
    return False, []


def _rule_cota_trabalho(cat: dict, blob: str) -> tuple[bool, list[str]]:
    """Cota empresa + reabilitação profissional — contencioso trabalhista comum."""
    if cat["id"] in {"cota_emprego_pcd_empresa", "reabilitacao_profissional_inss"}:
        return True, ["id_pre_classificado_trabalhista"]
    return False, []


def _rule_default_false(cat: dict, blob: str) -> tuple[bool, list[str]]:
    """Default seguro: direitos administrativos diretos (carteiras, tarifas, meia-entrada).

    Esses direitos têm canal de atendimento claro (CRAS, prefeitura, app gov.br)
    e raramente exigem advogado. False explícito documenta a decisão.
    """
    return False, ["default_administrativo"]


RULES: list[tuple[str, str, Callable]] = [
    ("capacidade_legal", "Direitos que afetam capacidade civil exigem jurista", _rule_capacidade_legal),
    ("crimes_pcd", "Ação penal exige denúncia formal/MP", _rule_crimes),
    ("pensoes_especiais", "Pensões hereditárias com lei própria", _rule_pensoes_especiais),
    ("prioridade_judicial", "Pedido processual só faz sentido com advogado/defensor", _rule_prioridade_judicial),
    ("isencao_tributaria", "IR/IPI/IPVA/ICMS + laudo + recurso CARF", _rule_isencao_tributaria),
    ("aposentadoria_pcd", "LC 142/2013 cálculo previdenciário complexo", _rule_aposentadoria_pcd),
    ("cota_trabalho", "Cota/reabilitação INSS sofrem contencioso trabalhista", _rule_cota_trabalho),
    ("pericia_medica_inss", "Perícia INSS controvertida + risco prazo revisão", _rule_pericia_medica_inss),
    ("indeferimento_recurso", "Direito historicamente indeferido + necessita recurso", _rule_indeferimento_recurso),
    ("default_administrativo", "Direito administrativo direto sem litígio típico", _rule_default_false),
]


def classify(cat: dict) -> tuple[bool, str, list[str]]:
    """Retorna (requer, regra_aplicada, sinais)."""
    blob = _text_blob(cat)
    for name, _desc, fn in RULES:
        matched, sinais = fn(cat, blob)
        if matched:
            return True, name, sinais
        if name == "default_administrativo":
            # default sempre casa, mas resultado é False
            return False, name, sinais
    return False, "sem_regra", []


def apply_to_payload(payload: dict, *, dry_run: bool) -> dict:
    counters: dict[str, int] = {"true": 0, "false": 0, "regras": {}}
    detail: list[dict] = []

    for cat in payload.get("categorias", []):
        requer, regra, sinais = classify(cat)
        cat["requer_consulta_especializada"] = requer
        cat["criterio_classificacao"] = {
            "regra": regra,
            "sinais": sinais,
        }
        counters["true" if requer else "false"] += 1
        counters["regras"][regra] = counters["regras"].get(regra, 0) + 1
        detail.append({"id": cat["id"], "requer": requer, "regra": regra, "sinais": sinais})

    if not dry_run:
        DATA.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return {"counters": counters, "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    payload = json.loads(DATA.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)
    total = len(payload.get("categorias", []))

    report = apply_to_payload(payload, dry_run=args.dry_run)
    c = report["counters"]

    print(f"Total categorias:                {total}")
    print(f"requer_consulta_especializada=T: {c['true']}")
    print(f"requer_consulta_especializada=F: {c['false']}")
    print("\nDistribuição por regra:")
    for regra, n in sorted(c["regras"].items(), key=lambda x: -x[1]):
        print(f"  {regra:<32} {n}")

    if args.verbose:
        print("\nDetalhe por categoria:")
        for d in report["detail"]:
            mark = "✅" if d["requer"] else "  "
            print(f"  {mark} {d['id']:<35} regra={d['regra']:<25} sinais={d['sinais']}")

    if args.dry_run:
        print("\n[DRY-RUN] Nenhuma escrita realizada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
