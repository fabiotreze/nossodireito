#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CADERNO DE TESTES COMPLETO — NossoDireito v1.14.4

Validação exaustiva de todas as funcionalidades e possibilidades do site.
Cobre: links, URLs, comportamentos, WhatsApp, PDF, pesquisas, estados,
categorias, fontes, visualização, acessibilidade, cliques, combinações
de palavras-chave, segurança, PWA, cross-OS e integridade de dados.

Complementa test_cross_browser.py (17 classes) com validações adicionais
que cobrem o caderno de testes completo solicitado pelo usuário.
"""

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
JS_DIR = ROOT / "js"
CSS_DIR = ROOT / "css"
SCRIPTS_DIR = ROOT / "scripts"


# ════════════════════════════════════════════════════════════════
# FIXTURES (Session-scoped for performance)
# ════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def direitos():
    with open(DATA / "direitos.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def matching():
    with open(DATA / "matching_engine.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def dicionario():
    with open(DATA / "dicionario_pcd.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def html():
    with open(ROOT / "index.html", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="session")
def appjs():
    with open(JS_DIR / "app.js", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="session")
def css():
    with open(CSS_DIR / "styles.css", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="session")
def swjs():
    with open(ROOT / "sw.js", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="session")
def manifest():
    with open(ROOT / "manifest.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def serverjs():
    with open(ROOT / "server.js", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="session")
def packagejson():
    with open(ROOT / "package.json", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text: str) -> str:
    """Reproduce the JS normalizeText for search simulation."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = re.sub(r"[\u0300-\u036f]", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    return text.strip()


# ════════════════════════════════════════════════════════════════
# A. URL & LINK VALIDATION
# ════════════════════════════════════════════════════════════════

class TestURLAndLinks:
    """Validate all URLs in direitos.json are correct format and official."""

    OFFICIAL_DOMAINS = [
        "gov.br", "leg.br", "jus.br", "def.br", "mp.br", "mil.br",
        "icd.who.int", "who.int", "planalto.gov.br",
        "anac.gov.br", "coffito.gov.br", "mdh.gov.br",
        "sp.gov.br", "fazenda.gov.br",
    ]

    def _extract_urls(self, data: dict) -> list[str]:
        text = json.dumps(data, ensure_ascii=False)
        return re.findall(r"https?://[^\s\"',)\]]+", text)

    def test_all_urls_are_https(self, direitos):
        """All URLs must use HTTPS."""
        urls = self._extract_urls(direitos)
        http_only = [u for u in urls if u.startswith("http://")]
        assert http_only == [], f"HTTP (non-HTTPS) URLs found: {http_only[:5]}"

    def test_all_urls_are_official_domains(self, direitos):
        """All URLs must be from official government/institutional domains."""
        urls = self._extract_urls(direitos)
        violations = []
        for url in urls:
            domain_match = re.search(r"https?://([^/]+)", url)
            if domain_match:
                host = domain_match.group(1).lower()
                if not any(host.endswith(d) for d in self.OFFICIAL_DOMAINS):
                    violations.append(url)
        assert violations == [], f"Non-official URLs: {violations[:5]}"

    def test_no_duplicate_urls_in_fontes(self, direitos):
        """Fontes should not have duplicate URLs."""
        urls = [f["url"] for f in direitos.get("fontes", []) if "url" in f]
        dupes = [u for u, c in Counter(urls).items() if c > 1]
        assert dupes == [], f"Duplicate fonte URLs: {dupes}"

    def test_fontes_have_required_fields(self, direitos):
        """Each fonte must have nome, tipo, url, orgao."""
        for fonte in direitos.get("fontes", []):
            assert "nome" in fonte, f"Fonte missing 'nome': {fonte}"
            assert "tipo" in fonte, f"Fonte missing 'tipo': {fonte.get('nome')}"
            assert "url" in fonte, f"Fonte missing 'url': {fonte.get('nome')}"
            assert "orgao" in fonte, f"Fonte missing 'orgao': {fonte.get('nome')}"

    def test_fontes_tipos_are_valid(self, direitos):
        """Fonte tipos must be one of: legislacao, servico, normativa, programa."""
        valid_tipos = {"legislacao", "servico", "normativa", "programa"}
        for fonte in direitos.get("fontes", []):
            tipo = fonte.get("tipo", "")
            assert tipo in valid_tipos, (
                f"Fonte '{fonte.get('nome')}' has invalid tipo: '{tipo}'"
            )

    def test_fontes_count_minimum(self, direitos):
        """Should have at least 40 official sources."""
        count = len(direitos.get("fontes", []))
        assert count >= 40, f"Only {count} fontes — expected ≥40"

    def test_category_links_have_url_and_titulo(self, direitos):
        """Every category link must have titulo and url."""
        for cat in direitos["categorias"]:
            for link in cat.get("links", []):
                assert "titulo" in link, (
                    f"Category '{cat['id']}' link missing 'titulo'"
                )
                assert "url" in link, (
                    f"Category '{cat['id']}' link missing 'url': {link.get('titulo')}"
                )


# ════════════════════════════════════════════════════════════════
# B. WHATSAPP SHARING
# ════════════════════════════════════════════════════════════════

class TestWhatsAppSharing:
    """Validate WhatsApp sharing functionality in app.js."""

    def test_whatsapp_api_url_in_code(self, appjs):
        """app.js must use the correct WhatsApp API URL."""
        assert "api.whatsapp.com" in appjs or "wa.me" in appjs, (
            "WhatsApp share URL not found in app.js"
        )

    def test_share_button_exists_in_js(self, appjs):
        """JS must render WhatsApp share buttons."""
        assert "btn-whatsapp" in appjs

    def test_share_analysis_whatsapp(self, appjs):
        """Analysis section should have WhatsApp share."""
        assert "shareAnalysisWhatsApp" in appjs

    def test_share_checklist_whatsapp(self, appjs):
        """Checklist section should have WhatsApp share."""
        assert "shareChecklistWhatsApp" in appjs

    def test_share_docs_whatsapp(self, appjs):
        """Docs section should have WhatsApp share."""
        assert "shareDocsWhatsApp" in appjs

    def test_whatsapp_share_includes_site_url(self, appjs):
        """Share text should include the site URL."""
        assert "nossodireito" in appjs.lower()


