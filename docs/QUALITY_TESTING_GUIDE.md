# Guia Completo de Validação de Qualidade
**NossoDireito v1.5.0**  
Última atualização: 2026-02-11

---

## 📋 Índice

1. [Ordem de Execução dos Scripts](#1-ordem-de-execução-dos-scripts)
2. [Validações Automatizadas](#2-validações-automatizadas)
3. [Testes Manuais no Browser](#3-testes-manuais-no-browser)
4. [Checklist Final de Qualidade](#4-checklist-final-de-qualidade)
5. [Troubleshooting](#5-troubleshooting)

---

## 1. Ordem de Execução dos Scripts

### 🚀 Pipeline Completo (Recomendado)

```bash
# Executar pipeline completo de validação (10 passos)
python3 scripts/quality_pipeline.py --full

# Duração estimada: ~3-5 minutos
# Score alvo: ≥98/100
```

### ⚡ Pipeline Rápido (Pre-Commit)

```bash
# Validação rápida antes de commit
python3 scripts/quality_pipeline.py --quick

# Duração estimada: ~30 segundos
# Valida apenas sintaxe e quality gate
```

### 🤖 Pipeline CI/CD

```bash
# Pipeline para integração contínua (sem testes de browser)
python3 scripts/quality_pipeline.py --ci

# Duração estimada: ~3 minutos
# Pula apenas testes manuais de browser
```

---

### 📊 Execução Manual Passo a Passo

Se preferir executar cada validação individualmente:

#### **PASSO 1: Limpeza e Higiene**

```bash
# 1.1 Remover backups
find . -name "*.backup" -type f -delete

# 1.2 Remover cache Python
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 1.3 Remover arquivos temporários
find . -type f \( -name "*.pyc" -o -name "*.pyo" -o -name "*~" -o -name "*.swp" \) -delete
```

#### **PASSO 2: Validação de Sintaxe**

```bash
# 2.1 Validar JSON principal
python3 -c "import json; json.load(open('data/direitos.json')); print('✅ JSON válido')"

# 2.2 Validar matching_engine.json
python3 -c "import json; json.load(open('data/matching_engine.json')); print('✅ matching_engine válido')"

# 2.3 Validar manifest.json
python3 -c "import json; json.load(open('manifest.json')); print('✅ manifest válido')"

# 2.4 Validar estrutura HTML
grep -q "<!DOCTYPE html>" index.html && grep -q "</html>" index.html && echo "✅ HTML válido"

# 2.5 Validar JavaScript (se Node.js instalado)
node -c js/app.js
```

#### **PASSO 3: Validação de Fontes Oficiais**

```bash
# Validar links para planalto.gov.br e gov.br
python3 scripts/validate_sources.py

# Duração: ~2-3 minutos (faz requisições HTTP)
```

#### **PASSO 4: Quality Gate Completo** ⭐

```bash
# Executar validação completa de qualidade
python3 codereview/codereview.py

# Duração: ~1 segundo
# Score mínimo aceitável: 75/100
# Score atual (v1.5.0): 98.7/100
```

#### **PASSO 5: Análise 360° (Opcional)**

```bash
# Análise completa de segurança, compliance e performance
python3 scripts/analise360.py

# Duração: ~1-2 minutos
# Gera relatório detalhado em 360_analysis_report.json
```

#### **PASSO 6: Validação de Acessibilidade**

```bash
# 6.1 Verificar atributos ARIA
grep -c "aria-" index.html

# 6.2 Verificar alt em imagens
grep "<img" index.html | grep -c "alt="

# 6.3 Verificar VLibras
grep -q "vlibras" index.html && echo "✅ VLibras encontrado"

# 6.4 Verificar roles ARIA
grep -c "role=" index.html
```

#### **PASSO 7: Validação de Segurança**

```bash
# 7.1 Verificar Content Security Policy
grep -q "Content-Security-Policy" index.html && echo "✅ CSP encontrado"

# 7.2 Verificar URLs HTTPS (NENHUM http:// deve existir)
grep -i "http://" data/direitos.json && echo "❌ HTTP encontrado" || echo "✅ Todas URLs HTTPS"

# 7.3 Verificar dados sensíveis (NENHUM deve existir)
grep -iE "(password|secret|token|api[_-]?key)" data/direitos.json && echo "❌ Dados sensíveis!" || echo "✅ OK"
```

#### **PASSO 8: Validação de Performance**

```bash
# 8.1 Verificar tamanho HTML (<50KB)
ls -lh index.html | awk '{print $5}'

# 8.2 Verificar tamanho JSON (<150KB)
ls -lh data/direitos.json | awk '{print $5}'

# 8.3 Verificar tamanho JavaScript (<100KB)
ls -lh js/app.js | awk '{print $5}'

# Resumo de tamanhos
echo "📦 Tamanhos dos arquivos principais:"
du -h index.html data/direitos.json js/app.js data/matching_engine.json
```

#### **PASSO 9: Iniciar Servidor Local**

```bash
# Opção 1: Python (recomendado - não precisa dependencies)
python3 -m http.server 3000

# Opção 2: Node.js (se instalado)
node server.js

# Abrir no navegador: http://localhost:3000
```

**➤ Prosseguir para Testes Manuais (Seção 3)**

#### **PASSO 10: Relatório Final**

```bash
# Ver relatório de qualidade
cat quality_report.json | python3 -m json.tool | head -50

# Ver score final do quality gate
python3 codereview/codereview.py | grep "Score Total"
```

---

## 2. Validações Automatizadas

### ✅ Quality Gate (codereview.py)

**16 Categorias Avaliadas:**

| Categoria | Score Alvo | v1.5.0 | Status |
|-----------|-----------|--------|--------|
| LGPD / Privacidade | 100% | 100% | ✅ |
| Segurança | 100% | 100% | ✅ |
| Qualidade de Software | 100% | 100% | ✅ |
| Confiabilidade | 100% | 100% | ✅ |
| Performance | 100% | 100% | ✅ |
| Transparência / Fontes | 100% | 100% | ✅ |
| Versionamento | 100% | 100% | ✅ |
| Modularidade | 100% | 100% | ✅ |
| Acessibilidade | 100% | 100% | ✅ |
| Instituições de Apoio | 100% | 100% | ✅ |
| Dados Sensíveis | 100% | 100% | ✅ |
| Higiene de Arquivos | 100% | 100% | ✅ |
| Documentação | 100% | 100% | ✅ |
| Disclaimer / Regulatório | 100% | 100% | ✅ |
| WAF 5 Pilares | 100% | 100% | ✅ |
| Schema / Governança | ≥75% | 78.8% | ⚠️ |

**Score Total:** 98.7/100 ✅

**Detalhes do Schema/Governança (78.8%):**
- ✅ 3/20 categorias COM planalto.gov.br: BPC, CIPTEA, Educação
- ⚠️ 17/20 categorias ANTIGAS sem planalto.gov.br (aceitável - leis mais antigas)
- Motivo: Leis mais recentes (2012-2025) exigem base_legal completa

---

### 📊 Validações do Pipeline

**Passos Obrigatórios (CRITICAL):**
1. ✅ Sintaxe JSON válida
2. ✅ Sintaxe HTML válida
3. ✅ HTTPS em todas URLs
4. ✅ Nenhum dado sensível exposto
5. ✅ Quality gate score ≥75/100

**Passos Opcionais (WARNING):**
1. ⚠️ Sintaxe JavaScript (requer Node.js)
2. ⚠️ Validação de links externos (pode ter timeout)
3. ⚠️ Análise 360° (análise adicional)

---

## 3. Testes Manuais no Browser

### 🌐 Pré-requisitos

1. Iniciar servidor local:
```bash
python3 -m http.server 3000
```

2. Abrir navegador: http://localhost:3000

3. Abrir DevTools (F12):
   - Console (verificar erros)
   - Network (verificar requests)
   - Lighthouse (performance, acessibilidade)

---

### 📝 Checklist de Testes Funcionais

#### **3.1 Carregamento Inicial** ⏱️

- [ ] Página carrega em <3 segundos
- [ ] Nenhum erro no Console
- [ ] 20 categorias visíveis na tela inicial
- [ ] Logo/título "NossoDireito" visível
- [ ] Disclaimer/aviso legal visível no rodapé
- [ ] VLibras widget visível no canto inferior direito

**Teste:**
```
1. Abrir http://localhost:3000
2. Cronometrar tempo de carregamento
3. Verificar Console (F12) para erros
4. Contar cards de categorias visíveis
```

---

#### **3.2 Busca e Matching Engine** 🔍

- [ ] Busca por "autismo" → retorna CIPTEA, educação, plano_saude
- [ ] Busca por "BPC" → retorna categoria BPC
- [ ] Busca por "carro" → retorna isencoes_tributarias
- [ ] Busca por "trabalho" → retorna categoria trabalho, cotas
- [ ] Busca por "escola" → retorna educação
- [ ] Busca por termo inexistente → mensagem "Nenhuma categoria encontrada"
- [ ] Limpar busca (X) → restaura todas categorias

**Teste:**
```
1. Digitar termo no campo de busca
2. Verificar categorias filtradas instantaneamente
3. Verificar se termos relacionados funcionam (keyword_map)
4. Testar busca case-insensitive (BPC, bpc, Bpc)
```

---

#### **3.3 Categorias - Conteúdo Detalhado** 📄

**Testar TODAS as 20 categorias:**

- [ ] **BPC/LOAS** - Clique → abre modal com:
  - Ícone 🏦
  - Resumo claro
  - Base legal (Lei 8.742/1993)
  - Requisitos listados
  - Documentos necessários
  - Passo a passo numerado
  - Dicas (bullets)
  - Valor atualizado (R$ 1.621)
  - Links oficiais (gov.br)

- [ ] **CIPTEA** - Verificar conteúdo completo
- [ ] **Educação Inclusiva** - Verificar multa de recusa
- [ ] **Plano de Saúde** - Verificar ANS
- [ ] **SUS** - Verificar terapias gratuitas
- [ ] **Transporte** - Verificar Passe Livre
- [ ] **Trabalho** - Verificar cotas
- [ ] **FGTS** - Verificar saque PcD
- [ ] **Moradia** - Verificar condomínio
- [ ] **Isenções Tributárias (IPVA)** - **TESTE CRÍTICO** ✨
- [ ] **Atendimento Prioritário** - Verificar Defensoria
- [ ] **Estacionamento** - Verificar Cartão Defis
- [ ] **Aposentadoria Especial** - Verificar tempo reduzido
- [ ] **Prioridade Judicial** - Verificar CPC
- [ ] **Tecnologia Assistiva** - Verificar BNDES
- [ ] **Meia-Entrada** - Verificar Lei 12.933
- [ ] **ProUni/FIES/SISU** - Verificar cotas PcD
- [ ] **Isenção IR** - Verificar doenças graves
- [ ] **Bolsa Família** - Verificar CadÚnico
- [ ] **Tarifa Social Energia** - Verificar BPC/equipamento médico

**Teste Detalhado por Modal:**
```
1. Clicar em categoria
2. Verificar modal abre suavemente
3. Verificar TODOS os campos preenchidos:
   - titulo, icone, resumo ✅
   - base_legal com lei + artigo + link ✅
   - requisitos (bullets) ✅
   - documentos (bullets) ✅
   - passo_a_passo (numerado) ✅
   - dicas (bullets com destaque visual) ✅
   - valor (se aplicável) ✅
   - onde (instruções de onde ir) ✅
   - links (externos, abrem nova aba) ✅
4. Scroll completo do modal
5. Fechar modal (X ou Esc ou fora do modal)
```

---

#### **3.4 IPVA - Dropdown Estados** 🚗 **CRÍTICO**

Esta funcionalidade é complexa e deve ser testada com atenção:

- [ ] Abrir categoria "Isenções Tributárias"
- [ ] Localizar dropdown "Selecione seu estado"
- [ ] Clicar dropdown → abre lista de 27 estados
- [ ] Selecionar "AC - Acre" →
  - Lei: LC 114/2002
  - Artigo: Art. 7º
  - Link SEFAZ: https://sefaznet.ac.gov.br/
- [ ] Selecionar "SP - São Paulo" →
  - Lei: Lei 13.296/2008
  - Artigo: Art. 13-A
  - Link SEFAZ: https://portal.fazenda.sp.gov.br/servicos/ipva/
- [ ] Selecionar "RJ - Rio de Janeiro" →
  - Lei: Lei 2.877/1997
  - Artigo: Art. 5º
- [ ] Trocar estado múltiplas vezes → informações atualizam corretamente
- [ ] Fechar modal e reabrir → dropdown resetado

**Estados para Testar (amostragem):**
```
AC, AL, SP, RJ, MG, PR, RS, DF, BA, CE
```

**Validação:**
```javascript
// Abrir Console (F12) e verificar:
direitos_data.categorias.find(c => c.id === 'isencoes_tributarias').ipva_estados.length
// Deve retornar: 27
```

---

#### **3.5 Links Externos** 🔗

**Todos os links devem:**
- [ ] Abrir em nova aba (`target="_blank"`)
- [ ] Ter `rel="noopener noreferrer"` (segurança)
- [ ] Ir para domínio gov.br ou planalto.gov.br
- [ ] Ser HTTPS (nenhum HTTP)

**Testar Links (amostra):**
- [ ] https://www.gov.br/pt-br/servicos/solicitar-beneficio-assistencial-a-pessoa-com-deficiencia
- [ ] https://meu.inss.gov.br/
- [ ] https://www.planalto.gov.br/ccivil_03/leis/l8742.htm
- [ ] https://aplicacoes.mds.gov.br/sagi/mops/
- [ ] Links da SEFAZ de cada estado (IPVA)

**Teste:**
```
1. Clicar em link externo
2. Verificar abre nova aba
3. Verificar site oficial abre corretamente
4. (Opcional) Verificar certificado SSL (cadeado 🔒)
```

---

#### **3.6 Acessibilidade - Navegação por Teclado** ⌨️

- [ ] **Tab** → navega entre categorias sequencialmente
- [ ] **Enter** → abre modal da categoria focada
- [ ] **Esc** → fecha modal aberto
- [ ] **Tab dentro do modal** → navega pelos links
- [ ] **Shift+Tab** → navega para trás
- [ ] **Estilos de foco visíveis** (outline azul/preto)

**Teste:**
```
1. Fechar/minimizar mouse
2. Usar APENAS teclado:
   - Tab para navegar
   - Enter para abrir
   - Esc para fechar
3. Verificar foco visual em cada elemento
```

---

#### **3.7 VLibras - Tradutor de Libras** 🤟

- [ ] Widget VLibras carrega no canto inferior direito
- [ ] Clicar no widget → abre controles
- [ ] Selecionar texto → tradução aparece
- [ ] Avatar de Libras funciona corretamente

**Teste:**
```
1. Localizar widget VLibras (canto inferior direito)
2. Clicar para expandir
3. Selecionar qualquer texto da página
4. Verificar avatar fazendo tradução em Libras
```

**⚠️ Limitação Conhecida:** VLibras pode não traduzir conteúdo dinâmico (modais). Veja [docs/VLIBRAS_LIMITATIONS.md](VLIBRAS_LIMITATIONS.md).

---

#### **3.8 Disclaimer e Aviso Legal** ⚖️

- [ ] Aviso legal visível no rodapé:
  > "Informações compiladas de fontes oficiais do governo brasileiro (gov.br). Podem estar desatualizadas. Verifique sempre as fontes originais."

- [ ] Link "Sobre" ou "Disclaimer" acessível
- [ ] Modal de aviso (se houver) mostra texto completo:
  - Não é aconselhamento jurídico
  - Dados podem estar desatualizados
  - Verificar fontes oficiais
  - Consultar profissionais (Defensoria, advogado)

**Teste:**
```
1. Scroll até o rodapé
2. Verificar texto de disclaimer visível
3. (Se houver) Clicar em "Sobre" ou "Disclaimer"
4. Ler texto completo do aviso legal
```

---

#### **3.9 Responsividade - Mobile/Tablet** 📱

**Desktop (>1024px):**
- [ ] 3-4 colunas de categorias
- [ ] Modal ocupa ~70% da largura
- [ ] Sidebar (se houver) visível

**Tablet (768px - 1024px):**
- [ ] 2-3 colunas de categorias
- [ ] Modal ocupa ~80% da largura
- [ ] Navegação adaptada

**Mobile (<768px):**
- [ ] 1 coluna de categorias
- [ ] Modal ocupa 95% da largura (fullscreen)
- [ ] Cards empilhados verticalmente
- [ ] Textos legíveis (mínimo 16px)
- [ ] Botões touch-friendly (mínimo 44px)

**Teste:**
```
1. Abrir DevTools (F12)
2. Ativar Device Toolbar (Ctrl+Shift+M)
3. Testar resoluções:
   - iPhone SE (375x667)
   - iPad (768x1024)
   - Desktop (1920x1080)
4. Verificar layout em cada tamanho
5. Testar rotação (portrait/landscape)
```

---

#### **3.10 Performance - Lighthouse** 🚀

- [ ] Abrir DevTools → Lighthouse
- [ ] Executar auditoria (Desktop ou Mobile)
- [ ] Verificar scores:
  - Performance: ≥90
  - Accessibility: ≥95
  - Best Practices: ≥90
  - SEO: ≥90

**Teste:**
```
1. DevTools (F12) → Lighthouse tab
2. Selecionar: Desktop, Todas categorias
3. Generate Report
4. Analisar resultados:
   - Performance: First Contentful Paint <1.8s
   - Accessibility: ARIA, contrast, alt OK
   - Best Practices: HTTPS, console errors
   - SEO: meta tags, sitemap
```

**Relatório esperado (v1.5.0):**
```
Performance:    95+ (HTML 29KB, JS 71KB, JSON 102KB)
Accessibility:  98+ (50 ARIA attrs, VLibras, keyboard nav)
Best Practices: 100 (HTTPS, no errors, CSP)
SEO:            95+ (meta tags, sitemap.xml, robots.txt)
```

---

## 4. Checklist Final de Qualidade

### ✅ Pre-Commit Checklist

Antes de `git commit`, garantir:

**Código:**
- [ ] ✅ Quality gate score ≥75/100 (atual: 98.7)
- [ ] ✅ Nenhum erro no Console do browser
- [ ] ✅ Nenhum warning crítico no codereview
- [ ] ✅ JSON válido (direitos.json, matching_engine.json)
- [ ] ✅ HTML válido (DOCTYPE, estrutura)
- [ ] ✅ JavaScript sem erros de sintaxe

**Conteúdo:**
- [ ] ✅ 20 categorias completas com todos os campos
- [ ] ✅ Todas URLs HTTPS (nenhum HTTP)
- [ ] ✅ Base legal com lei + artigo + link (categorias novas)
- [ ] ✅ Disclaimer/aviso legal visível
- [ ] ✅ Links externos válidos (gov.br, planalto.gov.br)

**Segurança:**
- [ ] ✅ Nenhum dado sensível exposto (passwords, keys, tokens)
- [ ] ✅ Content Security Policy presente
- [ ] ✅ HTTPS em todos os links
- [ ] ✅ .gitignore cobre arquivos sensíveis

**Acessibilidade:**
- [ ] ✅ 50+ atributos ARIA
- [ ] ✅ Navegação por teclado funcional (Tab, Enter, Esc)
- [ ] ✅ VLibras integrado
- [ ] ✅ Estilos de foco visíveis
- [ ] ✅ Alt em todas imagens

**Performance:**
- [ ] ✅ HTML <50KB (atual: 29KB)
- [ ] ✅ JavaScript <100KB (atual: 71KB)
- [ ] ✅ JSON <150KB (atual: 102KB)
- [ ] ✅ Lighthouse Performance ≥90

**Testes:**
- [ ] ✅ Busca funcionando (autismo, BPC, carro)
- [ ] ✅ IPVA dropdown com 27 estados
- [ ] ✅ Modais de todas 20 categorias funcionando
- [ ] ✅ Links externos abrindo em nova aba
- [ ] ✅ Responsividade (mobile, tablet, desktop)

---

### 🚀 Pre-Deploy Checklist

Antes do deploy em produção:

**Validações Automatizadas:**
```bash
# 1. Pipeline completo
python3 scripts/quality_pipeline.py --full

# 2. Quality gate
python3 codereview/codereview.py | grep "Score Total"
# Esperado: Score Total: 98.7/100

# 3. Verificar tamanhos
du -h index.html js/app.js data/direitos.json
# Esperado: 29K, 71K, 102K
```

**Testes Manuais:**
- [ ] Todas 20 categorias testadas no browser
- [ ] IPVA dropdown testado para 10+ estados
- [ ] VLibras funcionando
- [ ] Lighthouse scores ≥90

**Documentação:**
- [ ] CHANGELOG.md atualizado
- [ ] README.md atualizado
- [ ] Versão bumped (package.json, manifest.json)

**Git:**
- [ ] Branch atualizado (`git pull origin main`)
- [ ] Commit com mensagem descritiva
- [ ] Tag de versão criada (`git tag v1.5.0`)

**Azure:**
- [ ] Secrets/variáveis de ambiente configuradas
- [ ] Application Insights configurado
- [ ] Custom domain/SSL configurado (se aplicável)

**Monitoramento:**
- [ ] Verificar logs após deploy (15-30 min)
- [ ] Testar URL de produção
- [ ] Verificar métricas Application Insights

---

## 5. Troubleshooting

### ❌ Problema: "Quality gate falhou"

**Sintoma:**
```
Score Total: 72/100
❌ Pipeline FALHOU
```

**Solução:**
1. Ler relatório completo: `python3 codereview/codereview.py`
2. Identificar categoria com score baixo
3. Corrigir erros indicados
4. Re-executar pipeline

---

### ❌ Problema: "JSON inválido"

**Sintoma:**
```
json.decoder.JSONDecodeError: Expecting ',' delimiter
```

**Solução:**
```bash
# Validar JSON e mostrar erro detalhado
python3 -m json.tool data/direitos.json > /dev/null

# Ou usar online: https://jsonlint.com/
```

---

### ❌ Problema: "URLs HTTP encontradas"

**Sintoma:**
```
❌ 7.2 Verificar URLs HTTPS falhou
```

**Solução:**
```bash
# Encontrar URLs HTTP
grep -n "http://" data/direitos.json

# Substituir http:// por https:// manualmente
# Exemplo: http://acessounico.mec.gov.br → https://acessounico.mec.gov.br
```

---

### ❌ Problema: "IPVA dropdown não funciona"

**Sintoma:**
- Dropdown não abre
- Estados não listados
- Informações não atualizam ao selecionar estado

**Solução:**
1. Abrir Console (F12) e verificar erros JavaScript
2. Verificar se `direitos_data` carregou:
```javascript
console.log(direitos_data.categorias.find(c => c.id === 'isencoes_tributarias').ipva_estados.length);
// Deve retornar: 27
```
3. Verificar HTML: deve ter `<select id="ipva-estados">`
4. Verificar CSS: dropdown deve estar visível
5. Limpar cache: Ctrl+Shift+R (hard reload)

---

### ❌ Problema: "VLibras não carrega"

**Sintoma:**
- Widget VLibras não aparece
- Erro no Console sobre script VLibras

**Solução:**
1. Verificar script no HTML:
```html
<script src="https://vlibras.gov.br/app/vlibras-plugin.js"></script>
<script>new window.VLibras.Widget('https://vlibras.gov.br/app');</script>
```
2. Verificar conectividade com vlibras.gov.br
3. Adicionar exceção no CSP se necessário
4. Ver [docs/VLIBRAS_LIMITATIONS.md](VLIBRAS_LIMITATIONS.md)

---

### ❌ Problema: "Performance baixa (Lighthouse <90)"

**Sintomas:**
- First Contentful Paint >3s
- Total Blocking Time >300ms
- Lighthouse Performance <90

**Soluções:**

**1. Tamanho de arquivos:**
```bash
# Minificar HTML, JS, JSON
# (já feito em v1.5.0, mas verificar novamente)
ls -lh index.html js/app.js data/direitos.json
```

**2. Images:**
```bash
# Otimizar imagens (se houver)
# Usar WebP, comprimir PNG/JPG
# Lazy loading: <img loading="lazy" />
```

**3. Cache Headers:**
Verificar em `server.js` ou Azure Static Web Apps config:
```javascript
Cache-Control: public, max-age=31536000, immutable
```

**4. Defer/Async scripts:**
```html
<script src="js/app.js" defer></script>
```

---

### ⚠️ Problema: "Validação de links timeout"

**Sintoma:**
```
⚠️ 3.1 Validar fontes oficiais falhou (timeout)
```

**Causa:**
- Script `validate_sources.py` faz requests HTTP para cada link
- Sites gov.br podem estar lentos ou indisponíveis temporariamente

**Solução:**
- Este é um erro NÃO-CRÍTICO (warning)
- Pipeline pode continuar
- Validar manualmente 2-3 links principais:
```bash
curl -I https://www.planalto.gov.br/ccivil_03/leis/l8742.htm
curl -I https://www.gov.br/pt-br/servicos/solicitar-beneficio-assistencial-a-pessoa-com-deficiencia
```

---

### 📞 Suporte Adicional

**Documentação:**
- [README.md](../README.md) - Visão geral do projeto
- [CHANGELOG.md](../CHANGELOG.md) - Histórico de mudanças
- [COMPLIANCE.md](COMPLIANCE.md) - Conformidade legal
- [VLIBRAS_LIMITATIONS.md](VLIBRAS_LIMITATIONS.md) - Limitações VLibras

**Issues GitHub:**
- Criar issue em: https://github.com/[usuario]/nossodireito/issues
- Template: Bug report ou Feature request

**Contato:**
- Defensoria Pública: https://www.anadep.org.br/
- OAB (Comissão PcD): https://www.oab.org.br/

---

## 📊 Resumo de Validação (v1.5.0)

| Métrica | Alvo | v1.5.0 | Status |
|---------|------|--------|--------|
| Quality Gate Score | ≥75/100 | 98.7/100 | ✅ |
| WAF 5 Pillars | 100% | 100% | ✅ |
| Categorias Completas | 20/20 | 20/20 | ✅ |
| HTML Size | <50KB | 29KB | ✅ |
| JS Size | <100KB | 71KB | ✅ |
| JSON Size | <150KB | 102KB | ✅ |
| ARIA Attributes | ≥40 | 50 | ✅ |
| URLs HTTPS | 100% | 100% | ✅ |
| Lighthouse Performance | ≥90 | 95 | ✅ |
| Lighthouse Accessibility | ≥90 | 98 | ✅ |

---

**✅ Pronto para Produção!**  
Última validação: 2026-02-11  
Pipeline Status: ✅ PASSING (98.7/100)
