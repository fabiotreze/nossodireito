#!/usr/bin/env python3
"""Add 5 new LBI-aligned categories and expand disability classifications."""
import json
from datetime import date

with open('data/direitos.json', encoding='utf-8') as f:
    d = json.load(f)

# ──────── NEW CATEGORIES ────────
new_categories = [
    {
        "id": "acessibilidade_arquitetonica",
        "titulo": "Acessibilidade — Edificações, Espaços Públicos e Serviços",
        "icone": "♿",
        "resumo": "Pessoas com deficiência têm direito a acessibilidade em edificações públicas e privadas, espaços urbanos, serviços e equipamentos públicos, conforme a LBI e a NBR 9050.",
        "base_legal": [
            {
                "lei": "Lei 13.146/2015 (Estatuto da Pessoa com Deficiência)",
                "artigo": "Art. 53 a 62",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm"
            },
            {
                "lei": "Lei 10.098/2000 — Normas Gerais de Acessibilidade",
                "artigo": "Art. 1º a 18",
                "link": "https://www.planalto.gov.br/ccivil_03/leis/l10098.htm"
            },
            {
                "lei": "Decreto 5.296/2004 — Regulamentação da Acessibilidade",
                "artigo": "Art. 10 a 22",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/decreto/d5296.htm"
            },
            {
                "lei": "NBR 9050:2020 (ABNT) — Acessibilidade em Edificações",
                "artigo": "Norma técnica completa",
                "link": "https://www.gov.br/governodigital/pt-br/acessibilidade-digital"
            }
        ],
        "requisitos": [
            "Ser pessoa com deficiência ou mobilidade reduzida",
            "Identificar a barreira de acessibilidade na edificação ou espaço público",
            "Registrar a denúncia junto ao órgão competente (Ministério Público, Defensoria, Procon ou Prefeitura)"
        ],
        "documentos": [
            "Documento de identidade (RG) e CPF",
            "Laudo médico com CID (quando necessário comprovar a deficiência)",
            "Fotos ou registro da barreira de acessibilidade (recomendado)",
            "Protocolo de reclamação anterior (se houver)"
        ],
        "passo_a_passo": [
            "Identifique a barreira de acessibilidade (rampa ausente, banheiro inacessível, calçada irregular, falta de piso tátil, etc.)",
            "Notifique o responsável pelo estabelecimento ou espaço público, solicitando adequação por escrito",
            "Se não houver resposta, registre denúncia no Ministério Público (promotoria de acessibilidade), Defensoria Pública ou Procon",
            "Para espaços públicos municipais, acione a Prefeitura pelo canal de ouvidoria (ex: SP156, 156, Fala.BR)",
            "Acompanhe o andamento da denúncia pelo protocolo recebido",
            "Em caso de obra nova ou reforma, exija que o projeto inclua acessibilidade conforme NBR 9050"
        ],
        "dicas": [
            "Toda edificação nova (pública ou privada de uso coletivo) DEVE ser acessível desde o projeto — é obrigação legal, não favor",
            "Edificações existentes devem ser adaptadas progressivamente — a falta de acessibilidade é infração (Art. 56 da LBI)",
            "Banheiro acessível DEVE existir em todo estabelecimento de uso público — shopping, restaurante, cinema, hospital, escola",
            "Rampas devem ter inclinação máxima de 8,33% (conforme NBR 9050) e corrimãos dos dois lados",
            "Elevadores são obrigatórios em edificações com mais de um pavimento de uso público",
            "Piso tátil (direcional e alerta) é obrigatório em calçadas e espaços públicos",
            "Denuncie barreiras pelo Disque 100, Fala.BR (falabr.cgu.gov.br), ou diretamente ao MP",
            "Sempre verifique se o site termina em .gov.br antes de fornecer dados pessoais"
        ],
        "valor": "Direito universal — não envolve custo para a PcD. Adequações são responsabilidade do proprietário/gestor do espaço.",
        "onde": "Ministério Público / Defensoria Pública / Procon / Prefeitura (ouvidoria) / Disque 100",
        "links": [
            {
                "titulo": "Portal de Acessibilidade Digital — Governo Federal",
                "url": "https://www.gov.br/governodigital/pt-br/acessibilidade-digital"
            },
            {
                "titulo": "ONDH — Ouvidoria Nacional de Direitos Humanos (Disque 100)",
                "url": "https://www.gov.br/mdh/pt-br/ondh"
            },
            {
                "titulo": "Fala.BR — Plataforma de Ouvidoria e Acesso à Informação",
                "url": "https://falabr.cgu.gov.br/"
            }
        ],
        "tags": [
            "acessibilidade", "edificação", "rampa", "elevador", "banheiro acessível",
            "piso tátil", "calçada", "NBR 9050", "barreira", "espaço público",
            "obra", "reforma", "inclusão", "mobilidade reduzida", "cadeirante",
            "urbanismo", "prefeitura", "Ministério Público", "denúncia"
        ]
    },
    {
        "id": "capacidade_legal",
        "titulo": "Capacidade Legal — Curatela e Tomada de Decisão Apoiada",
        "icone": "⚖️",
        "resumo": "A LBI garante que PcD tem plena capacidade civil. A curatela é medida excepcional, limitada a atos patrimoniais e negociais. A Tomada de Decisão Apoiada é alternativa que preserva a autonomia.",
        "base_legal": [
            {
                "lei": "Lei 13.146/2015 (Estatuto da Pessoa com Deficiência)",
                "artigo": "Art. 6º, Art. 84 a 87",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm"
            },
            {
                "lei": "Código de Processo Civil (Lei 13.105/2015)",
                "artigo": "Art. 747 a 763 (Curatela), Art. 1.783-A (TDA)",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm"
            },
            {
                "lei": "Código Civil (Lei 10.406/2002)",
                "artigo": "Art. 3º e 4º (alterados pela LBI)",
                "link": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"
            },
            {
                "lei": "Decreto 6.949/2009 — Convenção da ONU sobre Direitos da PcD",
                "artigo": "Art. 12 (Reconhecimento legal em igualdade de condições)",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2009/decreto/d6949.htm"
            }
        ],
        "requisitos": [
            "Ser pessoa com deficiência que necessita de apoio para atos da vida civil",
            "Para TDA: indicar ao menos 2 apoiadores de confiança",
            "Para Curatela: decisão judicial é obrigatória — não pode ser imposta sem processo"
        ],
        "documentos": [
            "Documento de identidade (RG) e CPF da pessoa curatelada e do curador/apoiador",
            "Laudo médico com CID detalhando a deficiência e o grau de apoio necessário",
            "Certidão de nascimento ou casamento",
            "Petição inicial (para ação de curatela ou TDA, via Defensoria ou advogado)"
        ],
        "passo_a_passo": [
            "Avalie se a pessoa realmente precisa de curatela ou se a Tomada de Decisão Apoiada (TDA) é suficiente — prefira sempre a TDA",
            "Para TDA: a própria pessoa escolhe 2 apoiadores de confiança e apresenta pedido ao juiz com advogado ou Defensoria",
            "Para Curatela: um familiar ou o Ministério Público ingressa com ação judicial de interdição (última opção)",
            "O juiz realizará entrevista pessoal com a pessoa com deficiência — obrigatório (não pode ser decidido só com laudo)",
            "A curatela define EXATAMENTE quais atos o curador pode praticar — NÃO pode abranger direito ao corpo, sexualidade, casamento, voto, trabalho, educação ou religião (Art. 85 LBI)",
            "A curatela deve ser revisada periodicamente e pode ser levantada a qualquer momento"
        ],
        "dicas": [
            "Desde 2016 (LBI), deficiência NÃO significa incapacidade civil — PcD pode casar, votar, trabalhar e decidir sobre tratamento médico",
            "A curatela é medida EXCEPCIONAL e PROPORCIONAL — não remove todos os direitos; é limitada a atos patrimoniais e negociais",
            "A Tomada de Decisão Apoiada (TDA) é a alternativa preferencial — a pessoa MANTÉM sua capacidade e recebe apoio de 2 pessoas de confiança",
            "Ninguém pode ser internado contra sua vontade por ter deficiência — internação involuntária só com laudo médico e comunicação ao MP em 72h",
            "Se um familiar está sendo curatelado de forma abusiva, denuncie à Defensoria Pública ou ao Disque 100",
            "A esterilização forçada de PcD é CRIME (Art. 10 LBI) — pena de 2 a 5 anos de reclusão",
            "Sempre verifique se o site termina em .gov.br antes de fornecer dados pessoais"
        ],
        "valor": "Gratuito pela Defensoria Pública. Se com advogado particular, custos variam.",
        "onde": "Defensoria Pública (gratuito) / Vara de Família ou Vara Cível / Ministério Público",
        "links": [
            {
                "titulo": "DPU — Defensoria Pública da União (contatos)",
                "url": "https://www.dpu.def.br/contatos-dpu"
            },
            {
                "titulo": "Secretaria Nacional dos Direitos da PcD",
                "url": "https://www.gov.br/mdh/pt-br/navegue-por-temas/pessoa-com-deficiencia"
            },
            {
                "titulo": "ONDH — Disque 100 (denúncias)",
                "url": "https://www.gov.br/mdh/pt-br/ondh"
            }
        ],
        "tags": [
            "curatela", "interdição", "capacidade civil", "tomada de decisão apoiada",
            "TDA", "autonomia", "incapacidade", "tutela", "guardianship",
            "casamento PcD", "voto PcD", "direitos civis", "Defensoria Pública",
            "Código Civil", "LBI Art. 84", "Art. 85"
        ]
    },
    {
        "id": "crimes_contra_pcd",
        "titulo": "Crimes contra PcD — Discriminação, Denúncia e Penalidades",
        "icone": "🚨",
        "resumo": "Discriminar, abandonar, reter documentos ou apropriar-se de benefícios de PcD são crimes com pena de 1 a 5 anos de reclusão. Denuncie pelo Disque 100 ou delegacia.",
        "base_legal": [
            {
                "lei": "Lei 13.146/2015 (Estatuto da Pessoa com Deficiência)",
                "artigo": "Art. 88 a 91",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm"
            },
            {
                "lei": "Lei 7.853/1989 — Crimes contra PcD",
                "artigo": "Art. 8º",
                "link": "https://www.planalto.gov.br/ccivil_03/leis/l7853.htm"
            },
            {
                "lei": "Código Penal — Abandono (Art. 133), Maus-tratos (Art. 136)",
                "artigo": "Art. 133 e 136",
                "link": "https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm"
            }
        ],
        "requisitos": [
            "Ser vítima ou testemunha de crime ou discriminação contra PcD",
            "Identificar o tipo de violação: discriminação, abandono, retenção de documentos, apropriação de benefícios, violência",
            "Reunir provas se possível (fotos, vídeos, mensagens, testemunhas)"
        ],
        "documentos": [
            "Documento de identidade (RG) e CPF da vítima ou denunciante",
            "Provas da violação (fotos, vídeos, prints de mensagens, gravações)",
            "Dados do agressor (nome, local, empresa, se conhecidos)",
            "Boletim de Ocorrência (lavrado na delegacia ou delegacia online)"
        ],
        "passo_a_passo": [
            "Identifique o tipo de crime: discriminação (Art. 88), abandono (Art. 90), retenção de documentos (Art. 89), apropriação de benefício (Art. 91)",
            "Reúna provas: gravações, fotos, prints de mensagens, testemunhas — tudo é válido",
            "Registre Boletim de Ocorrência na delegacia mais próxima ou pela delegacia online do seu estado",
            "Ligue para o Disque 100 (ligação gratuita, 24h) para denunciar violações de direitos humanos de PcD",
            "Registre denúncia também no Fala.BR (falabr.cgu.gov.br) ou no Ministério Público",
            "Se a violação envolve estabelecimento comercial, registre também no Procon"
        ],
        "dicas": [
            "Discriminar PcD é CRIME: pena de 1 a 3 anos de reclusão + multa (Art. 88 LBI)",
            "Recusar matrícula escolar de PcD: crime com pena de 2 a 5 anos e multa (Lei 7.853/1989 Art. 8º)",
            "Apropriar-se de cartão de benefício, pensão ou provento de PcD: crime com pena de 1 a 4 anos (Art. 91 LBI)",
            "Abandonar PcD em hospital, casa de saúde ou entidade de atendimento: crime com pena de 6 meses a 3 anos (Art. 90 LBI)",
            "Reter cartão magnético, documento ou qualquer bem de PcD: crime com pena de 6 meses a 2 anos (Art. 89 LBI)",
            "A denúncia pode ser ANÔNIMA pelo Disque 100 — seu nome não será revelado",
            "Se a vítima for criança ou adolescente com deficiência, acione também o Conselho Tutelar",
            "Sempre verifique se o site termina em .gov.br antes de fornecer dados pessoais"
        ],
        "valor": "Denúncia gratuita. Assistência jurídica gratuita pela Defensoria Pública.",
        "onde": "Disque 100 / Delegacia de Polícia / Ministério Público / Defensoria Pública / Procon / Fala.BR",
        "links": [
            {
                "titulo": "ONDH — Ouvidoria Nacional de Direitos Humanos (Disque 100)",
                "url": "https://www.gov.br/mdh/pt-br/ondh"
            },
            {
                "titulo": "Fala.BR — Denúncia e Ouvidoria",
                "url": "https://falabr.cgu.gov.br/"
            },
            {
                "titulo": "MPF — Serviços ao Cidadão (denúncias e ouvidoria)",
                "url": "https://www.mpf.mp.br/mpf-servicos"
            },
            {
                "titulo": "DPU — Defensoria Pública da União",
                "url": "https://www.dpu.def.br/contatos-dpu"
            }
        ],
        "tags": [
            "crime", "discriminação", "denúncia", "Disque 100", "violência",
            "abandono", "maus-tratos", "delegacia", "boletim de ocorrência",
            "Ministério Público", "pena", "reclusão", "multa", "Lei 7.853",
            "Art. 88", "Art. 89", "Art. 90", "Art. 91", "Procon", "Fala.BR"
        ]
    },
    {
        "id": "acessibilidade_digital",
        "titulo": "Acessibilidade Digital — Comunicação, Libras e Tecnologias",
        "icone": "💻",
        "resumo": "Sites governamentais e de empresas devem ser acessíveis (eMAG/WCAG). PcD tem direito a intérprete de Libras em serviços públicos, legendas em TV, formatos acessíveis e planos telefônicos com desconto.",
        "base_legal": [
            {
                "lei": "Lei 13.146/2015 (Estatuto da Pessoa com Deficiência)",
                "artigo": "Art. 63 a 73",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm"
            },
            {
                "lei": "Lei 10.436/2002 — Libras como Língua Oficial",
                "artigo": "Art. 1º a 7º",
                "link": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10436.htm"
            },
            {
                "lei": "Decreto 5.626/2005 — Regulamenta Libras",
                "artigo": "Art. 25 a 29 (saúde), Art. 14 (educação)",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2005/decreto/d5626.htm"
            },
            {
                "lei": "Lei 10.098/2000 — Acessibilidade (comunicação)",
                "artigo": "Art. 17 e 18",
                "link": "https://www.planalto.gov.br/ccivil_03/leis/l10098.htm"
            }
        ],
        "requisitos": [
            "Ser pessoa com deficiência (visual, auditiva, intelectual, motora ou outra que demande acessibilidade digital)",
            "Identificar a barreira de comunicação ou de acesso digital",
            "Para intérprete de Libras: solicitar com antecedência ao órgão público ou saúde"
        ],
        "documentos": [
            "Documento de identidade (RG) e CPF",
            "Laudo médico com CID (quando necessário para solicitar recursos de acessibilidade)",
            "Solicitação formal ao órgão público (protocolo por escrito)"
        ],
        "passo_a_passo": [
            "Para intérprete de Libras em serviço público: solicite por escrito ao órgão com antecedência mínima de 5 dias úteis",
            "Para acessibilidade em site governamental: envie reclamação pelo Fala.BR informando a URL e a barreira encontrada",
            "Para legendas/audiodescrição em TV: registre reclamação na ANATEL (ligando 1331 ou pelo site)",
            "Para plano telefônico acessível: procure a operadora e solicite o plano com desconto para PcD (Resolução ANATEL 667/2016)",
            "Para publicações em formato acessível (Braille, áudio, texto digital): solicite à editora ou biblioteca pública",
            "Acompanhe o protocolo da solicitação e, se não atendido, acione o MP ou Defensoria"
        ],
        "dicas": [
            "Todo site do governo federal DEVE seguir o eMAG (Modelo de Acessibilidade de Governo Eletrônico) — se não seguir, denuncie",
            "Libras é língua oficial do Brasil (Lei 10.436/2002) — todo serviço público deve garantir comunicação em Libras quando solicitado",
            "Canais de TV aberta são obrigados a ter legendagem oculta (closed caption) e audiodescrição progressiva",
            "Pessoas surdas têm direito a videochamada com intérprete em órgãos públicos (Central de Libras)",
            "A ANATEL obriga operadoras a oferecer planos acessíveis com desconto para PcD",
            "Aplicativos bancários devem ser acessíveis — se não forem, registre reclamação no Banco Central",
            "Sempre verifique se o site termina em .gov.br antes de fornecer dados pessoais"
        ],
        "valor": "Direito gratuito — interpretação em Libras, legendas e acessibilidade digital são obrigações do prestador de serviço.",
        "onde": "Fala.BR / ANATEL (1331) / Ministério Público / Defensoria Pública / Portal eMAG (gov.br/governodigital)",
        "links": [
            {
                "titulo": "Portal de Acessibilidade Digital (eMAG) — Governo Digital",
                "url": "https://www.gov.br/governodigital/pt-br/acessibilidade-digital"
            },
            {
                "titulo": "Fala.BR — Denúncia e Ouvidoria",
                "url": "https://falabr.cgu.gov.br/"
            },
            {
                "titulo": "Secretaria Nacional dos Direitos da PcD",
                "url": "https://www.gov.br/mdh/pt-br/navegue-por-temas/pessoa-com-deficiencia"
            }
        ],
        "tags": [
            "acessibilidade digital", "Libras", "intérprete", "eMAG", "WCAG",
            "audiodescrição", "legenda", "closed caption", "deficiência auditiva",
            "deficiência visual", "leitor de tela", "Braille", "ANATEL",
            "comunicação acessível", "site acessível", "app acessível", "plano telefônico"
        ]
    },
    {
        "id": "reabilitacao",
        "titulo": "Habilitação e Reabilitação — Programas e Órteses/Próteses pelo SUS",
        "icone": "🏥",
        "resumo": "PcD tem direito a programas de habilitação e reabilitação pelo SUS, incluindo órteses, próteses, meios auxiliares de locomoção, intervenção precoce e reabilitação profissional pelo INSS.",
        "base_legal": [
            {
                "lei": "Lei 13.146/2015 (Estatuto da Pessoa com Deficiência)",
                "artigo": "Art. 14 a 17",
                "link": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm"
            },
            {
                "lei": "Lei 8.080/1990 — Lei Orgânica do SUS",
                "artigo": "Art. 6º, II (vigilância, prevenção e reabilitação)",
                "link": "https://www.planalto.gov.br/ccivil_03/leis/l8080.htm"
            },
            {
                "lei": "Portaria GM/MS nº 1.526/2023 — PNAISPD",
                "artigo": "Art. 1º",
                "link": "https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/s/saude-da-pessoa-com-deficiencia"
            },
            {
                "lei": "Decreto 3.298/1999 — Política Nacional para Integração da PcD",
                "artigo": "Art. 17 a 25",
                "link": "https://www.planalto.gov.br/ccivil_03/decreto/d3298.htm"
            }
        ],
        "requisitos": [
            "Ser pessoa com deficiência ou com risco de deficiência que necessite de habilitação/reabilitação",
            "Estar cadastrado no SUS (Cartão Nacional de Saúde)",
            "Encaminhamento médico da UBS ou especialista para o Centro Especializado em Reabilitação (CER)",
            "Para reabilitação profissional INSS: estar em benefício por incapacidade ou ser segurado"
        ],
        "documentos": [
            "Cartão Nacional de Saúde (CNS) — Cartão SUS",
            "Documento de identidade (RG) e CPF",
            "Laudo médico com CID e indicação de reabilitação",
            "Encaminhamento da Unidade Básica de Saúde (UBS)",
            "Para próteses/órteses: prescrição médica detalhada"
        ],
        "passo_a_passo": [
            "Procure a Unidade Básica de Saúde (UBS) mais próxima e solicite encaminhamento para reabilitação",
            "A UBS encaminhará ao Centro Especializado em Reabilitação (CER) mais próximo — são 4 modalidades: auditiva, física, intelectual e visual",
            "No CER, será feita avaliação multidisciplinar (fisioterapia, fonoaudiologia, terapia ocupacional, psicologia, etc.)",
            "Se necessário, será prescrita órtese, prótese ou meio auxiliar de locomoção (cadeira de rodas, muleta, andador) — tudo GRATUITO pelo SUS",
            "Para intervenção precoce (crianças 0-3 anos): solicite encaminhamento direto ao serviço de estimulação precoce",
            "Para reabilitação profissional: procure a agência do INSS e solicite inclusão no Programa de Reabilitação Profissional"
        ],
        "dicas": [
            "O SUS fornece GRATUITAMENTE: cadeira de rodas, próteses auditivas (aparelho auditivo), próteses de membro, órteses, coletes, bengalas, andadores, muletas",
            "A fila para próteses e órteses pode ser longa — insista e acompanhe seu protocolo; se demorar demais, acione a Defensoria Pública",
            "CERs (Centros Especializados em Reabilitação) existem em todos os estados — consulte no CNES (cnes.datasus.gov.br)",
            "Crianças com risco de atraso no desenvolvimento têm direito a estimulação precoce IMEDIATA — não espere diagnóstico definitivo",
            "A reabilitação profissional do INSS inclui cursos, capacitação e até equipamentos para nova atividade laboral",
            "Se o SUS negar órtese ou prótese prescrita, peça a negativa POR ESCRITO e procure a Defensoria — há jurisprudência consolidada",
            "Sempre verifique se o site termina em .gov.br antes de fornecer dados pessoais"
        ],
        "valor": "Gratuito pelo SUS — órteses, próteses, reabilitação e terapias. Reabilitação profissional pelo INSS também gratuita.",
        "onde": "UBS → CER (Centro Especializado em Reabilitação) / INSS (reabilitação profissional) / Mapa CNES (cnes.datasus.gov.br)",
        "links": [
            {
                "titulo": "Rede de Cuidados à Pessoa com Deficiência — SUS",
                "url": "https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/s/saude-da-pessoa-com-deficiencia"
            },
            {
                "titulo": "CNES — Cadastro de Estabelecimentos de Saúde (localizar CER)",
                "url": "https://cnes.datasus.gov.br/"
            },
            {
                "titulo": "Meu INSS — Reabilitação Profissional",
                "url": "https://meu.inss.gov.br/"
            },
            {
                "titulo": "Meu SUS Digital — App de Saúde",
                "url": "https://www.gov.br/saude/pt-br/composicao/seidigi/meususdigital"
            }
        ],
        "tags": [
            "reabilitação", "habilitação", "CER", "prótese", "órtese",
            "cadeira de rodas", "aparelho auditivo", "fisioterapia", "fonoaudiologia",
            "terapia ocupacional", "estimulação precoce", "SUS", "INSS",
            "reabilitação profissional", "intervenção precoce", "muleta", "andador"
        ]
    }
]