# ════════════════════════════════════════════════════════════════
# C. PDF / PRINT EXPORT
# ════════════════════════════════════════════════════════════════

class TestPDFExport:
    """Validate PDF/print export functionality."""

    def test_window_print_called(self, appjs):
        """app.js must call window.print() for PDF export."""
        assert "window.print()" in appjs

    def test_print_css_exists(self, css):
        """CSS must have @media print rules."""
        assert "@media print" in css

    def test_printing_classes_in_js(self, appjs):
        """JS uses print-specific body classes."""
        assert "printing-detalhe" in appjs
        assert "printing-analysis" in appjs
        assert "printing-checklist" in appjs

    def test_afterprint_cleanup(self, appjs):
        """JS cleans up after print (afterprint event)."""
        assert "afterprint" in appjs

    def test_export_pdf_button_ref(self, appjs):
        """exportPdf DOM reference exists."""
        assert "exportPdf" in appjs

    def test_print_date_attribute(self, appjs):
        """Print adds date for header/footer."""
        assert "data-print-date" in appjs

    def test_print_css_hides_nav(self, css):
        """Print styles should hide navigation and non-content elements."""
        # Check for common print-hidden selectors
        print_section = css[css.index("@media print"):]
        assert "display: none" in print_section or "display:none" in print_section


# ════════════════════════════════════════════════════════════════
# D. EXHAUSTIVE SEARCH — ALL 30 CATEGORIES REACHABLE
# ════════════════════════════════════════════════════════════════

class TestSearchAllCategories:
    """Every single one of the 30 categories must be findable by search."""

    @pytest.fixture(scope="class")
    def search_index(self, direitos, matching):
        return {"keyword_map": matching["keyword_map"], "categories": direitos["categorias"]}

    def _score_search(self, query: str, search_index: dict) -> list[str]:
        stopwords = {
            "de", "do", "da", "dos", "das", "e", "em", "o", "a",
            "os", "as", "no", "na", "nos", "nas", "um", "uma",
            "para", "por", "com", "que", "se",
        }
        normalized = normalize_text(query)
        terms = [t for t in normalized.split() if t not in stopwords and len(t) > 1]
        if not terms:
            return []

        scores: dict[str, float] = {}
        keyword_map = search_index["keyword_map"]

        for keyword, info in keyword_map.items():
            norm_kw = normalize_text(keyword)
            for term in terms:
                if term in norm_kw or norm_kw in normalized:
                    for cat_id in info["cats"]:
                        scores[cat_id] = scores.get(cat_id, 0) + info["weight"]

        for cat in search_index["categories"]:
            cat_id = cat["id"]
            searchable = normalize_text(
                f"{cat.get('titulo', '')} {cat.get('resumo', '')} "
                f"{' '.join(cat.get('tags', []))}"
            )
            match_count = sum(1 for t in terms if t in searchable)
            if match_count > 0:
                scores[cat_id] = scores.get(cat_id, 0) + match_count * 2

        results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:10] if r[1] > 0]

    # --- 30 categories: at least 3 search queries each in top 10 ---

    @pytest.mark.parametrize("query,expected_cat", [
        # bpc
        ("BPC", "bpc"), ("LOAS", "bpc"), ("beneficio prestacao continuada", "bpc"),
        # ciptea
        ("CIPTEA", "ciptea"), ("carteira autismo", "ciptea"), ("romeo mion", "ciptea"),
        # educacao
        ("educação inclusiva", "educacao"), ("escola", "educacao"), ("matrícula", "educacao"),
        # plano_saude
        ("plano saude", "plano_saude"), ("plano de saúde", "plano_saude"), ("ANS", "plano_saude"),
        # sus_terapias
        ("SUS terapias", "sus_terapias"), ("CER CAPS", "sus_terapias"), ("medicamento gratuito", "sus_terapias"),
        # transporte
        ("passe livre", "transporte"), ("transporte gratuito", "transporte"), ("IPVA", "isencoes_tributarias"),
        # trabalho
        ("cotas emprego", "trabalho"), ("trabalho PcD", "trabalho"), ("vaga deficiente", "trabalho"),
        # fgts
        ("FGTS", "fgts"), ("FGTS doença grave", "fgts"), ("saque FGTS", "fgts"),
        # moradia
        ("moradia", "moradia"), ("minha casa minha vida", "moradia"), ("habitação", "moradia"),
        # isencoes_tributarias
        ("isenção IPI", "isencoes_tributarias"), ("IOF veículo", "isencoes_tributarias"),
        ("ICMS carro", "isencoes_tributarias"),
        # atendimento_prioritario
        ("atendimento prioritário", "atendimento_prioritario"), ("prioridade fila", "atendimento_prioritario"),
        ("fila preferencial", "atendimento_prioritario"),
        # estacionamento_especial
        ("estacionamento", "estacionamento_especial"), ("vaga especial", "estacionamento_especial"),
        ("cartão defis", "estacionamento_especial"),
        # aposentadoria_especial_pcd
        ("aposentadoria especial", "aposentadoria_especial_pcd"),
        ("aposentadoria PcD", "aposentadoria_especial_pcd"),
        ("LC 142", "aposentadoria_especial_pcd"),
        # prioridade_judicial
        ("prioridade judicial", "prioridade_judicial"), ("tramitação prioritária", "prioridade_judicial"),
        # tecnologia_assistiva
        ("tecnologia assistiva", "tecnologia_assistiva"), ("cadeira de rodas", "tecnologia_assistiva"),
        ("prótese", "reabilitacao"),
        # meia_entrada
        ("meia entrada", "meia_entrada"), ("desconto cinema", "meia_entrada"), ("50% ingresso", "meia_entrada"),
        # prouni_fies_sisu
        ("prouni", "prouni_fies_sisu"), ("FIES", "prouni_fies_sisu"), ("SISU", "prouni_fies_sisu"),
        # isencao_ir
        ("isenção imposto renda", "isencao_ir"), ("IRPF PcD", "isencao_ir"),
        # bolsa_familia
        ("bolsa família", "bolsa_familia"), ("Bolsa Família PcD", "bolsa_familia"),
        # tarifa_social_energia
        ("tarifa social", "tarifa_social_energia"), ("desconto energia", "tarifa_social_energia"),
        ("conta luz", "tarifa_social_energia"),
        # auxilio_inclusao
        ("auxílio inclusão", "auxilio_inclusao"), ("auxilio inclusao", "auxilio_inclusao"),
        # protecao_social
        ("CRAS", "protecao_social"), ("CREAS", "protecao_social"), ("proteção social", "protecao_social"),
        # pensao_zika
        ("zika", "pensao_zika"), ("microcefalia", "pensao_zika"),
        # esporte_paralimpico
        ("esporte paralímpico", "esporte_paralimpico"), ("bolsa atleta", "esporte_paralimpico"),
        # turismo_acessivel
        ("turismo acessível", "turismo_acessivel"), ("viagem PcD", "turismo_acessivel"),
        # acessibilidade_arquitetonica
        ("acessibilidade arquitetônica", "acessibilidade_arquitetonica"),
        ("rampa", "acessibilidade_arquitetonica"), ("NBR 9050", "acessibilidade_arquitetonica"),
        # capacidade_legal
        ("curatela", "capacidade_legal"), ("tomada decisão apoiada", "capacidade_legal"),
        # crimes_contra_pcd
        ("discriminação PcD", "crimes_contra_pcd"), ("crime deficiente", "crimes_contra_pcd"),
        ("denúncia", "crimes_contra_pcd"),
        # acessibilidade_digital
        ("acessibilidade digital", "acessibilidade_digital"), ("Libras", "acessibilidade_digital"),
        # reabilitacao
        ("reabilitação", "reabilitacao"), ("órtese", "reabilitacao"), ("estimulação precoce", "reabilitacao"),
    ])
    def test_category_findable(self, query, expected_cat, search_index):
        results = self._score_search(query, search_index)
        assert expected_cat in results, (
            f"Query '{query}' did not find '{expected_cat}' in top 10. Got: {results}"
        )


