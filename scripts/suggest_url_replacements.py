#!/usr/bin/env python3
"""
suggest_url_replacements.py — para cada URL quebrada em data/direitos.json,
sugere candidatos via (1) sitemap.xml do subdomínio gov.br, (2) busca DuckDuckGo
HTML como fallback. Imprime tabela markdown para revisão humana.

Uso:
  python3 scripts/suggest_url_replacements.py            # processa data/direitos.json
  python3 scripts/suggest_url_replacements.py URL1 URL2  # ad-hoc
"""

from __future__ import annotations
import gzip
import io
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
TIMEOUT = 12
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "direitos.json"


def fetch(url: str, timeout: int = TIMEOUT) -> tuple[int, bytes, str]:
    """Returns (status, body, final_url). Returns (-1, b'', '') on error."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            if r.headers.get("content-encoding") == "gzip":
                body = gzip.decompress(body)
            return r.status, body, r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, b"", url
    except Exception:
        return -1, b"", url


def head_ok(url: str) -> int:
    """Returns HTTP status (200/3xx/4xx) or -1 on network error. Uses GET (HEAD often blocked)."""
    s, _, _ = fetch(url, timeout=8)
    return s


# Cache sitemap por subdomínio
_SITEMAP_CACHE: dict[str, list[str]] = {}


def sitemap_urls_for(broken_url: str) -> list[str]:
    """Tenta achar e baixar sitemap.xml correspondente ao subdomínio do URL."""
    p = urllib.parse.urlparse(broken_url)
    host = p.netloc  # ex: www.gov.br
    # Path "section": primeiro segmento do path antes de /pt-br/
    parts = [s for s in p.path.split("/") if s]
    section = parts[0] if parts and parts[0] != "pt-br" else "pt-br"

    candidates = [
        f"https://{host}/{section}/sitemap.xml",
        f"https://{host}/{section}/pt-br/sitemap.xml",
        f"https://{host}/sitemap.xml",
    ]
    key = f"{host}/{section}"
    if key in _SITEMAP_CACHE:
        return _SITEMAP_CACHE[key]

    for sm in candidates:
        status, body, _ = fetch(sm)
        if status == 200 and body:
            try:
                # Extrai <loc>…</loc>
                urls = re.findall(rb"<loc>([^<]+)</loc>", body)
                decoded = [u.decode("utf-8", errors="ignore").strip() for u in urls]
                # Se vier sitemap-index, baixa filhos (limita 5)
                if decoded and decoded[0].endswith(".xml"):
                    all_urls: list[str] = []
                    for child in decoded[:5]:
                        s2, b2, _ = fetch(child)
                        if s2 == 200:
                            all_urls.extend(
                                u.decode("utf-8", "ignore").strip()
                                for u in re.findall(rb"<loc>([^<]+)</loc>", b2)
                            )
                    decoded = all_urls
                _SITEMAP_CACHE[key] = decoded
                return decoded
            except Exception:
                pass
    _SITEMAP_CACHE[key] = []
    return []


def slug_of(url: str) -> str:
    return urllib.parse.urlparse(url).path.rstrip("/").split("/")[-1]


def keywords_of(url: str) -> list[str]:
    """Palavras-chave do slug + último diretório."""
    p = urllib.parse.urlparse(url).path
    parts = [s for s in p.split("/") if s and s not in ("pt-br", "assuntos")]
    tokens: set[str] = set()
    for seg in parts[-2:]:
        for w in re.split(r"[-_]", seg):
            if len(w) >= 4:
                tokens.add(w.lower())
    return sorted(tokens)


def fuzzy(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def rank_candidates(broken: str, pool: list[str], topn: int = 5) -> list[tuple[float, str]]:
    target_slug = slug_of(broken).lower()
    target_kw = set(keywords_of(broken))
    scored: list[tuple[float, str]] = []
    for u in pool:
        slug = slug_of(u).lower()
        ukw = set(keywords_of(u))
        kw_overlap = (
            len(target_kw & ukw) / max(1, len(target_kw)) if target_kw else 0
        )
        ratio = fuzzy(target_slug, slug)
        score = 0.7 * kw_overlap + 0.3 * ratio
        if score > 0.25:
            scored.append((score, u))
    scored.sort(reverse=True)
    return scored[:topn]


def duckduckgo_search(query: str, limit: int = 5) -> list[str]:
    """Scrape DuckDuckGo HTML como último recurso."""
    url = "https://duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    status, body, _ = fetch(url)
    if status != 200 or not body:
        return []
    html = body.decode("utf-8", "ignore")
    # Resultados: <a class="result__url" href="…">
    raw = re.findall(r'<a[^>]+class="result__url"[^>]+href="([^"]+)"', html)
    out: list[str] = []
    for r in raw:
        # DDG usa redirect uddg=URL_ESCAPADA
        m = re.search(r"uddg=([^&]+)", r)
        if m:
            try:
                out.append(urllib.parse.unquote(m.group(1)))
            except Exception:
                pass
        elif r.startswith("http"):
            out.append(r)
    # dedup preservando ordem
    seen, dedup = set(), []
    for u in out:
        if u not in seen:
            seen.add(u)
            dedup.append(u)
        if len(dedup) >= limit:
            break
    return dedup


def collect_broken_urls() -> list[str]:
    """Extrai todos URLs únicos de data/direitos.json e devolve apenas os 4xx/5xx/timeouts."""
    if not DATA.exists():
        return []
    obj = json.loads(DATA.read_text(encoding="utf-8"))
    urls: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, str) and node.startswith("http"):
            urls.add(node.strip())

    walk(obj)
    print(f"# {len(urls)} URLs únicos em data/direitos.json. Validando…", file=sys.stderr)

    broken: list[str] = []
    with ThreadPoolExecutor(max_workers=16) as ex:
        for u, fut in [(u, ex.submit(head_ok, u)) for u in sorted(urls)]:
            s = fut.result()
            if s == -1 or s >= 400:
                broken.append(u)
                print(f"  ✗ {s} {u}", file=sys.stderr)
    return broken


def suggest_for(broken: str) -> list[tuple[float, str, str]]:
    """Returns list of (score, candidate_url, source). Validates each (HEAD 200)."""
    out: list[tuple[float, str, str]] = []

    # 1) sitemap do subdomínio
    pool = sitemap_urls_for(broken)
    if pool:
        for score, u in rank_candidates(broken, pool, topn=5):
            out.append((score, u, "sitemap"))

    # 2) fallback DuckDuckGo se nada bom (>0.6) no sitemap
    if not out or out[0][0] < 0.6:
        p = urllib.parse.urlparse(broken)
        host = p.netloc
        parts = [s for s in p.path.split("/") if s]
        section = parts[0] if parts else ""
        slug = (slug_of(broken) or host).replace("-", " ")
        site = f"{host}/{section}" if section else host
        q = f"site:{site} {slug}"
        try:
            for u in duckduckgo_search(q, limit=4):
                out.append((0.5, u, "ddg"))
        except Exception:
            pass

    # validar cada um (HEAD)
    validated: list[tuple[float, str, str]] = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = {ex.submit(head_ok, u): (sc, u, src) for sc, u, src in out}
        for fut in as_completed(results):
            sc, u, src = results[fut]
            s = fut.result()
            if 200 <= s < 400:
                validated.append((sc, u, src))
    validated.sort(reverse=True)
    return validated[:5]


def main() -> int:
    if len(sys.argv) > 1:
        broken_urls = [a for a in sys.argv[1:] if a.startswith("http")]
    else:
        broken_urls = collect_broken_urls()

    if not broken_urls:
        print("Nenhuma URL quebrada encontrada.")
        return 0

    print(f"\n# Sugestões para {len(broken_urls)} URL(s) quebrada(s)\n")
    print("| # | URL quebrada | Sugestão | Score | Fonte |")
    print("|---|---|---|---|---|")
    for i, b in enumerate(broken_urls, 1):
        sugs = suggest_for(b)
        if not sugs:
            print(f"| {i} | `{b}` | _(nenhum candidato)_ | — | — |")
        else:
            first = True
            for sc, u, src in sugs:
                bcell = f"`{b}`" if first else ""
                idx = str(i) if first else ""
                print(f"| {idx} | {bcell} | `{u}` | {sc:.2f} | {src} |")
                first = False
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
