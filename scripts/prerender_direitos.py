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
    python3 scripts/prerender_direitos.py --check --mode home-only
    python3 scripts/prerender_direitos.py --check --mode prerender
"""
from __future__ import annotations

import argparse
import html
import json
import re
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
    :root{{--primary:#1e40af;--primary-dark:#1e3a8a;--text:#1e293b;--muted:#64748b;--surface:#fff;--surface-2:#f8fafc;--border:#e2e8f0}}
    @media (prefers-color-scheme:dark){{:root{{--primary:#60a5fa;--primary-dark:#3b82f6;--text:#f1f5f9;--muted:#94a3b8;--surface:#0f172a;--surface-2:#1e293b;--border:#334155}}}}
    html{{scroll-behavior:smooth;font-size:16px;scroll-padding-top:80px}}
    @media (prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}}}
    body{{font-family:"Segoe UI",system-ui,-apple-system,sans-serif;color:var(--text);background:var(--surface);line-height:1.6;-webkit-font-smoothing:antialiased}}
    .container{{max-width:1180px;margin:0 auto;padding:0 20px}}
    header.topbar{{background:var(--primary-dark);color:#fff;padding:1rem 0;margin-bottom:1.5rem;position:sticky;top:0;z-index:50}}
    header.topbar a{{color:#fff;text-decoration:none;font-weight:700;font-size:1.05rem}}
    header.topbar a:hover{{text-decoration:underline}}
    .scroll-progress{{position:fixed;top:0;left:0;height:3px;width:0;background:#fbbf24;z-index:100;transition:width 80ms linear}}
    @media (prefers-reduced-motion:reduce){{.scroll-progress{{transition:none}}}}
    main{{padding-bottom:3rem}}
    nav.breadcrumb{{font-size:.9rem;color:var(--muted);margin-bottom:1rem}}
    /* WCAG 2.4.4 / 1.4.1: links em bloco de texto devem ser distingu\u00edveis sem depender s\u00f3 de cor */
    nav.breadcrumb a{{color:var(--primary);text-decoration:underline}}
    nav.breadcrumb a:hover{{text-decoration:none}}
    h1{{font-size:1.85rem;color:var(--primary-dark);margin-bottom:.5rem;line-height:1.2}}
    .resumo{{font-size:1.05rem;color:var(--text);margin:1rem 0 1.5rem;padding:.9rem 1rem;background:var(--surface-2);border-left:4px solid var(--primary);border-radius:6px}}
    .page-layout{{display:block}}
    @media (min-width:1024px){{.page-layout{{display:grid;grid-template-columns:220px 1fr;gap:32px;align-items:start}}}}
    .toc-sidebar{{display:none}}
    @media (min-width:1024px){{
      .toc-sidebar{{display:block;position:sticky;top:88px;max-height:calc(100vh - 110px);overflow-y:auto;padding:14px 12px;background:var(--surface-2);border:1px solid var(--border);border-radius:8px;font-size:.88rem}}
      .toc-sidebar h2{{font-size:.78rem;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);font-weight:700;margin-bottom:8px;border:none;padding:0}}
      .toc-sidebar ol{{list-style:none;padding:0;margin:0}}
      .toc-sidebar li{{margin:2px 0}}
      .toc-sidebar a{{display:block;padding:6px 8px;border-radius:4px;color:var(--text);text-decoration:none;line-height:1.3;border-left:3px solid transparent}}
      .toc-sidebar a:hover{{background:var(--border);color:var(--primary)}}
      .toc-sidebar a:focus-visible{{outline:2px solid var(--primary);outline-offset:1px}}
      .toc-sidebar a[aria-current="location"]{{background:var(--surface);color:var(--primary);font-weight:600;border-left-color:var(--primary)}}
    }}
    section{{margin:1.5rem 0;scroll-margin-top:88px}}
    h2{{font-size:1.25rem;color:var(--primary-dark);margin-bottom:.6rem;border-bottom:2px solid var(--border);padding-bottom:.3rem}}
    h3{{font-size:1rem;margin:.8rem 0 .4rem;color:var(--text)}}
    ul,ol{{padding-left:1.4rem;margin:.4rem 0}}
    li{{margin:.3rem 0}}
    p{{margin:.5rem 0}}
    a{{color:var(--primary)}}
    details.dicas{{margin:1rem 0;border:1px solid var(--border);border-radius:6px;background:var(--surface-2);padding:0}}
    details.dicas[open]{{padding-bottom:.5rem}}
    details.dicas > summary{{cursor:pointer;padding:.7rem 1rem;font-weight:600;color:var(--primary-dark);list-style:none;display:flex;align-items:center;gap:8px}}
    details.dicas > summary::-webkit-details-marker{{display:none}}
    details.dicas > summary::before{{content:"\u25b6";font-size:.7rem;transition:transform .15s}}
    details.dicas[open] > summary::before{{transform:rotate(90deg)}}
    details.dicas > summary:hover{{background:var(--border)}}
    details.dicas > summary:focus-visible{{outline:2px solid var(--primary);outline-offset:-2px}}
    details.dicas ul{{padding:0 1rem 0 2.2rem}}
    @media (prefers-reduced-motion:reduce){{details.dicas > summary::before{{transition:none}}}}
    .meta-info{{font-size:.85rem;color:var(--muted);margin-top:2rem;padding-top:1rem;border-top:1px solid var(--border)}}
    .aviso{{background:#fef3c7;border-left:4px solid #f59e0b;padding:1rem;margin:1.5rem 0;border-radius:4px;font-size:.9rem;color:#78350f}}
    @media (prefers-color-scheme:dark){{.aviso{{background:#451a03;color:#fde68a}}}}
    .emergencia-box{{background:#fef2f2;border-left:4px solid #dc2626;padding:1rem;border-radius:6px;margin:1rem 0}}
    @media (prefers-color-scheme:dark){{.emergencia-box{{background:#450a0a;color:#fecaca}}}}
    footer{{text-align:center;padding:2rem 1rem;border-top:1px solid var(--border);font-size:.85rem;color:var(--muted);margin-top:3rem}}
  </style>
  {jsonld}
</head>
<body>
  <div class="scroll-progress" id="scrollProgress" aria-hidden="true"></div>
  <header class="topbar"><div class="container"><a href="/">⚖️ NossoDireito — Voltar à página inicial</a></div></header>
  <main class="container">
    <nav class="breadcrumb" aria-label="Navegação estrutural">
      <a href="/">Início</a> &rsaquo; <a href="/#categorias">Direitos PcD</a> &rsaquo; <span>{title_plain}</span>
    </nav>
    <div class="page-layout">
      <aside class="toc-sidebar" aria-label="Sumário desta página">
        <h2>Nesta página</h2>
        <ol id="tocList"></ol>
      </aside>
      <article class="page-body">
        <h1>{icone} {title}</h1>
        <p class="resumo">{description}</p>
{sections}
        <p class="meta-info">Versão dos dados: {versao} — atualizado em {ultima_atualizacao}.</p>
        <div class="aviso"><strong>Aviso:</strong> {aviso}</div>
      </article>
    </div>
  </main>
  <footer><p>NossoDireito — Projeto sem fins lucrativos · <a href="/">Página inicial</a> · <a href="/sitemap.xml">Sitemap</a></p></footer>
  <script>
  (function(){{
    var sections = document.querySelectorAll('article.page-body > section[id]');
    var tocList = document.getElementById('tocList');
    var progress = document.getElementById('scrollProgress');
    if (tocList && sections.length){{
      var links = [];
      sections.forEach(function(sec){{
        var h2 = sec.querySelector('h2');
        if (!h2) return;
        var li = document.createElement('li');
        var a = document.createElement('a');
        a.href = '#' + sec.id;
        a.textContent = h2.textContent;
        li.appendChild(a);
        tocList.appendChild(li);
        links.push({{a:a, sec:sec}});
      }});
      if ('IntersectionObserver' in window && links.length){{
        var io = new IntersectionObserver(function(entries){{
          entries.forEach(function(en){{
            if (en.isIntersecting){{
              links.forEach(function(l){{
                if (l.sec === en.target) l.a.setAttribute('aria-current','location');
                else l.a.removeAttribute('aria-current');
              }});
            }}
          }});
        }}, {{rootMargin:'-40% 0px -55% 0px', threshold:0}});
        links.forEach(function(l){{ io.observe(l.sec); }});
      }}
    }}
    if (progress){{
      var raf = 0;
      function upd(){{
        var sc = document.documentElement;
        var pct = (sc.scrollTop) / Math.max(1, sc.scrollHeight - sc.clientHeight);
        progress.style.width = (Math.min(1, Math.max(0, pct)) * 100) + '%';
        raf = 0;
      }}
      window.addEventListener('scroll', function(){{ if (!raf) raf = requestAnimationFrame(upd); }}, {{passive:true}});
      upd();
    }}
  }})();
  </script>
</body>
</html>
"""


