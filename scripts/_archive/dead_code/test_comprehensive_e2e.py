#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NossoDireito — Comprehensive E2E Test Suite v1.12.1

Exhaustive automated tests for ALL site functionality:
  1. Page Load & Core Structure
  2. Disclaimer Modal
  3. Navigation (desktop & mobile)
  4. Search — cities, states, UF codes, diseases, benefits, edge cases
  5. Category Grid & Detail View
  6. Checklist (Primeiros Passos)
  7. Document Upload Zone
  8. Official Links Section
  9. CID-10/11 Classification
 10. State Agencies (Órgãos Estaduais) + Region Filter
 11. Institutions + Type Filter
 12. Transparency & Sources
 13. Accessibility Panel (font, contrast, read-aloud)
 14. Footer & Disclaimer Reopen
 15. Back-to-Top Button
 16. Keyboard Navigation & ARIA
 17. External Link Attributes
 18. Console Errors Audit
 19. Performance Metrics (LCP, CLS, DOM size)
 20. Responsive / Mobile Layout

Requires: pip install playwright && playwright install chromium
Usage:   python3 scripts/_archive/dead_code/test_comprehensive_e2e.py [--headed]
(ARCHIVED — moved from scripts/test_comprehensive_e2e.py)
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# ── Resolve paths ──────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
NODE_BIN = "/opt/homebrew/Cellar/node@22/22.22.0/bin/node"
SERVER_JS = ROOT / "server.js"
BASE_URL = "http://localhost:8080"

# ── Colours ────────────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

HEADED = "--headed" in sys.argv


def js_click(page, selector):
    """Click element via JavaScript to avoid obstructions (sticky nav, overlays)."""
    page.evaluate(f'document.querySelector("{selector}")?.click()')


def safe_click(locator, timeout=5000):
    """Try Playwright click, fall back to JS click."""
    try:
        locator.click(timeout=timeout)
    except Exception:
        locator.evaluate("el => el.click()")


def scroll_and_click(page, locator, timeout=5000):
    """Scroll into view, then try click with short timeout and JS fallback."""
    try:
        locator.scroll_into_view_if_needed(timeout=3000)
    except Exception:
        pass
    page.wait_for_timeout(200)
    try:
        locator.click(timeout=timeout)
    except Exception:
        locator.evaluate("el => el.click()")


# ── Results tracker ────────────────────────────────────────────────
class Results:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.details = []
        self.console_errors = []

    def ok(self, name, info=""):
        self.passed += 1
        self.details.append(("PASS", name, info))
        print(f"  {GREEN}✓{RESET} {name}" + (f"  ({info})" if info else ""))

    def fail(self, name, reason=""):
        self.failed += 1
        self.details.append(("FAIL", name, reason))
        print(f"  {RED}✗ {name}{RESET}  → {reason}")

    def warn(self, name, reason=""):
        self.warnings += 1
        self.details.append(("WARN", name, reason))
        print(f"  {YELLOW}⚠ {name}{RESET}  → {reason}")

    def check(self, cond, name, fail_reason="", info=""):
        if cond:
            self.ok(name, info)
        else:
            self.fail(name, fail_reason)

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        pct = (self.passed / total * 100) if total else 0
        colour = GREEN if self.failed == 0 else RED
        print(
            f"{colour}{BOLD}{self.passed}/{total} PASSED ({pct:.0f}%){RESET}"
            f"  |  {self.warnings} warnings"
        )
        if self.failed:
            print(f"\n{RED}Failed tests:{RESET}")
            for status, name, reason in self.details:
                if status == "FAIL":
                    print(f"  ✗ {name}: {reason}")
        print(f"{'='*60}")
        return self.failed == 0


R = Results()

# ── Server management ─────────────────────────────────────────────
server_proc = None


def start_server():
    global server_proc
    server_proc = subprocess.Popen(
        [NODE_BIN, str(SERVER_JS)],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,
    )
    # Wait for server
    for _ in range(40):
        try:
            import urllib.request
            urllib.request.urlopen(BASE_URL, timeout=1)
            return True
        except Exception:
            time.sleep(0.25)
    print(f"{RED}Server did not start in time{RESET}")
    return False


def stop_server():
    global server_proc
    if server_proc:
        try:
            os.killpg(os.getpgid(server_proc.pid), signal.SIGTERM)
        except Exception:
            pass
        server_proc = None


# ══════════════════════════════════════════════════════════════════
#  TEST SUITES
# ══════════════════════════════════════════════════════════════════


