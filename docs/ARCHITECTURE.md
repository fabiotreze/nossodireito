# Arquitetura Atual — NossoDireito

Versao: 1.19.0  
Atualizado em: 2026-05-18

## Visao Geral

A plataforma roda em Azure App Service Linux (Node.js 22) com entrega via dominio customizado em Cloudflare. O backend expoe conteudo estatico e a API de analise por IA com opt-in explicito, usando Azure OpenAI.

## Topologia de Execucao

- Borda: Cloudflare (DNS, CDN, WAF, TLS)
- Aplicacao: Azure App Service (`app-nossodireito-br`)
- Runtime: Node.js 22 LTS
- Regiao: Brazil South (`brazilsouth`)
- Observabilidade: Application Insights + Log Analytics
- Segredos: Azure Key Vault + Managed Identity
- CI/CD: GitHub Actions com OIDC

## Fluxo de Requisicao

1. Usuario acessa `https://nossodireito.fabiotreze.com`.
2. Cloudflare aplica protecao de borda e encaminha para App Service.
3. O App Service entrega UI/PWA e ativos versionados.
4. Em analise por IA, o frontend exige consentimento explicito.
5. O backend anonimiza o texto e chama Azure OpenAI.
6. A resposta volta para o cliente sem persistencia de dados pessoais no servidor.

## API e Endpoints

- `GET /` -> aplicacao web
- `GET /health` -> health check da aplicacao
- `POST /api/analyze-document` -> analise de texto com IA (opt-in)
- `GET /data/*.json` -> base de direitos e mecanismos de busca

## Privacidade e LGPD

- Coleta de dados pessoais: nao
- Consentimento para IA: obrigatorio, especifico e revogavel
- Revogacao de consentimento: disponivel permanentemente na interface
- Base legal da analise de IA: consentimento (LGPD Art. 7o, I)
- Tratamento: anonimizado antes de envio ao provedor de IA

## Seguranca Aplicada

- HTTPS obrigatorio
- Security headers no servidor (CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy)
- Rate limiting para endpoint de IA
- Managed Identity para acesso a recursos Azure
- Sem secrets de producao hardcoded no codigo

## Diagramas

- Arquitetura E2E: [ARCHITECTURE.drawio](ARCHITECTURE.drawio)
- Fluxo de IA: [diagrams/02-ia-flow.drawio](diagrams/02-ia-flow.drawio)
- Replicacao: [diagrams/03-replication.drawio](diagrams/03-replication.drawio)

## Referencias Operacionais

- Operacao e runbook: [OPERATIONS.md](OPERATIONS.md)
- Seguranca e LGPD: [SECURITY-LGPD.md](SECURITY-LGPD.md)
- Replicacao: [REPLICATION.md](REPLICATION.md)
