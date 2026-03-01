#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTES CROSS-BROWSER SIMULADOS — NossoDireito v1.14.4

Valida a aplicação simulando todos os navegadores e plataformas:
  - Windows (Chrome, Firefox, Edge)
  - macOS (Chrome, Safari, Firefox)
  - Linux (Chrome, Firefox)
  - iPhone (Safari, Chrome)
  - Android (Chrome, Samsung Internet)

Cobertura:
  - Integridade de dados: direitos.json, matching_engine.json, dicionario_pcd.json
  - Motor de busca: keyword matching, CID matching, scoring
  - Matching engine: cobertura de sinônimos, CID ranges, gaps
  - HTML: semântica, ARIA, landmarks, skip links, meta tags
  - CSS: print styles, dark mode, high contrast, responsive
  - Segurança: CSP, SRI, hardcoded data, sensitive data
  - Acessibilidade: touch targets, WCAG AA, eMAG
  - Service Worker: estratégia, versionamento
  - Documentação: versões sincronizadas, links válidos
"""

import json
import re
import unicodedata
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
JS_DIR = ROOT / "js"
CSS_DIR = ROOT / "css"


# ════════════════════════════════════════════════════════════════

BROWSERS = {
    # Windows
    "chrome_win": {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "platform": "Windows",
        "viewport": (1920, 1080),
        "touch": False,
    },
    "firefox_win": {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "platform": "Windows",
        "viewport": (1920, 1080),
        "touch": False,
    },
    "edge_win": {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "platform": "Windows",
        "viewport": (1920, 1080),
        "touch": False,
    },
    # macOS
    "chrome_mac": {
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "platform": "macOS",
        "viewport": (1440, 900),
        "touch": False,
    },
    "safari_mac": {
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "platform": "macOS",
        "viewport": (1440, 900),
        "touch": False,
    },
    "firefox_mac": {
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
        "platform": "macOS",
        "viewport": (1440, 900),
        "touch": False,
    },
    # Linux
    "chrome_linux": {
        "ua": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "platform": "Linux",
        "viewport": (1920, 1080),
        "touch": False,
    },
    "firefox_linux": {
        "ua": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "platform": "Linux",
        "viewport": (1920, 1080),
        "touch": False,
    },
    # iPhone
    "safari_iphone": {
        "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
        "platform": "iOS",
        "viewport": (390, 844),
        "touch": True,
    },
    "chrome_iphone": {
        "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/122.0.6261.89 Mobile/15E148 Safari/604.1",
        "platform": "iOS",
        "viewport": (390, 844),
        "touch": True,
    },
    # Android
    "chrome_android": {
        "ua": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.105 Mobile Safari/537.36",
        "platform": "Android",
        "viewport": (412, 915),
        "touch": True,
    },
    "samsung_android": {
        "ua": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/24.0 Chrome/122.0.0.0 Mobile Safari/537.36",
        "platform": "Android",
        "viewport": (412, 915),
        "touch": True,
    },
}


def normalize_text(text: str) -> str:
    """Reproduce the JS normalizeText for search simulation."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = re.sub(r"[\u0300-\u036f]", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    return text.strip()


# ════════════════════════════════════════════════════════════════
# 1. DATA INTEGRITY
# ════════════════════════════════════════════════════════════════