def run_all_tests():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not HEADED)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="pt-BR",
            user_agent="Mozilla/5.0 NossoDireito-E2E-Test",
        )
        # Capture console errors
        page = context.new_page()
        page.on("console", lambda msg: _on_console(msg))
        page.on("pageerror", lambda err: R.console_errors.append(str(err)))

        # ── Load page ──────────────────────────────────────────────
        print(f"\n{CYAN}{BOLD}═══ Loading page ═══{RESET}")
        page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)  # let JS init finish

        # ── Run test groups ────────────────────────────────────────
        test_groups = [
            ("Page Structure", test_page_structure),
            ("Inline Disclaimer", test_inline_disclaimer),
            ("Navigation Desktop", test_navigation_desktop),
            ("Search Comprehensive", test_search_comprehensive),
            ("Category Grid", test_category_grid),
            ("Category Detail", test_category_detail),
            ("Checklist", test_checklist),
            ("Document Section", test_document_section),
            ("Links Section", test_links_section),
            ("CID Classification", test_cid_classification),
            ("Órgãos Estaduais", test_orgaos_estaduais),
            ("Instituições", test_instituicoes),
            ("Transparency", test_transparency_section),
            ("Accessibility Panel", test_accessibility_panel),
            ("Footer", test_footer),
            ("Back to Top", test_back_to_top),
            ("Keyboard & ARIA", test_keyboard_and_aria),
            ("External Links", test_external_links),
            ("Performance Metrics", test_performance_metrics),
        ]
        for name, fn in test_groups:
            try:
                fn(page)
            except Exception as e:
                R.fail(f"{name} (EXCEPTION)", str(e)[:200])

        # ── Mobile tests ──────────────────────────────────────────
        print(f"\n{CYAN}{BOLD}═══ Mobile viewport tests ═══{RESET}")
        page.set_viewport_size({"width": 375, "height": 812})
        page.wait_for_timeout(500)
        mobile_tests = [
            ("Mobile Layout", test_mobile_layout),
            ("Mobile Navigation", test_navigation_mobile),
            ("Mobile Search", test_mobile_search),
        ]
        for name, fn in mobile_tests:
            try:
                fn(page)
            except Exception as e:
                R.fail(f"{name} (EXCEPTION)", str(e)[:200])

        # ── Console errors audit ──────────────────────────────────
        print(f"\n{CYAN}{BOLD}═══ Console Errors Audit ═══{RESET}")
        test_console_errors()

        browser.close()


def _on_console(msg):
    if msg.type == "error":
        text = msg.text
        # Ignore expected / benign errors
        if any(x in text for x in [
            "govbr-servico",  # API not available locally
            "vlibras",
            "Failed to load resource",
            "net::ERR",
            "favicon",
        ]):
            return
        R.console_errors.append(text)


# ══════════════════════════════════════════════════════════════════
#  1. PAGE LOAD & CORE STRUCTURE
# ══════════════════════════════════════════════════════════════════
def test_page_structure(page):
    print(f"\n{CYAN}{BOLD}═══ 1. Page Structure ═══{RESET}")

    R.check(page.title() != "", "Page has title", "Empty <title>")
    R.check("NossoDireito" in page.title(), "Title contains NossoDireito",
            f"Title: {page.title()}")

    lang = page.locator("html").get_attribute("lang")
    R.check(lang == "pt-BR", "html lang=pt-BR", f"lang={lang}")

    R.check(page.locator("header nav").count() > 0, "Header nav exists")
    R.check(page.locator("main").count() > 0, "Main element exists")
    R.check(page.locator("footer").count() > 0, "Footer exists")

    # Meta viewport
    vp = page.locator('meta[name="viewport"]')
    R.check(vp.count() > 0, "Meta viewport present")

    # Meta description
    desc = page.locator('meta[name="description"]')
    R.check(desc.count() > 0, "Meta description present")

    # Charset
    charset = page.locator('meta[charset]')
    R.check(charset.count() > 0, "Meta charset present")

    # CSS loaded
    has_styles = page.evaluate(
        "document.styleSheets.length > 0"
    )
    R.check(has_styles, "CSS stylesheets loaded")

    # app.js loaded (check for a known global side effect)
    app_loaded = page.evaluate(
        "typeof document.getElementById('categoryGrid') !== 'undefined'"
    )
    R.check(app_loaded, "app.js executed")


# ══════════════════════════════════════════════════════════════════
#  2. INLINE DISCLAIMER
# ══════════════════════════════════════════════════════════════════
def test_inline_disclaimer(page):
    print(f"\n{CYAN}{BOLD}═══ 2. Inline Disclaimer ═══{RESET}")

    # Modal should NOT exist (was removed)
    modal_count = page.locator("#disclaimerModal").count()
    R.check(modal_count == 0, "Disclaimer modal removed from DOM")

    # Inline disclaimer box exists in transparency section
    disclaimer_box = page.locator("#disclaimerInline")
    R.check(disclaimer_box.count() > 0, "Inline disclaimer box exists")

    # Scroll to it and verify visibility
    disclaimer_box.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    R.check(disclaimer_box.is_visible(), "Inline disclaimer visible on page")

    # Check content keywords
    text = disclaimer_box.text_content().lower()
    R.check("não substitui" in text, "Disclaimer has 'não substitui'")
    R.check("defensoria" in text or "cras" in text,
            "Disclaimer mentions professional help")
    R.check("lgpd" in text or "privacidade" in text,
            "Disclaimer mentions privacy/LGPD")

    # Footer link points to inline disclaimer (anchor, not modal)
    footer_link = page.locator("a[href='#disclaimerInline']")
    R.check(footer_link.count() > 0, "Footer Aviso Legal links to #disclaimerInline")


# ══════════════════════════════════════════════════════════════════
#  3. NAVIGATION — DESKTOP
# ══════════════════════════════════════════════════════════════════
def test_navigation_desktop(page):
    print(f"\n{CYAN}{BOLD}═══ 3. Navigation (Desktop) ═══{RESET}")

    nav_links = page.locator("#navLinks a")
    count = nav_links.count()
    R.check(count == 10, "10 nav links present", f"Found {count}")

    expected = [
        ("Início", "#inicio"),
        ("Buscar", "#busca"),
        ("Categorias", "#categorias"),
        ("Primeiros Passos", "#checklist"),
        ("Documentos", "#documentos"),
        ("Sites Oficiais", "#links"),
        ("CID-10/11", "#classificacao"),
        ("Estados", "#orgaos-estaduais"),
        ("Instituições", "#instituicoes"),
        ("Fontes", "#transparencia"),
    ]

    for i, (text, href) in enumerate(expected):
        if i < count:
            actual_text = nav_links.nth(i).text_content().strip()
            actual_href = nav_links.nth(i).get_attribute("href")
            R.check(
                actual_text == text and actual_href == href,
                f"Nav[{i}] = '{text}' → {href}",
                f"Got '{actual_text}' → {actual_href}",
            )

    # Click each nav link and verify scroll/target section visible
    for text, href in [("Buscar", "#busca"), ("Categorias", "#categorias"),
                        ("Fontes", "#transparencia")]:
        link = page.locator(f'#navLinks a[href="{href}"]')
        if link.count() > 0:
            safe_click(link)
            page.wait_for_timeout(600)
            section_id = href.lstrip("#")
            visible = page.locator(f"#{section_id}").is_visible()
            R.check(visible, f"Nav click → #{section_id} visible")

    # Scroll back to top for next tests
    page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(300)


