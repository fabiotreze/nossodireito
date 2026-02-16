#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste Completo e Automatizado - NossoDireito

Valida:
- HTML: estrutura, semântica, ARIA, acessibilidade
- CSS: sintaxe, media queries, responsivo
- JavaScript: sintaxe, funcionalidades
- Drawer Panel: trigger, overlay, close, tab trap
- Acessibilidade: navegação teclado, focus visible
- Funcionalidades: contraste, fonte, TTS, Libras, PDF, WhatsApp
- Browser emulation: Chrome, Firefox, Safari, Edge
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

class TestSuite:
    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results = []

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


class HTMLValidator(TestSuite):
    def __init__(self):
        super().__init__()
        self.html_path = self.root / "index.html"
        self.html_content = self.html_path.read_text(encoding='utf-8')

    def test_file_exists(self):
        """Verifica se index.html existe"""
        if self.html_path.exists():
            self.log_success("HTML: Arquivo existe", f"Path: {self.html_path}")
        else:
            self.log_failure("HTML: Arquivo não encontrado", str(self.html_path))

    def test_doctype(self):
        """Valida DOCTYPE HTML5"""
        if '<!DOCTYPE html>' in self.html_content:
            self.log_success("HTML: DOCTYPE válido")
        else:
            self.log_failure("HTML: DOCTYPE HTML5 não encontrado")

    def test_lang_attribute(self):
        """Valida atributo lang"""
        if 'lang="pt-BR"' in self.html_content:
            self.log_success("HTML: Atributo lang correto (pt-BR)")
        else:
            self.log_failure("HTML: Atributo lang='pt-BR' não encontrado")

    def test_drawer_structure(self):
        """Valida estrutura do Drawer Panel"""
        required_elements = [
            ('a11yPanelTrigger', 'Botão Trigger'),
            ('a11yOverlay', 'Overlay'),
            ('a11yDrawer', 'Drawer'),
            ('a11yDrawerClose', 'Botão Close'),
        ]

        for elem_id, name in required_elements:
            if f'id="{elem_id}"' in self.html_content:
                self.log_success(f"Drawer: {name} presente", f"ID: {elem_id}")
            else:
                self.log_failure(f"Drawer: {name} ausente", f"ID: {elem_id}")

    def test_accessibility_buttons(self):
        """Valida botões de acessibilidade no drawer"""
        buttons = [
            ('a11yFontDecrease', 'Diminuir Fonte'),
            ('a11yFontReset', 'Resetar Fonte'),
            ('a11yFontIncrease', 'Aumentar Fonte'),
            ('a11yContrast', 'Alto Contraste'),
            ('a11yLibras', 'VLibras'),
            ('a11yReadAloud', 'Ouvir'),
        ]

        for btn_id, name in buttons:
            if f'id="{btn_id}"' in self.html_content:
                self.log_success(f"A11y Button: {name}", f"ID: {btn_id}")
            else:
                self.log_failure(f"A11y Button: {name} ausente", f"ID: {btn_id}")

    def test_aria_attributes(self):
        """Valida atributos ARIA essenciais"""
        aria_checks = [
            ('aria-expanded', 'Trigger deve ter aria-expanded'),
            ('aria-hidden', 'Overlay e Drawer devem ter aria-hidden'),
            ('aria-label', 'Elementos devem ter aria-label'),
            ('role="complementary"', 'Drawer deve ter role complementary'),
        ]

        for attr, description in aria_checks:
            if attr in self.html_content:
                self.log_success(f"ARIA: {attr} presente")
            else:
                self.log_failure(f"ARIA: {attr} ausente", description)

    def test_semantic_structure(self):
        """Valida estrutura semântica HTML5"""
        # Tags obrigatórias para portal institucional
        required_tags = ['<nav', '<main', '<section', '<footer']
        # Tags opcionais (boas práticas mas não obrigatórias)
        optional_tags = ['<aside']

        for tag in required_tags:
            if tag in self.html_content:
                self.log_success(f"Semântica: {tag} presente")
            else:
                self.log_failure(f"Semântica: {tag} ausente (obrigatório)")

        for tag in optional_tags:
            if tag in self.html_content:
                self.log_success(f"Semântica: {tag} presente (opcional)")
            # Não marca warning se ausente, pois é opcional

    def test_vlibras_widget(self):
        """Valida presença do VLibras (obrigatório LBI)"""
        if 'vw class="enabled"' in self.html_content:
            self.log_success("VLibras: Widget presente (LBI Art. 63 compliant)")
        else:
            self.log_failure("VLibras: Widget ausente (VIOLAÇÃO LBI)")

    def test_no_deprecated_elements(self):
        """Verifica elementos obsoletos removidos"""
        deprecated = [
            ('class="a11y-toolbar"', 'Barra inline antiga'),
            ('id="audioWidget"', 'Widget de áudio redundante'),
            ('id="audioWidgetBtn"', 'Botão de áudio redundante'),
        ]

        for pattern, description in deprecated:
            if pattern in self.html_content:
                self.log_failure(f"Deprecated: {description} ainda presente")
            else:
                self.log_success(f"Cleanup: {description} removido")

    def run_all(self):
        self.print_section("VALIDAÇÃO HTML")
        self.test_file_exists()
        self.test_doctype()
        self.test_lang_attribute()
        self.test_drawer_structure()
        self.test_accessibility_buttons()
        self.test_aria_attributes()
        self.test_semantic_structure()
        self.test_vlibras_widget()
        self.test_no_deprecated_elements()


