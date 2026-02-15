# Problemas Conhecidos e Limitações — NossoDireito

> **Status:** 🟢 Ativo
> **Versão:** 1.12.0 | **Atualizado:** 2026-02-15
> **Escopo:** Bugs, limitações técnicas, workarounds e trade-offs conhecidos
> **Absorve:** VLIBRAS_LIMITATIONS (mobile + CSP)

---

## 📱 1. MOBILE

### 🚨 VLibras Não Funciona em iPhone/Android

**Problema:**
O plugin oficial VLibras (https://vlibras.gov.br) não funciona em navegadores mobile.

**Causas técnicas:**
- Custom Elements v1 incompatíveis com Safari iOS <16.4 e Android WebView antigo
- Bugs `speechSynthesis.speak()` em iOS
- WebAssembly ~2MB com performance ruim em ARM <2018 e timeout em 3G/4G
- CORS do Safari mobile bloqueia recursos de `*.vlibras.gov.br`

**Status oficial:** GitHub Issues #47, #82, #134 — reconhecido, sem previsão de correção.

**Impacto:**
- ⚠️ Libras **INDISPONÍVEL** em mobile
- ✅ TTS, alto contraste, fonte, teclado — tudo funciona normalmente

**Workarounds para usuários:**
- **Desktop:** Firefox, Chrome ou Edge (100% VLibras)
- **Mobile:** [Hand Talk](https://handtalk.me/br/aplicativo/) (gratuito, 4.8★) | [ProDeaf](https://play.google.com/) (R$9,90/mês) | [Rybená](https://play.google.com/) (gratuito) | [iLibras](https://apps.apple.com/) (iOS, R$24,90)
- **TTS:** Botão "🔊 Ouvir" funciona em todos dispositivos

**Workarounds para devs:**
- Detectar mobile e ocultar botão VLibras (evitar confusão)
- Lazy load VLibras apenas em desktop (economiza 2MB, +5 pts Lighthouse)

### Trade-off CSP para VLibras

VLibras usa Unity WebAssembly que requer `eval()` — incompatível com CSP restritivo.

**Decisão:** Priorizamos acessibilidade governamental — adicionamos exceções CSP:
- `'unsafe-eval'` + `'wasm-unsafe-eval'`
- `worker-src` inclui `vlibras.gov.br`, `*.vlibras.gov.br`
- `connect-src` inclui `data:` para recursos inline
- `accelerometer=(self)`, `gyroscope=(self)` no Permissions-Policy

**Mitigações de segurança aplicadas:**
- Host validation (exact match), Rate limiting (120 req/min), HSTS preload, COEP require-corp, X-Content-Type-Options nosniff, Referrer-Policy no-referrer

---

### ⚠️ TTS (Ouvir) Com Sotaque Robótico

**Problema:**
A funcionalidade de "Ouvir" (Text-to-Speech) usa a **Web Speech API nativa** do navegador, que pode soar robótica em alguns dispositivos.

**Causa:**
- **iOS:** Usa motor Siri (boa qualidade)
- **Android:** Varia por fabricante
  - ✅ Samsung/Google: boa qualidade (Google TTS)
  - ⚠️ Xiaomi/Huawei: qualidade média (TTS genérico)
  - ❌ Dispositivos antigos: muito robótico

**Workaround Android:**
1. Instale [Google Text-to-Speech](https://play.google.com/store/apps/details?id=com.google.android.tts)
2. Vá em Configurações → Idioma → Saída de texto em voz
3. Selecione "Google Text-to-Speech" como padrão
4. Baixe voz "Português (Brasil)" de alta qualidade

**Status:**
🟢 **Limitação técnica** — Não há solução no navegador (depende do SO)

---

### 📶 Performance em Conexões 3G Lentas

**Problema:**
Site carrega lento em redes 3G/2G devido ao tamanho do JavaScript (115 KB).

**Impacto:**
- ⚠️ LCP (Largest Contentful Paint): ~4.5s em 3G (meta: <2.5s)
- ⚠️ TTI (Time to Interactive): ~6.2s em 3G (meta: <3.8s)

**Mitigação Atual:**
- ✅ Service Worker: cache offline após primeiro acesso
- ✅ Cloudflare CDN: compressão Brotli (-30% tamanho)
- ✅ Lazy load de PDF preview

**Roadmap:**
- 🔜 v1.6.0: Minificação app.js com Terser (-35 KB)
- 🔜 v1.6.0: Critical CSS inline (-15 KB primeira carga)
**Status:**
🟡 **Em melhoria** — v1.6.0 trará otimizações

---

## 🌐 2. LINKS EXTERNOS

### 🔗 Links Gov.br Podem Mudar Sem Aviso

**Problema:**
Órgãos governamentais reestruturadas sites sem configurar redirects (HTTP 301/302), quebrando links.

**Exemplos Recentes:**
- ❌ INSS mudou de `www.inss.gov.br` → `meu.inss.gov.br` (jan 2026)
- ❌ Receita Federal mudou estrutura de URLs (nov 2025)
- ❌ MDS reorganizou benefícios (dez 2025)

**Mitigação:**
- ✅ **Validação periódica** automática (validate_sources.py)
- ✅ **Fontes oficiais** priorizadas (planalto.gov.br, senado.leg.br)
- ✅ **Múltiplas fontes** por benefício (backup links)
- ✅ **Archive.org** como fallback (quando possível)

**Como Reportar:**
Se encontrar link quebrado:
1. **GitHub Issue:** https://github.com/fabiotreze/nossodireito/issues
2. **Email:** fabiotreze@gmail.com (assunto: "Link Quebrado")

**Tempo de Resposta:**
- 🔥 **Crítico** (links gov.br principais): 24 horas
- ⚠️ **Médio** (links secundários): 48-72 horas

**Status:**
🟢 **Monitorado** — Validação automática ativa

---

### 🔒 CONFAZ (confaz.fazenda.gov.br) com SSL Inválido

**Problema:**
Site do CONFAZ (Conselho Nacional de Política Fazendária) usa **certificado SSL auto-assinado** ou proxy com problema.

**Impacto:**
- ⚠️ Navegadores mostram aviso "Sua conexão não é privada"
- ⚠️ Script `validate_sources.py` falha na verificação SSL

**Workaround no Código:**
```python
# validate_sources.py linha 85
SSL_EXCEPTION_DOMAINS = [
    "confaz.fazenda.gov.br",
    "www.confaz.fazenda.gov.br"
]
```

**Segurança:**
- ✅ SSL verify **DESABILITADO** apenas para esse domínio específico
- ✅ Todos os outros domínios usam SSL verify **ATIVADO**
- ⚠️ Trade-off: Validação de link vs Segurança absoluta

**Status oficial:**
🟡 **Problema do CONFAZ** — Reportado, sem previsão de correção

**Link Seguro Alternativo:**
Use Planalto.gov.br para leis CONFAZ (mais confiável):
https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc.htm

**Status:**
🟡 **Monitorado** — Problema externo (CONFAZ)

---

## 🔍 3. BUSCA

### ❌ Alguns Termos Não Encontram Benefícios

**Problema:**
O motor de busca (`matching_engine.json`) não cobre **TODOS** os sinônimos possíveis.

**Exemplos:**
- ❌ "Aposentadoria PcD" → **NÃO encontra** (use "LOAS" ou "BPC")
- ❌ "Cadeirante" → **NÃO encontra** (use "mobilidade reduzida")
- ❌ "Autista" → **Acha**, mas poderia achar mais (faltam sinônimos)

**Workaround:**
Use **termos oficiais** das leis:
- ✅ "LOAS" em vez de "aposentadoria PcD"
- ✅ "Passe Livre" em vez de "transporte gratuito"
- ✅ "Isenção IPI" em vez de "desconto carro"

**Melhoria Contínua:**
- 🆕 v1.5.0: +60 keywords (prouni, irpf, bolsa família)
- 🔜 v1.6.0: +100 keywords planejados (sinônimos regionais)

**Como Sugerir Keywords:**
1. **GitHub Issue:** https://github.com/fabiotreze/nossodireito/issues
2. **Template:** "Busquei `[termo]`, deveria achar `[benefício]`"

**Status:**
🟢 **Em evolução** — Colaboração da comunidade

---

### ⚠️ Busca Por UF Não Funciona

**Problema:**
Buscar "IPVA SP" ou "Passe Livre RJ" **NÃO filtra por estado**.

**Exemplo:**
- Busca: "IPVA SP"
- Resultado: Mostra IPVA geral (sem filtro SP)

**Causa:**
Motor de busca atual é **keyword-based**, não entende geografia.

**Workaround:**
1. Busque "IPVA"
2. Abra benefício
3. Use dropdown "🚗 Consulta Detalhada - IPVA por Estado"
4. Selecione "SP"

**Status:**
🟡 **Planejado**

---

## 💾 4. OFFLINE

### 📦 Cache Offline Limitado a 10 MB

**Problema:**
Service Worker tem limite de **10 MB** em alguns navegadores (especialmente iOS).

**Impacto Atual:**
- ✅ **Seguro:** Site usa ~2 MB (3,111 linhas JSON + 115 KB JS + 60 KB CSS)
- ✅ **Margem:** 8 MB disponíveis (400% headroom)

**Futuro:**
- ⚠️ Se adicionar 50+ benefícios no futuro, pode ultrapassar 10 MB

**Workaround Planejado:**
- Lazy loading de categorias (carregar JSON on-demand)
- IndexedDB para storage ilimitado

**Status:**
🟢 **Sob controle** — Não é problema agora

---

### ❌ Service Worker Não Atualiza Imediatamente

**Problema:**
Após deploy, usuários podem ver **versão antiga** do site por até 24 horas.

**Causa:**
Service Worker usa estratégia **Cache First** (offline-first).

**Workaround Temporário:**
1. Ctrl+Shift+R (hard reload)
2. Ou: F12 → Application → Service Workers → "Unregister"

**Solução Permanente (v1.6.0):**
```javascript
// sw.js — Update notification
self.addEventListener('controllerchange', () => {
  if (confirm('Nova versão disponível! Recarregar?')) {
    window.location.reload();
  }
});
```

**Status:**
🔜 **Planejado** — v1.6.0 (mar 2026)

---

## 🔐 5. PRIVACIDADE

### 📡 VLibras Carrega Script Externo (vlibras.gov.br)

**Problema:**
VLibras carrega JavaScript de `https://vlibras.gov.br/app/vlibras-plugin.js` (domínio externo).

**Comportamento:**
- ✅ **Nenhum dado pessoal enviado** ao Gov.br
- ✅ Apenas assets são baixados (imagens avatar, WASM)
- ⚠️ **Cookies de sessão** podem ser criados por vlibras.gov.br

**Mitigação:**
- ✅ CSP (Content Security Policy) **whitelist explícita**:
  ```
  script-src https://vlibras.gov.br https://*.vlibras.gov.br
  ```
- ✅ **SameSite=Lax** cookies (bloqueio cross-site tracking)
- ✅ **Disclaimer** no modal de aviso legal

**LGPD:**
- ✅ **Compliant:** Nenhum dado pessoal coletado
- ✅ **Base legal:** Consentimento implícito (uso voluntário de VLibras)

**Status:**
🟢 **Conforme LGPD** — Auditado em dic 2025

---

### 🍪 Nenhum Cookie de Terceiros

**Status:**
✅ **Zero cookies** além de VLibras (opcional)

**Verificação:**
```javascript
// Abra F12 → Console
document.cookie
// Resultado: "" (vazio) ou apenas vlibras sessão
```

---

## ⚙️ 6. FUNCIONALIDADES AUSENTES

### ❌ Compartilhamento Social (Facebook, Twitter, WhatsApp)

**Status:**
🔜 **Planejado**

**Workaround:**
Copie URL manualmente e cole em rede social.

---

### ❌ Filtros Por Categoria (Tag Search)

**Problema:**
Não há como filtrar benefícios por tag (ex: "educação", "saúde", "transporte").

**Workaround:**
Use busca textual: "educação", "saúde", etc.

**Status:**
🔜 **Planejado** — v1.6.0

---

### ❌ Print-Friendly View (Versão Impressão)

**Problema:**
Imprimir (Ctrl+P) inclui cabeçalho, rodapé e toolbar (desperdício papel).

**Workaround:**
Use "Salvar como PDF" no navegador (mais econômico).

**Status:**
🔜 **Planejado**

---

### ❌ Modo Escuro (Dark Mode)

**Status:**
🔜 **Planejado**

**Workaround:**
Use extensão de navegador:
- Chrome: [Dark Reader](https://chrome.google.com/webstore/detail/dark-reader/eimadpbcbfnmbkopoojfekhnkhdbieeh)
- Firefox: [Dark Reader](https://addons.mozilla.org/pt-BR/firefox/addon/darkreader/)

---

## 🐛 7. BUGS CONHECIDOS

### 🐛 PDF Preview Não Funciona em iOS Safari

**Problema:**
Botão "👁️ Preview Laudo" não abre modal em Safari iOS.

**Causa:**
Safari iOS bloqueia `<object>` embed de PDFs.

**Workaround:**
Use Chrome iOS ou Edge iOS (suporte melhor a PDFs).

**Status:**
🟡 **Em investigação** — Pode ser limitação permanente do Safari

---

### 🐛 Alto Contraste Não Aplica em Imagens

**Problema:**
Modo alto contraste muda cores de texto/fundo, mas **não** inverte cores de images.

**Impacto:**
- ⚠️ Emojis permanecem com cores originais
- ⚠️ Logos ficam visualmente desconexos do fundo preto

**Workaround:**
```css
/* Se virar problema, adicionar: */
html.high-contrast img {
  filter: invert(1) hue-rotate(180deg);
}
```

**Status:**
🔵 **Baixa prioridade** — Emojis ainda legíveis

---

## 📊 8. LIMITAÇÕES DE ESCALA

### ⚠️ Benefícios > 50 Pode Tornar Busca Lenta

**Problema Futuro:**
Motor de busca atual é **O(n)** linear (percorre todos benefícios).

**Impacto Projetado:**
- ✅ 20 benefícios: ~5 ms
- ✅ 50 benefícios: ~12 ms (OK)
- ⚠️ 100 benefícios: ~25 ms (perceptível)
- ❌ 500 benefícios: ~120 ms (lento)

**Solução Futura:**
- Índice invertido (keyword → benefício ID)
- Trie data structure para autocomplete
- Web Workers para busca paralela

**Status:**
🟢 **Não é problema agora** (apenas 20 benefícios)

---

## 📞 REPORTAR NOVOS PROBLEMAS

### Como Reportar Bugs ou Limitações:

**Opção 1: GitHub Issues (Recomendado)**
https://github.com/fabiotreze/nossodireito/issues/new

**Template:**
```markdown
**Problema:** [Descrição breve]
**Passos para reproduzir:**
1. Abrir site
2. Clicar em [...]
3. Ver erro [...]

**Comportamento esperado:** [O que deveria acontecer]
**Comportamento atual:** [O que acontece de fato]

**Ambiente:**
- SO: [Windows 11 / macOS 14 / Android 13]
- Navegador: [Chrome 120 / Safari 17]
- Dispositivo: [Desktop / iPhone 15 Pro / Galaxy S23]
- Screenshot: [anexar se possível]
```

**Opção 2: Email**
fabiotreze@gmail.com (assunto: "Bug NossoDireito")

**Tempo de Resposta:**
- 🔥 **Crítico** (site fora do ar): 4 horas
- ⚠️ **Alto** (funcionalidade quebrada): 24 horas
- 🔵 **Médio/Baixo**: 48-72 horas

---

## 🔄 CRONOGRAMA DE ATUALIZAÇÕES

**Revisão deste documento:** **Mensal** (toda 1ª segunda-feira)
**Próxima revisão:** 03 de março de 2026

---

**Última Atualização:** 11 de fevereiro de 2026
**Responsável:** Fábio Treze (fabiotreze@gmail.com)
**Licença:** MIT
**Versão:** 1.0.0
