# Como Contribuir com o NossoDireito 🤝

**Bem-vindo(a)!** Este projeto é mantido pela **comunidade** e sua contribuição é essencial para manter as informações atualizadas e precisas.

---

## 🎯 Formas de Contribuir

### 1️⃣ Reportar Conteúdo Desatualizado (Mais Comum)

Encontrou um link quebrado, lei revogada ou informação incorreta?

#### ✅ O Que Reportar:

- 🔗 **Link quebrado** (retorna erro 404 ou 500)
- ⚖️ **Lei revogada ou alterada** (nova redação, emenda, STF)
- 📊 **Informação incorreta** (valor desatualizado, requisito mudado, prazo errado)
- 🆕 **Benefício novo** (lei recente não listada aqui)
- 📍 **Endereço/telefone desatualizado** (órgão mudou localização)

#### 📝 Como Reportar:

##### Opção A: GitHub Issues (Recomendado)

1. Acesse: https://github.com/fabiotreze/nossodireito/issues
2. Clique em **"New Issue"**
3. Escolha template: **"Conteúdo Desatualizado"**
4. Preencha:

```markdown
**Benefício afetado:** [ex: "Passe Livre Intermunicipal"]

**Problema encontrado:**
[ex: "Link do INSS retorna erro 404"]

**Fonte correta (se souber):**
[ex: "Novo link: https://meu.inss.gov.br/passe-livre"]

**Evidência (opcional):**
[screenshot do erro, print da lei, etc.]
```

5. Clique em **"Submit New Issue"**

##### Opção B: Email (Alternativa)

- **Para:** fabiotreze@hotmail.com
- **Assunto:** `NossoDireito — Conteúdo Desatualizado`
- **Corpo:**

```
Benefício: [nome do benefício]
Problema: [descrição do problema]
Fonte correta: [se souber o link correto]
```

#### ⏱️ Tempo de Resposta:

| Prioridade | Exemplo | SLA |
|------------|---------|-----|
| 🔥 **CRÍTICA** | Link gov.br principal quebrado | 24 horas |
| ⚠️ **ALTA** | Lei revogada, valor errado | 48 horas |
| 📌 **MÉDIA** | Link secundário, typo | 72 horas |
| 🔵 **BAIXA** | Sugestão de melhoria | 1 semana |

---

### 2️⃣ Sugerir Novos Benefícios

Conhece um benefício PcD que NÃO está no site?

#### ✅ Critérios de Inclusão:

- ✅ **Nacional** ou **multi-estadual** (não apenas um município)
- ✅ **Tem base legal** (lei, decreto, portaria)
- ✅ **Vigente** (não revogado)
- ✅ **Acessível** (não depende de liminar individual)
- ✅ **Verificável** (fonte oficial gov.br ou órgão reconhecido)

#### 📝 Informações Necessárias:

1. **Nome do benefício** (oficial)
2. **Resumo** (1 parágrafo, 50-100 palavras)
3. **Base legal** (lei + artigo):
   - Ex: "Lei 8.742/1993, Art. 20"
   - Link do Planalto: http://www.planalto.gov.br/ccivil_03/leis/...
4. **Requisitos** (quem tem direito)
5. **Documentos necessários**
6. **Onde solicitar** (site, presencial, telefone)
7. **Links oficiais** (no mínimo 2 fontes gov.br)

#### 📌 Como Submeter:

**GitHub Issue:**
https://github.com/fabiotreze/nossodireito/issues/new?template=novo_beneficio.md

**Email:**
Envie as informações acima para fabiotreze@hotmail.com (assunto: "Novo Benefício")

---

### 3️⃣ Contribuir com Código (Pull Request)

Sabe programar? Ajude a melhorar o código!

#### 🛠️ Setup do Ambiente de Desenvolvimento

```bash
# 1. Fork o repositório
# (clique em "Fork" no GitHub)

# 2. Clone seu fork
git clone https://github.com/SEU_USUARIO/nossodireito.git
cd nossodireito

# 3. Instale Python 3.11+ (se não tiver)
python3 --version  # deve ser >= 3.11

# 4. Rode o servidor de desenvolvimento
python3 -m http.server 8080

# 5. Abra no navegador
open http://localhost:8080
```

#### ✅ Checklist Antes de Abrir PR:

- [ ] **Rode o Quality Gate:**
  ```bash
  python scripts/master_compliance.py --quick
  ```

- [ ] **Valide JSON:**
  ```bash
  python -c "import json; json.load(open('data/direitos.json'))"
  ```

- [ ] **Teste no navegador:**
  - [ ] Desktop (Chrome, Firefox, Edge)
  - [ ] Mobile (iOS Safari, Android Chrome)
  - [ ] Acessibilidade (Tab navigation, Screen reader)

- [ ] **Atualize versão** (se relevante):
  ```bash
  python scripts/bump_version.py 1.X.Y
  ```

- [ ] **Atualize CHANGELOG.md**

#### 📋 Estrutura do Pull Request:

**Título:**
`[FEATURE] Adiciona benefício X` ou `[FIX] Corrige link Y` ou `[DOCS] Atualiza Z`

