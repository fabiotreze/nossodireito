# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.3.1] - 2025-07-15

### Adicionado
- **Quality Gate v2.0** — Pipeline completa de qualidade pré-deploy com 17 categorias
- Novas verificações: Dados Sensíveis, Higiene de Arquivos, Documentação, Disclaimer/Regulatório, WAF 5 Pilares
- Modo CI no codereview.py (`--ci`, `--min-score`) com exit code para pipelines
- Workflow `quality-gate.yml` — executa automaticamente em push/PR
- Deploy bloqueado se Quality Gate falhar (`needs: quality-gate` no deploy.yml)
- Scan automático de segredos (chaves, tokens, certificados) em arquivos rastreados
- Avaliação WAF dos 5 pilares: Segurança, Confiabilidade, Performance, Custos, Excelência Operacional
- Verificação de .gitignore para padrões sensíveis (*.pfx, *.pem, *.env, *.tfvars, *.tfstate)
- CHANGELOG.md (este arquivo)

### Alterado
- codereview.py atualizado de v1.0.0 para v2.0.0 (Quality Gate)
- deploy.yml agora depende do job quality-gate (deploy só ocorre se score >= 75)
- Cabeçalho do relatório atualizado para "Quality Gate"

## [1.3.0] - 2025-02-09

### Adicionado
- Categoria **moradia** (Minha Casa Minha Vida, adaptações, FGTS habitação)
- `renderLinksUteis()` — links dinâmicos a partir do JSON
- `renderHeroStats()` — contagem automática de categorias e fontes
- `checkStaleness()` — banner de conteúdo desatualizado (30 dias)
- CSS para banner de staleness com dark mode
- GOVERNANCE.md — critérios para fontes, categorias, revisão semanal
- Workflow `weekly-review.yml` — issue automática toda segunda-feira
- codereview.py v1.0.0 — 11 categorias de verificação, score 98.5/100
- SECURITY_AUDIT.md — documentação de auditoria de segurança

### Alterado
- Schema: 9 categorias, 20 fontes, 13 documentos_mestre, 12 instituições
- Hero stats dinâmicos (não mais hardcoded)
- Links úteis dinâmicos a partir do JSON

## [1.2.0] - 2025-02-01

### Adicionado
- Criptografia AES-GCM-256 via Web Crypto API para documentos no IndexedDB
- TTL de 15 minutos com auto-expiração e limpeza automática
- Revogação de Blob URLs com timeout de 15 segundos
- Content Security Policy (CSP) restritivo com `default-src 'none'`
- Subresource Integrity (SRI) sha384 em scripts CDN (pdf.js)
- Security headers: X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- `staticwebapp.config.json` com headers de segurança e regras de cache

### Alterado
- CryptoKey gerada com `extractable: false` (não-exportável)
- Documentos analisados são limpos automaticamente após TTL

## [1.1.0] - 2025-01-20

### Adicionado
- Upload e análise de documentos (PDF, imagens via pdf.js + Tesseract OCR)
- Checklist mestre de documentos por categoria
- Busca inteligente com KEYWORD_MAP
- Seção de instituições de apoio (governamentais, ONGs, profissionais)
- Seção de transparência com fontes e datas de consulta
- Dark mode automático (prefers-color-scheme)
- Suporte a impressão (CSS @media print)
- Navegação por teclado com tabindex e :focus-visible
- aria-live para conteúdo dinâmico

## [1.0.0] - 2025-01-10

### Adicionado
- Portal NossoDireito — consulta de direitos PcD
- 8 categorias iniciais: BPC, CIPTEA, Educação, Plano de Saúde, SUS/Terapias, Transporte, Trabalho, FGTS
- Base de dados JSON com legislação brasileira
- Interface responsiva com design tokens CSS
- Modal de disclaimer legal
- Seção de links úteis
- README.md com documentação do projeto
