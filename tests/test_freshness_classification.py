"""Gate determinístico para a política de classificação de URLs do
content-freshness cron — evita reincidência de falsos-positivos como o #206
(portais oficiais BR bloqueados por anti-bot/geo-fence dos runners do CI).

Política implementada em:
  - scripts/validate_sources.py :: classify_url_result
  - scripts/freshness_open_issue.py :: has_real_drift
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from validate_sources import classify_url_result, _is_oficial_br  # noqa: E402
from freshness_open_issue import has_real_drift, render_body  # noqa: E402


# ─── _is_oficial_br ─────────────────────────────────────────────────
@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://portal.barueri.sp.gov.br/", True),
        ("https://www.stj.jus.br/", True),
        ("https://legis.senado.leg.br/", True),
        ("https://www.mpsp.mp.br/", True),
        ("https://oab.def.br/", True),
        ("https://google.com/", False),
        ("https://example.org/", False),
        ("https://github.com/foo/bar", False),
    ],
)
def test_is_oficial_br(url, expected):
    assert _is_oficial_br(url) is expected


# ─── classify_url_result ────────────────────────────────────────────
class TestClassifyUrlResult:
    def test_2xx_is_ok(self):
        s, m, ci = classify_url_result("https://x.gov.br", 200)
        assert (s, ci) == ("ok", False)
        assert "200" in m

    def test_3xx_is_ok(self):
        s, _, ci = classify_url_result("https://x.com", 301)
        assert (s, ci) == ("ok", False)

    def test_404_in_oficial_br_is_real_error(self):
        # Página realmente sumiu — 404 nunca é falso-positivo, mesmo em gov.br
        s, m, ci = classify_url_result(
            "https://portal.barueri.sp.gov.br/cpa", 404
        )
        assert s == "error"
        assert ci is False
        assert "404" in m

    def test_404_in_non_oficial_is_error(self):
        s, _, ci = classify_url_result("https://example.com/x", 404)
        assert (s, ci) == ("error", False)

    def test_403_in_oficial_br_is_ci_blocked_warning(self):
        # Anti-bot WAF — falso-positivo de ambiente CI
        s, m, ci = classify_url_result("https://www.stj.jus.br/", 403)
        assert s == "warning"
        assert ci is True
        assert "anti-bot" in m.lower() or "waf" in m.lower()

    def test_403_in_non_oficial_is_real_error(self):
        # 403 fora de domínio oficial BR = bug de conteúdo (link mudou de auth)
        s, _, ci = classify_url_result("https://example.com/admin", 403)
        assert (s, ci) == ("error", False)

    def test_4xx_other_in_oficial_is_error(self):
        # 410 Gone, 451 etc. em gov.br ainda devem ser tratados como erro real
        # (não há padrão conhecido de WAF retornando esses códigos)
        s, _, ci = classify_url_result("https://x.gov.br", 410)
        assert (s, ci) == ("error", False)

    def test_5xx_is_warning_not_ci_blocked(self):
        # 5xx é instabilidade do servidor — warning, mas não ci_blocked
        s, _, ci = classify_url_result("https://x.gov.br", 503)
        assert s == "warning"
        assert ci is False

    def test_connection_failure_in_oficial_is_ci_blocked(self):
        # status=0 + gov.br = geo-fence (runner US bloqueado)
        s, m, ci = classify_url_result(
            "https://secdef.al.gov.br", 0, "timed out"
        )
        assert s == "warning"
        assert ci is True
        assert "geo-fence" in m.lower() or "ci" in m.lower()

    def test_connection_failure_outside_oficial_is_error(self):
        s, _, ci = classify_url_result("https://example.com", 0, "timed out")
        assert (s, ci) == ("error", False)


# ─── has_real_drift ─────────────────────────────────────────────────
class TestHasRealDrift:
    def test_empty_report_no_drift(self):
        assert has_real_drift({"results": []}) is False

    def test_only_ok_no_drift(self):
        report = {"results": [
            {"status": "ok", "source": "url", "ci_blocked": False},
        ]}
        assert has_real_drift(report) is False

    def test_only_ci_blocked_warnings_no_drift(self):
        # Cenário exato do #206 — 12 warnings todos ci_blocked
        report = {"results": [
            {"status": "warning", "source": "url", "ci_blocked": True},
            {"status": "warning", "source": "url", "ci_blocked": True},
        ]}
        assert has_real_drift(report) is False

    def test_error_is_drift(self):
        report = {"results": [
            {"status": "error", "source": "url", "ci_blocked": False},
        ]}
        assert has_real_drift(report) is True

    def test_non_ci_blocked_warning_is_drift(self):
        # 5xx ou warning fora de gov.br → drift acionável
        report = {"results": [
            {"status": "warning", "source": "url", "ci_blocked": False},
        ]}
        assert has_real_drift(report) is True

    def test_mixed_error_among_ci_blocked_is_drift(self):
        report = {"results": [
            {"status": "warning", "source": "url", "ci_blocked": True},
            {"status": "warning", "source": "url", "ci_blocked": True},
            {"status": "error", "source": "url", "ci_blocked": False},
        ]}
        assert has_real_drift(report) is True


# ─── render_body ────────────────────────────────────────────────────
class TestRenderBody:
    def test_body_has_three_sections_when_mixed(self):
        report = {
            "timestamp": "2026-05-28",
            "ok": 1, "warnings": 2, "errors": 1,
            "results": [
                {"status": "ok", "source": "url", "ci_blocked": False,
                 "item": "ok-item", "url": "https://x.gov.br", "http_code": 200},
                {"status": "error", "source": "url", "ci_blocked": False,
                 "item": "broken", "url": "https://y.gov.br/missing",
                 "http_code": 404, "message": "HTTP 404"},
                {"status": "warning", "source": "url", "ci_blocked": True,
                 "item": "geo-blocked-1", "url": "https://secdef.al.gov.br",
                 "http_code": 0, "message": "geo-fence"},
                {"status": "warning", "source": "url", "ci_blocked": True,
                 "item": "anti-bot-stj", "url": "https://www.stj.jus.br",
                 "http_code": 403, "message": "anti-bot"},
            ],
        }
        body = render_body(report, "fabiotreze/nossodireito", "12345")
        assert "URLs quebradas" in body  # seção real
        assert "Bloqueios de ambiente CI" in body  # seção informativa
        assert "broken" in body
        assert "geo-blocked-1" in body
        assert "anti-bot-stj" in body

    def test_body_only_ci_blocked_says_no_actionable(self):
        report = {
            "timestamp": "2026-05-28",
            "ok": 280, "warnings": 12, "errors": 0,
            "results": [
                {"status": "warning", "source": "url", "ci_blocked": True,
                 "item": f"item-{i}", "url": "https://x.gov.br",
                 "http_code": 0, "message": "geo-fence"}
                for i in range(12)
            ],
        }
        body = render_body(report, "fabiotreze/nossodireito", "12345")
        assert "Nenhum drift acionável" in body
        assert "Bloqueios de ambiente CI (12)" in body

    def test_body_empty_says_no_drift(self):
        report = {"timestamp": "2026-05-28", "ok": 280, "warnings": 0, "errors": 0,
                  "results": []}
        body = render_body(report, "fabiotreze/nossodireito", "12345")
        assert "Nenhum drift detectado" in body