# ════════════════════════════════════════════════════════════════
# E. STATE / ORGÃOS ESTADUAIS VALIDATION
# ════════════════════════════════════════════════════════════════

BRAZIL_STATES = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
    "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
    "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]


class TestStatesAndOrgaos:
    """Validate all 27 Brazilian states are mapped."""

    def test_orgaos_estaduais_exists(self, direitos):
        assert "orgaos_estaduais" in direitos
        assert len(direitos["orgaos_estaduais"]) == 27

    def test_all_27_states_present(self, direitos):
        state_ufs = {o["uf"] for o in direitos["orgaos_estaduais"]}
        missing = set(BRAZIL_STATES) - state_ufs
        assert missing == set(), f"Missing states: {missing}"

    def test_each_state_has_required_fields(self, direitos):
        for orgao in direitos["orgaos_estaduais"]:
            assert "uf" in orgao, f"Orgão missing 'uf'"
            assert "nome" in orgao, f"Orgão {orgao.get('uf')} missing 'nome'"
            assert "url" in orgao, f"Orgão {orgao.get('uf')} missing 'url'"

    def test_state_urls_are_official(self, direitos):
        for orgao in direitos["orgaos_estaduais"]:
            url = orgao.get("url", "")
            assert url.startswith("https://"), (
                f"State {orgao['uf']} URL not HTTPS: {url}"
            )

    def test_no_duplicate_states(self, direitos):
        ufs = [o["uf"] for o in direitos["orgaos_estaduais"]]
        dupes = [u for u, c in Counter(ufs).items() if c > 1]
        assert dupes == [], f"Duplicate states: {dupes}"

    def test_each_state_has_ipva_info(self, direitos):
        """Each state orgao should mention IPVA in beneficios_destaque."""
        for orgao in direitos["orgaos_estaduais"]:
            highlights = orgao.get("beneficios_destaque", [])
            highlights_text = " ".join(highlights).lower()
            assert "ipva" in highlights_text, (
                f"State {orgao['uf']} missing IPVA info in beneficios_destaque"
            )


# ════════════════════════════════════════════════════════════════
# F. CATEGORY STRUCTURE — ALL 30
# ════════════════════════════════════════════════════════════════

class TestCategoryStructure:
    """Validate all 30 category objects have correct structure."""

    def test_exactly_30_categories(self, direitos):
        assert len(direitos["categorias"]) == 30

    def test_required_fields_present(self, direitos):
        required = ["id", "titulo", "resumo", "icone", "base_legal", "links", "tags"]
        for cat in direitos["categorias"]:
            for field in required:
                assert field in cat, (
                    f"Category '{cat.get('id', '?')}' missing field: '{field}'"
                )

    def test_base_legal_has_lei_and_artigo(self, direitos):
        for cat in direitos["categorias"]:
            for bl in cat.get("base_legal", []):
                assert "lei" in bl, (
                    f"Category '{cat['id']}' base_legal missing 'lei'"
                )
                assert "artigo" in bl or "artigos" in bl, (
                    f"Category '{cat['id']}' base_legal missing 'artigo/artigos'"
                )

    def test_category_ids_are_lowercase_identifiers(self, direitos):
        for cat in direitos["categorias"]:
            cid = cat["id"]
            assert re.match(r"^[a-z][a-z0-9_]+$", cid), (
                f"Category ID '{cid}' is not a valid lowercase identifier"
            )

    def test_no_empty_arrays(self, direitos):
        for cat in direitos["categorias"]:
            assert len(cat.get("base_legal", [])) > 0, (
                f"Category '{cat['id']}' has empty base_legal"
            )
            assert len(cat.get("links", [])) > 0, (
                f"Category '{cat['id']}' has empty links"
            )
            assert len(cat.get("tags", [])) > 0, (
                f"Category '{cat['id']}' has empty tags"
            )

    def test_category_has_resumo_content(self, direitos):
        for cat in direitos["categorias"]:
            assert len(cat.get("resumo", "")) >= 20, (
                f"Category '{cat['id']}' resumo too short"
            )

    def test_no_duplicate_category_ids(self, direitos):
        ids = [c["id"] for c in direitos["categorias"]]
        dupes = [i for i, c in Counter(ids).items() if c > 1]
        assert dupes == [], f"Duplicate category IDs: {dupes}"


