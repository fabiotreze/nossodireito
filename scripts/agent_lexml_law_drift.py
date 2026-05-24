#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent: LexML Law Drift — Hash diff + lookup SRU
================================================
Monitora alterações no TEXTO das leis (planalto.gov.br) referenciadas em
`data/direitos.json` (campo `categorias[].base_legal[].link`).

Complementar ao agent_conecta_govbr_sync.py (S4):
- S4 monitora URLs gov.br de serviços/páginas institucionais.
- S6 (este) monitora especificamente o TEXTO LEGAL nas leis, com
  enriquecimento opcional de metadados via LexML.

Estratégia (read-only, idempotente):
1. Extrai URLs únicas planalto.gov.br de `base_legal[].link`.
2. GET, normaliza HTML (remove tags, scripts, comentários), SHA-256.
3. Constrói LexML lookup URL para cada lei (apoio à revisão humana).
4. Compara hash atual vs. baseline `data/lexml_law_state.json`.
5. Sinaliza alterações para revisão humana (não modifica direitos.json).

Uso:
    python scripts/agent_lexml_law_drift.py
    python scripts/agent_lexml_law_drift.py --update-state
    python scripts/agent_lexml_law_drift.py --json
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
from urllib.parse import quote, urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_JSON = PROJECT_ROOT / "data" / "direitos.json"
STATE_JSON = PROJECT_ROOT / "data" / "lexml_law_state.json"
USER_AGENT = (
    "NossoDireitoBot/1.0 (+https://nossodireito.org.br; "
    "monitor de drift legal mensal; contato: contato@nossodireito.org.br)"
)
TIMEOUT = 25
PLANALTO_HOSTS = ("www.planalto.gov.br", "planalto.gov.br")
LEXML_SEARCH = "https://www.lexml.gov.br/busca/search?keyword="

