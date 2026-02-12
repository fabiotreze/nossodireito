# 🎯 AUDITORIA DE ACESSIBILIDADE — NOSSODIREITO

**Data:** 12/02/2026
**Validadores:** AccessMonitor (PT), AccessibilityChecker.org, WAVE (WebAIM)
**Normas:** WCAG 2.1/2.2 AA, ABNT NBR 17060, eMAG 3.1
**URL:** https://nossodireito.fabiotreze.com/

---

## 📊 RESUMO EXECUTIVO

| Métrica | Valor | Status |
|---------|-------|--------|
| **AccessMonitor** | 8.7/10 | ⚠️ BOM |
| **AccessibilityChecker** | <90 | ❌ RISCO |
| **WAVE AIM Score** | 10/10 | ✅ EXCELENTE |
| **Issues Críticos (P0)** | 9 | 🔴 CORRIGIR |
| **Issues Altos (P1)** | 2 | 🟡 CORRIGIR |
| **Compliance WCAG AA** | ❌ NÃO | ⚠️ RISCO LEGAL |

### ⚖️ CLASSIFICAÇÃO LEGAL

- **Brasil (LBI 13.146/2015):** ⚠️ PARCIALMENTE CONFORME (9 issues críticos)
- **USA (ADA Title III):** ❌ NÃO CONFORME (risco de processos)
- **eMAG 3.1 (Gov.br):** ⚠️ ~75% (bom, mas gaps em P0)

---

## 🎯 PROBLEMAS CRÍTICOS (P0) — 9 ISSUES

### 1. **aria-hidden com elementos focáveis** (2 elementos) ⏱️ 2h

**WCAG:** 2.0-2.2 Level A
**Afeta:** Cegos, baixa visão, mobilidade reduzida

**Elementos:**
- `#disclaimerModal` - Modal com botões focáveis
- `#fileInput` - Input file oculto mas focável

**Solução:**
```html
<!-- disclaimerModal: adicionar tabindex="-1" -->
<div id="disclaimerModal" aria-hidden="true">
  <button tabindex="-1" class="close-modal">×</button>
  <button tabindex="-1" class="accept">OK</button>
</div>

<!-- fileInput: adicionar tabindex="-1" -->
<input type="file" id="fileInput"
       aria-hidden="true"
       tabindex="-1"
       class="sr-only" />
```

---

### 2. **Contraste de cores insuficiente** (1-2 elementos) ⏱️ 1h

**WCAG:** 2.0-2.2 Level AA
**Afeta:** Baixa visão, daltonismo

**Elementos:**
- `.transparency-note > h3` (cor accent vs fundo)

**Solução:**
```css
/* ANTES: contraste insuficiente */
.transparency-note h3 {
  color: var(--accent); /* ~3:1 */
}

/* DEPOIS: contraste ≥4.5:1 */
.transparency-note h3 {
  color: #0056b3; /* Azul escuro */
}
```