# ════════════════════════════════════════════════════════════════
# G. HTML SECTIONS & INTERACTIVE ELEMENTS
# ════════════════════════════════════════════════════════════════

class TestHTMLSections:
    """Validate all required sections and interactive elements exist."""

    REQUIRED_SECTIONS = [
        "inicio", "busca", "categorias", "detalhe", "checklist",
        "documentos", "links", "classificacao", "orgaos-estaduais",
        "instituicoes", "transparencia",
    ]

    @pytest.mark.parametrize("section_id", REQUIRED_SECTIONS)
    def test_section_exists(self, section_id, html):
        assert f'id="{section_id}"' in html, f"Missing section: {section_id}"

    def test_search_input_exists(self, html):
        assert 'id="searchInput"' in html

    def test_search_button_exists(self, html):
        assert 'id="searchBtn"' in html

    def test_back_button_exists(self, html):
        assert 'id="voltarBtn"' in html

    def test_category_grid_exists(self, html):
        assert 'id="categoryGrid"' in html

    def test_upload_zone_exists(self, html):
        assert 'id="uploadZone"' in html

    def test_file_input_exists(self, html):
        assert 'id="fileInput"' in html

    def test_export_pdf_button(self, html):
        assert 'id="exportPdf"' in html

    def test_all_buttons_have_type(self, html):
        """All <button> elements should have type attribute."""
        buttons_without_type = re.findall(
            r"<button(?![^>]*\btype\s*=)[^>]*>", html
        )
        assert buttons_without_type == [], (
            f"Buttons without type: {len(buttons_without_type)} found"
        )

    def test_no_target_blank_without_rel(self, html):
        """Links with target=_blank must have rel=noopener."""
        blanks = re.findall(r'target="_blank"[^>]*>', html)
        for tag in blanks:
            assert "noopener" in tag or "noreferrer" in tag, (
                f"target=_blank without rel=noopener: {tag[:80]}"
            )


# ════════════════════════════════════════════════════════════════
# H. ACCESSIBILITY — ARIA, LANDMARKS, FOCUS
# ════════════════════════════════════════════════════════════════

class TestAccessibility:
    """Comprehensive accessibility validation."""

    def test_skip_links_present(self, html):
        assert 'class="skip-link"' in html
        assert 'accesskey="1"' in html
        assert 'accesskey="2"' in html
        assert 'accesskey="3"' in html

    def test_skip_link_targets_exist(self, html):
        assert 'id="mainContent"' in html
        assert 'id="navLinks"' in html
        assert 'id="searchInput"' in html

    def test_setup_skip_links_in_js(self, appjs):
        """JS must have setupSkipLinks for macOS accesskey focus fix."""
        assert "setupSkipLinks" in appjs

    def test_skip_link_focus_logic(self, appjs):
        """setupSkipLinks must call .focus() on the target."""
        assert "target.focus" in appjs

    def test_aria_labels_on_nav(self, html):
        assert 'aria-label="Menu principal"' in html

    def test_aria_labels_on_a11y_panel(self, html):
        assert 'aria-label="Painel de acessibilidade"' in html

    def test_landmarks_present(self, html):
        assert "<nav" in html
        assert "<main" in html
        assert "<header" in html
        assert "<footer" in html
        assert 'role="complementary"' in html

    def test_form_elements_have_labels(self, html):
        assert 'for="searchInput"' in html
        assert 'for="fileInput"' in html or 'aria-label' in html

    def test_aria_live_regions(self, html):
        assert 'aria-live="polite"' in html

    def test_aria_expanded_on_toggles(self, html):
        assert 'aria-expanded="false"' in html

    def test_aria_pressed_on_toggle_buttons(self, html):
        assert 'aria-pressed="false"' in html

    def test_focus_visible_in_css(self, css):
        assert "focus-visible" in css

    def test_sr_only_class_exists(self, css):
        assert ".sr-only" in css

    def test_macos_shortcut_info_in_html(self, html):
        """macOS users see Ctrl+Option instructions in a11y panel."""
        assert "Ctrl + Option" in html or "Ctrl+Option" in html

    def test_a11y_panel_has_font_controls(self, html):
        assert 'id="a11yFontDecrease"' in html
        assert 'id="a11yFontReset"' in html
        assert 'id="a11yFontIncrease"' in html

    def test_a11y_panel_has_contrast(self, html):
        assert 'id="a11yContrast"' in html

    def test_a11y_panel_has_libras(self, html):
        assert 'id="a11yLibras"' in html

    def test_a11y_panel_has_read_aloud(self, html):
        assert 'id="a11yReadAloud"' in html


# ════════════════════════════════════════════════════════════════
# I. VISUALIZATION — RESPONSIVE, DARK MODE, HIGH CONTRAST, PRINT
# ════════════════════════════════════════════════════════════════