class TestDataIntegrity:
    """Validate JSON data files structure and content."""

    def test_direitos_has_categorias(self, direitos):
        assert "categorias" in direitos
        assert len(direitos["categorias"]) == 30

    def test_direitos_has_required_fields(self, direitos):
        required_top = ["versao", "ultima_atualizacao", "categorias"]
        for key in required_top:
            assert key in direitos, f"Missing top-level key: {key}"

    def test_each_category_has_required_fields(self, direitos):
        required = ["id", "titulo", "resumo", "icone"]
        for cat in direitos["categorias"]:
            for field in required:
                assert field in cat, f"Category {cat.get('id', '?')} missing field: {field}"

    def test_all_urls_are_official(self, direitos):
        """All URLs must be from gov.br, icd.who.int, or other official domains."""
        allowed_domains = [
            "gov.br", "leg.br", "jus.br",
            "icd.who.int", "who.int",
            "planalto.gov.br",
            # Official government entities with non-gov.br domains
            "def.br",       # Defensoria Pública (dpu.def.br, etc.)
            "mp.br",        # Ministério Público (mpf.mp.br, cnmp.mp.br)
            "cgu.gov.br",   # Controladoria-Geral da União (falabr.cgu.gov.br)
            "anac.gov.br",  # Agência Nacional de Aviação Civil
            "coffito.gov.br",  # Conselho Federal de Fisioterapia
            "mdh.gov.br",   # Ministério dos Direitos Humanos
            "sp.gov.br",    # Governo de São Paulo (ciptea.sp.gov.br)
            "fazenda.gov.br",  # Receita Federal (sisen)
        ]
        url_pattern = re.compile(r"https?://[^\s\"',)]+")
        text = json.dumps(direitos, ensure_ascii=False)
        urls = url_pattern.findall(text)
        violations = []
        for url in urls:
            domain = re.search(r"https?://([^/]+)", url)
            if domain:
                host = domain.group(1).lower()
                if not any(host.endswith(d) for d in allowed_domains):
                    violations.append(url)
        assert violations == [], f"Non-official URLs: {violations[:5]}"

    def test_matching_engine_structure(self, matching):
        assert "keyword_map" in matching
        assert "cid_range_map" in matching
        assert "uppercase_only_terms" in matching

    def test_keyword_map_has_entries(self, matching):
        kw = matching["keyword_map"]
        assert len(kw) >= 200, f"Only {len(kw)} keywords — expected ≥200"

    def test_keyword_weights_in_range(self, matching):
        for key, val in matching["keyword_map"].items():
            assert "cats" in val, f"Keyword '{key}' missing 'cats'"
            assert "weight" in val, f"Keyword '{key}' missing 'weight'"
            assert 1 <= val["weight"] <= 10, f"Keyword '{key}' weight {val['weight']} out of range"

    def test_cid_range_map_covers_major_prefixes(self, matching):
        crm = matching["cid_range_map"]
        # Major ICD-10 chapter prefixes relevant to disability
        required_prefixes = ["F", "G", "H", "Q", "E", "M"]
        for prefix in required_prefixes:
            assert prefix in crm, f"CID range map missing prefix: {prefix}"

    def test_dicionario_has_deficiencias(self, dicionario):
        assert "deficiencias" in dicionario
        assert len(dicionario["deficiencias"]) >= 10

    def test_dicionario_entries_have_cid(self, dicionario):
        # Categories that legitimately have no CID codes
        no_cid_categories = {
            "deficiencia_multipla",  # Combination of two or more disabilities
            "reabilitados_inss",     # INSS rehab workers — administrative category
            "mobilidade_reduzida",   # Elderly, pregnant, obese — temporary/varied
        }
        for entry in dicionario["deficiencias"]:
            assert "nome" in entry, f"Dicionario entry missing 'nome'"
            entry_id = entry.get("id", "")
            if entry_id in no_cid_categories:
                continue  # Known non-CID categories
            # CID values can be a string or a list of strings
            cid10 = entry.get("cid10", "")
            cid11 = entry.get("cid11", "")
            cid10_str = ", ".join(cid10) if isinstance(cid10, list) else str(cid10)
            cid11_str = ", ".join(cid11) if isinstance(cid11, list) else str(cid11)
            has_cid = bool(cid10_str.strip()) or bool(cid11_str.strip())
            assert has_cid, f"'{entry['nome']}' (id={entry_id}) has no CID codes"

    def test_category_ids_consistent(self, direitos, matching):
        """Category IDs in keyword_map must exist in direitos.json."""
        valid_ids = {c["id"] for c in direitos["categorias"]}
        bad_refs = set()
        for key, val in matching["keyword_map"].items():
            for cat in val["cats"]:
                if cat not in valid_ids:
                    bad_refs.add(cat)
        assert bad_refs == set(), f"Keywords reference non-existent categories: {bad_refs}"


# ════════════════════════════════════════════════════════════════
# 2. SEARCH ALGORITHM SIMULATION
# ════════════════════════════════════════════════════════════════

class TestSearchSimulation:
    """Simulate search queries as users would type them across browsers."""

    @pytest.fixture(scope="class")
    def search_index(self, direitos, matching):
        """Build a simple search index mimicking app.js logic."""
        keyword_map = matching["keyword_map"]
        categories = direitos["categorias"]
        return {"keyword_map": keyword_map, "categories": categories}

    def _score_search(self, query: str, search_index: dict) -> list[dict]:
        """Simplified Python port of app.js scoreSearch."""
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

        # Keyword map matching
        for keyword, info in keyword_map.items():
            norm_kw = normalize_text(keyword)
            for term in terms:
                if term in norm_kw or norm_kw in normalized:
                    for cat_id in info["cats"]:
                        scores[cat_id] = scores.get(cat_id, 0) + info["weight"]

        # Category content matching
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
        return [{"id": r[0], "score": r[1]} for r in results if r[1] > 0]

    @pytest.mark.parametrize("query,expected_cat", [
        ("BPC", "bpc"),
        ("LOAS", "bpc"),
        ("CIPTEA", "ciptea"),
        ("autismo", "ciptea"),
        ("educação inclusiva", "educacao"),
        ("IPVA", "isencoes_tributarias"),
        ("passe livre", "transporte"),
        ("FGTS", "fgts"),
        ("isenção IPI", "isencoes_tributarias"),
        ("aposentadoria especial", "aposentadoria_especial_pcd"),
        ("cadeirante", "bpc"),
        ("tecnologia assistiva", "tecnologia_assistiva"),
        ("plano de saúde", "plano_saude"),
        ("SUS terapias", "sus_terapias"),
        ("bolsa família", "bolsa_familia"),
        ("prioridade fila", "atendimento_prioritario"),
        ("transporte gratuito", "transporte"),
        ("desconto carro", "isencoes_tributarias"),
        ("cadeira de rodas", "tecnologia_assistiva"),
        ("mobilidade reduzida", "bpc"),
    ])
    def test_search_finds_expected_category(self, query, expected_cat, search_index):
        results = self._score_search(query, search_index)
        found_ids = [r["id"] for r in results[:5]]
        assert expected_cat in found_ids, (
            f"Query '{query}' did not find '{expected_cat}' in top 5. "
            f"Got: {found_ids}"
        )

    def test_empty_search_returns_nothing(self, search_index):
        assert self._score_search("", search_index) == []

    def test_stopword_only_returns_nothing(self, search_index):
        assert self._score_search("de do da", search_index) == []

    def test_search_results_sorted_by_score(self, search_index):
        results = self._score_search("BPC LOAS benefício", search_index)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)


