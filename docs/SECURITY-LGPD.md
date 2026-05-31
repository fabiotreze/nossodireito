# Segurança e LGPD

**Versão:** 1.37.0
**Atualizado:** 2026-05-31

## Baseline de Segurança

- HTTPS-only com HSTS (`strict-transport-security`)
- CSP habilitado com allowlist explícita
- `x-frame-options: DENY`
- `x-content-type-options: nosniff`
- `referrer-policy` e `permissions-policy` habilitados
- Rate limit para proteção contra abuso no runtime do servidor
- Ingresso do App Service restrito às faixas de IP da edge da Cloudflare (deny por padrão)
- Azure OpenAI em modo privado (`publicNetworkAccess=Disabled`)
- Key Vault em modo privado por padrão (`public_network_access_enabled=false`)
- Redis em modo privado (`publicNetworkAccess=Disabled`, TLS 1.2)

Executar verificação de baseline:

```bash
bash scripts/security_headers_check.sh
```

## Posicionamento LGPD

- Base legal para análise por IA: consentimento (Art. 7º, I)
- Revogação de consentimento: disponível em UI permanente (Art. 8º, §5)
- Direitos do titular (Art. 18): documentados no modal de consentimento
- Análise padrão é local; análise por IA envia apenas texto anonimizado
- Servidor rejeita payloads com PII evidente (HTTP 422)
- Meta de retenção para saída da análise por IA: zero retenção de prompt/conteúdo

> Checklist auditável recorrente: [LGPD-COMPLIANCE.md](LGPD-COMPLIANCE.md)

```mermaid
flowchart LR
  U[Usuario] --> A[Browser anonymiza texto]
  A --> C{Consentimento IA}
  C -->|Aceita| S["/api/analyze-document"]
  C -->|Recusa| L[Somente analise local]
  S --> V[Validacao anti-PII]
  V --> O[Azure OpenAI gpt-4o-mini via Private Endpoint]
  S --> K[Key Vault via MSI e DNS privado]
  S --> RD[Redis TLS 6380 via Private Endpoint]
  O --> RS[Resposta estruturada]
```

## Notas de Segurança de Rede

- Domínio oficial (`nossodireito.fabiotreze.com`) permanece público para os usuários.
- Hostname direto do App Service (`*.azurewebsites.net`) deve retornar 403.
- Tráfego App Service -> OpenAI, Key Vault e Redis ocorre por VNet + Private Endpoint + Private DNS.
- Segredo `redis-primary-key` por padrão não é atualizado pelo Terraform em runners externos à VNet.

## Fluxo do DPO

- Canal de contato: `dpo@fabiotreze.com`
- SLA recomendado de resposta: até 15 dias corridos
- Checklist de entrada:
  1. Solicitação recebida e registrada
  2. Identidade e escopo da solicitação confirmados
  3. Mapa de dados revisado (dados locais no navegador vs telemetria do servidor)
  4. Resposta enviada com resumo das ações

## Controles de Conformidade

- Checagens de CI para testes e qualidade de conteúdo
- Workflows de segurança do GitHub (CodeQL, gitleaks)
- Validação do Terraform + checagens de policy no pipeline
- Telemetria do App Insights configurada com controles que preservam privacidade

## Marco Civil da Internet (Lei 12.965/2014)

- **Art. 15:** Retenção de registros de acesso a aplicações por 6 meses em
  ambiente controlado e seguro (cumprido via App Insights com IP anonimizado;
  retenção configurada para 30 dias — inferior ao mínimo legal; ajustar se
  ordem judicial exigir preservação específica).
- **Art. 7º, VII:** Não fornecimento a terceiros de registros de conexão e
  acesso sem consentimento livre, expresso e informado ou determinação judicial.

## Referências normativas ANPD

| Resolução | Assunto | Impacto no portal |
|-----------|---------|-------------------|
| Res. CD/ANPD nº 2/2022 | Agentes de tratamento de pequeno porte | Portal NÃO se enquadra (dados sensíveis, IA, idosos, crianças) |
| Res. CD/ANPD nº 4/2023 | RIPD | [docs/RIPD.md](RIPD.md) |
| Res. CD/ANPD nº 15/2024 | Comunicação de incidentes | [RUNBOOK-INCIDENTE-LGPD.md](RUNBOOK-INCIDENTE-LGPD.md) |
| Res. CD/ANPD nº 18/2024 | Encarregado (DPO) | [docs/ENCARREGADO.md](ENCARREGADO.md) |
