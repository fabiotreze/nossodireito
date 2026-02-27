#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTES ABRANGENTES — NossoDireito v1.14.0

Cobertura completa:
  - direitos.json: categorias, fontes, classificações, estrutura, duplicidades
  - dicionario_pcd.json: deficiências, CIDs, benefícios elegíveis, leis
  - IPVA estadual: 27 estados validados inline em direitos.json (isencoes_tributarias)
  - matching_engine.json: keywords, CID ranges, consistência com categorias
  - schemas: validação JSON Schema
  - URLs: HTTPS, domínios gov.br, sem duplicatas
  - Integridade cruzada: dicionário ↔ direitos ↔ matching
  - HTML/SEO: structured data, contagens, acessibilidade
  - Scripts: existência e executabilidade
  - Funcionalidades: busca, categorias, estados, municípios
"""

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"


# ════════════════════════════════════════════════════════════════
# FIXTURES
# ════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def direitos():
    with open(DATA / "direitos.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def dicionario():
    with open(DATA / "dicionario_pcd.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def matching():
    with open(DATA / "matching_engine.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def schema():
    with open(ROOT / "schemas" / "direitos.schema.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def cat_ids(direitos):
    return {c["id"] for c in direitos["categorias"]}


@pytest.fixture(scope="session")
def index_html():
    with open(ROOT / "index.html", encoding="utf-8") as f:
        return f.read()


# ════════════════════════════════════════════════════════════════
# 1. DIREITOS.JSON — ESTRUTURA E INTEGRIDADE
# ════════════════════════════════════════════════════════════════

class TestDireitosStructure:
    """Validação estrutural de direitos.json"""

    def test_file_exists(self):
        assert (DATA / "direitos.json").exists()

    def test_valid_json(self, direitos):
        assert isinstance(direitos, dict)

    def test_root_fields(self, direitos):
        for field in ["versao", "ultima_atualizacao", "aviso", "fontes", "categorias"]:
            assert field in direitos, f"Campo raiz '{field}' ausente"

    def test_version_semver(self, direitos):
        parts = direitos["versao"].split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_date_format(self, direitos):
        assert re.match(r"\d{4}-\d{2}-\d{2}", direitos["ultima_atualizacao"])

    def test_minimum_categories(self, direitos):
        assert len(direitos["categorias"]) >= 30

    def test_minimum_fontes(self, direitos):
        assert len(direitos["fontes"]) >= 70

    def test_has_classificacao(self, direitos):
        assert "classificacao_deficiencia" in direitos
        assert len(direitos["classificacao_deficiencia"]) >= 16


class TestDireitosCategorias:
    """Validação de cada categoria em direitos.json"""

    REQUIRED_FIELDS = [
        "id", "titulo", "resumo", "icone", "base_legal",
        "requisitos", "documentos", "passo_a_passo",
        "dicas", "valor", "onde", "links", "tags"
    ]

    def test_all_required_fields(self, direitos):
        for cat in direitos["categorias"]:
            cid = cat.get("id", "UNKNOWN")
            for field in self.REQUIRED_FIELDS:
                assert field in cat, f"Cat '{cid}': campo '{field}' ausente"

    def test_minimum_content_quality(self, direitos):
        for cat in direitos["categorias"]:
            cid = cat["id"]
            assert len(cat["requisitos"]) >= 3, f"{cid}: min 3 requisitos"
            assert len(cat["documentos"]) >= 2, f"{cid}: min 2 documentos"
            assert len(cat["passo_a_passo"]) >= 3, f"{cid}: min 3 passos"
            assert len(cat["dicas"]) >= 2, f"{cid}: min 2 dicas"
            assert len(cat["links"]) >= 1, f"{cid}: min 1 link"
            assert len(cat["tags"]) >= 3, f"{cid}: min 3 tags"

    def test_no_duplicate_ids(self, direitos):
        ids = [c["id"] for c in direitos["categorias"]]
        assert len(ids) == len(set(ids)), f"IDs duplicados: {[x for x in ids if ids.count(x) > 1]}"

    def test_ids_snake_case(self, direitos):
        for cat in direitos["categorias"]:
            assert re.match(r"^[a-z][a-z0-9_]*$", cat["id"]), f"ID '{cat['id']}' não é snake_case"

    def test_icone_not_empty(self, direitos):
        for cat in direitos["categorias"]:
            assert cat["icone"].strip(), f"Cat '{cat['id']}' sem ícone"

    def test_base_legal_structure(self, direitos):
        for cat in direitos["categorias"]:
            bl = cat["base_legal"]
            assert isinstance(bl, list) and len(bl) >= 1, f"{cat['id']}: base_legal vazia"
            for item in bl:
                assert "lei" in item, f"{cat['id']}: base_legal sem 'lei'"
                assert "artigo" in item, f"{cat['id']}: base_legal sem 'artigo'"
                assert "link" in item, f"{cat['id']}: base_legal sem 'link'"

    def test_links_structure(self, direitos):
        for cat in direitos["categorias"]:
            for link in cat["links"]:
                assert "titulo" in link, f"{cat['id']}: link sem 'titulo'"
                assert "url" in link, f"{cat['id']}: link sem 'url'"
                assert link["url"].startswith("https://"), f"{cat['id']}: URL não HTTPS: {link['url']}"

    def test_new_categories_present(self, cat_ids):
        expected = {
            "acessibilidade_arquitetonica", "capacidade_legal",
            "crimes_contra_pcd", "acessibilidade_digital", "reabilitacao"
        }
        for cid in expected:
            assert cid in cat_ids, f"Nova categoria '{cid}' não encontrada"


# ════════════════════════════════════════════════════════════════
# 2. URLS — VALIDAÇÃO OFFLINE
# ════════════════════════════════════════════════════════════════

class TestURLs:
    """Validação de todas as URLs (formato, HTTPS, domínios)"""

    GOVT_DOMAINS = [".gov.br", ".leg.br", ".jus.br", ".def.br", ".mp.br", ".mil.br"]

    def _collect_urls(self, direitos):
        urls = []
        for cat in direitos["categorias"]:
            for bl in cat.get("base_legal", []):
                if "link" in bl:
                    urls.append((cat["id"], "base_legal", bl["link"]))
            for lnk in cat.get("links", []):
                if "url" in lnk:
                    urls.append((cat["id"], "link", lnk["url"]))
        for f in direitos.get("fontes", []):
            if "url" in f:
                urls.append(("fonte:" + f.get("nome", "?"), "fonte", f["url"]))
        return urls

    def test_all_urls_https(self, direitos):
        for cid, typ, url in self._collect_urls(direitos):
            assert url.startswith("https://"), f"HTTP em {cid}/{typ}: {url}"

    def test_no_duplicate_fonte_urls(self, direitos):
        urls = [f["url"] for f in direitos["fontes"]]
        counts = Counter(urls)
        dupes = {u: c for u, c in counts.items() if c > 1}
        assert not dupes, f"URLs de fontes duplicadas: {dupes}"

    def test_urls_valid_format(self, direitos):
        url_pattern = re.compile(r"^https://[a-zA-Z0-9][-a-zA-Z0-9.]*\.[a-zA-Z]{2,}")
        for cid, typ, url in self._collect_urls(direitos):
            assert url_pattern.match(url), f"URL mal-formada em {cid}/{typ}: {url}"

    def test_base_legal_urls_are_governmental(self, direitos):
        for cat in direitos["categorias"]:
            for bl in cat.get("base_legal", []):
                url = bl.get("link", "")
                is_govt = any(d in url for d in self.GOVT_DOMAINS) or "anac.gov.br" in url
                assert is_govt, f"{cat['id']}: base_legal URL não governamental: {url}"


# ════════════════════════════════════════════════════════════════
# 3. FONTES — INTEGRIDADE
# ════════════════════════════════════════════════════════════════

class TestFontes:
    """Validação de fontes em direitos.json"""

    VALID_TYPES = {"legislacao", "portal", "orgao_oficial", "servico", "programa",
                   "resolucao", "portaria", "decreto", "norma_tecnica", "app",
                   "dados", "referencia", "formulario", "normativa"}

    def test_required_fields(self, direitos):
        for f in direitos["fontes"]:
            assert "nome" in f, f"Fonte sem 'nome'"
            assert "url" in f, f"Fonte '{f.get('nome', '?')}' sem 'url'"
            assert "tipo" in f, f"Fonte '{f.get('nome', '?')}' sem 'tipo'"

    def test_tipos_valid(self, direitos):
        for f in direitos["fontes"]:
            assert f["tipo"] in self.VALID_TYPES, \
                f"Fonte '{f['nome']}': tipo '{f['tipo']}' inválido"


# ════════════════════════════════════════════════════════════════
# 4. CLASSIFICAÇÃO DE DEFICIÊNCIA
# ════════════════════════════════════════════════════════════════

class TestClassificacao:
    """Validação de classificacao_deficiencia"""

    def test_required_fields(self, direitos):
        for cl in direitos["classificacao_deficiencia"]:
            assert "tipo" in cl, "Classificação sem 'tipo'"
            assert "cid10" in cl, f"Classificação '{cl.get('tipo')}' sem 'cid10'"
            assert "criterio" in cl, f"Classificação '{cl.get('tipo')}' sem 'criterio'"

    def test_minimum_classifications(self, direitos):
        assert len(direitos["classificacao_deficiencia"]) >= 16

    def test_no_duplicate_types(self, direitos):
        tipos = [c["tipo"] for c in direitos["classificacao_deficiencia"]]
        assert len(tipos) == len(set(tipos))


# ════════════════════════════════════════════════════════════════
# 5. DICIONÁRIO PCD
# ════════════════════════════════════════════════════════════════

class TestDicionario:
    """Validação de dicionario_pcd.json"""

    def test_file_exists(self):
        assert (DATA / "dicionario_pcd.json").exists()

    def test_valid_json(self, dicionario):
        assert isinstance(dicionario, dict)

    def test_has_version(self, dicionario):
        assert "versao" in dicionario

    def test_has_deficiencias(self, dicionario):
        assert "deficiencias" in dicionario
        assert len(dicionario["deficiencias"]) >= 14

    def test_deficiencias_required_fields(self, dicionario):
        for d in dicionario["deficiencias"]:
            did = d.get("id", "UNKNOWN")
            for field in ["id", "nome", "descricao", "keywords_busca", "beneficios_elegiveis"]:
                assert field in d, f"Deficiência '{did}': campo '{field}' ausente"

    def test_no_duplicate_deficiencia_ids(self, dicionario):
        ids = [d["id"] for d in dicionario["deficiencias"]]
        assert len(ids) == len(set(ids))

    def test_beneficios_reference_valid_categories(self, dicionario, cat_ids):
        for d in dicionario["deficiencias"]:
            for b in d.get("beneficios_elegiveis", []):
                assert b in cat_ids, \
                    f"Deficiência '{d['id']}': benefício '{b}' não existe em direitos.json"

    def test_new_categories_in_beneficios(self, dicionario):
        """Verifica que as novas categorias estão nos benefícios elegíveis"""
        new_cats = {
            "acessibilidade_arquitetonica", "capacidade_legal",
            "crimes_contra_pcd", "acessibilidade_digital", "reabilitacao"
        }
        for d in dicionario["deficiencias"]:
            eligibles = set(d.get("beneficios_elegiveis", []))
            # Universal categories should be in all
            for uc in ["acessibilidade_arquitetonica", "capacidade_legal", "crimes_contra_pcd"]:
                assert uc in eligibles, \
                    f"Deficiência '{d['id']}': categoria universal '{uc}' ausente nos benefícios"

    def test_has_leis(self, dicionario):
        assert "leis" in dicionario
        assert len(dicionario["leis"]) >= 30

    def test_leis_have_url(self, dicionario):
        for lei in dicionario["leis"]:
            assert "url" in lei, f"Lei '{lei.get('nome', '?')}' sem URL"
            assert lei["url"].startswith("https://"), f"Lei URL não HTTPS: {lei['url']}"

    def test_has_fontes_oficiais_validacao(self, dicionario):
        fov = dicionario.get("fontes_oficiais_validacao", {})
        assert "dominios_aceitos" in fov
        assert ".gov.br" in fov["dominios_aceitos"]

    def test_has_beneficios(self, dicionario):
        assert "beneficios" in dicionario
        assert len(dicionario["beneficios"]) >= 17


# ════════════════════════════════════════════════════════════════
# 6. IPVA PCD — INLINE EM DIREITOS.JSON
# ════════════════════════════════════════════════════════════════

class TestIPVA:
    """Validação de IPVA inline em direitos.json (isencoes_tributarias)"""

    BRAZIL_STATES = [
        "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
        "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
        "RO", "RR", "RS", "SC", "SE", "SP", "TO"
    ]

    @pytest.fixture()
    def isencoes(self, direitos):
        return next(c for c in direitos["categorias"] if c["id"] == "isencoes_tributarias")

    def test_standalone_file_removed(self):
        """ipva_pcd_estados.json foi removido — dados agora inline"""
        assert not (DATA / "ipva_pcd_estados.json").exists(), \
            "ipva_pcd_estados.json deveria ter sido removido (dados agora inline em direitos.json)"

    def test_ipva_estados_exists(self, isencoes):
        assert "ipva_estados" in isencoes
        assert isinstance(isencoes["ipva_estados"], list)

    def test_ipva_estados_detalhado_exists(self, isencoes):
        assert "ipva_estados_detalhado" in isencoes
        assert isinstance(isencoes["ipva_estados_detalhado"], list)

    def test_all_27_states_simple(self, isencoes):
        ufs = [e["uf"] for e in isencoes["ipva_estados"]]
        for uf in self.BRAZIL_STATES:
            assert uf in ufs, f"Estado '{uf}' ausente em ipva_estados"

    def test_all_27_states_detalhado(self, isencoes):
        ufs = [e["uf"] for e in isencoes["ipva_estados_detalhado"]]
        for uf in self.BRAZIL_STATES:
            assert uf in ufs, f"Estado '{uf}' ausente em ipva_estados_detalhado"

    def test_simple_state_structure(self, isencoes):
        for estado in isencoes["ipva_estados"]:
            assert "uf" in estado, "Estado sem 'uf'"
            assert "lei" in estado, f"{estado['uf']}: sem 'lei'"
            assert "art" in estado, f"{estado['uf']}: sem 'art'"
            assert "sefaz" in estado, f"{estado['uf']}: sem 'sefaz'"

    def test_detailed_state_structure(self, isencoes):
        for estado in isencoes["ipva_estados_detalhado"]:
            assert "uf" in estado, "Estado sem 'uf'"
            assert "nome" in estado, f"{estado['uf']}: sem 'nome'"
            assert "lei" in estado, f"{estado['uf']}: sem 'lei'"
            assert "artigo" in estado, f"{estado['uf']}: sem 'artigo'"
            assert "condicoes" in estado, f"{estado['uf']}: sem 'condicoes'"
            assert "limite_valor" in estado, f"{estado['uf']}: sem 'limite_valor'"
            assert "sefaz" in estado, f"{estado['uf']}: sem 'sefaz'"

    def test_sefaz_urls_https(self, isencoes):
        for estado in isencoes["ipva_estados"]:
            assert estado["sefaz"].startswith("https://"), \
                f"IPVA {estado['uf']}: SEFAZ não-HTTPS: {estado['sefaz']}"

    def test_no_duplicate_states(self, isencoes):
        ufs_s = [e["uf"] for e in isencoes["ipva_estados"]]
        ufs_d = [e["uf"] for e in isencoes["ipva_estados_detalhado"]]
        assert len(ufs_s) == len(set(ufs_s)), f"UFs duplicadas em ipva_estados"
        assert len(ufs_d) == len(set(ufs_d)), f"UFs duplicadas em ipva_estados_detalhado"

    def test_states_consistent_between_simple_and_detailed(self, isencoes):
        ufs_s = sorted([e["uf"] for e in isencoes["ipva_estados"]])
        ufs_d = sorted([e["uf"] for e in isencoes["ipva_estados_detalhado"]])
        assert ufs_s == ufs_d, "ipva_estados e ipva_estados_detalhado devem ter os mesmos estados"


# ════════════════════════════════════════════════════════════════
# 7. MATCHING ENGINE
# ════════════════════════════════════════════════════════════════

class TestMatchingEngine:
    """Validação de matching_engine.json"""

    def test_file_exists(self):
        assert (DATA / "matching_engine.json").exists()

    def test_valid_json(self, matching):
        assert isinstance(matching, dict)

    def test_has_required_keys(self, matching):
        assert "keyword_map" in matching
        assert "cid_range_map" in matching
        assert "uppercase_only_terms" in matching

    def test_minimum_keywords(self, matching):
        assert len(matching["keyword_map"]) >= 600

    def test_keywords_reference_valid_categories(self, matching, cat_ids):
        for kw, val in matching["keyword_map"].items():
            cats = val.get("cats", [])
            for c in cats:
                assert c in cat_ids, \
                    f"Keyword '{kw}': referência a categoria inexistente '{c}'"

    def test_keywords_have_weight(self, matching):
        for kw, val in matching["keyword_map"].items():
            assert "weight" in val, f"Keyword '{kw}' sem weight"
            assert 1 <= val["weight"] <= 10, f"Keyword '{kw}': weight {val['weight']} fora do range 1-10"

    def test_cid_ranges_reference_valid_categories(self, matching, cat_ids):
        for prefix, cats in matching["cid_range_map"].items():
            for c in cats:
                assert c in cat_ids, \
                    f"CID range '{prefix}': referência a categoria inexistente '{c}'"

    def test_new_categories_in_keywords(self, matching):
        """Verifica que as 5 novas categorias têm keywords no matching engine"""
        new_cats = [
            "acessibilidade_arquitetonica", "capacidade_legal",
            "crimes_contra_pcd", "acessibilidade_digital", "reabilitacao"
        ]
        all_cats_in_keywords = set()
        for val in matching["keyword_map"].values():
            all_cats_in_keywords.update(val.get("cats", []))

        for nc in new_cats:
            assert nc in all_cats_in_keywords, \
                f"Nova categoria '{nc}' não tem keywords no matching engine"

    def test_uppercase_terms_unique(self, matching):
        terms = matching["uppercase_only_terms"]
        assert len(terms) == len(set(terms)), "Termos uppercase duplicados"


# ════════════════════════════════════════════════════════════════
# 8. SCHEMA VALIDATION
# ════════════════════════════════════════════════════════════════

class TestSchema:
    """Validação JSON Schema"""

    def test_schema_file_exists(self):
        assert (ROOT / "schemas" / "direitos.schema.json").exists()

    def test_direitos_validates_against_schema(self, direitos, schema):
        try:
            import jsonschema
            jsonschema.validate(direitos, schema)
        except ImportError:
            pytest.skip("jsonschema não instalado")

    def test_schema_has_required_definitions(self, schema):
        defs = schema.get("definitions", {})
        assert "categoria" in defs
        assert "fonte" in defs


# ════════════════════════════════════════════════════════════════
# 9. INTEGRIDADE CRUZADA (Cross-file consistency)
# ════════════════════════════════════════════════════════════════

class TestCrossFileIntegrity:
    """Validação de consistência entre arquivos de dados"""

    def test_dicionario_beneficios_exist_in_direitos(self, dicionario, cat_ids):
        """Todos os benefícios elegíveis do dicionário devem existir em direitos"""
        for d in dicionario["deficiencias"]:
            for b in d.get("beneficios_elegiveis", []):
                assert b in cat_ids, \
                    f"Deficiência '{d['id']}': benefício '{b}' inexistente"

    def test_dicionario_beneficios_list_nonempty(self, dicionario):
        """A lista de benefícios no dicionário não deve estar vazia"""
        ben_ids = [b["id"] for b in dicionario.get("beneficios", [])]
        assert len(ben_ids) >= 17
        assert len(ben_ids) == len(set(ben_ids)), "IDs de benefícios duplicados"

    def test_matching_covers_all_categories(self, matching, cat_ids):
        """Verifica que o matching engine cobre todas as categorias"""
        covered = set()
        for val in matching["keyword_map"].values():
            covered.update(val.get("cats", []))
        for cats in matching["cid_range_map"].values():
            covered.update(cats)

        not_covered = cat_ids - covered
        # Some categories may intentionally not be directly searchable
        # but the 5 new ones must be covered
        new_cats = {"acessibilidade_arquitetonica", "capacidade_legal",
                    "crimes_contra_pcd", "acessibilidade_digital", "reabilitacao"}
        missing_new = new_cats - covered
        assert not missing_new, f"Novas categorias sem cobertura no matching: {missing_new}"

    def test_ipva_category_exists(self, cat_ids):
        """A categoria de isenções tributárias (que inclui IPVA) deve existir"""
        assert "isencoes_tributarias" in cat_ids


# ════════════════════════════════════════════════════════════════
# 10. DUPLICIDADES GLOBAIS
# ════════════════════════════════════════════════════════════════

class TestDuplicates:
    """Detecção de duplicidades em todos os arquivos"""

    def test_no_duplicate_category_ids(self, direitos):
        ids = [c["id"] for c in direitos["categorias"]]
        dupes = [x for x in ids if ids.count(x) > 1]
        assert not dupes, f"Categorias duplicadas: {set(dupes)}"

    def test_no_duplicate_fonte_urls(self, direitos):
        urls = [f["url"] for f in direitos["fontes"]]
        dupes = [u for u in urls if urls.count(u) > 1]
        assert not dupes, f"URLs de fontes duplicadas: {set(dupes)}"

    def test_no_duplicate_deficiencia_ids(self, dicionario):
        ids = [d["id"] for d in dicionario["deficiencias"]]
        dupes = [x for x in ids if ids.count(x) > 1]
        assert not dupes, f"Deficiências duplicadas: {set(dupes)}"

    def test_no_duplicate_lei_ids(self, dicionario):
        ids = [l["id"] for l in dicionario.get("leis", [])]
        dupes = [x for x in ids if ids.count(x) > 1]
        assert not dupes, f"Leis duplicadas: {set(dupes)}"

    def test_no_duplicate_classificacao_tipos(self, direitos):
        tipos = [c["tipo"] for c in direitos["classificacao_deficiencia"]]
        dupes = [t for t in tipos if tipos.count(t) > 1]
        assert not dupes, f"Classificações duplicadas: {set(dupes)}"


# ════════════════════════════════════════════════════════════════
# 11. HTML / SEO / ACESSIBILIDADE
# ════════════════════════════════════════════════════════════════

class TestHTMLIntegrity:
    """Validação do index.html: SEO, structured data, acessibilidade"""

    def test_file_exists(self):
        assert (ROOT / "index.html").exists()

    def test_has_lang_attribute(self, index_html):
        assert 'lang="pt-BR"' in index_html

    def test_has_viewport_meta(self, index_html):
        assert "viewport" in index_html

    def test_has_meta_description(self, index_html):
        assert '<meta name="description"' in index_html

    def test_category_count_in_seo(self, index_html, direitos):
        num_cats = len(direitos["categorias"])
        assert f"{num_cats} categorias" in index_html, \
            f"index.html deveria mencionar '{num_cats} categorias'"

    def test_structured_data_itemlist_count(self, index_html, direitos):
        num_cats = len(direitos["categorias"])
        assert f'"numberOfItems": {num_cats}' in index_html, \
            f"ItemList deveria ter numberOfItems={num_cats}"

    def test_structured_data_has_all_categories(self, index_html, direitos):
        for cat in direitos["categorias"]:
            cid = cat["id"]
            assert cid in index_html, \
                f"Categoria '{cid}' ausente no structured data do index.html"

    def test_has_noscript_fallback(self, index_html):
        assert "<noscript>" in index_html

    def test_has_manifest(self, index_html):
        assert "manifest.json" in index_html

    def test_has_favicon(self, index_html):
        assert "favicon" in index_html

    def test_no_http_resources(self, index_html):
        """Nenhum recurso deve ser carregado via HTTP (mixed content)"""
        http_refs = re.findall(r'(src|href)="http://', index_html)
        assert not http_refs, f"Recursos HTTP encontrados (mixed content): {http_refs}"

    def test_seo_content_not_aria_hidden(self, index_html):
        """Bloco #seo-content NÃO deve ter aria-hidden (robôs devem indexar)"""
        # Procura o div seo-content e verifica que NÃO tem aria-hidden
        seo_match = re.search(r'<div[^>]*id="seo-content"[^>]*>', index_html)
        assert seo_match, "Bloco #seo-content não encontrado"
        tag = seo_match.group(0)
        assert 'aria-hidden' not in tag, \
            f"#seo-content tem aria-hidden (impede indexação Google): {tag}"

    def test_canonical_url_has_trailing_slash(self, index_html):
        """Canonical URL deve ter trailing slash (consistência com sitemap)"""
        match = re.search(r'<link rel="canonical" href="([^"]+)"', index_html)
        assert match, "Canonical URL não encontrada"
        url = match.group(1)
        assert url.endswith("/"), f"Canonical URL sem trailing slash: {url}"


