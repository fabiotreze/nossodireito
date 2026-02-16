#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de Servidor e Browser Básico - NossoDireito v1.9.0

Valida:
- Servidor HTTP local funcionando
- HTML sendo servido corretamente
- JavaScript carregando
- CSS carregando
- Recursos estáticos acessíveis
- Service Worker disponível
- Manifest.json válido
"""

import http.server
import json
import socketserver
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


class LocalServerTester:
    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.port = 8080
        self.server = None
        self.server_thread = None
        self.base_url = f"http://localhost:{self.port}"
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def log_success(self, test_name: str, message: str = ""):
        self.passed += 1
        print(f"{GREEN}✓ PASS{RESET} {BOLD}{test_name}{RESET}")
        if message:
            print(f"      {message}")

    def log_failure(self, test_name: str, message: str = ""):
        self.failed += 1
        print(f"{RED}✗ FAIL{RESET} {BOLD}{test_name}{RESET}")
        if message:
            print(f"      {RED}{message}{RESET}")

    def log_warning(self, test_name: str, message: str = ""):
        self.warnings += 1
        print(f"{YELLOW}⚠ WARN{RESET} {BOLD}{test_name}{RESET}")
        if message:
            print(f"      {YELLOW}{message}{RESET}")

    def start_server(self):
        """Inicia servidor HTTP local"""
        try:
            import os
            os.chdir(self.root)

            handler = http.server.SimpleHTTPRequestHandler
            self.server = socketserver.TCPServer(("", self.port), handler)

            def serve():
                self.server.serve_forever()

            self.server_thread = threading.Thread(target=serve, daemon=True)
            self.server_thread.start()
            time.sleep(2)  # Aguarda servidor iniciar

            self.log_success("Servidor HTTP iniciado", f"Rodando em {self.base_url}")
            return True
        except Exception as e:
            self.log_failure("Servidor HTTP não iniciou", str(e))
            return False

    def stop_server(self):
        """Para servidor HTTP"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()

    def test_index_html(self):
        """Testa se index.html é servido"""
        try:
            response = urllib.request.urlopen(f"{self.base_url}/index.html", timeout=5)
            content = response.read().decode('utf-8')

            if response.status == 200:
                if '<!DOCTYPE html>' in content:
                    self.log_success("index.html carregado", f"Status 200, {len(content)} bytes")
                    return content
                else:
                    self.log_failure("index.html sem DOCTYPE")
                    return None
            else:
                self.log_failure(f"index.html retornou status {response.status}")
                return None
        except Exception as e:
            self.log_failure("index.html não acessível", str(e))
            return None

    def test_drawer_structure(self, html_content: str):
        """Testa estrutura do drawer no HTML"""
        if not html_content:
            return

        required_ids = [
            'a11yPanelTrigger',
            'a11yDrawer',
            'a11yOverlay',
            'a11yDrawerClose'
        ]

        missing = []
        for elem_id in required_ids:
            if f'id="{elem_id}"' not in html_content:
                missing.append(elem_id)

        if not missing:
            self.log_success("Estrutura Drawer presente", f"{len(required_ids)} elementos encontrados")
        else:
            self.log_failure("Estrutura Drawer incompleta", f"Faltam: {', '.join(missing)}")

    def test_javascript_loaded(self, html_content: str):
        """Testa se app.js está referenciado"""
        if not html_content:
            return

        if 'src="js/app.js"' in html_content or 'src="./js/app.js"' in html_content:
            self.log_success("JavaScript referenciado", "app.js linkado")

            # Tenta carregar o JS
            try:
                response = urllib.request.urlopen(f"{self.base_url}/js/app.js", timeout=5)
                if response.status == 200:
                    js_content = response.read().decode('utf-8')
                    if 'setupAccessibilityPanel' in js_content:
                        self.log_success("app.js carregado", "setupAccessibilityPanel presente")
                    else:
                        self.log_warning("app.js carregado", "setupAccessibilityPanel não encontrado")
                else:
                    self.log_failure(f"app.js status {response.status}")
            except Exception as e:
                self.log_failure("app.js não acessível", str(e))
        else:
            self.log_failure("JavaScript não referenciado")

    def test_css_loaded(self, html_content: str):
        """Testa se styles.css está referenciado"""
        if not html_content:
            return

        if 'href="css/styles.css"' in html_content or 'href="./css/styles.css"' in html_content:
            self.log_success("CSS referenciado", "styles.css linkado")

            # Tenta carregar o CSS
            try:
                response = urllib.request.urlopen(f"{self.base_url}/css/styles.css", timeout=5)
                if response.status == 200:
                    css_content = response.read().decode('utf-8')
                    if '.a11y-drawer' in css_content:
                        self.log_success("styles.css carregado", ".a11y-drawer presente")
                    else:
                        self.log_warning("styles.css carregado", ".a11y-drawer não encontrado")
                else:
                    self.log_failure(f"styles.css status {response.status}")
            except Exception as e:
                self.log_failure("styles.css não acessível", str(e))
        else:
            self.log_failure("CSS não referenciado")

    def test_service_worker(self):
        """Testa se Service Worker está disponível"""
        try:
            response = urllib.request.urlopen(f"{self.base_url}/sw.js", timeout=5)
            if response.status == 200:
                sw_content = response.read().decode('utf-8')
                if 'install' in sw_content and 'fetch' in sw_content:
                    self.log_success("Service Worker disponível", "sw.js com eventos install e fetch")
                else:
                    self.log_warning("Service Worker incompleto", "Faltam eventos essenciais")
            else:
                self.log_failure(f"Service Worker status {response.status}")
        except Exception as e:
            self.log_warning("Service Worker não acessível", str(e))

    def test_manifest(self):
        """Testa manifest.json"""
        try:
            response = urllib.request.urlopen(f"{self.base_url}/manifest.json", timeout=5)
            if response.status == 200:
                manifest = json.loads(response.read().decode('utf-8'))

                required_keys = ['name', 'short_name', 'start_url', 'display', 'icons']
                missing = [k for k in required_keys if k not in manifest]

                if not missing:
                    self.log_success("manifest.json válido", f"{len(required_keys)} propriedades obrigatórias")
                else:
                    self.log_failure("manifest.json incompleto", f"Faltam: {', '.join(missing)}")
            else:
                self.log_failure(f"manifest.json status {response.status}")
        except json.JSONDecodeError:
            self.log_failure("manifest.json inválido", "JSON malformado")
        except Exception as e:
            self.log_failure("manifest.json não acessível", str(e))

    def test_data_files(self):
        """Testa arquivos de dados JSON"""
        data_files = [
            'data/direitos.json',
            'data/ipva_pcd_estados.json',
            'data/matching_engine.json'
        ]

        for file_path in data_files:
            try:
                response = urllib.request.urlopen(f"{self.base_url}/{file_path}", timeout=5)
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    self.log_success(f"{file_path} acessível", "JSON válido")
                else:
                    self.log_failure(f"{file_path} status {response.status}")
            except json.JSONDecodeError:
                self.log_failure(f"{file_path} inválido", "JSON malformado")
            except Exception as e:
                self.log_warning(f"{file_path} não acessível", str(e))

    def test_vlibras_widget(self, html_content: str):
        """Testa se VLibras está presente"""
        if not html_content:
            return

        if '<div vw class="enabled">' in html_content:
            self.log_success("VLibras widget presente", "Obrigatório LBI Art. 63")
        else:
            self.log_failure("VLibras widget ausente", "VIOLAÇÃO LBI")

    def run_all(self):
        """Executa todos os testes"""
        # Fix Windows encoding
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

        print(f"{BOLD}{CYAN}")
        print("=" * 71)
        print("     TESTE DE SERVIDOR E BROWSER - NossoDireito v1.9.0")
        print("                                                                   ")
        print("       Validacao de Servidor HTTP e Recursos Web                 ")
        print("=" * 71)
        print(f"{RESET}\n")

        # Inicia servidor
        if not self.start_server():
            print(f"\n{RED}Erro ao iniciar servidor. Encerrando testes.{RESET}\n")
            return 1

        try:
            # Executa testes
            html_content = self.test_index_html()
            self.test_drawer_structure(html_content)
            self.test_javascript_loaded(html_content)
            self.test_css_loaded(html_content)
            self.test_service_worker()
            self.test_manifest()
            self.test_data_files()
            self.test_vlibras_widget(html_content)

            # Sumário
            total = self.passed + self.failed + self.warnings

            print(f"\n{CYAN}{'='*70}{RESET}")
            print(f"{CYAN}{BOLD}{'SUMÁRIO FINAL':^70}{RESET}")
            print(f"{CYAN}{'='*70}{RESET}\n")

            print(f"{GREEN}✓ PASS:    {self.passed:3d}{RESET}")
            print(f"{RED}✗ FAIL:    {self.failed:3d}{RESET}")
            print(f"{YELLOW}⚠ WARN:    {self.warnings:3d}{RESET}")
            print(f"{'='*14}")
            print(f"{BOLD}TOTAL:     {total:3d}{RESET}\n")

            if self.failed == 0 and self.warnings == 0:
                print(f"{GREEN}{BOLD}🎉 SERVIDOR E RECURSOS: 100% SUCCESS{RESET}\n")
                print(f"{CYAN}Servidor rodando em: {self.base_url}{RESET}")
                print(f"{CYAN}Acesse no navegador para testar interações{RESET}\n")
                return 0
            elif self.failed == 0:
                print(f"{YELLOW}{BOLD}⚠️  SERVIDOR OK COM {self.warnings} WARNINGS{RESET}\n")
                return 0
            else:
                print(f"{RED}{BOLD}❌ {self.failed} TESTES FALHARAM{RESET}\n")
                return 1

        finally:
            self.stop_server()


def print_browser_testing_guide():
    """Imprime guia para testes completos de browser"""
    print(f"\n{CYAN}{'─'*70}{RESET}")
    print(f"{CYAN}TESTES COMPLETOS DE BROWSER (requer Selenium ou Playwright):{RESET}")
    print(f"{YELLOW}")
    print("Para testes E2E com emulação completa de browser, instale:")
    print("  pip install selenium webdriver-manager")
    print("ou")
    print("  pip install playwright")
    print("  playwright install")
    print(f"{RESET}")
    print("Com Selenium, você pode testar:")
    print("  - Clique no botão drawer")
    print("  - Animações de abertura/fechamento")
    print("  - Navegação por teclado (Tab, Esc)")
    print("  - Alto contraste visual")
    print("  - Text-to-Speech (TTS)")
    print("  - VLibras ativação")
    print(f"{CYAN}{'─'*70}{RESET}\n")


def main():
    tester = LocalServerTester()
    exit_code = tester.run_all()

    if exit_code == 0:
        print_browser_testing_guide()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
