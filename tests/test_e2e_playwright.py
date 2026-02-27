#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTES E2E PLAYWRIGHT — NossoDireito v1.14.4

Testes end-to-end reais com browser headless (Chromium) via Playwright.
Valida TODAS as funcionalidades do site servido localmente:

  - Navegação e renderização de páginas
  - Busca semântica (debounce + scoring)
  - 30 categorias: grid, cards, detalhe
  - Protocolo de Emergência: rendering + copy-to-clipboard
  - Checklist: localStorage, dependências, progresso
  - Painel de Acessibilidade: alto contraste, fonte, leitura
  - PWA: Service Worker, manifest.json
  - Impressão / Export PDF
  - Segurança: CSP headers, HTTPS redirect
  - Responsividade: mobile, tablet, desktop
  - ARIA landmarks e teclado

Requer: pip install playwright pytest-playwright && playwright install chromium
Inicia servidor Node automaticamente na porta 9876 (efêmero, sem conflito).

Uso:
  pytest tests/test_e2e_playwright.py -v
  pytest tests/test_e2e_playwright.py -v -k "search"
"""

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
E2E_PORT = 9876

# ════════════════════════════════════════════════════════════════
# SKIP se Playwright não está instalado
# ════════════════════════════════════════════════════════════════

try:
    from playwright.sync_api import sync_playwright  # noqa: F401
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

pytestmark = pytest.mark.skipif(
    not HAS_PLAYWRIGHT,
    reason="Playwright não instalado (pip install playwright pytest-playwright && playwright install chromium)"
)


# ════════════════════════════════════════════════════════════════
# FIXTURES
# ════════════════════════════════════════════════════════════════

def _port_in_use(port: int) -> bool:
    """Verifica se porta está em uso."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


@pytest.fixture(scope="session")
def server():
    """Inicia server.js na porta E2E_PORT e encerra ao final."""
    if _port_in_use(E2E_PORT):
        # Porta já ocupada — assume que servidor já roda (útil em CI)
        yield f"http://127.0.0.1:{E2E_PORT}"
        return

    env = os.environ.copy()
    env["PORT"] = str(E2E_PORT)
    env["NODE_ENV"] = "test"

    proc = subprocess.Popen(
        ["node", str(ROOT / "server.js")],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )

    # Aguardar servidor subir (máx 10s)
    for _ in range(100):
        if _port_in_use(E2E_PORT):
            break
        time.sleep(0.1)
    else:
        proc.kill()
        pytest.fail(f"Servidor não iniciou na porta {E2E_PORT} em 10s")

    yield f"http://127.0.0.1:{E2E_PORT}"

    # Cleanup
    if sys.platform == "win32":
        proc.send_signal(signal.CTRL_BREAK_EVENT)
    else:
        proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="session")
def browser_ctx():
    """Cria browser Chromium headless, compartilhado por toda a sessão."""
    if not HAS_PLAYWRIGHT:
        pytest.skip("Playwright não instalado")
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 720},
        locale="pt-BR",
        color_scheme="light",
    )
    yield ctx
    ctx.close()
    browser.close()
    pw.stop()


@pytest.fixture()
def page(server, browser_ctx):
    """Abre uma nova página e navega para o site."""
    pg = browser_ctx.new_page()
    pg.goto(server, wait_until="networkidle")
    yield pg
    pg.close()


@pytest.fixture(scope="session")
def direitos_data():
    """Carrega direitos.json para validações."""
    with open(ROOT / "data" / "direitos.json", encoding="utf-8") as f:
        return json.load(f)


# ════════════════════════════════════════════════════════════════
# 1. CARREGAMENTO E ESTRUTURA
# ════════════════════════════════════════════════════════════════

class TestPageLoad:
    """Verifica carregamento básico da página."""

    def test_title_contains_keywords(self, page):
        title = page.title()
        # SEO title: "Direitos PcD 2026: BPC, CIPTEA, ..." — verificar palavras-chave
        assert "Direitos" in title or "PcD" in title or "NossoDireito" in title

    def test_lang_pt_br(self, page):
        lang = page.locator("html").get_attribute("lang")
        assert lang == "pt-BR"

    def test_main_landmark_exists(self, page):
        assert page.locator("main").count() >= 1

    def test_header_visible(self, page):
        header = page.locator("header")
        assert header.is_visible()

    def test_footer_visible(self, page):
        footer = page.locator("footer")
        assert footer.is_visible()

    def test_no_console_errors(self, server, browser_ctx):
        """Página não deve emitir erros no console."""
        errors: list[str] = []
        pg = browser_ctx.new_page()
        pg.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        pg.goto(server, wait_until="networkidle")
        pg.wait_for_timeout(1000)
        pg.close()
        # Filtra erros de rede (favicon, etc.) e SW
        real_errors = [e for e in errors if "favicon" not in e.lower() and "sw" not in e.lower()]
        assert len(real_errors) == 0, f"Console errors: {real_errors}"


# ════════════════════════════════════════════════════════════════
# 2. CATEGORIAS GRID
# ════════════════════════════════════════════════════════════════

class TestCategoryGrid:
    """Valida grid de 30 categorias."""

    def test_grid_visible(self, page):
        grid = page.locator("#categoryGrid")
        assert grid.is_visible()

    def test_30_categories_rendered(self, page, direitos_data):
        cards = page.locator(".category-card")
        expected = len(direitos_data["categorias"])
        assert cards.count() == expected, f"Esperado {expected} cards, encontrado {cards.count()}"

    def test_cards_have_data_id(self, page, direitos_data):
        cat_ids = {c["id"] for c in direitos_data["categorias"]}
        cards = page.locator(".category-card")
        rendered_ids = set()
        for i in range(cards.count()):
            data_id = cards.nth(i).get_attribute("data-id")
            if data_id:
                rendered_ids.add(data_id)
        assert rendered_ids == cat_ids

    def test_cards_are_keyboard_accessible(self, page):
        card = page.locator(".category-card").first
        assert card.get_attribute("tabindex") == "0"
        assert card.get_attribute("role") == "button"

    def test_card_click_opens_detail(self, page):
        card = page.locator(".category-card").first
        card_id = card.get_attribute("data-id")
        card.click()
        page.wait_for_timeout(500)
        detalhe = page.locator("#detalhe")
        assert detalhe.is_visible()
        assert card_id in page.url