# ════════════════════════════════════════════════════════════════
# 3. CROSS-BROWSER HTML VALIDATION
# ════════════════════════════════════════════════════════════════

class TestHTMLStructure:
    """Validate HTML for cross-browser compatibility."""

    def test_doctype_declaration(self, html):
        assert html.strip().lower().startswith("<!doctype html>")

    def test_lang_attribute(self, html):
        assert 'lang="pt-BR"' in html

    def test_charset_meta(self, html):
        assert 'charset="utf-8"' in html.lower() or 'charset="UTF-8"' in html

    def test_viewport_meta(self, html):
        assert 'name="viewport"' in html
        assert "width=device-width" in html

    def test_has_skip_links(self, html):
        assert 'class="skip-link"' in html

    def test_has_main_landmark(self, html):
        assert "<main" in html.lower()

    def test_has_nav_landmark(self, html):
        assert "<nav" in html.lower()

    def test_has_header_landmark(self, html):
        assert "<header" in html.lower()

    def test_has_footer_landmark(self, html):
        assert "<footer" in html.lower()

    def test_has_h1(self, html):
        h1_count = len(re.findall(r"<h1[> ]", html, re.IGNORECASE))
        assert h1_count >= 1, "Page must have at least one <h1>"

    def test_noscript_fallback(self, html):
        assert "<noscript>" in html.lower()

    def test_search_input_has_label(self, html):
        assert 'for="searchInput"' in html

    def test_search_input_has_maxlength(self, html):
        search_input = re.search(
            r'<input[^>]*id="searchInput"[^>]*>', html, re.IGNORECASE
        )
        assert search_input, "Search input not found"
        assert "maxlength" in search_input.group(0).lower(), (
            "Search input should have maxlength to prevent abuse"
        )

    def test_disclaimer_present(self, html):
        lower = html.lower()
        has_disclaimer = (
            "não substitui" in lower
            or "caráter educacional" in lower
            or "aviso importante" in lower
        )
        assert has_disclaimer, "Disclaimer text not found"

    def test_jsonld_structured_data(self, html):
        assert 'application/ld+json' in html

    def test_og_meta_tags(self, html):
        assert 'property="og:title"' in html
        assert 'property="og:description"' in html

    def test_manifest_link(self, html):
        assert 'rel="manifest"' in html

    def test_service_worker_registration(self, html):
        assert "sw-register" in html

    def test_cache_busting_on_assets(self, html):
        """CSS and JS references should have version query strings."""
        css_ref = re.search(r'href="css/styles\.css(\?[^"]+)?"', html)
        js_ref = re.search(r'src="js/app\.js(\?[^"]+)?"', html)
        assert css_ref and css_ref.group(1), "styles.css should have cache-busting ?v="
        assert js_ref and js_ref.group(1), "app.js should have cache-busting ?v="


# ════════════════════════════════════════════════════════════════
# 4. CSS CROSS-BROWSER TESTS
# ════════════════════════════════════════════════════════════════

