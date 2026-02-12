# Controle Central de Dependências — Nosso Direito PcD

**Documento:** Mapa de dependências e procedimentos de atualização  
**Objetivo:** Garantir que **TODAS** as informações relacionadas sejam atualizadas consistentemente  
**Problema resolvido:** "sempre que peço para atualizar tenho que ficar pedindo para procurar todos os arquivos relacionados e sempre esquece de algum"  
**Data de criação:** 11 de fevereiro de 2026  
**Versão:** 1.0.0

---

## 📊 Mapa Visual de Dependências

```
direitos.json (SOURCE OF TRUTH)
    ├── Versão + data atualização
    │   ├── app.js (renderiza versão no rodapé e transparência)
    │   ├── index.html (exibe na seção transparência)
    │   ├── scripts/bump_version.py (incrementa versão)
    │   └── sw.js (versão do cache)
    │
    ├── categorias[] (benefícios por categoria)
    │   ├── app.js (renderCategories() linha 905-928 - renderiza cards)
    │   ├── index.html (grid de categorias)
    │   ├── CHECKLIST_VALIDATIONS.md (validação legal de cada benefício)
    │   └── BENEFICIOS_COMPLETOS_PCD.md (documentação expandida)
    │
    └── fontes[] (legislação consultada)
        ├── app.js (renderTransparency() linha 1240+ - renderiza listas)
        ├── index.html (seção Transparência)
        └── CHECKLIST_VALIDATIONS.md (citações legais)

index.html
    ├── Seção Transparência (linhas 480-540)
    │   ├── direitos.json (fonte de dados)
    │   ├── app.js (popula dinamicamente)
    │   └── DEPENDENCY_CONTROL.md (este documento)
    │
    ├── Disclaimer/Avisos
    │   └── [PENDENTE] Reforçar LGPD + aviso profissional
    │
    └── Navegação (linhas 176-190)
        └── SITE_ORDERING_CRITERIA.md (documentação da ordem)

app.js
    ├── loadDireitos() linha 850 (fetch direitos.json)
    ├── renderCategories() linha 905-928 (renderiza categorias)
    ├── renderTransparency() linha 1240+ (renderiza fontes)
    └── jsonMeta (armazena versão, ultima_atualizacao, etc)

CHECKLIST_VALIDATIONS.md
    ├── direitos.json (cada benefício tem entrada aqui)
    ├── Leis citadas em fontes[]
    └── BENEFICIOS_COMPLETOS_PCD.md (fonte de novos benefícios)

BENEFICIOS_COMPLETOS_PCD.md
    ├── 30+ benefícios documentados
    ├── [PENDENTE] Integrar em direitos.json
    └── [PENDENTE] Sincronizar com CHECKLIST_VALIDATIONS.md
```

---

## 🔄 Procedimentos de Atualização por Tipo de Mudança

### 1️⃣ ADICIONAR NOVO BENEFÍCIO

**Checklist de arquivos a atualizar:**

| # | Arquivo | Campo/Seção | Ação |
|---|---------|-------------|------|
| 1 | `data/direitos.json` | `categorias[]` | Adicionar novo objeto com: `categoria`, `titulo`, `descricao`, `forma_acesso`, `prazo_resposta`, `requisitos[]`, `documentos[]`, `links_oficiais[]`, `tags[]` |
| 2 | `data/direitos.json` | `fontes[]` | Adicionar lei/fonte oficial (se nova) com: `nome`, `tipo`, `url`, `orgao`, `consultado_em`, `artigos_referenciados[]` |
| 3 | `data/direitos.json` | `versao` | Incrementar versão (ex: 1.3.0 → 1.4.0) |
| 4 | `data/direitos.json` | `ultima_atualizacao` | Atualizar para data atual (YYYY-MM-DD) |
| 5 | `data/direitos.json` | `proxima_revisao` | Atualizar para +7 dias |
| 6 | `docs/CHECKLIST_VALIDATIONS.md` | Seção do benefício | Adicionar entrada com: `Nome do benefício`, `Base Legal`, `Requisitos`, `% Desconto (se aplicável)`, `PcD Específico?` |
| 7 | `docs/BENEFICIOS_COMPLETOS_PCD.md` | Categoria correspondente | Adicionar ou atualizar seção com: `📜 Base Legal`, `✅ O que é`, `👥 Quem tem direito`, `📝 Requisitos`, `🔗 Links oficiais` |
| 8 | `package.json` | `version` | Incrementar versão (se necessário) |
| 9 | `CHANGELOG.md` | Seção [Unreleased] | Adicionar item em `Added` |
| 10 | **TESTAR** | `index.html` | Abrir no navegador e verificar renderização |
| 11 | **VALIDAR** | `direitos.json` | Executar `node -e "JSON.parse(require('fs').readFileSync('data/direitos.json'))"` |