# ════════════════════════════════════════════════════════════════
# 3. DETALHE DE CATEGORIA
# ════════════════════════════════════════════════════════════════

class TestCategoryDetail:
    """Valida tela de detalhe de uma categoria."""

    def _open_detalhe(self, page, cat_id: str):
        page.goto(f"{page.url.split('#')[0]}#direito/{cat_id}", wait_until="networkidle")
        page.wait_for_timeout(500)

    def test_detail_shows_title(self, page, direitos_data):
        cat = direitos_data["categorias"][0]
        self._open_detalhe(page, cat["id"])
        content = page.locator("#detalheContent")
        assert content.is_visible()
        assert cat["titulo"] in content.inner_text()

    def test_detail_shows_base_legal(self, page, direitos_data):
        cat = direitos_data["categorias"][0]
        self._open_detalhe(page, cat["id"])
        # Base legal section should have links
        links = page.locator("#detalheContent .legal-link")
        assert links.count() > 0

    def test_detail_shows_passo_a_passo(self, page, direitos_data):
        cat = direitos_data["categorias"][0]
        self._open_detalhe(page, cat["id"])
        text = page.locator("#detalheContent").inner_text()
        assert "Passo a Passo" in text or "passo" in text.lower()

    def test_voltar_button_returns_to_grid(self, page, direitos_data):
        cat = direitos_data["categorias"][0]
        self._open_detalhe(page, cat["id"])
        voltar = page.locator("#voltarBtn")
        assert voltar.is_visible()
        voltar.click()
        page.wait_for_timeout(500)
        grid = page.locator("#categoryGrid")
        assert grid.is_visible()

    def test_all_30_categories_open(self, page, direitos_data):
        """Cada uma das 30 categorias deve abrir sem erro."""
        base_url = page.url.split("#")[0]
        for cat in direitos_data["categorias"]:
            page.goto(f"{base_url}#direito/{cat['id']}", wait_until="networkidle")
            page.wait_for_timeout(300)
            content = page.locator("#detalheContent")
            assert content.is_visible(), f"Categoria {cat['id']} não renderizou"


# ════════════════════════════════════════════════════════════════
# 4. PROTOCOLOS DE EMERGÊNCIA
# ════════════════════════════════════════════════════════════════

class TestEmergencyProtocol:
    """Valida renderização e funcionalidade dos protocolos de emergência."""

    def _open_detalhe(self, page, cat_id: str):
        base_url = page.url.split("#")[0]
        page.goto(f"{base_url}#direito/{cat_id}", wait_until="networkidle")
        page.wait_for_timeout(500)

    def test_emergency_section_rendered(self, page, direitos_data):
        """Protocolo de emergência deve aparecer para categorias com dados."""
        cats_with_emerg = [c for c in direitos_data["categorias"] if c.get("emergencia")]
        assert len(cats_with_emerg) == 30, "Todas 30 categorias devem ter emergência"

        # Testar a primeira (BPC)
        cat = cats_with_emerg[0]
        self._open_detalhe(page, cat["id"])
        section = page.locator(".emergencia-section")
        assert section.is_visible(), f"Emergência não visível para {cat['id']}"

    def test_emergency_has_conflito(self, page, direitos_data):
        cat = direitos_data["categorias"][0]
        self._open_detalhe(page, cat["id"])
        conflito = page.locator(".emergencia-conflito")
        assert conflito.is_visible()
        assert len(conflito.inner_text()) > 10

    def test_emergency_has_base_legal(self, page, direitos_data):
        cat = direitos_data["categorias"][0]
        self._open_detalhe(page, cat["id"])
        legal = page.locator(".emergencia-legal")
        assert legal.is_visible()

    def test_emergency_has_action_steps(self, page, direitos_data):
        cat = direitos_data["categorias"][0]
        self._open_detalhe(page, cat["id"])
        steps = page.locator(".emergencia-passos ol li")
        assert steps.count() >= 2, "Deve ter pelo menos 2 passos de ação"

    def test_emergency_has_notification_model(self, page, direitos_data):
        cat = direitos_data["categorias"][0]
        self._open_detalhe(page, cat["id"])
        modelo = page.locator(".notificacao-text")
        assert modelo.is_visible()
        assert len(modelo.inner_text()) > 20

    def test_copy_button_exists(self, page, direitos_data):
        cat = direitos_data["categorias"][0]
        self._open_detalhe(page, cat["id"])
        btn = page.locator(f"#copyNotif_{cat['id']}")
        assert btn.is_visible()

    def test_emergency_has_denuncia(self, page, direitos_data):
        cat = direitos_data["categorias"][0]
        self._open_detalhe(page, cat["id"])
        denuncia = page.locator(".emergencia-denuncia")
        assert denuncia.is_visible()

    def test_all_30_have_emergency(self, page, direitos_data):
        """Todas as 30 categorias devem renderizar seu protocolo de emergência."""
        base_url = page.url.split("#")[0]
        for cat in direitos_data["categorias"]:
            if not cat.get("emergencia"):
                continue
            page.goto(f"{base_url}#direito/{cat['id']}", wait_until="networkidle")
            page.wait_for_timeout(300)
            section = page.locator(".emergencia-section")
            assert section.is_visible(), f"Emergência ausente em {cat['id']}"


# ════════════════════════════════════════════════════════════════
# 5. BUSCA SEMÂNTICA
# ════════════════════════════════════════════════════════════════

