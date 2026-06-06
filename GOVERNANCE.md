# 📋 NossoDireito — Governança de Dados e Fontes

> Documento que define os critérios, fluxos e boas práticas para manter o portal atualizado,
> confiável e sempre embasado em fontes oficiais do governo brasileiro.

**Última revisão:** 2026-06-05
**Versão:** 1.43.30

---

## 1. Princípios Fundamentais

| Princípio | Descrição |
|-----------|-----------|
| **Oficialidade** | Toda informação deve vir de fonte oficial (gov.br, legislação, norma técnica) |
| **Rastreabilidade** | Cada dado deve ter fonte, data de consulta e link verificável |
| **Atualidade** | Informações devem ser revisadas periodicamente e atualizadas quando necessário |
| **Completude** | Cada categoria deve ter base legal, documentos, passo a passo e contatos |
| **Acessibilidade** | Informações devem ser compreensíveis por leigos (linguagem simples) |

---

## 2. Fontes Oficiais Aceitas

### 2.1, Fontes Primárias (obrigatórias)

| Domínio | Órgão | Tipo |
|---------|-------|------|
| `planalto.gov.br` | Presidência da República | Legislação federal |
| `gov.br` | Portal de Serviços do Governo | Serviços e informações |
| `inss.gov.br` | INSS | Benefícios previdenciários |
| `ans.gov.br` | Agência Nacional de Saúde | Planos de saúde |
| `mds.gov.br` | Min. Desenvolvimento Social | Assistência social |
| `cnmp.mp.br` | Conselho Nacional do MP | Ministério Público |
| `mpt.mp.br` | Ministério Público do Trabalho | Trabalho |
| `caixa.gov.br` | Caixa Econômica Federal | FGTS |
| `procon.sp.gov.br` | Procon | Defesa do consumidor |
| `abnt.org.br` | ABNT | Normas técnicas (NBR 9050) |

### 2.2. Fontes Secundárias (aceitas com ressalva)

| Domínio | Órgão | Justificativa |
|---------|-------|---------------|
| `apaebrasil.org.br` | APAE Brasil | Maior rede de PcD do Brasil |
| `anadep.org.br` | Defensoria Pública | Associação oficial |
| `oab.org.br` | OAB | Entidade de classe |
| `ama.org.br` | AMA | Pioneira em autismo |
| `ijc.org.br` | Instituto Jô Clemente | Referência em DI e TEA |
| `autismbrasil.org` | ABRACI | Articulação nacional |

> ⚠️ Fontes secundárias devem ser usadas apenas para **informações de contato e serviços**.
> Para **base legal e direitos**, usar sempre fontes primárias.

### 2.3. Fontes Proibidas

- Blogs pessoais, Wikipedia, sites de advocacia particular
- Redes sociais (Instagram, Facebook, TikTok)
- Sites com paywall ou que exijam cadastro
- Fontes sem data de publicação ou sem autor institucional

---

## 3. Critérios para Adicionar Nova Categoria

### 3.1. Pré-requisitos (TODOS obrigatórios)

- [ ] **Base legal federal** — pelo menos 1 lei federal vigente (planalto.gov.br)
- [ ] **Relevância** — afeta diretamente PcD ou familiares diretos
- [ ] **Acionabilidade** — existem passos concretos que a pessoa pode tomar
- [ ] **Fontes verificáveis** — links oficiais acessíveis e atualizados
- [ ] **Documentos** — lista clara de documentos necessários
- [ ] **Canal de acesso** — onde a pessoa vai buscar (CRAS, INSS, Prefeitura, etc.)

### 3.2. Schema Obrigatório da Categoria

```json
{
    "id": "identificador_unico",           // snake_case, sem acentos
    "titulo": "Nome — Subtítulo",          // Max 80 caracteres
    "icone": "🏠",                          // Emoji representativo
    "resumo": "Descrição em 1-2 frases",   // Max 200 caracteres
    "base_legal": [                         // Mínimo 1 entrada
        {
            "lei": "Lei XXXXX/YYYY",
            "artigo": "Art. XX",
            "link": "https://planalto.gov.br/..."  // campo 'url' no JSON real
        }
    ],
    "requisitos": ["..."],                  // Mínimo 2 requisitos
    "documentos": ["..."],                  // Mínimo 3 documentos
    "passo_a_passo": ["..."],               // Mínimo 3 passos
    "dicas": ["..."],                       // Mínimo 2 dicas
    "valor": "Descrição do valor/custo",
    "onde": "Local de atendimento",
    "links": [                              // Mínimo 1 link oficial
        {
            "titulo": "Texto do link",
            "url": "https://..."
        }
    ],
    "tags": ["..."]                         // Mínimo 5 tags para busca
}
```

### 3.3. Checklist ao adicionar categoria

1. Criar entrada no array `categorias` do JSON
2. Adicionar keywords no `KEYWORD_MAP` (app.js) — incluir variantes com/sem acento
3. Atualizar `instituicoes_apoio` — quais instituições cobrem a nova categoria
4. Atualizar `documentos_mestre` — adicionar "moradia" (ou nova cat) aos docs compartilhados
5. Adicionar `fontes` — leis, decretos e serviços usados
6. Atualizar `artigos_referenciados` nas fontes existentes (ex: LBI)
7. Incrementar versão (semver MINOR para nova categoria)
8. Atualizar `ultima_atualizacao`
9. Rodar `python3 scripts/validate_all.py --quick` — deve passar sem CRITICAL
10. Testar no navegador — categoria aparece, busca encontra, análise de documento detecta

