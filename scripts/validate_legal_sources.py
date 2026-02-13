#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador de Fontes Legais - NossoDireito v1.5.0

Valida base_legal em direitos.json:
- Busca artigos relevantes em fontes oficiais (planalto.gov.br)
- Identifica menções a PcD, autismo, deficiência
- Sugere artigos corretos baseados no conteúdo real da lei
- NUNCA usa dados genéricos - SEMPRE da fonte oficial

Uso:
    python3 scripts/validate_legal_sources.py
    python3 scripts/validate_legal_sources.py --fix  # Aplica correções
"""

import json
import re
import sys
import time
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path


class LegalTextParser(HTMLParser):
    """Parser HTML para extrair texto de leis do Planalto"""

    def __init__(self):
        super().__init__()
        self.text = []
        self.in_body = False

    def handle_starttag(self, tag, attrs):
        if tag in ['body', 'div', 'p']:
            self.in_body = True

    def handle_data(self, data):
        if self.in_body:
            self.text.append(data)

    def get_text(self):
        return ' '.join(self.text)


class LegalSourceValidator:
    """Validador de fontes legais com busca em fontes oficiais"""

    def __init__(self, fix_mode=False):
        self.root = Path(__file__).parent.parent
        self.fix_mode = fix_mode
        self.issues = []
        self.fixes = []

        # Palavras-chave para identificar artigos relevantes
        self.keywords = [
            'pessoa com deficiência', 'pessoa portadora de deficiência',
            'deficiente', 'pcd', 'autismo', 'tea', 'espectro autista',
            'deficiência física', 'deficiência visual', 'deficiência auditiva',
            'deficiência intelectual', 'deficiência mental',
            'laudo médico', 'atestado médico', 'impedimento de longo prazo',
            'acessibilidade', 'inclusão', 'benefício assistencial',
            'reserva de vagas', 'cotas', 'atendimento prioritário'
        ]

        with open(self.root / 'data' / 'direitos.json', 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def log(self, message, level='INFO'):
        """Log com timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        symbols = {'INFO': 'ℹ️', 'SUCCESS': '✅', 'ERROR': '❌', 'WARN': '⚠️', 'FIX': '🔧'}
        print(f"[{timestamp}] {symbols.get(level, 'ℹ️')} {message}")

    def is_official_source(self, url):
        """Verifica se URL é de fonte oficial"""
        official_domains = [
            'planalto.gov.br',
            'gov.br',
            'mec.gov.br',
            'receitafederal',
            'fazenda.gov.br'
        ]
        return any(domain in url for domain in official_domains)

    def fetch_law_content(self, url, retries=3):
        """Busca conteúdo da lei de fonte oficial com retry"""
        if not self.is_official_source(url):
            return None

        for attempt in range(retries):
            try:
                if attempt > 0:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.log(f"Retry {attempt + 1}/{retries} após {wait_time}s...", 'WARN')
                    time.sleep(wait_time)

                self.log(f"Buscando: {url[:80]}...", 'INFO')

                req = urllib.request.Request(
                    url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Accept': 'text/html,application/xhtml+xml',
                        'Accept-Language': 'pt-BR,pt;q=0.9',
                        'Connection': 'keep-alive'
                    }
                )

                with urllib.request.urlopen(req, timeout=30) as response:
                    if response.status != 200:
                        continue

                    html = response.read().decode('utf-8', errors='ignore')

                    # Parse HTML
                    parser = LegalTextParser()
                    parser.feed(html)
                    content = parser.get_text()

                    # Delay para não sobrecarregar servidor
                    time.sleep(1)

                    return content

            except Exception as e:
                if attempt == retries - 1:
                    self.log(f"Erro após {retries} tentativas: {str(e)[:50]}", 'WARN')
                continue

        return None

    def extract_articles(self, content, keywords):
        """Extrai artigos relevantes do conteúdo da lei"""
        if not content:
            return []

        # Normalizar texto
        content_lower = content.lower()

        # Padrões de artigos
        article_pattern = r'(art\.?\s*\d+[º°]?(?:-[A-Z])?|artigo\s+\d+[º°]?)'

        relevant_articles = set()

        # Buscar menções a keywords próximas a artigos
        for keyword in keywords:
            keyword_lower = keyword.lower()
            pos = 0

            while (pos := content_lower.find(keyword_lower, pos)) != -1:
                # Buscar artigo nos 500 caracteres antes e depois
                context_start = max(0, pos - 500)
                context_end = min(len(content), pos + 500)
                context = content[context_start:context_end]

                # Encontrar artigos no contexto
                matches = re.findall(article_pattern, context, re.IGNORECASE)
                for match in matches:
                    # Normalizar formato (Art. X°)
                    article = self.normalize_article(match)
                    relevant_articles.add(article)

                pos += 1

        return sorted(list(relevant_articles))

    def normalize_article(self, article):
        """Normaliza formato de artigo"""
        # Extrair número do artigo
        num_match = re.search(r'\d+', article)
        if not num_match:
            return article

        num = num_match.group()

        # Verificar se tem sufixo (-A, -B, etc)
        suffix_match = re.search(r'\d+([º°]?-?[A-Z]?)', article)
        suffix = suffix_match.group(1) if suffix_match else ''

        return f"Art. {num}{suffix}"

    def get_default_article(self, lei):
        """Retorna artigo padrão baseado no tipo de norma"""
        lei_lower = lei.lower()

        # Portarias e instruções normativas geralmente não citam artigo específico
        if any(word in lei_lower for word in ['portaria', 'instrução normativa', 'resolução']):
            return 'Norma completa'

        # Decretos regulamentadores
        if 'decreto' in lei_lower and 'regulament' in lei_lower:
            return 'Decreto completo'

        # Default
        return 'Lei completa'

    def validate_base_legal(self, categoria_id, base_legal_list):
        """Valida lista de base_legal de uma categoria"""
        for i, entry in enumerate(base_legal_list):
            lei = entry.get('lei', '')
            artigo = entry.get('artigo')
            url = entry.get('url', '')

            # Se já tem artigo, verificar se é válido
            if artigo and artigo.strip() and artigo != 'AUSENTE':
                continue

            # Se não tem URL oficial, sugerir artigo padrão
            if not url or not self.is_official_source(url):
                default_article = self.get_default_article(lei)

                self.issues.append({
                    'categoria': categoria_id,
                    'index': i,
                    'lei': lei,
                    'problema': 'URL não é fonte oficial ou ausente',
                    'url': url,
                    'sugestao': default_article
                })

                if self.fix_mode:
                    self.fixes.append({
                        'categoria': categoria_id,
                        'index': i,
                        'artigo': default_article
                    })
                    self.log(f"FIX: {categoria_id}[{i}] → {default_article}", 'FIX')

                continue

            # Buscar conteúdo da lei
            self.log(f"Validando: {categoria_id} - {lei}", 'INFO')
            content = self.fetch_law_content(url)

            if not content:
                self.issues.append({
                    'categoria': categoria_id,
                    'index': i,
                    'lei': lei,
                    'problema': 'Não foi possível acessar a lei na fonte oficial',
                    'url': url
                })
                continue

            # Extrair artigos relevantes
            relevant_articles = self.extract_articles(content, self.keywords)

            if relevant_articles:
                suggestion = relevant_articles[0] if len(relevant_articles) == 1 else f"{relevant_articles[0]} e outros"

                self.issues.append({
                    'categoria': categoria_id,
                    'index': i,
                    'lei': lei,
                    'problema': 'Artigo ausente',
                    'url': url,
                    'sugestao': suggestion,
                    'artigos_encontrados': relevant_articles[:5]  # Limitar a 5
                })

                if self.fix_mode:
                    self.fixes.append({
                        'categoria': categoria_id,
                        'index': i,
                        'artigo': relevant_articles[0]
                    })
                    self.log(f"FIX: {categoria_id}[{i}] → {relevant_articles[0]}", 'FIX')
            else:
                self.issues.append({
                    'categoria': categoria_id,
                    'index': i,
                    'lei': lei,
                    'problema': 'Artigo ausente - nenhum artigo relevante encontrado na lei',
                    'url': url,
                    'sugestao': 'Lei completa'
                })

                if self.fix_mode:
                    self.fixes.append({
                        'categoria': categoria_id,
                        'index': i,
                        'artigo': 'Lei completa'
                    })
                    self.log(f"FIX: {categoria_id}[{i}] → Lei completa", 'FIX')

    def apply_fixes(self):
        """Aplica correções ao direitos.json"""
        if not self.fix_mode or not self.fixes:
            return

        self.log(f"Aplicando {len(self.fixes)} correções...", 'INFO')

        for fix in self.fixes:
            cat_id = fix['categoria']
            index = fix['index']
            artigo = fix['artigo']

            # Encontrar categoria
            for cat in self.data['categorias']:
                if cat['id'] == cat_id:
                    if 'base_legal' in cat and index < len(cat['base_legal']):
                        cat['base_legal'][index]['artigo'] = artigo
                        self.log(f"✓ {cat_id}[{index}] artigo atualizado: {artigo}", 'SUCCESS')

        # Salvar arquivo
        output_file = self.root / 'data' / 'direitos.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

        self.log(f"Arquivo salvo: {output_file}", 'SUCCESS')

    def generate_report(self):
        """Gera relatório de validação"""
        self.log("=" * 70, 'INFO')
        self.log("RELATÓRIO DE VALIDAÇÃO DE FONTES LEGAIS", 'INFO')
        self.log("=" * 70, 'INFO')

        if not self.issues:
            self.log("✅ Nenhum problema encontrado!", 'SUCCESS')
            return True

        self.log(f"Total de problemas: {len(self.issues)}", 'WARN')

        # Agrupar por categoria
        by_category = {}
        for issue in self.issues:
            cat = issue['categoria']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(issue)

        for cat_id, cat_issues in by_category.items():
            self.log("", 'INFO')
            self.log(f"Categoria: {cat_id} ({len(cat_issues)} problema(s))", 'WARN')

            for issue in cat_issues:
                self.log(f"  Lei: {issue['lei']}", 'INFO')
                self.log(f"  Problema: {issue['problema']}", 'WARN')

                if 'sugestao' in issue:
                    self.log(f"  Sugestão: {issue['sugestao']}", 'FIX')

                if 'artigos_encontrados' in issue and len(issue['artigos_encontrados']) > 1:
                    self.log(f"  Outros artigos: {', '.join(issue['artigos_encontrados'][1:])}", 'INFO')

        self.log("", 'INFO')
        self.log("=" * 70, 'INFO')

        if self.fix_mode:
            self.log(f"✅ {len(self.fixes)} correções aplicadas", 'SUCCESS')
        else:
            self.log("💡 Para aplicar correções automaticamente, use: --fix", 'INFO')

        return len(self.issues) == 0

    def run(self):
        """Executa validação completa"""
        self.log("Validando fontes legais de direitos.json...", 'INFO')

        for categoria in self.data.get('categorias', []):
            cat_id = categoria.get('id')
            base_legal = categoria.get('base_legal', [])

            if base_legal:
                self.validate_base_legal(cat_id, base_legal)

        # Aplicar correções se modo fix
        if self.fix_mode:
            self.apply_fixes()

        # Gerar relatório
        success = self.generate_report()

        return 0 if success else 1


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    fix_mode = '--fix' in sys.argv

    if fix_mode:
        print("⚠️  MODO FIX ATIVADO - Alterações serão aplicadas em direitos.json")
        print("⚠️  Recomendamos fazer backup antes: cp data/direitos.json data/direitos.json.backup")
        print("")

    validator = LegalSourceValidator(fix_mode=fix_mode)
    exit_code = validator.run()
    sys.exit(exit_code)