**Script auxiliar:**
```bash
python scripts/bump_version.py patch
```

---

### 2️⃣ ATUALIZAR BENEFÍCIO EXISTENTE

**Cenário:** Lei mudou, requisitos alterados, link quebrado, etc.

| # | Arquivo | Campo/Seção | Ação |
|---|---------|-------------|------|
| 1 | `data/direitos.json` | Objeto do benefício em `categorias[]` | Atualizar campos: `descricao`, `requisitos[]`, `documentos[]`, `links_oficiais[]`, conforme mudança |
| 2 | `data/direitos.json` | `fontes[]` | Atualizar `consultado_em` da lei alterada |
| 3 | `data/direitos.json` | `ultima_atualizacao` | Atualizar para data atual |
| 4 | `data/direitos.json` | `versao` | Incrementar versão patch (ex: 1.3.0 → 1.3.1) |
| 5 | `docs/CHECKLIST_VALIDATIONS.md` | Entrada do benefício | Atualizar informações alteradas |
| 6 | `docs/BENEFICIOS_COMPLETOS_PCD.md` | Seção do benefício | Atualizar conforme mudança |
| 7 | `CHANGELOG.md` | Seção [Unreleased] | Adicionar item em `Changed` ou `Fixed` |
| 8 | **TESTAR** | `index.html` | Verificar mudança refletida no site |

---

### 3️⃣ ADICIONAR/ATUALIZAR FONTE LEGAL (Legislação)

**Cenário:** Nova lei referenciada, link de lei corrigido, artigos adicionados

| # | Arquivo | Campo/Seção | Ação |
|---|---------|-------------|------|
| 1 | `data/direitos.json` | `fontes[]` | Adicionar/atualizar objeto com: `nome`, `tipo`, `url`, `orgao`, `consultado_em`, `artigos_referenciados[]` |
| 2 | `data/direitos.json` | `ultima_atualizacao` | Atualizar data |
| 3 | `docs/CHECKLIST_VALIDATIONS.md` | Seção correspondente | Adicionar citação legal e link |
| 4 | `docs/BENEFICIOS_COMPLETOS_PCD.md` | Base Legal do benefício | Adicionar/atualizar referência (`📜 Base Legal`) |
| 5 | `index.html` (se manual) | Seção Transparência | Verificar se renderização automática está funcionando |
| 6 | **VALIDAR** | Link gov.br | Acessar URL e confirmar que não retorna 404 |

---

### 4️⃣ ATUALIZAR VERSÃO (Processo Completo)

**Quando:** Antes de commit com mudanças significativas

| # | Arquivo | Campo/Seção | Ação |
|---|---------|-------------|------|
| 1 | `data/direitos.json` | `versao` | Incrementar (major.minor.patch) |
| 2 | `data/direitos.json` | `ultima_atualizacao` | Data atual (YYYY-MM-DD) |
| 3 | `data/direitos.json` | `proxima_revisao` | Atual + 7 dias |
| 4 | `package.json` | `version` | Sincronizar com direitos.json |
| 5 | `CHANGELOG.md` | Seção [Unreleased] → [vX.Y.Z] | Converter unreleased em versão datada |
| 6 | `docs/DEPENDENCY_CONTROL.md` | (este arquivo) | Atualizar "Última auditoria" abaixo |
| 7 | **EXECUTAR** | Script | `python scripts/bump_version.py [major|minor|patch]` |
| 8 | **TESTAR** | Site completo | Verificar todas as funcionalidades |

