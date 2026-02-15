#!/usr/bin/env python3
"""
avaliacao_360.py — Avaliação 360° do site NossoDireito
======================================================
Valida TODAS as funcionalidades, dados e integridade do site:
- Estrutura do JSON (direitos.json, dicionario_pcd.json, matching_engine.json)
- Integridade de dados (campos obrigatórios, referências cruzadas)
- URLs (oficiais, acessíveis, sem duplicatas)
- SEO (meta tags, JSON-LD, sitemap, robots.txt)
- Acessibilidade (atributos ARIA, alt text, skip links)
- HTML (estrutura semântica, seções, navegação)
- JavaScript (app.js referências de dados)
- Segurança (CSP, LGPD compliance)
"""

import json
import os
import re
import sys
import urllib.parse
from pathlib import Path
from datetime import datetime
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DIREITOS = DATA_DIR / "direitos.json"
DICIONARIO = DATA_DIR / "dicionario_pcd.json"
MATCHING = DATA_DIR / "matching_engine.json"
IPVA = DATA_DIR / "ipva_pcd_estados.json"
INDEX_HTML = ROOT / "index.html"
SITEMAP = ROOT / "sitemap.xml"
ROBOTS = ROOT / "robots.txt"
MANIFEST = ROOT / "manifest.json"
APP_JS = ROOT / "js" / "app.js"
SW_JS = ROOT / "sw.js"
CSS = ROOT / "css" / "styles.css"

# Contadores globais
total_checks = 0
passed = 0
warnings = 0
errors = 0
results = []


def check(name, condition, detail=""):
    """Registra um check: OK ou FALHA."""
    global total_checks, passed, warnings, errors
    total_checks += 1
    if condition:
        passed += 1
        results.append(("✅", name, detail))
    else:
        errors += 1
        results.append(("❌", name, detail))


def warn(name, detail=""):
    """Registra um aviso."""
    global total_checks, warnings
    total_checks += 1
    warnings += 1
    results.append(("⚠️", name, detail))


def info(name, detail=""):
    """Registra info."""
    results.append(("ℹ️", name, detail))


# ════════════════════════════════════════════════
# 1. ESTRUTURA DE ARQUIVOS
# ════════════════════════════════════════════════
def check_file_structure():
    info("SEÇÃO 1", "ESTRUTURA DE ARQUIVOS")
    required_files = [
        DIREITOS, DICIONARIO, MATCHING, INDEX_HTML,
        SITEMAP, ROBOTS, MANIFEST, APP_JS, SW_JS, CSS,
    ]
    for f in required_files:
        check(f"Arquivo existe: {f.name}", f.exists(), str(f.relative_to(ROOT)))

    optional_files = [IPVA]
    for f in optional_files:
        if f.exists():
            check(f"Arquivo opcional: {f.name}", True)
        else:
            warn(f"Arquivo opcional ausente: {f.name}")


