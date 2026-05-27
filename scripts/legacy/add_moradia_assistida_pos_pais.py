#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adiciona categoria "moradia_assistida_pcd" (proteção pós-pais) a data/direitos.json
e enriquece o cadastro da AMA com programa residencial.

Idempotente: se já existir, não duplica.

Base legal principal:
- Lei 13.146/2015 (LBI) Art. 31 — direito à moradia digna
- Lei 8.742/1993 (LOAS) Art. 23 — Serviços socioassistenciais
- Resolução CNAS 109/2009 — Tipificação Nacional Serviços Socioassistenciais
  (Serviço de Acolhimento Institucional para Jovens e Adultos com Deficiência
   em Residências Inclusivas)
- Lei 12.435/2011 — SUAS
- Lei 12.764/2012 (Política Nacional TEA) Art. 3º
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "direitos.json"

NEW_CATEGORIA = {
    "id": "moradia_assistida_pcd",
    "titulo": "Moradia Assistida / Residência Inclusiva (proteção pós-pais)",
    "icone": "🏘️",
    "resumo": (
        "Direito a moradia digna com apoio para jovens e adultos com deficiência cujos "
        "responsáveis familiares envelheceram, faleceram ou já não conseguem oferecer "
        "cuidados. A Residência Inclusiva (SUAS) é o serviço público federal de "
        "acolhimento em pequeno grupo (até 10 pessoas), com equipe técnica, custeada "
        "pelo BPC e cofinanciada União/Estado/Município."
    ),
    "base_legal": [
        {
            "lei": "Lei 13.146/2015 (LBI)",
            "artigo": "Art. 31",
            "link": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm"
        },
        {
            "lei": "Lei 8.742/1993 (LOAS)",
            "artigo": "Art. 23",
            "link": "https://www.planalto.gov.br/ccivil_03/leis/l8742.htm"
        },
        {
            "lei": "Lei 12.435/2011 (SUAS)",
            "artigo": "Art. 6º-A",
            "link": "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12435.htm"
        },
        {
            "lei": "Resolução CNAS nº 109/2009",
            "artigo": "Tipificação Nacional — Acolhimento Institucional para PcD",
            "link": "https://www.gov.br/mds/pt-br/acesso-a-informacao/legislacao/cnas/resolucoes"
        },
        {
            "lei": "Lei 12.764/2012 (Política Nacional TEA)",
            "artigo": "Art. 3º, III, d",
            "link": "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2012/lei/l12764.htm"
        }
    ],
    "requisitos": [
        "Pessoa com deficiência (qualquer tipo) jovem ou adulta (a partir de 18 anos), em situação de dependência de cuidados",
        "Vínculos familiares fragilizados, rompidos ou ausentes (responsável envelheceu, faleceu ou não tem mais condição de cuidado)",
        "Avaliação social e técnica pelo CRAS/CREAS confirmando a necessidade de acolhimento",
        "Inscrição no CadÚnico (preferencialmente) e elegibilidade ao BPC quando aplicável",
        "Concordância da pessoa com deficiência (quando possível manifestar vontade) — princípio da autonomia LBI Art. 6º"
    ],
    "documentos": [
        "Documento de identidade da pessoa com deficiência (RG, CPF)",
        "Laudo médico/biopsicossocial detalhando deficiência e necessidades de apoio",
        "CIPCD ou CIPTEA quando aplicável",
        "Comprovante de inscrição no CadÚnico",
        "Documentos do responsável atual (se houver) e justificativa social (relatório CRAS/CREAS)",
        "Carta de encaminhamento da rede SUAS, Defensoria Pública ou Ministério Público"
    ],
    "passo_a_passo": [
        "Procurar o CRAS mais próximo (rede SUAS) e relatar a situação familiar — atendimento gratuito e universal",
        "Solicitar avaliação técnica do PAIF (Proteção e Atendimento Integral à Família) ou PAEFI (CREAS) conforme o caso",
        "Apresentar documentação e participar das entrevistas com a equipe (assistente social + psicólogo)",
        "Aguardar parecer técnico sobre necessidade de acolhimento em Residência Inclusiva (ou outro serviço SUAS)",
        "Se necessário acolhimento e não houver vaga, acionar Defensoria Pública ou Ministério Público para garantir o direito (LBI Art. 31)",
        "Acompanhar o Plano Individual de Atendimento (PIA) construído com a equipe da Residência Inclusiva após acolhimento"
    ],
    "dicas": [
        "Comece o planejamento ANTES da crise — converse com o CRAS enquanto os pais ainda têm condições, para construir vínculo e plano sucessório",
        "Mantenha o BPC ativo: o benefício continua sendo recebido pela pessoa acolhida e custeia parte do serviço",
        "Procure também ONGs especializadas como AMA (SP), Lar Escola São Francisco, APAEs e Instituto Jô Clemente — algumas oferecem programas próprios complementares ao SUAS",
        "Documentação do diagnóstico/laudo deve estar SEMPRE atualizada (≤ 2 anos) para acelerar o processo",
        "Defensoria Pública atua gratuitamente em casos de negativa ou demora — Lei 13.146/2015 Art. 79 garante prioridade processual para PcD"
    ],
    "valor": "Serviço gratuito (SUAS). BPC mantido (R$ 1.518,00 — salário mínimo 2026). Custo coberto por cofinanciamento União/Estado/Município.",
    "onde": "CRAS (porta de entrada) → CREAS (média complexidade) → Residência Inclusiva (alta complexidade SUAS). Em casos de negativa: Defensoria Pública da União ou Estadual.",
    "links": [
        {
            "titulo": "Tipificação Nacional dos Serviços Socioassistenciais (MDS)",
            "url": "https://www.gov.br/mds/pt-br/acesso-a-informacao/legislacao/cnas/resolucoes"
        },
        {
            "titulo": "Localizador de CRAS/CREAS (MDS)",
            "url": "https://www.gov.br/mds/pt-br/acesso-a-informacao/carta-de-servicos/desenvolvimento-social"
        },
        {
            "titulo": "Defensoria Pública da União — Pessoa com Deficiência",
            "url": "https://www.gov.br/defensoria/pt-br/assuntos/pessoa-com-deficiencia"
        },
        {
            "titulo": "Lei Brasileira de Inclusão (LBI) — Planalto",
            "url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm"
        }
    ],
    "tags": [
        "moradia",
        "pos-pais",
        "residencia inclusiva",
        "acolhimento",
        "suas",
        "autonomia"
    ],
    "cids_relacionados": [
        "F70-F79",
        "F84",
        "G80",
        "G71",
        "Q90"
    ],
    "aplicavel_a_todas_deficiencias": True
}

