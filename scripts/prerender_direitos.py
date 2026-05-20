#!/usr/bin/env python3
"""
prerender_direitos.py — Gera páginas HTML estáticas por categoria de direito
para indexação SEO (Google/Bing) com URLs limpas e conteúdo profundo.

Saída:
  direitos/<id>/index.html   (1 por categoria — N pages)
  sitemap.xml                (regenerado com home + N direitos)

Cada página contém:
  - <title>, meta description, canonical, Open Graph únicos
  - H1 + base legal, requisitos, documentos, passo-a-passo
  - JSON-LD Article + BreadcrumbList
  - Link de volta para home + link para fontes oficiais

Servidor (server.js) resolve /direitos/<id>/ -> direitos/<id>/index.html via
clean-URL resolution (sem necessidade de .htaccess/Nginx rewrites).

Uso:
    python3 scripts/prerender_direitos.py
    python3 scripts/prerender_direitos.py --check    # somente valida, não escreve
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "direitos.json"
OUT_DIR = ROOT / "direitos"
SITEMAP_FILE = ROOT / "sitemap.xml"
BASE_URL = "https://nossodireito.fabiotreze.com"

# ─────────────────────────── Template HTML ───────────────────────────


def esc(s: Any) -> str:
    return html.escape(str(s), quote=True)


def render_list(items: list, ordered: bool = False) -> str:
    if not items:
        return ""
    tag = "ol" if ordered else "ul"
    lis = "\n".join(f"      <li>{esc(i)}</li>" for i in items)
    return f"    <{tag}>\n{lis}\n    </{tag}>"


def render_base_legal(items: list[dict]) -> str:
    if not items:
        return ""
    rows = []
    for bl in items:
        lei = esc(bl.get("lei", ""))
        artigo = esc(bl.get("artigo", ""))
        link = esc(bl.get("link", ""))
        if link:
            rows.append(
                f'      <li><a href="{link}" rel="external noopener" target="_blank">{lei}</a> — {artigo}</li>'
            )
        else:
            rows.append(f"      <li>{lei} — {artigo}</li>")
    return "    <ul>\n" + "\n".join(rows) + "\n    </ul>"


def render_links(items: list) -> str:
    if not items:
        return ""
    rows = []
    for ln in items:
        if isinstance(ln, dict):
            title = esc(ln.get("titulo") or ln.get("nome") or ln.get("url", ""))
            url = esc(ln.get("url", ""))
        else:
            title = url = esc(ln)
        if url:
            rows.append(
                f'      <li><a href="{url}" rel="external noopener" target="_blank">{title}</a></li>'
            )
    if not rows:
        return ""
    return "    <ul>\n" + "\n".join(rows) + "\n    </ul>"


def build_jsonld(cat: dict, url: str) -> str:
    """Retorna JSON-LD Article + BreadcrumbList."""
    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": cat["titulo"],
        "description": cat.get("resumo", ""),
        "inLanguage": "pt-BR",
        "isAccessibleForFree": True,
        "url": url,
        "datePublished": "2026-02-13",
        "dateModified": str(date.today()),
        "author": {"@type": "Organization", "name": "NossoDireito"},
        "publisher": {
            "@type": "Organization",
            "name": "NossoDireito",
            "url": BASE_URL + "/",
        },
        "about": cat.get("tags", []),
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "NossoDireito",
                "item": BASE_URL + "/",
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "Direitos PcD",
                "item": BASE_URL + "/#categorias",
            },
            {"@type": "ListItem", "position": 3, "name": cat["titulo"], "item": url},
        ],
    }
    return (
        '<script type="application/ld+json">\n'
        + json.dumps(article, ensure_ascii=False, indent=2)
        + "\n</script>\n"
        + '<script type="application/ld+json">\n'
        + json.dumps(breadcrumb, ensure_ascii=False, indent=2)
        + "\n</script>"
    )


PAGE_TEMPLATE = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} | NossoDireito</title>
  <meta name="description" content="{description}" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
  <meta name="author" content="NossoDireito" />
  <link rel="canonical" href="{url}" />
  <link rel="alternate" hreflang="pt-BR" href="{url}" />
  <meta property="og:title" content="{title} | NossoDireito" />
  <meta property="og:description" content="{description}" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="{url}" />
  <meta property="og:locale" content="pt_BR" />
  <meta property="og:site_name" content="NossoDireito" />
  <meta property="og:image" content="{base}/images/og-image.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{title} | NossoDireito" />
  <meta name="twitter:description" content="{description}" />
  <meta name="theme-color" content="#1e3a8a" />
  <link rel="icon" type="image/x-icon" href="/images/favicon.ico" />
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    :root{{--primary:#1e40af;--primary-dark:#1e3a8a;--text:#1e293b;--surface:#fff;--border:#e2e8f0}}
    @media (prefers-color-scheme:dark){{:root{{--primary:#60a5fa;--primary-dark:#3b82f6;--text:#f1f5f9;--surface:#0f172a;--border:#334155}}}}
    html{{scroll-behavior:smooth;font-size:16px}}
    body{{font-family:"Segoe UI",system-ui,-apple-system,sans-serif;color:var(--text);background:var(--surface);line-height:1.6;-webkit-font-smoothing:antialiased}}
    .container{{max-width:880px;margin:0 auto;padding:0 20px}}
    header.topbar{{background:var(--primary-dark);color:#fff;padding:1rem 0;margin-bottom:2rem}}
    header.topbar a{{color:#fff;text-decoration:none;font-weight:700;font-size:1.1rem}}
    header.topbar a:hover{{text-decoration:underline}}
    main{{padding-bottom:3rem}}
    nav.breadcrumb{{font-size:.9rem;color:#64748b;margin-bottom:1rem}}
    nav.breadcrumb a{{color:var(--primary);text-decoration:none}}
    nav.breadcrumb a:hover{{text-decoration:underline}}
    h1{{font-size:2rem;color:var(--primary-dark);margin-bottom:.5rem;line-height:1.2}}
    .resumo{{font-size:1.1rem;color:#475569;margin:1rem 0 2rem;padding:1rem;background:#f1f5f9;border-left:4px solid var(--primary);border-radius:4px}}
    @media (prefers-color-scheme:dark){{.resumo{{background:#1e293b;color:#cbd5e1}}}}
    section{{margin:2rem 0}}
    h2{{font-size:1.35rem;color:var(--primary-dark);margin-bottom:.75rem;border-bottom:2px solid var(--border);padding-bottom:.3rem}}
    ul,ol{{padding-left:1.5rem;margin:.5rem 0}}
    li{{margin:.35rem 0}}
    a{{color:var(--primary)}}
    .meta-info{{font-size:.85rem;color:#64748b;margin-top:2rem;padding-top:1rem;border-top:1px solid var(--border)}}
    .aviso{{background:#fef3c7;border-left:4px solid #f59e0b;padding:1rem;margin:2rem 0;border-radius:4px;font-size:.9rem;color:#78350f}}
    @media (prefers-color-scheme:dark){{.aviso{{background:#451a03;color:#fde68a}}}}
    footer{{text-align:center;padding:2rem 1rem;border-top:1px solid var(--border);font-size:.85rem;color:#64748b;margin-top:3rem}}
  </style>
  {jsonld}
</head>
<body>
  <header class="topbar"><div class="container"><a href="/">⚖️ NossoDireito — Voltar à página inicial</a></div></header>
  <main class="container">
    <nav class="breadcrumb" aria-label="Navegação estrutural">
      <a href="/">Início</a> &rsaquo; <a href="/#categorias">Direitos PcD</a> &rsaquo; <span>{title_plain}</span>
    </nav>
    <article>
      <h1>{icone} {title}</h1>
      <p class="resumo">{description}</p>
{sections}
      <p class="meta-info">Versão dos dados: {versao} — atualizado em {ultima_atualizacao}.</p>
      <div class="aviso"><strong>Aviso:</strong> {aviso}</div>
    </article>
  </main>
  <footer><p>NossoDireito — Projeto sem fins lucrativos · <a href="/">Página inicial</a> · <a href="/sitemap.xml">Sitemap</a></p></footer>
</body>
</html>
"""