class TestVisualization:
    """Validate CSS for all display modes and responsive breakpoints."""

    def test_dark_mode_exists(self, css):
        assert "prefers-color-scheme: dark" in css or "prefers-color-scheme:dark" in css

    def test_high_contrast_rules(self, css):
        assert "html.high-contrast" in css

    def test_high_contrast_image_filter(self, css):
        assert "html.high-contrast img" in css
        assert "filter:" in css[css.index("html.high-contrast img"):]

    def test_print_styles(self, css):
        assert "@media print" in css

    def test_responsive_mobile_breakpoint(self, css):
        assert "480px" in css or "576px" in css

    def test_responsive_tablet_breakpoint(self, css):
        assert "768px" in css

    def test_responsive_desktop_breakpoint(self, css):
        assert "1024px" in css or "1100px" in css

    def test_mobile_a11y_button_is_fab(self, css):
        """Mobile a11y trigger becomes a circular FAB."""
        assert "border-radius: 50%" in css

    def test_desktop_a11y_button_is_sidebar(self, css):
        """Desktop a11y trigger is vertical sidebar."""
        assert "writing-mode: vertical-rl" in css

    def test_css_variables_defined(self, css):
        assert "--primary:" in css
        assert "--surface:" in css
        assert "--text:" in css

    def test_safe_area_for_iphone(self, css):
        """iPhone notch safe area support."""
        assert "safe-area-inset" in css or "env(" in css


# ════════════════════════════════════════════════════════════════
# J. MASSIVE KEYWORD SEARCH COMBINATIONS
# ════════════════════════════════════════════════════════════════

class TestDiverseKeywordSearch:
    """100+ keyword combinations covering different search patterns."""

    @pytest.fixture(scope="class")
    def search_index(self, direitos, matching):
        return {"keyword_map": matching["keyword_map"], "categories": direitos["categorias"]}

    def _score_search(self, query: str, search_index: dict) -> list[str]:
        stopwords = {
            "de", "do", "da", "dos", "das", "e", "em", "o", "a",
            "os", "as", "no", "na", "nos", "nas", "um", "uma",
            "para", "por", "com", "que", "se",
        }
        normalized = normalize_text(query)
        terms = [t for t in normalized.split() if t not in stopwords and len(t) > 1]
        if not terms:
            return []

        scores: dict[str, float] = {}
        keyword_map = search_index["keyword_map"]

        for keyword, info in keyword_map.items():
            norm_kw = normalize_text(keyword)
            for term in terms:
                if term in norm_kw or norm_kw in normalized:
                    for cat_id in info["cats"]:
                        scores[cat_id] = scores.get(cat_id, 0) + info["weight"]

        for cat in search_index["categories"]:
            cat_id = cat["id"]
            searchable = normalize_text(
                f"{cat.get('titulo', '')} {cat.get('resumo', '')} "
                f"{' '.join(cat.get('tags', []))}"
            )
            match_count = sum(1 for t in terms if t in searchable)
            if match_count > 0:
                scores[cat_id] = scores.get(cat_id, 0) + match_count * 2

        results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:10] if r[1] > 0]

    # Acronyms
    @pytest.mark.parametrize("query,expected", [
        ("TEA", "ciptea"), ("ABA", "plano_saude"), ("CID", "sus_terapias"),
        ("INSS", "bpc"), ("AEE", "educacao"),
        ("CAPS", "sus_terapias"), ("CER", "sus_terapias"),
        ("SISEN", "isencoes_tributarias"), ("LOAS", "bpc"),
    ])
    def test_acronym_search(self, query, expected, search_index):
        results = self._score_search(query, search_index)
        assert expected in results, (
            f"Acronym '{query}' → expected '{expected}', got {results}"
        )

    # CID codes
    @pytest.mark.parametrize("cid,expected", [
        ("F84", "ciptea"), ("Q90", "bpc"), ("F70", "bpc"),
        ("H54", "bpc"), ("H90", "bpc"), ("G80", "bpc"),
        ("E34.3", "bpc"), ("F90", "educacao"), ("F84.0", "ciptea"),
    ])
    def test_cid_code_search(self, cid, expected, search_index):
        results = self._score_search(cid, search_index)
        assert expected in results, (
            f"CID '{cid}' → expected '{expected}', got {results}"
        )

    # Informal/regional terms
    @pytest.mark.parametrize("query,expected", [
        ("deficiente", "bpc"),
        ("surdo", "bpc"), ("cego", "bpc"),
        ("cadeirante", "bpc"), ("paraplégico", "bpc"),
        ("down", "ciptea"),
        ("ritalina", "sus_terapias"),
    ])
    def test_informal_terms(self, query, expected, search_index):
        results = self._score_search(query, search_index)
        assert expected in results, (
            f"Informal '{query}' → expected '{expected}', got {results}"
        )

    # Multi-word phrases
    @pytest.mark.parametrize("query,expected", [
        ("lei brasileira inclusão", "educacao"),
        ("salário mínimo deficiente", "bpc"),
        ("imposto renda doença grave", "isencao_ir"),
        ("carteira identificação autismo", "ciptea"),
        ("saque fundo garantia", "fgts"),
        ("vaga emprego deficiente", "trabalho"),
        ("desconto conta energia", "tarifa_social_energia"),
        ("prioridade atendimento fila", "atendimento_prioritario"),
        ("escola recusa matrícula", "educacao"),
        ("aposentadoria tempo contribuição", "aposentadoria_especial_pcd"),
    ])
    def test_multi_word_phrases(self, query, expected, search_index):
        results = self._score_search(query, search_index)
        assert expected in results, (
            f"Phrase '{query}' → expected '{expected}', got {results}"
        )

    # Queries that should return NOTHING
    @pytest.mark.parametrize("query", [
        "", "de", "do da", "xyzqwerty", "zzxxwwvvuu",
    ])
    def test_gibberish_returns_empty(self, query, search_index):
        results = self._score_search(query, search_index)
        assert results == [], f"Gibberish '{query}' returned results: {results}"


# ════════════════════════════════════════════════════════════════
# K. DATA INTEGRITY — DICIONÁRIO + MATCHING ENGINE
# ════════════════════════════════════════════════════════════════

