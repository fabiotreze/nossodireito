# Problemas Conhecidos e Limitações — NossoDireito

> **Status:** 🟢 Ativo
> **Versão:** 1.15.0 | **Atualizado:** 2026-05-17
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
- ⏳ Futuro: Minificação app.js com Terser (-35 KB)
- ⏳ Futuro: Critical CSS inline (-15 KB primeira carga)
**Status:**
🟡 **Aceitável** — otimizações planejadas para versões futuras

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
2. **Email:** 38567767+fabiotreze@users.noreply.github.com (assunto: "Link Quebrado")

**Resposta:**
Reports serão analisados assim que possível. Não há SLA formal — projeto mantido por uma pessoa.

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

### ⚠️ Cobertura de Sinônimos em Evolução

**Contexto:**
O motor de busca (`matching_engine.json` + `dicionario_pcd.json`) cobre ~1.300 termos mas não todos os sinônimos regionais.

**Exemplos corrigidos em v1.14.4:**
- ✅ "Aposentadoria PcD" → encontra Aposentadoria Especial PcD
- ✅ "Cadeirante" → encontra BPC, Transporte, Isenção IPVA/IPI, Tecnologia Assistiva
- ✅ "Desconto carro" → encontra Isenção IPI e IPVA
- ✅ "Transporte gratuito" → encontra Transporte
- ✅ "Cadeira de rodas" → encontra Tecnologia Assistiva, SUS, Transporte

**Ainda limitado:**
- ⚠️ Sinônimos regionais muito específicos (gírias locais)
- ⚠️ Busca por UF não filtra geograficamente

**Melhoria Contínua:**
- 🆕 v1.5.0: +60 keywords (prouni, irpf, bolsa família)
- 🆕 v1.14.4: +40 keywords (cadeirante, paraplégico, deficiente visual, prótese, etc.)

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

### ✅ Service Worker Atualização Automática

**Status:**
🟢 **Implementado** — v1.14.0+

- Service Worker usa estratégia **Network-First** para assets do mesmo domínio
- `sw-register.js` monitora `controllerchange` e faz `location.reload()` automático
- Polling de atualização a cada 60 segundos via `reg.update()`
- Guard contra reload infinito (`_swReloading` flag)
```

**Status:**
� **Implementado** — v1.14.0+

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

### ✅ Compartilhamento Social (WhatsApp)

**Status:**
🟢 **Implementado** — v1.14.4

Compartilhamento via WhatsApp disponível em cards de direitos, análise de documentos e checklist.

---

### ❌ Filtros Por Categoria (Tag Search)

**Problema:**
Não há como filtrar benefícios por tag (ex: "educação", "saúde", "transporte").

**Workaround:**
Use busca textual: "educação", "saúde", etc.

**Status:**
⏳ **Futuro** — sem versão definida

---

### ✅ Print-Friendly View (Versão Impressão)

**Status:**
🟢 **Implementado** — v1.14.0+

Estilos `@media print` otimizam layout para impressão com 4 modos de exportação.

---

### ✅ Modo Escuro (Dark Mode)

**Status:**
🟢 **Implementado** — v1.14.0+

Dark mode automático via `@media (prefers-color-scheme: dark)` respeita configuração do sistema operacional.

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

### ✅ Alto Contraste Aplica Filter em Imagens

**Resolvido em v1.14.4:**
CSS inclui `html.high-contrast img { filter: brightness(1.1) contrast(1.2); }` — melhora legibilidade de imagens sem inverter cores (que tornaria fotos ilegíveis).

**Status:**
🟢 **Resolvido** — Implementado via CSS filter

---

## 📊 8. LIMITAÇÕES DE ESCALA

### ⚠️ Benefícios > 50 Pode Tornar Busca Lenta

**Problema Futuro:**
Motor de busca atual é **O(n)** linear (percorre todos benefícios).

**Impacto Projetado:**
- ✅ 30 categorias: ~8 ms
- ✅ 50 categorias: ~12 ms (OK)
- ⚠️ 100 categorias: ~25 ms (perceptível)
- ❌ 500 categorias: ~120 ms (lento)

**Solução Futura:**
- Índice invertido (keyword → benefício ID)
- Trie data structure para autocomplete
- Web Workers para busca paralela

**Status:**
🟢 **Não é problema agora** (30 categorias)

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
38567767+fabiotreze@users.noreply.github.com (assunto: "Bug NossoDireito")

**Resposta:**
Todo report será analisado assim que possível. Não há SLA formal — este é um projeto open source mantido por uma pessoa.

---

---

**Última Atualização:** 26 de fevereiro de 2026
**Responsável:** Fabio Costa (38567767+fabiotreze@users.noreply.github.com)
**Licença:** MIT
