#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIXTURES COMPARTILHADAS — NossoDireito

Centraliza fixtures session-scoped reutilizadas entre os módulos de teste:
  - test_comprehensive.py
  - test_comprehensive_validation.py
  - test_cross_browser.py

Reduz duplicação e garante carregamento único de arquivos pesados.
"""

import json
from pathlib import Path

import pytest

# ════════════════════════════════════════════════════════════════
# PATH CONSTANTS
# ════════════════════════════════════════════════════════════════

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
JS_DIR = ROOT / "js"
CSS_DIR = ROOT / "css"
SCRIPTS_DIR = ROOT / "scripts"


# ════════════════════════════════════════════════════════════════
# DATA FIXTURES
# ════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def direitos():
    """Carrega direitos.json (JSON completo)."""
    with open(DATA / "direitos.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def matching():
    """Carrega matching_engine.json (JSON completo)."""
    with open(DATA / "matching_engine.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def dicionario():
    """Carrega dicionario_pcd.json (JSON completo)."""
    with open(DATA / "dicionario_pcd.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def schema():
    """Carrega direitos.schema.json."""
    with open(ROOT / "schemas" / "direitos.schema.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def matching_schema():
    """Carrega matching_engine.schema.json."""
    with open(ROOT / "schemas" / "matching_engine.schema.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def dicionario_schema():
    """Carrega dicionario_pcd.schema.json."""
    with open(ROOT / "schemas" / "dicionario_pcd.schema.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def cat_ids(direitos):
    """Conjunto de IDs de categorias em direitos.json."""
    return {c["id"] for c in direitos["categorias"]}


# ════════════════════════════════════════════════════════════════
# FILE-CONTENT FIXTURES
# ════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def html():
    """Conteúdo de index.html (texto)."""
    with open(ROOT / "index.html", encoding="utf-8") as f:
        return f.read()


# Alias para test_comprehensive.py que usa o nome `index_html`
@pytest.fixture(scope="session")
def index_html(html):
    """Alias de html() para manter compatibilidade."""
    return html


@pytest.fixture(scope="session")
def appjs():
    """Conteúdo de js/app.js (texto)."""
    with open(JS_DIR / "app.js", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="session")
def css():
    """Conteúdo de css/styles.css (texto)."""
    with open(CSS_DIR / "styles.css", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="session")
def swjs():
    """Conteúdo de sw.js (texto)."""
    with open(ROOT / "sw.js", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="session")
def manifest():
    """Conteúdo de manifest.json (JSON)."""
    with open(ROOT / "manifest.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def packagejson():
    """Conteúdo de package.json (JSON)."""
    with open(ROOT / "package.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def serverjs():
    """Conteúdo de server.js (texto)."""
    with open(ROOT / "server.js", encoding="utf-8") as f:
        return f.read()
