#!/usr/bin/env python3
"""
add_cids_to_categorias.py — Adiciona campo `cids_relacionados` em cada categoria de direito.

Estratégia:
  - Carrega CIDs do dicionario_pcd.json (15 deficiências × CID-10 + CID-11).
  - Aplica mapeamento por categoria:
      * UNIVERSAIS: recebem todos os CIDs (matching busca por qualquer CID PcD).
      * ESPECÍFICAS: recebem apenas CIDs específicos (CIPTEA→TEA, Zika→Zika,
        FGTS doença grave→Lei 7.713/88 lista, etc.).
  - Idempotente: pode rodar várias vezes sem duplicar.

Uso: python3 scripts/add_cids_to_categorias.py
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIREITOS = ROOT / "data" / "direitos.json"
DICIONARIO = ROOT / "data" / "dicionario_pcd.json"

# Mapeamento curado: categoria_id → 'universal' | lista de def_ids do dicionário
# 'universal' = todos os CIDs do dicionário PcD
MAPEAMENTO = {
    # === UNIVERSAIS (qualquer deficiência elegível) ===
    "bpc":                          "universal",
    "educacao":                     "universal",
    "plano_saude":                  "universal",
    "sus_terapias":                 "universal",
    "transporte":                   "universal",
    "trabalho":                     "universal",
    "fgts":                         "universal",
    "moradia":                      "universal",
    "isencoes_tributarias":         "universal",
    "atendimento_prioritario":      "universal",
    "estacionamento_especial":      "universal",
    "aposentadoria_especial_pcd":   "universal",
    "prioridade_judicial":          "universal",
    "tecnologia_assistiva":         "universal",
    "meia_entrada":                 "universal",
    "prouni_fies_sisu":             "universal",
    "bolsa_familia":                "universal",
    "tarifa_social_energia":        "universal",
    "auxilio_inclusao":             "universal",
    "protecao_social":              "universal",
    "esporte_paralimpico":          "universal",
    "turismo_acessivel":            "universal",
    "acessibilidade_arquitetonica": "universal",
    "capacidade_legal":             "universal",
    "crimes_contra_pcd":            "universal",
    "acessibilidade_digital":       "universal",
    "reabilitacao":                 "universal",
    "politica_nacional_cuidados":   "universal",
    "horario_especial_servidor_pcd":"universal",
    "cota_emprego_pcd_empresa":     "universal",
    "curatela_decisao_apoiada":     "universal",

    # === ESPECÍFICAS (CIDs delimitados) ===
    "ciptea":                       ["tea"],
    "pensao_zika":                  ["sindrome_zika"],
    "caa_comunicacao_alternativa":  ["tea","deficiencia_fala","deficiencia_auditiva","deficiencia_intelectual"],

    # Isenção IR — Lei 7.713/88 art. 6º XIV (doenças graves específicas).
    # Cobrimos com defs que mais se enquadram + CIDs adicionais da lei
    # (neoplasia, cardiopatia, AIDS, esclerose múltipla, hepatopatia etc.).
    # Mantemos universal por ora porque a categoria também trata isenção
    # de IR sobre rendimentos PcD em geral (art. 35 Decreto 9.580/2018).
    "isencao_ir":                   "universal",

    # FGTS doença grave — Lei 7.713/88 lista. Universal por enquanto.
    "saque_fgts_doenca_grave":      "universal",
}

# CIDs adicionais para categorias específicas (não cobertos pelo dicionário PcD)
# Lei 7.713/1988 Art. 6º XIV — doenças graves para isenção IR e saque FGTS
CIDS_LEI_7713 = [
    # Neoplasia maligna
    "C00-C97",
    # Cardiopatia grave
    "I50",
    # Esclerose múltipla
    "G35",
    # AIDS
    "B20-B24",
    # Hepatopatia grave
    "K70-K77",
    # Hanseníase
    "A30",
    # Nefropatia grave
    "N18",
    # Doença de Parkinson
    "G20",
    # Espondilite anquilosante
    "M45",
    # Doença de Paget
    "M88",
    # Alienação mental
    "F00-F09","F20-F29",
    # Alzheimer
    "G30",
    # Tuberculose ativa
    "A15-A19",
    # Cegueira
    "H54",
    # Paralisia irreversível
    "G80-G83",
    # Contaminação por radiação
    "T66",
]


def main():
    dic = json.loads(DICIONARIO.read_text(encoding="utf-8"))
    deficiencias = {d["id"]: d for d in dic.get("deficiencias", [])}

    # CIDs universais = união de todos os CID-10 e CID-11 do dicionário
    universais = set()
    for d in deficiencias.values():
        universais.update(d.get("cid10", []))
        universais.update(d.get("cid11", []))
    universais_sorted = sorted(universais)

    direitos = json.loads(DIREITOS.read_text(encoding="utf-8"))
    cats = direitos["categorias"]

    updated = 0
    skipped_no_map = []
    for cat in cats:
        cid = cat["id"]
        regra = MAPEAMENTO.get(cid)
        if regra is None:
            skipped_no_map.append(cid)
            continue

        if regra == "universal":
            cids = universais_sorted.copy()
        else:
            cids = []
            for def_id in regra:
                d = deficiencias.get(def_id)
                if not d:
                    print(f"  ⚠️  def_id '{def_id}' não existe no dicionário (categoria {cid})")
                    continue
                cids.extend(d.get("cid10", []))
                cids.extend(d.get("cid11", []))
            cids = sorted(set(cids))

        # CIDs extras da Lei 7.713/88 para isenção IR e FGTS doença grave
        if cid in ("isencao_ir", "saque_fgts_doenca_grave"):
            cids.extend(CIDS_LEI_7713)
            cids = sorted(set(cids))

        cat["cids_relacionados"] = cids
        cat.setdefault("aplicavel_a_todas_deficiencias", regra == "universal")
        updated += 1

    DIREITOS.write_text(
        json.dumps(direitos, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"✅ {updated}/{len(cats)} categorias atualizadas com cids_relacionados.")
    print(f"   • CIDs universais: {len(universais_sorted)} ({', '.join(universais_sorted[:6])}...)")
    if skipped_no_map:
        print(f"   ⚠️  Sem mapeamento ({len(skipped_no_map)}): {skipped_no_map}")
    print(f"   ℹ️  Lei 7.713/88: {len(CIDS_LEI_7713)} faixas extras em isencao_ir/saque_fgts_doenca_grave.")


if __name__ == "__main__":
    main()