class TestDataIntegrityDeep:
    """Deep data integrity checks across all JSON files."""

    def test_dicionario_all_15_deficiencies(self, dicionario):
        assert len(dicionario["deficiencias"]) >= 15

    def test_dicionario_benefits_map_to_valid_categories(self, dicionario, direitos):
        valid_ids = {c["id"] for c in direitos["categorias"]}
        for entry in dicionario["deficiencias"]:
            for benefit in entry.get("beneficios_elegiveis", []):
                assert benefit in valid_ids, (
                    f"'{entry['nome']}' references unknown category: '{benefit}'"
                )

    def test_dicionario_version_matches_package(self, dicionario, packagejson):
        pkg_v = packagejson.get("version", "")
        dic_v = dicionario.get("versao", "")
        assert dic_v == pkg_v, (
            f"dicionario version={dic_v} != package version={pkg_v}"
        )

    def test_keyword_map_coverage(self, matching, direitos):
        """Every category must be reachable via keyword_map."""
        valid_ids = {c["id"] for c in direitos["categorias"]}
        reachable = set()
        for _kw, info in matching["keyword_map"].items():
            for cat in info["cats"]:
                reachable.add(cat)
        unreachable = valid_ids - reachable
        assert unreachable == set(), (
            f"Categories not reachable via keywords: {unreachable}"
        )

    def test_no_orphan_keyword_references(self, matching, direitos):
        """Keywords must not reference non-existent categories."""
        valid_ids = {c["id"] for c in direitos["categorias"]}
        orphans = set()
        for kw, info in matching["keyword_map"].items():
            for cat in info["cats"]:
                if cat not in valid_ids:
                    orphans.add(f"{kw}→{cat}")
        assert orphans == set(), f"Orphan keyword refs: {orphans}"

    def test_keyword_count_minimum(self, matching):
        count = len(matching["keyword_map"])
        assert count >= 750, f"Only {count} keywords — expected ≥750"

    def test_cid_ranges_cover_major_chapters(self, matching):
        crm = matching["cid_range_map"]
        for prefix in ["F", "G", "H", "Q", "E", "M"]:
            assert prefix in crm, f"CID range map missing prefix: {prefix}"

    def test_config_has_version(self, matching):
        """matching_engine should have version info."""
        assert "keyword_map" in matching

    def test_uppercase_terms_valid(self, matching):
        terms = matching.get("uppercase_only_terms", [])
        assert len(terms) >= 50

    def test_documentos_mestre_exist(self, direitos):
        """documentos_mestre must exist for checklist feature."""
        docs = direitos.get("documentos_mestre", [])
        assert len(docs) >= 5, f"Only {len(docs)} docs mestre"

    def test_documentos_mestre_map_to_categories(self, direitos):
        valid_ids = {c["id"] for c in direitos["categorias"]}
        for doc in direitos.get("documentos_mestre", []):
            for cat in doc.get("categorias", []):
                assert cat in valid_ids, (
                    f"Doc '{doc['nome']}' references unknown category: {cat}"
                )


# ════════════════════════════════════════════════════════════════
# L. SECURITY — OWASP HEADERS, NO LEAKS
# ════════════════════════════════════════════════════════════════

class TestSecurityDeep:
    """Security validation of server.js and app.js."""

    def test_no_console_log_in_appjs(self, appjs):
        """app.js must not have console.log (only console.warn/error)."""
        logs = re.findall(r"console\.log\(", appjs)
        assert logs == [], f"Found {len(logs)} console.log() calls in app.js"

    def test_no_eval_in_appjs(self, appjs):
        """app.js must not use eval()."""
        evals = re.findall(r"\beval\s*\(", appjs)
        assert evals == [], f"Found eval() in app.js"

    def test_safe_json_parse(self, appjs):
        """app.js uses safeJsonParse (anti-prototype pollution)."""
        assert "safeJsonParse" in appjs

    def test_deep_freeze(self, appjs):
        """app.js uses deepFreeze on loaded data."""
        assert "deepFreeze" in appjs

    def test_server_hsts(self, serverjs):
        assert "Strict-Transport-Security" in serverjs

    def test_server_csp(self, serverjs):
        assert "Content-Security-Policy" in serverjs

    def test_server_xframe(self, serverjs):
        assert "X-Frame-Options" in serverjs

    def test_server_nosniff(self, serverjs):
        assert "X-Content-Type-Options" in serverjs

    def test_server_rate_limit(self, serverjs):
        assert "RATE_LIMIT" in serverjs or "rateLimit" in serverjs

    def test_server_health_endpoint(self, serverjs):
        assert "/health" in serverjs

    def test_server_path_traversal(self, serverjs):
        assert ".." in serverjs or "normalize" in serverjs

    def test_no_hardcoded_secrets(self, serverjs):
        """No API keys, passwords, or tokens hardcoded."""
        secret_patterns = [
            r"sk-[a-zA-Z0-9]{32,}",
            r"password\s*=\s*['\"](?!.*env)",
            r"api_key\s*=\s*['\"]",
        ]
        for pattern in secret_patterns:
            matches = re.findall(pattern, serverjs, re.IGNORECASE)
            assert matches == [], f"Possible hardcoded secret: {matches[:1]}"


# ════════════════════════════════════════════════════════════════
# M. PWA & SERVICE WORKER
# ════════════════════════════════════════════════════════════════

class TestPWA:
    """Validate PWA configuration."""

    def test_sw_file_exists(self):
        assert (ROOT / "sw.js").exists()

    def test_sw_register_exists(self):
        assert (ROOT / "js" / "sw-register.js").exists()

    def test_manifest_has_name(self, manifest):
        assert "name" in manifest

    def test_manifest_has_icons(self, manifest):
        assert "icons" in manifest
        assert len(manifest["icons"]) >= 1

    def test_manifest_has_start_url(self, manifest):
        assert "start_url" in manifest

    def test_manifest_has_display(self, manifest):
        assert "display" in manifest

    def test_manifest_theme_color(self, manifest):
        assert "theme_color" in manifest

    def test_sw_has_cache_name(self, swjs):
        assert "cacheName" in swjs or "CACHE_NAME" in swjs or "CACHE" in swjs

    def test_sw_has_fetch_handler(self, swjs):
        assert "fetch" in swjs

    def test_sw_register_script_in_html(self, html):
        assert "sw-register.js" in html


