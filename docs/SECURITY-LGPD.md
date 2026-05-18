## Security and LGPD

**Version:** 1.19.0
**Updated:** 2026-05-18

## Security Baseline

- HTTPS-only with HSTS (`strict-transport-security`)
- CSP enabled with explicit allowlist
- `x-frame-options: DENY`
- `x-content-type-options: nosniff`
- `referrer-policy` and `permissions-policy` enabled
- Rate limit for abuse protection in server runtime

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
  V --> O[Azure OpenAI gpt-4o-mini]
  O --> R[Resposta estruturada]
```

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