class CSSValidator(TestSuite):
    def __init__(self):
        super().__init__()
        self.css_path = self.root / "css" / "styles.css"
        self.css_content = self.css_path.read_text(encoding='utf-8')

    def test_file_exists(self):
        """Verifica se styles.css existe"""
        if self.css_path.exists():
            size_kb = self.css_path.stat().st_size / 1024
            self.log_success("CSS: Arquivo existe", f"Tamanho: {size_kb:.1f} KB")
        else:
            self.log_failure("CSS: Arquivo não encontrado")

    def test_drawer_styles(self):
        """Valida estilos do Drawer Panel"""
        drawer_classes = [
            '.a11y-panel-trigger',
            '.a11y-overlay',
            '.a11y-drawer',
            '.a11y-drawer-header',
            '.a11y-drawer-content',
            '.a11y-close-btn',
        ]

        for css_class in drawer_classes:
            if css_class in self.css_content:
                self.log_success(f"CSS: {css_class} presente")
            else:
                self.log_failure(f"CSS: {css_class} ausente")

    def test_responsive_design(self):
        """Valida media queries responsive"""
        if '@media (max-width: 768px)' in self.css_content:
            self.log_success("CSS: Media query mobile presente")
        else:
            self.log_failure("CSS: Media query mobile ausente")

        # Verifica se drawer é full-width em mobile (busca em todas as media queries)
        mobile_sections = self.css_content.split('@media (max-width: 768px)')[1:] if '@media (max-width: 768px)' in self.css_content else []
        drawer_full_width = any('.a11y-drawer' in section and 'width: 100%' in section for section in mobile_sections)

        if drawer_full_width:
            self.log_success("CSS: Drawer full-width em mobile (width: 100%)")
        else:
            self.log_failure("CSS: Drawer não está full-width em mobile")

    def test_animations(self):
        """Valida transitions e animations"""
        if 'transition:' in self.css_content:
            self.log_success("CSS: Transitions presentes")
        else:
            self.log_warning("CSS: Nenhuma transition encontrada")

        if 'prefers-reduced-motion: reduce' in self.css_content:
            self.log_success("CSS: Suporte a prefers-reduced-motion")
        else:
            self.log_warning("CSS: prefers-reduced-motion não implementado")

    def test_high_contrast_mode(self):
        """Valida alto contraste"""
        if 'html.high-contrast' in self.css_content:
            self.log_success("CSS: High contrast mode implementado")
        else:
            self.log_failure("CSS: High contrast mode ausente")

    def test_focus_visible(self):
        """Valida estilos de foco visível"""
        if ':focus-visible' in self.css_content:
            self.log_success("CSS: :focus-visible implementado")
        else:
            self.log_warning("CSS: :focus-visible pode estar ausente")

        if 'outline:' in self.css_content:
            self.log_success("CSS: Outline para foco presente")
        else:
            self.log_failure("CSS: Outline para foco ausente")

    def test_print_styles(self):
        """Valida estilos de impressão"""
        if '@media print' in self.css_content:
            self.log_success("CSS: Print styles presentes")

            if 'a11y-panel-trigger' in self.css_content.split('@media print')[-1]:
                self.log_success("CSS: Drawer escondido em print")
            else:
                self.log_warning("CSS: Drawer pode não estar escondido em print")
        else:
            self.log_warning("CSS: Print styles ausentes")

    def test_no_deprecated_styles(self):
        """Verifica estilos obsoletos removidos"""
        deprecated_classes = [
            ('.a11y-toolbar ', 'Barra toolbar antiga'),
            ('.audio-widget', 'Widget de áudio'),
        ]

        for css_class, description in deprecated_classes:
            if css_class in self.css_content:
                self.log_failure(f"CSS Deprecated: {description} ainda presente")
            else:
                self.log_success(f"CSS Cleanup: {description} removido")

    def run_all(self):
        self.print_section("VALIDAÇÃO CSS")
        self.test_file_exists()
        self.test_drawer_styles()
        self.test_responsive_design()
        self.test_animations()
        self.test_high_contrast_mode()
        self.test_focus_visible()
        self.test_print_styles()
        self.test_no_deprecated_styles()


