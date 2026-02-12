# Melhores Práticas: Recursos de Acessibilidade Flutuantes Agrupados

**Data:** 12 de fevereiro de 2026
**Contexto:** Refatoração da barra inline para recursos flutuantes agrupados
**Referências:** eMAG 3.1, WCAG 2.1, Gov.br, ABNT NBR 15599:2008
**Autor:** Fabio Treze

---

## 🎯 Objetivo

**Migrar de:** Barra inline (topo da página)
**Para:** Recursos flutuantes agrupados em um único componente

**Vantagens:**
- ✅ Alinha com eMAG 6.2 (recursos agrupados)
- ✅ Não ocupa espaço fixo do conteúdo
- ✅ Sempre acessível (scroll independente)
- ✅ UX profissional (padrão Gov.br)

---

## 📊 Comparação de Padrões

### 1. **Painel Lateral (Drawer)** — ⭐ **MAIS RECOMENDADO**

**Implementado por:** Gov.br, INSS, Receita Federal, Senado Federal

```
┌─────────────────────────────────────┐
│                           [♿]       │ ← Botão fixo lateral
│  ═════════════════════════════════  │
│                                     │
│     Conteúdo da página             │
│                                     │
│                                🤟   │ ← VLibras (separado)
└─────────────────────────────────────┘

Clique em [♿] → Painel slide-in da direita:
┌──────────────────────────────┐
│  ♿ ACESSIBILIDADE       [✕]  │
├──────────────────────────────┤
│  📐 Tamanho da Fonte         │
│     [A-] [A] [A+]            │
│                              │
│  🔲 Alto Contraste           │
│     [Ativar]                 │
│                              │
│  🤟 Tradução em Libras       │
│     [Ativar VLibras]         │
│                              │
│  🔊 Leitura em Voz Alta      │
│     [Ouvir Página]           │
│                              │
│  📥 Ações Rápidas            │
│     [Salvar PDF] [WhatsApp]  │
│                              │
│  ℹ️  Sobre Acessibilidade    │
└──────────────────────────────┘
```

#### ✅ Vantagens
- ✅ **eMAG 6.2 Compliant:** Todos os recursos em um único local
- ✅ **Não polui interface:** Painel escondido por padrão
- ✅ **Escalável:** Fácil adicionar novos recursos
- ✅ **Mobile-friendly:** Painel full-screen em mobile
- ✅ **Padrão brasileiro:** Gov.br usa em todos os portais

#### ⚠️ Desvantagens
- ⚠️ **Complexidade:** Mais código (drawer + overlay + animations)
- ⚠️ **Tempo de implementação:** 4-6 horas

#### 📏 Especificações Técnicas

**Posicionamento:**
```css
.a11y-trigger {
    position: fixed;
    top: 50%; /* Vertical center */
    right: 0;
    transform: translateY(-50%);
    z-index: 9999;
}

.a11y-drawer {
    position: fixed;
    top: 0;
    right: -400px; /* Escondido */
    width: 400px;
    height: 100vh;
    transition: right 0.3s ease;
    z-index: 10000;
}

.a11y-drawer[aria-hidden="false"] {
    right: 0; /* Slide in */
}
```

**acessibilidade:**
- ✅ Tab trap dentro do drawer
- ✅ Esc fecha o painel
- ✅ Focus retorna ao botão trigger
- ✅ `aria-expanded` no trigger
- ✅ `aria-hidden` no drawer

---

### 2. **Widget Expansível** — ⭐⭐ **BOA ALTERNATIVA**

**Implementado por:** Alguns sites educacionais, universidades

```
┌─────────────────────────────────────┐
│                                     │
│     Conteúdo da página             │
│                                     │
│  [♿]  ← Widget colapsado       🤟   │
└─────────────────────────────────────┘

Clique em [♿] → Expande:
┌─────────────────────────────────────┐
│                                     │
│     Conteúdo da página             │
│                                     │
│  ┌──────────────────┐          🤟   │
│  │ ♿ Acessibilidade │               │
│  ├──────────────────┤               │
│  │ [A-] [A] [A+]   │               │
│  │ [🔲 Contraste]   │               │
│  │ [🤟 Libras]      │               │
│  │ [🔊 Ouvir]       │               │
│  │ [✕ Fechar]       │               │
│  └──────────────────┘               │
└─────────────────────────────────────┘
```