# ════════════════════════════════════════════════
# 2. DIREITOS.JSON — DADOS PRINCIPAIS
# ════════════════════════════════════════════════
def check_direitos_json():
    info("SEÇÃO 2", "DIREITOS.JSON — DADOS PRINCIPAIS")
    with open(DIREITOS, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Top-level keys
    required_keys = ["versao", "ultima_atualizacao", "categorias", "fontes",
                     "documentos_mestre", "instituicoes_apoio",
                     "orgaos_estaduais", "classificacao_deficiencia"]
    for key in required_keys:
        check(f"direitos.json: chave '{key}' presente", key in data)

    cats = data.get("categorias", [])
    fontes = data.get("fontes", [])
    docs = data.get("documentos_mestre", [])
    inst = data.get("instituicoes_apoio", [])
    orgaos = data.get("orgaos_estaduais", [])
    classif = data.get("classificacao_deficiencia", [])

    check(f"Categorias: {len(cats)} (esperado ≥25)", len(cats) >= 25)
    check(f"Fontes: {len(fontes)} (esperado ≥60)", len(fontes) >= 60)
    check(f"Documentos mestre: {len(docs)} (esperado ≥10)", len(docs) >= 10)
    check(f"Instituições apoio: {len(inst)} (esperado ≥20)", len(inst) >= 20)
    check(f"Órgãos estaduais: {len(orgaos)} (esperado 27)", len(orgaos) == 27)
    check(f"Classificações deficiência: {len(classif)} (esperado ≥10)", len(classif) >= 10)

    # Validar cada categoria
    cat_ids = set()
    required_cat_fields = ["id", "titulo", "icone", "resumo"]
    optional_cat_fields = ["base_legal", "requisitos", "documentos",
                           "passo_a_passo", "dicas", "valor", "onde", "links", "tags"]
    for cat in cats:
        cat_id = cat.get("id", "?")
        cat_ids.add(cat_id)
        for field in required_cat_fields:
            check(f"Cat [{cat_id}] campo '{field}'", field in cat and cat[field])

        # Verificar tags
        tags = cat.get("tags", [])
        if not tags:
            warn(f"Cat [{cat_id}] sem tags", "Tags ajudam na busca e matching")

        # Verificar base_legal
        base_legal = cat.get("base_legal", [])
        for bl in base_legal:
            if bl.get("link"):
                check(f"Cat [{cat_id}] lei '{bl.get('lei', '?')}' tem link válido",
                      bl["link"].startswith("http"))

        # Verificar links
        links = cat.get("links", [])
        for link in links:
            check(f"Cat [{cat_id}] link '{link.get('titulo', '?')}' tem URL",
                  bool(link.get("url")) and link["url"].startswith("http"))

    # IDs únicos
    check("IDs de categorias são únicos", len(cat_ids) == len(cats),
          f"{len(cats)} cats, {len(cat_ids)} IDs únicos")

    # Validar fontes
    fonte_types = Counter()
    for fonte in fontes:
        check(f"Fonte '{fonte.get('nome', '?')}' tem URL",
              bool(fonte.get("url")) and fonte["url"].startswith("http"))
        fonte_types[fonte.get("tipo", "?")] += 1

    info("Fontes por tipo", str(dict(fonte_types)))

    # Validar icd.who.int presente
    has_icd = any("icd.who.int" in f.get("url", "") for f in fontes)
    check("icd.who.int presente nas fontes (OMS CID)", has_icd,
          "CRÍTICO: icd.who.int valida todos os CID")

    # Validar órgãos estaduais — cobertura de todos os estados
    ufs = {o.get("uf") for o in orgaos}
    expected_ufs = {"AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
                    "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
                    "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"}
    check("Todos os 27 estados cobertos", ufs == expected_ufs,
          f"Faltam: {expected_ufs - ufs}" if ufs != expected_ufs else "27/27")

    # Validar classificação de deficiência
    for c in classif:
        check(f"Classificação '{c.get('tipo', '?')}' tem CID-10",
              bool(c.get("cid10")))
        check(f"Classificação '{c.get('tipo', '?')}' tem CID-11",
              bool(c.get("cid11")))

    # Verificar documentos_mestre referências de categorias
    for doc in docs:
        doc_cats = doc.get("categorias", [])
        for dc in doc_cats:
            check(f"Doc '{doc.get('nome', '?')}' cat '{dc}' existe",
                  dc in cat_ids)

    # Verificar instituições referências de categorias
    for inst_item in inst:
        inst_cats = inst_item.get("categorias", [])
        for ic in inst_cats:
            check(f"Inst '{inst_item.get('nome', '?')}' cat '{ic}' existe",
                  ic in cat_ids)

    return data, cat_ids


# ════════════════════════════════════════════════
# 3. URLs — DOMÍNIOS OFICIAIS
# ════════════════════════════════════════════════
def check_urls(data):
    info("SEÇÃO 3", "VALIDAÇÃO DE URLs")

    OFICIAL_DOMAINS = (".gov.br", ".leg.br", ".jus.br", ".mp.br", ".def.br", ".mil.br")
    INTL_DOMAINS = ("icd.who.int",)

    all_urls = set()

    def extract_urls(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ("url", "link", "sefaz", "portal") and isinstance(v, str) and v.startswith("http"):
                    all_urls.add(v)
                else:
                    extract_urls(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                extract_urls(item, f"{path}[{i}]")

    extract_urls(data)

    info(f"Total URLs encontradas", str(len(all_urls)))

    non_official = []
    for url in sorted(all_urls):
        try:
            domain = urllib.parse.urlparse(url).hostname or ""
            domain = domain.lower()
            is_official = any(domain.endswith(d) for d in OFICIAL_DOMAINS)
            is_intl = any(domain == d or domain.endswith("." + d) for d in INTL_DOMAINS)
            if not is_official and not is_intl:
                non_official.append(url)
        except Exception:
            non_official.append(url)

    check("Todas as URLs são oficiais ou whitelisted",
          len(non_official) == 0,
          f"Não-oficiais: {non_official}" if non_official else f"{len(all_urls)} URLs OK")

    # Verificar duplicatas
    url_counts = Counter()
    def count_urls(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ("url", "link", "sefaz") and isinstance(v, str) and v.startswith("http"):
                    url_counts[v] += 1
                else:
                    count_urls(v)
        elif isinstance(obj, list):
            for item in obj:
                count_urls(item)
    count_urls(data)

    dupes = {url: count for url, count in url_counts.items() if count > 5}
    if dupes:
        warn("URLs com muitas duplicatas (>5 ocorrências)",
             "; ".join(f"{url}: {count}x" for url, count in sorted(dupes.items(), key=lambda x: -x[1])[:5]))
    else:
        check("Sem URLs excessivamente duplicadas", True)


# ════════════════════════════════════════════════
# 4. DICIONÁRIO PcD
# ════════════════════════════════════════════════
def check_dicionario():
    info("SEÇÃO 4", "DICIONÁRIO PcD")
    if not DICIONARIO.exists():
        warn("dicionario_pcd.json não existe")
        return

    with open(DICIONARIO, "r", encoding="utf-8") as f:
        d = json.load(f)

    deficiencias = d.get("deficiencias", [])
    leis = d.get("leis", [])
    beneficios = d.get("beneficios", [])
    keywords = d.get("keywords_master", {})
    orgaos = d.get("orgaos_denuncia", [])
    elegibilidade = d.get("elegibilidade_cruzada", {})

    check(f"Deficiências: {len(deficiencias)}", len(deficiencias) >= 10)
    check(f"Leis: {len(leis)}", len(leis) >= 20)
    check(f"Benefícios: {len(beneficios)}", len(beneficios) >= 10)
    check(f"Canais denúncia: {len(orgaos)}", len(orgaos) >= 5)

    # Keywords
    if isinstance(keywords, dict):
        total_kw = sum(len(v) for v in keywords.values() if isinstance(v, list))
        check(f"Keywords master: {total_kw} keywords em {len(keywords)} categorias",
              total_kw >= 100)
    else:
        warn("keywords_master não é dict")

    # Verificar CID em deficiências
    for defic in deficiencias:
        nome = defic.get("nome", "?")
        cid10 = defic.get("cid10", [])
        cid11 = defic.get("cid11", [])
        if defic.get("nome") not in ("Deficiência Múltipla", "Reabilitados pelo INSS", "Mobilidade Reduzida"):
            check(f"Deficiência '{nome}' tem CID-10", len(cid10) > 0)

    # Verificar URLs de leis
    for lei in leis:
        url = lei.get("url", "")
        check(f"Lei '{lei.get('nome', '?')}' URL oficial",
              url.startswith("https://") and ".gov.br" in url,
              url[:60])

    # Elegibilidade cruzada
    check("Elegibilidade cruzada presente", bool(elegibilidade))


# ════════════════════════════════════════════════
# 5. MATCHING ENGINE
# ════════════════════════════════════════════════
def check_matching_engine(cat_ids):
    info("SEÇÃO 5", "MATCHING ENGINE")
    if not MATCHING.exists():
        warn("matching_engine.json não existe")
        return

    with open(MATCHING, "r", encoding="utf-8") as f:
        m = json.load(f)

    uppercase = m.get("uppercase_only_terms", [])
    cid_map = m.get("cid_range_map", {})
    keyword_map = m.get("keyword_map", {})

    check(f"uppercase_only_terms: {len(uppercase)}", len(uppercase) >= 50)
    check(f"cid_range_map: {len(cid_map)} letras", len(cid_map) >= 5)
    check(f"keyword_map: {len(keyword_map)} keywords", len(keyword_map) >= 200)

    # Verificar categorias referenciadas no cid_range_map
    for letter, cats in cid_map.items():
        for cat_id in cats:
            check(f"CID map '{letter}' → cat '{cat_id}' existe", cat_id in cat_ids)

    # Verificar categorias referenciadas no keyword_map
    invalid_cats = set()
    for keyword, config in keyword_map.items():
        for cat_id in config.get("cats", []):
            if cat_id not in cat_ids:
                invalid_cats.add(cat_id)

    check("keyword_map: todas as categorias existem",
          len(invalid_cats) == 0,
          f"Categorias inválidas: {invalid_cats}" if invalid_cats else "")


# ════════════════════════════════════════════════
# 6. SEO — META TAGS, JSON-LD, SITEMAP
# ════════════════════════════════════════════════
def check_seo():
    info("SEÇÃO 6", "SEO — META TAGS, JSON-LD, SITEMAP")
    html = INDEX_HTML.read_text(encoding="utf-8")

    # Meta tags essenciais
    seo_checks = {
        "title tag": r"<title>[^<]+</title>",
        "meta description": r'<meta\s+name="description"',
        "meta keywords": r'<meta\s+name="keywords"',
        "canonical link": r'<link\s+rel="canonical"',
        "og:title": r'property="og:title"',
        "og:description": r'property="og:description"',
        "og:image": r'property="og:image"',
        "og:url": r'property="og:url"',
        "og:type": r'property="og:type"',
        "og:locale": r'property="og:locale"',
        "twitter:card": r'name="twitter:card"',
        "twitter:title": r'name="twitter:title"',
        "twitter:description": r'name="twitter:description"',
        "twitter:image": r'name="twitter:image"',
        "robots meta": r'name="robots"',
        "google-site-verification": r'name="google-site-verification"',
        "theme-color": r'name="theme-color"',
        "viewport": r'name="viewport"',
        "lang=pt-BR": r'lang="pt-BR"',
    }
    for name, pattern in seo_checks.items():
        check(f"SEO: {name}", bool(re.search(pattern, html)))

    # JSON-LD schemas
    ld_schemas = re.findall(r'"@type"\s*:\s*"([^"]+)"', html)
    check("JSON-LD WebApplication presente", "WebApplication" in ld_schemas)
    check("JSON-LD FAQPage presente", "FAQPage" in ld_schemas)
    check("JSON-LD GovernmentService presente", "GovernmentService" in ld_schemas)
    check("JSON-LD Organization presente", "Organization" in ld_schemas)
    check("JSON-LD BreadcrumbList presente", "BreadcrumbList" in ld_schemas)
    check("JSON-LD ItemList presente", "ItemList" in ld_schemas)
    ld_unique = sorted(set(s for s in ld_schemas if s[0].isupper() and len(s) > 3))
    info("JSON-LD schemas encontrados", ", ".join(ld_unique))

    # FAQPage count
    faq_count = html.count('"@type": "Question"')
    check(f"FAQPage: {faq_count} perguntas (≥10)", faq_count >= 10)

    # Heading structure
    h1_count = len(re.findall(r"<h1[^>]*>", html))
    check(f"H1 tag: {h1_count} (deve ser 1)", h1_count == 1)

    # Sitemap.xml
    if SITEMAP.exists():
        sitemap_content = SITEMAP.read_text(encoding="utf-8")
        url_count = sitemap_content.count("<loc>")
        check(f"Sitemap: {url_count} URLs (≥10)", url_count >= 10,
              "Sitemap deve ter URLs de seções e categorias")
    else:
        check("Sitemap existe", False)

    # Robots.txt
    if ROBOTS.exists():
        robots = ROBOTS.read_text(encoding="utf-8")
        check("Robots.txt referencia sitemap", "Sitemap:" in robots)
        check("Robots.txt permite Googlebot", "Googlebot" in robots or "User-agent: *" in robots)
    else:
        check("Robots.txt existe", False)

    # Pre-rendered SEO content
    check("Conteúdo pré-renderizado para crawlers", "seo-content" in html,
          "Conteúdo semântico visível para buscadores mesmo sem JS")

    # Noscript content
    check("Noscript com conteúdo rico", "<noscript>" in html and "BPC" in html.split("<noscript>")[1].split("</noscript>")[0] if "<noscript>" in html else False,
          "Conteúdo noscript ajuda no SEO de SPAs")

    # Keywords SEO
    keywords_meta = re.search(r'name="keywords"\s+content="([^"]+)"', html)
    if keywords_meta:
        kw = keywords_meta.group(1)
        target_terms = ["PcD", "autismo", "TEA", "deficiente", "BPC", "CIPTEA",
                       "Down", "TDAH", "isenção", "passe livre"]
        for term in target_terms:
            check(f"Keyword '{term}' no meta keywords",
                  term.lower() in kw.lower())


# ════════════════════════════════════════════════
# 7. ACESSIBILIDADE
# ════════════════════════════════════════════════
def check_accessibility():
    info("SEÇÃO 7", "ACESSIBILIDADE")
    html = INDEX_HTML.read_text(encoding="utf-8")

    checks = {
        "Skip link": r'class="skip-link"',
        "aria-label no nav": r'<nav[^>]+aria-label',
        "aria-live region": r'aria-live="polite"',
        "role=dialog no modal": r'role="dialog"',
        "aria-modal": r'aria-modal="true"',
        "role=progressbar": r'role="progressbar"',
        "sr-only class": r'class="sr-only"',
        "alt text em imagens": r'<img[^>]+alt="[^"]*"',
        "VLibras integrado": r'vlibras',
        "Painel acessibilidade": r'a11y-drawer',
        "Controle de fonte": r'a11yFontIncrease',
        "Alto contraste": r'a11yContrast',
        "Leitura em voz alta": r'a11yReadAloud',
        "Libras button": r'a11yLibras',
    }
    for name, pattern in checks.items():
        check(f"A11y: {name}", bool(re.search(pattern, html, re.IGNORECASE)))

    # WCAG checkpoints
    check("A11y: lang definido", 'lang="pt-BR"' in html)
    check("A11y: charset UTF-8", 'charset="UTF-8"' in html)


# ════════════════════════════════════════════════
# 8. SEGURANÇA
# ════════════════════════════════════════════════
def check_security():
    info("SEÇÃO 8", "SEGURANÇA E LGPD")
    html = INDEX_HTML.read_text(encoding="utf-8")

    checks = {
        "CSP (Content-Security-Policy)": r'Content-Security-Policy',
        "X-Content-Type-Options": r'X-Content-Type-Options',
        "Referrer-Policy": r'Referrer-Policy',
        "Permissions-Policy": r'Permissions-Policy',
        "Aviso LGPD no modal": r'LGPD',
        "Disclaimer presente": r'disclaimerModal',
    }
    for name, pattern in checks.items():
        check(f"Segurança: {name}", bool(re.search(pattern, html)))

    # CSP policy check
    csp_match = re.search(r'content="(default-src[^"]+)"', html)
    if csp_match:
        csp = csp_match.group(1)
        check("CSP: default-src 'none'", "default-src 'none'" in csp)
        check("CSP: script-src definido", "script-src" in csp)
        check("CSP: form-action 'none'", "form-action 'none'" in csp)
    else:
        warn("CSP: política não encontrada")


# ════════════════════════════════════════════════
# 9. HTML SEMÂNTICO
# ════════════════════════════════════════════════
def check_html_structure():
    info("SEÇÃO 9", "HTML — ESTRUTURA SEMÂNTICA")
    html = INDEX_HTML.read_text(encoding="utf-8")

    sections = {
        "inicio": "Seção início/hero",
        "busca": "Seção busca",
        "categorias": "Seção categorias",
        "checklist": "Seção primeiros passos",
        "documentos": "Seção documentos",
        "links": "Seção sites oficiais",
        "classificacao": "Seção CID-10/11",
        "orgaos-estaduais": "Seção órgãos estaduais",
        "instituicoes": "Seção instituições",
        "transparencia": "Seção transparência",
    }
    for section_id, desc in sections.items():
        check(f"HTML: {desc} (#{section_id})",
              f'id="{section_id}"' in html)

    # Navigation links
    nav_links = re.findall(r'href="#([^"]+)"', html)
    for section_id in sections:
        check(f"Nav: link para #{section_id}",
              section_id in nav_links)

    # Manifest
    if MANIFEST.exists():
        with open(MANIFEST, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        check("Manifest: name presente", bool(manifest.get("name")))
        check("Manifest: icons presente", bool(manifest.get("icons")))
        check("Manifest: start_url presente", bool(manifest.get("start_url")))
        check("Manifest: display presente", bool(manifest.get("display")))


# ════════════════════════════════════════════════
# 10. APP.JS — REFERÊNCIAS DE DADOS
# ════════════════════════════════════════════════
def check_app_js(cat_ids):
    info("SEÇÃO 10", "APP.JS — REFERÊNCIAS E FUNCIONALIDADES")
    if not APP_JS.exists():
        check("app.js existe", False)
        return

    js = APP_JS.read_text(encoding="utf-8")

    functions = {
        "loadData": "Carregamento de dados",
        "renderCategories": "Renderização de categorias",
        "showDetalhe": "Detalhe de categoria",
        "performSearch": "Busca",
        "renderTransparency": "Transparência",
        "renderLinksUteis": "Links úteis",
        "renderClassificacao": "Classificação CID",
        "renderOrgaosEstaduais": "Órgãos estaduais",
        "renderInstituicoes": "Instituições",
        "analyzeSelectedDocuments": "Análise de documentos",
        "matchRights": "Matching de direitos",
        "exportPdf": "Exportar PDF",
        "setupSearch": "Setup de busca",
    }
    for func, desc in functions.items():
        check(f"JS: função '{func}' ({desc})",
              func in js)

    # Verifica referências de dados
    data_refs = {
        "direitos.json": "data/direitos.json",
        "matching_engine.json": "data/matching_engine.json",
    }
    for name, path in data_refs.items():
        check(f"JS: referência a '{name}'", path in js)

    # Verifica que IndexedDB é usado para docs
    check("JS: IndexedDB para documentos", "indexedDB" in js or "openDB" in js)

    # Verifica criptografia
    check("JS: AES/crypto para docs", "crypto" in js.lower() or "AES" in js)

    # Verifica deep linking
    check("JS: pushState para deep links", "pushState" in js)

    # Verifica WhatsApp share
    check("JS: compartilhar WhatsApp", "whatsapp" in js.lower())

    info("Total linhas app.js", str(js.count('\n') + 1))


# ════════════════════════════════════════════════
# 11. COERÊNCIA ENTRE DADOS
# ════════════════════════════════════════════════
def check_cross_references(data, cat_ids):
    info("SEÇÃO 11", "COERÊNCIA ENTRE DADOS")

    # Checar se matching_engine.json categorias fazem referência a direitos.json
    if MATCHING.exists():
        with open(MATCHING, "r", encoding="utf-8") as f:
            m = json.load(f)

        # Coletar todas as categorias referenciadas
        all_ref_cats = set()
        for letter, cats in m.get("cid_range_map", {}).items():
            all_ref_cats.update(cats)
        for keyword, config in m.get("keyword_map", {}).items():
            all_ref_cats.update(config.get("cats", []))

        missing = all_ref_cats - cat_ids
        check("Matching engine: todas as cats existem em direitos.json",
              len(missing) == 0,
              f"Ausentes: {missing}" if missing else f"{len(all_ref_cats)} refs OK")

    # Checar dicionário vs direitos.json
    if DICIONARIO.exists():
        with open(DICIONARIO, "r", encoding="utf-8") as f:
            d = json.load(f)

        dict_beneficios = {b.get("nome", "").lower() for b in d.get("beneficios", [])}
        cat_titles = {c.get("titulo", "").lower() for c in data.get("categorias", [])}

        # Não exigir match exato — apenas verificar que há overlap
        overlap = sum(1 for b in dict_beneficios
                      if any(word in t for t in cat_titles
                             for word in b.split() if len(word) > 4))
        check(f"Dicionário ↔ direitos.json: overlap de benefícios",
              overlap >= 5, f"{overlap} benefícios com overlap")


# ════════════════════════════════════════════════
# 12. RESUMO E RELATÓRIO
# ════════════════════════════════════════════════
def print_report():
    print("\n" + "=" * 70)
    print("🔍 AVALIAÇÃO 360° — NOSSODIREITO")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    current_section = ""
    for icon, name, detail in results:
        if icon == "ℹ️" and name.startswith("SEÇÃO"):
            current_section = detail
            print(f"\n{'─' * 60}")
            print(f"  {name}: {detail}")
            print(f"{'─' * 60}")
            continue
        elif icon == "ℹ️":
            print(f"  {icon} {name}: {detail}")
            continue

        detail_str = f" — {detail}" if detail else ""
        print(f"  {icon} {name}{detail_str}")

    print(f"\n{'═' * 70}")
    print(f"📊 RESULTADO FINAL")
    print(f"{'═' * 70}")
    print(f"  Total de verificações: {total_checks}")
    print(f"  ✅ Aprovados:  {passed}")
    print(f"  ⚠️  Avisos:     {warnings}")
    print(f"  ❌ Falhas:     {errors}")

    pct = (passed / total_checks * 100) if total_checks > 0 else 0
    print(f"\n  📈 Nota: {pct:.1f}% ({passed}/{total_checks})")

    if errors == 0:
        print(f"\n  🏆 SITE APROVADO — Todas as verificações passaram!")
    elif errors <= 3:
        print(f"\n  ⚠️  SITE QUASE PERFEITO — {errors} item(ns) a corrigir")
    else:
        print(f"\n  ❌ ATENÇÃO — {errors} falha(s) encontrada(s)")

    print("=" * 70)
    return errors


def main():
    check_file_structure()
    data, cat_ids = check_direitos_json()
    check_urls(data)
    check_dicionario()
    check_matching_engine(cat_ids)
    check_seo()
    check_accessibility()
    check_security()
    check_html_structure()
    check_app_js(cat_ids)
    check_cross_references(data, cat_ids)
    error_count = print_report()
    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