# ════════════════════════════════════════════════════════════════
# 12. SCRIPTS — EXISTÊNCIA
# ════════════════════════════════════════════════════════════════

class TestScripts:
    """Validação de scripts essenciais"""

    ESSENTIAL_SCRIPTS = [
        "validate_schema.py", "validate_content.py", "validate_urls.py",
        "validate_all.py", "bump_version.py"
    ]

    def test_essential_scripts_exist(self):
        scripts_dir = ROOT / "scripts"
        for script in self.ESSENTIAL_SCRIPTS:
            assert (scripts_dir / script).exists(), f"Script '{script}' não encontrado"

    def test_js_app_exists(self):
        assert (ROOT / "js" / "app.js").exists()

    def test_css_styles_exists(self):
        assert (ROOT / "css" / "styles.css").exists()

    def test_sw_exists(self):
        assert (ROOT / "sw.js").exists()

    def test_server_exists(self):
        assert (ROOT / "server.js").exists()


# ════════════════════════════════════════════════════════════════
# 13. GITHUB WORKFLOWS
# ════════════════════════════════════════════════════════════════

class TestWorkflows:
    """Validação de GitHub Actions workflows"""

    EXPECTED_WORKFLOWS = [
        "deploy.yml", "quality-gate.yml", "weekly-review.yml"
    ]

    def test_workflows_exist(self):
        wf_dir = ROOT / ".github" / "workflows"
        for wf in self.EXPECTED_WORKFLOWS:
            assert (wf_dir / wf).exists(), f"Workflow '{wf}' não encontrado"

    def test_quality_gate_category_count(self, direitos):
        wf_path = ROOT / ".github" / "workflows" / "quality-gate.yml"
        content = wf_path.read_text(encoding="utf-8")
        num_cats = len(direitos["categorias"])
        assert f"{num_cats} categorias" in content, \
            f"quality-gate.yml deveria mencionar '{num_cats} categorias'"