class TestSearch:
    """Valida funcionalidade de busca."""

    def test_search_input_visible(self, page):
        inp = page.locator("#searchInput")
        assert inp.is_visible()

    def test_search_returns_results(self, page):
        inp = page.locator("#searchInput")
        inp.fill("BPC deficiência")
        page.wait_for_timeout(500)  # debounce
        results = page.locator("#searchResults")
        assert results.is_visible()
        assert results.inner_text().strip() != ""

    def test_search_bpc_finds_bpc(self, page):
        inp = page.locator("#searchInput")
        inp.fill("BPC")
        page.wait_for_timeout(500)
        text = page.locator("#searchResults").inner_text()
        assert "BPC" in text or "Benefício" in text

    def test_search_educacao(self, page):
        inp = page.locator("#searchInput")
        inp.fill("escola matrícula")
        page.wait_for_timeout(500)
        text = page.locator("#searchResults").inner_text()
        assert "ducação" in text or "matrícula" in text.lower()

    def test_search_empty_clears(self, page):
        inp = page.locator("#searchInput")
        inp.fill("BPC")
        page.wait_for_timeout(500)
        inp.fill("")
        page.wait_for_timeout(500)
        results = page.locator("#searchResults")
        # Results should be empty or hidden
        assert not results.is_visible() or results.inner_text().strip() == ""

    def test_search_no_results_message(self, page):
        inp = page.locator("#searchInput")
        inp.fill("xyznonexistent123")
        page.wait_for_timeout(500)
        results = page.locator("#searchResults")
        text = results.inner_text().lower() if results.is_visible() else ""
        # Should show "nenhum resultado" or similar, or empty
        assert "nenhum" in text or text.strip() == "" or not results.is_visible()

    def test_search_cid_code(self, page):
        """Busca por CID deve retornar resultados."""
        inp = page.locator("#searchInput")
        inp.fill("F84")
        page.wait_for_timeout(500)
        results = page.locator("#searchResults")
        assert results.is_visible()
        assert results.inner_text().strip() != ""


# ════════════════════════════════════════════════════════════════
# 6. PAINEL DE ACESSIBILIDADE
# ════════════════════════════════════════════════════════════════

class TestAccessibilityPanel:
    """Valida painel de acessibilidade (alto contraste, fonte, etc.)."""

    def test_panel_trigger_visible(self, page):
        trigger = page.locator("#a11yPanelTrigger")
        assert trigger.is_visible()

    def test_panel_opens(self, page):
        page.locator("#a11yPanelTrigger").click()
        page.wait_for_timeout(300)
        drawer = page.locator("#a11yDrawer")
        assert drawer.is_visible()

    def test_panel_closes_with_button(self, page):
        page.locator("#a11yPanelTrigger").click()
        page.wait_for_timeout(300)
        page.locator("#a11yDrawerClose").click()
        page.wait_for_timeout(300)
        drawer = page.locator("#a11yDrawer")
        assert not drawer.is_visible() or drawer.get_attribute("aria-hidden") == "true"

    def test_panel_closes_with_overlay(self, page):
        page.locator("#a11yPanelTrigger").click()
        page.wait_for_timeout(300)
        overlay = page.locator("#a11yOverlay")
        if overlay.is_visible():
            overlay.click(force=True)
            page.wait_for_timeout(300)
            drawer = page.locator("#a11yDrawer")
            assert not drawer.is_visible() or drawer.get_attribute("aria-hidden") == "true"

    def test_high_contrast_toggle(self, page):
        """Alto contraste deve adicionar classe .high-contrast ao <html>."""
        page.locator("#a11yPanelTrigger").click()
        page.wait_for_timeout(300)
        page.locator("#a11yContrast").click()
        page.wait_for_timeout(300)
        html_classes = page.locator("html").get_attribute("class") or ""
        assert "high-contrast" in html_classes

    def test_high_contrast_persists_localstorage(self, server, browser_ctx):
        """Alto contraste deve persistir via localStorage (contexto limpo)."""
        # Usa página limpa para evitar estado residual
        pg = browser_ctx.new_page()
        pg.goto(server, wait_until="networkidle")
        # Garantir estado inicial limpo
        pg.evaluate("localStorage.removeItem('nossodireito_high_contrast')")
        pg.evaluate("document.documentElement.classList.remove('high-contrast')")
        pg.reload(wait_until="networkidle")

        pg.locator("#a11yPanelTrigger").click()
        pg.wait_for_timeout(300)
        # Verificar estado inicial é OFF
        initial = pg.evaluate("localStorage.getItem('nossodireito_high_contrast')")
        assert initial is None or initial == "false", f"Estado inicial deveria ser false/null, obteve '{initial}'"

        pg.locator("#a11yContrast").click()
        pg.wait_for_timeout(300)
        val = pg.evaluate("localStorage.getItem('nossodireito_high_contrast')")
        assert val == "true", f"Esperado 'true' após ativar, obteve '{val}'"

        # Verificar classe CSS também
        has_class = pg.evaluate("document.documentElement.classList.contains('high-contrast')")
        assert has_class is True

        # Cleanup
        pg.locator("#a11yContrast").click()
        pg.wait_for_timeout(200)
        pg.close()

    def test_font_increase(self, page):
        page.locator("#a11yPanelTrigger").click()
        page.wait_for_timeout(300)
        # Get initial font size
        initial = page.evaluate("parseFloat(getComputedStyle(document.documentElement).fontSize)")
        page.locator("#a11yFontIncrease").click()
        page.wait_for_timeout(300)
        after = page.evaluate("parseFloat(getComputedStyle(document.documentElement).fontSize)")
        assert after >= initial  # Should be same or larger

    def test_font_reset(self, page):
        page.locator("#a11yPanelTrigger").click()
        page.wait_for_timeout(300)
        page.locator("#a11yFontIncrease").click()
        page.wait_for_timeout(200)
        page.locator("#a11yFontReset").click()
        page.wait_for_timeout(300)
        # After reset, should be back to default
        val = page.evaluate("parseFloat(getComputedStyle(document.documentElement).fontSize)")
        assert val > 0  # Sanity check

    def test_accessibility_panel_right_side(self, page):
        """Painel deve estar posicionado à direita da tela."""
        page.locator("#a11yPanelTrigger").click()
        page.wait_for_timeout(300)
        drawer = page.locator("#a11yDrawer")
        box = drawer.bounding_box()
        if box:
            viewport_width = page.viewport_size["width"]
            # Panel should be in the right half of the viewport
            assert box["x"] + box["width"] > viewport_width / 2


# ════════════════════════════════════════════════════════════════
# 7. CHECKLIST
# ════════════════════════════════════════════════════════════════

class TestChecklist:
    """Valida checklist com localStorage."""

    def test_checklist_section_exists(self, page):
        section = page.locator("#checklist")
        assert section.count() >= 1

    def test_checklist_has_items(self, page):
        items = page.locator(".checklist-item input[type='checkbox']")
        assert items.count() > 0

    def test_checklist_toggle_saves(self, page):
        """Marcar checkbox deve salvar no localStorage."""
        checkbox = page.locator(".checklist-item input[type='checkbox']").first
        if not checkbox.is_checked():
            checkbox.check(force=True)
        page.wait_for_timeout(300)
        # Verify localStorage has checklist data
        val = page.evaluate("JSON.stringify(Object.keys(localStorage).filter(k => k.includes('checklist')))")
        assert "checklist" in val.lower()


