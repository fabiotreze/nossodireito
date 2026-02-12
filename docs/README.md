# Estrutura da Documentação — Padrão de Versionamento

**Versão:** 1.0.0  
**Data:** 11 de fevereiro de 2026  
**Objetivo:** Documentar padrão de organização e nomenclatura de arquivos

---

## 📁 Estrutura de Pastas

```
docs/
├── v1/                              # Documentação da versão atual (V1)
│   ├── ARCHITECTURE.md              # Arquitetura completa do sistema V1
│   ├── DIAGRAMS.md                  # Diagramas Mermaid (7 diagramas)
│   ├── LEGAL_COMPLIANCE.md          # Conformidade LGPD + regulatória
│   └── VLIBRAS_LIMITATIONS.md       # Limitações conhecidas do VLibras
│
├── v2/                              # Planejamento da versão futura (V2)
│   └── roadmap/
│       ├── ROADMAP_V2.md            # Roadmap completo V2
│       ├── TECHNICAL_SPECIFICATIONS.md  # Especificações técnicas
│       └── DEPLOYMENT_STRATEGY.md       # Estratégia de deployment
│
├── COMPLIANCE.md                   # 📊 Documento único de compliance (ISO 27001 + SOC 2)
├── DEPENDENCY_CONTROL.md           # 🔄 Mapa de dependências e procedimentos
├── CHECKLIST_VALIDATIONS.md       # ✅ Validações oficiais do checklist
├── SITE_ORDERING_CRITERIA.md      # 🎨 Critérios de ordenação UX/IA
├── BENEFICIOS_COMPLETOS_PCD.md    # 📚 Pesquisa de 30+ benefícios
└── README.md                        # Este arquivo (índice da documentação)
```

---

## 📝 Padrão de Nomenclatura

### Arquivos de Documentação

**Formato:** `CATEGORIA_NOME.md` (UPPERCASE com underscores)

**Categorias:**
- `ARCHITECTURE` — Arquitetura técnica do sistema
- `DIAGRAMS` — Diagramas visuais (Mermaid, C4, etc)
- `LEGAL` — Documentação legal/regulatória
- `ROADMAP` — Planejamento de versões futuras
- `VALIDATIONS` — Validações de requisitos com fontes oficiais
- `API` — Documentação de APIs (V2)

**Exemplos:**
- ✅ `ARCHITECTURE.md`
- ✅ `LEGAL_COMPLIANCE.md`
- ✅ `CHECKLIST_VALIDATIONS.md`
- ❌ `architecture-v1.md` (evitar lowercase com hífens)
- ❌ `Documentação da Arquitetura.md` (evitar espaços e acentos)

### Controle de Versão em Nomes

**Para documentos versionados:**
- Usar **pastas** para separar versões: `v1/`, `v2/`, `v3/`
- **Não incluir** versão no nome do arquivo dentro da pasta versionada

**Certo:**
```
docs/v1/ARCHITECTURE.md
docs/v2/ARCHITECTURE.md
```

**Errado:**
```
docs/ARCHITECTURE_V1.md
docs/ARCHITECTURE_V2.md
```

**Razão:** Facilita comparações com `diff v1/ARCHITECTURE.md v2/ARCHITECTURE.md`

---

## 🗂️ Organização por Versão

### 📊 COMPLIANCE.md — Documento Único de Compliance

**Padrão:** ISO 27001 + SOC 2 + LGPD + LBI  
**Objetivo:** Consolidar TODAS as informações de compliance em um único arquivo auditável

**Estrutura (9 seções):**
1. **§1 LEGAL** — LGPD, LBI, Propriedade Intelectual, Responsabilidade Civil
2. **§2 SEGURANÇA** — Criptografia, HTTPS/TLS, CSP, Azure Compliance
3. **§3 PRIVACIDADE** — Zero-Data Architecture, Anonimização, Direitos dos Titulares
4. **§4 ACESSIBILIDADE** — WCAG 2.1 AA, VLibras, eMAG
5. **§5 QUALIDADE** — Validação de Fontes, Links, Dependências
6. **§6 AUDITORIA** — Histórico, Métricas, Evidências
7. **§7 CERTIFICAÇÕES** — Azure ISO 27001, SOC 2
8. **§8 RISCOS** — Matriz de riscos e mitigação
9. **§9 RECOMENDAÇÕES** — Curto, médio e longo prazo

**Por que arquivo único?**
- ✅ **Auditável** — Empresas de auditoria (Big 4) inspecionam 1 arquivo
- ✅ **Rastreável** — Git diff mostra todas as mudanças de compliance
- ✅ **Versionável** — Cada versão do site tem snapshot de compliance
- ✅ **Automatizável** — Tools como Vanta/Drata escaneiam 1 arquivo
- ✅ **Compliance-as-Code** — CI/CD valida contra checklist

**Documentos consolidados:**
- ❌ ~~QUALITY_AUDIT_SUMMARY.md~~ (informações em §6)
- ❌ ~~LINKS_VALIDATION_REPORT.md~~ (métricas em §5.2 e §6.2)
- ✅ Referencia v1/LEGAL_COMPLIANCE.md (detalhamento completo de 866 linhas)
- ✅ Referencia CHECKLIST_VALIDATIONS.md (validação legal ativa)
- ✅ Referencia DEPENDENCY_CONTROL.md (procedimentos)

---

### V1 — Sistema Atual em Produção

**Pasta:** `docs/v1/`

