#!/usr/bin/env python3
"""
S3 (v1.28.0) — Adiciona 5 serviços federais faltantes a data/direitos.json.

Idempotente: se a categoria já existe (por id), pula. Caso contrário, adiciona.

Serviços:
  1. certificado_pcd_inss          — Comprovação de deficiência pelo INSS (LC 142/2013)
  2. carteira_identificacao_pcd    — CIPCD nacional (Lei 14.624/2023)
  3. reabilitacao_profissional_inss — Reabilitação Profissional INSS (Lei 8.213/91)
  4. pensao_talidomida              — Pensão Especial Talidomida (Lei 7.070/1982)
  5. pensao_hanseniase              — Pensão Especial Hanseníase (Lei 11.520/2007)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "direitos.json"

NOVAS_CATEGORIAS = [
    {
        "id": "certificado_pcd_inss",
        "titulo": "Certificado de Deficiência — Avaliação Biopsicossocial INSS",
        "icone": "📄",
        "resumo": "Avaliação biopsicossocial gratuita do INSS que comprova a condição de pessoa com deficiência (leve, moderada ou grave) para fins de aposentadoria especial (LC 142/2013), saque do FGTS e outros direitos federais.",
        "base_legal": [
            {
                "lei": "Lei Complementar 142/2013 — Aposentadoria da PcD",
                "artigo": "Art. 3º",
                "link": "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp142.htm"
            },
            {
                "lei": "Decreto 8.145/2013 — Regulamenta LC 142/2013",
                "artigo": "Art. 2º",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/decreto/d8145.htm"
            },
            {
                "lei": "Lei 13.146/2015 — Estatuto da PcD (LBI)",
                "artigo": "Art. 2º",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm"
            }
        ],
        "requisitos": [
            "Ser segurado(a) do INSS (contribuinte ativo ou em período de graça)",
            "Possuir deficiência física, mental, intelectual ou sensorial de longo prazo (≥ 2 anos)",
            "Solicitar avaliação biopsicossocial pelo canal Meu INSS",
            "Comparecer à perícia médica e à avaliação social do INSS"
        ],
        "documentos": [
            "Documento de identidade com foto (RG ou CNH)",
            "CPF",
            "Comprovante de residência",
            "Laudo médico recente com CID e descrição da deficiência",
            "Relatórios de equipe multidisciplinar (se houver)",
            "Histórico de contribuições ao INSS"
        ],
        "passo_a_passo": [
            "Acesse Meu INSS (app ou meu.inss.gov.br) e faça login com gov.br",
            "Escolha 'Novo Pedido' e procure por 'Aposentadoria da Pessoa com Deficiência' ou 'Avaliação Biopsicossocial'",
            "Anexe laudo médico, documentos pessoais e histórico clínico",
            "Agende e compareça à perícia médica e à avaliação social do INSS",
            "Aguarde o resultado da avaliação (grau leve, moderado ou grave)",
            "O certificado fica disponível em Meu INSS para uso em outros direitos federais"
        ],
        "dicas": [
            "A avaliação é GRATUITA e obrigatória para aposentadoria pela LC 142/2013",
            "Leve TODOS os laudos médicos antigos e recentes — quanto mais documentação, melhor a avaliação",
            "Se o INSS negar ou classificar grau menor que o esperado, é possível recorrer administrativamente em até 30 dias",
            "Em caso de negativa indevida, procure a Defensoria Pública da União (DPU) — atendimento gratuito",
            "A classificação influencia diretamente o tempo de contribuição exigido na aposentadoria"
        ],
        "valor": "Gratuito",
        "onde": "Meu INSS (app ou meu.inss.gov.br) e agências do INSS",
        "links": [
            {
                "titulo": "Meu INSS — Portal de Serviços",
                "url": "https://meu.inss.gov.br/",
                "tipo": "oficial",
                "esfera": "federal"
            },
            {
                "titulo": "Aposentadoria da PcD (INSS)",
                "url": "https://www.gov.br/inss/pt-br/saiba-mais/aposentadorias/aposentadoria-da-pessoa-com-deficiencia",
                "tipo": "informativo",
                "esfera": "federal"
            },
            {
                "titulo": "LC 142/2013 (texto completo)",
                "url": "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp142.htm",
                "tipo": "oficial",
                "esfera": "federal"
            }
        ],
        "tags": ["inss", "certificado", "avaliacao", "biopsicossocial", "aposentadoria", "lc142"],
        "emergencia": {
            "mensagem": "Se o INSS negar a avaliação ou classificar grau incorreto, procure a Defensoria Pública da União (DPU) — atendimento gratuito.",
            "telefone": "129",
            "orgao": "Defensoria Pública da União"
        },
        "cids_relacionados": [],
        "aplicavel_a_todas_deficiencias": True
    },
    {
        "id": "carteira_identificacao_pcd",
        "titulo": "CIPCD — Carteira de Identificação da Pessoa com Deficiência (Federal)",
        "icone": "🪪",
        "resumo": "Documento nacional gratuito instituído pela Lei 14.624/2023 que comprova a condição de pessoa com deficiência em todo o Brasil e dá acesso a atendimento prioritário, serviços públicos e privados.",
        "base_legal": [
            {
                "lei": "Lei 14.624/2023 — Cria a CIPCD nacional",
                "artigo": "Art. 1º e 2º",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/lei/l14624.htm"
            },
            {
                "lei": "Lei 13.146/2015 — Estatuto da PcD (LBI)",
                "artigo": "Art. 9º",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm"
            },
            {
                "lei": "Lei 9.265/1996 — Gratuidade de documentos essenciais",
                "artigo": "Art. 1º, VII",
                "link": "https://www.planalto.gov.br/ccivil_03/leis/l9265.htm"
            }
        ],
        "requisitos": [
            "Ser pessoa com deficiência (qualquer tipo — física, intelectual, mental, sensorial ou múltipla)",
            "Possuir laudo médico com CID que comprove a deficiência",
            "Apresentar documentos pessoais e comprovante de residência",
            "Solicitar a emissão no órgão competente da União, estado ou município"
        ],
        "documentos": [
            "Laudo médico com CID-10 ou CID-11",
            "Documento de identidade com foto",
            "CPF",
            "Comprovante de residência atualizado",
            "Foto 3x4 recente",
            "Documento do responsável legal (se aplicável)"
        ],
        "passo_a_passo": [
            "Verifique no site da prefeitura ou da Secretaria Estadual de Direitos da PcD qual órgão emissor da sua cidade/estado",
            "Reúna os documentos exigidos (laudo, identidade, CPF, comprovante de residência, foto)",
            "Faça o requerimento presencialmente ou online (varia conforme o local)",
            "Aguarde a emissão (prazo varia, geralmente 30 a 90 dias)",
            "Retire a carteira no local indicado ou receba por correio",
            "A CIPCD tem validade nacional e deve ser apresentada em todo o território brasileiro"
        ],
        "dicas": [
            "A emissão é GRATUITA por lei (Lei 9.265/1996)",
            "A CIPCD nacional é diferente da CIPTEA (TEA) — você pode ter as duas",
            "Garante atendimento prioritário em bancos, hospitais, supermercados e órgãos públicos",
            "Em caso de recusa de atendimento prioritário, denuncie pelo Disque 100 (24h, gratuito)",
            "Alguns estados já emitem versão digital pelo gov.br ou pelo app do estado"
        ],
        "valor": "Gratuito",
        "onde": "Órgão emissor designado pela União, estado ou município (geralmente Secretaria de Direitos da PcD)",
        "links": [
            {
                "titulo": "Lei 14.624/2023 (texto completo)",
                "url": "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/lei/l14624.htm",
                "tipo": "oficial",
                "esfera": "federal"
            },
            {
                "titulo": "Ministério dos Direitos Humanos — PcD",
                "url": "https://www.gov.br/mdh/pt-br/assuntos/noticias",
                "tipo": "informativo",
                "esfera": "federal"
            },
            {
                "titulo": "Disque 100 — denúncias de violações",
                "url": "https://www.gov.br/mdh/pt-br/acesso-a-informacao/disque-100",
                "tipo": "oficial",
                "esfera": "federal"
            }
        ],
        "tags": ["carteira", "identificacao", "cipcd", "lei14624", "federal", "prioridade"],
        "emergencia": {
            "mensagem": "Se for negada a emissão ou o atendimento prioritário com a CIPCD, denuncie pelo Disque 100.",
            "telefone": "100",
            "orgao": "Disque Direitos Humanos"
        },
        "cids_relacionados": [],
        "aplicavel_a_todas_deficiencias": True
    },
    {
        "id": "reabilitacao_profissional_inss",
        "titulo": "Reabilitação Profissional — INSS",
        "icone": "🛠️",
        "resumo": "Serviço gratuito do INSS que oferece reabilitação física, profissional e social a segurados com deficiência ou incapacidade laboral, incluindo cursos, próteses, órteses e adaptações para retorno ao trabalho.",
        "base_legal": [
            {
                "lei": "Lei 8.213/1991 — Plano de Benefícios da Previdência",
                "artigo": "Arts. 89 a 93",
                "link": "https://www.planalto.gov.br/ccivil_03/leis/l8213cons.htm"
            },
            {
                "lei": "Decreto 3.048/1999 — Regulamento da Previdência Social",
                "artigo": "Arts. 136 a 141",
                "link": "https://www.planalto.gov.br/ccivil_03/decreto/d3048.htm"
            },
            {
                "lei": "Lei 13.146/2015 — Estatuto da PcD (LBI)",
                "artigo": "Art. 36",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm"
            }
        ],
        "requisitos": [
            "Ser segurado(a) do INSS (incluindo aposentado por invalidez e beneficiário de auxílio por incapacidade)",
            "Possuir condição que dificulte ou impossibilite o exercício da atividade habitual",
            "Ser indicado(a) à reabilitação pela perícia médica do INSS",
            "Aderir voluntariamente ao programa após avaliação"
        ],
        "documentos": [
            "Documento de identidade com foto",
            "CPF",
            "Comprovante de residência",
            "Laudos médicos e exames recentes",
            "Comprovante de vínculo com o INSS (CTPS, carnê de contribuição, extrato CNIS)",
            "Currículo ou histórico profissional (quando aplicável)"
        ],
        "passo_a_passo": [
            "Procure uma agência do INSS ou Meu INSS e solicite encaminhamento à reabilitação profissional",
            "Compareça à perícia médica para avaliação inicial e definição do plano",
            "Participe das avaliações multidisciplinares (médico, assistente social, psicólogo, fisioterapeuta)",
            "Adira ao programa de reabilitação (cursos, treinamentos, próteses ou órteses, se necessário)",
            "Conclua o programa e receba o Certificado de Reabilitação Profissional",
            "Acompanhamento pós-reabilitação por até 1 ano para garantir o retorno ao trabalho"
        ],
        "dicas": [
            "O serviço é GRATUITO e inclui transporte, alimentação e materiais durante o programa",
            "Empresas com 100+ empregados têm cota de PcD (Lei 8.213/91, Art. 93) — reabilitados contam para a cota",
            "Se o empregador recusar reintegração pós-reabilitação, procure o Ministério Público do Trabalho (MPT)",
            "Próteses, órteses e cadeiras de rodas podem ser fornecidas pelo INSS sem custo durante o programa",
            "Em caso de negativa, recorra administrativamente em até 30 dias ou procure a DPU"
        ],
        "valor": "Gratuito (inclui transporte, alimentação e materiais)",
        "onde": "Agências do INSS, Centros de Referência Profissional e Meu INSS",
        "links": [
            {
                "titulo": "Reabilitação Profissional (INSS)",
                "url": "https://www.gov.br/inss/pt-br/direitos-e-deveres/beneficios-assistenciais",
                "tipo": "informativo",
                "esfera": "federal"
            },
            {
                "titulo": "Meu INSS — Portal de Serviços",
                "url": "https://meu.inss.gov.br/",
                "tipo": "oficial",
                "esfera": "federal"
            },
            {
                "titulo": "Lei 8.213/1991 (texto completo)",
                "url": "https://www.planalto.gov.br/ccivil_03/leis/l8213cons.htm",
                "tipo": "oficial",
                "esfera": "federal"
            }
        ],
        "tags": ["inss", "reabilitacao", "profissional", "retorno", "trabalho", "lei8213"],
        "emergencia": {
            "mensagem": "Se o INSS negar a reabilitação ou se o empregador recusar reintegração, procure a Defensoria Pública da União (DPU) ou o MPT.",
            "telefone": "129",
            "orgao": "Defensoria Pública da União / Ministério Público do Trabalho"
        },
        "cids_relacionados": [],
        "aplicavel_a_todas_deficiencias": True
    },
    {
        "id": "pensao_talidomida",
        "titulo": "Pensão Especial — Síndrome da Talidomida",
        "icone": "💊",
        "resumo": "Pensão mensal vitalícia paga pelo INSS a pessoas com deficiência física decorrente do uso da talidomida pela mãe durante a gestação, instituída pela Lei 7.070/1982 e atualizada por leis posteriores.",
        "base_legal": [
            {
                "lei": "Lei 7.070/1982 — Pensão Especial Talidomida",
                "artigo": "Art. 1º",
                "link": "https://www.planalto.gov.br/ccivil_03/leis/l7070.htm"
            },
            {
                "lei": "Lei 8.686/1993 — Reajuste da Pensão Talidomida",
                "artigo": "Art. 1º",
                "link": "https://www.planalto.gov.br/ccivil_03/leis/l8686.htm"
            },
            {
                "lei": "Lei 12.190/2010 — Indenização adicional",
                "artigo": "Art. 1º",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2010/lei/l12190.htm"
            },
            {
                "lei": "Lei 13.985/2020 — Atualização do valor",
                "artigo": "Art. 1º",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/lei/l13985.htm"
            }
        ],
        "requisitos": [
            "Possuir deficiência física decorrente comprovadamente do uso de talidomida pela mãe na gestação",
            "Apresentar laudo médico pericial reconhecendo o nexo causal com a talidomida",
            "Solicitar a pensão pelo INSS (não exige contribuição prévia)",
            "Ser brasileiro(a) ou residente permanente no Brasil"
        ],
        "documentos": [
            "Documento de identidade com foto",
            "CPF",
            "Comprovante de residência",
            "Laudo médico pericial com nexo causal à talidomida",
            "Certidão de nascimento",
            "Histórico médico desde o nascimento (quando disponível)"
        ],
        "passo_a_passo": [
            "Procure uma agência do INSS ou acesse Meu INSS e solicite a Pensão Especial Talidomida (Lei 7.070/1982)",
            "Anexe laudos médicos comprovando a deficiência física e o nexo causal com a talidomida",
            "Compareça à perícia médica do INSS para avaliação",
            "Aguarde a análise e o reconhecimento do direito",
            "Em caso de deferimento, a pensão é vitalícia, mensal e cumulativa com outros benefícios",
            "Para a indenização adicional (Lei 12.190/2010), faça pedido separado pela mesma via"
        ],
        "dicas": [
            "A pensão é VITALÍCIA e CUMULATIVA com aposentadoria, BPC e outros benefícios",
            "Não exige contribuição prévia ao INSS — é benefício de natureza indenizatória",
            "A Lei 12.190/2010 garantiu indenização adicional única — verifique se já recebeu",
            "Os valores são reajustados periodicamente por leis específicas",
            "Procure a Associação Brasileira dos Portadores da Síndrome da Talidomida (ABPST) para apoio jurídico"
        ],
        "valor": "Pensão mensal vitalícia (valor proporcional ao grau de deficiência) + indenização adicional única (Lei 12.190/2010)",
        "onde": "Meu INSS (app ou meu.inss.gov.br) e agências do INSS",
        "links": [
            {
                "titulo": "Lei 7.070/1982 (texto completo)",
                "url": "https://www.planalto.gov.br/ccivil_03/leis/l7070.htm",
                "tipo": "oficial",
                "esfera": "federal"
            },
            {
                "titulo": "Lei 13.985/2020 — Atualização do valor",
                "url": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/lei/l13985.htm",
                "tipo": "oficial",
                "esfera": "federal"
            },
            {
                "titulo": "Meu INSS — Portal de Serviços",
                "url": "https://meu.inss.gov.br/",
                "tipo": "oficial",
                "esfera": "federal"
            }
        ],
        "tags": ["pensao", "talidomida", "indenizacao", "vitalicia", "lei7070", "inss"],
        "emergencia": {
            "mensagem": "Se o INSS negar a pensão ou não reconhecer o nexo causal com a talidomida, procure a Defensoria Pública da União (DPU).",
            "telefone": "129",
            "orgao": "Defensoria Pública da União"
        },
        "cids_relacionados": [],
        "aplicavel_a_todas_deficiencias": False
    },
    {
        "id": "pensao_hanseniase",
        "titulo": "Pensão Especial — Hanseníase (Compulsoriamente Isolados)",
        "icone": "🤝",
        "resumo": "Pensão mensal vitalícia e indenização paga pelo Governo Federal a pessoas atingidas pela hanseníase que foram submetidas a isolamento e internação compulsórios em hospitais-colônia até 31/12/1986 (Lei 11.520/2007).",
        "base_legal": [
            {
                "lei": "Lei 11.520/2007 — Pensão Especial Hanseníase",
                "artigo": "Art. 1º",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2007/lei/l11520.htm"
            },
            {
                "lei": "Decreto 6.168/2007 — Regulamenta Lei 11.520/2007",
                "artigo": "Art. 1º",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2007/decreto/d6168.htm"
            },
            {
                "lei": "Lei 13.146/2015 — Estatuto da PcD (LBI)",
                "artigo": "Art. 2º",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm"
            }
        ],
        "requisitos": [
            "Ter sido pessoa atingida pela hanseníase e submetida a isolamento e internação compulsórios em hospital-colônia até 31/12/1986",
            "Comprovar o isolamento por meio de prontuários, registros médicos ou declarações testemunhais",
            "Solicitar a pensão pelo Ministério dos Direitos Humanos e Cidadania (MDHC)",
            "Ser brasileiro(a) e residente no Brasil"
        ],
        "documentos": [
            "Documento de identidade com foto",
            "CPF",
            "Comprovante de residência",
            "Comprovação do isolamento compulsório (prontuários, registros do hospital-colônia, declarações)",
            "Laudos médicos relacionados à hanseníase",
            "Certidão de nascimento"
        ],
        "passo_a_passo": [
            "Reúna documentos que comprovem o isolamento compulsório no hospital-colônia (prontuário, declarações)",
            "Acesse o site do Ministério dos Direitos Humanos e Cidadania (MDHC) ou ligue para o Disque 100",
            "Faça o requerimento da Pensão Especial Hanseníase (Lei 11.520/2007)",
            "Anexe toda a documentação comprobatória",
            "Aguarde a análise do MDHC e a publicação da concessão",
            "A pensão é vitalícia e mensal, paga pelo INSS após a concessão"
        ],
        "dicas": [
            "A pensão é VITALÍCIA e CUMULATIVA com aposentadoria, BPC e outros benefícios",
            "Hospitais-colônia ativos no Brasil até 1986: Itanhenga (ES), Padre Bento (SP), Marituba (PA) entre outros",
            "Movimento de Reintegração das Pessoas Atingidas pela Hanseníase (MORHAN) oferece apoio para a comprovação",
            "Em caso de negativa, procure a Defensoria Pública da União (DPU) — atendimento gratuito",
            "Familiares de pessoas já falecidas que foram isoladas têm direito à pensão por morte (dependentes habilitados)"
        ],
        "valor": "Pensão mensal vitalícia fixada em lei (atualizada periodicamente)",
        "onde": "Ministério dos Direitos Humanos e Cidadania (MDHC) e Disque 100",
        "links": [
            {
                "titulo": "Lei 11.520/2007 (texto completo)",
                "url": "https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2007/lei/l11520.htm",
                "tipo": "oficial",
                "esfera": "federal"
            },
            {
                "titulo": "Decreto 6.168/2007 (texto completo)",
                "url": "https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2007/decreto/d6168.htm",
                "tipo": "oficial",
                "esfera": "federal"
            },
            {
                "titulo": "Ministério dos Direitos Humanos e Cidadania",
                "url": "https://www.gov.br/mdh/pt-br",
                "tipo": "informativo",
                "esfera": "federal"
            },
            {
                "titulo": "Disque 100 — denúncias e informações",
                "url": "https://www.gov.br/mdh/pt-br/acesso-a-informacao/disque-100",
                "tipo": "oficial",
                "esfera": "federal"
            }
        ],
        "tags": ["pensao", "hanseniase", "isolamento", "compulsorio", "lei11520", "mdhc"],
        "emergencia": {
            "mensagem": "Se a pensão for negada, procure a Defensoria Pública da União (DPU) ou o MORHAN para apoio jurídico gratuito.",
            "telefone": "129",
            "orgao": "Defensoria Pública da União / MORHAN"
        },
        "cids_relacionados": [],
        "aplicavel_a_todas_deficiencias": False
    }
]


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cats = data["categorias"]
    existing_ids = {c["id"] for c in cats}

    added = []
    for nova in NOVAS_CATEGORIAS:
        if nova["id"] in existing_ids:
            print(f"  ⏭️  já existe: {nova['id']}")
            continue
        cats.append(nova)
        added.append(nova["id"])
        print(f"  ✅ adicionado: {nova['id']}")

    if added:
        DATA.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
        print(f"\n✅ {len(added)} categorias adicionadas. Total agora: {len(cats)}")
    else:
        print(f"\nNenhuma alteração. Total: {len(cats)}")


if __name__ == "__main__":
    main()