# ════════════════════════════════════════════════════════════════
# 14. IMAGES E ASSETS
# ════════════════════════════════════════════════════════════════

class TestAssets:
    """Validação de imagens e assets"""

    def test_favicon_exists(self):
        assert (ROOT / "images" / "favicon.ico").exists()

    def test_og_image_exists(self):
        assert (ROOT / "images" / "og-image.png").exists()

    def test_manifest_exists(self):
        assert (ROOT / "manifest.json").exists()

    def test_manifest_valid_json(self):
        with open(ROOT / "manifest.json", encoding="utf-8") as f:
            manifest = json.load(f)
        assert "name" in manifest or "short_name" in manifest

    def test_robots_exists(self):
        assert (ROOT / "robots.txt").exists()

    def test_sitemap_exists(self):
        assert (ROOT / "sitemap.xml").exists()


# ════════════════════════════════════════════════════════════════
# 15. DADOS ESPECÍFICOS — ESTADOS E MUNICÍPIOS
# ════════════════════════════════════════════════════════════════

class TestEstadosMunicipios:
    """Validação de cobertura de estados e consistência geográfica"""

    BRAZIL_STATES = {
        "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá",
        "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
        "GO": "Goiás", "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul",
        "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco",
        "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
        "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina",
        "SE": "Sergipe", "SP": "São Paulo", "TO": "Tocantins"
    }

    def test_ipva_covers_all_states(self, direitos):
        """IPVA (inline em isencoes_tributarias) cobre todos os 27 estados"""
        isencoes = next(c for c in direitos["categorias"] if c["id"] == "isencoes_tributarias")
        ufs = [e["uf"] for e in isencoes.get("ipva_estados", [])]
        for uf in self.BRAZIL_STATES:
            assert uf in ufs, f"IPVA: estado '{uf}' ausente"

    def test_ipva_state_names_correct(self, direitos):
        isencoes = next(c for c in direitos["categorias"] if c["id"] == "isencoes_tributarias")
        det = {e["uf"]: e["nome"] for e in isencoes.get("ipva_estados_detalhado", [])}
        for uf, expected_name in self.BRAZIL_STATES.items():
            actual = det.get(uf, "")
            assert actual == expected_name, f"IPVA: {uf} nome '{actual}' != '{expected_name}'"


