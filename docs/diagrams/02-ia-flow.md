# Fluxo de IA Atual

**Versão:** 1.43.48
**Atualizado:** 2026-06-07

Sequência canônica de uma análise de documento via IA, com consentimento explícito (LGPD Art. 7º, I) e anonimização antes de qualquer chamada ao provedor externo.

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuário (browser)
    participant FE as Frontend (js/app.js)
    participant CF as Cloudflare (edge)
    participant APP as App Service (server.js)
    participant ANON as Anonimizador (services/ai-analysis.js)
    participant PE as Private Endpoint (snet-openai-pe-prod)
    participant OAI as Azure OpenAI (gpt-4o-mini)

    U->>FE: Seleciona arquivo (PDF/imagem/texto)
    FE->>FE: OCR/parse local (PDF.js / Tesseract.js)
    FE->>FE: Gate clínico (shared/document-validator.js)
    Note right of FE: Score ≥ 5 + sinal forte<br/>(CRM/CRP/COFFITO/... ou CID-10)<br/>senão rejeita sem chamada
    FE->>U: Modal de consentimento (#aiConsentModal)
    U->>FE: Aceita (opt-in granular, 30 dias)
    FE->>CF: POST /api/analyze-document
    CF->>APP: HTTPS 443 (allowlist IPs CF)
    APP->>APP: Rate-limit adaptativo (Redis ou in-memory)
    APP->>ANON: Texto bruto
    ANON->>ANON: Anonimização<br/>(CPF, RG, CEP, telefone, nome próprio)
    ANON->>PE: HTTPS via Private Endpoint
    PE->>OAI: Inferência (modo privado, sem internet)
    OAI-->>PE: Resposta estruturada (JSON Schema)
    PE-->>ANON: Resposta
    ANON-->>APP: Sumário + categorias + justificativa literal
    APP-->>CF: 200 JSON
    CF-->>FE: 200 JSON
    FE->>FE: Render mini-cards + banner "🤖 Conteúdo gerado por IA"
    FE->>U: Resultado + botão "Abrir passo a passo"
    Note over U,FE: Zero persistência server-side.<br/>Consentimento revogável em<br/>/historico-aceite.html.
```

## Garantias

- **Anonimização obrigatória** antes do envio ao OpenAI (LGPD Art. 6º).
- **Private Endpoint** — tráfego ao Azure OpenAI não sai da VNet.
- **Circuit breaker** em `lib/ai-analyze.js` (timeout 8s, 1 retry).
- **Banner persistente** "🤖 Conteúdo gerado por IA (Azure OpenAI gpt-4o-mini, Brasil Sul)" no resultado (MS Learn AI Principles: Transparency + Validation).
- **Revogação** em `/historico-aceite.html` (apaga `nd_ai_consent_v2` do localStorage).

## Referências

- Código: [services/ai-analysis.js](../../services/ai-analysis.js), [lib/ai-analyze.js](../../lib/ai-analyze.js), [shared/document-validator.js](../../shared/document-validator.js)
- Infra: [terraform/ai-openai.tf](../../terraform/ai-openai.tf), [terraform/openai-private-network.tf](../../terraform/openai-private-network.tf)
- Política: [AI-PRINCIPLES.md](../AI-PRINCIPLES.md), [RIPD.md](../RIPD.md), [REVISAO-HUMANA-IA.md](../REVISAO-HUMANA-IA.md)
