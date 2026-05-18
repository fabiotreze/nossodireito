## Security and LGPD

**Version:** 1.20.0
**Updated:** 2026-05-18

## Security Baseline

- HTTPS-only with HSTS (`strict-transport-security`)
- CSP enabled with explicit allowlist
- `x-frame-options: DENY`
- `x-content-type-options: nosniff`
- `referrer-policy` and `permissions-policy` enabled
- Rate limit for abuse protection in server runtime
- App Service ingress restricted to Cloudflare edge ranges (default deny)
- Azure OpenAI in private mode (`publicNetworkAccess=Disabled`)
- Key Vault in private mode by default (`public_network_access_enabled=false`)
- Redis in private mode (`publicNetworkAccess=Disabled`, TLS 1.2)

Run baseline check:

```bash
bash scripts/security_headers_check.sh
```

## LGPD Position

- Legal basis for AI analysis: consent (Art. 7º, I)
- Consent revocation: available in permanent UI (Art. 8º, §5)
- Data subject rights (Art. 18): documented in consent modal
- Default analysis is local; AI analysis sends anonymized text only
- Server rejects obvious PII payloads (HTTP 422)
- Retention target for AI analysis output: no prompt/content retention

```mermaid
flowchart LR
  U[Usuario] --> A[Browser anonymiza texto]
  A --> C{Consentimento IA}
  C -->|Aceita| S[/api/analyze-document]
  C -->|Recusa| L[Somente analise local]
  S --> V[Validacao anti-PII]
  V --> O[Azure OpenAI gpt-4o-mini via Private Endpoint]
  S --> K[Key Vault via MSI e DNS privado]
  S --> RD[Redis TLS 6380 via Private Endpoint]
  O --> RS[Resposta estruturada]
```

## Network Security Notes

- Dominio oficial (`nossodireito.fabiotreze.com`) permanece publico para usuarios.
- Hostname direto do App Service (`*.azurewebsites.net`) deve retornar 403.
- Tráfego App Service -> OpenAI, Key Vault e Redis ocorre por VNet + Private Endpoint + Private DNS.
- Segredo `redis-primary-key` por padrao nao e atualizado por Terraform em runners externos a VNet.

## DPO Flow

- Contact channel: `dpo@fabiotreze.com`
- Recommended response SLA: up to 15 calendar days
- Intake checklist:
  1. Request received and logged
  2. Identity and request scope confirmed
  3. Data map reviewed (local browser data vs server telemetry)
  4. Response sent with action summary

## Compliance Controls

- CI checks for tests and content quality
- GitHub security workflows (CodeQL, gitleaks, scorecard)
- Terraform validation + policy checks in pipeline
- App Insights telemetry configured with privacy-safe controls