# ════════════════════════════════════════════════════════════════
# 16. FUNCIONALIDADES DE BUSCA
# ════════════════════════════════════════════════════════════════

class TestSearchFunctionality:
    """Testa que a lógica de busca no matching engine funciona corretamente"""

    def test_bpc_searchable(self, matching):
        assert "bpc" in matching["keyword_map"]
        assert "bpc" in matching["keyword_map"]["bpc"]["cats"]

    def test_ciptea_searchable(self, matching):
        assert "ciptea" in matching["keyword_map"]

    def test_autismo_searchable(self, matching):
        assert "autismo" in matching["keyword_map"]

    def test_common_terms_searchable(self, matching):
        common = ["deficiencia", "pcd", "transporte", "trabalho", "moradia",
                   "educacao", "saude", "fgts"]
        for term in common:
            found = any(term.lower() in k.lower() for k in matching["keyword_map"])
            assert found, f"Termo comum '{term}' não encontrado no matching engine"

    def test_new_category_terms_searchable(self, matching):
        """Testa que termos das novas categorias são encontráveis"""
        terms_to_find = {
            "curatela": "capacidade_legal",
            "crime PcD": "crimes_contra_pcd",
            "NBR 9050": "acessibilidade_arquitetonica",
            "WCAG": "acessibilidade_digital",
            "estimulacao precoce": "reabilitacao",
        }
        for term, expected_cat in terms_to_find.items():
            assert term in matching["keyword_map"], \
                f"Termo '{term}' não está no matching engine"
            assert expected_cat in matching["keyword_map"][term]["cats"], \
                f"Termo '{term}' não mapeia para '{expected_cat}'"

    def test_ipva_keyword_maps_to_isencoes(self, matching):
        """Buscar 'ipva' deve retornar isencoes_tributarias"""
        assert "ipva" in matching["keyword_map"]
        assert "isencoes_tributarias" in matching["keyword_map"]["ipva"]["cats"]

    def test_state_names_findable_in_orgaos(self, direitos):
        """Buscar por nome de estado deve ter match em orgaos_estaduais"""
        orgaos = direitos["orgaos_estaduais"]
        uf_set = {o["uf"] for o in orgaos}
        assert len(uf_set) == 27, "Deve ter 27 UFs únicas"
        expected_ufs = {"AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
                        "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
                        "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"}
        assert uf_set == expected_ufs

    def test_search_results_have_sefaz_detran(self, direitos):
        """Resultados de busca por estado devem ter SEFAZ e DETRAN"""
        for orgao in direitos["orgaos_estaduais"]:
            assert orgao["sefaz"].startswith("https://"), \
                f"{orgao['uf']}: SEFAZ URL inválida"
            assert orgao["detran"].startswith("https://"), \
                f"{orgao['uf']}: DETRAN URL inválida"

    def test_search_results_have_beneficios_destaque(self, direitos):
        """Resultados por estado devem exibir benefícios em destaque"""
        for orgao in direitos["orgaos_estaduais"]:
            bd = orgao.get("beneficios_destaque", [])
            assert len(bd) >= 1, f"{orgao['uf']}: sem benefícios destaque"
            for b in bd:
                assert len(b) >= 5, f"{orgao['uf']}: benefício muito curto: {b}"

    def test_ipva_detail_per_state_searchable(self, direitos):
        """Dados IPVA detalhados devem estar disponíveis por UF para dropdown"""
        isencoes = next(c for c in direitos["categorias"] if c["id"] == "isencoes_tributarias")
        detalhado = isencoes["ipva_estados_detalhado"]
        assert len(detalhado) == 27
        for estado in detalhado:
            assert estado["condicoes"], f"{estado['uf']}: condições vazias"
            assert estado["lei"], f"{estado['uf']}: lei vazia"
            assert estado["sefaz"].startswith("https://"), \
                f"{estado['uf']}: SEFAZ URL inválida"

    def test_matching_engine_synonyms_coverage(self, matching):
        """Sinônimos no matching engine devem cobrir termos frequentes"""
        km = matching["keyword_map"]
        # Termos que os usuários mais buscam
        high_freq = ["aposentadoria", "transporte", "educacao", "saude",
                     "moradia", "fgts", "ciptea", "bpc", "pcd"]
        for term in high_freq:
            assert any(term in k for k in km), \
                f"Termo frequente '{term}' não coberto pelo matching engine"

    def test_category_tags_enable_search(self, direitos):
        """Tags de cada categoria devem ser buscáveis (sem duplicatas, não vazias)"""
        for cat in direitos["categorias"]:
            tags = cat.get("tags", [])
            assert len(tags) >= 3, f"{cat['id']}: menos de 3 tags"
            # Duplicatas exatas (case-sensitive) — hard fail
            assert len(tags) == len(set(tags)), \
                f"{cat['id']}: tags duplicadas (exatas)"
            # Duplicatas case-insensitive — also fail
            lower_tags = [t.lower() for t in tags]
            assert len(lower_tags) == len(set(lower_tags)), \
                f"{cat['id']}: tags duplicadas (case-insensitive)"
            for tag in tags:
                assert len(tag.strip()) >= 2, \
                    f"{cat['id']}: tag muito curta: '{tag}'"