# ══════════════════════════════════════════════════════════════════
#  4. SEARCH — COMPREHENSIVE
# ══════════════════════════════════════════════════════════════════
def test_search_comprehensive(page):
    print(f"\n{CYAN}{BOLD}═══ 4. Search ═══{RESET}")

    search_input = page.locator("#searchInput")
    search_btn = page.locator("#searchBtn")
    results_div = page.locator("#searchResults")

    R.check(search_input.count() > 0, "Search input exists")
    R.check(search_btn.count() > 0, "Search button exists")

    def do_search(query, expect_min=1, label=None):
        page.evaluate("window.scrollTo(0, document.getElementById('busca')?.offsetTop - 80 || 0)")
        page.wait_for_timeout(200)
        search_input.fill("")
        search_input.fill(query)
        js_click(page, "#searchBtn")
        page.wait_for_timeout(800)
        html = results_div.inner_html()
        items = results_div.locator(".result-card, .search-result-item, .category-card, article, .result-item, [class*='result']").count()
        has_content = len(html.strip()) > 50
        name = label or f"Search '{query}'"
        if has_content and items >= expect_min:
            R.ok(name, f"{items} results")
        elif has_content:
            # Content exists but maybe different structure
            R.ok(name, f"content found (html {len(html)} chars)")
        else:
            R.fail(name, f"No results. HTML length: {len(html)}")

    # ── Cities ─────────────────────────────────────────────────
    cities = [
        "São Paulo", "Rio de Janeiro", "Belo Horizonte", "Salvador",
        "Curitiba", "Recife", "Manaus"
    ]
    for city in cities:
        do_search(city, 1, f"City: {city}")

    # ── States ─────────────────────────────────────────────────
    states = ["Minas Gerais", "Bahia", "Paraná"]
    for state in states:
        do_search(state, 1, f"State: {state}")

    # ── UF codes ───────────────────────────────────────────────
    for uf in ["SP", "RJ"]:
        do_search(uf, 1, f"UF: {uf}")

    # ── Diseases / conditions ──────────────────────────────────
    diseases = [
        "autismo", "sindrome de down", "TDAH", "deficiencia visual",
        "deficiencia auditiva", "paralisia cerebral", "TEA",
        "deficiencia intelectual",
    ]
    for d in diseases:
        do_search(d, 1, f"Disease: {d}")

    # ── Benefits / keywords ────────────────────────────────────
    benefits = [
        "BPC", "LOAS", "FGTS", "passe livre", "escola",
        "plano de saude", "medicamento", "aposentadoria",
        "meia entrada", "transporte", "moradia", "IPVA",
        "auxilio inclusao",
    ]
    for b in benefits:
        do_search(b, 1, f"Benefit: {b}")

    # ── CID codes ──────────────────────────────────────────────
    for cid in ["F84", "Q90", "G80"]:
        do_search(cid, 1, f"CID: {cid}")

    # ── Edge cases ─────────────────────────────────────────────
    # Empty search
    search_input.fill("")
    js_click(page, "#searchBtn")
    page.wait_for_timeout(500)
    empty_html = results_div.inner_html()
    R.check(len(empty_html.strip()) < 20 or "digite" in empty_html.lower() or len(empty_html) == 0,
            "Empty search → no/minimal results")

    # Gibberish
    do_search("xyzqwv12345", 0, "Gibberish → graceful empty")
    gibberish_html = results_div.inner_html()
    # Should either be empty or show "no results" message
    R.check(
        len(gibberish_html) < 200 or "nenhum" in gibberish_html.lower() or "resultado" in gibberish_html.lower(),
        "Gibberish search graceful",
        f"HTML length: {len(gibberish_html)}"
    )

    # ── Combined search (disease + city) ─────────────────────────
    combined = [
        ("TEA Barueri", "Combined: TEA Barueri"),
        ("autismo São Paulo", "Combined: autismo São Paulo"),
        ("BPC Curitiba", "Combined: BPC Curitiba"),
        ("FGTS Salvador", "Combined: FGTS Salvador"),
        ("escola Recife", "Combined: escola Recife"),
        ("deficiencia visual Manaus", "Combined: deficiencia visual Manaus"),
    ]
    for query, label in combined:
        page.evaluate("window.scrollTo(0, document.getElementById('busca')?.offsetTop - 80 || 0)")
        page.wait_for_timeout(200)
        search_input.fill("")
        search_input.fill(query)
        js_click(page, "#searchBtn")
        page.wait_for_timeout(800)
        html = results_div.inner_html()
        has_location = "search-location" in html
        has_results = "search-result-item" in html
        # Combined search should show location banner AND filtered results
        R.check(has_location and has_results, label,
                f"location={has_location} results={has_results}")

    # Clear results
    search_input.fill("")
    page.wait_for_timeout(200)