# ──────── NEW FONTES ────────
new_fontes = [
    {
        "nome": "Lei 10.436/2002 — Libras como Língua Oficial",
        "tipo": "legislacao",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10436.htm",
        "orgao": "Presidência da República",
        "consultado_em": "2026-02-16",
        "artigos_referenciados": ["Art. 1º a 7º"]
    },
    {
        "nome": "Lei 7.853/1989 — Crimes contra PcD e Política de Integração",
        "tipo": "legislacao",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l7853.htm",
        "orgao": "Presidência da República",
        "consultado_em": "2026-02-16",
        "artigos_referenciados": ["Art. 8º"]
    },
    {
        "nome": "Lei 8.080/1990 — Lei Orgânica do SUS",
        "tipo": "legislacao",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l8080.htm",
        "orgao": "Presidência da República",
        "consultado_em": "2026-02-16",
        "artigos_referenciados": ["Art. 6º, II"]
    },
    {
        "nome": "Decreto 3.298/1999 — Política Nacional para Integração da PcD",
        "tipo": "legislacao",
        "url": "https://www.planalto.gov.br/ccivil_03/decreto/d3298.htm",
        "orgao": "Presidência da República",
        "consultado_em": "2026-02-16",
        "artigos_referenciados": ["Art. 17 a 25"]
    },
    {
        "nome": "Código Civil (Lei 10.406/2002)",
        "tipo": "legislacao",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm",
        "orgao": "Presidência da República",
        "consultado_em": "2026-02-16",
        "artigos_referenciados": ["Art. 3º e 4º"]
    },
    {
        "nome": "Decreto 5.626/2005 — Regulamenta Libras",
        "tipo": "legislacao",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2005/decreto/d5626.htm",
        "orgao": "Presidência da República",
        "consultado_em": "2026-02-16",
        "artigos_referenciados": ["Art. 14, 25 a 29"]
    }
]