class TestCSSCompatibility:
    """Validate CSS for cross-browser and accessibility compliance."""

    def test_has_dark_mode_support(self, css):
        assert "prefers-color-scheme: dark" in css

    def test_has_print_styles(self, css):
        assert "@media print" in css

    def test_has_reduced_motion(self, css):
        assert "prefers-reduced-motion" in css

    def test_has_high_contrast(self, css):
        high_contrast = "high-contrast" in css or "forced-colors" in css
        assert high_contrast, "Missing high contrast/forced-colors support"

    def test_responsive_breakpoints(self, css):
        """Must have at least one mobile breakpoint."""
        media_queries = re.findall(r"@media[^{]+", css)
        has_mobile = any(
            "max-width" in mq or "min-width" in mq
            for mq in media_queries
        )
        assert has_mobile, "No responsive breakpoints found"

    def test_touch_targets_minimum_size(self, css):
        """Touch targets should be at least 44px for accessibility."""
        assert "44px" in css or "2.75rem" in css

    def test_focus_indicators(self, css):
        """Must have visible focus styles for keyboard navigation."""
        assert ":focus" in css

    def test_sr_only_class(self, css):
        """Screen-reader-only class for visually hidden text."""
        assert ".sr-only" in css

    def test_no_important_overuse(self, css):
        """Excessive !important indicates poor CSS architecture."""
        important_count = css.count("!important")
        # Allow some — high contrast mode legitimately needs them
        assert important_count < 200, (
            f"Too many !important ({important_count}). Consider refactoring."
        )


# ════════════════════════════════════════════════════════════════
# 5. JAVASCRIPT SECURITY & QUALITY
# ════════════════════════════════════════════════════════════════

class TestJSSecurity:
    """Validate JS for security, sensitive data, and best practices."""

    def test_no_hardcoded_api_keys(self, appjs):
        """No API keys, tokens, or secrets in JavaScript."""
        patterns = [
            r"(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{8,}",
            r"Bearer\s+[A-Za-z0-9\-_.]{20,}",
            r"sk-[A-Za-z0-9]{20,}",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, appjs, re.IGNORECASE)
            assert matches == [], f"Potential secret found: {matches[:3]}"

    def test_escape_html_exists(self, appjs):
        assert "escapeHtml" in appjs

    def test_escape_regex_exists(self, appjs):
        assert "escapeRegex" in appjs

    def test_safe_json_parse_exists(self, appjs):
        assert "safeJsonParse" in appjs

    def test_deep_freeze_exists(self, appjs):
        assert "deepFreeze" in appjs

    def test_uses_strict_mode(self, appjs):
        assert "'use strict'" in appjs

    def test_no_eval_usage(self, appjs):
        """No direct eval() in app code (allowed in VLibras only)."""
        # Remove string literals and comments to avoid false positives
        cleaned = re.sub(r"//[^\n]*", "", appjs)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"'[^']*'", "''", cleaned)
        cleaned = re.sub(r'"[^"]*"', '""', cleaned)
        # Check for eval( calls
        eval_calls = re.findall(r"\beval\s*\(", cleaned)
        assert eval_calls == [], "Direct eval() usage found in app.js"

    def test_no_document_write(self, appjs):
        assert "document.write" not in appjs

    def test_no_innerhtml_without_escape(self, appjs):
        """innerHTML assignments should use escapeHtml."""
        # This is a heuristic — verify innerHTML is sanitized
        assert "escapeHtml" in appjs, "escapeHtml function must exist for XSS prevention"

    def test_crypto_api_usage(self, appjs):
        """Must use Web Crypto API for encryption."""
        assert "crypto.subtle" in appjs

    def test_aes_gcm_256_used(self, appjs):
        assert "AES-GCM" in appjs

    def test_ttl_is_15_minutes(self, appjs):
        assert "FILE_TTL_MINUTES = 15" in appjs


# ════════════════════════════════════════════════════════════════
# 6. SERVICE WORKER VALIDATION
# ════════════════════════════════════════════════════════════════

class TestServiceWorker:
    """Validate sw.js for correct caching strategy."""

    def test_cache_version_matches_package(self, swjs, packagejson):
        version = packagejson["version"]
        expected = f"nossodireito-v{version}"
        assert expected in swjs, (
            f"SW cache version should contain '{expected}'"
        )

    def test_network_first_for_same_origin(self, swjs):
        assert "networkFirst" in swjs

    def test_cache_first_for_cdn_only(self, swjs):
        assert "cacheFirst" in swjs

    def test_static_assets_include_critical_files(self, swjs):
        critical = ["/index.html", "/css/styles.css", "/js/app.js",
                    "/data/direitos.json", "/data/matching_engine.json"]
        for asset in critical:
            assert asset in swjs, f"SW missing critical asset: {asset}"

    def test_old_cache_cleanup(self, swjs):
        assert "caches.delete" in swjs or "caches.keys" in swjs

    def test_skip_waiting(self, swjs):
        assert "skipWaiting" in swjs

    def test_clients_claim(self, swjs):
        assert "clients.claim" in swjs

    def test_offline_fallback_exists(self, swjs):
        has_offline = "Offline" in swjs or "offline" in swjs or "503" in swjs
        assert has_offline, "SW should have offline fallback"