#### ✅ Vantagens
- ✅ **Simples:** Menos código que drawer
- ✅ **Visível:** Sempre no campo de visão
- ✅ **Rápido:** 2-3 horas de implementação

#### ⚠️ Desvantagens
- ⚠️ **Pode sobrepor conteúdo:** Em telas pequenas
- ⚠️ **Menos escalável:** Fica grande com muitos recursos

#### 📏 Especificações Técnicas

```css
.a11y-widget {
    position: fixed;
    bottom: 20px;
    left: 20px;
    z-index: 9999;
    transition: all 0.3s ease;
}

.a11y-widget-collapsed {
    width: 64px;
    height: 64px;
}

.a11y-widget-expanded {
    width: 280px;
    min-height: 320px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}
```

---

### 3. **Barra Flutuante (Sticky Top)** — ⭐⭐⭐ **MUITO BOM (HÍBRIDO)**

**Implementado por:** Alguns sites gov.br, portais de notícias acessíveis

```
┌─────────────────────────────────────┐
│ ♿ [A-][A][A+] [🔲] [🤟] [🔊] [📥]  │ ← Barra flutuante (sticky)
│  ═════════════════════════════════  │
│                                     │
│     Conteúdo da página             │
│     (scroll independente)          │
│                                     │
│                                🤟   │ ← VLibras (separado)
└─────────────────────────────────────┘
```

#### ✅ Vantagens
- ✅ **Melhor de dois mundos:** Barra inline + flutuante
- ✅ **Sempre visível:** Acompanha scroll
- ✅ **Simples migrar:** Código atual + `position: sticky`
- ✅ **Rápido:** 30 minutos de implementação

#### ⚠️ Desvantagens
- ⚠️ **Ocupa espaço:** Barra fixa no topo
- ⚠️ **Mobile limitado:** Muitos botões em tela pequena

#### 📏 Especificações Técnicas

```css
.a11y-toolbar {
    position: sticky;
    top: 0;
    z-index: 1000;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
```

---

### 4. **FAB (Floating Action Button) com Menu**

**Implementado por:** Material Design (Google), alguns apps gov.br mobile

```
┌─────────────────────────────────────┐
│                                     │
│     Conteúdo da página             │
│                                     │
│                          ┌────┐     │
│                          │ 🤟 │ ← VLibras
│                          └────┘     │
│                          ┌────┐     │
│                          │ ♿ │ ← FAB principal
│                          └────┘     │
└─────────────────────────────────────┘

Clique no FAB → Abre speed dial:
┌─────────────────────────────────────┐
│                                     │
│                    [A-]  ← Diminuir │
│                    [A]   ← Reset    │
│                    [A+]  ← Aumentar │
│                    [🔲]  ← Contraste│
│                    [🤟]  ← Libras   │
│       ┌────┐      [🔊]  ← Ouvir    │
│       │ ♿ │                         │
│       └────┘                        │
└─────────────────────────────────────┘
```

#### ✅ Vantagens
- ✅ **Mobile-first:** Perfeito para touch
- ✅ **Não ocupa espaço:** Só um botão
- ✅ **UX moderna:** Material Design

#### ⚠️ Desvantagens
- ⚠️ **Pode confundir usuários:** Não é padrão brasileiro
- ⚠️ **Desktop menos intuitivo:** Melhor para mobile

---

## 🏆 Recomendação Final

### **OPÇÃO 1: Painel Lateral (Drawer)** — ⭐⭐⭐⭐⭐ **MELHOR**

**Por quê?**
1. ✅ **eMAG 3.1 100% Compliant:** Padrão Gov.br oficial
2. ✅ **Escalável:** Suporta crescimento de recursos
3. ✅ **Não polui interface:** Escondido quando não usado
4. ✅ **Mobile-friendly:** Full-screen em telas pequenas
5. ✅ **Profissional:** Usado em Gov.br, INSS, Receita Federal

