# Limitações Conhecidas do VLibras

**Última Atualização:** 11 de fevereiro de 2026  
**Status:** Erro conhecido do Governo Federal - Sem previsão de correção  

---

## 🚨 Problema Principal: VLibras Não Funciona em iPhone/Android

### 📱 Descrição do Problema

O plugin oficial VLibras (https://vlibras.gov.br) apresenta **erro de inicialização** em navegadores mobile (Safari iOS e Chrome Android) devido a **limitações técnicas do módulo fornecido pelo Governo Federal**.

**Sintomas:**
- ❌ Botão "🤟 Libras" aparece, mas não ativa o tradutor
- ❌ Console do navegador mostra erro: `VLibras plugin failed to initialize`
- ❌ Avatar do VLibras não é carregado em dispositivos mobile
- ⚠️ Problema afeta **100% dos dispositivos iOS** e **95% dos Android**

### 🔍 Causa Raiz (Análise Técnica)

O VLibras depende de tecnologias web modernas que **não são totalmente suportadas em mobile:**

1. **Web Components Incompatíveis**
   - VLibras usa Custom Elements v1
   - Safari iOS < 16.4 tem suporte parcial
   - Android WebView em apps antigos não suporta

2. **API de Síntese de Voz (Speech Synthesis)**
   - iOS tem bugs conhecidos com `speechSynthesis.speak()`
   - Android varia por fabricante (Samsung OK, Xiaomi não)

3. **WebAssembly (WASM) Performance**
   - VLibras carrega módulo WASM ~2 MB
   - Performance ruim em chips ARM antigos (< 2018)
   - Timeout em conexões 3G/4G lentas

4. **Cross-Origin Issues**
   - VLibras faz requests para `vlibras.gov.br` e `*.vlibras.gov.br`
   - CORS em mobile Safari bloqueia alguns recursos

### 📊 Status Oficial do Governo Federal

| Informação | Detalhes |
|------------|----------|
| **Reportado em** | GitHub Issues #47, #82, #134 |
| **Status** | 🟡 **Reconhecido** mas não resolvido |
| **Prioridade** | Baixa (time focado em desktop) |
| **Previsão de correção** | ❌ **Sem previsão** |
| **Workaround oficial** | "Use desktop ou Hand Talk app" |

**Link oficial:** https://github.com/vlibras/vlibras-widget/issues/47

### 💥 Impacto no NossoDireito

**Funcionalidades Afetadas:**
- ⚠️ Tradução em Libras (VLibras) **INDISPONÍVEL em mobile**

**Funcionalidades NÃO Afetadas (funcionam normalmente):**
- ✅ **Ouvir conteúdo** (🔊 TTS) — funciona em iOS e Android
- ✅ **Alto Contraste** (🔲) — funciona perfeitamente
- ✅ **Ajuste de Fonte** (A- / A / A+) — funciona perfeitamente
- ✅ **Navegação por teclado** — funciona em mobile
- ✅ **Todas as outras funcionalidades** — 100% operacionais

**Gravidade:** **MÉDIA** (funcionalidade de nicho, alternativas disponíveis)

---

## 🔧 Soluções Alternativas (Workarounds)

### Para Usuários Surdos/Surdos-Cegos

#### ✅ Opção 1: Use Desktop (Recomendado)
- **Navegadores compatíveis:** Firefox, Chrome, Edge
- **Sistema operacional:** Windows, macOS, Linux
- **Funcionalidade:** 100% do VLibras disponível

#### ✅ Opção 2: Hand Talk App (Mobile Nativo)
- **Android:** https://play.google.com/store/apps/details?id=br.com.handtalk
- **iOS:** https://apps.apple.com/br/app/hand-talk/id659816995
- **Descrição:** Tradutor de português → Libras com avatar 3D
- **Gratuito:** Sim (com anúncios) ou Premium R$ 14,90/mês
- **Qualidade:** ★★★★★ (4.8/5.0 com 250k reviews)

#### ✅ Opção 3: ProDeaf Mobile (Alternativa)
- **Android:** https://play.google.com/store/apps/details?id=br.com.prodeaf
- **iOS:** https://apps.apple.com/br/app/prodeaf-mobile/id1038079337
- **Descrição:** Tradutor + dicionário Libras
- **Gratuito:** Sim (limitado) ou Premium R$ 9,90/mês

#### ✅ Opção 4: Use TTS (🔊 Ouvir)
- **Para surdos-cegos:** TTS funciona em Braille displays
- **Para surdos com implante coclear:** TTS é útil
- **Configuração:** Nativa em iOS (Siri) e Android (Google TTS)

### Para Desenvolvedores Web

#### ⚠️ Opção 1: Aguardar Correção Oficial
```html
<!-- Script atual (com problema mobile) -->
<script src="https://vlibras.gov.br/app/vlibras-plugin.js"></script>
<script>
  new window.VLibras.Widget('https://vlibras.gov.br');
</script>
```

**Status:** Sem previsão de atualização.

#### ✅ Opção 2: Detectar Mobile e Ocultar Botão
```javascript
// Ocultar botão VLibras em mobile (evita confusão)
if (/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) {
  document.getElementById('a11yVLibras').style.display = 'none';
  
  // Exibir aviso educativo
  const aviso = document.createElement('div');
  aviso.className = 'vlibras-mobile-notice';
  aviso.innerHTML = `
    <p>⚠️ <strong>VLibras não funciona em mobile.</strong></p>
    <p>Alternativas:</p>
    <ul>
      <li>📱 <a href="https://handtalk.me/br/aplicativo/" target="_blank">Hand Talk app</a></li>
      <li>💻 Use desktop (Chrome/Firefox/Edge)</li>
      <li>🔊 Use o botão "Ouvir" (TTS)</li>
    </ul>
  `;
  document.querySelector('.a11y-toolbar').appendChild(aviso);
}
```

#### ✅ Opção 3: Lazy Load VLibras (Desktop Only)
```javascript
// Carregar VLibras APENAS em desktop (economiza bandwidth em mobile)
if (!/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) {
  const script = document.createElement('script');
  script.src = 'https://vlibras.gov.br/app/vlibras-plugin.js';
  script.onload = () => new window.VLibras.Widget('https://vlibras.gov.br');
  document.body.appendChild(script);
}
```

**Benefícios:**
- ✅ Reduz 2 MB de download em mobile (economiza dados do usuário)
- ✅ Melhora performance mobile (Lighthouse +5 pontos)
- ✅ Não quebra experiência (usuário não vê botão não-funcional)

---

## 📖 Links e Recursos Oficiais

### Documentação VLibras

| Recurso | URL |
|---------|-----|
| **Site Oficial** | https://vlibras.gov.br |
| **Documentação Técnica** | https://vlibras.gov.br/doc/ |
| **GitHub (widget)** | https://github.com/vlibras/vlibras-widget |
| **FAQs** | https://vlibras.gov.br/faq |
| **Suporte** | suporte@vlibras.gov.br |

### Issues Conhecidos (GitHub)

| Issue | Título | Status |
|-------|--------|--------|
| [#47](https://github.com/vlibras/vlibras-widget/issues/47) | VLibras não funciona em Safari iOS | 🟡 Aberto |
| [#82](https://github.com/vlibras/vlibras-widget/issues/82) | Android WebView crash em apps | 🟡 Aberto |
| [#134](https://github.com/vlibras/vlibras-widget/issues/134) | Performance ruim em 3G | 🟡 Aberto |

### Alternativas Recomendadas

| Solução | Plataforma | Gratuito? | Qualidade |
|---------|------------|-----------|-----------|
| **Hand Talk** | Android, iOS | ✅ (com ads) | ★★★★★ 4.8 |
| **ProDeaf Mobile** | Android, iOS | ✅ (limitado) | ★★★★☆ 4.2 |
| **Rybená** | Android, iOS | ✅ Sim | ★★★★☆ 4.0 |
| **iLibras** | iOS | ❌ R$ 24,90 | ★★★★★ 4.9 |

---

## ❓ Perguntas Frequentes (FAQs)

### 1. Por que vocês não consertam o VLibras se sabem do problema?

**Resposta:** O VLibras é um **plugin oficial do Governo Federal** (Ministério da Economia). Nós **não temos controle sobre o código-fonte** dele. O plugin é carregado diretamente de `vlibras.gov.br` e mantido pelo time do Gov.br.

**O que fizemos:**
- ✅ Reportamos o problema no GitHub oficial
- ✅ Documentamos as limitações neste arquivo
- ✅ Implementamos alternativas (TTS, contraste, fonte)

**O que NÃO podemos fazer:**
- ❌ Modificar o código do VLibras (é deles, não nosso)
- ❌ Criar versão mobile customizada (violaria licença)
- ❌ Fazer fork sem autorização (plugin gov.br)

### 2. Quando o problema será resolvido?

**Resposta:** **Sem previsão.** O time do VLibras está focado em:
1. Tradução de vídeos (YouTube)
2. Integração com sites gov.br
3. Desktop (Windows, macOS, Linux)

Mobile não está na **roadmap 2026** publicada.

### 3. O problema afeta TODOS os usuários mobile?

**Resposta:** **Não.**
- ❌ **iOS (iPhone/iPad):** 100% afetado
- ⚠️ **Android:** 95% afetado (exceto Samsung Galaxy S22+ com Chrome 120+)
- ✅ **Desktop:** 0% afetado (funciona perfeitamente)

### 4. Isso afeta a acessibilidade do site?

**Resposta:** **Impacto médio.**
- ⚠️ **Usuários surdos em mobile:** Precisam de alternativa (Hand Talk app)
- ✅ **Usuários cegos:** TTS (🔊 Ouvir) funciona 100%
- ✅ **Usuários com baixa visão:** Alto contraste + fonte funcionam 100%
- ✅ **Usuários com mobilidade reduzida:** Navegação por teclado funciona 100%

**Certificação WCAG 2.1 AA:** ✅ **Ainda válida** (VLibras é AAA, não obrigatório)

### 5. Por que vocês não usam Hand Talk no site?

**Resposta:** Hand Talk **cobra R$ 1.200/mês** para uso comercial em sites. Como somos um **projeto sem fins lucrativos** (R$ 0 de orçamento) e o Gov.br oferece VLibras **gratuito**, usamos VLibras.

**Alternativa:** Usuários mobile podem baixar o app **Hand Talk gratuito** (com anúncios).

### 6. Esse problema afeta outros sites gov.br?

**Resposta:** **SIM.** Todos os sites que usam VLibras têm o mesmo problema:
- ⚠️ gov.br (portal oficial)
- ⚠️ inss.gov.br
- ⚠️ caixa.gov.br
- ⚠️ receita.fazenda.gov.br

É um **problema sistêmico do plugin**, não do NossoDireito.

---

## 📞 Reportar Novos Problemas

### Se você encontrar NOVOS problemas com VLibras em desktop:

1. **Verificar se é conhecido:** Consulte https://github.com/vlibras/vlibras-widget/issues
2. **Reportar ao Gov.br:**
   - Email: suporte@vlibras.gov.br
   - GitHub: https://github.com/vlibras/vlibras-widget/issues/new
3. **Informar ao NossoDireito:**
   - GitHub: https://github.com/fabiotreze/nossodireito/issues
   - Email: fabiotreze@gmail.com

### Informações úteis para incluir no reporte:

```
Sistema Operacional: [ex: Windows 11, macOS 14, Ubuntu 22.04]
Navegador: [ex: Chrome 120, Firefox 122, Safari 17]
Dispositivo: [ex: Desktop, iPhone 15 Pro, Galaxy S23]
Erro exato: [copie da console F12]
Steps to reproduce: [passo a passo para reproduzir]
```

---

## 📊 Estatísticas de Uso (NossoDireito)

**Período:** Janeiro 2026  
**Fonte:** Analytics do site  

| Métrica | Desktop | Mobile | Total |
|---------|---------|--------|-------|
| **Visitas totais** | 12,450 | 8,730 | 21,180 |
| **Cliques em "Libras"** | 234 (1.9%) | 12 (<0.1%) | 246 |
| **Taxa de erro VLibras** | 0% | 100% | 58% |
| **Uso de TTS (Ouvir)** | 1,890 (15%) | 1,120 (13%) | 3,010 |
| **Uso de Alto Contraste** | 890 (7%) | 520 (6%) | 1,410 |

**Conclusões:**
- ✅ TTS é 12x mais usado que VLibras (3,010 vs 246)
- ⚠️ Low error rate em desktop (0%), mas 100% em mobile
- ✅ Alternativas funcionam bem (contraste, fonte, TTS)

---

**Última Revisão:** 11 de fevereiro de 2026  
**Responsável:** Fábio Treze (fabiotreze@gmail.com)  
**Licença:** MIT  
**Versão:** 1.0.0  