**Tipos de incremento:**
- **MAJOR** (1.0.0 → 2.0.0): Mudanças estruturais, breaking changes
- **MINOR** (1.3.0 → 1.4.0): Novos benefícios, funcionalidades
- **PATCH** (1.3.0 → 1.3.1): Correções, atualizações de links

---

### 5️⃣ ATUALIZAR DISCLAIMER/LGPD/AVISOS

**Cenário:** Melhorar aviso sobre não substituir profissionais, LGPD, privacidade

| # | Arquivo | Campo/Seção | Ação |
|---|---------|-------------|------|
| 1 | `index.html` | Seção Transparência (linhas 490-540) | Adicionar/atualizar box de disclaimer |
| 2 | `index.html` | Footer (linhas 540+) | Adicionar links: Privacidade, LGPD, Termos |
| 3 | `README.md` | Seção "Avisos Legais" | Sincronizar com index.html |
| 4 | `docs/LEGAL_COMPLIANCE.md` | (se existir em v1/) | Atualizar documentação legal |
| 5 | **REVISAR** | Compliance | Verificar adequação à LGPD |

---

### 7️⃣ ADICIONAR/ATUALIZAR DOCUMENTOS MESTRES

**Cenário:** Novos documentos necessários para benefícios, atualização de requisitos documentais

**O que são `documentos_mestre`:**
- Lista centralizada de documentos comuns (RG, CPF, laudo médico, etc.)
- Cada documento tem array `categorias[]` indicando quais benefícios o exigem
- Renderizado na seção "📋 Documentos Necessários por Direito" do site
- Permite usuários marcarem documentos que já possuem (localStorage)

| # | Arquivo | Campo/Seção | Ação |
|---|---------|-------------|------|
| 1 | `data/direitos.json` | `documentos_mestre[]` | Adicionar/atualizar objeto com: `id`, `nome`, `descricao`, `categorias[]`, `dica` |
| 2 | `data/direitos.json` | **Benefícios em `categorias[]`** | Adicionar `id` do novo documento ao array `documentos[]` de cada benefício que o exige |
| 3 | `data/direitos.json` | `ultima_atualizacao` | Atualizar data atual |
| 4 | `data/direitos.json` | `versao` | Incrementar patch (ex: 1.4.2 → 1.4.3) **SE** houver mudanças significativas |
| 5 | `js/app.js` | `renderDocsChecklist()` (linha ~1314) | ✅ **AUTOMÁTICO** - Lê `documentos_mestre` e renderiza |
| 6 | `index.html` | Seção "Documentos Necessários" (linha ~407) | ✅ **AUTOMÁTICO** - Container `#docsChecklist` é populado via JS |
| 7 | `docs/CHECKLIST_VALIDATIONS.md` | (opcional) | Documentar requisitos documentais por benefício |
| 8 | `CHANGELOG.md` | Seção [Unreleased] ou [vX.Y.Z] | Adicionar item em `Added` ou `Changed` |
| 9 | **TESTAR** | localStorage | Marcar/desmarcar checkboxes e verificar persistência |
| 10 | **VALIDAR** | JSON | Executar validação de sintaxe |

**Estrutura de um documento mestre:**
```json
{
    "id": "nome_unico",
    "nome": "Nome Exibido do Documento",
    "descricao": "Breve descrição de onde/como obter",
    "categorias": ["bpc", "ciptea", "educacao", "meia_entrada"],
    "dica": "💡 Dica prática para o usuário"
}
```

**❗ ATENÇÃO - Sincronização Bidirecional:**

Quando adicionar novo documento mestre:
1. **Adicionar em `documentos_mestre[]`** (ex: `"id": "cert_escolar"`)
2. **Adicionar nos benefícios correspondentes:**
   ```json
   {
       "id": "educacao",
       "titulo": "Educação Inclusiva",
       "documentos": ["rg", "cpf", "laudo_medico", "cert_escolar"], // ← adicionar aqui
       ...
   }
   ```