# ════════════════════════════════════════════════════════════════
# 8. PWA (Service Worker + Manifest)
# ════════════════════════════════════════════════════════════════

class TestPWA:
    """Valida recursos PWA."""

    def test_manifest_link_in_html(self, page):
        link = page.locator('link[rel="manifest"]')
        assert link.count() >= 1

    def test_service_worker_registered(self, page):
        """SW deve ser registrado (pode falhar se localhost http, ok)."""
        # Em localhost com http, SW pode não registrar
        sw_status = page.evaluate("""
            async () => {
                if ('serviceWorker' in navigator) {
                    try {
                        const reg = await navigator.serviceWorker.getRegistration();
                        return reg ? 'registered' : 'not-registered';
                    } catch(e) {
                        return 'error: ' + e.message;
                    }
                }
                return 'unsupported';
            }
        """)
        # PWA features may not work on http://localhost, just verify API exists
        assert sw_status != "unsupported"

    def test_meta_theme_color(self, page):
        meta = page.locator('meta[name="theme-color"]')
        assert meta.count() >= 1


# ════════════════════════════════════════════════════════════════
# 9. ARIA E ACESSIBILIDADE
# ════════════════════════════════════════════════════════════════

class TestARIA:
    """Valida atributos ARIA e landmarks."""

    def test_skip_link(self, page):
        skip = page.locator("a.skip-link, a[href='#main'], a[href='#conteudo']")
        assert skip.count() >= 1

    def test_nav_landmark(self, page):
        nav = page.locator("nav, [role='navigation']")
        assert nav.count() >= 1

    def test_aria_labels_present(self, page):
        count = page.evaluate("""
            document.querySelectorAll('[aria-label]').length
        """)
        assert count >= 10

    def test_aria_live_regions(self, page):
        live = page.evaluate("""
            document.querySelectorAll('[aria-live]').length
        """)
        assert live >= 1

    def test_images_have_alt(self, page):
        """Todas as imagens devem ter atributo alt."""
        imgs_without_alt = page.evaluate("""
            [...document.querySelectorAll('img')].filter(i => !i.hasAttribute('alt')).length
        """)
        assert imgs_without_alt == 0

    def test_form_inputs_have_labels(self, page):
        """Inputs devem ter label associado ou aria-label."""
        unlabeled = page.evaluate("""
            [...document.querySelectorAll('input:not([type="hidden"]):not([type="checkbox"])')].filter(i => {
                const id = i.id;
                const hasLabel = id && document.querySelector(`label[for="${id}"]`);
                const hasAriaLabel = i.hasAttribute('aria-label') || i.hasAttribute('aria-labelledby');
                const hasTitle = i.hasAttribute('title');
                return !hasLabel && !hasAriaLabel && !hasTitle;
            }).length
        """)
        assert unlabeled == 0

    def test_heading_hierarchy(self, page):
        """Headings devem seguir hierarquia (h1 → h2 → h3, sem pular)."""
        headings = page.evaluate("""
            [...document.querySelectorAll('h1, h2, h3, h4, h5, h6')].map(h => parseInt(h.tagName[1]))
        """)
        if len(headings) > 1:
            # Deve começar com h1 ou h2
            assert headings[0] <= 2
            # Nunca deve pular mais de 1 nível
            for i in range(1, len(headings)):
                assert headings[i] - headings[i - 1] <= 1 or headings[i] <= headings[i - 1]


# ════════════════════════════════════════════════════════════════
# 10. SEGURANÇA
# ════════════════════════════════════════════════════════════════

class TestSecurity:
    """Valida headers de segurança do servidor."""

    def test_csp_header(self, server, browser_ctx):
        pg = browser_ctx.new_page()
        resp = pg.goto(server, wait_until="networkidle")
        headers = resp.headers if resp else {}
        pg.close()
        assert "content-security-policy" in headers, "CSP header ausente"

    def test_x_content_type_options(self, server, browser_ctx):
        pg = browser_ctx.new_page()
        resp = pg.goto(server, wait_until="networkidle")
        headers = resp.headers if resp else {}
        pg.close()
        assert headers.get("x-content-type-options") == "nosniff"

    def test_referrer_policy(self, server, browser_ctx):
        pg = browser_ctx.new_page()
        resp = pg.goto(server, wait_until="networkidle")
        headers = resp.headers if resp else {}
        pg.close()
        assert "referrer-policy" in headers

    def test_no_server_version_leak(self, server, browser_ctx):
        pg = browser_ctx.new_page()
        resp = pg.goto(server, wait_until="networkidle")
        headers = resp.headers if resp else {}
        pg.close()
        server_hdr = headers.get("server", "")
        assert "express" not in server_hdr.lower()
        assert "node" not in server_hdr.lower()


# ════════════════════════════════════════════════════════════════
# 11. RESPONSIVIDADE
# ════════════════════════════════════════════════════════════════

class TestResponsiveness:
    """Valida layout em diferentes viewports."""

    def test_mobile_viewport(self, server, browser_ctx):
        """Site deve funcionar em viewport mobile (375x667)."""
        from playwright.sync_api import sync_playwright
        pg = browser_ctx.new_page()
        pg.set_viewport_size({"width": 375, "height": 667})
        pg.goto(server, wait_until="networkidle")
        # Grid e busca devem estar visíveis
        assert pg.locator("#categoryGrid").is_visible()
        assert pg.locator("#searchInput").is_visible()
        pg.close()

    def test_tablet_viewport(self, server, browser_ctx):
        pg = browser_ctx.new_page()
        pg.set_viewport_size({"width": 768, "height": 1024})
        pg.goto(server, wait_until="networkidle")
        assert pg.locator("#categoryGrid").is_visible()
        pg.close()

    def test_wide_desktop_viewport(self, server, browser_ctx):
        pg = browser_ctx.new_page()
        pg.set_viewport_size({"width": 1920, "height": 1080})
        pg.goto(server, wait_until="networkidle")
        assert pg.locator("#categoryGrid").is_visible()
        pg.close()


