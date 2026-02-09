# Security Policy

## Versões Suportadas

| Versão | Suportada |
|--------|-----------|
| 1.0.x  | ✅        |

## Reportando Vulnerabilidades

Se você encontrar uma vulnerabilidade de segurança neste projeto, por favor reporte de forma **responsável**:

1. **NÃO** abra uma issue pública
2. Envie um email para **security@fabiotreze.com** com:
   - Descrição da vulnerabilidade
   - Passos para reproduzir
   - Impacto potencial
3. Você receberá uma resposta em até **48 horas**

## Práticas de Segurança

### Dados do Usuário
- **Zero coleta de dados pessoais** — nenhuma informação é enviada a servidores
- Todo processamento ocorre **localmente no navegador** do usuário
- **Nenhum cookie** de rastreamento, analytics ou fingerprinting
- Conformidade com LGPD Art. 4º, I

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
- `Permissions-Policy`: camera, microphone, geolocation desabilitados
- **SRI** (Subresource Integrity) em todos os scripts CDN

### Infraestrutura
- Azure App Service com **HTTPS Only** enforced
- Certificado PFX próprio via **Azure Key Vault** (BYOC, SNI SSL)
- **FTPS desabilitado**, SCM basic auth desabilitado
- **Managed Identity** para acesso ao Key Vault (sem credenciais em código)
- Secrets gerenciados via **GitHub Secrets** (ARM_*, PFX_BASE64)

### CI/CD
- **Quality Gate** automatizado (score mínimo 75/100) bloqueia deploys inseguros
- Scan de dados sensíveis em cada push (*.pfx, *.pem, *.key, *.env)
- `.gitignore` cobre certificados, chaves, tfvars, tfstate
- Terraform state **nunca commitado** — persistido via GitHub Artifacts

## Dependências

| Dependência | Uso | Escopo |
|---|---|---|
| pdf.js (CDN) | Análise de PDFs | Client-side, com SRI |
| applicationinsights | Telemetria server-side | Server-side apenas |

Nenhuma outra dependência externa é utilizada no frontend.
