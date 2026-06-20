# Política de Segurança

## Versões Suportadas

| Versão | Suportada | Notas                                                                 |
|--------|-----------|-----------------------------------------------------------------------|
| 1.43.x | ✅        | Atual — IA Azure OpenAI + Managed Identity + Structured Outputs       |
| 1.42.x | ✅        | Compatível (sem mudanças de segurança bloqueantes)                    |
| < 1.42 | ❌        | Atualize — anonymizer/document-validator anteriores, sem enum no schema |

> **Ambiente:** este projeto roda em **infra de desenvolvimento/POC** (App Service B1 single region).
> Não é um ambiente de produção corporativo. Veja [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Reportando Vulnerabilidades

Se você encontrar uma vulnerabilidade de segurança neste projeto, por favor reporte de forma **responsável**:

1. **NÃO** abra uma issue pública
2. Envie um email para **38567767+fabiotreze@users.noreply.github.com** com:
   - Descrição da vulnerabilidade
   - Passos para reproduzir
   - Impacto potencial
3. Seu report será analisado assim que possível (sem SLA formal — projeto mantido individualmente)

## Práticas de Segurança

### Dados do Usuário
- **Minimização de dados** — sem cadastro, sem CPF/RG/nome obrigatório e sem perfil individual
- Todo processamento de conteúdo ocorre **localmente no navegador** do usuário
- **Nenhum cookie** de rastreamento, analytics de terceiros ou fingerprinting
- **Armazenamento local transparente:** documentos criptografados no IndexedDB expiram em 15 minutos; cache local do último resultado expira em 30 minutos.
- **Sem telemetria de aplicação:** nenhum SDK de APM/observabilidade emite envelopes a partir do servidor (Application Insights removido em 2026-06-05). Métricas operacionais usam contadores agregados em memória, Azure Monitor platform metrics (App Service), http logs do App Service (180d) e relatórios técnicos de CSP. Zero corpo de documento em logs.
- Conformidade voluntária com LGPD (Lei 13.709/2018) — Art. 4º, I (não aplicabilidade para pessoa natural sem fins econômicos)

### Criptografia
- **AES-GCM-256** via Web Crypto API para documentos no IndexedDB
- CryptoKey gerada com `extractable: false` (não-exportável)
- **TTL de 15 minutos** com auto-expiração e limpeza automática
- Blob URLs revogados automaticamente após uso

### Headers de Segurança
- `Content-Security-Policy`: `default-src 'none'` com whitelist restritiva
- `X-Content-Type-Options`: `nosniff`
- `X-Frame-Options`: `DENY`
- `Referrer-Policy`: `strict-origin-when-cross-origin`
- `Permissions-Policy`: camera, microphone, geolocation desabilitados; accelerometer/gyroscope/magnetometer permitidos para same-origin (necessário para VLibras Unity/Emscripten no Chromium)
- **SRI** (Subresource Integrity) em todos os scripts CDN

### SRI (Subresource Integrity)
- **PDF.js**: SRI hash `sha384-...` verificado em cada carregamento
- **VLibras**: Script oficial do governo (vlibras.gov.br) — sem SRI disponível (URLs não versionadas). Risco mitigado por ser CDN governamental e CSP restritivo.

### Trade-off CSP: `unsafe-eval` para VLibras (decisão documentada)

O VLibras (widget oficial do governo brasileiro para tradução em Libras) é construído
com **Unity WebGL**, que internamente usa `eval()` para compilação de WebAssembly.
Sem `'unsafe-eval'` no CSP, o VLibras não carrega e o avatar de Libras não aparece.

**Decisão:** Priorizamos acessibilidade governamental (LBI Art. 63) sobre CSP restritivo.

- `'unsafe-eval'` — necessário para Unity WebGL (VLibras)
- `'wasm-unsafe-eval'` — Chrome 95+ permite .wasm sem `unsafe-eval` (fallback progressivo)

**Mitigações aplicadas para compensar:**
- `script-src` restringe origens a domínios confiáveis (`'self'`, `cdnjs.cloudflare.com`, `vlibras.gov.br`, `cdn.jsdelivr.net`)
- Rate limiting (120 req/min), HSTS preload, host validation (exact match)
- `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, SRI em CDNs
- Nenhum dado do usuário é transmitido — processamento 100% local

**Referências:** [ARCHITECTURE.md](docs/ARCHITECTURE.md), [server.js](server.js)

### Infraestrutura
- Azure App Service com **HTTPS Only** enforced
- Certificado PFX próprio via **Azure Key Vault** (BYOC, SNI SSL)
- **FTPS desabilitado**, SCM basic auth desabilitado
- **Managed Identity** para acesso ao Key Vault (sem credenciais em código)
- Secrets gerenciados via **GitHub Secrets** (ARM_*, PFX_BASE64)

### Segredos: por que o PFX_PASSWORD vive no GitHub e não no Key Vault

O `PFX_PASSWORD` permanece em GitHub Secret (não no Key Vault) por uma razão circular: ele é usado **uma única vez** durante `terraform apply` para importar o `.pfx` dentro do próprio Key Vault. Mover a senha para o KV antes do KV existir é um problema do tipo chicken-and-egg. Após o import, o certificado vive no KV com HSM e o App Service o consome via Managed Identity — a senha original deixa de ser necessária em runtime.

### CI/CD
- **Quality Gate** automatizado (score mínimo 75/100) bloqueia deploys inseguros
- Scan de dados sensíveis em cada push (*.pfx, *.pem, *.key, *.env)
- `.gitignore` cobre certificados, chaves, tfvars, tfstate
- Terraform state **nunca commitado** — persistido via GitHub Artifacts

## Dependências

| Dependência | Uso | Escopo |
|---|---|---|
| pdf.js (CDN) | Análise de PDFs | Client-side, com SRI |

Nenhuma outra dependência externa é utilizada no frontend.
