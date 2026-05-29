#!/usr/bin/env python3
"""
Gera um refresh token OAuth para a Search Console API.

Execute UMA VEZ localmente com seu usuário owner da propriedade.
O refresh token gerado vai para o secret GSC_OAUTH_REFRESH_TOKEN no GitHub.

Pré-requisitos:
  pip install google-auth-oauthlib

Passos no Google Cloud Console ANTES de rodar este script:
  1. https://console.cloud.google.com/apis/credentials
  2. Create Credentials > OAuth client ID
  3. Application type: Desktop app
  4. Name: nossodireito-gsc-local
  5. Baixar o JSON do client (Download JSON)
  6. Renomear para gsc_oauth_client.json e colocar na raiz do repo
     (já está no .gitignore — não será commitado)

Uso:
  python3 scripts/gsc_get_refresh_token.py

Saída:
  Imprime os 3 valores para salvar nos GitHub Secrets:
    GSC_OAUTH_CLIENT_ID
    GSC_OAUTH_CLIENT_SECRET
    GSC_OAUTH_REFRESH_TOKEN
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLIENT_SECRETS_FILE = ROOT / "gsc_oauth_client.json"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"


def main() -> int:
    if not CLIENT_SECRETS_FILE.exists():
        print(f"FAIL: arquivo não encontrado: {CLIENT_SECRETS_FILE}", file=sys.stderr)
        print("Baixe o JSON do OAuth client em https://console.cloud.google.com/apis/credentials", file=sys.stderr)
        return 1

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("FAIL: instale a dependência:\n  pip install google-auth-oauthlib", file=sys.stderr)
        return 1

    raw = json.loads(CLIENT_SECRETS_FILE.read_text(encoding="utf-8"))
    client_id = raw.get("installed", raw.get("web", {})).get("client_id", "")
    client_secret = raw.get("installed", raw.get("web", {})).get("client_secret", "")

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), scopes=SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n" + "=" * 60)
    print("Salve estes 3 valores nos GitHub Secrets do repositório:")
    print("=" * 60)
    print(f"\nGSC_OAUTH_CLIENT_ID\n  {client_id}")
    print(f"\nGSC_OAUTH_CLIENT_SECRET\n  {client_secret}")
    print(f"\nGSC_OAUTH_REFRESH_TOKEN\n  {creds.refresh_token}")
    print("\nE configure também:")
    print("GSC_PROPERTY_URL\n  https://nossodireito.fabiotreze.com/")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