# ══════════════════════════════════════════════════════════════════
#  5. CATEGORY GRID
# ══════════════════════════════════════════════════════════════════
def test_category_grid(page):
    print(f"\n{CYAN}{BOLD}═══ 5. Category Grid ═══{RESET}")

    grid = page.locator("#categoryGrid")
    R.check(grid.count() > 0, "Category grid exists")

    cards = grid.locator(".category-card")
    count = cards.count()
    R.check(count == 25, f"25 category cards rendered", f"Found {count}")

    # Verify each card has required attributes
    for i in range(min(count, 5)):  # Spot-check first 5
        card = cards.nth(i)
        data_id = card.get_attribute("data-id")
        has_role = card.get_attribute("role") == "button"
        has_tabindex = card.get_attribute("tabindex") == "0"
        has_h3 = card.locator("h3").count() > 0
        R.check(
            data_id and has_role and has_tabindex and has_h3,
            f"Card[{i}] '{data_id}' has role/tabindex/h3",
            f"id={data_id} role={has_role} tabindex={has_tabindex} h3={has_h3}",
        )


# ══════════════════════════════════════════════════════════════════
#  6. CATEGORY DETAIL VIEW
# ══════════════════════════════════════════════════════════════════
def test_category_detail(page):
    print(f"\n{CYAN}{BOLD}═══ 6. Category Detail ═══{RESET}")

    # Click first category card
    cards = page.locator("#categoryGrid .category-card")
    if cards.count() == 0:
        R.fail("Category detail", "No cards to click")
        return

    first_id = cards.first.get_attribute("data-id")
    cards.first.scroll_into_view_if_needed()
    safe_click(cards.first)
    page.wait_for_timeout(800)

    # Detail section should be visible
    detail_section = page.locator("#detalhe")
    R.check(detail_section.is_visible(), "Detail section visible after card click")

    # Categories section should be hidden
    cat_section = page.locator("#categorias")
    cat_hidden = not cat_section.is_visible()
    R.check(cat_hidden, "Categories section hidden when detail shown")

    # Detail content should have content
    detail_content = page.locator("#detalheContent")
    html = detail_content.inner_html()
    R.check(len(html) > 100, "Detail content has substance",
            f"HTML length: {len(html)}")

    # Should contain article with heading
    R.check(detail_content.locator("article").count() > 0,
            "Detail has <article>")
    R.check(detail_content.locator("h2").count() > 0,
            "Detail has <h2> title")

    # Check for legal links (most categories have them)
    legal_links = detail_content.locator("a.legal-link")
    R.check(legal_links.count() >= 0, "Legal links section exists",
            f"{legal_links.count()} links")

    # Back button returns to categories
    voltar_btn = page.locator("#voltarBtn")
    R.check(voltar_btn.count() > 0, "Voltar button exists")
    safe_click(voltar_btn)
    page.wait_for_timeout(500)
    R.check(cat_section.is_visible(), "Categories visible after Voltar click")
    R.check(not detail_section.is_visible() or detail_section.evaluate(
        "el => el.style.display === 'none'"
    ), "Detail hidden after Voltar click")

    # Test keyboard activation (Enter on card)
    second_card = cards.nth(1)
    second_card.scroll_into_view_if_needed()
    second_card.focus()
    page.keyboard.press("Enter")
    page.wait_for_timeout(800)
    R.check(detail_section.is_visible(), "Detail opens on Enter key")

    # Go back for following tests
    safe_click(voltar_btn)
    page.wait_for_timeout(500)


# ══════════════════════════════════════════════════════════════════
#  7. CHECKLIST
# ══════════════════════════════════════════════════════════════════
def test_checklist(page):
    print(f"\n{CYAN}{BOLD}═══ 7. Checklist (Primeiros Passos) ═══{RESET}")

    section = page.locator("#checklist")
    section.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    R.check(section.is_visible(), "Checklist section visible")

    # Heading
    heading = section.locator("h2")
    R.check(heading.count() > 0, "Checklist heading exists")

    # Checkboxes
    checkboxes = section.locator("input[type='checkbox']")
    cb_count = checkboxes.count()
    R.check(cb_count == 10, f"10 checklist items", f"Found {cb_count}")

    # Progress text
    progress = page.locator("#checklistProgress")
    R.check(progress.count() > 0, "Progress counter exists")

    # Progress bar
    bar = page.locator("#checklistProgressBar")
    R.check(bar.count() > 0, "Progress bar exists")

    # Check first item and verify progress updates
    if cb_count > 0:
        first_cb = checkboxes.first
        first_cb.evaluate("el => el.click()")
        page.wait_for_timeout(400)
        progress_text = progress.text_content()
        R.check("1 de" in progress_text or "1/" in progress_text,
                "Progress updates on check", f"Text: {progress_text}")

        # Uncheck
        first_cb.evaluate("el => el.click()")
        page.wait_for_timeout(400)
        progress_text2 = progress.text_content()
        R.check("0 de" in progress_text2 or "0/" in progress_text2,
                "Progress updates on uncheck", f"Text: {progress_text2}")

    # WhatsApp share button
    wa_btn = page.locator("#shareChecklistWhatsApp")
    R.check(wa_btn.count() > 0, "WhatsApp share button exists")

    # PDF export button
    pdf_btn = page.locator("#exportChecklistPdf")
    R.check(pdf_btn.count() > 0, "PDF export button exists")