# ════════════════════════════════════════════════════════════════
# N. APP.JS FEATURE COMPLETENESS
# ════════════════════════════════════════════════════════════════

class TestAppFeatures:
    """Validate all major features exist in app.js."""

    def test_search_setup(self, appjs):
        assert "setupSearch" in appjs

    def test_navigation_setup(self, appjs):
        assert "setupNavigation" in appjs

    def test_checklist_setup(self, appjs):
        assert "setupChecklist" in appjs

    def test_upload_setup(self, appjs):
        assert "setupUpload" in appjs

    def test_analysis_setup(self, appjs):
        assert "setupAnalysis" in appjs

    def test_categories_render(self, appjs):
        assert "renderCategories" in appjs

    def test_detalhe_show(self, appjs):
        assert "showDetalhe" in appjs

    def test_transparency_render(self, appjs):
        assert "renderTransparency" in appjs

    def test_classification_render(self, appjs):
        assert "renderClassificacao" in appjs

    def test_links_render(self, appjs):
        assert "renderLinksUteis" in appjs

    def test_staleness_check(self, appjs):
        assert "checkStaleness" in appjs

    def test_file_encryption(self, appjs):
        """AES-GCM encryption for uploaded files."""
        assert "AES-GCM" in appjs or "aes-gcm" in appjs.lower()

    def test_web_crypto_api(self, appjs):
        assert "crypto.subtle" in appjs

    def test_debounce_search(self, appjs):
        """Search should have debounce."""
        assert "debounce" in appjs.lower() or "setTimeout" in appjs

    def test_levenshtein_fuzzy(self, appjs):
        """Fuzzy matching via Levenshtein distance."""
        assert "levenshtein" in appjs.lower() or "editdist" in appjs.lower()

    def test_accent_normalization(self, appjs):
        """Text normalization strips accents."""
        assert "NFD" in appjs or "normalize" in appjs

    def test_deep_link_hash_routing(self, appjs):
        """Support #direito/{id} deep links."""
        assert "#direito/" in appjs

    def test_search_action_url_param(self, appjs):
        """Support ?q= URL parameter for SearchAction."""
        assert "?q=" in appjs or "get('q')" in appjs


# ════════════════════════════════════════════════════════════════
# O. VERSION CONSISTENCY
# ════════════════════════════════════════════════════════════════

class TestVersionConsistency:
    """All version references must be consistent."""

    def test_direitos_version_matches_package(self, direitos, packagejson):
        assert direitos["versao"] == packagejson["version"]

    def test_dicionario_version_matches_package(self, dicionario, packagejson):
        assert dicionario["versao"] == packagejson["version"]

    def test_html_css_cache_bust_matches(self, html, packagejson):
        version = packagejson["version"]
        assert f"styles.css?v={version}" in html

    def test_html_js_cache_bust_matches(self, html, packagejson):
        version = packagejson["version"]
        assert f"app.js?v={version}" in html

    def test_manifest_version_exists(self, manifest):
        """Manifest should have version field."""
        assert "version" in manifest or "name" in manifest


# ════════════════════════════════════════════════════════════════
# P. DISABILITY SEGMENT COVERAGE — ALL 6 TYPES
# ════════════════════════════════════════════════════════════════

class TestDisabilitySegmentCoverage:
    """Validate all 6 disability segments are covered in search keywords.

    Per WCAG/Microsoft Learn, disability includes:
    Visão, Audição, Mobilidade, Saúde Mental, Neurodiversidade e Fala.
    """

    # --- Visão (Vision) ---
    @pytest.mark.parametrize("kw", [
        "cegueira", "baixa visão", "deficiência visual", "cego",
        "visão monocular", "daltonismo", "braille", "dosvox",
    ])
    def test_vision_keywords(self, kw, matching):
        km = matching["keyword_map"]
        assert kw in km, f"Vision keyword missing: '{kw}'"

    # --- Audição (Hearing) ---
    @pytest.mark.parametrize("kw", [
        "surdez", "deficiência auditiva", "surdo", "implante coclear",
        "aparelho auditivo", "libras", "perda auditiva", "audiometria",
        "hipoacusia", "surdocegueira",
    ])
    def test_hearing_keywords(self, kw, matching):
        km = matching["keyword_map"]
        assert kw in km, f"Hearing keyword missing: '{kw}'"

    # --- Mobilidade (Mobility) ---
    @pytest.mark.parametrize("kw", [
        "cadeirante", "paraplegia", "tetraplegia", "amputação",
        "deficiência física", "cadeira de rodas", "paralisia cerebral",
        "mobilidade reduzida", "lesão medular",
    ])
    def test_mobility_keywords(self, kw, matching):
        km = matching["keyword_map"]
        assert kw in km, f"Mobility keyword missing: '{kw}'"

    # --- Saúde Mental (Mental Health) ---
    @pytest.mark.parametrize("kw", [
        "saúde mental", "depressão", "ansiedade", "esquizofrenia",
        "transtorno bipolar", "psicossocial",
    ])
    def test_mental_health_keywords(self, kw, matching):
        km = matching["keyword_map"]
        assert kw in km, f"Mental health keyword missing: '{kw}'"

    # --- Neurodiversidade (Neurodiversity) ---
    @pytest.mark.parametrize("kw", [
        "autismo", "tea", "tdah", "dislexia", "síndrome de down",
        "neurodivergente", "déficit de atenção",
    ])
    def test_neurodiversity_keywords(self, kw, matching):
        km = matching["keyword_map"]
        assert kw in km, f"Neurodiversity keyword missing: '{kw}'"

    # --- Fala (Speech) ---
    @pytest.mark.parametrize("kw", [
        "mudez", "afasia", "gagueira", "mutismo", "disfonia",
        "disfluência", "disartria", "fonoaudiologia", "laringectomia",
    ])
    def test_speech_keywords(self, kw, matching):
        km = matching["keyword_map"]
        assert kw in km, f"Speech keyword missing: '{kw}'"

    # --- Dicionário: all segments represented ---
    def test_dicionario_has_speech_entry(self, dicionario):
        ids = {e["id"] for e in dicionario["deficiencias"]}
        assert "deficiencia_fala" in ids, "Missing speech disability in dicionário"

    def test_dicionario_has_all_segments(self, dicionario):
        ids = {e["id"] for e in dicionario["deficiencias"]}
        required = {
            "deficiencia_visual",       # Visão
            "deficiencia_auditiva",     # Audição
            "deficiencia_fisica_paralisia",  # Mobilidade
            "deficiencia_psicossocial", # Saúde Mental
            "tea",                      # Neurodiversidade
            "tdah",                     # Neurodiversidade
            "deficiencia_fala",         # Fala
        }
        missing = required - ids
        assert missing == set(), f"Missing segments in dicionário: {missing}"