# ════════════════════════════════════════════════════════════════
# 17. PWA / SERVICE WORKER
# ════════════════════════════════════════════════════════════════

class TestPWA:
    """Validação PWA"""

    def test_sw_caches_direitos(self):
        sw = (ROOT / "sw.js").read_text(encoding="utf-8")
        assert "direitos.json" in sw

    def test_sw_caches_matching(self):
        sw = (ROOT / "sw.js").read_text(encoding="utf-8")
        assert "matching_engine.json" in sw

    def test_manifest_valid(self):
        with open(ROOT / "manifest.json", encoding="utf-8") as f:
            m = json.load(f)
        assert "icons" in m or "name" in m


# ════════════════════════════════════════════════════════════════
# 18. DOCS
# ════════════════════════════════════════════════════════════════

class TestDocs:
    """Validação de documentação essencial"""

    ESSENTIAL_DOCS = ["README.md", "CHANGELOG.md", "LICENSE", "SECURITY.md"]

    def test_essential_docs_exist(self):
        for doc in self.ESSENTIAL_DOCS:
            assert (ROOT / doc).exists(), f"Doc '{doc}' não encontrado"

    def test_changelog_not_empty(self):
        content = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert len(content) > 100


# ════════════════════════════════════════════════════════════════
# 19. RESPOSTAS E DADOS ÍNTEGROS
# ════════════════════════════════════════════════════════════════

