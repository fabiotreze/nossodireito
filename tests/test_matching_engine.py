"""
Testes de precisão do matching engine (data/matching_engine.json).

Cobre o gap fim-a-fim: garantir que toda keyword roteia para categorias
existentes em data/direitos.json, que os pesos são válidos e que keywords
críticas casam com as categorias esperadas.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


@pytest.fixture(scope="module")
def matching():
    return json.loads((DATA / "matching_engine.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def direitos():
    return json.loads((DATA / "direitos.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def categoria_slugs(direitos):
    return {c["id"] for c in direitos.get("categorias", [])}


class TestMatchingEngineIntegrity:
    """Integridade estrutural do keyword_map."""

    def test_has_keyword_map(self, matching):
        assert "keyword_map" in matching
        assert isinstance(matching["keyword_map"], dict)
        assert len(matching["keyword_map"]) > 100

    def test_entries_shape(self, matching):
        for kw, entry in matching["keyword_map"].items():
            assert isinstance(kw, str) and kw.strip(), f"keyword vazia: {kw!r}"
            assert isinstance(entry, dict), f"{kw}: entry não é dict"
            assert "cats" in entry, f"{kw}: falta 'cats'"
            assert "weight" in entry, f"{kw}: falta 'weight'"
            assert isinstance(entry["cats"], list) and entry["cats"], (
                f"{kw}: 'cats' deve ser lista não-vazia"
            )
            assert isinstance(entry["weight"], (int, float)), (
                f"{kw}: 'weight' deve ser numérico"
            )
            assert 1 <= entry["weight"] <= 10, (
                f"{kw}: peso fora do intervalo 1-10 ({entry['weight']})"
            )

    def test_all_cats_exist_in_direitos(self, matching, categoria_slugs):
        """Toda categoria referenciada precisa existir em direitos.json."""
        invalid = {}
        for kw, entry in matching["keyword_map"].items():
            missing = [c for c in entry["cats"] if c not in categoria_slugs]
            if missing:
                invalid[kw] = missing
        assert not invalid, (
            f"{len(invalid)} keywords apontam para categorias inexistentes: "
            f"{dict(list(invalid.items())[:5])}"
        )

    def test_no_duplicate_lowercase_keywords(self, matching):
        seen = {}
        dups = []
        for kw in matching["keyword_map"]:
            low = kw.lower().strip()
            if low in seen:
                dups.append((kw, seen[low]))
            else:
                seen[low] = kw
        assert not dups, f"keywords duplicadas (case-insensitive): {dups[:10]}"


class TestMatchingPrecision:
    """Casos críticos: queries reais devem roteiar para a categoria certa."""

    CRITICAL_QUERIES = [
        # (query, categoria_esperada_no_topo)
        ("bpc", "bpc"),
        ("loas", "bpc"),
        ("bpc loas", "bpc"),
        ("benefício assistencial", "bpc"),
        ("isenção ipi", "isencoes_tributarias"),
        ("isenção ir", "isencao_ir"),
        ("aposentadoria especial pcd", "aposentadoria_especial_pcd"),
        ("auxílio inclusão", "auxilio_inclusao"),
        ("curatela", "curatela_decisao_apoiada"),
        ("tomada de decisão apoiada", "curatela_decisao_apoiada"),
        ("ciptea", "ciptea"),
        ("meia entrada", "meia_entrada"),
        ("estacionamento", "estacionamento_especial"),
        ("tarifa social energia", "tarifa_social_energia"),
        ("bolsa família", "bolsa_familia"),
    ]

    @staticmethod
    def _score(query: str, keyword_map: dict) -> dict[str, float]:
        """Simula scoring do site: somatório de pesos por categoria."""
        q = query.lower().strip()
        scores: dict[str, float] = {}
        for kw, entry in keyword_map.items():
            kw_low = kw.lower().strip()
            # match: keyword aparece como token/substring na query
            if kw_low in q or q in kw_low:
                for cat in entry["cats"]:
                    scores[cat] = scores.get(cat, 0) + entry["weight"]
        return scores

    @pytest.mark.parametrize("query,expected", CRITICAL_QUERIES)
    def test_critical_query_routes_to_expected_category(
        self, matching, query, expected, categoria_slugs
    ):
        """Esperado deve estar entre as top-3 categorias do keyword_map.

        Nota: o site combina este score com sinais do texto da categoria
        (titulo/resumo/tags). O teste isola o keyword_map para detectar
        regressões de roteamento — daí a tolerância de top-3.
        """
        assert expected in categoria_slugs, (
            f"Categoria esperada {expected!r} não existe em direitos.json"
        )
        scores = self._score(query, matching["keyword_map"])
        assert scores, f"Nenhum match para query {query!r}"
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        top3 = [c for c, _ in ranked[:3]]
        assert expected in top3, (
            f"Query {query!r}: esperado em top-3, obtido {top3} "
            f"(scores={dict(ranked[:5])})"
        )


class TestCategoriesCoverage:
    """Toda categoria com slug deve ter pelo menos uma keyword apontando para ela."""

    # Categorias que ainda não têm keywords dedicadas — tolerância temporária.
    ALLOWED_UNCOVERED: set[str] = set()

    def test_all_categories_have_at_least_one_keyword(self, matching, categoria_slugs):
        covered = set()
        for entry in matching["keyword_map"].values():
            covered.update(entry["cats"])
        uncovered = categoria_slugs - covered - self.ALLOWED_UNCOVERED
        assert not uncovered, (
            f"{len(uncovered)} categorias sem keyword no matching engine: "
            f"{sorted(uncovered)}"
        )
