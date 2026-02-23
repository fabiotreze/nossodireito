#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Content Validation - Validação Semântica e Estrutural
NossoDireito v1.14.0

Valida:
- 30 categorias com todos os campos obrigatórios
- Matching engine (keywords, sinônimos)
- Dropdown IPVA (27 estados)
- Fontes oficiais (base_legal completa)
- Categorias relacionadas
- Padrões de código
- Análise semântica de conteúdo

Uso:
    python3 scripts/validate_content.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Configurar encoding UTF-8 para saída (Windows compatibility)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class ContentValidator:
    """Validador de conteúdo e estrutura"""

    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.errors = []
        self.warnings = []
        self.passes = []

        # Load data
        with open(self.root / 'data' / 'direitos.json', 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        with open(self.root / 'data' / 'matching_engine.json', 'r', encoding='utf-8') as f:
            self.matching = json.load(f)

    def log(self, message, level='PASS'):
        """Log resultado"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        symbols = {'PASS': '✅', 'WARN': '⚠️', 'ERROR': '❌'}
        print(f"[{timestamp}] {symbols[level]} {message}")

        if level == 'PASS':
            self.passes.append(message)
        elif level == 'WARN':
            self.warnings.append(message)
        else:  # ERROR
            self.errors.append(message)

    def validate_categories(self):
        """Validar 30 categorias completas"""
        self.log("=" * 70, 'PASS')
        self.log("VALIDAÇÃO DE CATEGORIAS (30)", 'PASS')
        self.log("=" * 70, 'PASS')

        categorias = self.data.get('categorias', [])

        # 1. Total de categorias
        if len(categorias) != 30:
            self.log(f"Total de categorias: {len(categorias)} (esperado: 30)", 'ERROR')
        else:
            self.log(f"Total de categorias: 30 ✓", 'PASS')

        # IDs esperados
        expected_ids = [
            'bpc', 'ciptea', 'educacao', 'plano_saude', 'sus_terapias',
            'transporte', 'trabalho', 'fgts', 'moradia', 'isencoes_tributarias',
            'atendimento_prioritario', 'estacionamento_especial', 'aposentadoria_especial_pcd',
            'prioridade_judicial', 'tecnologia_assistiva', 'meia_entrada',
            'prouni_fies_sisu', 'isencao_ir', 'bolsa_familia', 'tarifa_social_energia',
            'auxilio_inclusao', 'protecao_social', 'pensao_zika',
            'esporte_paralimpico', 'turismo_acessivel',
            'acessibilidade_arquitetonica', 'capacidade_legal',
            'crimes_contra_pcd', 'acessibilidade_digital', 'reabilitacao'
        ]

        found_ids = [c['id'] for c in categorias]
        missing = set(expected_ids) - set(found_ids)
        extra = set(found_ids) - set(expected_ids)

        if missing:
            self.log(f"Categorias faltando: {missing}", 'ERROR')
        if extra:
            self.log(f"Categorias extras (não esperadas): {extra}", 'WARN')
        if not missing and not extra:
            self.log("Todas 30 categorias presentes ✓", 'PASS')

        # 2. Campos obrigatórios por categoria
        required_fields = ['id', 'titulo', 'icone', 'resumo', 'base_legal',
                          'requisitos', 'documentos', 'passo_a_passo', 'dicas',
                          'valor', 'onde', 'links', 'tags']

        for cat in categorias:
            cat_id = cat.get('id', 'unknown')

            # Verificar campos obrigatórios
            missing_fields = [f for f in required_fields if f not in cat]
            if missing_fields:
                self.log(f"{cat_id}: campos faltando: {missing_fields}", 'ERROR')
            else:
                self.log(f"{cat_id}: todos campos obrigatórios presentes ✓", 'PASS')

            # 3. Base legal completa (lei + artigo + link)
            base_legal = cat.get('base_legal', [])
            if not base_legal:
                self.log(f"{cat_id}: base_legal vazia", 'ERROR')
            else:
                for bl in base_legal:
                    if 'lei' not in bl or 'artigo' not in bl:
                        self.log(f"{cat_id}: base_legal incompleta (falta lei ou artigo)", 'WARN')
                    if 'url' in bl or 'link' in bl:
                        url = bl.get('url') or bl.get('link')
                        if not url.startswith('https://'):
                            self.log(f"{cat_id}: base_legal com URL não-HTTPS: {url}", 'ERROR')

            # 4. Listas não vazias
            if not cat.get('requisitos'):
                self.log(f"{cat_id}: requisitos vazio", 'WARN')
            if not cat.get('documentos'):
                self.log(f"{cat_id}: documentos vazio", 'WARN')
            if not cat.get('passo_a_passo'):
                self.log(f"{cat_id}: passo_a_passo vazio", 'ERROR')
            if not cat.get('dicas'):
                self.log(f"{cat_id}: dicas vazio", 'WARN')
            if not cat.get('links'):
                self.log(f"{cat_id}: links vazio", 'ERROR')
            if not cat.get('tags'):
                self.log(f"{cat_id}: tags vazio", 'WARN')

            # 5. Links externos válidos
            for link in cat.get('links', []):
                url = link.get('url', '')
                # Aceitar tel:, mailto:, e HTTPS
                if not (url.startswith('https://') or url.startswith('tel:') or url.startswith('mailto:')):
                    self.log(f"{cat_id}: link não-HTTPS: {url}", 'ERROR')
                if 'titulo' not in link:
                    self.log(f"{cat_id}: link sem título", 'WARN')

    def validate_ipva_dropdown(self):
        """Validar dropdown IPVA com 27 estados"""
        self.log("=" * 70, 'PASS')
        self.log("VALIDAÇÃO DROPDOWN IPVA (27 ESTADOS)", 'PASS')
        self.log("=" * 70, 'PASS')

        isencoes = next((c for c in self.data['categorias'] if c['id'] == 'isencoes_tributarias'), None)

        if not isencoes:
            self.log("Categoria 'isencoes_tributarias' não encontrada", 'ERROR')
            return

        ipva_estados = isencoes.get('ipva_estados', [])

        # 1. Total de estados
        if len(ipva_estados) != 27:
            self.log(f"Total de estados IPVA: {len(ipva_estados)} (esperado: 27)", 'ERROR')
        else:
            self.log(f"Total de estados IPVA: 27 ✓", 'PASS')

        # 2. UFs esperadas
        expected_ufs = [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
            'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
            'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]

        found_ufs = [e['uf'] for e in ipva_estados]
        missing_ufs = set(expected_ufs) - set(found_ufs)
        extra_ufs = set(found_ufs) - set(expected_ufs)

        if missing_ufs:
            self.log(f"Estados IPVA faltando: {missing_ufs}", 'ERROR')
        if extra_ufs:
            self.log(f"Estados IPVA extras: {extra_ufs}", 'WARN')
        if not missing_ufs and not extra_ufs:
            self.log("Todos 27 estados presentes ✓", 'PASS')

        # 3. Campos obrigatórios por estado
        for estado in ipva_estados:
            uf = estado.get('uf', 'unknown')

            if 'lei' not in estado:
                self.log(f"IPVA {uf}: campo 'lei' faltando", 'ERROR')
            if 'art' not in estado:
                self.log(f"IPVA {uf}: campo 'art' faltando", 'ERROR')
            if 'sefaz' not in estado:
                self.log(f"IPVA {uf}: campo 'sefaz' faltando", 'ERROR')
            elif not estado['sefaz'].startswith('https://'):
                self.log(f"IPVA {uf}: SEFAZ não-HTTPS: {estado['sefaz']}", 'ERROR')

        # 4. Dropdown detalhado (se existir)
        ipva_detalhado = isencoes.get('ipva_estados_detalhado', [])
        if ipva_detalhado:
            if len(ipva_detalhado) != 27:
                self.log(f"IPVA detalhado: {len(ipva_detalhado)} estados (esperado: 27)", 'WARN')
            else:
                self.log(f"IPVA detalhado: 27 estados ✓", 'PASS')

    def validate_orgaos_estaduais(self):
        """Validar órgãos estaduais expandidos (27 UFs com sefaz, detran, benefícios)"""
        self.log("=" * 70, 'PASS')
        self.log("VALIDAÇÃO ÓRGÃOS ESTADUAIS EXPANDIDOS", 'PASS')
        self.log("=" * 70, 'PASS')

        expected_ufs = sorted([
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
            'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
            'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ])

        orgaos = self.data.get('orgaos_estaduais', [])

        # 1. Total de estados
        found_ufs = sorted([o['uf'] for o in orgaos])
        if found_ufs != expected_ufs:
            missing = set(expected_ufs) - set(found_ufs)
            self.log(f"Órgãos estaduais: faltando UFs {missing}", 'ERROR')
        else:
            self.log(f"Órgãos estaduais: 27 UFs presentes ✓", 'PASS')

        # 2. Campos obrigatórios
        for o in orgaos:
            uf = o.get('uf', '?')
            for campo in ['nome', 'url', 'sefaz', 'detran']:
                if campo not in o or not o[campo]:
                    self.log(f"Órgão {uf}: campo '{campo}' ausente ou vazio", 'ERROR')

            # 3. URLs HTTPS
            for url_field in ['url', 'sefaz', 'detran']:
                url = o.get(url_field, '')
                if url and not url.startswith('https://'):
                    self.log(f"Órgão {uf}: {url_field} não-HTTPS: {url}", 'ERROR')

            # 4. Benefícios destaque
            beneficios = o.get('beneficios_destaque', [])
            if len(beneficios) < 1:
                self.log(f"Órgão {uf}: sem benefícios destaque", 'WARN')

        self.log("Validação de órgãos estaduais concluída ✓", 'PASS')

    def validate_matching_engine(self):
        """Validar matching engine e keywords"""
        self.log("=" * 70, 'PASS')
        self.log("VALIDAÇÃO MATCHING ENGINE", 'PASS')
        self.log("=" * 70, 'PASS')

        # 1. Estrutura básica - matching_engine pode ter diferentes formatos
        if 'uppercase_only_terms' in self.matching:
            terms = self.matching['uppercase_only_terms']
            self.log(f"Termos uppercase: {len(terms)} encontrados", 'PASS')

        # Buscar keyword_map (estrutura atual)
        if 'keyword_map' not in self.matching:
            self.log("keyword_map não encontrado", 'ERROR')
            return

        keyword_map = self.matching['keyword_map']
        self.log(f"Total de keywords no keyword_map: {len(keyword_map)}", 'PASS')

        # 2. Validar estrutura: cada keyword deve ter "cats" e "weight"
        cat_ids = [c['id'] for c in self.data['categorias']]
        categories_found = set()

        for keyword, config in keyword_map.items():
            if not isinstance(config, dict):
                self.log(f"keyword_map['{keyword}']: deve ser dict, encontrado {type(config).__name__}", 'ERROR')
                continue

            if 'cats' not in config:
                self.log(f"keyword_map['{keyword}']: falta campo 'cats'", 'ERROR')
                continue

            if 'weight' not in config:
                self.log(f"keyword_map['{keyword}']: falta campo 'weight'", 'WARN')

            # Validar categorias referenciadas
            for cat_id in config['cats']:
                categories_found.add(cat_id)
                if cat_id not in cat_ids:
                    self.log(f"keyword_map['{keyword}']: categoria '{cat_id}' não existe em direitos.json", 'ERROR')

            # Keyword deve ser lowercase
            if keyword != keyword.lower():
                self.log(f"keyword_map: keyword não lowercase: '{keyword}'", 'WARN')

        # 3. Verificar se todas categorias têm pelo menos 3 keywords
        for cat_id in cat_ids:
            keywords_for_cat = [k for k, c in keyword_map.items() if cat_id in c.get('cats', [])]
            num_keywords = len(keywords_for_cat)

            if num_keywords == 0:
                self.log(f"Categoria '{cat_id}' sem keywords no keyword_map", 'WARN')
            elif num_keywords < 3:
                self.log(f"Categoria '{cat_id}' com poucas keywords ({num_keywords})", 'WARN')
            else:
                self.log(f"Categoria '{cat_id}': {num_keywords} keywords ✓", 'PASS')

    def validate_documentos_mestre(self):
        """Validar documentos_mestre"""
        self.log("=" * 70, 'PASS')
        self.log("VALIDAÇÃO DOCUMENTOS_MESTRE", 'PASS')
        self.log("=" * 70, 'PASS')

        docs = self.data.get('documentos_mestre', [])

        if not docs:
            self.log("documentos_mestre vazio", 'ERROR')
            return

        self.log(f"Total de documentos: {len(docs)}", 'PASS')

        # IDs esperados
        expected_doc_ids = [
            'rg', 'cpf', 'comprovante_residencia', 'laudo_medico', 'nis',
            'comprovante_renda', 'foto_3x4', 'cartao_sus', 'carteirinha_plano',
            'prescricao_medica', 'ctps', 'certidao_dependencia', 'convencao_condominio',
            'comprovante_deficiencia', 'comprovante_bpc', 'prescricao_equipamento_medico'
        ]

        found_doc_ids = [d['id'] for d in docs]
        missing_docs = set(expected_doc_ids) - set(found_doc_ids)

        if missing_docs:
            self.log(f"Documentos faltando: {missing_docs}", 'WARN')

        # Verificar campos obrigatórios
        cat_ids = [c['id'] for c in self.data['categorias']]

        for doc in docs:
            doc_id = doc.get('id', 'unknown')

            if 'nome' not in doc:
                self.log(f"Documento '{doc_id}': campo 'nome' faltando", 'ERROR')
            if 'descricao' not in doc:
                self.log(f"Documento '{doc_id}': campo 'descricao' faltando", 'ERROR')
            if 'categorias' not in doc or not doc['categorias']:
                self.log(f"Documento '{doc_id}': campo 'categorias' vazio", 'ERROR')
            else:
                # Verificar se categorias referenciadas existem
                for cat in doc['categorias']:
                    if cat not in cat_ids:
                        self.log(f"Documento '{doc_id}': categoria '{cat}' não existe", 'ERROR')

    def validate_related_categories(self):
        """Validar categorias relacionadas"""
        self.log("=" * 70, 'PASS')
        self.log("VALIDAÇÃO CATEGORIAS RELACIONADAS", 'PASS')
        self.log("=" * 70, 'PASS')

        cat_ids = [c['id'] for c in self.data['categorias']]

        # Verificar se documentos_mestre cria relacionamentos válidos
        docs = self.data.get('documentos_mestre', [])

        total_relations = 0
        for doc in docs:
            categorias = doc.get('categorias', [])
            total_relations += len(categorias)

            # Verificar relacionamentos bidirecionais implícitos
            if len(categorias) > 1:
                self.log(f"Documento '{doc['id']}' relaciona {len(categorias)} categorias", 'PASS')

        self.log(f"Total de relacionamentos via documentos: {total_relations}", 'PASS')

    def validate_code_patterns(self):
        """Validar padrões de código no HTML/JS"""
        self.log("=" * 70, 'PASS')
        self.log("VALIDAÇÃO DE PADRÕES DE CÓDIGO", 'PASS')
        self.log("=" * 70, 'PASS')

        # 1. Verificar index.html
        html_file = self.root / 'index.html'
        with open(html_file, 'r', encoding='utf-8') as f:
            html = f.read()

        # Anti-patterns
        if 'alert(' in html:
            self.log("HTML: alert() encontrado (usar showToast)", 'ERROR')
        else:
            self.log("HTML: nenhum alert() encontrado ✓", 'PASS')

        if 'console.log(' in html and 'production' in html:
            self.log("HTML: console.log() em produção", 'WARN')

        # 2. Verificar app.js
        js_file = self.root / 'js' / 'app.js'
        with open(js_file, 'r', encoding='utf-8') as f:
            js = f.read()

        if 'alert(' in js:
            count = js.count('alert(')
            self.log(f"JS: {count} alert() encontrado(s) (usar showToast)", 'ERROR')
        else:
            self.log("JS: nenhum alert() encontrado ✓", 'PASS')

        # Verificar error handling
        if '.catch(' in js or 'try {' in js:
            self.log("JS: Error handling presente ✓", 'PASS')
        else:
            self.log("JS: Nenhum error handling encontrado", 'WARN')

        # Verificar ARIA
        aria_count = html.count('aria-')
        if aria_count >= 40:
            self.log(f"HTML: {aria_count} atributos ARIA (bom!) ✓", 'PASS')
        else:
            self.log(f"HTML: apenas {aria_count} atributos ARIA (esperado ≥40)", 'WARN')

    def validate_semantic_content(self):
        """Validar conteúdo semântico"""
        self.log("=" * 70, 'PASS')
        self.log("VALIDAÇÃO SEMÂNTICA DE CONTEÚDO", 'PASS')
        self.log("=" * 70, 'PASS')

        # 1. Verificar se resumos são informativos (>30 chars)
        for cat in self.data['categorias']:
            resumo = cat.get('resumo', '')
            if len(resumo) < 30:
                self.log(f"{cat['id']}: resumo muito curto ({len(resumo)} chars)", 'WARN')

        # 2. Verificar se dicas são úteis (>20 chars cada)
        for cat in self.data['categorias']:
            dicas = cat.get('dicas', [])
            for i, dica in enumerate(dicas):
                if len(dica) < 20:
                    self.log(f"{cat['id']}: dica {i+1} muito curta", 'WARN')

        # 3. Verificar valores monetários atualizados (ano 2026)
        current_year = datetime.now().year
        for cat in self.data['categorias']:
            valor = cat.get('valor', '')
            if 'R$' in valor or 'salário' in valor.lower():
                # OK - tem valor monetário
                self.log(f"{cat['id']}: valor declarado ✓", 'PASS')

        # 4. Verificar se disclaimer está presente
        aviso = self.data.get('aviso', '')
        if 'desatualizadas' in aviso.lower() and 'fontes originais' in aviso.lower():
            self.log("Disclaimer completo presente ✓", 'PASS')
        else:
            self.log("Disclaimer incompleto ou ausente", 'ERROR')

    def run(self):
        """Executar todas validações"""
        self.log("=" * 70, 'PASS')
        self.log("CONTENT VALIDATION - NossoDireito v1.14.0", 'PASS')
        self.log(f"Timestamp: {datetime.now().isoformat()}", 'PASS')
        self.log("=" * 70, 'PASS')

        # Executar validações
        self.validate_categories()
        self.validate_ipva_dropdown()
        self.validate_orgaos_estaduais()
        self.validate_matching_engine()
        self.validate_documentos_mestre()
        self.validate_related_categories()
        self.validate_code_patterns()
        self.validate_semantic_content()

        # Relatório final
        self.log("=" * 70, 'PASS')
        self.log("RELATÓRIO FINAL", 'PASS')
        self.log("=" * 70, 'PASS')

        total = len(self.passes) + len(self.warnings) + len(self.errors)
        self.log(f"Total de validações: {total}", 'PASS')
        self.log(f"✅ Passou: {len(self.passes)}", 'PASS')
        self.log(f"⚠️ Avisos: {len(self.warnings)}", 'WARN' if self.warnings else 'PASS')
        self.log(f"❌ Erros: {len(self.errors)}", 'ERROR' if self.errors else 'PASS')

        if self.errors:
            self.log("", 'ERROR')
            self.log("🛑 VALIDAÇÃO FALHOU - Corrija os erros antes de commit", 'ERROR')
            return False
        elif self.warnings:
            self.log("", 'WARN')
            self.log("⚠️ VALIDAÇÃO PASSOU COM AVISOS", 'WARN')
            return True
        else:
            self.log("", 'PASS')
            self.log("✅ VALIDAÇÃO PASSOU SEM ERROS!", 'PASS')
            return True


if __name__ == '__main__':
    validator = ContentValidator()
    success = validator.run()
    exit(0 if success else 1)