def build_sections(cat: dict) -> str:
    parts: list[str] = []

    def section(title: str, body: str, sid: str = "", extra_class: str = "") -> None:
        if body and body.strip():
            cls = f' class="{extra_class}"' if extra_class else ""
            sid_attr = f' id="{sid}"' if sid else ""
            parts.append(f"      <section{sid_attr}{cls}>\n        <h2>{esc(title)}</h2>\n{body}\n      </section>")

    section("Base legal", render_base_legal(cat.get("base_legal", [])), sid="base-legal")
    if cat.get("valor"):
        section(
            "Valor / Benefício",
            f"        <p>{esc(cat['valor'])}</p>",
            sid="valor",
        )
    section("Requisitos", render_list(cat.get("requisitos", [])), sid="requisitos")
    section("Documentos necessários", render_list(cat.get("documentos", [])), sid="documentos")
    section("Passo a passo", render_list(cat.get("passo_a_passo", []), ordered=True), sid="passo-a-passo")
    if cat.get("dicas"):
        # Dicas colapsáveis para reduzir muralha de texto em mobile
        dicas_html = render_list(cat["dicas"])
        body = (
            f'        <details class="dicas">\n'
            f'          <summary>Dicas práticas ({len(cat["dicas"])})</summary>\n'
            f'{dicas_html}\n'
            f'        </details>'
        )
        parts.append(f'      <section id="dicas">\n        <h2>Dicas práticas</h2>\n{body}\n      </section>')
    if cat.get("onde"):
        onde = cat["onde"]
        if isinstance(onde, str):
            section("Onde solicitar", f"        <p>{esc(onde)}</p>", sid="onde-solicitar")
        elif isinstance(onde, list):
            section("Onde solicitar", render_list(onde), sid="onde-solicitar")
    section("Links oficiais", render_links(cat.get("links", [])), sid="links-oficiais")
    if cat.get("emergencia"):
        emerg_body = render_emergencia(cat["emergencia"])
        wrapped = f'        <div class="emergencia-box">\n{emerg_body}\n        </div>'
        parts.append(
            f'      <section id="emergencia">\n        <h2>Em caso de emergência ou recusa</h2>\n{wrapped}\n      </section>'
        )

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