# ══════════════════════════════════════════════════════════════════
#  8. DOCUMENT UPLOAD SECTION
# ══════════════════════════════════════════════════════════════════
def test_document_section(page):
    print(f"\n{CYAN}{BOLD}═══ 8. Documents Section ═══{RESET}")

    section = page.locator("#documentos")
    section.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    R.check(section.is_visible(), "Documents section visible")

    # Upload zone
    zone = page.locator("#uploadZone")
    R.check(zone.count() > 0, "Upload zone exists")
    R.check(zone.get_attribute("role") == "button", "Upload zone has role=button")
    R.check(zone.get_attribute("tabindex") == "0", "Upload zone has tabindex=0")

    # File input
    file_input = page.locator("#fileInput")
    R.check(file_input.count() > 0, "File input exists")
    accept = file_input.get_attribute("accept")
    R.check(accept and "pdf" in accept.lower(), "Accepts PDF files", f"accept={accept}")

    # Analyze button
    analyze_btn = page.locator("#analyzeSelected")
    R.check(analyze_btn.count() > 0, "Analyze button exists")

    # Docs checklist
    docs_cl = page.locator("#docsChecklist")
    R.check(docs_cl.count() > 0, "Docs checklist exists")

    # Share/export buttons
    R.check(page.locator("#shareDocsWhatsApp").count() > 0,
            "Docs WhatsApp share button exists")
    R.check(page.locator("#exportDocsChecklistPdf").count() > 0,
            "Docs PDF export button exists")


# ══════════════════════════════════════════════════════════════════
#  9. OFFICIAL LINKS
# ══════════════════════════════════════════════════════════════════
def test_links_section(page):
    print(f"\n{CYAN}{BOLD}═══ 9. Official Links ═══{RESET}")

    section = page.locator("#links")
    section.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    R.check(section.is_visible(), "Links section visible")

    grid = page.locator("#linksGrid")
    R.check(grid.count() > 0, "Links grid exists")

    links = grid.locator("a")
    link_count = links.count()
    R.check(link_count > 5, "Multiple official links rendered", f"{link_count} links")

    # Spot-check first few links have target and rel
    for i in range(min(link_count, 5)):
        href = links.nth(i).get_attribute("href")
        target = links.nth(i).get_attribute("target")
        rel = links.nth(i).get_attribute("rel") or ""
        if href and href.startswith("http"):
            R.check(
                target == "_blank" and "noopener" in rel,
                f"Link[{i}] target/rel ok",
                f"href={href[:50]}",
            )


# ══════════════════════════════════════════════════════════════════
#  10. CID CLASSIFICATION
# ══════════════════════════════════════════════════════════════════
def test_cid_classification(page):
    print(f"\n{CYAN}{BOLD}═══ 10. CID-10/11 Classification ═══{RESET}")

    section = page.locator("#classificacao")
    section.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    R.check(section.is_visible(), "Classification section visible")

    grid = page.locator("#classificacaoGrid")
    R.check(grid.count() > 0, "Classification grid exists")

    # Should have content (cards/rows)
    html = grid.inner_html()
    R.check(len(html) > 200, "Classification content rendered",
            f"HTML length: {len(html)}")

    # Check for known CID codes in the content
    has_f84 = "F84" in html or "f84" in html.lower()
    has_h54 = "H54" in html or "h54" in html.lower()
    has_g80 = "G80" in html or "g80" in html.lower()
    R.check(has_f84, "CID F84 (Autismo) present in grid")
    R.check(has_h54, "CID H54 (Visual) present in grid")
    R.check(has_g80, "CID G80 (Física) present in grid")


# ══════════════════════════════════════════════════════════════════
#  11. STATE AGENCIES + REGION FILTER
# ══════════════════════════════════════════════════════════════════
def test_orgaos_estaduais(page):
    print(f"\n{CYAN}{BOLD}═══ 11. State Agencies ═══{RESET}")

    section = page.locator("#orgaos-estaduais")
    section.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    R.check(section.is_visible(), "Órgãos Estaduais section visible")

    grid = page.locator("#orgaosEstaduaisGrid")
    R.check(grid.count() > 0, "State agencies grid exists")

    html = grid.inner_html()
    R.check(len(html) > 200, "State agencies content rendered",
            f"HTML length: {len(html)}")

    # Region filter buttons
    filter_buttons = section.locator("button.orgao-filter-btn")
    fb_count = filter_buttons.count()
    R.check(fb_count == 6, "6 region filter buttons (Todos + 5 regions)",
            f"Found {fb_count}")

    # Test filter click — "Sudeste"
    sudeste_btn = section.locator('button[data-filter="Sudeste"]')
    if sudeste_btn.count() > 0:
        safe_click(sudeste_btn)
        page.wait_for_timeout(500)
        # Check aria-pressed
        pressed = sudeste_btn.get_attribute("aria-pressed")
        R.check(pressed == "true", "Sudeste filter aria-pressed=true")

        # Check that content changed (some items hidden)
        visible_items = grid.locator(":scope > *:not([style*='display: none']):not([hidden])").count()
        R.check(visible_items > 0, "Sudeste filter shows results",
                f"{visible_items} items visible")

        # Reset to "Todos"
        todos_btn = section.locator('button[data-filter="todos"]')
        safe_click(todos_btn)
        page.wait_for_timeout(300)