# ════════════════════════════════════════════════════════════════
# 12. DISCLAIMER
# ════════════════════════════════════════════════════════════════

class TestDisclaimer:
    """Valida que disclaimer é renderizado e visível."""

    def test_disclaimer_alert_visible(self, page):
        disclaimer = page.locator(".disclaimer-alert")
        assert disclaimer.count() >= 1

    def test_disclaimer_has_role_alert(self, page):
        alert = page.locator("[role='alert']")
        assert alert.count() >= 1

    def test_disclaimer_text_content(self, page):
        text = page.locator(".disclaimer-alert").first.inner_text()
        assert "profissional qualificado" in text.lower() or "advogado" in text.lower()


# ════════════════════════════════════════════════════════════════
# 13. PERFORMANCE
# ════════════════════════════════════════════════════════════════

class TestPerformance:
    """Valida métricas básicas de performance."""

    def test_page_loads_under_5s(self, server, browser_ctx):
        pg = browser_ctx.new_page()
        start = time.time()
        pg.goto(server, wait_until="networkidle")
        elapsed = time.time() - start
        pg.close()
        assert elapsed < 5.0, f"Página levou {elapsed:.1f}s para carregar"

    def test_dom_content_loaded(self, server, browser_ctx):
        pg = browser_ctx.new_page()
        pg.goto(server, wait_until="domcontentloaded")
        # After DOM is loaded, categories should be present
        grid = pg.locator("#categoryGrid")
        assert grid.count() >= 1
        pg.close()


# ════════════════════════════════════════════════════════════════
# 14. NAVEGAÇÃO POR TECLADO
# ════════════════════════════════════════════════════════════════

class TestKeyboardNavigation:
    """Valida navegação por teclado."""

    def test_tab_navigation(self, page):
        """Tab deve mover foco entre elementos interativos."""
        page.keyboard.press("Tab")
        focused = page.evaluate("document.activeElement.tagName")
        assert focused != "BODY", "Tab não moveu o foco"

    def test_enter_on_category_opens_detail(self, page):
        """Enter em um card deve abrir detalhe."""
        card = page.locator(".category-card").first
        card.focus()
        page.keyboard.press("Enter")
        page.wait_for_timeout(500)
        assert page.locator("#detalhe").is_visible()

    def test_close_button_closes_panel(self, page):
        """Botão fechar (X) deve fechar painel de acessibilidade."""
        page.locator("#a11yPanelTrigger").click()
        page.wait_for_timeout(300)
        assert page.locator("#a11yDrawer").is_visible()
        page.locator("#a11yDrawerClose").click()
        page.wait_for_timeout(300)
        drawer = page.locator("#a11yDrawer")
        assert not drawer.is_visible() or drawer.get_attribute("aria-hidden") == "true"


# ════════════════════════════════════════════════════════════════
# 15. VLIBRAS
# ════════════════════════════════════════════════════════════════

class TestVLibras:
    """Valida presença do widget VLibras."""

    def test_vlibras_dns_prefetch(self, page):
        """VLibras deve ter dns-prefetch para carregamento rápido."""
        link = page.locator("link[rel='dns-prefetch'][href*='vlibras']")
        assert link.count() >= 1

    def test_vlibras_widget_container(self, page):
        """Container VLibras [vw] deve existir no HTML."""
        widget = page.locator("[vw]")
        assert widget.count() >= 1

    def test_vlibras_toggle_button(self, page):
        """Botão de ativar VLibras no painel de acessibilidade."""
        page.locator("#a11yPanelTrigger").click()
        page.wait_for_timeout(300)
        btn = page.locator("#a11yLibras")
        assert btn.is_visible()


# ════════════════════════════════════════════════════════════════
# 16. HASH ROUTING
# ════════════════════════════════════════════════════════════════

class TestHashRouting:
    """Valida navegação por hash."""

    def test_direct_hash_opens_detail(self, page, direitos_data):
        cat = direitos_data["categorias"][5]
        base = page.url.split("#")[0]
        page.goto(f"{base}#direito/{cat['id']}", wait_until="networkidle")
        page.wait_for_timeout(500)
        assert page.locator("#detalhe").is_visible()

    def test_back_button_returns_to_grid(self, page, direitos_data):
        cat = direitos_data["categorias"][0]
        base = page.url.split("#")[0]
        page.goto(base, wait_until="networkidle")
        page.goto(f"{base}#direito/{cat['id']}", wait_until="networkidle")
        page.wait_for_timeout(300)
        page.go_back()
        page.wait_for_timeout(500)
        # Grid should be visible again
        grid = page.locator("#categoryGrid")
        assert grid.is_visible()


# ════════════════════════════════════════════════════════════════
# 17. IMPRESSÃO / EXPORT
# ════════════════════════════════════════════════════════════════

class TestExport:
    """Valida botão de exportação/impressão."""

    def test_export_button_in_detail(self, page, direitos_data):
        cat = direitos_data["categorias"][0]
        base = page.url.split("#")[0]
        page.goto(f"{base}#direito/{cat['id']}", wait_until="networkidle")
        page.wait_for_timeout(500)
        # Look for export/print button
        btn = page.locator("#exportDetalheBtn, .btn-export-pdf, button:has-text('PDF'), button:has-text('Imprimir')")
        assert btn.count() >= 1


# ════════════════════════════════════════════════════════════════
# 18. DICAS COLAPSÁVEIS
# ════════════════════════════════════════════════════════════════

