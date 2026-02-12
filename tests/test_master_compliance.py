#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTES UNITÁRIOS — Master Compliance

Testes automatizados para scripts/master_compliance.py.
"""

import json
import sys
from pathlib import Path

import pytest

# Adicionar diretório raiz ao path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import master_compliance


class TestMasterCompliance:
    """Testes para Master Compliance"""

    @pytest.fixture
    def direitos_data(self):
        """Carrega dados de direitos.json"""
        data_path = ROOT / "data" / "direitos.json"
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_direitos_json_exists(self):
        """Testa se data/direitos.json existe"""
        data_path = ROOT / "data" / "direitos.json"
        assert data_path.exists(), "data/direitos.json não encontrado"

    def test_direitos_json_valid(self, direitos_data):
        """Testa se JSON é válido e tem campos obrigatórios"""
        assert 'versao' in direitos_data
        assert 'categorias' in direitos_data
        assert 'fontes' in direitos_data
        assert isinstance(direitos_data['categorias'], list)
        assert len(direitos_data['categorias']) > 0

    def test_all_categories_have_required_fields(self, direitos_data):
        """Testa se todas as categorias têm campos obrigatórios"""
        required_fields = [
            'id', 'titulo', 'resumo', 'base_legal',
            'requisitos', 'documentos', 'passo_a_passo',
            'dicas', 'valor', 'onde', 'links', 'tags'
        ]

        for cat in direitos_data['categorias']:
            for field in required_fields:
                assert field in cat, f"Categoria {cat.get('id', 'unknown')} não tem campo '{field}'"

    def test_categories_minimum_content(self, direitos_data):
        """Testa se categorias têm conteúdo mínimo"""
        for cat in direitos_data['categorias']:
            cat_id = cat.get('id', 'unknown')

            # Mínimos de qualidade
            assert len(cat.get('requisitos', [])) >= 3, f"{cat_id}: mínimo 3 requisitos"
            assert len(cat.get('documentos', [])) >= 2, f"{cat_id}: mínimo 2 documentos"
            assert len(cat.get('passo_a_passo', [])) >= 3, f"{cat_id}: mínimo 3 passos"
            assert len(cat.get('dicas', [])) >= 2, f"{cat_id}: mínimo 2 dicas"
            assert len(cat.get('links', [])) >= 1, f"{cat_id}: mínimo 1 link"
            assert len(cat.get('tags', [])) >= 3, f"{cat_id}: mínimo 3 tags"

    def test_base_legal_structure(self, direitos_data):
        """Testa estrutura de base_legal"""
        for cat in direitos_data['categorias']:
            base_legal = cat.get('base_legal', [])
            assert len(base_legal) >= 1, f"Categoria {cat.get('id')} sem base legal"

            for item in base_legal:
                assert 'lei' in item, "Item de base_legal sem campo 'lei'"

    def test_links_have_url(self, direitos_data):
        """Testa se todos os links têm URL válida (http://, https://, ou tel:)"""
        for cat in direitos_data['categorias']:
            links = cat.get('links', [])
            for link in links:
                assert 'url' in link, f"Link em {cat.get('id')} sem URL"
                assert link['url'].startswith(('http', 'tel:')), f"URL inválida em {cat.get('id')}: {link['url']}"

    def test_fontes_have_required_fields(self, direitos_data):
        """Testa se fontes têm campos obrigatórios"""
        fontes = direitos_data.get('fontes', [])
        assert len(fontes) > 0, "Nenhuma fonte encontrada"

        for fonte in fontes:
            assert 'nome' in fonte
            assert 'tipo' in fonte
            assert 'url' in fonte
            assert fonte['url'].startswith('http')

    def test_no_duplicate_category_ids(self, direitos_data):
        """Testa se não há IDs duplicados"""
        ids = [cat.get('id') for cat in direitos_data['categorias']]
        assert len(ids) == len(set(ids)), "IDs de categorias duplicados encontrados"

    def test_version_format(self, direitos_data):
        """Testa formato da versão (semantic versioning)"""
        versao = direitos_data.get('versao', '')
        parts = versao.split('.')
        assert len(parts) == 3, f"Versão {versao} não segue semantic versioning (X.Y.Z)"
        for part in parts:
            assert part.isdigit(), f"Parte '{part}' da versão não é numérica"