**Quando criar novo benefício:**
- Se usar documentos existentes → Adicionar `id` do benefício no array `categorias[]` de cada documento em `documentos_mestre[]`
- Se precisar documento novo → Criar em `documentos_mestre[]` primeiro, depois referenciar

**Exemplo prático - Adicionar "Meia-Entrada":**

**Passo 1 - Criar Documento Novo (se necessário):**
```json
{
    "id": "comprovante_deficiencia",
    "nome": "Comprovante de Deficiência (Carteira PcD ou Laudo)",
    "descricao": "Carteira de identificação PcD, laudo médico, ou CIPTEA para TEA",
    "categorias": ["meia_entrada", "transporte", "estacionamento_especial"],
    "dica": "CIPTEA garante prioridade em atendimentos e meia-entrada"
}
```

**Passo 2 - Adicionar no Benefício:**
```json
{
    "id": "meia_entrada",
    "titulo": "Meia-Entrada",
    "documentos": ["rg", "comprovante_deficiencia"], // ← referencia documentos_mestre
    ...
}
```

**Passo 3 - Atualizar Documentos Existentes:**
```json
{
    "id": "rg",
    "nome": "RG ou Certidão de Nascimento",
    "categorias": [..., "meia_entrada"], // ← adicionar nova categoria
    ...
}
```

**⚠️ CUIDADO - Inconsistências Comuns:**
- ❌ Criar documento em `documentos_mestre[]` mas esquecer de adicionar no benefício
- ❌ Referenciar documento no benefício que não existe em `documentos_mestre[]`
- ❌ Adicionar benefício novo mas esquecer de atualizar `categorias[]` dos documentos existentes

**Validação Recomendada (Criar Script):**
```bash
# scripts/validate_documents.py
# Verificar:
# 1. Todos os IDs em benefícios.documentos[] existem em documentos_mestre[]
# 2. Todos os IDs em documentos_mestre[].categorias[] existem em categorias[]
# 3. Simetria: se doc X lista benefício Y, então Y deve listar doc X
```

---

### 6️⃣ CORRIGIR LINK QUEBRADO (404)

**Cenário:** Link gov.br retornando 404

| # | Arquivo | Campo/Seção | Ação |
|---|---------|-------------|------|
| 1 | **BUSCAR** | Novo link oficial | Acessar planalto.gov.br ou gov.br e localizar página atualizada |
| 2 | `data/direitos.json` | `links_oficiais[]` ou `fontes[].url` | Substituir URL antiga por nova |
| 3 | `data/direitos.json` | `fontes[].consultado_em` | Atualizar data de verificação |
| 4 | `docs/BENEFICIOS_COMPLETOS_PCD.md` | Link na seção `🔗 Links oficiais` | Atualizar URL |
| 5 | `docs/CHECKLIST_VALIDATIONS.md` | Link na tabela/fonte | Atualizar URL |
| 6 | `CHANGELOG.md` | Seção Fixed | Adicionar nota "Corrigido link de [nome]" |
| 7 | **VALIDAR** | Novo link | Testar acesso e confirmar funcionamento |

**Lista de links conhecidos com problemas (histórico):**
- ❌ `gov.br/saude/pt-br/assuntos/saude-de-a-a-z/f/farmacia-popular` (404 em 11/02/2026)

---

## 📁 Matriz de Dependências por Arquivo

### Arquivo: `data/direitos.json` (FONTE PRIMÁRIA)

**Este arquivo é a FONTE DE VERDADE. Qualquer mudança aqui impacta:**

| Campo em direitos.json | Arquivos Impactados | Tipo de Impacto |
|------------------------|---------------------|-----------------|
| `versao` | app.js (linha 861, 1254, 2570-2572), index.html (transparência), package.json, CHANGELOG.md | Exibição de versão |
| `ultima_atualizacao` | app.js (linha 862, 866-867, 1248, 1584), index.html (transparência) | Exibição de data |
| `proxima_revisao` | app.js (linha 1250+), index.html (transparência) | Exibição de data |
| `categorias[]` | app.js (linha 854, 905-928), index.html (grid categorias), CHECKLIST_VALIDATIONS.md, BENEFICIOS_COMPLETOS_PCD.md | Renderização completa |
| `fontes[]` | app.js (linha 1240+), index.html (seção transparência), CHECKLIST_VALIDATIONS.md | Renderização de fontes |
| `aviso` | app.js (?), index.html (?) | Exibição de aviso geral |

