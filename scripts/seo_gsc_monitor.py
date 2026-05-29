#!/usr/bin/env python3
"""Monitor de tendência SEO para URLs /direitos/* via Google Search Console.

Modos de autenticação suportados:

1. OAuth refresh token (recomendado — user owner da propriedade):
   Variáveis:
     GSC_OAUTH_CLIENT_ID
     GSC_OAUTH_CLIENT_SECRET
     GSC_OAUTH_REFRESH_TOKEN

2. Service account (requer que o e-mail da SA seja aceito no Search Console):
   Variável:
     GSC_SERVICE_ACCOUNT_JSON

Uso típico (em CI):
  python3 scripts/seo_gsc_monitor.py \
    --property-url "https://nossodireito.fabiotreze.com/" \
    --path-prefix "/direitos/" \
    --drop-threshold-pct -20 \
    --json-out gsc_report.json

Exit codes:
  0 = OK (ou sem dados suficientes)
  2 = configuração ausente
  3 = alerta (queda >= threshold)
  1 = erro inesperado
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta


try:
    from googleapiclient.discovery import build
    from google.oauth2 import credentials as oauth2_credentials
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
except Exception:
    print("FAIL: dependências Google não instaladas (google-api-python-client/google-auth)", file=sys.stderr)
    sys.exit(2)

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def build_service_from_oauth() -> object:
    """Autentica via OAuth refresh token (owner da propriedade)."""
    client_id = os.environ.get("GSC_OAUTH_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GSC_OAUTH_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("GSC_OAUTH_REFRESH_TOKEN", "").strip()

    if not all([client_id, client_secret, refresh_token]):
        return None

    creds = oauth2_credentials.Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def build_service_from_sa() -> object:
    """Autentica via service account JSON."""
    sa_json = os.environ.get("GSC_SERVICE_ACCOUNT_JSON", "").strip()
    if not sa_json:
        return None

    sa_info = json.loads(sa_json)
    creds = service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def get_service() -> tuple[object, str]:
    """Retorna (service, modo) usando o primeiro método de autenticação disponível."""
    svc = build_service_from_oauth()
    if svc:
        return svc, "oauth"
    svc = build_service_from_sa()
    if svc:
        return svc, "service_account"
    return None, "none"


def pct_delta(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0 if current == 0 else 100.0
    return ((current - previous) / previous) * 100.0


def query_period(service, property_url: str, start: str, end: str, path_prefix: str) -> tuple[float, float]:
    request = {
        "startDate": start,
        "endDate": end,
        "dimensions": ["page"],
        "dimensionFilterGroups": [
            {
                "filters": [
                    {
                        "dimension": "page",
                        "operator": "contains",
                        "expression": path_prefix,
                    }
                ]
            }
        ],
        "rowLimit": 25000,
    }
    response = service.searchanalytics().query(siteUrl=property_url, body=request).execute()
    rows = response.get("rows", [])
    clicks = float(sum(r.get("clicks", 0) for r in rows))
    impressions = float(sum(r.get("impressions", 0) for r in rows))
    return clicks, impressions


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitora tendência de SEO por prefixo de URL no GSC")
    parser.add_argument("--property-url", required=True)
    parser.add_argument("--path-prefix", default="/direitos/")
    parser.add_argument("--drop-threshold-pct", type=float, default=-20.0)
    parser.add_argument("--json-out", default="gsc_report.json")
    args = parser.parse_args()

    try:
        service, auth_mode = get_service()
    except Exception:
        print("FAIL: erro ao autenticar no GSC", file=sys.stderr)
        return 1

    if service is None:
        print(
            "FAIL: nenhuma credencial configurada.\n"
            "Configure GSC_OAUTH_CLIENT_ID + GSC_OAUTH_CLIENT_SECRET + GSC_OAUTH_REFRESH_TOKEN\n"
            "ou GSC_SERVICE_ACCOUNT_JSON.",
            file=sys.stderr,
        )
        return 2

    today = date.today()
    cur_start = today - timedelta(days=7)
    cur_end = today - timedelta(days=1)
    prev_start = today - timedelta(days=14)
    prev_end = today - timedelta(days=8)

    try:
        cur_clicks, cur_impressions = query_period(
            service,
            args.property_url,
            cur_start.isoformat(),
            cur_end.isoformat(),
            args.path_prefix,
        )
        prev_clicks, prev_impressions = query_period(
            service,
            args.property_url,
            prev_start.isoformat(),
            prev_end.isoformat(),
            args.path_prefix,
        )
    except Exception:
        print("FAIL: erro consultando GSC", file=sys.stderr)
        return 1

    clicks_delta = pct_delta(cur_clicks, prev_clicks)
    impr_delta = pct_delta(cur_impressions, prev_impressions)

    report = {
        "property": args.property_url,
        "auth_mode": auth_mode,
        "path_prefix": args.path_prefix,
        "period_current": {"start": cur_start.isoformat(), "end": cur_end.isoformat()},
        "period_previous": {"start": prev_start.isoformat(), "end": prev_end.isoformat()},
        "current": {"clicks": cur_clicks, "impressions": cur_impressions},
        "previous": {"clicks": prev_clicks, "impressions": prev_impressions},
        "delta_pct": {"clicks": clicks_delta, "impressions": impr_delta},
        "threshold_pct": args.drop_threshold_pct,
        "alert": clicks_delta <= args.drop_threshold_pct or impr_delta <= args.drop_threshold_pct,
    }

    with open(args.json_out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    print(
        "OK: relatório gerado "
        f"(auth={auth_mode}, clicks_delta={clicks_delta:.2f}%, impressions_delta={impr_delta:.2f}%)"
    )

    if report["alert"]:
        print(
            f"ALERT: queda detectada (clicks {clicks_delta:.2f}%, impressions {impr_delta:.2f}%)",
            file=sys.stderr,
        )
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