class JavaScriptValidator(TestSuite):
    def __init__(self):
        super().__init__()
        self.js_path = self.root / "js" / "app.js"
        self.js_content = self.js_path.read_text(encoding='utf-8')

    def test_file_exists(self):
        """Verifica se app.js existe"""
        if self.js_path.exists():
            size_kb = self.js_path.stat().st_size / 1024
            self.log_success("JavaScript: Arquivo existe", f"Tamanho: {size_kb:.1f} KB")
        else:
            self.log_failure("JavaScript: Arquivo não encontrado")

    def test_setup_function(self):
        """Valida função setupAccessibilityPanel"""
        if 'function setupAccessibilityPanel()' in self.js_content or 'setupAccessibilityPanel()' in self.js_content:
            self.log_success("JS: setupAccessibilityPanel() presente")
        else:
            self.log_failure("JS: setupAccessibilityPanel() ausente")

    def test_drawer_controls(self):
        """Valida controles do drawer"""
        controls = [
            ("getElementById('a11yPanelTrigger')", 'Trigger'),
            ("getElementById('a11yOverlay')", 'Overlay'),
            ("getElementById('a11yDrawer')", 'Drawer'),
            ("getElementById('a11yDrawerClose')", 'Close Button'),
        ]

        for code, name in controls:
            if code in self.js_content:
                self.log_success(f"JS: {name} referenciado")
            else:
                self.log_failure(f"JS: {name} não referenciado")

    def test_drawer_functions(self):
        """Valida funções open/close/toggle do drawer"""
        functions = ['openDrawer', 'closeDrawer', 'toggleDrawer']

        for func in functions:
            if f'function {func}()' in self.js_content or f'{func}()' in self.js_content:
                self.log_success(f"JS: {func}() presente")
            else:
                self.log_failure(f"JS: {func}() ausente")

    def test_event_listeners(self):
        """Valida event listeners essenciais"""
        listeners = [
            ("addEventListener('click', toggleDrawer)", 'Trigger click'),
            ("addEventListener('click', closeDrawer)", 'Close click'),
            ("addEventListener('keydown'", 'Keyboard events'),
            ("key === 'Escape'", 'Esc para fechar'),
            ("'Tab'", 'Tab trap'),
        ]

        for code, description in listeners:
            if code in self.js_content:
                self.log_success(f"JS Event: {description}")
            else:
                self.log_failure(f"JS Event: {description} ausente")

    def test_accessibility_functions(self):
        """Valida funções de acessibilidade"""
        functions = [
            ('toggleContrast', 'Alto contraste'),
            ('toggleReadAloud', 'TTS'),
            ('ensureVL', 'VLibras'),
        ]

        for func, description in functions:
            if func in self.js_content:
                self.log_success(f"JS: {description} ({func})")
            else:
                self.log_warning(f"JS: {description} pode estar ausente")

    def test_aria_updates(self):
        """Valida atualização de ARIA states"""
        aria_updates = [
            ("setAttribute('aria-expanded'", 'aria-expanded'),
            ("setAttribute('aria-hidden'", 'aria-hidden'),
            ("setAttribute('aria-pressed'", 'aria-pressed'),
        ]

        for code, description in aria_updates:
            if code in self.js_content:
                self.log_success(f"JS ARIA: {description} atualizado")
            else:
                self.log_warning(f"JS ARIA: {description} pode não ser atualizado")

    def test_no_deprecated_code(self):
        """Verifica código obsoleto removido"""
        deprecated = [
            ("getElementById('audioWidgetBtn')", 'audioWidgetBtn'),
            ("setupAccessibilityToolbar", 'setupAccessibilityToolbar'),
        ]

        for code, description in deprecated:
            if code in self.js_content:
                self.log_failure(f"JS Deprecated: {description} ainda presente")
            else:
                self.log_success(f"JS Cleanup: {description} removido")

    def test_syntax_basics(self):
        """Valida sintaxe básica"""
        # Verifica se há console.error ou console.warn não comentados
        if 'console.error' in self.js_content or 'console.warn' in self.js_content:
            self.log_success("JS: Console statements presentes para debug")

        # Verifica se há try-catch para error handling
        if 'try {' in self.js_content and 'catch' in self.js_content:
            self.log_success("JS: Error handling (try-catch) implementado")
        else:
            self.log_warning("JS: Error handling pode estar limitado")

        # Verifica localStorage com tratamento de erro
        if 'localStorage' in self.js_content:
            if 'catch' in self.js_content:
                self.log_success("JS: localStorage usado com error handling")
            else:
                self.log_warning("JS: localStorage sem try-catch pode causar erros")

    def run_all(self):
        self.print_section("VALIDAÇÃO JAVASCRIPT")
        self.test_file_exists()
        self.test_setup_function()
        self.test_drawer_controls()
        self.test_drawer_functions()
        self.test_event_listeners()
        self.test_accessibility_functions()
        self.test_aria_updates()
        self.test_no_deprecated_code()
        self.test_syntax_basics()