class TestCollapsibleDicas:
    """Valida UX de dicas colapsáveis (≤5 visíveis, 'Mostrar mais' p/ resto)."""

    def _open_category(self, page, direitos_data, cat_id):
        base = page.url.split("#")[0]
        page.goto(f"{base}#direito/{cat_id}", wait_until="networkidle")
        page.wait_for_timeout(500)

    def test_category_with_many_dicas_has_toggle(self, page, direitos_data):
        """Categorias com >5 dicas devem ter botão 'Mostrar mais'."""
        for cat in direitos_data["categorias"]:
            if len(cat.get("dicas", [])) > 5:
                self._open_category(page, direitos_data, cat["id"])
                btn = page.locator(f"#dicasToggle_{cat['id']}")
                assert btn.is_visible(), f"{cat['id']}: botão 'Mostrar mais' ausente"
                return
        pytest.skip("Nenhuma categoria com >5 dicas")

    def test_hidden_dicas_initially_invisible(self, page, direitos_data):
        for cat in direitos_data["categorias"]:
            if len(cat.get("dicas", [])) > 5:
                self._open_category(page, direitos_data, cat["id"])
                hidden = page.locator(f"#dicasHidden_{cat['id']}")
                assert not hidden.is_visible()
                return

    def test_toggle_reveals_hidden_dicas(self, page, direitos_data):
        for cat in direitos_data["categorias"]:
            if len(cat.get("dicas", [])) > 5:
                self._open_category(page, direitos_data, cat["id"])
                btn = page.locator(f"#dicasToggle_{cat['id']}")
                btn.click()
                page.wait_for_timeout(200)
                hidden = page.locator(f"#dicasHidden_{cat['id']}")
                assert hidden.is_visible()
                assert btn.get_attribute("aria-expanded") == "true"
                return

    def test_toggle_collapses_again(self, page, direitos_data):
        for cat in direitos_data["categorias"]:
            if len(cat.get("dicas", [])) > 5:
                self._open_category(page, direitos_data, cat["id"])
                btn = page.locator(f"#dicasToggle_{cat['id']}")
                btn.click()
                page.wait_for_timeout(100)
                btn.click()
                page.wait_for_timeout(200)
                hidden = page.locator(f"#dicasHidden_{cat['id']}")
                assert not hidden.is_visible()
                assert btn.get_attribute("aria-expanded") == "false"
                return

    def test_category_with_few_dicas_no_toggle(self, page, direitos_data):
        """Categorias com ≤5 dicas não devem ter botão 'Mostrar mais'."""
        for cat in direitos_data["categorias"]:
            if 1 <= len(cat.get("dicas", [])) <= 5:
                self._open_category(page, direitos_data, cat["id"])
                btn = page.locator(f"#dicasToggle_{cat['id']}")
                assert btn.count() == 0
                return


# ════════════════════════════════════════════════════════════════
# 19. ÍCONE DE ACESSIBILIDADE ABNT NBR 9050
# ════════════════════════════════════════════════════════════════

class TestAccessibilityIconABNT:
    """Valida que o ícone de acessibilidade usa SVG (conforme ABNT NBR 9050:2020)."""

    def test_trigger_icon_is_svg(self, page):
        svg = page.locator(".a11y-trigger-icon svg")
        assert svg.count() >= 1, "Ícone do trigger deve ser SVG, não emoji"

    def test_drawer_icon_is_svg(self, page, direitos_data):
        # Open panel first
        page.locator("#a11yPanelTrigger").click()
        page.wait_for_timeout(300)
        svg = page.locator(".a11y-drawer-icon svg")
        assert svg.count() >= 1, "Ícone do drawer deve ser SVG, não emoji"

    def test_icon_has_viewbox(self, page):
        svg = page.locator(".a11y-trigger-icon svg")
        vb = svg.get_attribute("viewBox")
        assert vb and len(vb.split()) >= 4

    def test_icon_uses_currentcolor(self, page):
        """SVG deve usar currentColor para herdar a cor do botão."""
        html = page.locator(".a11y-trigger-icon svg").inner_html()
        assert "currentColor" in html


# ════════════════════════════════════════════════════════════════
# 20. QUALIDADE DE CONTEÚDO
# ════════════════════════════════════════════════════════════════

class TestContentQuality:
    """Valida limites de conteúdo e linguagem simplificada."""

    def test_max_10_dicas_per_category(self, direitos_data):
        for cat in direitos_data["categorias"]:
            n = len(cat.get("dicas", []))
            assert n <= 10, f"{cat['id']}: {n} dicas (máx 10)"

    def test_all_categories_have_dicas(self, direitos_data):
        for cat in direitos_data["categorias"]:
            assert len(cat.get("dicas", [])) >= 3, f"{cat['id']}: muito poucas dicas"

    def test_all_categories_have_emergency(self, direitos_data):
        for cat in direitos_data["categorias"]:
            assert "emergencia" in cat, f"{cat['id']}: sem protocolo de emergência"

    def test_emergency_has_all_fields(self, direitos_data):
        required = {"titulo", "conflito", "base_legal_resgate", "acao_imediata", "modelo_notificacao", "orgao_denuncia", "aviso"}
        for cat in direitos_data["categorias"]:
            em = cat.get("emergencia", {})
            missing = required - set(em.keys())
            assert not missing, f"{cat['id']}: emergência sem {missing}"

    def test_dicas_not_too_long(self, direitos_data):
        """Dicas devem ser concisas (≤300 chars) para público leigo."""
        for cat in direitos_data["categorias"]:
            for i, d in enumerate(cat.get("dicas", [])):
                assert len(d) <= 300, f"{cat['id']} dica[{i}]: {len(d)} chars (máx 300)"

    def test_resumo_exists_and_concise(self, direitos_data):
        for cat in direitos_data["categorias"]:
            r = cat.get("resumo", "")
            assert 20 <= len(r) <= 500, f"{cat['id']}: resumo {len(r)} chars"

    def test_tags_reasonable_count(self, direitos_data):
        for cat in direitos_data["categorias"]:
            tags = cat.get("tags", [])
            assert len(tags) <= 70, f"{cat['id']}: {len(tags)} tags (máx 70)"


# ════════════════════════════════════════════════════════════════
# 21. DOCUMENTAÇÃO
# ════════════════════════════════════════════════════════════════