# Enriquecimento da AMA com programa residencial pós-pais
AMA_UPDATES = {
    "descricao": (
        "Pioneira no atendimento ao autismo no Brasil (desde 1983). Oferece terapias, "
        "orientação familiar, advocacia por direitos e — central para famílias preocupadas "
        "com a 'proteção pós-pais' — mantém programas residenciais e de moradia assistida "
        "para jovens e adultos com TEA cujos responsáveis envelheceram ou faleceram."
    ),
    "servicos": [
        "Terapias especializadas para TEA (ABA, fonoaudiologia, TO, psicologia)",
        "Programa de moradia assistida / residencial pós-pais para adultos com TEA",
        "Orientação para famílias sobre planejamento sucessório e curatela compartilhada",
        "Advocacy por direitos junto a legisladores e órgãos públicos",
        "Capacitação profissional e inclusão produtiva"
    ],
    "categorias": [
        "ciptea",
        "educacao",
        "plano_saude",
        "sus_terapias",
        "moradia_assistida_pcd"
    ]
}

NEW_KEYWORDS = {
    k: {"cats": ["moradia_assistida_pcd"], "weight": 5}
    for k in [
        "moradia assistida",
        "moradia assistida pcd",
        "residencia inclusiva",
        "residência inclusiva",
        "pos pais",
        "pos-pais",
        "pós-pais",
        "apos os pais",
        "depois dos pais",
        "protecao apos os pais",
        "acolhimento institucional",
        "suas pcd",
        "ama lar",
        "lar escola",
        "cras pcd moradia",
        "tipificacao 109",
        "resolucao cnas 109",
        "lbi art 31",
    ]
}


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))

    # 1. Adiciona categoria (idempotente)
    cats = data.setdefault("categorias", [])
    existing_ids = {c["id"] for c in cats}
    if NEW_CATEGORIA["id"] in existing_ids:
        print(f"⏩ Categoria '{NEW_CATEGORIA['id']}' já existe — pulando")
    else:
        cats.append(NEW_CATEGORIA)
        print(f"✅ Categoria '{NEW_CATEGORIA['id']}' adicionada — total {len(cats)} categorias")

    # 2. Enriquece AMA
    inst = data.get("instituicoes_apoio", [])
    if isinstance(inst, dict):
        inst = inst.get("instituicoes", [])
    ama = next((i for i in inst if i.get("id") == "ama"), None)
    if ama:
        before = ama.get("descricao", "")[:40]
        ama.update(AMA_UPDATES)
        print(f"✅ AMA enriquecida (era: '{before}...')")
    else:
        print("⚠️  AMA não encontrada — pulando enriquecimento")

    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 3. Adiciona keywords ao matching_engine.json
    ME = ROOT / "data" / "matching_engine.json"
    if ME.exists():
        me = json.loads(ME.read_text(encoding="utf-8"))
        kmap = me.setdefault("keyword_map", {})
        added = 0
        for k, v in NEW_KEYWORDS.items():
            if k not in kmap:
                kmap[k] = v
                added += 1
        ME.write_text(json.dumps(me, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"✅ matching_engine.json: {added} keywords novas (total kmap: {len(kmap)})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
