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
  6. Renomear para gsc_oauth_client.json e colocar em UM destes locais
     (procurados nesta ordem):
       a. $XDG_CONFIG_HOME/nossodireito/gsc_oauth_client.json
       b. ~/.config/nossodireito/gsc_oauth_client.json   (recomendado)
       c. ./gsc_oauth_client.json                        (legacy, deprecated)
     Garanta permissões 0600 no arquivo e 0700 no diretório.

Uso:
  python3 scripts/gsc_get_refresh_token.py

Saída:
  Define diretamente os secrets/variables no GitHub (sem exibir segredos):
    secret GSC_OAUTH_CLIENT_ID
    secret GSC_OAUTH_CLIENT_SECRET
    secret GSC_OAUTH_REFRESH_TOKEN
    secret GSC_PROPERTY_URL
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def resolve_client_secrets_file() -> Path:
    """Find the OAuth client JSON.

    Search order (most secure first):
      1. $XDG_CONFIG_HOME/nossodireito/gsc_oauth_client.json
      2. ~/.config/nossodireito/gsc_oauth_client.json
      3. <repo>/gsc_oauth_client.json   (legacy; warns)
    """
    xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
    candidates: list[Path] = []
    if xdg:
        candidates.append(Path(xdg) / "nossodireito" / "gsc_oauth_client.json")
    candidates.append(Path.home() / ".config" / "nossodireito" / "gsc_oauth_client.json")
    legacy = ROOT / "gsc_oauth_client.json"
    candidates.append(legacy)

    for path in candidates:
        if path.is_file():
            if path == legacy:
                print(
                    "WARN: usando gsc_oauth_client.json na raiz do repo (deprecated).\n"
                    "  Mova para ~/.config/nossodireito/gsc_oauth_client.json com\n"
                    "  permissões 0600 (arquivo) e 0700 (diretório).",
                    file=sys.stderr,
                )
            return path
    # Default to the recommended location for a clean error message below.
    return Path.home() / ".config" / "nossodireito" / "gsc_oauth_client.json"


CLIENT_SECRETS_FILE = resolve_client_secrets_file()
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"


def gh_set_secret(name: str, value: str) -> None:
    subprocess.run(
        ["gh", "secret", "set", name],
        input=value,
        text=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


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

    refresh_token = creds.refresh_token or ""
    if not client_id or not client_secret or not refresh_token:
      print("FAIL: OAuth não retornou credenciais completas", file=sys.stderr)
      return 1

    try:
      gh_set_secret("GSC_OAUTH_CLIENT_ID", client_id)
      gh_set_secret("GSC_OAUTH_CLIENT_SECRET", client_secret)
      gh_set_secret("GSC_OAUTH_REFRESH_TOKEN", refresh_token)
      gh_set_secret("GSC_PROPERTY_URL", "https://nossodireito.fabiotreze.com/")
    except FileNotFoundError:
      print("FAIL: GitHub CLI (gh) não encontrado no PATH", file=sys.stderr)
      return 1
    except subprocess.CalledProcessError:
      print("FAIL: não foi possível definir os secrets no GitHub", file=sys.stderr)
      print("Confirme autenticação com: gh auth status", file=sys.stderr)
      return 1

    print("\nSecrets atualizados com sucesso no repositório:")
    print("- GSC_OAUTH_CLIENT_ID")
    print("- GSC_OAUTH_CLIENT_SECRET")
    print("- GSC_OAUTH_REFRESH_TOKEN")
    print("- GSC_PROPERTY_URL")
    print("Próximo passo: definir variável SEO_PRERENDER_MODE=prerender.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