def check_home_only_mode() -> int:
    if not SITEMAP_FILE.exists():
        print("FAIL: sitemap.xml ausente", file=sys.stderr)
        return 1

    sitemap = SITEMAP_FILE.read_text(encoding="utf-8")
    locs = re.findall(r"<loc>(.*?)</loc>", sitemap)
    if f"{BASE_URL}/" not in locs:
        print("FAIL: sitemap.xml sem URL da home", file=sys.stderr)
        return 1

    deep_urls = [u for u in locs if u.startswith(f"{BASE_URL}/direitos/")]
    if deep_urls:
        print("FAIL: sitemap.xml contém URLs profundas em modo home-only", file=sys.stderr)
        return 1

    print("OK: modo home-only válido (sitemap com home apenas)")
    return 0


def check_prerender_mode(slugs: list[str]) -> int:
    missing = []
    for slug in slugs:
        f = OUT_DIR / slug / "index.html"
        if not f.exists():
            missing.append(slug)

    if not SITEMAP_FILE.exists():
        print("FAIL: sitemap.xml ausente", file=sys.stderr)
        return 1

    sitemap = SITEMAP_FILE.read_text(encoding="utf-8")
    sitemap_ok = all(f"/direitos/{s}/" in sitemap for s in slugs)
    if missing:
        print(f"FAIL: páginas faltando ({len(missing)}): {missing}", file=sys.stderr)
    if not sitemap_ok:
        print("FAIL: sitemap.xml desatualizado para modo prerender", file=sys.stderr)
    if missing or not sitemap_ok:
        print("Rode: python3 scripts/prerender_direitos.py", file=sys.stderr)
        return 1

    print(f"OK: modo prerender válido ({len(slugs)} páginas + sitemap sincronizados)")
    return 0


# ─────────────────────────── Main ───────────────────────────


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--check",
        action="store_true",
        help="Não escreve arquivos; apenas valida que páginas existem e estão sincronizadas.",
    )
    p.add_argument(
        "--mode",
        choices=["home-only", "prerender"],
        default="prerender",
        help=(
            "Modo de validação quando usado com --check. "
            "home-only valida sitemap com home apenas; prerender valida páginas profundas + sitemap."
        ),
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
        if args.mode == "home-only":
            return check_home_only_mode()
        return check_prerender_mode(slugs)

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