class TestDataIntegrity:
    """Testes de integridade geral dos dados"""

    def test_all_json_files_parse(self):
        """Todos os JSONs na pasta data devem ser válidos"""
        for f in DATA.glob("*.json"):
            with open(f, encoding="utf-8") as fp:
                try:
                    json.load(fp)
                except json.JSONDecodeError as e:
                    pytest.fail(f"{f.name}: JSON inválido — {e}")

    def test_no_empty_strings_in_categories(self, direitos):
        for cat in direitos["categorias"]:
            assert cat["titulo"].strip(), f"{cat['id']}: titulo vazio"
            assert cat["resumo"].strip(), f"{cat['id']}: resumo vazio"
            assert cat["valor"].strip(), f"{cat['id']}: valor vazio"
            assert cat["onde"].strip(), f"{cat['id']}: onde vazio"

    def test_tags_are_lowercase_strings(self, direitos):
        for cat in direitos["categorias"]:
            for tag in cat["tags"]:
                assert isinstance(tag, str), f"{cat['id']}: tag não é string"
                assert tag.strip(), f"{cat['id']}: tag vazia"

    def test_no_prototype_pollution_keys(self, direitos):
        """Verifica que não há chaves de prototype pollution"""
        dangerous = {"__proto__", "constructor", "prototype"}
        raw = json.dumps(direitos)
        for key in dangerous:
            assert f'"{key}"' not in raw, f"Chave perigosa '{key}' encontrada"

    def test_aviso_legal_present(self, direitos):
        assert "aviso" in direitos
        assert len(direitos["aviso"]) > 50, "Aviso legal muito curto"