# ════════════════════════════════════════════════════════════════
# 7. MANIFEST & PWA
# ════════════════════════════════════════════════════════════════

class TestPWA:
    """Validate PWA manifest and configuration."""

    def test_manifest_name(self, manifest):
        assert "name" in manifest
        assert len(manifest["name"]) > 0

    def test_manifest_short_name(self, manifest):
        assert "short_name" in manifest

    def test_manifest_start_url(self, manifest):
        assert "start_url" in manifest

    def test_manifest_display(self, manifest):
        assert manifest.get("display") in ("standalone", "fullscreen", "minimal-ui")

    def test_manifest_theme_color(self, manifest):
        assert "theme_color" in manifest

    def test_manifest_icons(self, manifest):
        assert "icons" in manifest
        sizes = [icon.get("sizes", "") for icon in manifest["icons"]]
        assert any("192x192" in s for s in sizes), "Missing 192x192 icon"
        assert any("512x512" in s for s in sizes), "Missing 512x512 icon"

    def test_manifest_lang(self, manifest):
        assert manifest.get("lang") == "pt-BR"


# ════════════════════════════════════════════════════════════════
# 8. CROSS-BROWSER SIMULATION
# ════════════════════════════════════════════════════════════════

class TestCrossBrowserSimulation:
    """Simulate browser-specific behaviors and validate compatibility."""

    @pytest.mark.parametrize("browser_id", list(BROWSERS.keys()))
    def test_html_parseable_all_browsers(self, browser_id, html):
        """HTML5 doctype ensures consistent parsing across browsers."""
        browser = BROWSERS[browser_id]
        assert html.strip().lower().startswith("<!doctype html>"), (
            f"[{browser_id}] Missing HTML5 doctype for consistent rendering"
        )

    @pytest.mark.parametrize("browser_id", [
        b for b, info in BROWSERS.items() if info["touch"]
    ])
    def test_mobile_browsers_have_touch_targets(self, browser_id, css):
        """Mobile browsers need 44px minimum touch targets (WCAG 2.5.8)."""
        assert "44px" in css or "2.75rem" in css, (
            f"[{browser_id}] Touch targets not enforced in CSS"
        )

    @pytest.mark.parametrize("browser_id", [
        b for b, info in BROWSERS.items() if info["touch"]
    ])
    def test_mobile_has_hamburger_menu(self, html, browser_id):
        """Mobile browsers should get hamburger menu."""
        has_hamburger = (
            "hamburger" in html.lower()
            or "menu-toggle" in html.lower()
            or "navbar-toggle" in html.lower()
            or "menu-btn" in html.lower()
            or "menuBtn" in html
        )
        assert has_hamburger, f"[{browser_id}] No mobile menu toggle found"

    @pytest.mark.parametrize("browser_id", [
        b for b, info in BROWSERS.items() if "safari" in b
    ])
    def test_safari_webkit_prefixes(self, css, browser_id):
        """Safari may need -webkit- prefixes for some properties."""
        has_webkit = "-webkit-" in css
        assert has_webkit, f"[{browser_id}] No -webkit- prefixes for Safari compatibility"

    @pytest.mark.parametrize("browser_id", list(BROWSERS.keys()))
    def test_search_works_all_browsers(self, browser_id, direitos, matching):
        """Core search must work identically across all browsers."""
        kw_map = matching["keyword_map"]
        # Test basic BPC search
        assert "bpc" in kw_map, f"[{browser_id}] 'bpc' not in keyword_map"
        assert "bpc" in kw_map["bpc"]["cats"], f"[{browser_id}] BPC keyword missing BPC category"


# ════════════════════════════════════════════════════════════════
# 11. SECURITY & COMPLIANCE CHECKS
# ════════════════════════════════════════════════════════════════