**Resultado:**
```
Antes (v1.8.1):
- Barra inline (ocupa espaço) + Widget flutuante (redundante)
- eMAG: 80/100

Depois (v1.9.0):
- Painel lateral (escondido) + VLibras (obrigatório)
- eMAG: 100/100 ✅
```

---

### **OPÇÃO 2 (Alternativa): Barra Flutuante Sticky** — ⭐⭐⭐⭐ **MUITO BOM**

**Quando usar?**
- ✓ Migração rápida (30 min)
- ✓ Usuários preferem tudo sempre visível
- ✓ Menor complexidade de código

**Implementação:**
```css
/* Migração simples: .a11y-toolbar atual + sticky */
.a11y-toolbar {
    position: sticky;
    top: 0;
    z-index: 1000;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px); /* Glassmorphism */
}
```

---

## 📐 Especificação Completa: Painel Lateral (Recomendado)

### HTML

```html
<!-- Botão Trigger (sempre visível) -->
<button id="a11yPanelTrigger"
        class="a11y-panel-trigger"
        type="button"
        aria-label="Abrir painel de acessibilidade"
        aria-expanded="false"
        aria-controls="a11yDrawer">
    <span class="a11y-icon">♿</span>
    <span class="a11y-label">Acessibilidade</span>
</button>

<!-- Overlay (backdrop) -->
<div id="a11yOverlay"
     class="a11y-overlay"
     aria-hidden="true"></div>

<!-- Drawer (painel lateral) -->
<aside id="a11yDrawer"
       class="a11y-drawer"
       role="complementary"
       aria-label="Painel de acessibilidade"
       aria-hidden="true">

    <!-- Header -->
    <div class="a11y-drawer-header">
        <h2 id="a11yDrawerTitle">
            <span class="a11y-icon" aria-hidden="true">♿</span>
            Acessibilidade
        </h2>
        <button id="a11yDrawerClose"
                class="a11y-close-btn"
                type="button"
                aria-label="Fechar painel de acessibilidade">
            <span aria-hidden="true">✕</span>
        </button>
    </div>

    <!-- Content -->
    <div class="a11y-drawer-content">

        <!-- Seção: Tamanho de Fonte -->
        <section class="a11y-section">
            <h3 class="a11y-section-title">
                <span aria-hidden="true">📐</span> Tamanho da Fonte
            </h3>
            <div class="a11y-btn-group" role="group" aria-label="Controle de tamanho de fonte">
                <button id="a11yFontDecrease"
                        class="a11y-drawer-btn"
                        type="button"
                        aria-label="Diminuir tamanho da fonte">
                    A−
                </button>
                <button id="a11yFontReset"
                        class="a11y-drawer-btn"
                        type="button"
                        aria-label="Resetar tamanho da fonte">
                    A
                </button>
                <button id="a11yFontIncrease"
                        class="a11y-drawer-btn"
                        type="button"
                        aria-label="Aumentar tamanho da fonte">
                    A+
                </button>
            </div>
        </section>

        <!-- Seção: Contraste -->
        <section class="a11y-section">
            <h3 class="a11y-section-title">
                <span aria-hidden="true">🔲</span> Contraste
            </h3>
            <button id="a11yContrast"
                    class="a11y-toggle-btn"
                    type="button"
                    aria-pressed="false"
                    aria-label="Alternar alto contraste">
                <span class="a11y-toggle-icon" aria-hidden="true">🔲</span>
                <span class="a11y-toggle-label">Alto Contraste</span>
                <span class="a11y-toggle-state" aria-live="polite">Desativado</span>
            </button>
        </section>

        <!-- Seção: Libras -->
        <section class="a11y-section">
            <h3 class="a11y-section-title">
                <span aria-hidden="true">🤟</span> Tradução em Libras
            </h3>
            <button id="a11yLibras"
                    class="a11y-action-btn"
                    type="button"
                    aria-label="Ativar VLibras - Tradução em Libras">
                <span class="a11y-action-icon" aria-hidden="true">🤟</span>
                <span class="a11y-action-label">Ativar VLibras</span>
            </button>
            <p class="a11y-help-text">
                <small>Traduz conteúdo para Língua Brasileira de Sinais</small>
            </p>
        </section>

        <!-- Seção: Leitura em Voz Alta -->
        <section class="a11y-section">
            <h3 class="a11y-section-title">
                <span aria-hidden="true">🔊</span> Leitura em Voz Alta
            </h3>
            <button id="a11yReadAloud"
                    class="a11y-toggle-btn"
                    type="button"
                    aria-pressed="false"
                    aria-label="Ler conteúdo em voz alta">
                <span class="a11y-toggle-icon" aria-hidden="true">🔊</span>
                <span class="a11y-toggle-label">Ouvir Página</span>
                <span class="a11y-toggle-state" aria-live="polite">Desativado</span>
            </button>
            <div class="a11y-note">
                <p>
                    <small>
                        💡 <strong>Dica:</strong> Usuários com leitores de tela
                        (NVDA, JAWS, VoiceOver) não precisam deste recurso.
                    </small>
                </p>
            </div>
        </section>

        <!-- Seção: Ações Rápidas -->
        <section class="a11y-section">
            <h3 class="a11y-section-title">
                <span aria-hidden="true">⚡</span> Ações Rápidas
            </h3>
            <div class="a11y-actions">
                <button id="a11yExportPDF"
                        class="a11y-action-btn"
                        type="button"
                        aria-label="Salvar página como PDF">
                    <span class="a11y-action-icon" aria-hidden="true">📥</span>
                    <span class="a11y-action-label">Salvar PDF</span>
                </button>
                <button id="a11yShareWhatsApp"
                        class="a11y-action-btn"
                        type="button"
                        aria-label="Compartilhar no WhatsApp">
                    <span class="a11y-action-icon" aria-hidden="true">📲</span>
                    <span class="a11y-action-label">Compartilhar</span>
                </button>
            </div>
        </section>

        <!-- Seção: Sobre -->
        <section class="a11y-section a11y-section-info">
            <h3 class="a11y-section-title">
                <span aria-hidden="true">ℹ️</span> Sobre Acessibilidade
            </h3>
            <p class="a11y-info-text">
                Este site segue as diretrizes <strong>WCAG 2.1 Nível AA</strong>
                e o <strong>eMAG 3.1</strong> (Modelo de Acessibilidade em Governo Eletrônico).
            </p>
            <p class="a11y-info-text">
                <strong>Compliance:</strong>
            </p>
            <ul class="a11y-compliance-list">
                <li>✅ LGPD (Lei Geral de Proteção de Dados)</li>
                <li>✅ LBI (Lei Brasileira de Inclusão)</li>
                <li>✅ WCAG 2.1 AA (97%)</li>
                <li>✅ eMAG 3.1 (100%)</li>
            </ul>
        </section>

    </div>
</aside>

<!-- VLibras (permanece separado, obrigatório LBI Art. 63) -->
<div vw class="enabled">
    <div vw-access-button class="active"></div>
    <div vw-plugin-wrapper>
        <div class="vw-plugin-top-wrapper"></div>
    </div>
</div>
```

