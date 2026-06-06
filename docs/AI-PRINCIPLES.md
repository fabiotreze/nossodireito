# Princípios de uso de IA no NossoDireito

**Versão:** 1.43.21
**Última revisão:** 2026-06-06

Este documento descreve como a ferramenta opcional de análise por IA do NossoDireito se alinha aos
princípios públicos de **Responsible AI** da Microsoft, em particular aos
[Principles for AI-generated content](https://learn.microsoft.com/en-gb/principles-for-ai-generated-content)
publicados pela equipe do Microsoft Learn.

Adotamos esses princípios voluntariamente porque o NossoDireito utiliza
[Azure OpenAI](https://learn.microsoft.com/azure/ai-services/openai/) e somos beneficiários diretos
do mesmo programa de **Responsible AI** da Microsoft.

> Para a postura geral de Responsible AI da Microsoft, ver
> [Responsible AI at Microsoft](https://www.microsoft.com/ai/responsible-ai).

## Escopo: onde a IA é usada

A IA aparece em **um único ponto** da plataforma:

- **Ferramenta de análise opcional de documentos** ([`lib/ai-analyze.js`](../lib/ai-analyze.js)) —
  o usuário cola/envia um texto de laudo, atestado ou relatório médico e a IA sugere CIDs,
  datas relevantes e direitos potencialmente aplicáveis do catálogo.

A IA **não** é usada para gerar o catálogo de direitos
([`data/direitos.json`](../data/direitos.json)) — ele é 100% editorial humano,
referenciado em fontes oficiais (.gov.br, Planalto, INSS, Ministério da Saúde).

## Princípio 1 — Transparência

> _"All articles that contain any AI-generated content include text acknowledging the role of AI."_
> ([MS Learn](https://learn.microsoft.com/en-gb/principles-for-ai-generated-content))

Aplicação:

| Onde | Como sinalizamos |
|---|---|
| Antes da análise | Modal de consentimento opt-in nomeando "Análise com IA" e o modelo usado ([index.html L2552-2618](../index.html)) |
| Durante a análise | Spinner com mensagem explícita |
| No resultado (UI) | Banner persistente "🤖 Gerado por IA (Azure OpenAI gpt-4o-mini) — pode conter imprecisões" |
| No PDF exportado | Mesmo banner replicado no cabeçalho da impressão |
| No share por WhatsApp | Linha de rodapé "🤖 Conteúdo gerado por IA — verifique no .gov.br" |
| Em documentação pública | Esta página + [docs/RIPD.md](RIPD.md) + [docs/LGPD-COMPLIANCE.md](LGPD-COMPLIANCE.md) |

## Princípio 2 — Augmentation

> _"AI to augment their content creation process [...]. The author reviews and revises the AI-generated content."_

Aplicação:

- O catálogo (fonte editorial) é humano. A IA **não publica nada por conta própria** no portal.
- O resultado da IA é **destinado a uma única pessoa** (o próprio usuário) e é apresentado como
  sugestão de leitura cruzada com o catálogo, **nunca como decisão**.
- O usuário sempre pode **revisar manualmente** os direitos navegando pelas
  [42 categorias](../index.html) — a IA é atalho, não substituta.

## Princípio 3 — Validação

> _"The author tests all AI-generated code before publishing."_

Como o output da IA é gerado em tempo real para uma pessoa específica (não publicado em massa),
a validação editorial prévia não se aplica. Em compensação, adotamos:

- **Anonimização anterior** ao envio: nome, CPF, RG, e-mail, telefone, endereço, CEP e data
  de nascimento são removidos no navegador antes da chamada
  ([`shared/anonymizer.js`](../shared/anonymizer.js)).
- **Validação automatizada do resultado**: a resposta é validada contra schema JSON antes de
  ser renderizada ([`lib/ai-analyze.js`](../lib/ai-analyze.js)).
- **Disclaimer "orientação preliminar"** explícito no modal de consentimento e no rodapé do
  resultado: "não substitui parecer profissional (Defensoria, advogado(a), CRAS)".
- **Botão de revisão humana** (LGPD Art. 20) na própria UI, permitindo ao usuário solicitar
  revisão de decisão automatizada.
- **Testes de regressão** ([`tests/ai-analyze.test.mjs`](../tests/ai-analyze.test.mjs)) cobrindo
  comportamento esperado, fallback de erro e rate-limiting.

## Princípio 4 — Modelos declarados

> _"Currently, we use large language models that we access through Azure services to generate content."_

Declaração pública:

| Item | Valor |
|---|---|
| **Provedor** | [Azure OpenAI Service](https://learn.microsoft.com/azure/ai-services/openai/overview) |
| **Modelo** | `gpt-4o-mini` (deployment `cog-nossodireito-br-openai`) |
| **Região** | Brasil Sul (LGPD Art. 33 — transferência internacional não aplicável) |
| **Autenticação** | Managed Identity (sem chaves de API em código) |
| **Rede** | Private Endpoint, `publicNetworkAccess=Disabled` ([ARCHITECTURE.md](ARCHITECTURE.md)) |
| **Retenção** | Zero — configuração oficial Azure OpenAI (sem retenção de prompt nem resposta) |
| **Treino** | Os dados enviados **não** alimentam modelos da Microsoft/OpenAI |
| **Acordo legal** | [Microsoft Products and Services DPA](https://www.microsoft.com/licensing/docs/view/Microsoft-Products-and-Services-Data-Protection-Addendum-DPA) |

Mudanças de modelo serão refletidas neste documento e no modal de consentimento
([index.html L2567](../index.html)). Caso o modelo ou provedor mude, **o consentimento prévio
do usuário será reapresentado**.

## Para o usuário

Em linguagem simples (também disponível dentro do modal de consentimento):

- A IA é **opcional** — você precisa marcar duas caixas (consentimento + dados sensíveis) antes de cada uso.
- O texto vai para um computador da Microsoft no **Brasil** (Azure OpenAI, região Brasil Sul).
- O texto é **lido**, processado e a resposta volta. Nada fica armazenado.
- Seus dados **não treinam** modelos da Microsoft nem da OpenAI.
- Você pode **revogar o consentimento** a qualquer momento limpando os dados do site, e pedir
  **revisão humana** de qualquer resposta da IA (botão dentro do resultado, conforme LGPD Art. 20).
- A análise é **orientação preliminar** — não substitui Defensoria Pública, advogado(a) ou CRAS.

## Referências cruzadas

- [LGPD — Checklist Auditável](LGPD-COMPLIANCE.md) — secção 7 (Disclaimer e termos informativos)
- [RIPD — Relatório de Impacto à Proteção de Dados](RIPD.md) — secção R1 (tratamento de dados sensíveis)
- [Segurança e LGPD](SECURITY-LGPD.md) — fluxo E2E + Private Endpoint
- [Arquitetura](ARCHITECTURE.md) — diagrama de fluxo IA
- [Microsoft — Principles for AI-generated content](https://learn.microsoft.com/en-gb/principles-for-ai-generated-content)
- [Microsoft — Responsible AI](https://www.microsoft.com/ai/responsible-ai)
- [Microsoft — Azure OpenAI Data, privacy, and security](https://learn.microsoft.com/legal/cognitive-services/openai/data-privacy)
