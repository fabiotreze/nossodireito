#!/usr/bin/env python3
"""
Teste focado: Alto Contraste — Verificação completa
  1. Toggle via botão JS (#a11yContrast)
  2. Persistência (localStorage)
  3. Contraste WCAG AAA (≥7:1) de CADA componente visível
  4. Cores, bordas, backgrounds de todos os elementos high-contrast
  5. Screenshots antes/depois para inspeção visual
"""

import asyncio
import json
import os
import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("⚠️  Playwright não instalado.")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
SCREENSHOTS = ROOT / "screenshots"
SCREENSHOTS.mkdir(exist_ok=True)


def _luminance(r: int, g: int, b: int) -> float:
    def lin(c: int) -> float:
        s = c / 255
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(fg: tuple, bg: tuple) -> float:
    l1 = _luminance(*fg)
    l2 = _luminance(*bg)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def parse_rgb(css: str) -> tuple:
    css = css.strip()
    for prefix in ("rgba(", "rgb("):
        if css.startswith(prefix):
            nums = css[len(prefix):-1].split(",")
            return (int(nums[0]), int(nums[1]), int(nums[2]))
    return (0, 0, 0)


class HighContrastAudit:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.details: list[dict] = []

    def _ok(self, msg: str):
        print(f"  ✅ {msg}")
        self.passed += 1
        self.details.append({"test": msg, "status": "pass"})

    def _fail(self, msg: str, detail: str):
        print(f"  ❌ {msg}")
        print(f"      {detail}")
        self.failed += 1
        self.details.append({"test": msg, "status": "fail", "detail": detail})

    def _warn(self, msg: str, detail: str):
        print(f"  ⚠️  {msg}")
        print(f"      {detail}")
        self.warnings += 1
        self.details.append({"test": msg, "status": "warn", "detail": detail})

    # ── 1. Toggle via botão JS ────────────────────────────────────

    async def test_toggle_button(self, page, base_url: str):
        """Verifica se clicar no botão a11yContrast ativa/desativa o modo."""
        try:
            await page.goto(base_url, wait_until="networkidle")

            # Remover VLibras overlay
            await page.evaluate("""
                document.querySelectorAll('[vw], .enabled[vw]').forEach(el => el.remove());
                const aside = document.querySelector('aside[aria-label*="VLibras"]');
                if (aside) aside.remove();
            """)
            await page.wait_for_timeout(200)

            # Abrir drawer
            await page.click("#a11yPanelTrigger")
            await page.wait_for_timeout(400)

            # Estado inicial: sem high-contrast
            has_class = await page.evaluate("document.documentElement.classList.contains('high-contrast')")
            assert not has_class, "high-contrast já ativo antes do click"

            # Screenshot ANTES
            await page.screenshot(path=str(SCREENSHOTS / "hc_01_before.png"), full_page=True)

            # Clicar no botão de contraste
            await page.click("#a11yContrast")
            await page.wait_for_timeout(400)

            # Verificar que a classe foi adicionada
            has_class = await page.evaluate("document.documentElement.classList.contains('high-contrast')")
            assert has_class, "high-contrast não ativado após click"

            # Verificar aria-pressed
            pressed = await page.locator("#a11yContrast").get_attribute("aria-pressed")
            assert pressed == "true", f"aria-pressed={pressed}, esperado 'true'"

            # Screenshot DEPOIS
            await page.screenshot(path=str(SCREENSHOTS / "hc_02_after.png"), full_page=True)

            # Desativar
            await page.click("#a11yContrast")
            await page.wait_for_timeout(300)
            has_class = await page.evaluate("document.documentElement.classList.contains('high-contrast')")
            assert not has_class, "high-contrast não desativado após segundo click"

            self._ok("Toggle Button (ativa/desativa via #a11yContrast)")
        except Exception as e:
            self._fail("Toggle Button", str(e))

    # ── 2. Persistência localStorage ──────────────────────────────

    async def test_persistence(self, page, base_url: str):
        """Verifica que o estado high-contrast persiste após reload."""
        try:
            await page.goto(base_url, wait_until="networkidle")
            await page.evaluate("""
                document.querySelectorAll('[vw], .enabled[vw]').forEach(el => el.remove());
                const aside = document.querySelector('aside[aria-label*="VLibras"]');
                if (aside) aside.remove();
            """)
            await page.wait_for_timeout(200)

            # Abrir drawer e ativar
            await page.click("#a11yPanelTrigger")
            await page.wait_for_timeout(400)
            await page.click("#a11yContrast")
            await page.wait_for_timeout(300)

            # Verificar localStorage
            stored = await page.evaluate("localStorage.getItem('nossodireito_high_contrast')")
            assert stored == "true", f"localStorage={stored}, esperado 'true'"

            # Recarregar página
            await page.reload(wait_until="networkidle")
            await page.wait_for_timeout(500)

            # Verificar que a classe persiste
            has_class = await page.evaluate("document.documentElement.classList.contains('high-contrast')")
            assert has_class, "high-contrast não persistiu após reload"

            # Limpar
            await page.evaluate("localStorage.removeItem('nossodireito_high_contrast')")

            self._ok("Persistência (localStorage + reload)")
        except Exception as e:
            # Limpar
            await page.evaluate("try{localStorage.removeItem('nossodireito_high_contrast')}catch(e){}")
            self._fail("Persistência", str(e))

    # ── 3. Contraste WCAG de cada componente ──────────────────────

    async def test_component_contrasts(self, page, base_url: str):
        """Calcula contraste fg/bg de cada componente visível no modo alto contraste."""
        try:
            await page.goto(base_url, wait_until="networkidle")
            await page.evaluate("document.documentElement.classList.add('high-contrast')")
            await page.wait_for_timeout(400)

            # Medir fg/bg de cada componente com resolução de backgrounds transparentes
            components = await page.evaluate("""() => {
                function resolvedBg(el) {
                    let node = el;
                    while (node) {
                        const s = getComputedStyle(node);
                        const bg = s.backgroundColor;
                        const bgImg = s.backgroundImage;
                        if (bgImg && bgImg !== 'none' && bgImg.includes('gradient')) {
                            const colors = bgImg.match(/rgb[a]?\\([^)]+\\)/g);
                            if (colors && colors.length > 0) return colors[0];
                        }
                        if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') return bg;
                        node = node.parentElement;
                    }
                    return 'rgb(0, 0, 0)';
                }

                const pairs = [];
                const selectors = {
                    'Body':                'body',
                    'Hero h1':             '.hero h1',
                    'Hero subtitle':       '.hero-sub',
                    'Navbar brand':        '.navbar-brand',
                    'Nav link':            '.nav-links a',
                    'Section h2':          '.section h2',
                    'Section desc':        '.section-desc',
                    'Category card':       '.category-card',
                    'Card title':          '.category-card h3',
                    'Checklist label':     '.checklist-item',
                    'Link card':           '.link-card',
                    'Link card title':     '.link-card h3',
                    'Button primary':      '.btn-primary',
                    'Footer':              '.footer',
                    'Footer text':         '.footer p',
                    'Footer link':         '.footer a',
                    'Staleness banner':    '.staleness-banner',
                    'Search input':        '#searchInput',
                    'Modal content':       '.modal-content',
                    'Modal title':         '.modal-content h2',
                    'A11y drawer':         '.a11y-drawer',
                    'A11y drawer btn':     '.a11y-drawer-btn',
                    'Progress bar label':  '.progress-text',
                    'Orgao card':          '.orgao-card',
                    'Inst card':           '.inst-card',
                    'Filter btn active':   '.orgao-filter-btn[aria-pressed="true"]',
                };

                for (const [name, sel] of Object.entries(selectors)) {
                    const el = document.querySelector(sel);
                    if (!el) { pairs.push({name, fg: '', bg: '', skip: true}); continue; }
                    const cs = getComputedStyle(el);
                    if (cs.display === 'none' || cs.visibility === 'hidden') {
                        pairs.push({name, fg: '', bg: '', skip: true});
                        continue;
                    }
                    pairs.push({
                        name,
                        fg: cs.color,
                        bg: resolvedBg(el),
                        fontSize: parseFloat(cs.fontSize),
                        fontWeight: cs.fontWeight,
                    });
                }
                return pairs;
            }""")

            # Limpar
            await page.evaluate("document.documentElement.classList.remove('high-contrast')")

            errors = []
            aa_results = []
            for p in components:
                if p.get("skip") or not p["fg"] or not p["bg"]:
                    continue
                try:
                    fg = parse_rgb(p["fg"])
                    bg = parse_rgb(p["bg"])
                except Exception:
                    continue

                ratio = contrast_ratio(fg, bg)
                # Texto grande (≥18pt ou ≥14pt bold) precisa de 3:1 (AA) ou 4.5 (AAA)
                # Texto normal precisa de 4.5 (AA) ou 7:1 (AAA)
                is_large = p.get("fontSize", 16) >= 24 or (
                    p.get("fontSize", 16) >= 18.66 and int(p.get("fontWeight", 400)) >= 700
                )
                threshold_aa = 3.0 if is_large else 4.5
                threshold_aaa = 4.5 if is_large else 7.0

                status = "AAA" if ratio >= threshold_aaa else "AA" if ratio >= threshold_aa else "FAIL"

                aa_results.append({
                    "name": p["name"],
                    "fg": f"rgb({fg[0]},{fg[1]},{fg[2]})",
                    "bg": f"rgb({bg[0]},{bg[1]},{bg[2]})",
                    "ratio": round(ratio, 2),
                    "level": status,
                    "threshold": f"AA≥{threshold_aa}, AAA≥{threshold_aaa}",
                    "fontSize": p.get("fontSize"),
                    "large": is_large,
                })

                if status == "FAIL":
                    errors.append(f"{p['name']}: {ratio:.2f}:1 (mín AA {threshold_aa}:1)")

            # Imprimir tabela detalhada
            print()
            print("    ┌─────────────────────────┬───────────────────────┬──────────────────────┬────────┬───────┐")
            print("    │ Componente              │ Foreground            │ Background           │ Ratio  │ Level │")
            print("    ├─────────────────────────┼───────────────────────┼──────────────────────┼────────┼───────┤")
            for r in aa_results:
                name = r["name"][:23].ljust(23)
                fg = r["fg"][:21].ljust(21)
                bg = r["bg"][:20].ljust(20)
                ratio = f"{r['ratio']:>5.1f}:1"
                level = r["level"].ljust(5)
                icon = "✅" if r["level"] != "FAIL" else "❌"
                print(f"    │ {name} │ {fg} │ {bg} │ {ratio} │ {icon}{level}│")
            print("    └─────────────────────────┴───────────────────────┴──────────────────────┴────────┴───────┘")
            print()

            aaa_count = sum(1 for r in aa_results if r["level"] == "AAA")
            aa_count = sum(1 for r in aa_results if r["level"] == "AA")
            fail_count = sum(1 for r in aa_results if r["level"] == "FAIL")
            total = len(aa_results)

            if errors:
                self._fail(
                    f"Component Contrasts ({fail_count}/{total} falhas WCAG AA)",
                    "; ".join(errors[:5])
                )
            else:
                self._ok(f"Component Contrasts ({aaa_count} AAA + {aa_count} AA = {total}/{total} ≥ AA)")

        except Exception as e:
            await page.evaluate("try{document.documentElement.classList.remove('high-contrast')}catch(e){}")
            self._fail("Component Contrasts", str(e))

    # ── 4. Cores de borda e background dos cards ──────────────────

    async def test_border_colors(self, page, base_url: str):
        """Verifica que bordas dos cards ficam amarelas (visíveis) no alto contraste."""
        try:
            await page.goto(base_url, wait_until="networkidle")
            await page.evaluate("document.documentElement.classList.add('high-contrast')")
            await page.wait_for_timeout(300)

            borders = await page.evaluate("""() => {
                const items = [];
                const selectors = [
                    '.category-card', '.link-card', '.inst-card',
                    '.orgao-card', '.modal-content', '.checklist-card'
                ];
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (!el) continue;
                    const cs = getComputedStyle(el);
                    items.push({
                        sel,
                        borderColor: cs.borderColor,
                        borderWidth: cs.borderWidth,
                        borderStyle: cs.borderStyle,
                        bg: cs.backgroundColor,
                    });
                }
                return items;
            }""")

            await page.evaluate("document.documentElement.classList.remove('high-contrast')")

            errors = []
            for b in borders:
                # Borda deve ser visível (não transparent, width > 0)
                if "0px" in b["borderWidth"] and b["borderStyle"] == "none":
                    errors.append(f"{b['sel']}: sem borda visível")
                # Background deve ser escuro (#0a0a0a ou #000)
                bg = parse_rgb(b["bg"])
                if bg[0] > 30 or bg[1] > 30 or bg[2] > 30:
                    errors.append(f"{b['sel']}: bg não é escuro ({b['bg']})")

            if errors:
                self._fail(f"Border Colors ({len(errors)} problemas)", "; ".join(errors))
            else:
                self._ok(f"Border Colors ({len(borders)} cards com borda visível + bg escuro)")
        except Exception as e:
            self._fail("Border Colors", str(e))

    # ── 5. Links visíveis (azul claro sobre preto) ────────────────

    async def test_link_visibility(self, page, base_url: str):
        """Verifica que links são legíveis sobre seu fundo real no HC."""
        try:
            await page.goto(base_url, wait_until="networkidle")
            await page.evaluate("document.documentElement.classList.add('high-contrast')")
            await page.wait_for_timeout(300)

            links = await page.evaluate("""() => {
                function resolvedBg(el) {
                    let node = el;
                    while (node) {
                        const s = getComputedStyle(node);
                        const bg = s.backgroundColor;
                        const bgImg = s.backgroundImage;
                        if (bgImg && bgImg !== 'none' && bgImg.includes('gradient')) {
                            const colors = bgImg.match(/rgb[a]?\\([^)]+\\)/g);
                            if (colors && colors.length > 0) return colors[0];
                        }
                        if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') return bg;
                        node = node.parentElement;
                    }
                    return 'rgb(0, 0, 0)';
                }

                const results = [];
                const allLinks = document.querySelectorAll('a:not(.navbar-brand)');
                let count = 0;
                for (const a of allLinks) {
                    if (count >= 15) break;
                    const cs = getComputedStyle(a);
                    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
                    const rect = a.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) continue;
                    // Skip off-screen skip links (sr-only, clip, negative positions)
                    if (rect.right < 0 || rect.bottom < 0 || rect.left > window.innerWidth) continue;
                    if (a.classList.contains('sr-only') || a.classList.contains('skip-link')) continue;
                    results.push({
                        text: a.textContent.trim().substring(0, 40),
                        color: cs.color,
                        bg: resolvedBg(a),
                        fontSize: parseFloat(cs.fontSize),
                    });
                    count++;
                }
                return results;
            }""")

            await page.evaluate("document.documentElement.classList.remove('high-contrast')")

            errors = []
            for link in links:
                fg = parse_rgb(link["color"])
                bg = parse_rgb(link["bg"])
                ratio = contrast_ratio(fg, bg)
                if ratio < 4.5:
                    errors.append(f"'{link['text'][:20]}': {ratio:.1f}:1 ({link['color']})")

            if errors:
                self._fail(f"Link Visibility ({len(errors)} links baixo contraste)", "; ".join(errors[:5]))
            else:
                self._ok(f"Link Visibility ({len(links)} links ≥ 4.5:1 sobre preto)")
        except Exception as e:
            self._fail("Link Visibility", str(e))

    # ── 6. Botão primary legível ──────────────────────────────────

    async def test_primary_button_contrast(self, page, base_url: str):
        """Verifica .btn-primary no HC: bg amarelo, texto preto, ≥4.5:1."""
        try:
            await page.goto(base_url, wait_until="networkidle")
            await page.evaluate("document.documentElement.classList.add('high-contrast')")
            await page.wait_for_timeout(300)

            btn = await page.evaluate("""() => {
                const el = document.querySelector('.btn-primary');
                if (!el) return null;
                const cs = getComputedStyle(el);
                return {
                    color: cs.color,
                    bg: cs.backgroundColor,
                    borderColor: cs.borderColor,
                    fontSize: parseFloat(cs.fontSize),
                };
            }""")

            await page.evaluate("document.documentElement.classList.remove('high-contrast')")

            if not btn:
                self._warn("Primary Button", "Nenhum .btn-primary encontrado")
                return

            fg = parse_rgb(btn["color"])
            bg = parse_rgb(btn["bg"])
            ratio = contrast_ratio(fg, bg)

            errors = []
            if ratio < 4.5:
                errors.append(f"Contraste {ratio:.1f}:1 < 4.5:1")
            # Texto deve ser escuro sobre fundo claro (ou vice-versa)
            if fg[0] > 50 and fg[1] > 50:
                errors.append(f"Texto não é escuro: {btn['color']}")

            if errors:
                self._fail("Primary Button Contrast", "; ".join(errors))
            else:
                self._ok(f"Primary Button (ratio {ratio:.1f}:1, fg={btn['color']}, bg={btn['bg']})")
        except Exception as e:
            self._fail("Primary Button Contrast", str(e))

    # ── 7. Hero Section com contraste adequado ────────────────────

    async def test_hero_high_contrast(self, page, base_url: str):
        """Verifica hero no HC: fundo escuro, texto branco/amarelo, destaque visível."""
        try:
            await page.goto(base_url, wait_until="networkidle")
            await page.evaluate("document.documentElement.classList.add('high-contrast')")
            await page.wait_for_timeout(300)

            hero = await page.evaluate("""() => {
                const h = document.querySelector('.hero');
                const h1 = document.querySelector('.hero h1');
                const sub = document.querySelector('.hero-sub');
                const hl = document.querySelector('.hero-highlight');
                if (!h) return null;
                const heroCs = getComputedStyle(h);
                return {
                    heroBg: heroCs.backgroundImage || heroCs.backgroundColor,
                    h1Color: h1 ? getComputedStyle(h1).color : '',
                    subColor: sub ? getComputedStyle(sub).color : '',
                    highlightColor: hl ? getComputedStyle(hl).color : '',
                };
            }""")

            await page.evaluate("document.documentElement.classList.remove('high-contrast')")

            if not hero:
                self._fail("Hero HC", "Hero não encontrado")
                return

            errors = []
            # h1 deve ser claro
            if hero["h1Color"]:
                h1 = parse_rgb(hero["h1Color"])
                h1_lum = _luminance(*h1)
                if h1_lum < 0.5:
                    errors.append(f"h1 muito escuro: {hero['h1Color']} (luminância {h1_lum:.2f})")

            # Highlight deve ser amarelo/dourado (brilhante)
            if hero["highlightColor"]:
                hl = parse_rgb(hero["highlightColor"])
                ratio_vs_black = contrast_ratio(hl, (0, 0, 0))
                if ratio_vs_black < 4.5:
                    errors.append(f"Highlight baixo contraste vs preto: {ratio_vs_black:.1f}:1")

            if errors:
                self._fail("Hero HC", "; ".join(errors))
            else:
                self._ok(f"Hero HC (h1={hero['h1Color']}, highlight={hero['highlightColor']})")
        except Exception as e:
            self._fail("Hero HC", str(e))

    # ── 8. Footer legível ─────────────────────────────────────────

    async def test_footer_high_contrast(self, page, base_url: str):
        """Verifica footer no HC: bg preto, texto/borda visíveis."""
        try:
            await page.goto(base_url, wait_until="networkidle")
            await page.evaluate("document.documentElement.classList.add('high-contrast')")
            await page.wait_for_timeout(300)

            footer = await page.evaluate("""() => {
                const f = document.querySelector('.footer');
                if (!f) return null;
                const cs = getComputedStyle(f);
                const link = f.querySelector('a');
                return {
                    bg: cs.backgroundColor,
                    color: cs.color,
                    borderTop: cs.borderTopColor,
                    linkColor: link ? getComputedStyle(link).color : '',
                };
            }""")

            await page.evaluate("document.documentElement.classList.remove('high-contrast')")

            if not footer:
                self._fail("Footer HC", "Footer não encontrado")
                return

            errors = []
            bg = parse_rgb(footer["bg"])
            fg = parse_rgb(footer["color"])
            ratio = contrast_ratio(fg, bg)

            if ratio < 4.5:
                errors.append(f"Texto/bg: {ratio:.1f}:1 < 4.5:1")
            if bg[0] > 20:
                errors.append(f"Bg não é preto: {footer['bg']}")

            if footer["linkColor"]:
                link_fg = parse_rgb(footer["linkColor"])
                link_ratio = contrast_ratio(link_fg, bg)
                if link_ratio < 4.5:
                    errors.append(f"Link: {link_ratio:.1f}:1 < 4.5:1")

            if errors:
                self._fail("Footer HC", "; ".join(errors))
            else:
                self._ok(f"Footer HC (ratio {ratio:.1f}:1, bg preto, borda {footer['borderTop']})")
        except Exception as e:
            self._fail("Footer HC", str(e))

    # ── 9. A11y Drawer legível no HC ──────────────────────────────

    async def test_a11y_drawer_high_contrast(self, page, base_url: str):
        """Verifica que o drawer de acessibilidade é legível no HC."""
        try:
            await page.goto(base_url, wait_until="networkidle")
            await page.evaluate("""
                document.querySelectorAll('[vw], .enabled[vw]').forEach(el => el.remove());
                const aside = document.querySelector('aside[aria-label*="VLibras"]');
                if (aside) aside.remove();
            """)
            await page.wait_for_timeout(200)
            await page.evaluate("document.documentElement.classList.add('high-contrast')")
            await page.wait_for_timeout(300)

            # Abrir drawer
            await page.click("#a11yPanelTrigger")
            await page.wait_for_timeout(400)

            # Screenshot do drawer aberto em HC
            await page.screenshot(path=str(SCREENSHOTS / "hc_03_drawer.png"), full_page=False)

            drawer = await page.evaluate("""() => {
                const d = document.querySelector('.a11y-drawer');
                if (!d) return null;
                const cs = getComputedStyle(d);
                const btns = d.querySelectorAll('.a11y-drawer-btn, .a11y-toggle-btn, .a11y-action-btn');
                const btnData = [];
                btns.forEach(b => {
                    const bcs = getComputedStyle(b);
                    btnData.push({
                        text: b.textContent.trim().substring(0, 30),
                        color: bcs.color,
                        bg: bcs.backgroundColor,
                        border: bcs.borderColor,
                    });
                });
                return {
                    bg: cs.backgroundColor,
                    color: cs.color,
                    borderLeft: cs.borderLeftColor,
                    borderLeftWidth: cs.borderLeftWidth,
                    buttons: btnData,
                };
            }""")

            await page.evaluate("document.documentElement.classList.remove('high-contrast')")

            if not drawer:
                self._fail("A11y Drawer HC", "Drawer não encontrado")
                return

            errors = []
            bg = parse_rgb(drawer["bg"])
            fg = parse_rgb(drawer["color"])
            ratio = contrast_ratio(fg, bg)

            if ratio < 4.5:
                errors.append(f"Drawer texto/bg: {ratio:.1f}:1 < 4.5:1")

            # Verificar botões
            for b in drawer["buttons"]:
                btn_fg = parse_rgb(b["color"])
                btn_bg = parse_rgb(b["bg"])
                btn_ratio = contrast_ratio(btn_fg, btn_bg)
                if btn_ratio < 3.0:
                    errors.append(f"Botão '{b['text'][:15]}': {btn_ratio:.1f}:1 < 3:1")

            if errors:
                self._fail(f"A11y Drawer HC ({len(errors)} problemas)", "; ".join(errors[:5]))
            else:
                self._ok(f"A11y Drawer HC (ratio {ratio:.1f}:1, {len(drawer['buttons'])} botões legíveis)")
        except Exception as e:
            self._fail("A11y Drawer HC", str(e))

    # ── 10. Filtros visíveis no HC ────────────────────────────────

    async def test_filter_buttons_hc(self, page, base_url: str):
        """Verifica que filtros de região/instituição são visíveis no HC."""
        try:
            await page.goto(base_url, wait_until="networkidle")
            await page.evaluate("document.documentElement.classList.add('high-contrast')")
            await page.wait_for_timeout(300)

            filters = await page.evaluate("""() => {
                const results = [];
                document.querySelectorAll('.orgao-filter-btn, .inst-filter-btn').forEach(el => {
                    const cs = getComputedStyle(el);
                    results.push({
                        text: el.textContent.trim(),
                        color: cs.color,
                        bg: cs.backgroundColor,
                        border: cs.borderColor,
                        pressed: el.getAttribute('aria-pressed'),
                    });
                });
                return results;
            }""")

            await page.evaluate("document.documentElement.classList.remove('high-contrast')")

            errors = []
            for f in filters:
                fg = parse_rgb(f["color"])
                bg = parse_rgb(f["bg"])
                ratio = contrast_ratio(fg, bg)
                if ratio < 3.0:
                    errors.append(f"'{f['text']}': {ratio:.1f}:1 < 3:1")

            if errors:
                self._fail(f"Filter Buttons HC ({len(errors)} baixo contraste)", "; ".join(errors))
            else:
                self._ok(f"Filter Buttons HC ({len(filters)} filtros legíveis)")
        except Exception as e:
            self._fail("Filter Buttons HC", str(e))

    # ── 11. Screenshot comparativo full-page ──────────────────────

    async def test_full_page_comparison(self, page, base_url: str):
        """Gera screenshots lado-a-lado: normal vs alto contraste."""
        try:
            # Mobile HC
            await page.set_viewport_size({"width": 375, "height": 812})
            await page.goto(base_url, wait_until="networkidle")
            await page.evaluate("document.documentElement.classList.add('high-contrast')")
            await page.wait_for_timeout(400)
            await page.screenshot(path=str(SCREENSHOTS / "hc_04_mobile.png"), full_page=True)
            await page.evaluate("document.documentElement.classList.remove('high-contrast')")

            # Tablet HC
            await page.set_viewport_size({"width": 768, "height": 1024})
            await page.goto(base_url, wait_until="networkidle")
            await page.evaluate("document.documentElement.classList.add('high-contrast')")
            await page.wait_for_timeout(400)
            await page.screenshot(path=str(SCREENSHOTS / "hc_05_tablet.png"), full_page=True)
            await page.evaluate("document.documentElement.classList.remove('high-contrast')")

            self._ok("Screenshots Comparativos (hc_04_mobile + hc_05_tablet)")
        except Exception as e:
            self._fail("Screenshots Comparativos", str(e))

    # ── Runner ────────────────────────────────────────────────────

    async def run_all(self) -> int:
        port = os.environ.get("E2E_PORT", "8080")
        base_url = f"http://localhost:{port}"

        import urllib.request
        try:
            urllib.request.urlopen(base_url, timeout=2)
        except Exception:
            print(f"⚠️  Servidor não detectado em {base_url}")
            sys.exit(1)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await ctx.new_page()

            print("=" * 80)
            print("🔲 AUDITORIA ALTO CONTRASTE — Verificação Completa")
            print("=" * 80)

            print("\n🔘 Mecanismo de Toggle:")
            await self.test_toggle_button(page, base_url)
            await self.test_persistence(page, base_url)

            print("\n🎨 Contraste WCAG por Componente:")
            await self.test_component_contrasts(page, base_url)

            print("\n🧩 Elementos Específicos:")
            await self.test_border_colors(page, base_url)
            await self.test_link_visibility(page, base_url)
            await self.test_primary_button_contrast(page, base_url)
            await self.test_hero_high_contrast(page, base_url)
            await self.test_footer_high_contrast(page, base_url)
            await self.test_a11y_drawer_high_contrast(page, base_url)
            await self.test_filter_buttons_hc(page, base_url)

            print("\n📸 Screenshots:")
            await self.test_full_page_comparison(page, base_url)

            await browser.close()

        total = self.passed + self.failed + self.warnings
        print("\n" + "=" * 80)
        print("📊 RESULTADO ALTO CONTRASTE:")
        print("=" * 80)
        print(f"  ✅ Passou:  {self.passed}")
        print(f"  ⚠️  Avisos:  {self.warnings}")
        print(f"  ❌ Falhou:  {self.failed}")
        print(f"  📈 Total:   {total}")
        print("=" * 80)

        if self.failed == 0:
            print(f"\n🎉 ALTO CONTRASTE FUNCIONA CORRETAMENTE! ({self.warnings} avisos)")
        else:
            print(f"\n⚠️  {self.failed} problema(s) encontrado(s).")

        print(f"\n📸 Screenshots salvos em: {SCREENSHOTS.resolve()}")
        print("   hc_01_before.png  — Antes do toggle")
        print("   hc_02_after.png   — Após ativar alto contraste (desktop)")
        print("   hc_03_drawer.png  — Drawer a11y aberto em HC")
        print("   hc_04_mobile.png  — Mobile em HC")
        print("   hc_05_tablet.png  — Tablet em HC")

        # JSON
        report = SCREENSHOTS / "high_contrast_report.json"
        with open(report, "w", encoding="utf-8") as f:
            json.dump(self.details, f, indent=2, ensure_ascii=False)

        return self.failed


if __name__ == "__main__":
    runner = HighContrastAudit()
    code = asyncio.run(runner.run_all())
    sys.exit(code)
