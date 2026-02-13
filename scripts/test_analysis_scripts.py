#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste Automatizado de Scripts de Análise - NossoDireito v1.9.0

Valida todos os scripts Python de análise:
- analise360.py
- analise_funcionalidades.py
- audit_content.py
- bump_version.py
- master_compliance.py
- validate_all.py
- validate_content.py
- validate_govbr_urls.py
- validate_legal_sources.py
- validate_sources.py
"""

import ast
import sys
from pathlib import Path

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


class ScriptTester:
    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.scripts_dir = self.root / "scripts"
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results = []

        # Scripts a serem testados
        self.analysis_scripts = [
            'analise360.py',
            'analise_funcionalidades.py',
            'audit_content.py',
            'bump_version.py',
            'master_compliance.py',
            'validate_all.py',
            'validate_content.py',
            'validate_govbr_urls.py',
            'validate_legal_sources.py',
            'validate_sources.py',
        ]

    def log_success(self, test_name: str, message: str = ""):
        self.passed += 1
        status = f"{GREEN}✓ PASS{RESET}"
        self.results.append((status, test_name, message))
        print(f"{status} {BOLD}{test_name}{RESET}")
        if message:
            print(f"      {message}")

    def log_failure(self, test_name: str, message: str = ""):
        self.failed += 1
        status = f"{RED}✗ FAIL{RESET}"
        self.results.append((status, test_name, message))
        print(f"{status} {BOLD}{test_name}{RESET}")
        if message:
            print(f"      {RED}{message}{RESET}")

    def log_warning(self, test_name: str, message: str = ""):
        self.warnings += 1
        status = f"{YELLOW}⚠ WARN{RESET}"
        self.results.append((status, test_name, message))
        print(f"{status} {BOLD}{test_name}{RESET}")
        if message:
            print(f"      {YELLOW}{message}{RESET}")

    def print_section(self, title: str):
        print(f"\n{CYAN}{'='*70}{RESET}")
        print(f"{CYAN}{BOLD}{title:^70}{RESET}")
        print(f"{CYAN}{'='*70}{RESET}\n")

    def test_file_exists(self, script_name: str) -> bool:
        """Verifica se o script existe"""
        script_path = self.scripts_dir / script_name
        if script_path.exists():
            size_kb = script_path.stat().st_size / 1024
            self.log_success(f"{script_name}: Arquivo existe", f"Tamanho: {size_kb:.1f} KB")
            return True
        else:
            self.log_failure(f"{script_name}: Arquivo não encontrado")
            return False

    def test_python_syntax(self, script_name: str) -> bool:
        """Valida sintaxe Python"""
        script_path = self.scripts_dir / script_name
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                source = f.read()
            ast.parse(source)
            self.log_success(f"{script_name}: Sintaxe Python válida")
            return True
        except SyntaxError as e:
            self.log_failure(f"{script_name}: Erro de sintaxe", f"Linha {e.lineno}: {e.msg}")
            return False
        except Exception as e:
            self.log_failure(f"{script_name}: Erro ao validar sintaxe", str(e))
            return False

    def test_imports(self, script_name: str) -> bool:
        """Verifica se as importações estão corretas"""
        script_path = self.scripts_dir / script_name
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)

            if imports:
                self.log_success(f"{script_name}: Importações encontradas", f"{len(imports)} módulos")
                return True
            else:
                self.log_warning(f"{script_name}: Nenhuma importação encontrada")
                return True
        except Exception as e:
            self.log_failure(f"{script_name}: Erro ao analisar importações", str(e))
            return False

    def test_main_function(self, script_name: str) -> bool:
        """Verifica se o script tem função main ou estrutura executável"""
        script_path = self.scripts_dir / script_name
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                source = f.read()

            has_main = 'def main(' in source
            has_if_main = "if __name__ == '__main__'" in source or 'if __name__ == "__main__"' in source
            has_classes = 'class ' in source
            has_functions = 'def ' in source

            if has_main:
                self.log_success(f"{script_name}: Função main() presente")
                return True
            elif has_if_main:
                self.log_success(f"{script_name}: Bloco __main__ presente")
                return True
            elif has_classes and has_functions:
                self.log_success(f"{script_name}: Classes e funções presentes")
                return True
            elif has_functions:
                self.log_success(f"{script_name}: Funções presentes")
                return True
            else:
                self.log_warning(f"{script_name}: Estrutura executável não detectada")
                return True
        except Exception as e:
            self.log_failure(f"{script_name}: Erro ao verificar estrutura", str(e))
            return False

    def test_shebang_and_encoding(self, script_name: str) -> bool:
        """Verifica shebang e encoding"""
        script_path = self.scripts_dir / script_name
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                second_line = f.readline().strip()

            has_shebang = first_line.startswith('#!') and 'python' in first_line.lower()
            has_encoding = 'coding' in first_line or 'coding' in second_line

            if has_shebang and has_encoding:
                self.log_success(f"{script_name}: Shebang e encoding corretos")
                return True
            elif has_shebang:
                self.log_warning(f"{script_name}: Shebang presente, encoding ausente")
                return True
            elif has_encoding:
                self.log_warning(f"{script_name}: Encoding presente, shebang ausente")
                return True
            else:
                self.log_warning(f"{script_name}: Shebang e encoding ausentes")
                return True
        except Exception as e:
            self.log_failure(f"{script_name}: Erro ao verificar headers", str(e))
            return False

    def test_docstring(self, script_name: str) -> bool:
        """Verifica se há docstring no módulo"""
        script_path = self.scripts_dir / script_name
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)
            docstring = ast.get_docstring(tree)

            if docstring and len(docstring) > 10:
                self.log_success(f"{script_name}: Docstring presente", f"{len(docstring)} chars")
                return True
            else:
                self.log_warning(f"{script_name}: Docstring ausente ou curta")
                return True
        except Exception as e:
            self.log_failure(f"{script_name}: Erro ao verificar docstring", str(e))
            return False

    def test_no_syntax_errors_exec(self, script_name: str) -> bool:
        """Testa se o script pode ser compilado (não executa)"""
        script_path = self.scripts_dir / script_name
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                source = f.read()

            compile(source, script_path, 'exec')
            self.log_success(f"{script_name}: Compilação Python bem-sucedida")
            return True
        except Exception as e:
            self.log_failure(f"{script_name}: Erro de compilação", str(e))
            return False

    def test_dependencies_available(self, script_name: str) -> bool:
        """Verifica se dependências comuns estão disponíveis"""
        script_path = self.scripts_dir / script_name
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                source = f.read()

            # Extrai importações
            tree = ast.parse(source)
            imports = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])

            # Remove módulos built-in comuns
            builtin_modules = {'os', 'sys', 're', 'json', 'pathlib', 'datetime',
                             'typing', 'collections', 'itertools', 'functools'}
            external_imports = imports - builtin_modules

            if not external_imports:
                self.log_success(f"{script_name}: Apenas dependências built-in")
                return True

            # Verifica se importações externas estão disponíveis
            missing = []
            for module in external_imports:
                try:
                    __import__(module)
                except ImportError:
                    missing.append(module)

            if not missing:
                self.log_success(f"{script_name}: Todas dependências disponíveis",
                               f"{len(external_imports)} externas")
                return True
            else:
                self.log_warning(f"{script_name}: Dependências faltando",
                               f"Ausentes: {', '.join(missing)}")
                return True
        except Exception as e:
            self.log_failure(f"{script_name}: Erro ao verificar dependências", str(e))
            return False

    def test_data_files_access(self, script_name: str) -> bool:
        """Verifica se script acessa arquivos de dados corretamente"""
        script_path = self.scripts_dir / script_name
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                source = f.read()

            # Procura por referências a arquivos de dados
            data_patterns = [
                'direitos.json',
                'ipva_pcd_estados.json',
                'matching_engine.json',
                'index.html',
                'styles.css',
                'app.js',
            ]

            referenced_files = []
            for pattern in data_patterns:
                if pattern in source:
                    referenced_files.append(pattern)

            if referenced_files:
                # Verifica se arquivos existem
                missing = []
                data_dir = self.root / 'data'

                for filename in referenced_files:
                    if filename.endswith('.json'):
                        if not (data_dir / filename).exists():
                            missing.append(filename)
                    elif filename == 'index.html':
                        if not (self.root / filename).exists():
                            missing.append(filename)
                    elif filename.endswith('.css'):
                        if not (self.root / 'css' / filename).exists():
                            missing.append(filename)
                    elif filename.endswith('.js'):
                        if not (self.root / 'js' / filename).exists():
                            missing.append(filename)

                if not missing:
                    self.log_success(f"{script_name}: Arquivos de dados acessíveis",
                                   f"{len(referenced_files)} referenciados")
                    return True
                else:
                    self.log_failure(f"{script_name}: Arquivos de dados ausentes",
                                   f"Faltam: {', '.join(missing)}")
                    return False
            else:
                self.log_success(f"{script_name}: Não requer arquivos de dados externos")
                return True
        except Exception as e:
            self.log_failure(f"{script_name}: Erro ao verificar acesso a dados", str(e))
            return False

    def test_script(self, script_name: str):
        """Executa todos os testes para um script"""
        self.print_section(f"TESTANDO: {script_name}")

        if not self.test_file_exists(script_name):
            return  # Se arquivo não existe, skip outros testes

        self.test_python_syntax(script_name)
        self.test_shebang_and_encoding(script_name)
        self.test_docstring(script_name)
        self.test_imports(script_name)
        self.test_main_function(script_name)
        self.test_no_syntax_errors_exec(script_name)
        self.test_dependencies_available(script_name)
        self.test_data_files_access(script_name)

    def run_all(self):
        """Executa testes para todos os scripts"""
        # Fix Windows encoding
        import sys
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

        print(f"{BOLD}{BLUE}")
        print("=" * 71)
        print("         TESTE DE SCRIPTS DE ANALISE - NossoDireito v1.9.0       ")
        print("                                                                   ")
        print("    Validacao de Sintaxe, Estrutura, Dependencias e Dados        ")
        print("=" * 71)
        print(f"{RESET}\n")

        for script in self.analysis_scripts:
            self.test_script(script)

        self.print_summary()

    def print_summary(self):
        """Imprime sumário final"""
        total_tests = self.passed + self.failed + self.warnings

        print(f"\n{CYAN}{'='*70}{RESET}")
        print(f"{CYAN}{BOLD}{'SUMÁRIO FINAL':^70}{RESET}")
        print(f"{CYAN}{'='*70}{RESET}\n")

        print(f"{GREEN}✓ PASS:    {self.passed:3d}{RESET}")
        print(f"{RED}✗ FAIL:    {self.failed:3d}{RESET}")
        print(f"{YELLOW}⚠ WARN:    {self.warnings:3d}{RESET}")
        print(f"{BLUE}══════════════{RESET}")
        print(f"{BOLD}TOTAL:     {total_tests:3d}{RESET}\n")

        success_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0

        if self.failed == 0 and self.warnings == 0:
            print(f"{GREEN}{BOLD}🎉 TODOS OS SCRIPTS VALIDADOS! 100% SUCCESS{RESET}\n")
            print(f"{GREEN}✅ SCRIPTS PRONTOS PARA USO{RESET}\n")
            return 0
        elif self.failed == 0:
            print(f"{YELLOW}{BOLD}⚠️  SCRIPTS VALIDADOS COM {self.warnings} WARNINGS ({success_rate:.1f}% success){RESET}\n")
            print(f"{YELLOW}⚡ SCRIPTS FUNCIONAIS (revisar warnings){RESET}\n")
            return 0
        else:
            print(f"{RED}{BOLD}❌ {self.failed} TESTES FALHARAM ({success_rate:.1f}% success){RESET}\n")
            print(f"{RED}🛑 CORRIGIR FALHAS ANTES DE USAR SCRIPTS{RESET}\n")
            return 1


def main():
    tester = ScriptTester()
    exit_code = tester.run_all()

    if exit_code == 0:
        print(f"{CYAN}{'─'*70}{RESET}")
        print(f"{CYAN}PRÓXIMOS PASSOS:{RESET}")
        print(f"{GREEN}1. Executar scripts de análise individualmente{RESET}")
        print(f"{GREEN}2. Revisar outputs e corrigir warnings{RESET}")
        print(f"{GREEN}3. Integrar scripts no pipeline CI/CD{RESET}")
        print(f"{CYAN}{'─'*70}{RESET}\n")

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