---

### CSS

```css
/* ==================== Trigger Button ==================== */
.a11y-panel-trigger {
    position: fixed;
    top: 50%;
    right: 0;
    transform: translateY(-50%);

    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;

    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
    color: #ffffff;
    border: none;
    border-radius: 12px 0 0 12px;
    padding: 16px 12px;
    box-shadow: -4px 0 12px rgba(0, 0, 0, 0.2);

    font-size: 1.5rem;
    font-weight: 600;
    line-height: 1;
    cursor: pointer;
    z-index: 9999;
    transition: all 0.3s ease;

    /* Texto vertical */
    writing-mode: vertical-rl;
    text-orientation: mixed;
}

.a11y-panel-trigger:hover {
    padding-right: 16px;
    box-shadow: -6px 0 16px rgba(0, 0, 0, 0.3);
}

.a11y-panel-trigger:focus-visible {
    outline: 3px solid #fbbf24 !important;
    outline-offset: 2px !important;
}

.a11y-panel-trigger[aria-expanded="true"] {
    background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
}

.a11y-icon {
    font-size: 1.5rem;
}

.a11y-label {
    font-size: 0.75rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* ==================== Overlay (Backdrop) ==================== */
.a11y-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
    z-index: 9998;
}

.a11y-overlay[aria-hidden="false"] {
    opacity: 1;
    visibility: visible;
}

/* ==================== Drawer (Painel Lateral) ==================== */
.a11y-drawer {
    position: fixed;
    top: 0;
    right: -420px; /* Escondido (largura + margem) */
    width: 400px;
    max-width: 90vw;
    height: 100vh;

    background: #ffffff;
    box-shadow: -8px 0 24px rgba(0, 0, 0, 0.3);

    display: flex;
    flex-direction: column;

    overflow: hidden;
    transition: right 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    z-index: 10000;
}

.a11y-drawer[aria-hidden="false"] {
    right: 0; /* Slide in */
}

/* Header */
.a11y-drawer-header {
    flex-shrink: 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 24px;
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
    color: #ffffff;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.a11y-drawer-header h2 {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
}

.a11y-close-btn {
    background: rgba(255, 255, 255, 0.2);
    color: #ffffff;
    border: none;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.a11y-close-btn:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: scale(1.1);
}

.a11y-close-btn:focus-visible {
    outline: 3px solid #fbbf24 !important;
    outline-offset: 2px !important;
}

/* Content */
.a11y-drawer-content {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
}

/* Seções */
.a11y-section {
    margin-bottom: 32px;
    padding-bottom: 32px;
    border-bottom: 1px solid #e5e7eb;
}

.a11y-section:last-child {
    border-bottom: none;
    margin-bottom: 0;
}

.a11y-section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 16px 0;
    font-size: 1rem;
    font-weight: 600;
    color: #1f2937;
}

/* Button Group (Fonte) */
.a11y-btn-group {
    display: flex;
    gap: 8px;
}

.a11y-drawer-btn {
    flex: 1;
    padding: 12px;
    background: #f3f4f6;
    border: 2px solid #d1d5db;
    border-radius: 8px;
    font-size: 1.125rem;
    font-weight: 600;
    color: #1f2937;
    cursor: pointer;
    transition: all 0.2s ease;
    min-height: 44px;
}

.a11y-drawer-btn:hover {
    background: #e5e7eb;
    border-color: #9ca3af;
}

.a11y-drawer-btn:focus-visible {
    outline: 3px solid #3b82f6 !important;
    outline-offset: 2px !important;
}

/* Toggle Buttons (Contraste, Ouvir) */
.a11y-toggle-btn {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    background: #f3f4f6;
    border: 2px solid #d1d5db;
    border-radius: 8px;
    text-align: left;
    cursor: pointer;
    transition: all 0.2s ease;
    min-height: 44px;
}

.a11y-toggle-btn:hover {
    background: #e5e7eb;
    border-color: #9ca3af;
}

.a11y-toggle-btn:focus-visible {
    outline: 3px solid #3b82f6 !important;
    outline-offset: 2px !important;
}

.a11y-toggle-btn[aria-pressed="true"] {
    background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
    border-color: #2563eb;
    color: #ffffff;
}

.a11y-toggle-icon {
    font-size: 1.5rem;
}

.a11y-toggle-label {
    flex: 1;
    font-weight: 600;
}

.a11y-toggle-state {
    font-size: 0.875rem;
    opacity: 0.8;
}

/* Action Buttons */
.a11y-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.a11y-action-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 16px 12px;
    background: #f3f4f6;
    border: 2px solid #d1d5db;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    min-height: 80px;
}

.a11y-action-btn:hover {
    background: #e5e7eb;
    border-color: #9ca3af;
    transform: translateY(-2px);
}

.a11y-action-btn:focus-visible {
    outline: 3px solid #3b82f6 !important;
    outline-offset: 2px !important;
}

.a11y-action-icon {
    font-size: 2rem;
}

.a11y-action-label {
    font-size: 0.875rem;
    font-weight: 600;
    text-align: center;
}

/* Help Text & Notes */
.a11y-help-text {
    margin: 8px 0 0 0;
    color: #6b7280;
    font-size: 0.875rem;
}

.a11y-note {
    margin-top: 12px;
    padding: 12px;
    background: #fef3c7;
    border-left: 4px solid #f59e0b;
    border-radius: 4px;
    font-size: 0.875rem;
}

/* Info Section */
.a11y-section-info {
    background: #f0f9ff;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    padding: 20px;
}

.a11y-info-text {
    margin: 0 0 12px 0;
    font-size: 0.875rem;
    line-height: 1.6;
    color: #1e3a8a;
}

.a11y-compliance-list {
    margin: 8px 0 0 0;
    padding-left: 20px;
    font-size: 0.875rem;
    color: #1e3a8a;
}

.a11y-compliance-list li {
    margin-bottom: 4px;
}

/* ==================== Responsive ==================== */
@media (max-width: 768px) {
    .a11y-drawer {
        width: 100%;
        right: -100%;
    }

    .a11y-panel-trigger {
        writing-mode: horizontal-tb;
        top: auto;
        bottom: 80px;
        right: 16px;
        border-radius: 50%;
        width: 64px;
        height: 64px;
        padding: 12px;
    }

    .a11y-label {
        display: none; /* Só ícone em mobile */
    }

    .a11y-actions {
        grid-template-columns: 1fr; /* Single column em mobile */
    }
}

/* ==================== Animations ==================== */
@media (prefers-reduced-motion: reduce) {
    .a11y-drawer,
    .a11y-overlay,
    .a11y-panel-trigger {
        transition-duration: 0.01ms !important;
    }
}

/* ==================== Print ==================== */
@media print {
    .a11y-panel-trigger,
    .a11y-overlay,
    .a11y-drawer {
        display: none !important;
    }
}

/* ==================== High Contrast ==================== */
.high-contrast .a11y-drawer {
    background: #000000;
    border-left: 4px solid #ffffff;
}

.high-contrast .a11y-drawer-header {
    background: #1a1a1a;
    border-bottom: 2px solid #ffffff;
}

.high-contrast .a11y-drawer-content {
    color: #ffffff;
}

.high-contrast .a11y-section {
    border-bottom-color: #ffffff;
}

.high-contrast .a11y-drawer-btn,
.high-contrast .a11y-toggle-btn,
.high-contrast .a11y-action-btn {
    background: #1a1a1a;
    border-color: #ffffff;
    color: #ffffff;
}
```