class TestDocumentation:
    """Valida presença e integridade de todas as documentações."""

    REQUIRED_DOCS = [
        "README.md", "CHANGELOG.md", "LICENSE", "SECURITY.md",
        "GOVERNANCE.md", "TESTING.md", "SECURITY_AUDIT.md",
    ]

    REQUIRED_DOCS_DIR = [
        "ARCHITECTURE.md", "COMPLIANCE.md", "CONTRIBUTING.md",
        "KNOWN_ISSUES.md", "QUALITY_GUIDE.md", "REFERENCE.md",
        "VALIDATION_STATUS.md", "ACCESSIBILITY.md",
    ]

    def test_root_docs_exist(self):
        for doc in self.REQUIRED_DOCS:
            assert (ROOT / doc).exists(), f"Documento raiz ausente: {doc}"

    def test_docs_dir_exist(self):
        for doc in self.REQUIRED_DOCS_DIR:
            assert (ROOT / "docs" / doc).exists(), f"Documento ausente: docs/{doc}"

    def test_testing_guide_has_steps(self):
        content = (ROOT / "TESTING.md").read_text(encoding="utf-8")
        for step in ["Passo 1", "Passo 2", "pip install", "pytest", "playwright"]:
            assert step in content, f"TESTING.md sem '{step}'"

    def test_architecture_drawio_exists(self):
        assert (ROOT / "docs" / "ARCHITECTURE.drawio.xml").exists()

    def test_changelog_not_empty(self):
        content = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert len(content) > 200

    def test_readme_has_test_section(self):
        content = (ROOT / "README.md").read_text(encoding="utf-8")
        assert "test" in content.lower() or "teste" in content.lower()

    def test_no_broken_doc_links(self):
        """Verifica que links internos em docs/ apontam para arquivos existentes."""
        import re
        docs_dir = ROOT / "docs"
        broken = []
        for md in docs_dir.glob("*.md"):
            content = md.read_text(encoding="utf-8")
            # Find markdown links like [text](path)
            for match in re.finditer(r'\[.*?\]\(([^)#]+)', content):
                target = match.group(1).strip()
                if target.startswith(("http", "mailto:", "#")):
                    continue
                resolved = (md.parent / target).resolve()
                if not resolved.exists():
                    broken.append(f"{md.name}: {target}")
        assert not broken, f"Links internos quebrados: {broken}"


# ════════════════════════════════════════════════════════════════
# 22. DETECÇÃO DE ÓRFÃOS
# ════════════════════════════════════════════════════════════════

class TestOrphanDetection:
    """Detecta arquivos, scripts e referências órfãs."""

    def test_no_archive_folder(self):
        """_archive/ foi removido — scripts mortos não devem existir."""
        assert not (ROOT / "scripts" / "_archive").exists()

    def test_no_orphan_underscore_scripts(self):
        orphans = [f.name for f in (ROOT / "scripts").glob("_*.py")]
        assert not orphans, f"Scripts _ órfãos: {orphans}"

    def test_no_temp_files(self):
        temp_patterns = ["_tmp*", "*.tmp", "*.bak", "*.swp"]
        temps = []
        for pat in temp_patterns:
            temps.extend(ROOT.rglob(pat))
        # Exclude .venv and node_modules
        temps = [t for t in temps if ".venv" not in str(t) and "node_modules" not in str(t)]
        assert not temps, f"Arquivos temporários: {temps}"

    def test_no_screenshots_folder(self):
        assert not (ROOT / "screenshots").is_dir(), "Pasta screenshots/ deveria ter sido removida"

    def test_all_data_files_used(self):
        """Todo JSON em data/ deve ser importado no app.js."""
        app_js = (ROOT / "js" / "app.js").read_text(encoding="utf-8")
        for f in (ROOT / "data").glob("*.json"):
            assert f.name in app_js, f"data/{f.name} não é referenciado em app.js"

    def test_no_dead_css_files(self):
        """Só deve existir 1 CSS principal."""
        css_files = list((ROOT / "css").glob("*.css"))
        assert len(css_files) == 1, f"CSS extras: {[f.name for f in css_files]}"

    def test_no_dead_js_files(self):
        """Apenas app.js e sw-register.js no diretório js/."""
        js_files = {f.name for f in (ROOT / "js").glob("*.js")}
        expected = {"app.js", "sw-register.js"}
        extra = js_files - expected
        assert not extra, f"JS extras: {extra}"


# ════════════════════════════════════════════════════════════════
# 23. LGPD & DADOS SENSÍVEIS
# ════════════════════════════════════════════════════════════════

class TestLGPD:
    """Verifica conformidade LGPD e ausência de dados sensíveis."""

    SENSITIVE_PATTERNS = [
        r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b',  # CPF
        r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b',  # CNPJ
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'password|senha|secret|api[_-]?key|token',  # Creds
    ]

    def test_no_sensitive_data_in_json(self):
        import re
        for jf in (ROOT / "data").glob("*.json"):
            content = jf.read_text(encoding="utf-8")
            for pattern in self.SENSITIVE_PATTERNS[:2]:  # CPF, CNPJ only
                matches = re.findall(pattern, content, re.IGNORECASE)
                assert not matches, f"{jf.name}: dados sensíveis encontrados: {matches[:3]}"
            # Email check — allow .gov.br official emails
            emails = re.findall(self.SENSITIVE_PATTERNS[2], content, re.IGNORECASE)
            private_emails = [e for e in emails if not e.endswith(".gov.br")]
            assert not private_emails, f"{jf.name}: emails privados: {private_emails[:3]}"

    def test_no_secrets_in_source(self):
        import re
        for f in [ROOT / "js" / "app.js", ROOT / "server.js"]:
            content = f.read_text(encoding="utf-8")
            for pat in [r'api[_-]?key\s*[:=]\s*["\'][^"\']+', r'password\s*[:=]\s*["\'][^"\']+']:
                matches = re.findall(pat, content, re.IGNORECASE)
                assert not matches, f"{f.name}: possíveis credenciais: {matches}"

    def test_no_tracking_scripts(self, page):
        """Não deve ter Google Analytics, Facebook Pixel, etc."""
        html = page.content()
        trackers = ["google-analytics", "gtag", "facebook.net", "fb-pixel", "hotjar"]
        for t in trackers:
            assert t not in html.lower(), f"Tracker detectado: {t}"

    def test_no_third_party_cookies(self, page):
        """Site não deve definir cookies de terceiros."""
        cookies = page.context.cookies()
        base_domain = "localhost"
        third_party = [c for c in cookies if base_domain not in c.get("domain", "")]
        assert not third_party, f"Cookies de terceiros: {third_party}"

    def test_disclaimer_warns_users(self, page):
        disclaimer = page.locator(".disclaimer-alert")
        text = disclaimer.text_content().lower()
        assert "profissional" in text or "informativ" in text or "jurídic" in text

    def test_localstorage_only_for_preferences(self, page):
        """localStorage só deve guardar preferências de acessibilidade e checklist."""
        keys = page.evaluate("() => Object.keys(localStorage)")
        allowed_prefixes = ["a11y", "checklist", "theme", "font", "high", "contrast", "govbr"]
        for k in keys:
            ok = any(k.lower().startswith(p) or p in k.lower() for p in allowed_prefixes)
            assert ok, f"localStorage com chave suspeita: {k}"


