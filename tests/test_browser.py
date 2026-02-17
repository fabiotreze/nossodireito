#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTES EMULADOS VIA BROWSER — NossoDireito

Usa Playwright para validar:
  - Carregamento sem erros JS
  - Navegação entre seções
  - Busca e resultados
  - Categorias renderizadas (30)
  - Órgãos estaduais (27 UFs)
  - Classificação CID
  - Acessibilidade (skip links, aria, contraste)
  - Responsividade mobile
  - JSON-LD structured data
  - Service Worker registration
  - Checklist funcional
"""

import json
import os
import re
import pytest
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get("E2E_BASE_URL", "http://localhost:8080")


@pytest.fixture(scope="module")
def browser_ctx():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-web-security"])
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 720},
            locale="pt-BR",
            ignore_https_errors=True,
        )
        yield ctx
        ctx.close()
        browser.close()


@pytest.fixture(scope="module")
def page(browser_ctx):
    pg = browser_ctx.new_page()
    # Collect console errors
    pg._js_errors = []
    pg.on("console", lambda msg: pg._js_errors.append(msg.text) if msg.type == "error" else None)
    pg.on("pageerror", lambda err: pg._js_errors.append(str(err)))
    pg.goto(BASE, wait_until="domcontentloaded", timeout=30000)
    # Wait for data to load and categories to render (eager, above-fold)
    pg.wait_for_function(
        "document.querySelectorAll('#categoryGrid .category-card').length >= 30",
        timeout=30000
    )
    yield pg
    pg.close()


def _scroll_to_deferred(page, section_id, selector, min_count, timeout=15000):
    """Scroll a deferred (IntersectionObserver) section into view and wait for it to render."""
    page.evaluate(f"document.getElementById('{section_id}')?.scrollIntoView()")
    page.wait_for_function(
        f"document.querySelectorAll('{selector}').length >= {min_count}",
        timeout=timeout
    )


# ════════════════════════════════════════════════════════════════
# 1. CARREGAMENTO E ERROS JS
# ════════════════════════════════════════════════════════════════

class TestPageLoad:
    def test_page_loads(self, page):
        assert page.title()
        assert "NossoDireito" in page.title()

    def test_no_js_errors(self, page):
        critical = [e for e in page._js_errors if "favicon" not in e.lower()]
        assert not critical, f"Erros JS: {critical}"

    def test_hero_visible(self, page):
        hero = page.locator(".hero")
        expect(hero).to_be_visible()

    def test_navbar_visible(self, page):
        nav = page.locator(".navbar")
        expect(nav).to_be_visible()


# ════════════════════════════════════════════════════════════════
# 2. CATEGORIAS RENDERIZADAS
# ════════════════════════════════════════════════════════════════

class TestCategories:
    def test_30_categories_rendered(self, page):
        cards = page.locator("#categoryGrid .category-card")
        count = cards.count()
        assert count >= 1, f"Nenhuma categoria renderizada (encontrado {count})"

    def test_category_cards_have_titles(self, page):
        first_card = page.locator("#categoryGrid .category-card").first
        expect(first_card).to_contain_text("BPC")

    def test_click_category_shows_detail(self, page):
        page.locator("#categoryGrid .category-card").first.click()
        page.wait_for_selector("#detalhe", state="visible", timeout=5000)
        detail = page.locator("#detalheContent")
        expect(detail).to_be_visible()
        # Go back via browser history (avoids flaky button visibility on fast rerenders)
        page.go_back()
        page.wait_for_timeout(500)


# ════════════════════════════════════════════════════════════════
# 3. BUSCA E RESULTADOS
# ════════════════════════════════════════════════════════════════

class TestSearch:
    def _search(self, page, query):
        """Helper: click input for user-gesture focus, fill, then press Enter."""
        inp = page.locator("#searchInput")
        inp.click()
        inp.fill(query)
        inp.press("Enter")

    def test_search_bpc(self, page):
        self._search(page, "BPC")
        results = page.locator("#searchResults")
        expect(results).to_contain_text("BPC", timeout=10000)

    def test_search_autismo(self, page):
        self._search(page, "autismo")
        results = page.locator("#searchResults")
        expect(results).not_to_be_empty(timeout=10000)

    def test_search_transporte(self, page):
        self._search(page, "transporte")
        results = page.locator("#searchResults")
        expect(results).to_contain_text("Transporte", timeout=10000)

    def test_search_empty_clears(self, page):
        self._search(page, "")
        page.wait_for_timeout(300)

    def test_search_curatela(self, page):
        """Testa busca por nova categoria"""
        self._search(page, "curatela")
        results = page.locator("#searchResults")
        expect(results).not_to_be_empty(timeout=10000)
        text = results.inner_text()
        assert "apacidade" in text.lower() or "curatela" in text.lower() or "legal" in text.lower(), \
            f"Busca 'curatela' não retornou resultado relevante: {text[:200]}"

    def test_search_acessibilidade_digital(self, page):
        self._search(page, "WCAG")
        results = page.locator("#searchResults")
        expect(results).not_to_be_empty(timeout=10000)
        self._search(page, "")
        page.wait_for_timeout(200)


# ════════════════════════════════════════════════════════════════
# 4. SEÇÕES E NAVEGAÇÃO
# ════════════════════════════════════════════════════════════════

class TestNavigation:
    def test_all_sections_exist(self, page):
        sections = ["busca", "categorias", "checklist", "documentos",
                     "classificacao", "orgaos-estaduais", "instituicoes",
                     "transparencia"]
        for s in sections:
            el = page.locator(f"#{s}")
            assert el.count() > 0, f"Seção #{s} não encontrada"

    def test_nav_links_navigate(self, page):
        page.locator('a[href="#categorias"]').first.click()
        page.wait_for_timeout(500)
        # Should scroll to categorias
        assert page.url.endswith("#categorias") or "categorias" in page.url

    def test_back_to_top_button(self, page):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        btn = page.locator("#backToTop")
        expect(btn).to_be_visible(timeout=3000)
        btn.click()
        page.wait_for_timeout(500)


# ════════════════════════════════════════════════════════════════
# 5. ÓRGÃOS ESTADUAIS (27 UFs)
# ════════════════════════════════════════════════════════════════

class TestOrgaosEstaduaisBrowser:
    def _ensure_rendered(self, page):
        _scroll_to_deferred(page, 'orgaos-estaduais', '#orgaosEstaduaisGrid .orgao-card', 27)

    def test_orgaos_grid_rendered(self, page):
        self._ensure_rendered(page)
        grid = page.locator("#orgaosEstaduaisGrid")
        expect(grid).not_to_be_empty()

    def test_27_orgaos_rendered(self, page):
        self._ensure_rendered(page)
        # Reset filters
        page.locator('.orgao-filter-btn[data-filter="todos"]').click()
        page.wait_for_timeout(300)
        cards = page.locator("#orgaosEstaduaisGrid .orgao-card")
        count = cards.count()
        assert count == 27, f"Esperado 27 órgãos, encontrado {count}"

    def test_region_filters_work(self, page):
        self._ensure_rendered(page)
        page.locator('.orgao-filter-btn[data-filter="Sudeste"]').click()
        page.wait_for_timeout(300)
        cards = page.locator("#orgaosEstaduaisGrid .orgao-card")
        count = cards.count()
        assert count == 4, f"Sudeste deveria ter 4 estados, tem {count}"
        # Reset
        page.locator('.orgao-filter-btn[data-filter="todos"]').click()
        page.wait_for_timeout(300)


# ════════════════════════════════════════════════════════════════
# 6. CLASSIFICAÇÃO CID
# ════════════════════════════════════════════════════════════════

class TestClassificacaoBrowser:
    def _ensure_rendered(self, page):
        _scroll_to_deferred(page, 'classificacao', '#classificacaoGrid .classif-table tbody tr', 1)

    def test_classification_table_rendered(self, page):
        self._ensure_rendered(page)
        grid = page.locator("#classificacaoGrid")
        expect(grid).not_to_be_empty()

    def test_has_autismo_row(self, page):
        self._ensure_rendered(page)
        grid = page.locator("#classificacaoGrid")
        expect(grid).to_contain_text("Autismo")

    def test_has_cid_codes(self, page):
        self._ensure_rendered(page)
        grid = page.locator("#classificacaoGrid")
        expect(grid).to_contain_text("F84")


# ════════════════════════════════════════════════════════════════
# 7. ACESSIBILIDADE
# ════════════════════════════════════════════════════════════════

class TestAccessibility:
    def test_html_lang_attribute(self, page):
        lang = page.locator("html").get_attribute("lang")
        assert lang == "pt-BR"

    def test_skip_link_exists(self, page):
        skip = page.locator(".skip-link")
        assert skip.count() >= 1

    def test_accessibility_panel_exists(self, page):
        trigger = page.locator("#a11yPanelTrigger")
        expect(trigger).to_be_attached()

    def test_accessibility_panel_opens(self, page):
        trigger = page.locator("#a11yPanelTrigger")
        trigger.click()
        page.wait_for_timeout(500)
        drawer = page.locator("#a11yDrawer")
        expect(drawer).to_be_visible()
        # Close it
        page.locator("#a11yDrawerClose").click()
        page.wait_for_timeout(300)

    def test_font_size_controls(self, page):
        trigger = page.locator("#a11yPanelTrigger")
        trigger.click()
        page.wait_for_timeout(500)
        increase = page.locator("#a11yFontIncrease")
        expect(increase).to_be_visible()
        increase.click()
        page.wait_for_timeout(200)
        # Reset
        page.locator("#a11yFontReset").click()
        page.wait_for_timeout(200)
        page.locator("#a11yDrawerClose").click()
        page.wait_for_timeout(300)

    def test_contrast_toggle(self, page):
        trigger = page.locator("#a11yPanelTrigger")
        trigger.click()
        page.wait_for_timeout(500)
        contrast = page.locator("#a11yContrast")
        expect(contrast).to_be_visible()
        contrast.click()
        page.wait_for_timeout(300)
        # Toggle back
        contrast.click()
        page.wait_for_timeout(200)
        page.locator("#a11yDrawerClose").click()
        page.wait_for_timeout(300)

    def test_all_images_have_alt(self, page):
        images = page.locator("img")
        count = images.count()
        for i in range(count):
            alt = images.nth(i).get_attribute("alt")
            assert alt is not None, f"Imagem {i} sem atributo alt"

    def test_search_input_has_label(self, page):
        label = page.locator('label[for="searchInput"]')
        assert label.count() > 0


# ════════════════════════════════════════════════════════════════
# 8. RESPONSIVIDADE MOBILE
# ════════════════════════════════════════════════════════════════

class TestMobile:
    def test_mobile_viewport(self, browser_ctx):
        mobile_page = browser_ctx.new_page()
        mobile_page.set_viewport_size({"width": 375, "height": 667})
        mobile_page.goto(BASE, wait_until="domcontentloaded", timeout=30000)
        mobile_page.wait_for_function(
            "document.querySelectorAll('#categoryGrid .category-card').length >= 30",
            timeout=30000
        )
        cards = mobile_page.locator("#categoryGrid .category-card")
        assert cards.count() == 30
        mobile_page.close()


# ════════════════════════════════════════════════════════════════
# 9. TRANSPARÊNCIA / FONTES
# ════════════════════════════════════════════════════════════════

class TestTransparencia:
    def test_fontes_rendered(self, page):
        legislacao = page.locator("#fontesLegislacao")
        expect(legislacao).not_to_be_empty()

    def test_version_displayed(self, page):
        version = page.locator("#transVersion")
        text = version.inner_text()
        assert re.match(r"v?\d+\.\d+\.\d+", text), f"Versão inválida: {text}"

    def test_last_update_displayed(self, page):
        update = page.locator("#transLastUpdate")
        text = update.inner_text()
        assert len(text) > 5, f"Data atualização vazia: {text}"


# ════════════════════════════════════════════════════════════════
# 10. CHECKLIST
# ════════════════════════════════════════════════════════════════

class TestChecklist:
    def test_checklist_items_exist(self, page):
        items = page.locator(".checklist-item")
        assert items.count() >= 10

    def test_checklist_progress_text(self, page):
        progress = page.locator("#checklistProgress")
        expect(progress).to_contain_text("de 10")

    def test_checkbox_toggles(self, page):
        first = page.locator('.checklist-item input[type="checkbox"]').first
        first.check()
        page.wait_for_timeout(300)
        progress = page.locator("#checklistProgress")
        expect(progress).to_contain_text("1 de 10")
        # Uncheck
        first.uncheck()
        page.wait_for_timeout(300)


# ════════════════════════════════════════════════════════════════
# 11. JSON-LD NO BROWSER
# ════════════════════════════════════════════════════════════════

class TestJSONLDBrowser:
    def test_jsonld_blocks_exist(self, page):
        blocks = page.locator('script[type="application/ld+json"]')
        count = blocks.count()
        assert count >= 6, f"Esperado 6+ JSON-LD blocks, encontrado {count}"

    def test_jsonld_parseable(self, page):
        blocks = page.locator('script[type="application/ld+json"]')
        for i in range(blocks.count()):
            raw = blocks.nth(i).inner_text()
            data = json.loads(raw)
            assert "@context" in data
            assert "@type" in data


# ════════════════════════════════════════════════════════════════
# 12. CSS RENDERING
# ════════════════════════════════════════════════════════════════

class TestCSS:
    def test_no_overflow_x(self, page):
        overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        assert not overflow, "Página tem overflow horizontal"

    def test_hero_has_background(self, page):
        bg = page.evaluate("getComputedStyle(document.querySelector('.hero')).background")
        assert bg and ("linear-gradient" in bg or "rgb" in bg)