def build_sections(cat: dict) -> str:
    parts: list[str] = []

    def section(title: str, body: str) -> None:
        if body and body.strip():
            parts.append(f"      <section>\n        <h2>{esc(title)}</h2>\n{body}\n      </section>")

    section("Base legal", render_base_legal(cat.get("base_legal", [])))
    if cat.get("valor"):
        section(
            "Valor / Benefício",
            f"        <p>{esc(cat['valor'])}</p>",
        )
    section("Requisitos", render_list(cat.get("requisitos", [])))
    section("Documentos necessários", render_list(cat.get("documentos", [])))
    section("Passo a passo", render_list(cat.get("passo_a_passo", []), ordered=True))
    if cat.get("dicas"):
        section("Dicas práticas", render_list(cat["dicas"]))
    if cat.get("onde"):
        onde = cat["onde"]
        if isinstance(onde, str):
            section("Onde solicitar", f"        <p>{esc(onde)}</p>")
        elif isinstance(onde, list):
            section("Onde solicitar", render_list(onde))
    section("Links oficiais", render_links(cat.get("links", [])))
    if cat.get("emergencia"):
        section("Em caso de emergência ou recusa", render_emergencia(cat["emergencia"]))

    return "\n".join(parts)


def render_emergencia(e: Any) -> str:
    """Renderiza bloco de emergência (dict ou string)."""
    if isinstance(e, str):
        return f"        <p>{esc(e)}</p>"
    if not isinstance(e, dict):
        return ""
    parts: list[str] = []
    if e.get("titulo"):
        parts.append(f"        <h3>{esc(e['titulo'])}</h3>")
    if e.get("conflito"):
        parts.append(f"        <p><strong>Situação:</strong> {esc(e['conflito'])}</p>")
    if e.get("base_legal_resgate"):
        parts.append(
            f"        <p><strong>Base legal:</strong> {esc(e['base_legal_resgate'])}</p>"
        )
    if e.get("acao_imediata"):
        parts.append("        <p><strong>Ação imediata:</strong></p>")
        parts.append(render_list(e["acao_imediata"], ordered=True))
    if e.get("modelo_notificacao"):
        parts.append(
            f"        <p><strong>Modelo de notificação:</strong></p>\n"
            f"        <blockquote>{esc(e['modelo_notificacao'])}</blockquote>"
        )
    od = e.get("orgao_denuncia")
    if isinstance(od, dict):
        nome = esc(od.get("nome", ""))
        contato = esc(od.get("contato", ""))
        url = esc(od.get("url", ""))
        link = f' — <a href="{url}" rel="external noopener" target="_blank">{url}</a>' if url else ""
        parts.append(
            f"        <p><strong>Onde denunciar:</strong> {nome} ({contato}){link}</p>"
        )
    if e.get("aviso"):
        parts.append(f'        <p class="aviso-inline"><em>{esc(e["aviso"])}</em></p>')
    return "\n".join(parts)