**Ferramenta:** [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

---

### 3. **Links não distinguíveis sem cor** (3 elementos) ⏱️ 1h

**WCAG:** 2.0-2.2 Level A
**Afeta:** Baixa visão, daltonismo

**Links afetados:**
- Links em  parágrafos (3 elementos)
- Email: `fabiotreze@hotmail.com`
- Links externos (OMS ICD, Ministério da Saúde)

**Solução:**
```css
/* Adicionar underline em links dentro de texto */
p a, .section-desc a, .benefits-grid a {
  text-decoration: underline;
  text-underline-offset: 2px;
}

p a:hover, .section-desc a:hover {
  text-decoration: none;
  font-weight: 600;
}
```

---

### 4. **Controles interativos aninhados** (1 elemento) ⏱️ 2h

**WCAG:** 2.0-2.2 Level A
**Afeta:** Cegos, mobilidade reduzida

**Elemento:**
- `#uploadZone` (div role="button" contém input file)

**Solução:**
```html
<!-- ANTES (errado) -->
<div id="uploadZone" role="button" tabindex="0">
  <input type="file" id="fileInput" />
</div>

<!-- DEPOIS (correto) -->
<div id="uploadZone" role="button" tabindex="0"
     onclick="document.getElementById('fileInput').click()"
     aria-label="Clique ou arraste arquivos">
  <p>📎 Clique ou arraste arquivos</p>
</div>
<input type="file" id="fileInput"
       class="sr-only"
       aria-hidden="true"
       tabindex="-1" />
```

---

### 5. **Form label faltando** (1 elemento) ⏱️ 0.5h

**WCAG:** 2.0-2.2 Level A
**Afeta:** Cegos, baixa visão

**Ação:**
1. Identificar qual input está sem label
2. Adicionar `<label>` ou `aria-label`

**Solução genérica:**
```html
<!-- Adicionar label -->
<label for="inputId" class="sr-only">Descrição</label>
<input id="inputId" type="text" />
```

---

## 🟡 PROBLEMAS ALTOS (P1) — 2 ISSUES

### 6. **Conteúdo fora de landmarks** (2 elementos VLibras) ⏱️ 1h

**Best Practice (WCAG Support)**
**Afeta:** Cegos, surdocegos, baixa visão

**Solução:**
```html
<aside aria-label="Widget de acessibilidade VLibras"
       role="complementary">
  <div vw class="enabled">
    <div vw-access-button class="active"></div>
    <div vw-plugin-wrapper>
      <div class="vw-plugin-top-wrapper"></div>
    </div>
  </div>
</aside>
```

---

### 7. **Texto visível não no nome acessível** (4 elementos) ⏱️ 2h

**WCAG:** 2.0-2.2 Level A
**Afeta:** Usuários de comandos de voz, leitores de tela

**Solução:**
```html
<!-- ANTES (errado) -->
<button aria-label="Fechar modal">×</button>

<!-- DEPOIS (correto - Opção 1) -->
<button aria-label="× Fechar modal">×</button>

<!-- DEPOIS (correto - Opção 2) -->
<button>
  <span aria-hidden="true">×</span>
  <span class="sr-only">Fechar modal</span>
</button>
```

---

## 🟢 MELHORIAS OPCIONAIS (P2) — NÃO OBRIGATÓRIAS

### 8. **Contraste AAA** (78 combinações) ⏱️ 4h

**WCAG:** 2.0-2.2 Level AAA (opcional)
**Meta:** Contraste ≥7:1

**Não obrigatório**, mas recomendado para excelência.

---

### 9. **Link redundante** (1 elemento) ⏱️ 0.25h

**WAVE Best Practice**

**Solução:**
```html
<!-- Remover aria-label duplicado -->
<a href="index.html" aria-hidden="true" tabindex="-1">
```

---

## 📋 PLANO DE AÇÃO — TIMELINE

### **Sprint 1 (Esta semana) — P0** ⏱️ 6.5h

**Objetivo:** Eliminar 9 issues críticos

| Ação | Complexidade | Status |
|------|--------------|--------|
| 1. Executar `fix_accessibility_p0.py` | 0.5h | 🔜 PRÓXIMO |
| 2. Correções manuais HTML | 3h | 🔜 PRÓXIMO |
| 3. Correções manuais CSS | 1h | 🔜 PRÓXIMO |
| 4. Validação nos 3 tools | 2h | 🔜 PRÓXIMO |

**Meta:** AccessMonitor ≥9.0/10 | AccessibilityChecker ≥95

---

### **Sprint 2 (Próxima semana) — P1** ⏱️ 3h

**Objetivo:** Resolver 6 elementos altos

| Ação | Complexidade | Status |
|------|--------------|--------|
| 1. VLibras em landmark | 1h | 🔜 AGUARDANDO |
| 2. Texto visível em nomes | 2h | 🔜 AGUARDANDO |

**Meta:** AccessMonitor ≥9.3/10 | AccessibilityChecker ≥98

---

### **Sprint 3 (Mês 1) — P2 Opcional** ⏱️ 4.25h

**Objetivo:** Excelência (AAA parcial)

| Ação | Complexidade | Status |
|------|--------------|--------|
| 1. Contraste AAA | 4h | 🔜 OPCIONAL |
| 2. Link redundante | 0.25h | 🔜 OPCIONAL |

**Meta:** AccessMonitor ≥9.5/10 | AccessibilityChecker 100

---

## 📊 ANÁLISE DOS 3 VALIDADORES

### 1️⃣ **AccessMonitor (Portugal)** — 8.7/10

**Práticas Aceitáveis:** 25
**Práticas Manuais:** 6
**Práticas Não Aceitáveis:** 4

✅ **Pontos fortes:**
- HTML válido (W3C)
- Imagens com alt text
- Controles com nomes acessíveis
- Semântica banner/main/contentinfo correta
- Zero IDs repetidos

❌ **Falhas:**
- 2 combinações de cor com contraste AA insuficiente
- 2 elementos aria-hidden com foco
- 1 papel semântico com descendentes focáveis
- 4 elementos com texto visível não no nome

---

### 2️⃣ **AccessibilityChecker.org** — <90 (NOT COMPLIANT)

**Passed Audits:** 45
**Critical Issues:** 9
**Manual Audits:** 22

✅ **Pontos fortes:**
- HTML válido
- ARIA correto
- Semântica robusta

❌ **Falhas (coincidem com AccessMonitor):**
- Focusable in aria-hidden (2)
- Color contrast (1)
- Links not distinguishable (3)
- Nested controls (1)
- Content outside landmarks (2)

---

### 3️⃣ **WAVE (WebAIM)** — AIM Score 10/10

**Errors:** 1
**Contrast Errors:** 0 (mas AAA: 2)
**Alerts:** 2 relevantes

✅ **Pontos fortes:**
- Features: 31 (alt text, labels, headings, landmarks)
- ARIA: 59 (roles, labels, alerts)
- Structure: 59 (headings, lists, landmarks)

❌ **Falhas:**
- 1 form label faltando
- 1 link redundante (alerta)

---

## 🎯 COMPARAÇÃO COM eMAG 3.1 (Gov.br)

| Recomendação | Status | Meta P0 | Meta P1 |
|--------------|--------|---------|---------|
| **1. Marcação** | ✅ 100% | - | - |
| **2. Comportamento** | ⚠️ 75% | ✅ 95% | ✅ 100% |
| **3. Conteúdo** | ⚠️ 70% | ✅ 90% | ✅ 95% |
| **4. Apresentação** | ⚠️ 65% | ✅ 90% | ✅ 95% |
| **5. Multimídia** | ⚠️ 70% | - | ✅ 80% |
| **6. Formulário** | ⚠️ 80% | ✅ 100% | - |

**Compliance atual:** ~75%
**Meta após P0:** ~92%
**Meta após P1:** ~97%

---

## 🔗 FERRAMENTAS E RECURSOS

### Validadores Usados
- [AccessMonitor](https://accessmonitor.acessibilidade.gov.pt/)
- [AccessibilityChecker.org](https://www.accessibilitychecker.org/)
- [WAVE](https://wave.webaim.org/)

### Ferramentas de Contraste
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Coolors Contrast Checker](https://coolors.co/contrast-checker)

### Normas e Legislação
- [WCAG 2.1](https://www.w3.org/TR/WCAG21/)
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [eMAG 3.1](https://emag.governoeletronico.gov.br/)
- [LBI 13.146/2015](http://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm)

---

## ✅ CHECKLIST RÁPIDO — CORREÇÕES

### P0 (Críticos)
- [ ] `#disclaimerModal`: adicionar `tabindex="-1"` em botões
- [ ] `#fileInput`: adicionar `tabindex="-1"`
- [ ] `.transparency-note h3`: mudar cor para `#0056b3`
- [ ] Links em `<p>`: adicionar `text-decoration: underline`
- [ ] `#uploadZone`: mover input para fora
- [ ] Form label: identificar e adicionar

### P1 (Altos)
- [ ] VLibras: envolver em `<aside role="complementary">`
- [ ] Nomes acessíveis: incluir texto visível em `aria-label`

### Validação
- [ ] AccessMonitor ≥9.0/10
- [ ] AccessibilityChecker ≥95
- [ ] WAVE 0 erros
- [ ] Teste teclado (Tab順)
- [ ] Teste leitor de tela (NVDA/JAWS)

---

## 📊 ESTIMATIVA DE IMPACTO

### **Após P0 (6.5h):**
- AccessMonitor: **9.0-9.2/10** (+0.3-0.5)
- AccessibilityChecker: **≥95** (+>5)
- Compliance WCAG AA: **✅ MÍNIMO**
- Risco legal: **🟡 BAIXO**

### **Após P1 (3h):**
- AccessMonitor: **9.3-9.5/10** (+0.6-0.8)
- AccessibilityChecker: **≥98** (+>8)
- Compliance WCAG AA: **✅ ROBUSTO**
- Risco legal: **🟢 MUITO BAIXO**

### **Após P2 (4.25h):**
- AccessMonitor: **9.5-9.8/10** (+0.8-1.1)
- AccessibilityChecker: **100**
- Compliance: **✅ WCAG AA + AAA parcial**
- Risco legal: **🟢 ZERO**

---

**Última atualização:** 12/02/2026
**Próxima auditoria:** Após implementação P0
**Responsável:** Fábio Treze