# Regex para extrair número e ano da Lei a partir do título "Lei 8.742/1993 (LOAS)"
LEI_RE = re.compile(
    r"(?:Lei(?:\s+Complementar)?|LC|Decreto(?:[\-\s]Lei)?|EC|Constituição)"
    r"\s*n?\.?\s*([\d\.]+)?(?:\s*/\s*(\d{4}))?",
    re.IGNORECASE,
)
TAG_RE = re.compile(r"<(script|style|noscript)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
ANY_TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def collect_law_links(data: dict) -> list[dict]:
    """Extrai (lei, artigo, link) únicos planalto.gov.br de base_legal."""
    seen: dict[str, dict] = {}
    for cat in data.get("categorias", []):
        for bl in cat.get("base_legal", []):
            if not isinstance(bl, dict):
                continue
            link = (bl.get("link") or "").strip()
            if not link or not _is_planalto(link):
                continue
            if link in seen:
                continue
            seen[link] = {
                "lei": bl.get("lei", ""),
                "artigo": bl.get("artigo", ""),
                "link": link,
                "categoria_id": cat.get("id"),
            }
    return sorted(seen.values(), key=lambda r: r["link"])


def _is_planalto(url: str) -> bool:
    try:
        return (urlparse(url).hostname or "") in PLANALTO_HOSTS
    except ValueError:
        return False


def lexml_lookup_url(lei_str: str) -> str:
    """Gera URL de busca LexML (apoio humano) para uma lei."""
    if not lei_str:
        return LEXML_SEARCH
    return LEXML_SEARCH + quote(lei_str)


def fetch_and_hash(url: str) -> dict:
    """GET → normaliza (sem tags/scripts/comentários) → SHA-256."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    out = {
        "url": url,
        "status": None,
        "hash": None,
        "length": 0,
        "etag": None,
        "last_modified": None,
        "error": None,
    }
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310
            out["status"] = resp.status
            out["etag"] = resp.headers.get("ETag")
            out["last_modified"] = resp.headers.get("Last-Modified")
            body = resp.read(5_000_000)  # 5MB cap (leis grandes)
            text = body.decode("latin-1", errors="replace")  # planalto usa latin-1 em alguns docs antigos
            text = COMMENT_RE.sub(" ", text)
            text = TAG_RE.sub(" ", text)
            stripped = ANY_TAG_RE.sub(" ", text)
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
        return {"version": 1, "checked_at": None, "laws": {}}
    try:
        return json.loads(STATE_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": 1, "checked_at": None, "laws": {}}


def save_state(state: dict) -> None:
    STATE_JSON.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def diff_against_state(state: dict, results: list[dict]) -> dict:
    changed, new, errors = [], [], []
    unchanged = 0
    prev = state.get("laws", {})
    for r in results:
        if r["fetch"]["error"]:
            errors.append({
                "url": r["link"],
                "lei": r["lei"],
                "error": r["fetch"]["error"],
                "status": r["fetch"]["status"],
            })
            continue
        prev_entry = prev.get(r["link"])
        if not prev_entry:
            new.append({"lei": r["lei"], "link": r["link"], "hash": r["fetch"]["hash"]})
        elif prev_entry.get("hash") != r["fetch"]["hash"]:
            changed.append({
                "lei": r["lei"],
                "artigo": r["artigo"],
                "link": r["link"],
                "lexml": r["lexml"],
                "old_hash": prev_entry.get("hash"),
                "new_hash": r["fetch"]["hash"],
                "old_checked": prev_entry.get("checked_at"),
            })
        else:
            unchanged += 1
    return {"changed": changed, "new": new, "errors": errors, "unchanged": unchanged}


def main() -> int:
    parser = argparse.ArgumentParser(description="LexML Law Drift Monitor")
    parser.add_argument("--update-state", action="store_true",
                        help="Persiste estado em data/lexml_law_state.json")
    parser.add_argument("--json", action="store_true", help="Saída em JSON")
    parser.add_argument("--max-laws", type=int, default=0,
                        help="Limita N leis (0 = todas)")
    parser.add_argument("--delay", type=float, default=0.6,
                        help="Delay (s) entre requisições (cortesia ao planalto)")
    args = parser.parse_args()

    if not DATA_JSON.exists():
        print(f"ERRO: {DATA_JSON} não encontrado", file=sys.stderr)
        return 2

    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    laws = collect_law_links(data)
    if args.max_laws > 0:
        laws = laws[: args.max_laws]

    if not args.json:
        print(f"⚖️  LexML Law Drift — {len(laws)} leis planalto.gov.br")
        print(f"📅 Iniciado: {datetime.now(timezone.utc).isoformat()}")

    results: list[dict] = []
    for i, law in enumerate(laws, 1):
        fetch = fetch_and_hash(law["link"])
        result = {
            "lei": law["lei"],
            "artigo": law["artigo"],
            "link": law["link"],
            "categoria_id": law["categoria_id"],
            "lexml": lexml_lookup_url(law["lei"]),
            "fetch": fetch,
        }
        results.append(result)
        if not args.json:
            mark = "✅" if fetch["hash"] else f"❌ {fetch['error'] or fetch['status']}"
            print(f"  [{i:3d}/{len(laws)}] {mark}  {law['lei'][:50]:50s}  {law['link']}")
        if args.delay > 0 and i < len(laws):
            time.sleep(args.delay)

    state = load_state()
    diff = diff_against_state(state, results)

    now = datetime.now(timezone.utc).isoformat()
    if args.update_state:
        new_state = {
            "version": 1,
            "checked_at": now,
            "laws": {
                r["link"]: {
                    "lei": r["lei"],
                    "artigo": r["artigo"],
                    "hash": r["fetch"]["hash"],
                    "etag": r["fetch"]["etag"],
                    "last_modified": r["fetch"]["last_modified"],
                    "status": r["fetch"]["status"],
                    "lexml": r["lexml"],
                    "checked_at": now,
                }
                for r in results
                if r["fetch"]["hash"]
            },
        }
        save_state(new_state)

    summary = {
        "checked_at": now,
        "total": len(laws),
        "ok": sum(1 for r in results if r["fetch"]["hash"]),
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
        print(f"  🔄 Alteradas: {summary['changed']}")
        print(f"  ✨ Novas: {summary['new']}")
        print(f"  ➡️  Inalteradas: {summary['unchanged']}")
        print(f"  ❌ Erros: {summary['errors']}")
        print("=" * 60)
        if diff["changed"]:
            print("\n🔄 Leis com TEXTO alterado (revisar urgentemente):")
            for c in diff["changed"]:
                print(f"  - {c['lei']}  ({c['artigo']})")
                print(f"      {c['link']}")
                print(f"      LexML: {c['lexml']}")
        if diff["errors"]:
            print("\n❌ Erros transitórios:")
            for e in diff["errors"][:10]:
                print(f"  - {e['lei']}: {e['error'] or e['status']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