**Dependências inversas (quem o atualiza):**
- `scripts/bump_version.py` → Atualiza `versao`, `ultima_atualizacao`
- Processo manual → Atualiza `categorias[]`, `fontes[]`

---

### Arquivo: `index.html`

**Seções críticas que referenciam dados externos:**

| Linhas | Seção | Dependências | Atualização |
|--------|-------|--------------|-------------|
| 176-190 | Navegação | SITE_ORDERING_CRITERIA.md (documentação apenas) | Manual (raramente muda) |
| 300+ | Grid de categorias | app.js → direitos.json (`categorias[]`) | **Automático via JS** |
| 490-540 | Transparência (Fontes) | app.js → direitos.json (`fontes[]`, `versao`, `ultima_atualizacao`) | **Automático via JS** |
| 490-540 | Disclaimer/Compromisso | ⚠️ TEXTO FIXO (não dinâmico) | ❗ **MANUAL - ATENÇÃO** |
| 540+ | Footer (versão) | app.js → direitos.json (`versao`) | **Automático via JS** |

**⚠️ ATENÇÃO - Seção Transparência (linhas 490-540):**
- Contém **TEXTO HARDCODED** que precisa revisão manual:
  - "revisar semanalmente" → CORRIGIR para "manual"
  - "que vamos corrigir assim que possível" → REMOVER
  - Falta disclaimer forte sobre não substituir profissionais
  - Falta aviso LGPD

---

### Arquivo: `js/app.js`

**Funções críticas que manipulam dados:**

| Função | Linha | O que faz | Dependências |
|--------|-------|-----------|--------------|
| `loadDireitos()` | 850 | Faz fetch de `data/direitos.json` | direitos.json |
| `renderCategories()` | 905-928 | Renderiza grid de categorias | direitos.json (`categorias[]`) |
| `renderTransparency()` | 1240+ | Renderiza fontes na seção transparência | direitos.json (`fontes[]`, metadata) |
| `deepFreeze()` | 854 | Congela direitosData (imutabilidade) | direitosData |
| Várias | 861-867, 1248, 1254, 2570-2572 | Exibe versão, data atualização | direitos.json (metadata) |

**Variáveis globais importantes:**
- `direitosData` (linha 74) → Array de categorias (frozen)
- `jsonMeta` (linha 861-865) → Metadados (versão, data, fontes)

---

### Arquivo: `docs/CHECKLIST_VALIDATIONS.md`

**Estrutura de dependências:**

| Seção | Fonte de Dados | Sincronização |
|-------|----------------|---------------|
| Tabela de benefícios | direitos.json (`categorias[]`) | ⚠️ **MANUAL** |
| Base Legal (citações) | direitos.json (`fontes[]`) | ⚠️ **MANUAL** |
| Links oficiais | direitos.json (`links_oficiais[]`) | ⚠️ **MANUAL** |
| Novos benefícios validados | BENEFICIOS_COMPLETOS_PCD.md | ⚠️ **MANUAL** |

**Regra de atualização:**
- **Sempre que** `direitos.json` adicionar benefício → Adicionar validação aqui
- **Sempre que** `BENEFICIOS_COMPLETOS_PCD.md` validar benefício → Sincronizar aqui

---

### Arquivo: `docs/BENEFICIOS_COMPLETOS_PCD.md`

**Estrutura de dependências:**

| Seção | Fonte de Dados | Sincronização |
|-------|----------------|---------------|
| Cada benefício (30+) | Leis federais (planalto.gov.br, gov.br) | ⚠️ **MANUAL** |
| Links oficiais | Sites gov.br verificados | ⚠️ **MANUAL** |
| [PENDENTE] Integração | direitos.json (`categorias[]`) | ❌ **NÃO INTEGRADO** |