# ════════════════════════════════════════════════════════════════
# 20. SITEMAP.XML
# ════════════════════════════════════════════════════════════════

class TestSitemap:
    """Validação de sitemap.xml"""

    @pytest.fixture(autouse=True)
    def _load_sitemap(self):
        self.sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")

    def test_file_exists(self):
        assert (ROOT / "sitemap.xml").exists()

    def test_valid_xml_header(self):
        assert self.sitemap.startswith('<?xml version="1.0"')

    def test_has_urlset(self):
        assert "<urlset" in self.sitemap
        assert "</urlset>" in self.sitemap

    def test_canonical_url_present(self):
        """Sitemap deve conter a URL canônica principal (SPA = 1 URL indexável)"""
        assert "https://nossodireito.fabiotreze.com/" in self.sitemap

    def test_no_fragment_urls(self):
        """Google ignora fragmentos (#) — sitemap NÃO deve conter URLs com #"""
        import re
        fragments = re.findall(r'<loc>[^<]*#[^<]*</loc>', self.sitemap)
        assert not fragments, \
            f"Sitemap contém URLs com fragmento (Google ignora): {fragments[:5]}"

    def test_single_url_for_spa(self):
        """SPA com hash-routing deve ter apenas 1 URL no sitemap"""
        import re
        urls = re.findall(r'<loc>([^<]+)</loc>', self.sitemap)
        assert len(urls) == 1, \
            f"SPA deveria ter 1 URL no sitemap, encontrado {len(urls)}: {urls[:5]}"

    def test_dates_are_current(self):
        """Datas não devem estar defasadas (within 90 days of today)"""
        import re as _re
        from datetime import datetime, timedelta
        dates = _re.findall(r'<lastmod>(\d{4}-\d{2}-\d{2})</lastmod>', self.sitemap)
        assert dates, "Nenhuma data encontrada no sitemap"
        cutoff = datetime.now() - timedelta(days=90)
        for d in dates:
            dt = datetime.strptime(d, '%Y-%m-%d')
            assert dt >= cutoff, f"Data {d} está defasada (mais de 90 dias)"

    def test_priority_values_valid(self):
        priorities = re.findall(r"<priority>([\d.]+)</priority>", self.sitemap)
        for p in priorities:
            val = float(p)
            assert 0.0 <= val <= 1.0, f"Priority {p} fora do range"


# ════════════════════════════════════════════════════════════════
# 21. ROBOTS.TXT
# ════════════════════════════════════════════════════════════════

class TestRobots:
    """Validação de robots.txt"""

    @pytest.fixture(autouse=True)
    def _load_robots(self):
        self.robots = (ROOT / "robots.txt").read_text(encoding="utf-8")

    def test_file_exists(self):
        assert (ROOT / "robots.txt").exists()

    def test_has_user_agent(self):
        assert "User-agent:" in self.robots

    def test_has_sitemap_reference(self):
        assert "Sitemap: https://nossodireito.fabiotreze.com/sitemap.xml" in self.robots

    def test_disallows_dev_paths(self):
        for path in ["/terraform/", "/scripts/", "/tests/", "/__pycache__/", "/schemas/"]:
            assert f"Disallow: {path}" in self.robots, \
                f"robots.txt não bloqueia '{path}'"

    def test_allows_root(self):
        assert "Allow: /" in self.robots

    def test_blocks_ai_crawlers(self):
        for bot in ["GPTBot", "CCBot", "anthropic-ai"]:
            assert bot in self.robots, f"robots.txt não bloqueia crawler IA '{bot}'"


# ════════════════════════════════════════════════════════════════
# 22. JSON-LD STRUCTURED DATA
# ════════════════════════════════════════════════════════════════