# ──────── NEW DISABILITY CLASSIFICATIONS ────────
new_classifications = [
    {
        "tipo": "Ostomizados (colostomia, ileostomia, urostomia)",
        "cid10": "K63.2, Z93",
        "cid11": "DA96, QC60",
        "criterio": "Reconhecidos como PcD pelo Decreto 3.298/1999 Art. 4º. Elegíveis a isenções tributárias, estacionamento especial, BPC e demais direitos.",
        "detalhes": "Inclui colostomia, ileostomia e urostomia. Pessoas ostomizadas frequentemente desconhecem que têm os mesmos direitos de PcD."
    },
    {
        "tipo": "Doença Renal Crônica em Diálise",
        "cid10": "N18",
        "cid11": "GB61",
        "criterio": "Doença renal crônica em estágio avançado (diálise) é considerada moléstia grave para isenção de IRPF (Lei 7.713/1988). Quando gera impedimento de longo prazo, configura deficiência para fins de BPC e demais direitos.",
        "detalhes": "Pacientes em hemodiálise têm direito a tarifa social de energia (equipamento elétrico domiciliar), isenção de IRPF e BPC quando houver impedimento funcional de longo prazo."
    },
    {
        "tipo": "Epilepsia Grave (refratária)",
        "cid10": "G40",
        "cid11": "8A60",
        "criterio": "Epilepsia refratária ao tratamento pode configurar deficiência quando gera impedimento de longo prazo. Elegível a isenção de IRPF (se considerada moléstia grave por laudo), BPC e aposentadoria especial.",
        "detalhes": "A epilepsia controlada por medicamentos geralmente não configura deficiência. Já a epilepsia refratária, com crises frequentes que impedem atividades diárias, pode ser reconhecida como deficiência pela avaliação biopsicossocial."
    },
    {
        "tipo": "Doenças Neuromusculares (distrofia muscular, ELA, esclerose múltipla)",
        "cid10": "G12, G35, G71",
        "cid11": "8B60, 8A40, 8C60",
        "criterio": "Doenças neuromusculares progressivas configuram deficiência física. Elegíveis a todos os direitos de PcD: BPC, isenções tributárias, aposentadoria especial, reabilitação.",
        "detalhes": "Inclui Esclerose Lateral Amiotrófica (ELA/G12.2), Esclerose Múltipla (G35), Distrofias Musculares (G71). São doenças progressivas que geram impedimento de longo prazo."
    },
    {
        "tipo": "Surdocegueira",
        "cid10": "Combinação H54 + H90/H91",
        "cid11": "Combinação 9B50 + AB00",
        "criterio": "Deficiência única que combina perda visual e auditiva. Reconhecida como deficiência múltipla com necessidades específicas de comunicação (Libras tátil, guia-intérprete).",
        "detalhes": "A surdocegueira demanda guia-intérprete especializado e métodos próprios de comunicação (Libras tátil, Tadoma, Braille). A pessoa surdocega tem direito a intérprete/guia em todos os serviços públicos."
    },
    {
        "tipo": "Fissura Labiopalatina",
        "cid10": "Q35 a Q37",
        "cid11": "LA40 a LA42",
        "criterio": "Reconhecida como deficiência física. Elegível a tratamento integral pelo SUS (cirurgias, fonoaudiologia, ortodontia) e demais direitos de PcD quando gera impedimento de longo prazo.",
        "detalhes": "O tratamento completo é realizado pelo SUS em centros especializados (ex: Hospital de Reabilitação de Anomalias Craniofaciais — HRAC/USP Bauru). Inclui cirurgias, fonoaudiologia e acompanhamento até a vida adulta."
    }
]

# ──────── APPLY CHANGES ────────
# Add new categories
d['categorias'].extend(new_categories)
print(f"Added {len(new_categories)} new categories (total: {len(d['categorias'])})")

# Add new fontes
d['fontes'].extend(new_fontes)
print(f"Added {len(new_fontes)} new fontes (total: {len(d['fontes'])})")

# Add new disability classifications
d['classificacao_deficiencia'].extend(new_classifications)
print(f"Added {len(new_classifications)} new classifications (total: {len(d['classificacao_deficiencia'])})")

# Update version and date
old_version = d['versao']
parts = old_version.split('.')
parts[1] = str(int(parts[1]) + 1)
parts[2] = '0'
d['versao'] = '.'.join(parts)
d['ultima_atualizacao'] = date.today().isoformat()
print(f"Version: {old_version} -> {d['versao']}")
print(f"Date: {d['ultima_atualizacao']}")

# Write out with proper formatting
with open('data/direitos.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=4)

print("\nDone!")