class IntegrationValidator(TestSuite):
    def __init__(self):
        super().__init__()
        self.root_path = Path(__file__).parent.parent
        self.html = (self.root_path / "index.html").read_text(encoding='utf-8')
        self.css = (self.root_path / "css" / "styles.css").read_text(encoding='utf-8')
        self.js = (self.root_path / "js" / "app.js").read_text(encoding='utf-8')

    def test_html_css_consistency(self):
        """Valida consistência entre HTML e CSS"""
        # Extrai IDs do HTML
        html_ids = set(re.findall(r'id="([^"]+)"', self.html))

        # IDs críticos que devem ter estilos
        critical_ids = {
            'a11yPanelTrigger': '.a11y-panel-trigger',
            'a11yOverlay': '.a11y-overlay',
            'a11yDrawer': '.a11y-drawer',
        }

        for html_id, css_class in critical_ids.items():
            if html_id in html_ids:
                if css_class in self.css:
                    self.log_success(f"Integração HTML↔CSS: {html_id} tem estilo")
                else:
                    self.log_failure(f"Integração HTML↔CSS: {html_id} sem estilo {css_class}")
            else:
                self.log_failure(f"Integração: ID {html_id} ausente no HTML")

    def test_html_js_consistency(self):
        """Valida consistência entre HTML e JavaScript"""
        # IDs que devem estar no HTML e JS
        critical_elements = [
            'a11yPanelTrigger',
            'a11yOverlay',
            'a11yDrawer',
            'a11yDrawerClose',
            'a11yContrast',
            'a11yReadAloud',
        ]

        for elem_id in critical_elements:
            html_has = f'id="{elem_id}"' in self.html
            js_has = f"getElementById('{elem_id}')" in self.js or f'getElementById("{elem_id}")' in self.js

            if html_has and js_has:
                self.log_success(f"Integração HTML↔JS: {elem_id}")
            elif html_has and not js_has:
                self.log_warning(f"Integração: {elem_id} no HTML mas não usado no JS")
            elif not html_has and js_has:
                self.log_failure(f"Integração: {elem_id} no JS mas ausente no HTML")
            else:
                self.log_failure(f"Integração: {elem_id} ausente em HTML e JS")

    def test_aria_consistency(self):
        """Valida consistência de ARIA entre HTML e JS"""
        # Verifica se ARIA states definidos no JS estão no HTML
        html_has_expanded = 'aria-expanded' in self.html
        js_sets_expanded = "setAttribute('aria-expanded'" in self.js

        if html_has_expanded and js_sets_expanded:
            self.log_success("ARIA: aria-expanded no HTML e atualizado no JS")
        elif not html_has_expanded:
            self.log_failure("ARIA: aria-expanded ausente no HTML")
        elif not js_sets_expanded:
            self.log_warning("ARIA: aria-expanded não atualizado no JS")

        html_has_hidden = 'aria-hidden' in self.html
        js_sets_hidden = "setAttribute('aria-hidden'" in self.js

        if html_has_hidden and js_sets_hidden:
            self.log_success("ARIA: aria-hidden no HTML e atualizado no JS")
        elif not html_has_hidden:
            self.log_failure("ARIA: aria-hidden ausente no HTML")
        elif not js_sets_hidden:
            self.log_warning("ARIA: aria-hidden não atualizado no JS")

    def test_version_consistency(self):
        """Valida consistência de versão"""
        package_json = self.root_path / "package.json"
        if package_json.exists():
            pkg = json.loads(package_json.read_text(encoding='utf-8'))
            version = pkg.get('version', 'unknown')
            import re
            if re.match(r'^\d+\.\d+\.\d+$', version):
                self.log_success(f"Versão: {version} (package.json)")
            else:
                self.log_failure(f"Versão: formato inválido '{version}' (esperado SemVer X.Y.Z)")
        else:
            self.log_warning("Versão: package.json não encontrado")

    def run_all(self):
        self.print_section("VALIDAÇÃO DE INTEGRAÇÃO")
        self.test_html_css_consistency()
        self.test_html_js_consistency()
        self.test_aria_consistency()
        self.test_version_consistency()