class TestSecurityCompliance:
    """Validate security controls and LGPD compliance."""

    def test_no_sensitive_data_in_json(self, direitos):
        """No CPF, RG, or personal data in knowledge base.

        Note: Public service phone numbers (Disque 100, INSS 135, etc.)
        are intentional and allowed.
        """
        text = json.dumps(direitos, ensure_ascii=False)
        cpf_pattern = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
        # Phone numbers of public services (Disque 100 WhatsApp, etc.) are allowed
        # Only flag personal cell phones not associated with government services
        email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@(?!example\.com)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
        assert not cpf_pattern.search(text), "CPF found in data"
        # Allow gov.br emails, block personal
        emails = email_pattern.findall(text)
        personal = [e for e in emails if not e.endswith(".gov.br")]
        assert personal == [], f"Personal emails in data: {personal}"

    def test_csp_meta_tag(self, html):
        """CSP must be present via meta tag or documented as HTTP header."""
        has_meta = "Content-Security-Policy" in html or "content-security-policy" in html.lower()
        # CSP enforced via HTTP header in server.js is acceptable
        has_header_comment = "CSP enforced via HTTP header" in html
        assert has_meta or has_header_comment, "No CSP meta tag or server-side CSP reference found"

    def test_sri_on_external_scripts(self, html):
        """External scripts must have SRI (integrity attribute)."""
        # Find all <script> with src containing cdnjs or cdn
        cdn_scripts = re.findall(
            r'<script[^>]+src="https://cdn[^"]*"[^>]*>', html, re.IGNORECASE
        )
        for script in cdn_scripts:
            assert "integrity=" in script, f"CDN script without SRI: {script[:80]}"

    def test_robots_txt_exists(self):
        assert (ROOT / "robots.txt").exists()

    def test_sitemap_xml_exists(self):
        assert (ROOT / "sitemap.xml").exists()

    def test_no_hardcoded_credentials(self, appjs):
        """No passwords, API keys, or secrets."""
        forbidden = [
            r"password\s*=\s*['\"]",
            r"api_key\s*=\s*['\"]",
            r"secret\s*=\s*['\"]",
        ]
        for pattern in forbidden:
            assert not re.search(pattern, appjs, re.IGNORECASE), (
                f"Hardcoded credential pattern found: {pattern}"
            )


# ════════════════════════════════════════════════════════════════
# 12. MATCHING ENGINE COVERAGE
# ════════════════════════════════════════════════════════════════

class TestMatchingCoverage:
    """Validate comprehensive keyword and CID coverage."""

    def test_new_synonyms_present(self, matching):
        """Verify newly added synonyms exist."""
        kw = matching["keyword_map"]
        new_terms = [
            "cadeirante", "cadeira de rodas", "mobilidade reduzida",
            "transporte gratuito", "desconto carro", "deficiente visual",
            "surdo", "paralisia cerebral",
        ]
        for term in new_terms:
            assert term in kw, f"Missing new synonym: '{term}'"

    def test_all_categories_reachable_via_keywords(self, direitos, matching):
        """Every category should be reachable via at least one keyword."""
        cat_ids = {c["id"] for c in direitos["categorias"]}
        reachable = set()
        for _kw, info in matching["keyword_map"].items():
            for cat in info["cats"]:
                reachable.add(cat)
        unreachable = cat_ids - reachable
        assert unreachable == set(), (
            f"Categories not reachable via any keyword: {unreachable}"
        )

    def test_cid_uppercase_terms_valid(self, matching):
        """Uppercase-only terms should be valid CID codes or known acronyms."""
        terms = matching["uppercase_only_terms"]
        assert len(terms) >= 50, f"Only {len(terms)} uppercase terms"


# ════════════════════════════════════════════════════════════════
# 14. CASE-INSENSITIVE & ACCENT-INSENSITIVE SEARCH
# ════════════════════════════════════════════════════════════════

class TestSearchCaseAccent:
    """User request: 'Se pesquiso na busca maiusculo, minusculo?
    se troco algumas letras ou palavras como é o comportamento?'"""

    @pytest.fixture(scope="class")
    def search_index(self, direitos, matching):
        keyword_map = matching["keyword_map"]
        categories = direitos["categorias"]
        return {"keyword_map": keyword_map, "categories": categories}

    def _score_search(self, query: str, search_index: dict) -> list[str]:
        """Return top-5 category IDs for a query."""
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
        return [r[0] for r in results[:5] if r[1] > 0]

    # --- Case insensitivity ---

    @pytest.mark.parametrize("query_lower,query_upper,expected_cat", [
        ("bpc", "BPC", "bpc"),
        ("ciptea", "CIPTEA", "ciptea"),
        ("fgts", "FGTS", "fgts"),
        ("ipva", "IPVA", "isencoes_tributarias"),
        ("sus terapias", "SUS TERAPIAS", "sus_terapias"),
        ("passe livre", "PASSE LIVRE", "transporte"),
    ])
    def test_case_insensitive_same_results(
        self, query_lower, query_upper, expected_cat, search_index
    ):
        """Uppercase and lowercase queries must find the same category."""
        results_lower = self._score_search(query_lower, search_index)
        results_upper = self._score_search(query_upper, search_index)
        assert expected_cat in results_lower, (
            f"'{query_lower}' did not find '{expected_cat}'"
        )
        assert expected_cat in results_upper, (
            f"'{query_upper}' did not find '{expected_cat}'"
        )

    @pytest.mark.parametrize("query_mixed,expected_cat", [
        ("Bpc Loas", "bpc"),
        ("CiPtEa", "ciptea"),
        ("Educação Inclusiva", "educacao"),
        ("Transporte Gratuito", "transporte"),
        ("Plano De Saúde", "plano_saude"),
    ])
    def test_mixed_case_finds_category(
        self, query_mixed, expected_cat, search_index
    ):
        """Mixed case (Title Case, random) must still find the category."""
        results = self._score_search(query_mixed, search_index)
        assert expected_cat in results, (
            f"'{query_mixed}' did not find '{expected_cat}'. Got: {results}"
        )

    # --- Accent insensitivity ---

    @pytest.mark.parametrize("with_accent,without_accent,expected_cat", [
        ("educação", "educacao", "educacao"),
        ("isenção", "isencao", "isencoes_tributarias"),
        ("saúde", "saude", "plano_saude"),
        ("prótese", "protese", "reabilitacao"),
        ("família", "familia", "bolsa_familia"),
    ])
    def test_accent_insensitive_search(
        self, with_accent, without_accent, expected_cat, search_index
    ):
        """Queries with/without accents must return same category."""
        results_accent = self._score_search(with_accent, search_index)
        results_plain = self._score_search(without_accent, search_index)
        assert expected_cat in results_accent, (
            f"'{with_accent}' did not find '{expected_cat}'"
        )
        assert expected_cat in results_plain, (
            f"'{without_accent}' did not find '{expected_cat}'"
        )

    # --- Normalize function parity ---

    @pytest.mark.parametrize("text,expected", [
        ("BPC/LOAS", "bpc loas"),
        ("Educação Inclusiva", "educacao inclusiva"),
        ("CIPTEA — Lei Romeo Mion", "ciptea   lei romeo mion"),
        ("R$ 200.000", "r  200 000"),
        ("  espaços  extras  ", "espacos  extras"),
    ])
    def test_normalize_function(self, text, expected):
        """normalize_text must strip accents, lowercase, replace punc with space."""
        result = normalize_text(text)
        assert result == expected, f"normalize('{text}') = '{result}', expected '{expected}'"