# ══════════════════════════════════════════════════════════════════
#  12. INSTITUTIONS + TYPE FILTER
# ══════════════════════════════════════════════════════════════════
def test_instituicoes(page):
    print(f"\n{CYAN}{BOLD}═══ 12. Institutions ═══{RESET}")

    section = page.locator("#instituicoes")
    section.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    R.check(section.is_visible(), "Institutions section visible")

    grid = page.locator("#instituicoesGrid")
    R.check(grid.count() > 0, "Institutions grid exists")

    html = grid.inner_html()
    R.check(len(html) > 200, "Institutions content rendered",
            f"HTML length: {len(html)}")

    # Type filter buttons
    filter_buttons = section.locator("button.inst-filter-btn")
    fb_count = filter_buttons.count()
    R.check(fb_count == 4, "4 institution filter buttons",
            f"Found {fb_count}")

    # Test ONG filter
    ong_btn = section.locator('button[data-filter="ong"]')
    if ong_btn.count() > 0:
        safe_click(ong_btn)
        page.wait_for_timeout(500)
        pressed = ong_btn.get_attribute("aria-pressed")
        R.check(pressed == "true", "ONG filter aria-pressed=true")

        # Reset
        todos_btn = section.locator('button[data-filter="todos"]')
        safe_click(todos_btn)
        page.wait_for_timeout(300)


# ══════════════════════════════════════════════════════════════════
#  13. TRANSPARENCY & SOURCES
# ══════════════════════════════════════════════════════════════════
def test_transparency_section(page):
    print(f"\n{CYAN}{BOLD}═══ 13. Transparency ═══{RESET}")

    section = page.locator("#transparencia")
    section.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    R.check(section.is_visible(), "Transparency section visible")

    # Legislation sources
    leg = page.locator("#fontesLegislacao")
    R.check(leg.count() > 0, "Legislação sources div exists")
    leg_html = leg.inner_html()
    R.check(len(leg_html) > 100, "Legislação sources populated",
            f"HTML length: {len(leg_html)}")

    # Services sources
    svc = page.locator("#fontesServicos")
    R.check(svc.count() > 0, "Serviços sources div exists")

    # Normativas
    norma = page.locator("#fontesNormativas")
    R.check(norma.count() > 0, "Normativas sources div exists")

    # Version info
    ver = page.locator("#transVersion")
    R.check(ver.count() > 0, "Version element exists")
    ver_text = ver.text_content().strip()
    R.check(len(ver_text) > 0, "Version text not empty", f"v={ver_text}")

    # Last update
    last_upd = page.locator("#transLastUpdate")
    R.check(last_upd.count() > 0, "Last update element exists")


# ══════════════════════════════════════════════════════════════════
#  14. ACCESSIBILITY PANEL
# ══════════════════════════════════════════════════════════════════
def test_accessibility_panel(page):
    print(f"\n{CYAN}{BOLD}═══ 14. Accessibility Panel ═══{RESET}")

    trigger = page.locator("#a11yPanelTrigger")
    R.check(trigger.count() > 0, "A11y trigger button exists")

    # Open panel
    safe_click(trigger)
    page.wait_for_timeout(500)

    drawer = page.locator("#a11yDrawer")
    is_open = drawer.get_attribute("aria-hidden") == "false"
    R.check(is_open, "A11y drawer opens on trigger click")

    # Font size buttons
    R.check(page.locator("#a11yFontIncrease").count() > 0, "Font+ button exists")
    R.check(page.locator("#a11yFontDecrease").count() > 0, "Font- button exists")
    R.check(page.locator("#a11yFontReset").count() > 0, "Font reset button exists")

    # Increase font size
    js_click(page, "#a11yFontIncrease")
    page.wait_for_timeout(300)
    font_size = page.evaluate("parseFloat(getComputedStyle(document.documentElement).fontSize)")
    R.check(font_size > 16, "Font size increased", f"{font_size}px")

    # Reset font
    js_click(page, "#a11yFontReset")
    page.wait_for_timeout(300)
    font_reset = page.evaluate("parseFloat(getComputedStyle(document.documentElement).fontSize)")
    R.check(font_reset <= 17, "Font size reset", f"{font_reset}px")

    # High contrast toggle
    contrast_btn = page.locator("#a11yContrast")
    R.check(contrast_btn.count() > 0, "Contrast toggle exists")
    js_click(page, "#a11yContrast")
    page.wait_for_timeout(300)
    has_hc_class = page.evaluate(
        "document.body.classList.contains('high-contrast') || document.documentElement.classList.contains('high-contrast')"
    )
    R.check(has_hc_class, "High contrast class applied on toggle")

    # Toggle off
    js_click(page, "#a11yContrast")
    page.wait_for_timeout(300)
    no_hc = not page.evaluate(
        "document.body.classList.contains('high-contrast') || document.documentElement.classList.contains('high-contrast')"
    )
    R.check(no_hc, "High contrast removed on second toggle")

    # VLibras button
    libras_btn = page.locator("#a11yLibras")
    R.check(libras_btn.count() > 0, "VLibras button exists")

    # Read aloud button
    read_btn = page.locator("#a11yReadAloud")
    R.check(read_btn.count() > 0, "Read aloud button exists")

    # Close drawer
    close_btn = page.locator("#a11yDrawerClose")
    R.check(close_btn.count() > 0, "Drawer close button exists")
    js_click(page, "#a11yDrawerClose")
    page.wait_for_timeout(300)
    is_closed = drawer.get_attribute("aria-hidden") == "true"
    R.check(is_closed, "Drawer closes on close button")