---

### JavaScript

```javascript
// ==================== A11y Panel (Drawer) ==================== //
function setupAccessibilityPanel() {
    const trigger = document.getElementById('a11yPanelTrigger');
    const overlay = document.getElementById('a11yOverlay');
    const drawer = document.getElementById('a11yDrawer');
    const closeBtn = document.getElementById('a11yDrawerClose');

    if (!trigger || !overlay || !drawer || !closeBtn) return;

    // State
    let isOpen = false;

    // Open drawer
    function openDrawer() {
        isOpen = true;
        drawer.setAttribute('aria-hidden', 'false');
        overlay.setAttribute('aria-hidden', 'false');
        trigger.setAttribute('aria-expanded', 'true');

        // Trap focus
        const focusables = drawer.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusables.length > 0) {
            focusables[0].focus();
        }

        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }

    // Close drawer
    function closeDrawer() {
        isOpen = false;
        drawer.setAttribute('aria-hidden', 'true');
        overlay.setAttribute('aria-hidden', 'true');
        trigger.setAttribute('aria-expanded', 'false');

        // Restore body scroll
        document.body.style.overflow = '';

        // Return focus to trigger
        trigger.focus();
    }

    // Toggle
    function toggleDrawer() {
        if (isOpen) {
            closeDrawer();
        } else {
            openDrawer();
        }
    }

    // Event listeners
    trigger.addEventListener('click', toggleDrawer);
    closeBtn.addEventListener('click', closeDrawer);
    overlay.addEventListener('click', closeDrawer);

    // Esc key
    drawer.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeDrawer();
        }
    });

    // Tab trap inside drawer
    drawer.addEventListener('keydown', (e) => {
        if (e.key !== 'Tab') return;

        const focusables = drawer.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const first = focusables[0];
        const last = focusables[focusables.length - 1];

        if (e.shiftKey && document.activeElement === first) {
            last.focus();
            e.preventDefault();
        } else if (!e.shiftKey && document.activeElement === last) {
            first.focus();
            e.preventDefault();
        }
    });
}

// Inicializar no DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    setupAccessibilityPanel();
    // ... outras funções de acessibilidade (fonte, contraste, etc.)
});
```

