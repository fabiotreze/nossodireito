# Estimativa de Custo (Azure Pricing Calculator)

**Version:** 1.34.1
**Updated:** 2026-05-24
**Region:** Brazil South (`brazilsouth`)
**Currency base:** USD

## Objetivo

Esta pagina lista os itens do projeto no formato do Azure Pricing Calculator,
com configuracao inicial sugerida para replica do ambiente atual.

## Escopo desta estimativa

Inclui apenas custos Azure do ambiente atual em Terraform:

- App Service Linux (B1)
- Azure OpenAI (gpt-4o-mini, Global Standard)
- Private Endpoint (OpenAI)
- Private DNS Zone (`privatelink.openai.azure.com`)
- Application Insights + Log Analytics Workspace
- Key Vault Standard
- Azure Monitor Alerts (volume baixo)

Nao inclui:

- Cloudflare (DNS/CDN/WAF)
- Custos de CI/CD GitHub
- Trafego de saida (egress) fora de franquias aplicaveis

## Itens para criar no Azure Pricing Calculator

1. Azure App Service

- Region: `Brazil South`
- Tier/SKU: `Basic B1` (Linux)
- Instances: `1`
- Hours/month: `730`

1. Azure OpenAI Service

- Region: `Brazil South`
- Deployment/model: `gpt-4o-mini` (Global Standard)
- Preencher consumo mensal de tokens:
  - Input tokens/month
  - Output tokens/month

1. Azure Private Link

- Meter: `Private Endpoint` (`0.01 USD/hour` de referencia)
- Quantity: `1 endpoint` x `730 h/mes`
- Data processed: estimar GB/mes (entrada + saida)

1. Azure DNS (Private)

- Meter: `Private DNS Zone`
- Quantity: `1 zona` (`privatelink.openai.azure.com`)
- DNS queries: estimar volume mensal

1. Log Analytics

- Region: `Brazil South`
- SKU: `Analytics Logs (PerGB2018)`
- Ingestion estimate: definir GB/mes (ex.: 1, 5, 20)
- Retention: 30 dias (conforme Terraform)

1. Application Insights

- Workspace-based (ligado ao Log Analytics)
- Considerar overage apenas se ultrapassar franquias aplicaveis

1. Key Vault

- SKU: `Standard`
- Meter principal: `Operations`
- Estimar operacoes/mes em blocos de 10k

## Referencia de precos (consulta 2026-05-18, retail)

Valores variam por contrato, impostos e mudancas da Azure.

- App Service B1 Linux (`brazilsouth`): `0.02 USD/h`
- Private Endpoint (`referencia oficial Azure Private Link`): `0.01 USD/h`
- Private Link Data Processed (`referencia oficial`): `0.01 USD/GB` por direção
- Private DNS Zone (`referencia de mercado Azure DNS`): `~0.50 USD/mes` por zona
- Log Analytics Analytics Logs (`brazilsouth`): `2.3 USD/GB` (ingestao analisada)
- Key Vault Standard Operations (`brazilsouth`): `0.03 USD / 10k operacoes`

## Baseline mensal sem IA (estimativa rapida)

Premissas:

- App Service Linux B1: `730 h/mes`
- Logs: `1 GB/mes`
- Key Vault: `100k operacoes/mes`

Calculo:

- App Service: `730 * 0.02 = 14.60 USD`
- Log Analytics: `1 * 2.3 = 2.30 USD`
- Key Vault: `(100000 / 10000) * 0.03 = 0.30 USD`

**Subtotal sem IA: ~17.20 USD/mes**

## Delta de custo com rede privada (OpenAI)

Premissas de referencia:

- 1 Private Endpoint ativo 24x7
- 1 Private DNS Zone
- Trafego Private Link variavel por GB

Calculo base:

- Private Endpoint: `730 * 0.01 = 7.30 USD/mes`
- Private DNS Zone: `~0.50 USD/mes`
- Data processada no Private Link: `0.01 USD/GB` por direção

**Delta fixo aproximado: ~7.80 USD/mes** (sem considerar GB processado)

Exemplos de delta total (com dados):

1. Baixo uso (50 GB totais entrada+saida): `~8.30 USD/mes`
2. Medio uso (500 GB totais): `~12.80 USD/mes`
3. Alto uso (1 TB total): `~17.80 USD/mes`

## Como calcular a parte de IA

O custo de IA e variavel por tokens. No calculator, preencha os tokens
mensais de input e output do deployment `gpt-4o-mini`.

Formula geral:

$$
Custo\_IA\_mensal = (Tokens\_in / 1{,}000{,}000) * Preco\_in +
(Tokens\_out / 1{,}000{,}000) * Preco\_out
$$

Total mensal aproximado:

$$
Total = Subtotal\_sem\_IA + Custo\_IA\_mensal
$$

## Custo Real Observado (atualizado 2026-05-19)

Dados extraidos do Azure Cost Management (mes corrente, BRL).

### Total subscription

- **Custo acumulado no mes:** `R$ 66.58`
- **Previsao fim do mes:** `R$ 112.83`
- **Credito disponivel:** `R$ 512.07`
- **Saldo projetado:** `~R$ 399 sobra`

### Top servicos (mes corrente)

| Servico                           | BRL    |
| --------------------------------- | ------ |
| Azure App Service (B1 Linux)      | ~30.20 |
| Container Registry                | ~13.85 |
| Azure OpenAI (gpt-4o-mini)        | ~9.40  |
| Private Endpoint + Private DNS    | ~5.10  |
| Log Analytics + App Insights      | ~4.80  |
| Key Vault Standard                | ~1.50  |
| Outros (Monitor, Cosmos < R$0.01) | ~1.73  |

> Valores arredondados a partir da consulta `az consumption usage list`.
> A coluna oficial fica em USD; conversao aproximada a `R$ 5,00/USD`.

### Observacoes

- Custo real esta **dentro do baseline + delta privado** projetado acima.
- Container Registry aparece por imagens de build antigas; nao e usado em runtime (deploy atual e ZIP via azd).
- Cosmos DB esta em SKU serverless ocioso (custo < R$ 0.01/mes); pode ser removido se nao for ativado.

## Proximo passo recomendado

Salvar dois cenarios no calculator para acompanhar operacao:

1. Baseline (baixo uso): logs 1 GB/mes + IA baixa
2. Pico (campanha): logs 5-20 GB/mes + IA media/alta

## Fontes tecnicas no repositorio

- Infra Terraform: `terraform/main.tf`
- Variaveis de SKU/regiao: `terraform/variables.tf`
- Operacao e runbook: `docs/OPERATIONS.md`