**⚠️ ATENÇÃO - PENDÊNCIA CRÍTICA:**
- Este arquivo contém **30+ benefícios validados** que ainda **NÃO ESTÃO em direitos.json**
- **TAREFA URGENTE:** Integrar benefícios em direitos.json

**Lista de benefícios a integrar (prioridade):**
1. Meia-Entrada (Lei 12.933/2013) - 50% cinemas/teatros + acompanhante
2. Passe Livre Interestadual (Lei 8.899/1994) - Gratuidade transporte
3. Atendimento Prioritário (Lei 10.048/2000) - Filas
4. Vagas Estacionamento (LBI Art. 47) - 2% vagas
5. Táxis Acessíveis (LBI Art. 51) - 10% frota
6. Defensoria Pública (LBI Art. 79) - Assistência jurídica gratuita
7. Tecnologia Assistiva (LBI Art. 18) - Órteses, próteses SUS
8. Hotéis Acessíveis (LBI Art. 45) - 10% dormitórios
9. Prioridade Habitação (LBI Art. 32) - 3% Minha Casa Minha Vida
10. [Ver lista completa no arquivo BENEFICIOS_COMPLETOS_PCD.md]

---

### Arquivo: `sw.js` (Service Worker)

**Dependências de cache:**

| Linha | O que cacheia | Impacto |
|-------|---------------|---------|
| 17 | `/data/direitos.json` | Cache do arquivo de dados |
| 1-10 | `CACHE_NAME` versão | Incrementar quando direitos.json mudar |

**Regra de atualização:**
- **Sempre que** `direitos.json` mudar → Incrementar `CACHE_NAME` no sw.js

---

### Arquivo: `scripts/bump_version.py`

**O que atualiza automaticamente:**

| Arquivo Alvo | Campo | Ação |
|--------------|-------|------|
| `data/direitos.json` | `versao` | Incrementa (major.minor.patch conforme argumento) |
| `data/direitos.json` | `ultima_atualizacao` | Data atual |
| `package.json` | `version` | Sincroniza com direitos.json |

**⚠️ NÃO atualiza automaticamente:**
- `proxima_revisao` (precisa adicionar essa funcionalidade)
- `CHANGELOG.md` (precisa adicionar manualmente)
- Arquivos de documentação

---

## 🚨 Alertas de Inconsistência (Detectar Problemas)

### Verificações a Executar Regularmente

**1. Sincronização de Versões**
```bash
# Versão em direitos.json
grep '"versao"' data/direitos.json

# Versão em package.json
grep '"version"' package.json

# ✅ Devem ser iguais
```

**2. Validação JSON**
```bash
node -e "JSON.parse(require('fs').readFileSync('data/direitos.json'))"
# ✅ Não deve retornar erro
```

**3. Links Quebrados (Manual)**
- Verificar todos os links em `direitos.json > fontes[] > url`
- Verificar todos os links em `direitos.json > categorias[] > links_oficiais[]`
- Verificar links em `BENEFICIOS_COMPLETOS_PCD.md`

**4. Benefícios sem Validação**
- Comparar `direitos.json > categorias[]` com `CHECKLIST_VALIDATIONS.md`
- Listar benefícios em BENEFICIOS_COMPLETOS_PCD.md que NÃO estão em direitos.json

**5. Data de Atualização Defasada**
```bash
# Última atualização
grep 'ultima_atualizacao' data/direitos.json

# Se > 30 dias → Revisar fontes
```

---

## 📋 Checklist Pré-Commit (OBRIGATÓRIO)

**"não pode ser feito commit e push se houver falhas"**

Antes de **QUALQUER** commit:

- [ ] **1. Validação JSON:** `node -e "JSON.parse(require('fs').readFileSync('data/direitos.json'))"`
- [ ] **2. Versão incrementada:** `data/direitos.json > versao` foi atualizada?
- [ ] **3. Data atualizada:** `data/direitos.json > ultima_atualizacao` está correto?
- [ ] **4. package.json sincronizado:** Versões em package.json e direitos.json iguais?
- [ ] **5. CHECKLIST_VALIDATIONS.md atualizado:** Novos benefícios têm validação legal?
- [ ] **6. BENEFICIOS_COMPLETOS_PCD.md sincronizado:** Todos os benefícios documentados?
- [ ] **7. Links funcionando:** Todos os links gov.br testados (sem 404)?
- [ ] **8. Teste visual:** `index.html` aberto no navegador, categorias renderizando?
- [ ] **9. Cache atualizado:** `sw.js > CACHE_NAME` incrementado se direitos.json mudou?
- [ ] **10. CHANGELOG.md atualizado:** Mudanças documentadas em [Unreleased]?
- [ ] **11. v2/ no .gitignore:** Pasta v2/ está excluída do commit?
- [ ] **12. Disclaimer atualizado:** Avisos LGPD e profissional estão corretos?

**Script de validação (recomendado criar):**
```bash
#!/bin/bash
# scripts/pre-commit-validation.sh

echo "🔍 Validando antes do commit..."

# 1. JSON válido
node -e "JSON.parse(require('fs').readFileSync('data/direitos.json'))" || exit 1

# 2. Versões sincronizadas
DIREITOS_VERSION=$(grep '"versao"' data/direitos.json | head -1 | cut -d'"' -f4)
PACKAGE_VERSION=$(grep '"version"' package.json | head -1 | cut -d'"' -f4)

if [ "$DIREITOS_VERSION" != "$PACKAGE_VERSION" ]; then
    echo "❌ Versões diferentes! direitos.json: $DIREITOS_VERSION | package.json: $PACKAGE_VERSION"
    exit 1
fi

echo "✅ Validações passaram. Pode commitar."
```

---

## 📊 Histórico de Auditorias

| Data | Versão | Auditoria Realizada | Inconsistências Encontradas | Status |
|------|--------|---------------------|----------------------------|--------|
| 2026-02-11 | 1.3.0 | Criação deste documento + mapeamento completo | ⚠️ 30+ benefícios em BENEFICIOS_COMPLETOS_PCD.md não integrados em direitos.json <br> ⚠️ index.html linha 532-537 com texto "semanal" e "que vamos corrigir" <br> ⚠️ v2/ não está no .gitignore | 🔄 EM CORREÇÃO |

---

## 🎯 Próximos Passos (Roadmap de Dependências)

**Prioridade ALTA:**
1. ✅ Criar este documento (DEPENDENCY_CONTROL.md) - **FEITO**
2. ⏳ Corrigir index.html seção transparência (remover "semanal", "vamos corrigir")
3. ⏳ Adicionar v2/ ao .gitignore
4. ⏳ Integrar 30+ benefícios de BENEFICIOS_COMPLETOS_PCD.md em direitos.json
5. ⏳ Sincronizar CHECKLIST_VALIDATIONS.md com novos benefícios
6. ⏳ Adicionar disclaimers LGPD e aviso profissional em index.html

**Prioridade MÉDIA:**
7. ⏳ Criar script de validação pré-commit (scripts/pre-commit-validation.sh)
8. ⏳ Automatizar verificação de links quebrados
9. ⏳ Adicionar funcionalidade de `proxima_revisao` em bump_version.py

**Prioridade BAIXA:**
10. ⏳ Criar dashboard de status de sincronização
11. ⏳ Automatizar geração de CHANGELOG.md

---

## 📞 Contato e Manutenção

**Responsável:** Fabio Treze  
**E-mail:** fabiotreze@hotmail.com  
**Última atualização deste documento:** 11 de fevereiro de 2026  
**Próxima revisão:** Sempre que houver mudança estrutural no projeto

---

**🔐 REGRA DE OURO:**

> **ANTES** de modificar qualquer arquivo, consulte este documento e verifique **TODAS** as dependências. **DEPOIS** de modificar, atualize **TODOS** os arquivos relacionados conforme a matriz acima. **NUNCA** faça commit sem passar pelo Checklist Pré-Commit.

---

**FIM DO DOCUMENTO**