**Descrição:**
```markdown
## Resumo
[Descreva a mudança em 1-2 frases]

## Motivação
[Por que essa mudança é necessária?]

## Checklist
- [x] Quality Gate passou (score >= 75)
- [x] JSON validado
- [x] Testado em desktop E mobile
- [x] CHANGELOG.md atualizado
- [x] Versão atualizada (se relevante)

## Screenshots (se aplicável)
[Cole prints antes/depois]
```

**Label:**
Adicione label apropriado: `bugfix`, `enhancement`, `documentation`, `security`

#### ⏱️ Tempo de Revisão:

- 🔥 **Hotfix** (site quebrado): 4-8 horas
- ⚠️ **Bugfix**: 1-3 dias
- 🆕 **Feature**: 3-7 dias (revisão mais cuidadosa)
- 📖 **Docs**: 1-2 dias

---

### 4️⃣ Melhorar Documentação

Documentação never is enough! Ajude a documentar:

#### 📚 Docs Que Precisam de Ajuda:

- [ ] **README.md** — Melhorar instruções de uso
- [ ] **ARCHITECTURE.md** — Documentar decisões arquiteturais
- [ ] **ACCESSIBILITY.md** — Auditoria WCAG 2.1
- [ ] **PERFORMANCE.md** — Lighthouse scores, otimizações
- [ ] **SECURITY.md** — Vulnerabilidades conhecidas

#### 📝 Como Contribuir:

1. Edite arquivo `.md` no seu fork
2. Abra PR com label `documentation`
3. Descreva o que foi melhorado

---

### 5️⃣ Traduzir para Outros Idiomas

**Planejado:** Suporte a Espanhol e Inglês (sem data definida).

Se você fala esses idiomas e quer ajudar, entre em contato:
fabiotreze@hotmail.com (assunto: "Tradução")

---

## 🚨 O Que NÃO Fazer (Proibido)

❌ **Não adicione dados pessoais:** Jamais inclua CPF, RG, endereço de terceiros
❌ **Não faça spam:** Pull Requests com propagandas serão rejeitados
❌ **Não copie conteúdo protegido:** Use apenas fontes oficiais e citadas
❌ **Não remova créditos:** Mantenha autoria e licença MIT
❌ **Não quebre o código:** Sempre rode Quality Gate antes de enviar PR

---

## 📜 Código de Conduta

Este projeto segue o [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).

**Resumo:**

- ✅ Seja respeitoso e inclusivo
- ✅ Aceite críticas construtivas
- ✅ Foque no que é melhor para a comunidade
- ❌ Não tolere assédio, discriminação ou linguagem ofensiva

**Reportar violações:**
fabiotreze@hotmail.com (assunto: "Código de Conduta")

---

## 🏆 Reconhecimento

### Hall da Fama dos Contribuidores:

| Contribuidor | Contribuições | Desde |
|--------------|---------------|-------|
| **Fabio Costa** | Criador e mantenedor | dez/2025 |
| _(seu nome aqui)_ | _(suas contribuições)_ | _(data)_ |

**Como aparecer aqui:**
Envie 3+ Pull Requests aceitos ou reporte 5+ issues úteis!

---

## 💬 Dúvidas Frequentes (FAQs)

### P: Preciso saber programar para contribuir?

**R:** **NÃO!** A maioria das contribuições são **reportes de conteúdo desatualizado** (links quebrados, leis mudadas). Qualquer pessoa pode ajudar!

### P: Quanto tempo leva para meu PR ser revisado?

**R:** Depende da complexidade:
- Bugfix simples: 1-3 dias
- Feature nova: 3-7 dias
- Mudança grande (arquitetura): 1-2 semanas

### P: Minha sugestão foi rejeitada. Por quê?

**R:** Possíveis motivos:
- Benefício não é nacional (apenas um município)
- Não tem base legal clara
- Fonte não é oficial (blogpost, rede social)
- Duplicado (já existe no site)

Sempre explicamos o motivo da rejeição no Issue/PR.

### P: Posso contribuir anonimamente?

**R:** **Sim!** Use pseudônimo no GitHub. Não pedimos dados pessoais.

### P: Ganho algo contribuindo?

**R:** **Reconhecimento público:**
- Nome no Hall da Fama
- Créditos no README.md
- Badge de contribuidor no GitHub

**Não há pagamento** (projeto sem fins lucrativos).

### P: Como sei se meu Issue já foi reportado?

**R:** Busque antes de criar novo:
https://github.com/fabiotreze/nossodireito/issues?q=is%3Aissue

---

## 📞 Contato

**Mantenedor Principal:**
Fabio Costa — fabiotreze@hotmail.com

**GitHub:**
https://github.com/fabiotreze/nossodireito

**Site:**
https://nossodireito.fabiotreze.com

---

## 📄 Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a [Licença MIT](../LICENSE).

**Resumo:**
- ✅ Livre para usar, modificar, distribuir
- ✅ Sem garantias (use por sua conta e risco)
- ✅ Mantenha créditos e licença

---

**Última Atualização:** 11 de fevereiro de 2026
**Versão:** 1.0.0
**Agradecemos sua contribuição!** 🙏