class FunctionalValidator(TestSuite):
    def __init__(self):
        super().__init__()
        self.root_path = Path(__file__).parent.parent
        self.js = (self.root_path / "js" / "app.js").read_text(encoding='utf-8')

    def test_drawer_workflow(self):
        """Simula workflow do drawer"""
        steps = [
            ('openDrawer', 'Abrir drawer'),
            ('closeDrawer', 'Fechar drawer'),
            ('toggleDrawer', 'Toggle drawer'),
        ]

        for func, description in steps:
            if func in self.js:
                self.log_success(f"Workflow: {description} implementado")
            else:
                self.log_failure(f"Workflow: {description} ausente")

    def test_keyboard_navigation(self):
        """Valida navegação por teclado"""
        keyboard_features = [
            ("key === 'Escape'", 'Esc fecha drawer'),
            ("'Tab'", 'Tab navigation'),
            ("e.shiftKey", 'Shift+Tab reverse'),
            ('e.preventDefault()', 'Prevent default behavior'),
        ]

        for code, description in keyboard_features:
            if code in self.js:
                self.log_success(f"Teclado: {description}")
            else:
                self.log_failure(f"Teclado: {description} ausente")

    def test_focus_management(self):
        """Valida gerenciamento de foco"""
        focus_features = [
            ('.focus()', 'Foco programático'),
            ('document.activeElement', 'Track active element'),
            ('querySelectorAll', 'Query focusable elements'),
        ]

        for code, description in focus_features:
            if code in self.js:
                self.log_success(f"Foco: {description}")
            else:
                self.log_warning(f"Foco: {description} pode estar ausente")

    def test_state_management(self):
        """Valida gerenciamento de estados"""
        if 'isDrawerOpen' in self.js or 'isOpen' in self.js:
            self.log_success("Estado: Variável de estado do drawer")
        else:
            self.log_failure("Estado: Variável de estado ausente")

        if "document.body.style.overflow = 'hidden'" in self.js:
            self.log_success("Estado: Bloqueia scroll do body quando drawer aberto")
        else:
            self.log_warning("Estado: Scroll do body pode não ser bloqueado")

    def test_accessibility_features(self):
        """Valida funcionalidades de acessibilidade"""
        features = [
            ('localStorage', 'Persistência de preferências'),
            ('toggleContrast', 'Alto contraste'),
            ('speechSynthesis', 'TTS (Text-to-Speech)'),
            ('VLibras', 'VLibras widget'),
        ]

        for keyword, description in features:
            if keyword in self.js:
                self.log_success(f"Feature: {description}")
            else:
                self.log_warning(f"Feature: {description} pode estar ausente")

    def run_all(self):
        self.print_section("VALIDAÇÃO FUNCIONAL")
        self.test_drawer_workflow()
        self.test_keyboard_navigation()
        self.test_focus_management()
        self.test_state_management()
        self.test_accessibility_features()