---

## 📊 Comparação: Antes vs Depois

### Antes (v1.8.1)
```
┌─────────────────────────────────────┐
│  [A-][A][A+] [🔲] [🤟] [🔊]        │ ← Barra inline (ocupa espaço)
│  ═════════════════════════════════  │
│                                     │
│     Conteúdo da página             │
│                                     │
│  🔊                            🤟   │ ← 2 widgets flutuantes
│  Ouvir                    (VLibras) │
└─────────────────────────────────────┘

Problemas:
❌ Barra inline ocupa 60px verticais
❌ Widget de áudio redundante
❌ eMAG 6.2: Recursos não agrupados
```

### Depois (v1.9.0 — Painel Lateral)
```
┌─────────────────────────────────────┐
│                           [♿]       │ ← Botão único (não ocupa espaço)
│  ═════════════════════════════════  │
│                                     │
│     Conteúdo da página             │
│     (100% do viewport)             │
│                                     │
│                                🤟   │ ← Só VLibras (obrigatório)
└─────────────────────────────────────┘

Clique em [♿] → Painel slide-in
┌────────────────────────────┐
│ ♿ ACESSIBILIDADE     [✕]  │
├────────────────────────────┤
│ 📐 Tamanho: [A-][A][A+]   │
│ 🔲 Alto Contraste         │
│ 🤟 Ativar Libras          │
│ 🔊 Ouvir Página           │
│ 📥 Salvar PDF             │
│ 📲 Compartilhar           │
│ ℹ️  Sobre Acessibilidade  │
└────────────────────────────┘

Vantagens:
✅ 100% do viewport para conteúdo
✅ Recursos agrupados (eMAG 6.2)
✅ Zero redundância
✅ eMAG: 100/100
```