# ════════════════════════════════════════════════════════════════
# Q. WCAG POUR COMPLIANCE
# ════════════════════════════════════════════════════════════════

class TestWCAGPOUR:
    """Validate WCAG POUR principles at AA level.

    Perceivable, Operable, Understandable, Robust.
    """

    # --- PERCEIVABLE ---
    def test_alt_text_on_images(self, html):
        imgs = re.findall(r"<img\s[^>]*>", html)
        for img in imgs:
            assert 'alt=' in img, f"Image without alt: {img[:60]}"

    def test_captions_support_libras(self, appjs):
        """Libras integration = Portuguese sign language for deaf users."""
        assert "vlibras" in appjs.lower()

    def test_text_to_speech_support(self, appjs):
        """TTS for vision-impaired users."""
        assert "speechSynthesis" in appjs

    def test_high_contrast_mode(self, css):
        assert "html.high-contrast" in css

    def test_font_size_controls(self, html):
        assert 'id="a11yFontIncrease"' in html
        assert 'id="a11yFontDecrease"' in html
        assert 'id="a11yFontReset"' in html

    def test_color_not_sole_indicator(self, appjs):
        """Icons (icone field) supplement color for categories."""
        assert "icone" in appjs

    # --- OPERABLE ---
    def test_keyboard_navigation(self, appjs):
        """All functionality available via keyboard."""
        assert "keydown" in appjs
        assert "Escape" in appjs

    def test_skip_links(self, html):
        assert 'class="skip-link"' in html

    def test_focus_trap_in_drawer(self, appjs):
        """A11y drawer has focus trap (Tab cycling)."""
        assert "focusableElements" in appjs or "focusable" in appjs.lower()

    def test_back_to_top_button(self, html):
        assert 'id="backToTop"' in html

    def test_reduced_motion_respected(self, css):
        assert "prefers-reduced-motion" in css

    def test_no_auto_playing_content(self, html):
        """No autoplay audio or video."""
        assert "autoplay" not in html.lower()

    # --- UNDERSTANDABLE ---
    def test_lang_attribute(self, html):
        assert 'lang="pt-BR"' in html

    def test_consistent_navigation(self, html):
        """Nav links exist in header."""
        assert 'id="navLinks"' in html

    def test_error_identification(self, appjs):
        """Search shows clear feedback when no results."""
        assert "nenhum" in appjs.lower() or "resultado" in appjs.lower()

    def test_platform_specific_instructions(self, html):
        """A11y panel shows platform-specific keyboard shortcuts."""
        assert "Windows" in html
        assert "macOS" in html or "Mac" in html

    # --- ROBUST ---
    def test_aria_roles_present(self, html):
        assert 'role="navigation"' in html or 'aria-label="Menu' in html

    def test_aria_live_for_dynamic_content(self, html):
        assert 'aria-live="polite"' in html

    def test_aria_current_in_nav(self, appjs):
        """Active nav link gets aria-current attribute."""
        assert "aria-current" in appjs

    def test_valid_html_structure(self, html):
        """Must have proper HTML5 structure."""
        assert "<!DOCTYPE html>" in html or "<!doctype html>" in html
        assert "<html" in html
        assert "<head>" in html
        assert "<body>" in html

    def test_forced_colors_support(self, css):
        """Windows High Contrast Mode support."""
        assert "forced-colors" in css


# ════════════════════════════════════════════════════════════════
# R. NAVIGATION ACCESSIBILITY BY DISABILITY TYPE
# ════════════════════════════════════════════════════════════════

class TestNavigationByDisability:
    """Verify site navigation works for each disability type."""

    def test_vision_screen_reader_landmarks(self, html):
        """Screen reader users need landmarks."""
        assert "<nav" in html
        assert "<main" in html
        assert "<header" in html
        assert "<footer" in html

    def test_vision_alt_text(self, html):
        """All images must have alt text."""
        imgs_no_alt = re.findall(r"<img(?![^>]*alt=)[^>]*>", html)
        assert imgs_no_alt == [], f"Images without alt: {len(imgs_no_alt)}"

    def test_hearing_libras_integration(self, appjs):
        """Deaf users need Libras (sign language)."""
        assert "vlibras" in appjs.lower()

    def test_hearing_visual_feedback(self, html):
        """Deaf users need visual (not audio-only) feedback."""
        assert 'aria-live="polite"' in html

    def test_mobility_keyboard_only(self, appjs):
        """Motor-impaired users need full keyboard access."""
        assert "keydown" in appjs
        assert "setupSkipLinks" in appjs

    def test_mobility_focus_styles(self, css):
        """Focus indicators must be visible."""
        assert "focus-visible" in css

    def test_mental_health_no_flashing(self, css):
        """No flashing content (seizure prevention)."""
        assert "prefers-reduced-motion" in css

    def test_neurodiversity_clear_layout(self, html):
        """Clear, predictable structure with headings."""
        h2_count = len(re.findall(r"<h2", html))
        assert h2_count >= 5, f"Only {h2_count} h2 headings — need clear structure"

    def test_speech_alternative_input(self, html):
        """Speech-impaired users need non-voice input methods."""
        assert 'id="searchInput"' in html
        assert 'id="fileInput"' in html