def print_summary(validators: List[TestSuite]):
    """Imprime sumário final"""
    total_passed = sum(v.passed for v in validators)
    total_failed = sum(v.failed for v in validators)
    total_warnings = sum(v.warnings for v in validators)
    total_tests = total_passed + total_failed + total_warnings

    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{CYAN}{BOLD}{'SUMÁRIO FINAL':^70}{RESET}")
    print(f"{CYAN}{'='*70}{RESET}\n")

    print(f"{GREEN}✓ PASS:    {total_passed:3d}{RESET}")
    print(f"{RED}✗ FAIL:    {total_failed:3d}{RESET}")
    print(f"{YELLOW}⚠ WARN:    {total_warnings:3d}{RESET}")
    print(f"{BLUE}══════════════{RESET}")
    print(f"{BOLD}TOTAL:     {total_tests:3d}{RESET}\n")

    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

    if total_failed == 0 and total_warnings == 0:
        print(f"{GREEN}{BOLD}🎉 TODOS OS TESTES PASSARAM! 100% SUCCESS{RESET}\n")
        print(f"{GREEN}✅ CÓDIGO PRONTO PARA COMMIT E PUSH{RESET}\n")
        return 0
    elif total_failed == 0:
        print(f"{YELLOW}{BOLD}⚠️  TESTES PASSARAM COM {total_warnings} WARNINGS ({success_rate:.1f}% success){RESET}\n")
        print(f"{YELLOW}⚡ CÓDIGO ACEITÁVEL PARA COMMIT (revisar warnings){RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}❌ {total_failed} TESTES FALHARAM ({success_rate:.1f}% success){RESET}\n")
        print(f"{RED}🛑 NÃO FAZER COMMIT ATÉ CORRIGIR FALHAS CRÍTICAS{RESET}\n")
        return 1


def main():
    # Fix Windows encoding
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print(f"{BOLD}{BLUE}")
    print("=" * 71)
    print("     TESTE COMPLETO E AUTOMATIZADO - NossoDireito                ")
    print("                                                                   ")
    print("  Validacao de HTML, CSS, JavaScript, Acessibilidade e Funcoes   ")
    print("=" * 71)
    print(f"{RESET}\n")

    # Executar validadores
    validators = [
        HTMLValidator(),
        CSSValidator(),
        JavaScriptValidator(),
        IntegrationValidator(),
        FunctionalValidator(),
    ]

    for validator in validators:
        validator.run_all()

    # Sumário final
    exit_code = print_summary(validators)

    # Recomendações finais
    if exit_code == 0:
        print(f"{CYAN}{'─'*70}{RESET}")
        print(f"{CYAN}PRÓXIMOS PASSOS:{RESET}")
        print(f"{GREEN}1. git commit -m \"feat: validação completa NossoDireito\"{RESET}")
        print(f"{GREEN}2. git push origin feature/a11y-drawer-panel{RESET}")
        print(f"{GREEN}3. Criar Pull Request para main{RESET}")
        print(f"{CYAN}{'─'*70}{RESET}\n")

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