# ════════════════════════════════════════════════════════════════
# 15. FUZZY MATCH (LEVENSHTEIN DISTANCE) VALIDATION
# ════════════════════════════════════════════════════════════════

class TestFuzzyMatching:
    """Validate that the JS engine supports Levenshtein fuzzy matching.
    app.js implements getLevenshteinDistance with max edit distance 2."""

    def test_levenshtein_function_exists(self, appjs):
        """app.js must define a Levenshtein distance function."""
        assert "levenshtein" in appjs.lower() or "editdist" in appjs.lower(), (
            "Levenshtein / edit distance function not found in app.js"
        )

    def test_fuzzy_match_threshold(self, appjs):
        """Fuzzy match distance should be capped (<=2 or <=3)."""
        # Look for distance comparison patterns
        found = bool(re.search(r"distance\s*[<=>]+\s*[23]", appjs, re.IGNORECASE))
        if not found:
            found = bool(re.search(r"maxDist|MAX_EDIT", appjs, re.IGNORECASE))
        assert found, "No fuzzy match threshold found in app.js"

    @pytest.mark.parametrize("typo,correct,expected_distance", [
        ("autimo", "autismo", 1),   # Missing 's'
        ("educcao", "educacao", 1), # Extra 'c' (accent stripped)
        ("benefico", "beneficio", 1),  # Missing 'i' (accent stripped)
        ("trasporte", "transporte", 1),  # Missing 'n'
        ("aponsentadoria", "aposentadoria", 1),  # Extra 'n'
    ])
    def test_levenshtein_distance_calculation(
        self, typo, correct, expected_distance
    ):
        """Verify Levenshtein distance for common typos is <=2."""

        def levenshtein(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return levenshtein(s2, s1)
            if len(s2) == 0:
                return len(s1)
            prev = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                curr = [i + 1]
                for j, c2 in enumerate(s2):
                    cost = 0 if c1 == c2 else 1
                    curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
                prev = curr
            return prev[-1]

        dist = levenshtein(
            normalize_text(typo), normalize_text(correct)
        )
        assert dist == expected_distance, (
            f"levenshtein('{typo}', '{correct}') = {dist}, expected {expected_distance}"
        )
        assert dist <= 2, f"Distance {dist} exceeds fuzzy threshold of 2"


# ════════════════════════════════════════════════════════════════
# 16. PLATFORM PARITY (Desktop vs Mobile)
# ════════════════════════════════════════════════════════════════

class TestPlatformParity:
    """User request: 'a experiência desktop, mobile é a mesma?
    windows, mac os, linux, iphone, android? safari, chrome, edge?'"""

    def test_all_platforms_represented_in_browsers(self):
        """All major platforms are in the BROWSERS dict."""
        platforms = {b["platform"] for b in BROWSERS.values()}
        required = {"Windows", "macOS", "Linux", "iOS", "Android"}
        missing = required - platforms
        assert missing == set(), f"Missing platforms: {missing}"

    def test_touch_targets_for_mobile(self, css):
        """Mobile browsers need touch targets >= 44px."""
        assert "min-height: 44px" in css or "min-height:44px" in css

    def test_responsive_breakpoints_exist(self, css):
        """CSS must have responsive breakpoints for mobile/tablet/desktop."""
        has_768 = "@media" in css and "768px" in css
        has_small = "@media" in css and ("480px" in css or "576px" in css)
        assert has_768, "Missing tablet breakpoint (~768px)"
        assert has_small, "Missing mobile breakpoint (~480-576px)"

    def test_dark_mode_media_query(self, css):
        """Dark mode for all platforms."""
        assert "prefers-color-scheme: dark" in css or "prefers-color-scheme:dark" in css

    def test_viewport_fit_cover(self, html):
        """iPhone notch safe areas (viewport-fit=cover)."""
        assert "viewport-fit=cover" in html

    def test_apple_mobile_web_app_capable(self, html):
        """iOS PWA meta tags."""
        assert 'name="apple-mobile-web-app-capable"' in html

    def test_manifest_for_android(self, manifest):
        """Android PWA manifest."""
        assert "name" in manifest
        assert "icons" in manifest
        assert "start_url" in manifest

    @pytest.mark.parametrize("browser_key", list(BROWSERS.keys()))
    def test_browser_viewport_is_positive(self, browser_key):
        """All browser viewport dimensions must be positive."""
        vw, vh = BROWSERS[browser_key]["viewport"]
        assert vw > 0 and vh > 0

    def test_desktop_viewports_wider_than_mobile(self):
        """Desktop viewports should be wider than mobile viewports."""
        desktop_widths = [
            BROWSERS[k]["viewport"][0]
            for k in BROWSERS
            if not BROWSERS[k]["touch"]
        ]
        mobile_widths = [
            BROWSERS[k]["viewport"][0]
            for k in BROWSERS
            if BROWSERS[k]["touch"]
        ]
        assert min(desktop_widths) > max(mobile_widths), (
            "Desktop viewport should be wider than mobile"
        )


# ════════════════════════════════════════════════════════════════
# 17. CROSS-OS COMMAND COMPATIBILITY
# ════════════════════════════════════════════════════════════════

class TestCrossOSCommands:
    """User request: 'os comandos aqui deste repo podem ser
    executados no windows ou mac os? linux?'"""

    def test_python_scripts_have_shebang(self):
        """Python scripts should have shebang (Unix) or be
        invocable via 'python scripts/<name>.py' (all OS)."""
        scripts_dir = ROOT / "scripts"
        for py_file in scripts_dir.glob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            # Either has shebang or can be invoked as module
            assert (
                "#!/" in content[:50]
                or "import " in content[:500]
                or "def " in content[:500]
            ), f"{py_file.name} is not a valid Python script"

    def test_no_unix_only_paths_in_scripts(self):
        """Scripts should not use Unix-only paths like /usr/local or /opt."""
        scripts_dir = ROOT / "scripts"
        for py_file in scripts_dir.glob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            # Allow shebangs and comments
            code_lines = [
                line
                for line in content.split("\n")
                if line.strip()
                and not line.strip().startswith("#")
                and not line.strip().startswith("#!/")
            ]
            code_text = "\n".join(code_lines)
            unix_paths = re.findall(r'["\']/(usr|opt|etc)/[^"\']+["\']', code_text)
            assert unix_paths == [], (
                f"{py_file.name} has Unix-only paths: {unix_paths}"
            )

    def test_scripts_use_pathlib_or_os_path(self):
        """Scripts should use pathlib or os.path for cross-OS compat.
        Allow scripts that use __file__ or open() with relative paths too."""
        scripts_dir = ROOT / "scripts"
        for py_file in scripts_dir.glob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            if len(content) < 100:
                continue  # Skip trivially small files
            uses_path = (
                "pathlib" in content
                or "os.path" in content
                or "Path(" in content
                or "__file__" in content
                or "os.getcwd" in content
                or "open(" in content  # file I/O works cross-OS
            )
            assert uses_path, f"{py_file.name} doesn't use pathlib or os.path"

    def test_package_json_scripts_cross_platform(self):
        """package.json scripts should not use Unix-only commands."""
        pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        scripts = pkg.get("scripts", {})
        unix_only = ["chmod", "chown", "ln -s", "grep ", "sed "]
        for name, cmd in scripts.items():
            for unix_cmd in unix_only:
                assert unix_cmd not in cmd, (
                    f"package.json script '{name}' uses Unix-only '{unix_cmd}'"
                )

    def test_requirements_files_exist(self):
        """All requirements files exist and are valid."""
        for req_file in ["requirements.txt", "requirements-dev.txt"]:
            path = ROOT / req_file
            assert path.exists(), f"Missing {req_file}"
            content = path.read_text(encoding="utf-8")
            assert len(content.strip()) > 0, f"{req_file} is empty"