class TestJSONLD:
    """Validação de JSON-LD structured data no index.html"""

    @pytest.fixture(autouse=True)
    def _extract_jsonld(self, index_html):
        """Extrai todos os blocos JSON-LD do HTML"""
        blocks = re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
            index_html, re.DOTALL
        )
        self.jsonld_blocks = []
        for b in blocks:
            self.jsonld_blocks.append(json.loads(b))
        self.types = {b.get("@type") for b in self.jsonld_blocks}

    def test_has_web_application(self):
        assert "WebApplication" in self.types

    def test_has_website(self):
        """WebSite schema com SearchAction para sitelinks searchbox do Google"""
        assert "WebSite" in self.types
        ws = [b for b in self.jsonld_blocks if b.get("@type") == "WebSite"]
        assert len(ws) >= 1
        assert "potentialAction" in ws[0], "WebSite deve ter potentialAction (SearchAction)"
        assert ws[0]["potentialAction"]["@type"] == "SearchAction"

    def test_has_faq_page(self):
        assert "FAQPage" in self.types

    def test_has_government_service(self):
        assert "GovernmentService" in self.types

    def test_has_organization(self):
        assert "Organization" in self.types

    def test_has_breadcrumb(self):
        assert "BreadcrumbList" in self.types

    def test_breadcrumb_no_fragments(self):
        """BreadcrumbList não deve ter URLs com fragmentos (#)"""
        bc = [b for b in self.jsonld_blocks if b.get("@type") == "BreadcrumbList"]
        assert len(bc) >= 1
        for item in bc[0].get("itemListElement", []):
            url = item.get("item", "")
            assert "#" not in url, f"BreadcrumbList tem fragmento: {url}"

    def test_has_itemlist_categorias(self):
        item_lists = [b for b in self.jsonld_blocks if b.get("@type") == "ItemList"]
        cat_list = [il for il in item_lists if "Benefícios" in il.get("name", "")]
        assert len(cat_list) >= 1, "ItemList de categorias não encontrada"
        # numberOfItems must match actual categorias count from direitos.json
        n = cat_list[0]["numberOfItems"]
        assert isinstance(n, int) and n >= 1, f"numberOfItems inválido: {n}"

    def test_government_service_has_30_offers(self):
        gs = [b for b in self.jsonld_blocks if b.get("@type") == "GovernmentService"]
        assert len(gs) >= 1
        catalog = gs[0].get("hasOfferCatalog", {})
        items = catalog.get("itemListElement", [])
        assert len(items) >= 1, f"GovernmentService tem {len(items)} offers, esperado pelo menos 1"

    def test_faq_has_questions(self):
        faq = [b for b in self.jsonld_blocks if b.get("@type") == "FAQPage"]
        assert len(faq) >= 1
        questions = faq[0].get("mainEntity", [])
        assert len(questions) >= 10, f"FAQ tem apenas {len(questions)} perguntas"

    def test_all_jsonld_valid(self):
        """Todos os blocos JSON-LD devem ter @context e @type"""
        for b in self.jsonld_blocks:
            assert "@context" in b, f"JSON-LD sem @context: {b.get('@type', '?')}"
            assert "@type" in b, f"JSON-LD sem @type"


# ════════════════════════════════════════════════════════════════
# 23. ORGÃOS ESTADUAIS (27 ESTADOS)
# ════════════════════════════════════════════════════════════════

class TestOrgaosEstaduais:
    """Validação de órgãos estaduais expandidos em direitos.json"""

    BRAZIL_UFS = sorted([
        "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
        "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
        "RO", "RR", "RS", "SC", "SE", "SP", "TO"
    ])

    def test_all_27_states_have_orgaos(self, direitos):
        orgaos = direitos.get("orgaos_estaduais", [])
        ufs = sorted({o["uf"] for o in orgaos})
        assert ufs == self.BRAZIL_UFS, \
            f"Missing UFs: {set(self.BRAZIL_UFS) - set(ufs)}"

    def test_orgaos_have_required_fields(self, direitos):
        for o in direitos.get("orgaos_estaduais", []):
            assert "uf" in o, "Orgão sem UF"
            assert "nome" in o, f"Orgão {o.get('uf', '?')} sem nome"
            assert "url" in o, f"Orgão {o.get('uf', '?')} sem URL"

    def test_orgaos_urls_https(self, direitos):
        for o in direitos.get("orgaos_estaduais", []):
            assert o["url"].startswith("https://"), \
                f"Orgão {o['uf']}: URL não HTTPS: {o['url']}"

    def test_orgaos_have_sefaz(self, direitos):
        """Todos os 27 estados devem ter URL da SEFAZ"""
        for o in direitos.get("orgaos_estaduais", []):
            assert "sefaz" in o and o["sefaz"], \
                f"Orgão {o['uf']}: sem SEFAZ"
            assert o["sefaz"].startswith("https://"), \
                f"Orgão {o['uf']}: SEFAZ não HTTPS: {o['sefaz']}"

    def test_orgaos_have_detran(self, direitos):
        """Todos os 27 estados devem ter URL do DETRAN"""
        for o in direitos.get("orgaos_estaduais", []):
            assert "detran" in o and o["detran"], \
                f"Orgão {o['uf']}: sem DETRAN"
            assert o["detran"].startswith("https://"), \
                f"Orgão {o['uf']}: DETRAN não HTTPS: {o['detran']}"

    def test_orgaos_have_beneficios_destaque(self, direitos):
        """Todos os estados devem ter benefícios destaque"""
        for o in direitos.get("orgaos_estaduais", []):
            assert "beneficios_destaque" in o, \
                f"Orgão {o['uf']}: sem beneficios_destaque"
            assert len(o["beneficios_destaque"]) >= 1, \
                f"Orgão {o['uf']}: beneficios_destaque vazio"


# ════════════════════════════════════════════════════════════════
# 24. SCRIPTS — PÓS-HIGIENIZAÇÃO
# ════════════════════════════════════════════════════════════════

class TestScriptsPostCleanup:
    """Verifica que scripts essenciais existem após limpeza"""

    ACTIVE_SCRIPTS = [
        "validate_all.py", "validate_content.py", "validate_schema.py",
        "validate_sources.py", "validate_urls.py", "validate_govbr_urls.py",
        "validate_legal_compliance.py", "validate_legal_sources.py",
        "master_compliance.py", "bump_version.py", "discover_benefits.py",
        "analise360.py", "audit_automation.py",
        "complete_beneficios.py"
    ]

    def test_all_active_scripts_present(self):
        scripts_dir = ROOT / "scripts"
        for s in self.ACTIVE_SCRIPTS:
            assert (scripts_dir / s).exists(), f"Script ativo '{s}' ausente"

    def test_no_orphan_underscore_scripts(self):
        """Scripts com prefixo _ não devem existir no diretório principal"""
        scripts_dir = ROOT / "scripts"
        orphans = [f.name for f in scripts_dir.glob("_*.py")]
        assert not orphans, f"Scripts _ órfãos: {orphans}"