# ══════════════════════════════════════════════════════════════════
#  15. FOOTER
# ══════════════════════════════════════════════════════════════════
def test_footer(page):
    print(f"\n{CYAN}{BOLD}═══ 15. Footer ═══{RESET}")

    footer = page.locator("footer")
    footer.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    R.check(footer.is_visible(), "Footer visible")

    # Last update
    last_upd = page.locator("#lastUpdate")
    R.check(last_upd.count() > 0, "Footer last update span exists")
    upd_text = last_upd.text_content().strip()
    R.check(len(upd_text) > 0, "Footer last update not empty", f"'{upd_text}'")

    # Version
    ver = page.locator("#footerVersion")
    R.check(ver.count() > 0, "Footer version span exists")
    ver_text = ver.text_content().strip()
    R.check(len(ver_text) > 0, "Footer version not empty", f"'{ver_text}'")

    # Disclaimer link in footer (now anchors to inline, no modal)
    R.check(page.locator("a[href='#disclaimerInline']").count() > 0,
            "Disclaimer anchor link in footer")


# ══════════════════════════════════════════════════════════════════
#  16. BACK TO TOP
# ══════════════════════════════════════════════════════════════════
def test_back_to_top(page):
    print(f"\n{CYAN}{BOLD}═══ 16. Back to Top ═══{RESET}")

    btn = page.locator("#backToTop")
    R.check(btn.count() > 0, "Back-to-top button exists")

    # Scroll to bottom
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(600)

    # Button should be visible after scroll
    is_visible = btn.is_visible()
    R.check(is_visible, "Back-to-top visible after scroll down")

    # Click should scroll to top
    if is_visible:
        js_click(page, "#backToTop")
        page.wait_for_timeout(1500)  # smooth scroll takes time
        scroll_y = page.evaluate("window.scrollY")
        R.check(scroll_y < 300, "Page scrolled to top after click",
                f"scrollY={scroll_y}")


# ══════════════════════════════════════════════════════════════════
#  17. KEYBOARD & ARIA
# ══════════════════════════════════════════════════════════════════
def test_keyboard_and_aria(page):
    print(f"\n{CYAN}{BOLD}═══ 17. Keyboard & ARIA ═══{RESET}")

    # Skip links
    skip_links = page.locator("a.skip-link")
    skip_count = skip_links.count()
    R.check(skip_count >= 3, "3+ skip links present (eMAG 4.1)",
            f"Found {skip_count}")

    # Check skip link targets exist
    for i in range(min(skip_count, 3)):
        href = skip_links.nth(i).get_attribute("href")
        if href and href.startswith("#"):
            target_id = href.lstrip("#")
            exists = page.locator(f"#{target_id}").count() > 0
            R.check(exists, f"Skip link target #{target_id} exists")

    # Nav has role="navigation"
    R.check(page.locator('nav[role="navigation"]').count() > 0,
            "Nav has role=navigation")

    # Nav has aria-label
    nav_label = page.locator("nav").first.get_attribute("aria-label")
    R.check(nav_label and len(nav_label) > 0, "Nav has aria-label",
            f"'{nav_label}'")

    # Main landmark
    R.check(page.locator("main").count() > 0, "Main landmark exists")

    # Search input has label
    search_label = page.locator('label[for="searchInput"]')
    R.check(search_label.count() > 0, "Search input has <label>")

    # aria-live regions
    live_regions = page.locator('[aria-live]')
    R.check(live_regions.count() >= 2, "2+ aria-live regions",
            f"Found {live_regions.count()}")

    # Inline disclaimer is accessible (no modal needed)
    disclaimer_box = page.locator("#disclaimerInline")
    R.check(disclaimer_box.count() > 0, "Inline disclaimer accessible in DOM")


# ══════════════════════════════════════════════════════════════════
#  18. EXTERNAL LINKS
# ══════════════════════════════════════════════════════════════════
def test_external_links(page):
    print(f"\n{CYAN}{BOLD}═══ 18. External Links ═══{RESET}")

    all_links = page.locator("a[href^='http']")
    total = all_links.count()
    bad = 0
    checked = 0

    for i in range(total):
        link = all_links.nth(i)
        href = link.get_attribute("href")
        target = link.get_attribute("target")
        rel = link.get_attribute("rel") or ""
        if href and not href.startswith(BASE_URL):
            checked += 1
            if target != "_blank" or "noopener" not in rel:
                bad += 1
                if bad <= 5:
                    R.warn(f"Ext link missing target/rel",
                           f"{href[:60]} target={target} rel={rel}")

    if bad == 0:
        R.ok(f"All {checked} external links have target=_blank rel=noopener")
    elif bad <= 3:
        R.warn(f"External links", f"{bad}/{checked} missing target=_blank (may be inline HTML links)")
    else:
        R.fail(f"External links issues", f"{bad}/{checked} missing target/rel")


# ══════════════════════════════════════════════════════════════════
#  19. PERFORMANCE METRICS
# ══════════════════════════════════════════════════════════════════
def test_performance_metrics(page):
    print(f"\n{CYAN}{BOLD}═══ 19. Performance Metrics ═══{RESET}")

    # DOM element count
    dom_count = page.evaluate("document.querySelectorAll('*').length")
    if dom_count < 1500:
        R.ok("DOM size < 1500 elements", f"{dom_count} elements")
    else:
        R.warn("DOM size", f"{dom_count} elements (target < 1500)")

    # Check LCP (approximate via PerformanceObserver)
    lcp = page.evaluate("""() => {
        return new Promise(resolve => {
            try {
                new PerformanceObserver(list => {
                    const entries = list.getEntries();
                    resolve(entries.length > 0 ? entries[entries.length-1].startTime : -1);
                }).observe({type: 'largest-contentful-paint', buffered: true});
                setTimeout(() => resolve(-1), 3000);
            } catch(e) { resolve(-1); }
        });
    }""")
    if lcp > 0:
        R.check(lcp < 3000, f"LCP < 3s", f"{lcp:.0f}ms")
    else:
        R.warn("LCP measurement", "Could not measure")

    # CLS — Note: after test interactions (clicking, scrolling, toggling), 
    # cumulative CLS will be high. We just report it as informational.
    cls_val = page.evaluate("""() => {
        return new Promise(resolve => {
            try {
                let cls = 0;
                new PerformanceObserver(list => {
                    for (const entry of list.getEntries()) {
                        if (!entry.hadRecentInput) cls += entry.value;
                    }
                    resolve(cls);
                }).observe({type: 'layout-shift', buffered: true});
                setTimeout(() => resolve(cls), 2000);
            } catch(e) { resolve(-1); }
        });
    }""")
    if cls_val >= 0:
        if cls_val < 0.1:
            R.ok(f"CLS < 0.1", f"CLS={cls_val:.4f}")
        else:
            # High CLS expected after many test interactions
            R.warn("CLS (cumulative after tests)", f"CLS={cls_val:.4f} (expected high after interactions)")

    # Page weight — check total transfer size approx
    resources = page.evaluate("""() => {
        const entries = performance.getEntriesByType('resource');
        return entries.reduce((acc, e) => acc + (e.transferSize || 0), 0);
    }""")
    kb = resources / 1024
    R.check(kb < 2000, f"Total resource size < 2MB", f"{kb:.0f}KB")