**Documentos obrigatórios:**
1. **ARCHITECTURE.md** — Arquitetura completa (15 seções)
   - Executive Summary
   - Tech Stack
   - Infrastructure (Azure)
   - Security & EASM
   - LGPD Compliance
   - Accessibility (WCAG 2.1 AA)
   - Performance
   - CI/CD
   - Monitoring
   - Cost Analysis
   - Limitations
   - DNS & CDN
   - Disaster Recovery

2. **DIAGRAMS.md** — Diagramas Mermaid
   - General Architecture
   - Data Flow (sequence)
   - Infrastructure (Terraform)
   - Client-side modules
   - Security layers
   - CI/CD pipeline
   - LGPD data flow

3. **LEGAL_COMPLIANCE.md** — Conformidade regulatória
   - LGPD Art. 4º I compliance
   - LBI (Acessibilidade)
   - Copyright & licensing
   - Civil liability
   - Azure regulations
   - Global compliance (GDPR, CCPA, PIPEDA)
   - Government data sources
   - eMAG/WCAG
   - INPI software registration
   - Risk matrix

4. **VLIBRAS_LIMITATIONS.md** — Limitações conhecidas do VLibras Widget

### V2 — Planejamento Futuro

**Pasta:** `docs/v2/roadmap/`

**Documentos planejados:**
1. **ROADMAP_V2.md** — Visão geral do roadmap
2. **TECHNICAL_SPECIFICATIONS.md** — Especificações técnicas detalhadas
3. **DEPLOYMENT_STRATEGY.md** — Estratégia de deployment
4. **API_DESIGN.md** (futuro) — Design da API RESTful
5. **DATABASE_SCHEMA.md** (futuro) — Schema do banco de dados

---

## 🔄 Backup e Versionamento

### Backup Automático

**Comando:**
```bash
rsync -av --exclude='docs/roadmap' --exclude='backup' --exclude='.git' --exclude='node_modules' . backup/
```

**Quando executar:**
- Antes de grandes mudanças no código
- Antes de migração V1 → V2
- Periodicamente (semanal/mensal)

### Git Commits

**Padrão de mensagem:**
```
tipo(escopo): descrição curta

Descrição detalhada (opcional)

Ref: #issue-number
```

**Tipos:**
- `feat:` — Nova funcionalidade
- `fix:` — Correção de bug
- `docs:` — Alteração em documentação
- `style:` — Formatação (não afeta código)
- `refactor:` — Refatoração de código
- `perf:` — Melhoria de performance
- `test:` — Adição/correção de testes
- `chore:` — Tarefas de manutenção

**Exemplos:**
```
docs(v1): adicionar validações de checklist com fontes oficiais

feat(checklist): adicionar validação automática de dependências BPC→CadÚnico

fix(vlibras): corrigir loading do widget em navegadores Safari
```

---

## 📊 Métricas de Documentação

### Cobertura Atual

| Área | Documentado? | Arquivo |
|------|--------------|---------|
| Arquitetura V1 | ✅ | v1/ARCHITECTURE.md |
| Diagramas V1 | ✅ | v1/DIAGRAMS.md |
| Compliance legal | ✅ | v1/LEGAL_COMPLIANCE.md (detalhado) |
| **Compliance único** | ✅ | **COMPLIANCE.md** (ISO 27001 + SOC 2) |
| Dependências | ✅ | DEPENDENCY_CONTROL.md |
| Validações checklist | ✅ | CHECKLIST_VALIDATIONS.md |
| Critérios UX | ✅ | SITE_ORDERING_CRITERIA.md |
| Pesquisa benefícios | ✅ | BENEFICIOS_COMPLETOS_PCD.md |
| Limitações VLibras | ✅ | v1/VLIBRAS_LIMITATIONS.md |
| Roadmap V2 | ⚠️ | v2/roadmap/ROADMAP_V2.md (simplificar) |
| API V2 | ❌ | Pendente |
| Database V2 | ❌ | Pendente |
| Tests V2 | ❌ | Pendente |

### Tamanho Estimado

- **V1 total:** ~60.000 palavras
  - ARCHITECTURE.md: ~25.000 palavras
  - DIAGRAMS.md: ~8.000 palavras (+ 7 diagramas)
  - LEGAL_COMPLIANCE.md: ~12.000 palavras
  - **COMPLIANCE.md: ~8.000 palavras (novo)**
  - DEPENDENCY_CONTROL.md: ~4.000 palavras
  - CHECKLIST_VALIDATIONS.md: ~3.000 palavras
  - VLIBRAS_LIMITATIONS.md: ~500 palavras

- **Validações:** ~3.500 palavras

---

## 🎯 Próximos Passos

### Curto Prazo (Sprint atual)

1. ✅ Criar CHECKLIST_VALIDATIONS.md
2. ✅ Reorganizar estrutura v1/ e v2/
3. ⏳ Simplificar ROADMAP_V2.md
4. ⏳ Adicionar links de validação no FAQ do site

### Médio Prazo (Próximo mês)

1. Criar API_DESIGN.md (quando iniciar V2)
2. Criar DATABASE_SCHEMA.md (quando iniciar V2)
3. Documentar testes automatizados
4. Adicionar CONTRIBUTING.md para colaboradores

---

## 📚 Referências

- **Conventional Commits:** https://www.conventionalcommits.org/
- **Semantic Versioning:** https://semver.org/
- **C4 Model (Diagramas):** https://c4model.com/
- **Mermaid Diagrams:** https://mermaid.js.org/

---

**Última atualização:** 11 de fevereiro de 2026  
**Responsável:** Equipe NossoDireito