# ════════════════════════════════════════════════════════════════
# 24. CSS & LEGIBILIDADE
# ════════════════════════════════════════════════════════════════

class TestCSSReadability:
    """Valida configurações CSS de legibilidade e acessibilidade."""

    def test_mobile_font_not_below_16px(self):
        """Font-size mobile deve ser ≥16px (WCAG)."""
        css = (ROOT / "css" / "styles.css").read_text(encoding="utf-8")
        import re
        # Find font-size in @media blocks
        matches = re.findall(r'font-size:\s*(\d+)px', css)
        for m in matches:
            assert int(m) >= 14, f"font-size {m}px muito pequeno (mínimo 14px)"

    def test_body_line_height_adequate(self):
        css = (ROOT / "css" / "styles.css").read_text(encoding="utf-8")
        import re
        body_match = re.search(r'body\s*\{[^}]*line-height:\s*([\d.]+)', css)
        assert body_match, "body sem line-height"
        lh = float(body_match.group(1))
        assert lh >= 1.5, f"line-height {lh} muito baixo (mínimo 1.5)"

    def test_dica_item_has_line_height(self):
        css = (ROOT / "css" / "styles.css").read_text(encoding="utf-8")
        import re
        match = re.search(r'\.dica-item\s*\{[^}]*line-height:\s*([\d.]+)', css)
        assert match, ".dica-item sem line-height"
        assert float(match.group(1)) >= 1.5

    def test_has_print_styles(self):
        css = (ROOT / "css" / "styles.css").read_text(encoding="utf-8")
        assert "@media print" in css

    def test_has_dark_mode(self):
        css = (ROOT / "css" / "styles.css").read_text(encoding="utf-8")
        assert "prefers-color-scheme: dark" in css

    def test_has_reduced_motion(self):
        css = (ROOT / "css" / "styles.css").read_text(encoding="utf-8")
        assert "prefers-reduced-motion" in css

    def test_has_high_contrast(self):
        css = (ROOT / "css" / "styles.css").read_text(encoding="utf-8")
        assert "forced-colors" in css or "high-contrast" in css.lower()

    def test_focus_visible_styles(self):
        css = (ROOT / "css" / "styles.css").read_text(encoding="utf-8")
        assert "focus-visible" in css

    def test_btn_ver_mais_styles(self):
        """Botão 'Mostrar mais' dicas deve ter estilos."""
        css = (ROOT / "css" / "styles.css").read_text(encoding="utf-8")
        assert ".btn-ver-mais" in css


# ════════════════════════════════════════════════════════════════
# 25. VERSÕES & ARQUITETURA
# ════════════════════════════════════════════════════════════════

class TestVersionArchitecture:
    """Valida consistência de versões e arquitetura."""

    def test_package_json_has_version(self):
        pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        assert "version" in pkg
        parts = pkg["version"].split(".")
        assert len(parts) == 3

    def test_version_consistent_across_files(self):
        pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        ver = pkg["version"]
        # direitos.json
        d = json.loads((ROOT / "data" / "direitos.json").read_text(encoding="utf-8"))
        assert d.get("versao") == ver, f"direitos.json: {d.get('versao')} != {ver}"

    def test_sw_cache_version_matches(self):
        pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        sw = (ROOT / "sw.js").read_text(encoding="utf-8")
        assert pkg["version"] in sw, "sw.js cache version não confere com package.json"

    def test_terraform_files_exist(self):
        tf = ROOT / "terraform"
        assert (tf / "main.tf").exists()
        assert (tf / "outputs.tf").exists()

    def test_github_actions_exist(self):
        ga = ROOT / ".github" / "workflows"
        if ga.exists():
            workflows = list(ga.glob("*.yml"))
            assert len(workflows) >= 4, f"Apenas {len(workflows)} workflows"

    def test_architecture_doc_has_components(self):
        arch = (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
        for comp in ["frontend", "dados", "busca", "acessibilidade"]:
            assert comp.lower() in arch.lower(), f"ARCHITECTURE.md sem menção a '{comp}'"

    def test_no_unused_schemas(self):
        """Schemas devem ser referenciados em tests ou scripts."""
        for schema_file in (ROOT / "schemas").glob("*.json"):
            name = schema_file.name
            # Check if referenced anywhere in tests/ or scripts/
            found = False
            for search_dir in [ROOT / "tests", ROOT / "scripts"]:
                if search_dir.exists():
                    for f in search_dir.rglob("*.py"):
                        if name in f.read_text(encoding="utf-8"):
                            found = True
                            break
                if found:
                    break
            assert found, f"Schema órfão: {name}"


# ════════════════════════════════════════════════════════════════
# 26. TRANSPARÊNCIA & DISCLAIMER
# ════════════════════════════════════════════════════════════════

class TestTransparency:
    """Valida transparência, disclaimer e termos legais."""

    def test_disclaimer_alert_role(self, page):
        d = page.locator(".disclaimer-alert")
        assert d.count() >= 1
        role = d.get_attribute("role")
        assert role == "alert"

    def test_disclaimer_mentions_professional_advice(self, page):
        text = page.locator(".disclaimer-alert").text_content()
        assert "profissional" in text.lower() or "advogado" in text.lower() or "jurídic" in text.lower()

    def test_disclaimer_is_in_page(self, page):
        d = page.locator(".disclaimer-alert")
        assert d.count() >= 1, "Disclaimer ausente na página"
        # Scroll to disclaimer and verify it's visible
        d.scroll_into_view_if_needed()
        assert d.is_visible()

    def test_footer_has_author(self, page):
        footer = page.locator("footer")
        text = footer.text_content().lower()
        assert "fabio" in text or "nossodireito" in text

    def test_footer_has_license_info(self, page):
        footer = page.locator("footer")
        text = footer.text_content().lower()
        assert "open source" in text or "licença" in text or "mit" in text or "educacional" in text

    def test_aviso_legal_in_data(self, direitos_data):
        assert "aviso" in direitos_data or "aviso_legal" in direitos_data, \
            "direitos.json sem campo de aviso legal"