---

## 4. Critérios para Adicionar Nova Fonte

### 4.1. Validação obrigatória

- [ ] URL responde HTTP 200 (ou 301/302)
- [ ] Domínio pertence à lista de fontes oficiais aceitas (seção 2.1 deste documento)
- [ ] Campo `consultado_em` preenchido com data YYYY-MM-DD
- [ ] Campo `orgao` preenchido
- [ ] Se legislação: campo `artigos_referenciados` preenchido

### 4.2. Atualização de fontes existentes

Quando uma lei é alterada:
1. Manter entrada original (histórico)
2. Adicionar nova entrada com lei atualizada
3. Atualizar `artigos_referenciados`
4. Atualizar `consultado_em` com a data da verificação
5. Atualizar conteúdo das categorias afetadas

---

## 5. Fluxo de Revisão

```
Revisão (manual) ─────→ Quando houver mudança legislativa ou atualização
                         ├─ Acessar sites oficiais
                         ├─ Verificar mudanças legislativas
                         ├─ Atualizar valores ($)
                         ├─ Testar todos os links manualmente
                         └─ Atualizar JSON se necessário

Pós-revisão ──────────→ Atualizar campos do JSON
                         ├─ ultima_atualizacao
                         ├─ consultado_em (nas fontes verificadas)
                         └─ Registrar no CHANGELOG
```

### 5.1. Onde verificar mudanças legislativas

| O que verificar | Onde | Frequência |
|----------------|------|------------|
| Novas leis PcD | planalto.gov.br → Legislação → Pesquisa | Sob demanda |
| Alterações no BPC | gov.br/inss → Notícias | Sob demanda |
| Valor salário mínimo | gov.br → Salário mínimo | Anual (jan) |
| Mudanças ANS | gov.br/ans → Notícias | Sob demanda |
| NBR 9050 atualizações | abnt.org.br | Quando publicada |
| Programas habitacionais | gov.br/cidades → MCMV | Sob demanda |
| Diário Oficial da União | dou.gov.br | Sob demanda |

### 5.2. Alertas que demandam ação imediata

- Lei PcD **revogada ou alterada** → Atualizar base_legal + conteúdo em 24h
- Valor do BPC/salário mínimo **atualizado** → Atualizar campo `valor` imediatamente
- Link oficial **quebrado** → Encontrar URL nova e atualizar em 48h
- Serviço gov.br **migrado** → Atualizar URLs e passo_a_passo em 48h

---

## 6. Categorias Candidatas (backlog de pesquisa)

Categorias que podem ser adicionadas após pesquisa e validação:

| Categoria | Base Legal Potencial | Status |
|-----------|---------------------|--------|
| Isenção de impostos (IR, IPTU) | Lei 7.713/1988, leis municipais | ✅ Implementada (v1.5.0+) |
| Prioridade em filas e atendimento | Lei 10.048/2000 | ✅ Implementada (v1.5.0+) |
| Curatela e tomada de decisão apoiada | Código Civil Art. 1.767+, LBI Art. 84-87 | 🔍 Pesquisar |
| Tecnologia assistiva | LBI Art. 74-75, Lei 10.098/2000 | ✅ Implementada (v1.5.0+) |
| Perícia e aposentadoria PcD | LC 142/2013 | ✅ Implementada (v1.5.0+) |
| CNH especial | Resolução Contran 168/2004 | 🔍 Pesquisar |
| Certidão de PcD estadual | Leis estaduais variadas | 🔍 Pesquisar |

> Para cada candidata, aplicar os critérios da Seção 3.1 antes de implementar.

---

## 7. Boas Práticas de Integridade

### 7.1. Nunca fazer

- ❌ Copiar texto de sites sem verificar a fonte original (gov.br)
- ❌ Usar informações de fontes não-oficiais como base legal
- ❌ Publicar sem rodar `validate_all.py --quick` (deve passar sem CRITICAL)
- ❌ Deixar link quebrado sem correção
- ❌ Inventar ou inferir direitos não previstos em lei
- ❌ Dar conselho jurídico — o site **informa**, não aconselha

### 7.2. Sempre fazer

- ✅ Citar a lei, artigo e link direto para o texto legal
- ✅ Incluir o disclaimer de que informações podem estar desatualizadas
- ✅ Manter `consultado_em` atualizado em cada fonte verificada
- ✅ Testar todos os links antes de publicar
- ✅ Rodar `validate_all.py --quick` após qualquer alteração
- ✅ Incluir variantes sem acento no `KEYWORD_MAP` (ex: `condomínio` e `condominio`)

### 7.3. Tom e linguagem

- Usar linguagem **simples e direta** (5ª série / público leigo)
- Evitar jargão jurídico excessivo — quando usar, explicar
- Sempre indicar **onde ir** e **o que levar** (ação concreta)
- Incluir **dicas práticas** que ajudem famílias no dia a dia

---

## 8. Versionamento

| Tipo de mudança | Incremento | Exemplo |
|----------------|------------|---------|
| Correção de texto/link | PATCH | 1.0.0 → 1.0.1 |
| Nova categoria | MINOR | 1.0.0 → 1.1.0 |
| Reestruturação do JSON/app | MAJOR | 1.0.0 → 2.0.0 |
| Atualização de valor (BPC) | PATCH | 1.0.0 → 1.0.1 |
| Nova instituição | PATCH | 1.0.0 → 1.0.1 |

---

*Documento mantido como parte do projeto NossoDireito.*
*Para dúvidas sobre o processo, abra uma issue no GitHub.*
