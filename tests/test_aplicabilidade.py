"""
Testes-gate: coerência entre `aplicabilidade` e `cids_relacionados`.

Garante que toda categoria de `data/direitos.json` declara `aplicabilidade`
explicitamente e que a presença/ausência de `cids_relacionados` é consistente
com o tipo declarado. Categoria nova sem declarar tipo → CI quebra.

Política: scripts/classify_aplicabilidade.py (determinístico).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DIREITOS = ROOT / "data" / "direitos.json"

ENUM = {"condicao_medica", "documento_administrativo", "publico_fechado", "servico_universal"}


@pytest.fixture(scope="module")
def categorias():
    return json.loads(DIREITOS.read_text(encoding="utf-8")).get("categorias", [])


class TestAplicabilidade:
    def test_todas_categorias_declaram_aplicabilidade(self, categorias):
        sem = [c["id"] for c in categorias if "aplicabilidade" not in c]
        assert not sem, (
            f"Categorias sem `aplicabilidade`: {sem}. "
            "Rode: python scripts/classify_aplicabilidade.py"
        )

    def test_aplicabilidade_dentro_do_enum(self, categorias):
        invalid = [(c["id"], c.get("aplicabilidade")) for c in categorias if c.get("aplicabilidade") not in ENUM]
        assert not invalid, f"Valores fora do enum {ENUM}: {invalid}"

    def test_condicao_medica_exige_cids(self, categorias):
        offenders = [
            c["id"]
            for c in categorias
            if c.get("aplicabilidade") == "condicao_medica" and not c.get("cids_relacionados")
        ]
        assert not offenders, (
            f"Categorias `condicao_medica` sem `cids_relacionados`: {offenders}. "
            "Ou preencha cids, ou reclassifique via classify_aplicabilidade.py."
        )

    def test_publico_fechado_tem_cid_canonico(self, categorias):
        """Talidomida/hanseníase/zika precisam CID público da OMS (validado pelo cron #205)."""
        offenders = [
            c["id"]
            for c in categorias
            if c.get("aplicabilidade") == "publico_fechado" and not c.get("cids_relacionados")
        ]
        assert not offenders, (
            f"`publico_fechado` sem CIDs canônicos: {offenders}. "
            "Rode: python scripts/enrich_cids_canonicos.py"
        )

    def test_documento_administrativo_sem_cids(self, categorias):
        """Documentos não restringem por CID — flag para evitar curadoria por engano."""
        offenders = [
            (c["id"], c.get("cids_relacionados"))
            for c in categorias
            if c.get("aplicabilidade") == "documento_administrativo" and c.get("cids_relacionados")
        ]
        assert not offenders, (
            f"`documento_administrativo` não deve listar CIDs (é documento, não condição): {offenders}"
        )