def render_page(cat: dict, meta: dict) -> str:
    slug = cat["id"]
    url = f"{BASE_URL}/direitos/{slug}/"
    title = cat["titulo"]
    description = cat.get("resumo", title)[:300]
    return PAGE_TEMPLATE.format(
        title=esc(title),
        title_plain=esc(title),
        description=esc(description),
        url=url,
        base=BASE_URL,
        icone=esc(cat.get("icone", "")),
        sections=build_sections(cat),
        versao=esc(meta.get("versao", "")),
        ultima_atualizacao=esc(meta.get("ultima_atualizacao", "")),
        aviso=esc(meta.get("aviso", "")),
        jsonld=build_jsonld(cat, url),
    )


# ─────────────────────────── Sitemap ───────────────────────────


def render_sitemap(slugs: list[str], lastmod: str) -> str:
    urls = [
        (BASE_URL + "/", "1.0", "weekly"),
    ]
    for slug in slugs:
        urls.append((f"{BASE_URL}/direitos/{slug}/", "0.8", "monthly"))

    body = "\n".join(
        f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{lastmod}</lastmod>\n"
        f"    <changefreq>{cf}</changefreq>\n    <priority>{p}</priority>\n  </url>"
        for u, p, cf in urls
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!--\n  Sitemap NossoDireito — gerado por scripts/prerender_direitos.py\n"
        "  NÃO EDITE MANUALMENTE. Re-execute o script após alterar data/direitos.json.\n-->\n"
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + body
        + "\n</urlset>\n"
    )


# ─────────────────────────── Main ───────────────────────────


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--check",
        action="store_true",
        help="Não escreve arquivos; apenas valida que páginas existem e estão sincronizadas.",
    )
    args = p.parse_args()

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    categorias = data["categorias"]
    meta = {
        "versao": data.get("versao", ""),
        "ultima_atualizacao": data.get("ultima_atualizacao", str(date.today())),
        "aviso": data.get("aviso", ""),
    }

    slugs = [c["id"] for c in categorias]
    lastmod = meta["ultima_atualizacao"]

    if args.check:
        missing = []
        for slug in slugs:
            f = OUT_DIR / slug / "index.html"
            if not f.exists():
                missing.append(slug)
        sitemap_ok = SITEMAP_FILE.exists() and all(
            f"/direitos/{s}/" in SITEMAP_FILE.read_text(encoding="utf-8") for s in slugs
        )
        if missing:
            print(f"FAIL: páginas faltando ({len(missing)}): {missing}", file=sys.stderr)
        if not sitemap_ok:
            print("FAIL: sitemap.xml desatualizado", file=sys.stderr)
        if missing or not sitemap_ok:
            print("Rode: python3 scripts/prerender_direitos.py", file=sys.stderr)
            return 1
        print(f"OK: {len(slugs)} páginas + sitemap sincronizados")
        return 0

    # Generate
    OUT_DIR.mkdir(exist_ok=True)
    written = 0
    for cat in categorias:
        slug = cat["id"]
        page_dir = OUT_DIR / slug
        page_dir.mkdir(exist_ok=True)
        (page_dir / "index.html").write_text(render_page(cat, meta), encoding="utf-8")
        written += 1

    SITEMAP_FILE.write_text(render_sitemap(slugs, lastmod), encoding="utf-8")

    print(f"✅ Gerado: {written} páginas em direitos/ + sitemap.xml ({len(slugs) + 1} URLs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
