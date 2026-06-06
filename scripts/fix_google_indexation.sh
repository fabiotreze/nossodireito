#!/bin/bash
# 🔧 FIX: Remove duplicação de conteúdo que bloqueia indexação Google
# SOLUÇÃO A: Deletar direitos/*.html (manter JS rendering apenas)

set -e

echo "🔍 VERIFICANDO ESTRUTURA..."

PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
DIREITOS_DIR="$PROJECT_ROOT/direitos"

# Contar arquivos HTML
HTML_COUNT=$(find "$DIREITOS_DIR" -name "index.html" 2>/dev/null | wc -l)
BR_COUNT=$(find "$DIREITOS_DIR" -name "index.html.br" 2>/dev/null | wc -l)
GZ_COUNT=$(find "$DIREITOS_DIR" -name "index.html.gz" 2>/dev/null | wc -l)

echo ""
echo "📊 ANTES:"
echo "  - HTML files: $HTML_COUNT"
echo "  - Brotli files: $BR_COUNT"
echo "  - Gzip files: $GZ_COUNT"
echo ""

if [ "$HTML_COUNT" -eq 0 ]; then
  echo "✅ Já foram removidos! Nada a fazer."
  exit 0
fi

echo "⚠️  AVISO: Esta ação vai deletar $HTML_COUNT + $BR_COUNT + $GZ_COUNT arquivos pré-renderizados"
echo ""
read -p "Continuar? (s/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
  echo "❌ Abortado."
  exit 1
fi

echo ""
echo "💾 FAZENDO BACKUP..."
BACKUP_FILE="$PROJECT_ROOT/direitos_prender_backup_$(date +%s).tar.gz"
tar -czf "$BACKUP_FILE" "$DIREITOS_DIR" 2>/dev/null
echo "   ✅ Backup: $BACKUP_FILE"
echo ""

echo "🗑️  DELETANDO ARQUIVOS PRÉ-RENDERIZADOS..."
find "$DIREITOS_DIR" -name "index.html" -delete
find "$DIREITOS_DIR" -name "index.html.br" -delete
find "$DIREITOS_DIR" -name "index.html.gz" -delete

echo "   ✅ Deletado"
echo ""

# Contar novamente
NEW_HTML_COUNT=$(find "$DIREITOS_DIR" -name "index.html" 2>/dev/null | wc -l)
echo "📊 DEPOIS:"
echo "  - HTML files: $NEW_HTML_COUNT"
echo ""

echo "✅ FIX APLICADO!"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo ""
echo "1. Testar servidor localmente:"
echo "   npm run start"
echo "   curl -v http://localhost:3000/direitos/bpc/"
echo "   → Deve retornar /index.html com JS rendering dinâmico"
echo ""
echo "2. Fazer commit:"
echo "   git add direitos/"
echo "   git commit -m 'fix: remove prerendered HTML (resolve Google indexation #21)'"
echo ""
echo "3. Deploy para produção"
echo ""
echo "4. Ir para Google Search Console:"
echo "   - Coverage → Coverage issues"
echo "   - Clicar em \"Crawled - currently not indexed\""
echo "   - Request indexing em 5 URLs"
echo "   - Aguardar 7-14 dias"
echo ""
echo "5. Monitorar:"
echo "   - Search Console → Performance"
echo "   - Esperar primeiras impressões (5-7 dias)"
echo "   - Esperar primeiros cliques (2-3 semanas)"
echo ""
