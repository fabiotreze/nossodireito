#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent: Conecta gov.br — Sync Quinzenal
=======================================
Monitora alterações nos serviços oficiais (gov.br / Conecta gov.br)
referenciados em data/direitos.json. Detecta mudanças por hash do conteúdo
HTML normalizado e gera relatório (e, opcionalmente, issue no GitHub).

Estratégia (read-only, idempotente):
1. Coleta URLs gov.br únicas de fontes[] e links[] das 42 categorias.
2. Faz GET com timeout, captura ETag/Last-Modified quando disponíveis.
3. Calcula hash SHA-256 do <main>/<article>/<body> (texto normalizado).
4. Compara com data/conecta_sync_state.json (estado anterior).
5. Emite relatório JSON. Se mudanças detectadas, sugere abrir issue.

NUNCA modifica direitos.json — apenas detecta drift e alerta humano.

Uso:
    python scripts/agent_conecta_govbr_sync.py
    python scripts/agent_conecta_govbr_sync.py --update-state
    python scripts/agent_conecta_govbr_sync.py --json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_JSON = PROJECT_ROOT / "data" / "direitos.json"
STATE_JSON = PROJECT_ROOT / "data" / "conecta_sync_state.json"
USER_AGENT = (
    "NossoDireitoBot/1.0 (+https://nossodireito.org.br; "
    "sync quinzenal Conecta gov.br; contato: contato@nossodireito.org.br)"
)
TIMEOUT = 20
# Apenas domínios oficiais Conecta gov.br / serviços federais
ALLOWED_HOSTS = (
    "www.gov.br",
    "gov.br",
)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def collect_govbr_urls(data: dict) -> list[str]:
    """Extrai URLs gov.br únicas de fontes[] e links[] das categorias."""
    urls: set[str] = set()
    for fonte in data.get("fontes", []):
        u = fonte.get("url", "")
        if _is_govbr(u):
            urls.add(u)
    for cat in data.get("categorias", []):
        for link in cat.get("links", []):
            u = link.get("url", "")
            if _is_govbr(u):
                urls.add(u)
        for fonte in cat.get("fontes", []):
            u = fonte.get("url", "")
            if _is_govbr(u):
                urls.add(u)
    return sorted(urls)


def _is_govbr(url: str) -> bool:
    if not url:
        return False
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        return False
    return host in ALLOWED_HOSTS


def fetch_normalized(url: str) -> dict:
    """GET + extrai texto normalizado + ETag/Last-Modified. Não levanta exceção."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    out = {
        "url": url,
        "status": None,
        "etag": None,
        "last_modified": None,
        "hash": None,
        "length": 0,
        "error": None,
    }
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310
            out["status"] = resp.status
            out["etag"] = resp.headers.get("ETag")
            out["last_modified"] = resp.headers.get("Last-Modified")
            body = resp.read(2_000_000)  # 2MB hard cap
            text = body.decode("utf-8", errors="replace")
            # Normaliza: remove tags + colapsa espaços
            stripped = TAG_RE.sub(" ", text)
            normalized = WS_RE.sub(" ", stripped).strip()
            out["length"] = len(normalized)
            out["hash"] = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    except urllib.error.HTTPError as exc:
        out["status"] = exc.code
        out["error"] = f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        out["error"] = str(exc)[:200]
    return out


def load_state() -> dict:
    if not STATE_JSON.exists():
        return {"version": 1, "checked_at": None, "urls": {}}
    try:
        return json.loads(STATE_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": 1, "checked_at": None, "urls": {}}


def save_state(state: dict) -> None:
    STATE_JSON.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def diff_against_state(state: dict, results: list[dict]) -> dict:
    """Compara hashes atuais vs. anteriores. Retorna sumário."""
    changed: list[dict] = []
    new: list[dict] = []
    errors: list[dict] = []
    unchanged = 0
    prev = state.get("urls", {})
    for r in results:
        if r["error"]:
            errors.append({"url": r["url"], "error": r["error"], "status": r["status"]})
            continue
        prev_entry = prev.get(r["url"])
        if not prev_entry:
            new.append({"url": r["url"], "hash": r["hash"]})
        elif prev_entry.get("hash") != r["hash"]:
            changed.append({
                "url": r["url"],
                "old_hash": prev_entry.get("hash"),
                "new_hash": r["hash"],
                "old_checked": prev_entry.get("checked_at"),
            })
        else:
            unchanged += 1
    return {
        "changed": changed,
        "new": new,
        "errors": errors,
        "unchanged": unchanged,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Conecta gov.br")
    parser.add_argument("--update-state", action="store_true",
                        help="Persiste estado atual em data/conecta_sync_state.json")
    parser.add_argument("--json", action="store_true",
                        help="Saída em JSON (para CI)")
    parser.add_argument("--max-urls", type=int, default=0,
                        help="Limita N URLs (0 = todas)")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Delay (s) entre requisições (cortesia)")
    args = parser.parse_args()

    if not DATA_JSON.exists():
        print(f"ERRO: {DATA_JSON} não encontrado", file=sys.stderr)
        return 2

    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    urls = collect_govbr_urls(data)
    if args.max_urls > 0:
        urls = urls[: args.max_urls]

    if not args.json:
        print(f"🔄 Conecta gov.br Sync — {len(urls)} URLs gov.br")
        print(f"📅 Iniciado: {datetime.now(timezone.utc).isoformat()}")

    results: list[dict] = []
    for i, url in enumerate(urls, 1):
        r = fetch_normalized(url)
        results.append(r)
        if not args.json:
            mark = "✅" if r["hash"] else f"❌ {r['error'] or r['status']}"
            print(f"  [{i:3d}/{len(urls)}] {mark}  {url}")
        if args.delay > 0 and i < len(urls):
            time.sleep(args.delay)

    state = load_state()
    diff = diff_against_state(state, results)

    now = datetime.now(timezone.utc).isoformat()
    if args.update_state:
        new_state = {
            "version": 1,
            "checked_at": now,
            "urls": {
                r["url"]: {
                    "hash": r["hash"],
                    "etag": r["etag"],
                    "last_modified": r["last_modified"],
                    "status": r["status"],
                    "checked_at": now,
                }
                for r in results
                if r["hash"]  # só persiste sucessos
            },
        }
        save_state(new_state)

    summary = {
        "checked_at": now,
        "total": len(urls),
        "ok": sum(1 for r in results if r["hash"]),
        "errors": len(diff["errors"]),
        "changed": len(diff["changed"]),
        "new": len(diff["new"]),
        "unchanged": diff["unchanged"],
        "details": diff,
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("\n" + "=" * 60)
        print(f"  Total: {summary['total']}  ✅ OK: {summary['ok']}")
        print(f"  🔄 Alterados: {summary['changed']}")
        print(f"  ✨ Novos: {summary['new']}")
        print(f"  ➡️  Inalterados: {summary['unchanged']}")
        print(f"  ❌ Erros: {summary['errors']}")
        print("=" * 60)
        if diff["changed"]:
            print("\n🔄 URLs com mudança de conteúdo:")
            for c in diff["changed"]:
                print(f"  - {c['url']}")
        if diff["errors"]:
            print("\n❌ Erros:")
            for e in diff["errors"][:10]:
                print(f"  - {e['url']}  ({e['error'] or e['status']})")

    # Exit 0 sempre (drift não é falha — apenas alerta).
    return 0


if __name__ == "__main__":
    sys.exit(main())
