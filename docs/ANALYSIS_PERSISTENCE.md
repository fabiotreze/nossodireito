# 🔄 Persistência de Análise de Documentos

## O Problema

Quando você faz upload de um documento e realiza uma análise, depois clica em "Voltar para categorias" ou usa o botão voltar do navegador, **a análise desaparecia** e você tinha que fazer tudo de novo.

## A Solução

A partir da versão 1.43.50, o **NossoDireito** implementou **cache de análise** usando IndexedDB. Agora:

✅ Você faz upload → análise → clica voltar → volta e a análise **continua lá**  
✅ Navega entre categorias sem perder o resultado  
✅ Cache expira após 30 minutos (segurança + privacidade)  
✅ Você pode limpar manualmente via "Limpar análise"

## Como Funciona

### 1. **Cachear a Análise** (Cliente)

Quando o resultado da análise é renderizado:

```javascript
// Em js/branding-cache.js
window.ANALYSIS_CACHE.save({
  results,        // Resultados da análise
  fileNames,      // Nomes dos arquivos
  hasPdf,         // Se era PDF ou imagem
  errors,         // Erros durante processamento
  aiResult,       // Resultado da IA (se usado)
  aiAttempted     // Se IA foi tentada
});
```

Dados são salvos em IndexedDB com:
- **TTL (Time To Live)**: 30 minutos
- **Chave**: `latest` (última análise)
- **Formato**: JSON estruturado

### 2. **Usar a History API** (Navegação)

Quando análise é renderizada, adicionamos ao histórico:

```javascript
history.pushState({ view: 'analysis' }, '', '#analise');
```

### 3. **Recuperar ao Voltar** (Recovery)

Quando usuário clica voltar:

```javascript
window.addEventListener('popstate', async (e) => {
  if (e.state?.view === 'analysis') {
    const cached = await window.ANALYSIS_CACHE.retrieve();
    if (cached) {
      // Restaurar análise se ainda estiver válida (TTL)
      renderAnalysisResults(...);
    }
  }
});
```

## 🏗️ Arquitetura

```
User Behavior          |  Storage              |  Rendering
──────────────────────────────────────────────────────────
Upload + Analyze       → Save to IndexedDB    → Render results
                       → history.pushState()  
                       
Click "Back"           ← Retrieve from IDB    ← Re-render results
or browser back        ← Check TTL (valid?)   ← Same analysis state
```

## 📊 Dados Armazenados

Cada registro de análise em cache contém:

```javascript
{
  id: 'latest',
  timestamp: 1623456789012,           // Quando foi cachada
  ttl: 1800000,                       // 30 min em ms
  data: {
    results: [
      {
        category: { id, titulo, resumo },
        score: 85,
        matches: ['CID-10: F84', 'autismo', ...]
      }
    ],
    fileNames: ['laudo_medico.pdf'],
    hasPdf: [true],
    errors: [],
    aiResult: { ... },                // Se IA foi usada
    aiAttempted: true
  }
}
```

## 🔒 Privacidade & Segurança

✅ **Dados salvos apenas no navegador** (IndexedDB — local)  
✅ **Nada vai a servidores** após renderização  
✅ **TTL de 30 min** — cache expira automaticamente  
✅ **Usuário pode limpar** manualmente em qualquer momento  
✅ **Sem sync entre dispositivos** — cada navegador tem seu cache  

**Nota**: O texto do documento (`originalText`) **NÃO é cachado**, apenas os resultados da análise. Se você voltar e clicar "Ver detalhes", apenas o resultado é mostrado.

## 🧪 Testar Localmente

### Teste 1: Cache Básico
```bash
1. npm start
2. Vá para "Consultar / Análise"
3. Faça upload de um PDF
4. Espere análise completar
5. Clique "Voltar para categorias"
6. Clique voltar novamente (browser back)
   → Análise deve reaparecer
```

### Teste 2: TTL de Cache
```bash
1. Siga Teste 1 até a análise aparecer
2. Abra DevTools > Console
3. Rode: localStorage.clear(); // Limpa tudo
4. Recarregue a página
5. Cache deve estar vazio (normal)
```

### Teste 3: Múltiplas Análises
```bash
1. Faça Análise 1
2. Volte
3. Faça Análise 2 (diferente)
4. Volte e volte novamente
   → Deve mostrar Análise 2 (última)
5. (Anterior é sobrescrita)
```

## 🛠️ Troubleshooting

### Problema: Análise não persiste ao voltar

**Solução**:
1. Abra DevTools > Application > IndexedDB
2. Verifique se banco `NossoDireitoDB` existe
3. Procure por store `analysis_results`
4. Se não existir, recarregue a página e faça análise novamente
5. Verifique se IndexedDB está habilitado (em modo privado, não funciona)

### Problema: Análise desaparece após 30 min

**É normal!** O cache expira por segurança. Você pode:
- Fazer nova análise
- Aumentar TTL em `js/branding-cache.js`:
  ```javascript
  TTL_MINUTES: 60,  // Aumentar para 1 hora
  ```

### Problema: "Analysis_results store not found"

**Solução**:
1. Limpe IndexedDB: `indexedDB.deleteDatabase('NossoDireitoDB')`
2. Recarregue a página
3. Banco será recriado automaticamente

## 🔧 Customização

### Aumentar TTL de Cache

Em `js/branding-cache.js`, linha ~70:

```javascript
window.ANALYSIS_CACHE = {
  TTL_MINUTES: 30,  // ← Mudar para quanto quiser (em minutos)
  // ...
};
```

### Desabilitar Cache (dev)

Se quiser desabilitar para debug:

```javascript
// Em js/branding-cache.js, comentar save():
async save(analysisData) {
  // return false;  // ← Comentar recuperação
}
```

### Adicionar Clear Button

Para dar ao usuário controle manual:

```html
<button id="clearAnalysisCache">🗑️ Limpar análise</button>

<script>
document.getElementById('clearAnalysisCache').addEventListener('click', async () => {
  await window.ANALYSIS_CACHE.clear();
  alert('Análise foi limpa.');
});
</script>
```

## 📈 Monitoramento

Para debug / logs:

```javascript
// Recuperar análise atual
await window.ANALYSIS_CACHE.retrieve().then(data => {
  console.log('Cached analysis:', data);
});

// Limpar programaticamente
await window.ANALYSIS_CACHE.clear();
```

## 🚀 Próximas Melhorias

- [ ] Múltiplos históricos de análise (não só a última)
- [ ] Exportar análise em PDF
- [ ] Compartilhar análise via link
- [ ] Sincronizar entre abas do mesmo navegador

## 📚 Referências Técnicas

- [IndexedDB MDN](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API)
- [History API](https://developer.mozilla.org/en-US/docs/Web/API/History_API)
- [popstate Event](https://developer.mozilla.org/en-US/docs/Web/API/Window/popstate_event)

---

**Dúvidas?** Abra uma issue com tag `analysis-cache` no [GitHub](https://github.com/fabiotreze/nossodireito/issues).