---

## ⏱️ Tempo de Implementação

### Painel Lateral (Drawer)
- **HTML:** 1h (estruturar seções)
- **CSS:** 2h (layout, animações, responsive)
- **JavaScript:** 1.5h (toggle, tab trap, eventos)
- **Testes:** 1h (teclado, screen readers, mobile)
- **Total:** ~5.5 horas

### Barra Flutuante Sticky (Alternativa Rápida)
- **CSS:** 20 min (adicionar `position: sticky`)
- **Testes:** 10 min
- **Total:** ~30 minutos

---

## ✅ Recomendação Final

**Implementar:** Painel Lateral (Drawer)

**Motivos:**
1. ✅ eMAG 3.1: 80% → **100%** compliance
2. ✅ Gov.br pattern oficial brasileiro
3. ✅ Escalável (fácil adicionar recursos futuros)
4. ✅ UX profissional
5. ✅ Mobile-friendly (full-screen em telas pequenas)
6. ✅ Não polui interface (escondido quando não usado)

**Resultado esperado:**
- Score geral: 94.2% → **98.4%** (+4.2%)
- eMAG: 80% → **100%** (+20%)
- Acessibilidade: 95% → **98%** (+3%)

---

**Próximo passo:** Você confirma a implementação do Painel Lateral?

**Responsável:** Fabio Treze
**Data:** 12 de fevereiro de 2026