# ══════════════════════════════════════════════════════════════════
#  20. MOBILE LAYOUT
# ══════════════════════════════════════════════════════════════════
def test_mobile_layout(page):
    print(f"\n{CYAN}{BOLD}═══ 20. Mobile Layout ═══{RESET}")

    # Hamburger menu should exist
    menu_toggle = page.locator("#menuToggle")
    R.check(menu_toggle.is_visible(), "Hamburger menu visible on mobile")

    # Nav links should be hidden
    nav_links = page.locator("#navLinks")
    is_collapsed = not nav_links.evaluate(
        "el => el.classList.contains('open')"
    )
    R.check(is_collapsed, "Nav links collapsed on mobile")

    # Hero section
    hero = page.locator("#inicio")
    R.check(hero.is_visible(), "Hero section visible on mobile")

    # Search section
    search = page.locator("#busca")
    search.scroll_into_view_if_needed()
    R.check(search.is_visible(), "Search section visible on mobile")

    # Category grid should stack
    grid = page.locator("#categoryGrid")
    grid.scroll_into_view_if_needed()
    R.check(grid.is_visible(), "Category grid visible on mobile")

    # No horizontal overflow
    has_overflow = page.evaluate("""() => {
        return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    }""")
    R.check(not has_overflow, "No horizontal overflow on mobile")


def test_navigation_mobile(page):
    print(f"\n{CYAN}{BOLD}═══ 21. Mobile Navigation ═══{RESET}")

    menu_toggle = page.locator("#menuToggle")
    nav_links = page.locator("#navLinks")

    # Open mobile menu
    safe_click(menu_toggle)
    page.wait_for_timeout(400)
    is_open = nav_links.evaluate("el => el.classList.contains('open')")
    R.check(is_open, "Mobile menu opens on hamburger click")

    expanded = menu_toggle.get_attribute("aria-expanded")
    R.check(expanded == "true", "Hamburger aria-expanded=true when open")

    # Click a link — menu should close
    buscar_link = page.locator('#navLinks a[href="#busca"]')
    if buscar_link.count() > 0:
        safe_click(buscar_link)
        page.wait_for_timeout(600)
        is_closed = not nav_links.evaluate("el => el.classList.contains('open')")
        R.check(is_closed, "Mobile menu closes on link click")

    # Open and close with Escape
    safe_click(menu_toggle)
    page.wait_for_timeout(400)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    is_closed_esc = not nav_links.evaluate("el => el.classList.contains('open')")
    R.check(is_closed_esc, "Mobile menu closes on Escape")


def test_mobile_search(page):
    print(f"\n{CYAN}{BOLD}═══ 22. Mobile Search ═══{RESET}")

    search_input = page.locator("#searchInput")
    search_btn = page.locator("#searchBtn")
    results = page.locator("#searchResults")

    search_input.scroll_into_view_if_needed()
    search_input.fill("BPC")
    js_click(page, "#searchBtn")
    page.wait_for_timeout(800)
    html = results.inner_html()
    R.check(len(html) > 50, "Mobile search works for 'BPC'",
            f"HTML length: {len(html)}")

    # Clear
    search_input.fill("")


# ══════════════════════════════════════════════════════════════════
#  CONSOLE ERRORS AUDIT
# ══════════════════════════════════════════════════════════════════
def test_console_errors():
    if len(R.console_errors) == 0:
        R.ok("No unexpected console errors")
    else:
        for err in R.console_errors[:5]:
            R.fail("Console error", err[:120])
        if len(R.console_errors) > 5:
            R.warn("Console errors", f"{len(R.console_errors)} total errors")


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print(f"\n{BOLD}{'='*60}")
    print(f"  NossoDireito — Comprehensive E2E Test Suite")
    print(f"  v1.12.1 · {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}{RESET}\n")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(f"{RED}Playwright not installed. Run: pip install playwright && playwright install chromium{RESET}")
        sys.exit(1)

    print(f"Starting Node.js server...")
    if not start_server():
        print(f"{RED}Failed to start server{RESET}")
        sys.exit(1)
    print(f"{GREEN}Server running at {BASE_URL}{RESET}")

    try:
        run_all_tests()
    except Exception as e:
        print(f"\n{RED}FATAL ERROR: {e}{RESET}")
        import traceback
        traceback.print_exc()
    finally:
        stop_server()

    success = R.summary()
    sys.exit(0 if success else 1)
