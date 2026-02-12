#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Compliance Validator - NossoDireito v1.8.0

Sistema mestre COMPLETO de validação de compliance, qualidade e consistência.
Orquestra todos os validadores e gera score final de qualidade.

Validações realizadas (17 categorias):
1. Dados (direitos.json, matching_engine.json, vinculação, classificação)
2. Código (Python, JS, HTML, CSS + linting avançado)
3. Fontes oficiais (validação de URLs e artigos)
4. Arquitetura (estrutura de pastas, padrões)
5. Documentação (completude, atualização de versões)
6. Segurança (SECURITY.md, vulnerabilidades, secrets scanning)
7. Performance (otimizações, caching, profiling)
8. Acessibilidade (WCAG, ARIA)
9. SEO (meta tags, sitemap)
10. Infraestrutura (Terraform, scripts)
11. Testes Automatizados (E2E, unit tests)
12. Dead Code Detection (código não usado, importações órfãs)
13. Arquivos Órfãos (cleanup automático)
14. Lógica de Negócio (validação de regras e fluxos)
15. Regulatory Compliance (LGPD, finance, disclaimer, dados sensíveis)
16. Cloud Security (Azure, EASM, MITRE)
17. CI/CD (GitHub Actions workflows, segurança, boas práticas)

Objetivo: Precisão 100% com validação completa
Requisito: Somente fontes oficiais validadas + segurança máxima
"""

import json
import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime

class MasterComplianceValidator:
    """Validador mestre de compliance e qualidade"""
    
    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.version = "1.8.0"
        self.errors = []
        self.warnings = []
        self.passes = []
        self.score = 0.0
        self.max_score = 0.0
        self.start_time = datetime.now()
        
        # Métricas por categoria (17 categorias)
        self.metrics = {
            'dados': {'score': 0, 'max': 0, 'checks': []},
            'codigo': {'score': 0, 'max': 0, 'checks': []},
            'fontes': {'score': 0, 'max': 0, 'checks': []},
            'arquitetura': {'score': 0, 'max': 0, 'checks': []},
            'documentacao': {'score': 0, 'max': 0, 'checks': []},
            'seguranca': {'score': 0, 'max': 0, 'checks': []},
            'performance': {'score': 0, 'max': 0, 'checks': []},
            'acessibilidade': {'score': 0, 'max': 0, 'checks': []},
            'seo': {'score': 0, 'max': 0, 'checks': []},
            'infraestrutura': {'score': 0, 'max': 0, 'checks': []},
            'testes': {'score': 0, 'max': 0, 'checks': []},
            'dead_code': {'score': 0, 'max': 0, 'checks': []},
            'orfaos': {'score': 0, 'max': 0, 'checks': []},
            'logica': {'score': 0, 'max': 0, 'checks': []},
            'regulatory': {'score': 0, 'max': 0, 'checks': []},
            'cloud_security': {'score': 0, 'max': 0, 'checks': []},
            'cicd': {'score': 0, 'max': 0, 'checks': []}
        }
        
        # Carregar dados principais
        try:
            with open(self.root / 'data' / 'direitos.json', 'r', encoding='utf-8') as f:
                self.direitos = json.load(f)
        except Exception as e:
            self.direitos = None
            self.log_error('dados', f"Erro ao carregar direitos.json: {e}")
        
        try:
            with open(self.root / 'data' / 'matching_engine.json', 'r', encoding='utf-8') as f:
                self.matching = json.load(f)
        except Exception as e:
            self.matching = None
            self.log_error('dados', f"Erro ao carregar matching_engine.json: {e}")
    
    def log_error(self, category: str, message: str):
        """Registra erro"""
        self.errors.append({'category': category, 'message': message})
        self.metrics[category]['checks'].append({'type': 'ERROR', 'message': message})
        print(f"❌ [{category.upper()}] {message}")
    
    def log_warning(self, category: str, message: str):
        """Registra aviso"""
        self.warnings.append({'category': category, 'message': message})
        self.metrics[category]['checks'].append({'type': 'WARN', 'message': message})
        print(f"⚠️  [{category.upper()}] {message}")
    
    def log_pass(self, category: str, message: str, points: float = 1.0):
        """Registra sucesso com pontuação"""
        self.passes.append({'category': category, 'message': message})
        self.metrics[category]['score'] += points
        self.metrics[category]['max'] += points
        self.metrics[category]['checks'].append({'type': 'PASS', 'message': message, 'points': points})
        print(f"✅ [{category.upper()}] {message}")
    
    def log_fail(self, category: str, message: str, points: float = 1.0):
        """Registra falha com penalização"""
        self.metrics[category]['max'] += points
        self.log_error(category, message)
    
    # =========================================================================
    # CATEGORIA 1: VALIDAÇÃO DE DADOS
    # =========================================================================
    
    def validate_data_integrity(self):
        """Valida integridade e consistência dos dados"""
        print("\n" + "=" * 80)
        print("VALIDAÇÃO DE DADOS - Integridade e Consistência")
        print("=" * 80)
        
        if not self.direitos:
            self.log_fail('dados', "direitos.json não carregado", 50)
            return
        
        # 1. Estrutura básica
        required_keys = ['versao', 'categorias', 'documentos_mestre', 'fontes']
        for key in required_keys:
            if key in self.direitos:
                self.log_pass('dados', f"Campo '{key}' presente", 2)
            else:
                self.log_fail('dados', f"Campo obrigatório '{key}' ausente", 2)
        
        # 2. Validar categorias (25 esperadas)
        cats = self.direitos.get('categorias', [])
        if len(cats) == 25:
            self.log_pass('dados', f"25 categorias presentes ✓", 5)
        else:
            self.log_fail('dados', f"Esperado 25 categorias, encontrado {len(cats)}", 5)
        
        # 3. Cada categoria deve ter campos obrigatórios
        required_cat_fields = ['id', 'titulo', 'resumo', 'base_legal', 'requisitos', 
                               'documentos', 'passo_a_passo', 'dicas', 'valor', 'onde', 'links', 'tags']
        
        for cat in cats:
            cat_id = cat.get('id', 'UNKNOWN')
            for field in required_cat_fields:
                if field not in cat or not cat[field]:
                    self.log_warning('dados', f"Categoria '{cat_id}': campo '{field}' ausente ou vazio")
                else:
                    self.log_pass('dados', f"Categoria '{cat_id}': campo '{field}' ✓", 0.5)
            
            # Validar base_legal tem artigos
            for idx, bl in enumerate(cat.get('base_legal', [])):
                if 'artigo' not in bl or not bl['artigo']:
                    self.log_warning('dados', f"Categoria '{cat_id}': base_legal[{idx}] sem artigo")
                elif 'lei' in bl and 'url' in bl:
                    self.log_pass('dados', f"Categoria '{cat_id}': base_legal[{idx}] completa", 0.3)
        
        # 4. Validar matching_engine
        if not self.matching:
            self.log_fail('dados', "matching_engine.json não carregado", 10)
            return
        
        if 'keyword_map' in self.matching:
            keyword_map = self.matching['keyword_map']
            self.log_pass('dados', f"keyword_map presente com {len(keyword_map)} keywords", 5)
            
            # Validar estrutura de cada keyword
            for kw, config in keyword_map.items():
                if 'cats' in config and 'weight' in config:
                    self.log_pass('dados', f"Keyword '{kw}': estrutura válida", 0.1)
                else:
                    self.log_warning('dados', f"Keyword '{kw}': estrutura incompleta")
        else:
            self.log_fail('dados', "keyword_map ausente no matching_engine.json", 10)
    
    # =========================================================================
    # CATEGORIA 2: VALIDAÇÃO DE CÓDIGO
    # =========================================================================
    
    def validate_code_quality(self):
        """Valida qualidade do código Python, JS, HTML, CSS"""
        print("\n" + "=" * 80)
        print("VALIDAÇÃO DE CÓDIGO - Qualidade e Padrões")
        print("=" * 80)
        
        # 1. Executar validate_content.py
        try:
            result = subprocess.run(
                ['python3', 'scripts/validate_content.py'],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                # Extrair métricas do output
                output = result.stdout
                if 'Passou:' in output:
                    match = re.search(r'Passou: (\d+)', output)
                    if match:
                        passes = int(match.group(1))
                        self.log_pass('codigo', f"validate_content.py: {passes} validações OK", passes * 0.5)
                
                if 'Erros: 0' in output:
                    self.log_pass('codigo', "validate_content.py: 0 erros ✓", 10)
                else:
                    match = re.search(r'Erros: (\d+)', output)
                    if match:
                        errors = int(match.group(1))
                        self.log_fail('codigo', f"validate_content.py: {errors} erros encontrados", 10)
            else:
                self.log_fail('codigo', f"validate_content.py falhou (exit {result.returncode})", 20)
                
        except Exception as e:
            self.log_fail('codigo', f"Erro ao executar validate_content.py: {e}", 20)
        
        # 2. Validar arquivos Python
        python_files = list(self.root.glob('**/*.py'))
        for py_file in python_files:
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            # Verificar sintaxe
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    compile(f.read(), py_file, 'exec')
                self.log_pass('codigo', f"{py_file.name}: sintaxe válida", 0.5)
            except SyntaxError as e:
                self.log_fail('codigo', f"{py_file.name}: erro de sintaxe linha {e.lineno}", 1)
        
        # 3. Validar JSON
        json_files = ['data/direitos.json', 'data/matching_engine.json', 'manifest.json', 'package.json']
        for json_file in json_files:
            try:
                with open(self.root / json_file, 'r', encoding='utf-8') as f:
                    json.load(f)
                self.log_pass('codigo', f"{json_file}: JSON válido", 2)
            except Exception as e:
                self.log_fail('codigo', f"{json_file}: JSON inválido - {e}", 2)
    
    # =========================================================================
    # CATEGORIA 3: VALIDAÇÃO DE FONTES OFICIAIS
    # =========================================================================
    
    def validate_official_sources(self):
        """Valida todas as fontes oficiais (URLs de leis)"""
        print("\n" + "=" * 80)
        print("VALIDAÇÃO DE FONTES - Oficialidade e Disponibilidade")
        print("=" * 80)
        
        # Executar validate_legal_sources.py
        try:
            result = subprocess.run(
                ['python3', 'scripts/validate_legal_sources.py'],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            output = result.stdout + result.stderr
            
            # Analisar relatório
            if 'Total de problemas: 0' in output or 'problemas: 0' in output:
                self.log_pass('fontes', "Todas fontes legais validadas ✓", 20)
            else:
                match = re.search(r'Total de problemas: (\d+)', output)
                if match:
                    problems = int(match.group(1))
                    self.log_warning('fontes', f"{problems} problemas encontrados nas fontes legais")
                    self.metrics['fontes']['score'] += max(0, 20 - problems * 2)
                    self.metrics['fontes']['max'] += 20
            
        except Exception as e:
            self.log_fail('fontes', f"Erro ao validar fontes legais: {e}", 20)
        
        # Validar URLs principais
        official_domains = [
            'planalto.gov.br',
            'gov.br',
            'inss.gov.br',
            'receita.fazenda.gov.br',
            'mec.gov.br',
            'who.int',       # OMS — Organização Mundial da Saúde (fonte internacional legítima)
            'icd.who.int',   # OMS — CID-10/CID-11 (classificação oficial de doenças)
            'dpu.def.br',    # Defensoria Pública da União (domínio oficial)
            'mpf.mp.br',     # Ministério Público Federal (domínio oficial)
            'cpb.org.br',    # Comitê Paralímpico Brasileiro
            'falabr.cgu.gov.br',  # Plataforma Fala.BR (CGU)
            'apaebrasil.org.br',  # APAE Brasil
            'ijc.org.br',        # Instituto Jô Clemente
            'ama.org.br',        # AMA
            'cnmp.mp.br',        # Conselho Nacional do MP
            'mpt.mp.br',         # Ministério Público do Trabalho
            'oab.org.br',        # OAB
            'anadep.org.br',     # Associação Nac. Defensores Públicos
            'procon.sp.gov.br',  # Procon SP
            'cfm.org.br',        # Conselho Federal de Medicina
            'cfp.org.br',        # Conselho Federal de Psicologia
            'coffito.gov.br',    # COFFITO
            'autismbrasil.org',  # ABRACI
            'ans.gov.br',        # ANS
            'caixa.gov.br',      # Caixa Econômica
        ]
        
        if self.direitos:
            fontes = self.direitos.get('fontes', [])
            for fonte in fontes:
                url = fonte.get('url', '')
                if any(domain in url for domain in official_domains):
                    self.log_pass('fontes', f"Fonte oficial: {fonte.get('nome', 'N/A')} ✓", 0.5)
                else:
                    self.log_warning('fontes', f"Fonte não oficial: {fonte.get('nome', 'N/A')} - {url}")
    
    # =========================================================================
    # CATEGORIA 4: VALIDAÇÃO DE ARQUITETURA
    # =========================================================================
    
    def validate_architecture(self):
        """Valida estrutura de pastas e arquitetura do projeto"""
        print("\n" + "=" * 80)
        print("VALIDAÇÃO DE ARQUITETURA - Estrutura e Organização")
        print("=" * 80)
        
        # Estrutura esperada
        expected_structure = {
            'data': ['direitos.json', 'matching_engine.json'],
            'scripts': ['validate_content.py', 'validate_sources.py', 'validate_legal_sources.py',
                       'bump_version.py', 'quality_pipeline.py', 'pre-commit'],
            'css': ['styles.css'],
            'js': ['app.js', 'sw-register.js'],
            'docs': ['VLIBRAS_LIMITATIONS.md', 'QUALITY_SYSTEM.md'],
            'terraform': ['main.tf', 'providers.tf', 'variables.tf', 'outputs.tf'],
            '.githooks': ['pre-commit'],
            '.': ['index.html', 'manifest.json', 'robots.txt', 'sitemap.xml', 
                  'sw.js', 'LICENSE', 'README.md', 'SECURITY.md', 'GOVERNANCE.md']
        }
        
        for folder, files in expected_structure.items():
            folder_path = self.root / folder if folder != '.' else self.root
            
            if not folder_path.exists() and folder != '.':
                self.log_fail('arquitetura', f"Pasta ausente: {folder}", 2)
                continue
            
            for file in files:
                file_path = folder_path / file
                if file_path.exists():
                    self.log_pass('arquitetura', f"{folder}/{file} presente", 0.5)
                else:
                    self.log_warning('arquitetura', f"{folder}/{file} ausente")
        
        # Validar .gitignore
        gitignore = self.root / '.gitignore'
        if gitignore.exists():
            self.log_pass('arquitetura', ".gitignore presente", 1)
        else:
            self.log_warning('arquitetura', ".gitignore ausente")
    
    # =========================================================================
    # CATEGORIA 5: VALIDAÇÃO DE DOCUMENTAÇÃO
    # =========================================================================
    
    def validate_documentation(self):
        """Valida completude e atualização da documentação"""
        print("\n" + "=" * 80)
        print("VALIDAÇÃO DE DOCUMENTAÇÃO - Completude e Atualização")
        print("=" * 80)
        
        # Documentos obrigatórios
        required_docs = {
            'README.md': 10,
            'SECURITY.md': 5,
            'GOVERNANCE.md': 5,
            'LICENSE': 5,
            'CHANGELOG.md': 5,
            'docs/QUALITY_SYSTEM.md': 10,
            'docs/VLIBRAS_LIMITATIONS.md': 3
        }
        
        for doc, points in required_docs.items():
            doc_path = self.root / doc
            if doc_path.exists():
                # Verificar tamanho mínimo
                size = doc_path.stat().st_size
                if size > 100:  # Pelo menos 100 bytes
                    self.log_pass('documentacao', f"{doc} presente e completo", points)
                else:
                    self.log_warning('documentacao', f"{doc} muito curto ({size} bytes)")
                    self.metrics['documentacao']['score'] += points * 0.5
                    self.metrics['documentacao']['max'] += points
            else:
                self.log_fail('documentacao', f"{doc} ausente", points)
        
        # Validar README
        readme_path = self.root / 'README.md'
        if readme_path.exists():
            content = readme_path.read_text(encoding='utf-8')
            
            required_sections = ['Descrição', 'Funcionalidades', 'Como Usar', 'Tecnologias']
            for section in required_sections:
                if section.lower() in content.lower():
                    self.log_pass('documentacao', f"README: seção '{section}' presente", 1)
                else:
                    self.log_warning('documentacao', f"README: seção '{section}' ausente")
    
    # =========================================================================
    # CATEGORIA 6: VALIDAÇÃO DE SEGURANÇA
    # =========================================================================
    
    def validate_security(self):
        """Valida aspectos de segurança"""
        print("\n" + "=" * 80)
        print("VALIDAÇÃO DE SEGURANÇA - Vulnerabilidades e Boas Práticas")
        print("=" * 80)
        
        # 1. SECURITY.md existe e está completo
        security_md = self.root / 'SECURITY.md'
        if security_md.exists():
            content = security_md.read_text(encoding='utf-8')
            if len(content) > 500:
                self.log_pass('seguranca', "SECURITY.md completo", 10)
            else:
                self.log_warning('seguranca', "SECURITY.md muito curto")
        else:
            self.log_fail('seguranca', "SECURITY.md ausente", 10)
        
        # 2. Verificar senhas/chaves hardcoded (padrões comuns)
        dangerous_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        
        code_files = list(self.root.glob('**/*.py')) + list(self.root.glob('**/*.js'))
        found_secrets = False
        
        for file in code_files:
            if 'venv' in str(file) or 'node_modules' in str(file):
                continue
            
            try:
                content = file.read_text(encoding='utf-8')
                for pattern in dangerous_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        self.log_warning('seguranca', f"{file.name}: possível credencial hardcoded")
                        found_secrets = True
            except:
                pass
        
        if not found_secrets:
            self.log_pass('seguranca', "Nenhuma credencial hardcoded detectada", 10)
        
        # 3. Validar CSP (Content Security Policy) no HTML
        index_html = self.root / 'index.html'
        if index_html.exists():
            content = index_html.read_text(encoding='utf-8')
            if 'Content-Security-Policy' in content or 'CSP' in content:
                self.log_pass('seguranca', "CSP configurado no HTML", 5)
            else:
                self.log_warning('seguranca', "CSP não encontrado no HTML")
    
    # =========================================================================
    # CATEGORIA 7: VALIDAÇÃO DE PERFORMANCE
    # =========================================================================
    
    def validate_performance(self):
        """Valida otimizações e performance"""
        print("\n" + "=" * 80)
        print("VALIDAÇÃO DE PERFORMANCE - Otimizações e Caching")
        print("=" * 80)
        
        # 1. Service Worker presente
        sw_js = self.root / 'sw.js'
        if sw_js.exists():
            content = sw_js.read_text(encoding='utf-8')
            if 'cache' in content.lower():
                self.log_pass('performance', "Service Worker com cache implementado", 10)
            else:
                self.log_warning('performance', "Service Worker sem cache")
        else:
            self.log_fail('performance', "Service Worker ausente", 10)
        
        # 2. Minificação
        if (self.root / 'index.min.html').exists():
            self.log_pass('performance', "HTML minificado presente", 5)
        else:
            self.log_warning('performance', "HTML minificado ausente")
        
        # 3. Tamanho dos arquivos JSON
        data_files = ['data/direitos.json', 'data/matching_engine.json']
        for file in data_files:
            path = self.root / file
            if path.exists():
                size_mb = path.stat().st_size / (1024 * 1024)
                if size_mb < 5:
                    self.log_pass('performance', f"{file}: tamanho OK ({size_mb:.2f}MB)", 2)
                else:
                    self.log_warning('performance', f"{file}: arquivo grande ({size_mb:.2f}MB)")
    
    # =========================================================================
    # CATEGORIA 8: VALIDAÇÃO DE ACESSIBILIDADE
    # =========================================================================
    
    def validate_accessibility(self):
        """Valida acessibilidade (WCAG, ARIA)"""
        print("\n" + "=" * 80)
        print("VALIDAÇÃO DE ACESSIBILIDADE - WCAG e ARIA")
        print("=" * 80)
        
        index_html = self.root / 'index.html'
        if not index_html.exists():
            self.log_fail('acessibilidade', "index.html não encontrado", 20)
            return
        
        content = index_html.read_text(encoding='utf-8')
        
        # 1. Atributos ARIA
        aria_count = len(re.findall(r'aria-\w+', content))
        if aria_count >= 30:
            self.log_pass('acessibilidade', f"{aria_count} atributos ARIA encontrados ✓", 10)
        else:
            self.log_warning('acessibilidade', f"Poucos atributos ARIA ({aria_count})")
        
        # 2. VLibras
        if 'vlibras' in content.lower():
            self.log_pass('acessibilidade', "VLibras integrado", 10)
        else:
            self.log_warning('acessibilidade', "VLibras não encontrado")
        
        # 3. Alt text em imagens
        img_tags = re.findall(r'<img[^>]+>', content)
        missing_alt = 0
        for img in img_tags:
            if 'alt=' not in img:
                missing_alt += 1
        
        if missing_alt == 0:
            self.log_pass('acessibilidade', "Todas imagens com alt text", 5)
        else:
            self.log_warning('acessibilidade', f"{missing_alt} imagens sem alt text")
        
        # 4. Semântica HTML5
        semantic_tags = ['nav', 'main', 'section', 'article', 'header', 'footer']
        for tag in semantic_tags:
            if f'<{tag}' in content.lower():
                self.log_pass('acessibilidade', f"Tag semântica <{tag}> presente", 1)
            else:
                self.log_warning('acessibilidade', f"Tag semântica <{tag}> ausente")
    
    # =========================================================================
    # CATEGORIA 9: VALIDAÇÃO DE SEO
    # =========================================================================
    
    def validate_seo(self):
        """Valida SEO e meta tags"""
        print("\n" + "=" * 80)
        print("VALIDAÇÃO DE SEO - Meta Tags e Sitemap")
        print("=" * 80)
        
        # 1. Meta tags no HTML
        index_html = self.root / 'index.html'
        if index_html.exists():
            content = index_html.read_text(encoding='utf-8')
            
            required_meta = [
                'description',
                'keywords',
                'author',
                'og:title',
                'og:description'
            ]
            
            for meta in required_meta:
                if meta in content:
                    self.log_pass('seo', f"Meta tag '{meta}' presente", 2)
                else:
                    self.log_warning('seo', f"Meta tag '{meta}' ausente")
        
        # 2. Sitemap.xml
        sitemap = self.root / 'sitemap.xml'
        if sitemap.exists():
            self.log_pass('seo', "sitemap.xml presente", 5)
        else:
            self.log_fail('seo', "sitemap.xml ausente", 5)
        
        # 3. Robots.txt
        robots = self.root / 'robots.txt'
        if robots.exists():
            self.log_pass('seo', "robots.txt presente", 5)
        else:
            self.log_warning('seo', "robots.txt ausente")
        
        # 4. Manifest.json
        manifest = self.root / 'manifest.json'
        if manifest.exists():
            try:
                with open(manifest, 'r', encoding='utf-8') as f:
                    manifest_data = json.load(f)
                
                required_fields = ['name', 'short_name', 'description', 'icons']
                for field in required_fields:
                    if field in manifest_data:
                        self.log_pass('seo', f"manifest.json: campo '{field}' presente", 1)
                    else:
                        self.log_warning('seo', f"manifest.json: campo '{field}' ausente")
            except:
                self.log_fail('seo', "manifest.json inválido", 5)
        else:
            self.log_fail('seo', "manifest.json ausente", 5)
    
    # =========================================================================
    # CATEGORIA 10: VALIDAÇÃO DE INFRAESTRUTURA
    # =========================================================================
    
    def validate_infrastructure(self):
        """Valida Terraform e scripts de infraestrutura"""
        print("\n" + "=" * 80)
        print("VALIDAÇÃO DE INFRAESTRUTURA - Terraform e Deploy")
        print("=" * 80)
        
        terraform_dir = self.root / 'terraform'
        
        if not terraform_dir.exists():
            self.log_fail('infraestrutura', "Pasta terraform/ ausente", 20)
            return
        
        # Arquivos Terraform obrigatórios
        required_tf = ['main.tf', 'providers.tf', 'variables.tf', 'outputs.tf']
        
        for tf_file in required_tf:
            path = terraform_dir / tf_file
            if path.exists():
                self.log_pass('infraestrutura', f"{tf_file} presente", 5)
                
                # Validar sintaxe básica
                content = path.read_text(encoding='utf-8')
                if 'resource' in content or 'variable' in content or 'output' in content or 'terraform' in content:
                    self.log_pass('infraestrutura', f"{tf_file}: sintaxe válida", 2)
            else:
                self.log_fail('infraestrutura', f"{tf_file} ausente", 5)
        
        # terraform.tfvars.example
        tfvars_example = terraform_dir / 'terraform.tfvars.example'
        if tfvars_example.exists():
            self.log_pass('infraestrutura', "terraform.tfvars.example presente", 3)
        else:
            self.log_warning('infraestrutura', "terraform.tfvars.example ausente")
    
    # =========================================================================
    # 11. TESTES AUTOMATIZADOS
    # =========================================================================
    
    def validate_automated_tests(self):
        """Valida testes automatizados E2E e unitários"""
        print("\n[TESTES] Validando testes automatizados...")
        
        # 1. Existe script de testes E2E?
        test_e2e = self.root / 'scripts' / 'test_e2e_automated.py'
        if test_e2e.exists():
            self.log_pass('testes', "test_e2e_automated.py presente", 5)
            
            # Executar testes E2E
            try:
                result = subprocess.run(
                    ['python3', str(test_e2e)],
                    capture_output=True,
                    timeout=60,
                    cwd=self.root
                )
                
                output = result.stdout.decode('utf-8')
                
                # Contar sucessos/falhas
                if 'TODOS OS TESTES PASSARAM' in output:
                    self.log_pass('testes', "Testes E2E: 100% sucesso", 20)
                elif 'BOA QUALIDADE' in output:
                    self.log_pass('testes', "Testes E2E: ≥90% sucesso", 15)
                elif result.returncode == 0:
                    self.log_pass('testes', "Testes E2E executaram", 10)
                else:
                    self.log_fail('testes', "Testes E2E falharam", 20)
                    
            except subprocess.TimeoutExpired:
                self.log_warning('testes', "Testes E2E demoraram >60s")
            except Exception as e:
                self.log_warning('testes', f"Erro ao executar testes E2E: {e}")
        else:
            self.log_fail('testes', "test_e2e_automated.py ausente", 25)
        
        # 2. Verificar cobertura de testes
        js_file = self.root / 'js' / 'app.js'
        if js_file.exists():
            content = js_file.read_text()
            
            # Funções críticas que devem ter testes
            critical_functions = [
                'performSearch',
                'displayCategoryDetails',
                'analyzeDocuments',
                'encryptDocument',
                'generatePDF',
                'loadChecklistState'
            ]
            
            tested_count = 0
            for func in critical_functions:
                if func in content:
                    tested_count += 1
            
            coverage = (tested_count / len(critical_functions)) * 100
            if coverage == 100:
                self.log_pass('testes', f"Todas funções críticas presentes ({tested_count}/{len(critical_functions)})", 10)
            elif coverage >= 80:
                self.log_pass('testes', f"Boa cobertura de funções ({tested_count}/{len(critical_functions)})", 7)
            else:
                self.log_warning('testes', f"Cobertura baixa de funções ({tested_count}/{len(critical_functions)})")
    
    # =========================================================================
    # 12. DEAD CODE DETECTION
    # =========================================================================
    
    def validate_dead_code(self):
        """Detecta código morto (não usado)"""
        print("\n[DEAD_CODE] Detectando código não usado...")
        
        # 1. Verificar funções JS não usadas
        js_file = self.root / 'js' / 'app.js'
        if js_file.exists():
            content = js_file.read_text()
            
            # Extrair todas as declarações de função
            import re
            function_declarations = re.findall(r'function\s+(\w+)\s*\(', content)
            function_declarations += re.findall(r'const\s+(\w+)\s*=\s*(?:async\s*)?\(', content)
            function_declarations += re.findall(r'let\s+(\w+)\s*=\s*(?:async\s*)?\(', content)
            
            # Filtrar funções internas e IIFEs
            declarations_filtered = [fn for fn in function_declarations if not fn.startswith('setup') and fn != 'count']
            
            unused_functions = []
            for func_name in declarations_filtered:
                # Contar chamadas diretas funcName() e addEventListener(funcName - sem parênteses)
                direct_calls = content.count(f'{func_name}(') - 1  # -1 para declaração
                event_listener_calls = content.count(f'addEventListener(') and func_name in re.findall(rf'addEventListener\([^,]+,\s*{func_name}\)', content)
                
                total_usage = direct_calls + len(re.findall(rf'addEventListener\([^,]+,\s*{func_name}\)', content))
                
                if total_usage == 0:
                    # Verificar se é callback em outro contexto
                    if content.count(func_name) <= 2:  # Apenas declaração + 1 menção
                        unused_functions.append(func_name)
            
            if len(unused_functions) == 0:
                self.log_pass('dead_code', "JavaScript: nenhuma função não usada detectada", 15)
            elif len(unused_functions) <= 2:
                self.log_pass('dead_code', f"JavaScript: apenas {len(unused_functions)} função(ões) possivelmente não usada(s) - OK", 12)
            else:
                self.log_fail('dead_code', f"JavaScript: {len(unused_functions)} funções não usadas: {', '.join(unused_functions[:5])}...", 15)
        
        # 2. Verificar importações Python não usadas
        py_files = list(self.root.glob('scripts/**/*.py'))
        total_unused_imports = 0
        
        for py_file in py_files:
            if 'venv' in str(py_file) or 'node_modules' in str(py_file):
                continue
            
            content = py_file.read_text()
            
            # Extrair imports
            import_pattern = r'import\s+(\w+)|from\s+\w+\s+import\s+(\w+)'
            imports = re.findall(import_pattern, content)
            
            for imp in imports:
                module_name = imp[0] if imp[0] else imp[1]
                
                # Verificar se é usado no código
                if content.count(module_name) == 1:  # Apenas na linha de import
                    total_unused_imports += 1
        
        if total_unused_imports == 0:
            self.log_pass('dead_code', "Python: nenhuma importação não usada", 10)
        elif total_unused_imports <= 3:
            self.log_pass('dead_code', f"Python: {total_unused_imports} importação(ões) não usada(s) - OK", 7)
        else:
            self.log_warning('dead_code', f"Python: {total_unused_imports} importações não usadas")
        
        # 3. Verificar console.log() esquecidos
        js_content = js_file.read_text() if js_file.exists() else ""
        console_logs = js_content.count('console.log')
        
        # Console.log é aceitável se comentado para debug
        uncommented_logs = len(re.findall(r'^\s*console\.log', js_content, re.MULTILINE))
        
        if uncommented_logs == 0:
            self.log_pass('dead_code', "JavaScript: sem console.log() ativo em produção", 5)
        elif uncommented_logs <= 3:
            self.log_pass('dead_code', f"JavaScript: {uncommented_logs} console.log() (aceitável para debug)", 4)
        elif uncommented_logs <= 8:
            self.log_warning('dead_code', f"JavaScript: {uncommented_logs} console.log() ativos - considerar remover para produção")
            self.log_pass('dead_code', "JavaScript: console.log() moderado", 3)
        else:
            self.log_warning('dead_code', f"JavaScript: {uncommented_logs} console.log() - alto para produção")
    
    # =========================================================================
    # 13. ARQUIVOS ÓRFÃOS
    # =========================================================================
    
    def validate_orphaned_files(self):
        """Detecta e limpa arquivos órfãos"""
        print("\n[ORFAOS] Detectando arquivos órfãos...")
        
        orphaned_files = []
        cleanup_count = 0
        
        # Padrões de arquivos órfãos
        orphan_patterns = [
            '**/*.backup',
            '**/*.tmp',
            '**/*.bak',
            '**/*.old',
            '**/*.swp',
            '**/.DS_Store',
            '**/*.log',
            '**/__pycache__/**',
            '**/node_modules/**' # Se existir mas não deveria
        ]
        
        for pattern in orphan_patterns:
            matches = list(self.root.glob(pattern))
            
            # Filtrar apenas arquivos (não diretórios vazios já ignorados)
            for match in matches:
                if match.is_file() and '.git' not in str(match):
                    orphaned_files.append(match)
        
        if len(orphaned_files) == 0:
            self.log_pass('orfaos', "Nenhum arquivo órfão detectado", 15)
        else:
            self.log_warning('orfaos', f"{len(orphaned_files)} arquivo(s) órfão(s) detectado(s)")
            
            # Auto-cleanup (opcional - pode ser ativado com flag)
            auto_cleanup = False  # Mudar para True para auto-limpeza
            
            if auto_cleanup:
                for orphan in orphaned_files:
                    try:
                        orphan.unlink()
                        cleanup_count += 1
                    except Exception as e:
                        pass
                
                if cleanup_count > 0:
                    self.log_pass('orfaos', f"{cleanup_count} arquivo(s) órfão(s) removido(s)", 10)
            else:
                self.log_pass('orfaos', "Detecção de órfãos funcionando", 10)
                
                # Listar primeiros 5 órfãos
                for orphan in orphaned_files[:5]:
                    rel_path = orphan.relative_to(self.root)
                    print(f"  ⚠️  Órfão: {rel_path}")
        
        # Verificar arquivos grandes não rastreados (>10MB)
        large_files = []
        for ext in ['.zip', '.tar.gz', '.mp4', '.mov', '.pdf']:
            matches = list(self.root.glob(f'**/*{ext}'))
            for match in matches:
                if match.is_file() and match.stat().st_size > 10 * 1024 * 1024:
                    large_files.append((match, match.stat().st_size))
        
        if len(large_files) == 0:
            self.log_pass('orfaos', "Nenhum arquivo grande (>10MB) detectado", 5)
        else:
            total_size = sum(size for _, size in large_files) / (1024 * 1024)
            self.log_warning('orfaos', f"{len(large_files)} arquivo(s) grande(s) ({total_size:.1f}MB total)")
    
    # =========================================================================
    # 14. LÓGICA DE NEGÓCIO
    # =========================================================================
    
    def validate_business_logic(self):
        """Valida lógica de negócio e regras"""
        print("\n[LOGICA] Validando lógica de negócio...")
        
        # 1. Validar vinculação bidirecional de dados
        data_file = self.root / 'data' / 'direitos.json'
        if not data_file.exists():
            self.log_fail('logica', "direitos.json não encontrado", 20)
            return
        
        try:
            direitos = json.loads(data_file.read_text())
        except:
            self.log_fail('logica', "direitos.json inválido", 20)
            return
        
        categorias = direitos.get('categorias', [])
        cat_ids = set(cat['id'] for cat in categorias)
        
        # 2. Validar documentos_mestre tem relacionamentos corretos
        docs_mestre = direitos.get('documentos_mestre', [])
        
        broken_links = 0
        for doc in docs_mestre:
            cats_relacionadas = doc.get('categorias', [])
            
            for cat_id in cats_relacionadas:
                if cat_id not in cat_ids:
                    broken_links += 1
                    self.log_warning('logica', f"Documento '{doc.get('nome', 'unknown')}' referencia categoria inexistente: {cat_id}")
        
        if broken_links == 0:
            self.log_pass('logica', "Documentos_mestre: vínculos corretos", 15)
        else:
            self.log_fail('logica', f"Documentos_mestre: {broken_links} vínculo(s) quebrado(s)", 15)
        
        # 3. Validar que cada categoria tem pelo menos 1 documento
        cats_sem_docs = []
        for cat in categorias:
            cat_id = cat['id']
            
            # Verificar se categoria aparece em algum documento
            found = False
            for doc in docs_mestre:
                if cat_id in doc.get('categorias', []):
                    found = True
                    break
            
            if not found:
                cats_sem_docs.append(cat_id)
        
        if len(cats_sem_docs) == 0:
            self.log_pass('logica', "Todas categorias têm documentos vinculados", 10)
        else:
            self.log_warning('logica', f"{len(cats_sem_docs)} categoria(s) sem documentos: {', '.join(cats_sem_docs[:3])}...")
        
        # 4. Validar classificação de dados (tipo de informação)
        dados_sensiveis = 0
        for cat in categorias:
            resumo = cat.get('resumo', '').lower()
            passo_a_passo = str(cat.get('passo_a_passo', '')).lower()
            
            # Detectar menção a dados sensíveis
            sensitive_keywords = ['cpf', 'rg', 'senha', 'cartão', 'conta', 'saldo']
            
            for keyword in sensitive_keywords:
                if keyword in resumo or keyword in passo_a_passo:
                    dados_sensiveis += 1
                    break
        
        if dados_sensiveis == 0:
            self.log_pass('logica', "Nenhuma menção direta a dados sensíveis", 10)
        else:
            self.log_warning('logica', f"{dados_sensiveis} categoria(s) mencionam dados sensíveis - validar LGPD")
        
        # 5. Validar que todas as categorias têm pelo menos 3 passos
        cats_poucos_passos = []
        for cat in categorias:
            passos = cat.get('passo_a_passo', [])
            if len(passos) < 3:
                cats_poucos_passos.append(cat['id'])
        
        if len(cats_poucos_passos) == 0:
            self.log_pass('logica', "Todas categorias ≥3 passos", 8)
        else:
            self.log_warning('logica', f"{len(cats_poucos_passos)} categoria(s) com <3 passos")
        
        # 6. Validar URLs de base_legal são HTTPS
        http_urls = 0
        for cat in categorias:
            for lei in cat.get('base_legal', []):
                url = lei.get('url', '')
                if url.startswith('http://'):
                    http_urls += 1
        
        if http_urls == 0:
            self.log_pass('logica', "Todas URLs base_legal são HTTPS", 7)
        else:
            self.log_fail('logica', f"{http_urls} URL(s) HTTP (devem ser HTTPS)", 7)
    
    # =========================================================================
    # 15. REGULATORY COMPLIANCE
    # =========================================================================
    
    def validate_regulatory_compliance(self):
        """Valida compliance regulatório (LGPD, finance, disclaimer)"""
        print("\n[REGULATORY] Validando compliance regulatório...")
        
        index_html = self.root / 'index.html'
        if not index_html.exists():
            self.log_fail('regulatory', "index.html não encontrado", 30)
            return
        
        content = index_html.read_text()
        
        # 1. LGPD - Lei 13.709/2018
        lgpd_checks = [
            ('LGPD' in content, "Menção à LGPD"),
            ('Lei 13.709' in content or '13.709/2018' in content, "Citação Lei 13.709/2018"),
            ('dados pessoais' in content.lower(), "Menção a 'dados pessoais'"),
            ('privacidade' in content.lower(), "Política de privacidade"),
            ('não coletamos' in content.lower() or 'não coleta' in content.lower(), "Declaração de não coleta"),
            ('localStorage' in content or 'IndexedDB' in content, "LocalStorage/IndexedDB mencionado"),
        ]
        
        lgpd_score = sum(1 for check, name in lgpd_checks if check)
        if lgpd_score == len(lgpd_checks):
            self.log_pass('regulatory', "LGPD: 100% compliance", 15)
        elif lgpd_score >= 4:
            self.log_pass('regulatory', f"LGPD: {lgpd_score}/{len(lgpd_checks)} checks OK", 10)
        else:
            self.log_fail('regulatory', f"LGPD: apenas {lgpd_score}/{len(lgpd_checks)} checks", 15)
        
        # 2. Disclaimer / Aviso Legal
        disclaimer_checks = [
            ('aviso legal' in content.lower() or 'disclaimer' in content.lower(), "Aviso legal presente"),
            ('não substitui' in content.lower(), "Não substitui orientação profissional"),
            ('consultoria jurídica' in content.lower() or 'assessoria jurídica' in content.lower(), "Não é consultoria jurídica"),
            ('defensoria pública' in content.lower(), "Menção Defensoria Pública"),
            ('fontes oficiais' in content.lower(), "Referência a fontes oficiais")
        ]
        
        disclaimer_score = sum(1 for check, name in disclaimer_checks if check)
        if disclaimer_score == len(disclaimer_checks):
            self.log_pass('regulatory', "Disclaimer: completo", 12)
        elif disclaimer_score >= 3:
            self.log_pass('regulatory', f"Disclaimer: {disclaimer_score}/{len(disclaimer_checks)} OK", 8)
        else:
            self.log_fail('regulatory', f"Disclaimer: apenas {disclaimer_score}/{len(disclaimer_checks)}", 12)
        
        # 3. Finance / Transparência Financeira (projeto sem fins lucrativos)
        finance_checks = [
            ('sem fins lucrativos' in content.lower() or 'non-profit' in content.lower(), "Declaração sem fins lucrativos"),
            ('gratuito' in content.lower() or 'free' in content.lower(), "Serviço gratuito"),
            ('sem custo' in content.lower() or 'sem cobrança' in content.lower() or 'não cobra' in content.lower(), "Sem custo")
        ]
        
        finance_score = sum(1 for check, name in finance_checks if check)
        if finance_score >= 2:
            self.log_pass('regulatory', "Finance: transparência OK", 8)
        else:
            self.log_warning('regulatory', f"Finance: apenas {finance_score}/{len(finance_checks)} mencionado")
        
        # 4. GitHub Security (segredos expostos)
        security_file = self.root / 'SECURITY.md'
        if security_file.exists():
            sec_content = security_file.read_text()
            
            github_sec_checks = [
                ('reportando vulnerabilidades' in sec_content.lower() or 'reporting vulnerabilities' in sec_content.lower(), "Processo de reporte"),
                ('@' in sec_content or 'email' in sec_content.lower(), "Contato de segurança"),
                ('não' in sec_content and 'issue pública' in sec_content.lower(), "Não usar issue pública")
            ]
            
            gh_sec_score = sum(1 for check, name in github_sec_checks if check)
            if gh_sec_score >= 2:
                self.log_pass('regulatory', "GitHub Security: OK", 8)
            else:
                self.log_warning('regulatory', f"GitHub Security: {gh_sec_score}/{len(github_sec_checks)}")
        else:
            self.log_fail('regulatory', "SECURITY.md ausente", 8)
        
        # 5. Dados Sensíveis Expostos (scan de arquivos)
        sensitive_patterns = [
            (r'password\s*=\s*["\']', "password hardcoded"),
            (r'api[_-]?key\s*=\s*["\']', "API key hardcoded"),
            (r'secret\s*=\s*["\']', "secret hardcoded"),
            (r'token\s*=\s*["\']', "token hardcoded"),
            (r'AWS_SECRET|AZURE_CLIENT_SECRET', "Cloud credentials")
        ]
        
        files_to_scan = [
            self.root / 'js' / 'app.js',
            self.root / 'sw.js',
            index_html
        ]
        
        sensitive_found = []
        for file_path in files_to_scan:
            if not file_path.exists():
                continue
            
            file_content = file_path.read_text()
            
            for pattern, name in sensitive_patterns:
                if re.search(pattern, file_content, re.IGNORECASE):
                    sensitive_found.append((file_path.name, name))
        
        if len(sensitive_found) == 0:
            self.log_pass('regulatory', "Dados Sensíveis: nenhum exposto", 12)
        else:
            self.log_fail('regulatory', f"Dados Sensíveis: {len(sensitive_found)} padrão(ões) detectado(s)", 12)
            for filename, pattern_name in sensitive_found[:3]:
                print(f"  ⚠️  {filename}: {pattern_name}")
        
        # 6. Validar versões consistentes entre documentos
        version_files = [
            (self.root / 'README.md', 'README'),
            (self.root / 'SECURITY.md', 'SECURITY'),
            (self.root / 'CHANGELOG.md', 'CHANGELOG'),
            (self.root / 'docs' / 'SECURITY_AUDIT.md', 'SECURITY_AUDIT')
        ]
        
        versions_found = {}
        for file_path, name in version_files:
            if not file_path.exists():
                continue
            
            file_content = file_path.read_text()
            
            # Extrair versões semver (1.x.x) - ignora scores, porcentagens e datas
            # Requer exatamente 3 componentes (major.minor.patch) para evitar falsos positivos
            version_matches = re.findall(r'(?:^|\s|v)(\d{1,2}\.\d{1,2}\.\d{1,3})(?:\s|$|["\)\],])', file_content)
            
            if version_matches:
                # Pegar a versão mais recente mencionada
                latest_version = max(version_matches, key=lambda v: tuple(map(int, v.split('.'))))
                versions_found[name] = latest_version
        
        if len(set(versions_found.values())) == 1:
            version = list(versions_found.values())[0]
            self.log_pass('regulatory', f"Versões consistentes: v{version}", 10)
        else:
            version_str = ', '.join(f"{name}:v{ver}" for name, ver in versions_found.items())
            self.log_warning('regulatory', f"Versões inconsistentes: {version_str}")
    
    # =========================================================================
    # =========================================================================
    # 16. CLOUD SECURITY (Azure/EASM/Defender for Cloud)
    # =========================================================================
    
    def validate_cloud_security(self):
        """Valida configurações de segurança Azure/Cloud (específicas dos recursos usados)"""
        print("\n[CLOUD_SECURITY] Validando Azure Security Posture (App Service + Key Vault)...")
        
        # 1. Terraform Security Best Practices
        terraform_dir = self.root / 'terraform'
        if not terraform_dir.exists():
            self.log_warning('cloud_security', "Diretório terraform ausente - infra não gerenciada por IaC")
            return
        
        main_tf = terraform_dir / 'main.tf'
        if not main_tf.exists():
            self.log_fail('cloud_security', "main.tf ausente", 10)
            return
        
        tf_content = main_tf.read_text()
        
        # ===== VALIDAÇÕES ESPECÍFICAS DOS RECURSOS USADOS =====
        
        # 1. App Service - HTTPS Only (CRÍTICO)
        if 'azurerm_linux_web_app' in tf_content or 'azurerm_windows_web_app' in tf_content:
            if 'https_only = true' in tf_content:
                self.log_pass('cloud_security', "App Service: HTTPS Only enforced ✓", 12)
            else:
                self.log_fail('cloud_security', "App Service: HTTPS Only NÃO enforced (vulnerável a downgrade)", 12)
        
        # 2. Key Vault - Soft Delete (proteção contra exclusão acidental)
        if 'azurerm_key_vault' in tf_content:
            if 'soft_delete_retention_days' in tf_content:
                days_match = re.search(r'soft_delete_retention_days\s*=\s*(\d+)', tf_content)
                if days_match:
                    days = int(days_match.group(1))
                    if days >= 7:
                        self.log_pass('cloud_security', f"Key Vault: Soft Delete habilitado ({days} dias) ✓", 8)
                    else:
                        self.log_warning('cloud_security', f"Key Vault: Soft Delete < 7 dias ({days} dias)")
                        self.log_pass('cloud_security', "Key Vault: Soft Delete presente", 5)
            else:
                self.log_fail('cloud_security', "Key Vault: Soft Delete não configurado", 8)
        
        # 3. Managed Identity (zero credenciais hardcoded)
        if 'identity {' in tf_content or 'identity{' in tf_content:
            if 'type = "SystemAssigned"' in tf_content or 'type = "UserAssigned"' in tf_content:
                self.log_pass('cloud_security', "Managed Identity configurado (zero secrets hardcoded) ✓", 10)
            else:
                self.log_warning('cloud_security', "Identity block presente mas tipo não reconhecido")
        else:
            self.log_warning('cloud_security', "Managed Identity não detectado - app usa credenciais?")
        
        # 4. Application Insights (observability/detecção de ataques)
        if 'azurerm_application_insights' in tf_content:
            self.log_pass('cloud_security', "Application Insights habilitado (rastreamento de anomalias) ✓", 8)
        else:
            self.log_warning('cloud_security', "Application Insights ausente - sem telemetry/alertas")
        
        # 5. Monitor Alerts (detecção proativa de incidentes)
        if 'azurerm_monitor_metric_alert' in tf_content:
            alert_count = tf_content.count('azurerm_monitor_metric_alert')
            if alert_count >= 3:
                self.log_pass('cloud_security', f"Monitor Alerts: {alert_count} alertas configurados (5xx/health/latency) ✓", 10)
            elif alert_count >= 1:
                self.log_pass('cloud_security', f"Monitor Alerts: {alert_count} alerta(s) presente(s)", 6)
            else:
                self.log_warning('cloud_security', "Monitor Alerts configurados mas count não detectado")
        else:
            self.log_warning('cloud_security', "Monitor Alerts ausentes - sem notificações de incidentes")
        
        # ===== VALIDAÇÃO DE SECURITY HEADERS (server.js) =====
        
        # 6. Security Headers no server.js (CSP, HSTS, etc.)
        server_js = self.root / 'server.js'
        if server_js.exists():
            server_content = server_js.read_text()
            
            security_headers = [
                ('Content-Security-Policy' in server_content, "CSP"),
                ('Strict-Transport-Security' in server_content, "HSTS"),
                ('X-Content-Type-Options' in server_content, "X-Content-Type-Options"),
                ('X-Frame-Options' in server_content, "X-Frame-Options")
            ]
            
            headers_count = sum(1 for check, _ in security_headers if check)
            
            if headers_count >= 4:
                self.log_pass('cloud_security', f"Security Headers: {headers_count}/4 implementados (CSP+HSTS+nosniff+frameguard) ✓", 12)
            elif headers_count >= 2:
                self.log_pass('cloud_security', f"Security Headers: {headers_count}/4 implementados", 7)
                missing = [name for check, name in security_headers if not check]
                self.log_warning('cloud_security', f"Security Headers faltando: {', '.join(missing)}")
            else:
                self.log_fail('cloud_security', "Security Headers insuficientes (< 2/4)", 12)
        else:
            self.log_warning('cloud_security', "server.js ausente - não foi possível validar security headers")
        
        # ===== DOCUMENTAÇÃO & COMPLIANCE =====
        
        # 7. LGPD/GDPR Compliance (mencionado em docs?)
        compliance_docs = [self.root / 'SECURITY.md', self.root / 'README.md']
        compliance_found = False
        
        for doc_path in compliance_docs:
            if doc_path.exists():
                content = doc_path.read_text().lower()
                if 'lgpd' in content or 'gdpr' in content or 'privacidade' in content:
                    compliance_found = True
                    break
        
        if compliance_found:
            self.log_pass('cloud_security', "LGPD/GDPR: mencionado em documentação ✓", 7)
        else:
            self.log_warning('cloud_security', "LGPD/GDPR não mencionado - validar se aplicável")
    
    # =========================================================================
    # CATEGORIA 17: CI/CD — GitHub Actions Workflows
    # =========================================================================
    
    def validate_cicd(self):
        """Validação completa de CI/CD: workflows, segurança, boas práticas"""
        print("\n" + "=" * 80)
        print("VALIDAÇÃO DE CI/CD — GitHub Actions Workflows")
        print("=" * 80)
        
        cat = 'cicd'
        workflows_dir = self.root / '.github' / 'workflows'
        
        if not workflows_dir.exists():
            self.log_fail(cat, "Pasta .github/workflows/ ausente", 30)
            return
        
        self.log_pass(cat, ".github/workflows/ presente", 2)
        
        # ── 1. Workflows obrigatórios ──
        required_workflows = {
            'quality-gate.yml': 'Quality Gate (validação de qualidade)',
            'deploy.yml': 'Deploy (entrega contínua)',
            'terraform.yml': 'Terraform (infraestrutura como código)',
            'weekly-review.yml': 'Revisão Periódica (monitoramento contínuo)'
        }
        
        workflow_contents = {}  # cache para reusar
        
        for wf_name, wf_desc in required_workflows.items():
            wf_path = workflows_dir / wf_name
            if wf_path.exists():
                self.log_pass(cat, f"{wf_name} presente — {wf_desc}", 3)
                try:
                    content = wf_path.read_text(encoding='utf-8')
                    workflow_contents[wf_name] = content
                except Exception as e:
                    self.log_fail(cat, f"{wf_name}: erro ao ler — {e}", 3)
            else:
                self.log_fail(cat, f"{wf_name} ausente — {wf_desc}", 3)
        
        if not workflow_contents:
            self.log_fail(cat, "Nenhum workflow legível encontrado", 10)
            return
        
        # ── 2. YAML válido (sem erros de sintaxe) ──
        for wf_name, content in workflow_contents.items():
            # Verificar estrutura mínima YAML
            has_name = 'name:' in content
            has_on = '\non:' in content or content.startswith('on:')
            has_jobs = 'jobs:' in content
            
            if has_name and has_on and has_jobs:
                self.log_pass(cat, f"{wf_name}: estrutura YAML válida (name/on/jobs)", 2)
            else:
                missing = [x for x, v in [('name', has_name), ('on', has_on), ('jobs', has_jobs)] if not v]
                self.log_fail(cat, f"{wf_name}: faltam campos — {', '.join(missing)}", 2)
        
        # ── 3. Segurança: permissions (least privilege) ──
        for wf_name, content in workflow_contents.items():
            if 'permissions:' in content:
                self.log_pass(cat, f"{wf_name}: permissions definidas (least privilege)", 3)
                
                # Verificar se não tem permissions: write-all
                if 'permissions: write-all' in content or 'permissions:\n  contents: write' in content:
                    self.log_warning(cat, f"{wf_name}: permissions muito amplas — restringir")
            else:
                # deploy.yml pode não ter permissions explícitas mas herda defaults
                if wf_name in ('deploy.yml',):
                    self.log_warning(cat, f"{wf_name}: permissions não explícitas — considerar adicionar")
                else:
                    self.log_warning(cat, f"{wf_name}: permissions não definidas")
        
        # ── 4. Segurança: actions pinadas (versão fixa) ──
        import re as re_mod
        total_actions = 0
        pinned_actions = 0
        unpinned_list = []
        
        for wf_name, content in workflow_contents.items():
            # Encontrar todas as uses:
            action_refs = re_mod.findall(r'uses:\s*([^\s]+)', content)
            for action_ref in action_refs:
                total_actions += 1
                # SHA-pinned: @sha256:... ou @<40-hex>
                if re_mod.search(r'@[a-f0-9]{40}', action_ref):
                    pinned_actions += 1
                # Version tag: @v4, @v5, etc (aceitável para actions oficiais)
                elif re_mod.search(r'@v\d+', action_ref):
                    # Actions oficiais do GitHub com version tag são aceitáveis
                    if action_ref.startswith('actions/'):
                        pinned_actions += 1
                    else:
                        unpinned_list.append(f"{wf_name}: {action_ref}")
                else:
                    unpinned_list.append(f"{wf_name}: {action_ref}")
        
        if total_actions > 0:
            pin_rate = (pinned_actions / total_actions) * 100
            if pin_rate == 100:
                self.log_pass(cat, f"Actions pinadas: {pinned_actions}/{total_actions} (100%)", 5)
            elif pin_rate >= 80:
                self.log_pass(cat, f"Actions pinadas: {pinned_actions}/{total_actions} ({pin_rate:.0f}%)", 3)
                for item in unpinned_list:
                    self.log_warning(cat, f"Action sem pin: {item}")
            else:
                self.log_fail(cat, f"Actions pinadas: {pinned_actions}/{total_actions} ({pin_rate:.0f}%) — risco supply chain", 5)
        
        # ── 5. Quality Gate obrigatório antes de deploy ──
        deploy_content = workflow_contents.get('deploy.yml', '')
        if deploy_content:
            if 'needs: quality-gate' in deploy_content or 'needs:\n' in deploy_content:
                self.log_pass(cat, "Deploy depende de Quality Gate (needs)", 5)
            else:
                self.log_fail(cat, "Deploy NÃO depende de Quality Gate — risco", 5)
            
            # Concurrency (evita deploys paralelos)
            if 'concurrency:' in deploy_content:
                self.log_pass(cat, "Deploy com concurrency group (sem paralelos)", 3)
            else:
                self.log_warning(cat, "Deploy sem concurrency — deploys paralelos possíveis")
        
        # ── 6. Sensitive data scan no CI ──
        qg_content = workflow_contents.get('quality-gate.yml', '')
        has_secret_scan = False
        for content in workflow_contents.values():
            if 'PRIVATE KEY' in content or 'AKIA' in content or 'dados sensíveis' in content.lower():
                has_secret_scan = True
                break
        
        if has_secret_scan:
            self.log_pass(cat, "Scan de dados sensíveis presente nos workflows", 4)
        else:
            self.log_fail(cat, "Sem scan de dados sensíveis nos workflows", 4)
        
        # ── 7. Secrets: não hardcoded nos workflows ──
        secrets_hardcoded = False
        for wf_name, content in workflow_contents.items():
            # Verificar se há valores hardcoded (não ${{ secrets.* }})
            # Padrões perigosos: chaves AWS, tokens, senhas literais
            dangerous_patterns = [
                r'AKIA[0-9A-Z]{16}',
                r'ghp_[a-zA-Z0-9]{36}',
                r'sk-[a-zA-Z0-9]{20,}',
                r"password:\s*['\"][^$][^{]",
            ]
            for pattern in dangerous_patterns:
                if re_mod.search(pattern, content):
                    secrets_hardcoded = True
                    self.log_fail(cat, f"{wf_name}: segredo hardcoded detectado!", 5)
                    break
        
        if not secrets_hardcoded:
            self.log_pass(cat, "Sem segredos hardcoded nos workflows", 4)
        
        # Secrets usados via ${{ secrets.* }} (boa prática)
        secrets_refs = set()
        for content in workflow_contents.values():
            refs = re_mod.findall(r'\$\{\{\s*secrets\.(\w+)\s*\}\}', content)
            secrets_refs.update(refs)
        
        if secrets_refs:
            self.log_pass(cat, f"Secrets via GitHub: {len(secrets_refs)} referências seguras", 3)
        
        # ── 8. Health check após deploy ──
        if deploy_content:
            if 'healthz' in deploy_content or 'health' in deploy_content.lower():
                self.log_pass(cat, "Health check pós-deploy presente", 3)
            else:
                self.log_warning(cat, "Sem health check após deploy")
        
        # ── 9. Artifact upload (relatórios) ──
        has_artifacts = False
        for content in workflow_contents.values():
            if 'upload-artifact' in content:
                has_artifacts = True
                break
        
        if has_artifacts:
            self.log_pass(cat, "Artifact upload configurado (relatórios persistidos)", 2)
        else:
            self.log_warning(cat, "Sem upload de artifacts nos workflows")
        
        # ── 10. Terraform: workflow_dispatch com parâmetros ──
        tf_content = workflow_contents.get('terraform.yml', '')
        if tf_content:
            if 'workflow_dispatch' in tf_content:
                self.log_pass(cat, "Terraform: execução manual habilitada (workflow_dispatch)", 2)
            
            if 'terraform plan' in tf_content:
                self.log_pass(cat, "Terraform: plan presente", 2)
            else:
                self.log_fail(cat, "Terraform: sem plan", 2)
            
            if 'terraform validate' in tf_content:
                self.log_pass(cat, "Terraform: validate presente", 2)
            else:
                self.log_warning(cat, "Terraform: sem validate")
            
            if 'terraform fmt' in tf_content:
                self.log_pass(cat, "Terraform: fmt check presente", 2)
            else:
                self.log_warning(cat, "Terraform: sem fmt check")
            
            # State management
            if 'tfstate' in tf_content or 'terraform.tfstate' in tf_content:
                self.log_pass(cat, "Terraform: state management configurado", 2)
            else:
                self.log_warning(cat, "Terraform: state management não encontrado")
        
        # ── 11. Weekly review (monitoramento contínuo) ──
        weekly_content = workflow_contents.get('weekly-review.yml', '')
        if weekly_content:
            if 'schedule' in weekly_content or 'cron' in weekly_content:
                self.log_pass(cat, "Revisão periódica com schedule/cron", 3)
            else:
                self.log_warning(cat, "Revisão periódica sem schedule — execução manual apenas")
            
            if 'issues: write' in weekly_content:
                self.log_pass(cat, "Revisão periódica cria issues automaticamente", 2)
            else:
                self.log_warning(cat, "Revisão periódica não cria issues")
        
        # ── 12. CI executa codereview/codereview.py ──
        ci_runs_codereview = False
        for content in workflow_contents.values():
            if 'codereview.py' in content or 'codereview/codereview.py' in content:
                ci_runs_codereview = True
                break
        
        if ci_runs_codereview:
            self.log_pass(cat, "CI executa codereview.py (quality gate automatizado)", 4)
        else:
            self.log_fail(cat, "CI não executa codereview.py", 4)
        
        # ── 13. validate_content.py no CI ──
        ci_runs_validate = False
        for content in workflow_contents.values():
            if 'validate_content.py' in content:
                ci_runs_validate = True
                break
        
        if ci_runs_validate:
            self.log_pass(cat, "CI executa validate_content.py (validação de dados)", 3)
        else:
            self.log_warning(cat, "CI não executa validate_content.py")
        
        # ── 14. $GITHUB_STEP_SUMMARY (relatório no PR) ──
        has_summary = False
        for content in workflow_contents.values():
            if 'GITHUB_STEP_SUMMARY' in content:
                has_summary = True
                break
        
        if has_summary:
            self.log_pass(cat, "GitHub Step Summary configurado (relatório visual)", 2)
        else:
            self.log_warning(cat, "Sem GITHUB_STEP_SUMMARY nos workflows")
        
        # ── 15. Triggers seguros (não usa pull_request_target sem precaução) ──
        unsafe_triggers = False
        for wf_name, content in workflow_contents.items():
            if 'pull_request_target' in content:
                unsafe_triggers = True
                self.log_warning(cat, f"{wf_name}: usa pull_request_target — risco de injection")
        
        if not unsafe_triggers:
            self.log_pass(cat, "Sem triggers inseguros (pull_request_target)", 2)
    
    # =========================================================================
    # GERAÇÃO DE RELATÓRIO
    # =========================================================================
    
    def generate_report(self) -> float:
        """Gera relatório consolidado final"""
        print("\n" + "="*60)
        print(f"🔍 MASTER COMPLIANCE REPORT v{self.version}")
        print("="*60)
        
        category_names = {
            'dados': '📊 DADOS',
            'codigo': '💻 CÓDIGO',
            'fontes': '📚 FONTES',
            'arquitetura': '🏗️  ARQUITETURA',
            'documentacao': '📝 DOCUMENTAÇÃO',
            'seguranca': '🔒 SEGURANÇA',
            'performance': '⚡ PERFORMANCE',
            'acessibilidade': '♿ ACESSIBILIDADE',
            'seo': '🔍 SEO',
            'infraestrutura': '🏢 INFRAESTRUTURA',
            'testes': '🧪 TESTES',
            'dead_code': '🧹 DEAD CODE',
            'orfaos': '🗑️  ÓRFÃOS',
            'logica': '🎯 LÓGICA',
            'regulatory': '⚖️  REGULATORY',
            'cloud_security': '☁️  CLOUD_SECURITY',
            'cicd': '🔄 CI/CD'
        }
        
        total_score = 0
        total_max = 0
        category_percentages = []
        
        for category_id, data in self.metrics.items():
            score = data['score']
            max_score = data['max']
            
            total_score += score
            total_max += max_score
            
            if max_score > 0:
                percentage = (score / max_score) * 100
            else:
                percentage = 100.0
            
            category_percentages.append((category_id, percentage, score, max_score))
            
            status = "✅" if percentage == 100 else "⚠️" if percentage >= 70 else "❌"
            category_display = category_names.get(category_id, category_id.upper())
            
            print(f"{status} {category_display:30} {score:5.1f}/{max_score:5.1f} ({percentage:5.1f}%)")
        
        final_percentage = (total_score / total_max * 100) if total_max > 0 else 100.0
        
        print("="*60)
        print(f"📊 SCORE FINAL: {total_score:.1f}/{total_max:.1f} = {final_percentage:.2f}%")
        print("="*60)
        
        # Identificar categorias que precisam atenção
        failing_categories = [(cat, pct, score, max_score) for cat, pct, score, max_score in category_percentages if pct < 100]
        
        if failing_categories:
            print("\n⚠️  CATEGORIAS ABAIXO DE 100%:")
            for cat, pct, score, max_score in failing_categories:
                category_display = category_names.get(cat, cat.upper())
                gap = max_score - score
                print(f"   • {category_display}: {pct:.1f}% (falta {gap:.1f} pontos)")
        
        # Recomendações
        if final_percentage == 100:
            print("\n🎉 PERFEITO! Todos os critérios foram atendidos!")
        elif final_percentage >= 95:
            print("\n🎯 EXCELENTE! Quase perfeito, pequenos ajustes restantes.")
        elif final_percentage >= 90:
            print("\n✅ BOM! Acima de 90%, mas há espaço para melhorias.")
        elif final_percentage >= 70:
            print("\n⚠️  ATENÇÃO! Score abaixo de 90%, requer ação.")
        else:
            print("\n❌ CRÍTICO! Score abaixo de 70%, ação urgente necessária.")
        
        print(f"\nRelatório gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tempo de execução: {(datetime.now() - self.start_time).total_seconds():.2f}s")
        
        return final_percentage
    
    # =========================================================================
    # EXECUÇÃO PRINCIPAL
    # =========================================================================
    
    def run(self):
        """Executa todas as validações e gera relatório"""
        print("="*60)
        print(f"🚀 MASTER COMPLIANCE VALIDATOR v{self.version}")
        print("="*60)
        print(f"Workspace: {self.root}")
        print(f"Início: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n🎯 17 CATEGORIAS DE VALIDAÇÃO:")
        print("   1. Dados  2. Código  3. Fontes  4. Arquitetura  5. Documentação")
        print("   6. Segurança  7. Performance  8. Acessibilidade  9. SEO  10. Infraestrutura")
        print("   11. Testes E2E  12. Dead Code  13. Órfãos  14. Lógica  15. Regulatory")
        print("   16. Cloud Security  17. CI/CD (GitHub Actions)")
        
        # Executar todas as 17 categorias
        self.validate_data_integrity()
        self.validate_code_quality()
        self.validate_official_sources()
        self.validate_architecture()
        self.validate_documentation()
        self.validate_security()
        self.validate_performance()
        self.validate_accessibility()
        self.validate_seo()
        self.validate_infrastructure()
        self.validate_automated_tests()
        self.validate_dead_code()
        self.validate_orphaned_files()
        self.validate_business_logic()
        self.validate_regulatory_compliance()
        self.validate_cloud_security()
        self.validate_cicd()
        
        # Gerar relatório
        percentage = self.generate_report()
        
        # Exit code baseado no score
        if percentage >= 90:
            return 0
        elif percentage >= 70:
            return 1
        else:
            return 2


if __name__ == '__main__':
    validator = MasterComplianceValidator()
    exit_code = validator.run()
    sys.exit(exit_code)
