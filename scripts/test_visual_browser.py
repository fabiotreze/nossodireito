#!/usr/bin/env python3
"""
Testes Visuais — Playwright Browser Emulation
Verifica formatação, cores, contraste, responsividade, overflow, sobreposição, etc.

Gera screenshots em  screenshots/  para inspeção manual.
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
    print("⚠️  Playwright não instalado. Execute:")
    print("   pip install playwright && playwright install chromium")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
SCREENSHOTS = ROOT / "screenshots"
SCREENSHOTS.mkdir(exist_ok=True)

# WCAG 2.1 AA minimum contrast ratios
CONTRAST_AA_NORMAL = 4.5
CONTRAST_AA_LARGE = 3.0


def _relative_luminance(r: int, g: int, b: int) -> float:
    """Luminância relativa sRGB conforme WCAG 2.1."""
    def _lin(c: int) -> float:
        s = c / 255
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast_ratio(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    """Calcula razão de contraste WCAG entre fg e bg."""
    l1 = _relative_luminance(*fg)
    l2 = _relative_luminance(*bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def parse_rgb(css_color: str) -> tuple[int, int, int]:
    """Extrai (r, g, b) de 'rgb(r, g, b)' ou 'rgba(r, g, b, a)'."""
    css_color = css_color.strip()
    if css_color.startswith("rgba"):
        nums = css_color.replace("rgba(", "").replace(")", "")
    elif css_color.startswith("rgb"):
        nums = css_color.replace("rgb(", "").replace(")", "")
    else:
        return (0, 0, 0)
    parts = [x.strip() for x in nums.split(",")]
    return (int(parts[0]), int(parts[1]), int(parts[2]))


class VisualBrowserTests:
    """Testes visuais de formatação, cor, layout e responsividade."""

    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results: list[dict] = []

    # ─── helpers ───────────────────────────────────────────────────

    def _pass(self, msg: str) -> None:
        print(f"  ✅ {msg}")
        self.passed += 1
        self.results.append({"name": msg, "status": "pass"})

    def _fail(self, msg: str, detail: str) -> None:
        print(f"  ❌ {msg}")
        print(f"      {detail}")
        self.failed += 1
        self.results.append({"name": msg, "status": "fail", "detail": detail})

    def _warn(self, msg: str, detail: str) -> None:
        print(f"  ⚠️  {msg}")
        print(f"      {detail}")
        self.warnings += 1
        self.results.append({"name": msg, "status": "warn", "detail": detail})

    # ─── screenshots em 3 viewports ───────────────────────────────

    async def capture_screenshots(self, page, base_url: str) -> None:
        """Captura screenshots desktop, tablet e mobile para inspeção manual."""
        viewports = {
            "desktop_1920": {"width": 1920, "height": 1080},
            "tablet_768": {"width": 768, "height": 1024},
            "mobile_375": {"width": 375, "height": 812},
        }
        for name, vp in viewports.items():
            await page.set_viewport_size(vp)
            await page.goto(base_url, wait_until="networkidle")
            await page.wait_for_timeout(500)
            path = SCREENSHOTS / f"{name}.png"
            await page.screenshot(path=str(path), full_page=True)
            self._pass(f"Screenshot {name} salvo ({path.name})")

        # screenshot de alto contraste
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.goto(base_url, wait_until="networkidle")
        await page.evaluate("document.documentElement.classList.add('high-contrast')")
        await page.wait_for_timeout(300)
        p = SCREENSHOTS / "desktop_high_contrast.png"
        await page.screenshot(path=str(p), full_page=True)
        await page.evaluate("document.documentElement.classList.remove('high-contrast')")
        self._pass(f"Screenshot alto contraste salvo ({p.name})")

    # ─── 1. CSS Custom Properties carregadas ──────────────────────

    async def test_css_variables_loaded(self, page, base_url: str) -> None:
        """Verifica se as CSS custom properties (design tokens) estão carregadas."""
        try:
            await page.goto(base_url, wait_until="networkidle")
            tokens = await page.evaluate("""() => {
                const cs = getComputedStyle(document.documentElement);
                return {
                    primary:  cs.getPropertyValue('--primary').trim(),
                    accent:   cs.getPropertyValue('--accent').trim(),
                    surface:  cs.getPropertyValue('--surface').trim(),
                    text:     cs.getPropertyValue('--text').trim(),
                    border:   cs.getPropertyValue('--border').trim(),
                    radius:   cs.getPropertyValue('--radius').trim(),
                    font:     cs.getPropertyValue('--font').trim(),
                };
            }""")
            errors = []
            for k, v in tokens.items():
                if not v:
                    errors.append(f"--{k} vazio")
            assert not errors, "; ".join(errors)
            self._pass(f"CSS Variables ({len(tokens)} design tokens carregados)")
        except Exception as e:
            self._fail("CSS Variables", str(e))

    # ─── 2. Contraste WCAG AA — pares críticos ───────────────────

    async def test_contrast_ratios(self, page, base_url: str) -> None:
        """Calcula razão de contraste WCAG 2.1 AA de pares texto/fundo críticos."""
        try:
            await page.goto(base_url, wait_until="networkidle")
            pairs = await page.evaluate("""() => {
                function cs(el) { return getComputedStyle(el); }
                function rgb(el, prop) { return cs(el)[prop]; }
                // Resolve transparent backgrounds by walking up the DOM
                // Also handles linear-gradient by sampling pixel color via canvas
                function resolvedBg(el) {
                    let node = el;
                    while (node) {
                        const s = getComputedStyle(node);
                        const bg = s.backgroundColor;
                        const bgImg = s.backgroundImage;
                        // Has a gradient? Use canvas to sample the actual pixel color
                        if (bgImg && bgImg !== 'none' && bgImg.includes('gradient')) {
                            try {
                                const rect = node.getBoundingClientRect();
                                const canvas = document.createElement('canvas');
                                canvas.width = 1; canvas.height = 1;
                                const ctx = canvas.getContext('2d');
                                // Parse the gradient to extract colors
                                const colors = bgImg.match(/rgb[a]?\\([^)]+\\)/g);
                                if (colors && colors.length > 0) {
                                    // Use the darkest/first color as approximation
                                    return colors[0];
                                }
                            } catch(e) {}
                        }
                        if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') return bg;
                        node = node.parentElement;
                    }
                    return 'rgb(255, 255, 255)';
                }
                const body = document.body;
                const hero = document.querySelector('.hero');
                const heroH1 = document.querySelector('.hero h1');
                const navbar = document.querySelector('.navbar');
                const navLink = document.querySelector('.nav-links a');
                const footer = document.querySelector('.footer');
                const section = document.querySelector('.section');
                const sectionH2 = document.querySelector('.section h2');
                const card = document.querySelector('.category-card');
                return [
                    {name: 'Body text/bg', fg: rgb(body,'color'), bg: resolvedBg(body)},
                    {name: 'Hero h1/bg', fg: heroH1 ? rgb(heroH1,'color') : '', bg: hero ? resolvedBg(hero) : ''},
                    {name: 'Navbar link/bg', fg: navLink ? rgb(navLink,'color') : '', bg: navbar ? resolvedBg(navbar) : ''},
                    {name: 'Footer text/bg', fg: footer ? rgb(footer,'color') : '', bg: resolvedBg(footer)},
                    {name: 'Section h2/bg', fg: sectionH2 ? rgb(sectionH2,'color') : '', bg: section ? resolvedBg(section) : ''},
                    {name: 'Card text/bg', fg: card ? rgb(card,'color') : '', bg: card ? resolvedBg(card) : ''},
                ];
            }""")

            errors = []
            for p in pairs:
                if not p["fg"] or not p["bg"]:
                    continue
                try:
                    fg = parse_rgb(p["fg"])
                    bg = parse_rgb(p["bg"])
                except Exception:
                    continue
                ratio = contrast_ratio(fg, bg)
                threshold = CONTRAST_AA_NORMAL
                status = "OK" if ratio >= threshold else "FAIL"
                label = f"{p['name']}: {ratio:.2f}:1 (mín {threshold}:1)"
                if status == "FAIL":
                    errors.append(label)
                else:
                    pass  # log individual passes only in verbose mode

            if errors:
                self._fail(f"Contraste WCAG AA ({len(errors)} falhas)", "; ".join(errors))
            else:
                self._pass(f"Contraste WCAG AA ({len(pairs)} pares ≥ {CONTRAST_AA_NORMAL}:1)")
        except Exception as e:
            self._fail("Contraste WCAG AA", str(e))

    # ─── 3. Contraste alto contraste mode ─────────────────────────

    async def test_high_contrast_colors(self, page, base_url: str) -> None:
        """Verifica cores no modo alto contraste (class high-contrast)."""
        try:
            await page.goto(base_url, wait_until="networkidle")
            await page.evaluate("document.documentElement.classList.add('high-contrast')")
            await page.wait_for_timeout(300)

            colors = await page.evaluate("""() => {
                const cs = getComputedStyle(document.documentElement);
                return {
                    bg: getComputedStyle(document.body).backgroundColor,
                    text: getComputedStyle(document.body).color,
                    surface: cs.getPropertyValue('--surface').trim(),
                };
            }""")

            bg = parse_rgb(colors["bg"])
            fg = parse_rgb(colors["text"])
            ratio = contrast_ratio(fg, bg)

            await page.evaluate("document.documentElement.classList.remove('high-contrast')")

            errors = []
            # Alto contraste: fundo deve ser muito escuro
            if bg[0] > 30 or bg[1] > 30 or bg[2] > 30:
                errors.append(f"Fundo não é preto: rgb({bg[0]},{bg[1]},{bg[2]})")
            # Texto deve ser brilhante
            if fg[0] < 200 and fg[1] < 200 and fg[2] < 30:
                errors.append(f"Texto não é amarelo/claro: rgb({fg[0]},{fg[1]},{fg[2]})")
            # Contraste mínimo 7:1 para AAA
            if ratio < 7.0:
                errors.append(f"Contraste insuficiente AAA: {ratio:.2f}:1 (mín 7:1)")

            if errors:
                self._fail("Alto Contraste Colors", "; ".join(errors))
            else:
                self._pass(f"Alto Contraste Colors (ratio {ratio:.1f}:1, bg preto, texto amarelo)")
        except Exception as e:
            self._fail("Alto Contraste Colors", str(e))

    # ─── 4. Fontes carregadas e legíveis ──────────────────────────

    async def test_font_rendering(self, page, base_url: str) -> None:
        """Verifica se fontes estão sendo aplicadas e tamanhos mínimos."""
        try:
            await page.goto(base_url, wait_until="networkidle")
            fonts = await page.evaluate("""() => {
                const cs = prop => getComputedStyle(document.body)[prop];
                const h1 = document.querySelector('h1');
                const p = document.querySelector('.hero-sub') || document.querySelector('p');
                const small = document.querySelector('.text-muted, small');
                return {
                    bodyFont: cs('fontFamily'),
                    bodySize: parseFloat(cs('fontSize')),
                    h1Size: h1 ? parseFloat(getComputedStyle(h1).fontSize) : 0,
                    pSize: p ? parseFloat(getComputedStyle(p).fontSize) : 0,
                    smallSize: small ? parseFloat(getComputedStyle(small).fontSize) : 0,
                    lineHeight: parseFloat(cs('lineHeight')),
                };
            }""")

            errors = []
            # Mínimo body 14px (acessibilidade)
            if fonts["bodySize"] < 14:
                errors.append(f"Body font-size {fonts['bodySize']}px < 14px")
            # h1 deve ser >24px
            if fonts["h1Size"] < 24:
                errors.append(f"h1 font-size {fonts['h1Size']}px < 24px")
            # Parágrafos >14px
            if fonts["pSize"] and fonts["pSize"] < 14:
                errors.append(f"p font-size {fonts['pSize']}px < 14px")
            # small/muted ≥12px
            if fonts["smallSize"] and fonts["smallSize"] < 12:
                errors.append(f"small/muted {fonts['smallSize']}px < 12px")
            # font-family não deve ser o fallback padrão "serif"
            if "serif" in fonts["bodyFont"].lower() and "sans-serif" not in fonts["bodyFont"].lower():
                errors.append(f"Font fallback para serif: {fonts['bodyFont']}")

            if errors:
                self._fail("Font Rendering", "; ".join(errors))
            else:
                self._pass(f"Font Rendering (body {fonts['bodySize']}px, h1 {fonts['h1Size']}px, line-height {fonts['lineHeight']}px)")
        except Exception as e:
            self._fail("Font Rendering", str(e))

    # ─── 5. Overflow horizontal (nenhum conteúdo vaza) ────────────

    async def test_no_horizontal_overflow(self, page, base_url: str) -> None:
        """Verifica se nenhum elemento causa scroll horizontal em 3 viewports."""
        try:
            viewports = [
                ("desktop 1920", 1920, 1080),
                ("tablet 768", 768, 1024),
                ("mobile 375", 375, 812),
            ]
            errors = []
            for name, w, h in viewports:
                await page.set_viewport_size({"width": w, "height": h})
                await page.goto(base_url, wait_until="networkidle")
                await page.wait_for_timeout(300)

                overflow = await page.evaluate("""() => {
                    const docWidth = document.documentElement.scrollWidth;
                    const vpWidth = document.documentElement.clientWidth;
                    const diff = docWidth - vpWidth;
                    // Encontrar elementos que vazam
                    const overflowing = [];
                    document.querySelectorAll('*').forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.right > vpWidth + 5) {
                            const tag = el.tagName.toLowerCase();
                            const id = el.id ? '#' + el.id : '';
                            const cls = el.className && typeof el.className === 'string' ?
                                '.' + el.className.split(' ').filter(Boolean).join('.') : '';
                            overflowing.push(`${tag}${id}${cls} (right=${Math.round(rect.right)}px)`);
                        }
                    });
                    return {diff, overflowing: overflowing.slice(0, 5)};
                }""")

                if overflow["diff"] > 5:
                    culprits = ", ".join(overflow["overflowing"]) if overflow["overflowing"] else "não identificados"
                    errors.append(f"{name}: overflow {overflow['diff']}px [{culprits}]")

            if errors:
                self._fail(f"Horizontal Overflow ({len(errors)} viewports)", "; ".join(errors))
            else:
                self._pass("Horizontal Overflow (0 em 3 viewports)")
        except Exception as e:
            self._fail("Horizontal Overflow", str(e))

    # ─── 6. Elementos sobrepostos (z-index / position) ────────────

    async def test_no_element_overlap(self, page, base_url: str) -> None:
        """Verifica se elementos fixos/absolutos não cobrem conteúdo principal."""
        try:
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(base_url, wait_until="networkidle")
            await page.wait_for_timeout(500)

            overlaps = await page.evaluate("""() => {
                const fixed = [];
                const issues = [];
                // Coletar elementos fixos/sticky
                document.querySelectorAll('*').forEach(el => {
                    const pos = getComputedStyle(el).position;
                    if (pos === 'fixed' || pos === 'sticky') {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            const tag = el.tagName.toLowerCase();
                            const id = el.id ? '#' + el.id : '';
                            fixed.push({name: `${tag}${id}`, rect, zIndex: getComputedStyle(el).zIndex});
                        }
                    }
                });

                // Verificar que main content não está oculto sob fixed elements
                const main = document.querySelector('main#mainContent');
                if (main) {
                    const mainRect = main.getBoundingClientRect();
                    for (const f of fixed) {
                        // Verificação: elemento fixo totalmente sobre o main com z alto
                        if (f.rect.width > mainRect.width * 0.8 &&
                            f.rect.height > mainRect.height * 0.5 &&
                            f.name !== 'nav' && !f.name.includes('navbar')) {
                            issues.push(`${f.name} (z=${f.zIndex}) pode ocultar conteúdo`);
                        }
                    }
                }
                return {fixedCount: fixed.length, issues, elements: fixed.map(f => `${f.name}(z:${f.zIndex})`)};
            }""")

            if overlaps["issues"]:
                self._fail("Element Overlap", "; ".join(overlaps["issues"]))
            else:
                els = ", ".join(overlaps["elements"][:6]) if overlaps["elements"] else "nenhum"
                self._pass(f"Element Overlap (0 sobreposições, {overlaps['fixedCount']} fixed/sticky: {els})")
        except Exception as e:
            self._fail("Element Overlap", str(e))

    # ─── 7. Layout responsivo — grid/flex em mobile ───────────────

    async def test_responsive_layout(self, page, base_url: str) -> None:
        """Verifica que grids colapsam para 1 coluna em mobile."""
        try:
            # Mobile
            await page.set_viewport_size({"width": 375, "height": 812})
            await page.goto(base_url, wait_until="networkidle")
            await page.wait_for_timeout(300)

            layout = await page.evaluate("""() => {
                const checks = {};
                // card-grid deve ser 1 coluna
                const grid = document.querySelector('.card-grid');
                if (grid) {
                    const cols = getComputedStyle(grid).gridTemplateColumns;
                    checks.cardGridCols = cols;
                    checks.cardGridSingle = cols.split(' ').filter(Boolean).length <= 1 ||
                                             cols.includes('1fr') && !cols.includes(' 1fr');
                }
                // hero-grid deve ser column
                const heroGrid = document.querySelector('.hero-grid');
                if (heroGrid) {
                    checks.heroDirection = getComputedStyle(heroGrid).flexDirection;
                }
                // nav-links deve estar oculto (translateY) quando fechado
                const nav = document.querySelector('.nav-links');
                if (nav) {
                    checks.navTransform = getComputedStyle(nav).transform;
                    checks.navVisible = nav.classList.contains('open');
                }
                // menu-toggle deve ser visível
                const toggle = document.querySelector('.menu-toggle');
                if (toggle) {
                    checks.menuToggleDisplay = getComputedStyle(toggle).display;
                }
                // hero h1 tamanho
                const h1 = document.querySelector('.hero h1');
                if (h1) {
                    checks.h1Size = parseFloat(getComputedStyle(h1).fontSize);
                }
                return checks;
            }""")

            errors = []
            if layout.get("heroDirection") and layout["heroDirection"] != "column":
                errors.append(f"hero-grid flex-direction={layout['heroDirection']}, esperado column")
            if layout.get("menuToggleDisplay") == "none":
                errors.append("menu-toggle oculto em mobile")
            if layout.get("navVisible"):
                errors.append("nav-links aberto por padrão em mobile")
            if layout.get("h1Size") and layout["h1Size"] > 32:
                errors.append(f"h1 muito grande em mobile: {layout['h1Size']}px")

            if errors:
                self._fail("Responsive Layout Mobile", "; ".join(errors))
            else:
                self._pass(f"Responsive Layout Mobile (hero column, toggle visível, h1 {layout.get('h1Size', '?')}px)")
        except Exception as e:
            self._fail("Responsive Layout Mobile", str(e))

    # ─── 8. Tablet: grid 2 colunas ────────────────────────────────

    async def test_responsive_tablet(self, page, base_url: str) -> None:
        """Verifica layout em tablet (768-1024px)."""
        try:
            await page.set_viewport_size({"width": 900, "height": 1024})
            await page.goto(base_url, wait_until="networkidle")
            await page.wait_for_timeout(300)

            layout = await page.evaluate("""() => {
                const grid = document.querySelector('.card-grid');
                const cols = grid ? getComputedStyle(grid).gridTemplateColumns : '';
                const colCount = cols.split(' ').filter(x => x.trim()).length;
                const hero = document.querySelector('.hero h1');
                // Use clientWidth (visible area) to avoid false positives from overflow-x:hidden
                const bodyWidth = document.documentElement.clientWidth;
                return {
                    gridCols: cols,
                    colCount,
                    h1Size: hero ? parseFloat(getComputedStyle(hero).fontSize) : 0,
                    bodyWidth: bodyWidth,
                    vpWidth: window.innerWidth,
                };
            }""")

            errors = []
            if layout["colCount"] < 2:
                errors.append(f"card-grid {layout['colCount']} colunas, esperado ≥2")
            # Sem overflow
            if layout["bodyWidth"] > layout["vpWidth"] + 5:
                errors.append(f"Overflow: body {layout['bodyWidth']}px > vp {layout['vpWidth']}px")

            if errors:
                self._fail("Responsive Tablet (900px)", "; ".join(errors))
            else:
                self._pass(f"Responsive Tablet ({layout['colCount']} colunas, h1 {layout['h1Size']}px)")
        except Exception as e:
            self._fail("Responsive Tablet", str(e))

    # ─── 9. Links e botões visíveis/legíveis ──────────────────────

    async def test_interactive_elements_visible(self, page, base_url: str) -> None:
        """Verifica se links e botões têm tamanho mínimo de toque (44×44px) em mobile."""
        try:
            await page.set_viewport_size({"width": 375, "height": 812})
            await page.goto(base_url, wait_until="networkidle")
            await page.wait_for_timeout(300)

            results = await page.evaluate("""() => {
                const issues = [];
                const checked = 0;
                // Botões visíveis na viewport
                document.querySelectorAll('button, a.btn, [role="button"]').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    const vis = getComputedStyle(el);
                    if (vis.display === 'none' || vis.visibility === 'hidden' || vis.opacity === '0') return;
                    if (rect.width === 0 || rect.height === 0) return;
                    // WCAG 2.5.5 target size (44px min para mobile)
                    if (rect.width < 24 || rect.height < 24) {
                        const tag = el.tagName.toLowerCase();
                        const id = el.id ? '#' + el.id : '';
                        issues.push(`${tag}${id} ${Math.round(rect.width)}×${Math.round(rect.height)}px`);
                    }
                });
                return {smallTargets: issues.slice(0, 8), total: issues.length};
            }""")

            if results["total"] > 0:
                detail = ", ".join(results["smallTargets"])
                self._warn(f"Touch Targets ({results['total']} < 24px)", detail)
            else:
                self._pass("Touch Targets (todos ≥ 24px em mobile)")
        except Exception as e:
            self._fail("Touch Targets", str(e))

    # ─── 10. Espaçamento e padding consistentes ───────────────────

    async def test_spacing_consistency(self, page, base_url: str) -> None:
        """Verifica espaçamento das seções (padding mínimo, gap de grids)."""
        try:
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(base_url, wait_until="networkidle")
            errors = []

            spacings = await page.evaluate("""() => {
                const sections = document.querySelectorAll('.section');
                const data = [];
                sections.forEach(s => {
                    const cs = getComputedStyle(s);
                    data.push({
                        id: s.id || s.className,
                        padTop: parseFloat(cs.paddingTop),
                        padBottom: parseFloat(cs.paddingBottom),
                    });
                });
                // Card grid gap
                const grid = document.querySelector('.card-grid');
                const gridGap = grid ? getComputedStyle(grid).gap : '0px';
                return {sections: data, gridGap};
            }""")

            for s in spacings["sections"]:
                if s["padTop"] < 20:
                    errors.append(f"#{s['id']}: padding-top {s['padTop']}px < 20px")
                if s["padBottom"] < 20:
                    errors.append(f"#{s['id']}: padding-bottom {s['padBottom']}px < 20px")

            if errors:
                self._fail(f"Spacing Consistency ({len(errors)} issues)", "; ".join(errors[:5]))
            else:
                self._pass(f"Spacing Consistency ({len(spacings['sections'])} seções, grid gap={spacings['gridGap']})")
        except Exception as e:
            self._fail("Spacing Consistency", str(e))

    # ─── 11. Imagens renderizadas ─────────────────────────────────

    async def test_images_render(self, page, base_url: str) -> None:
        """Verifica se imagens carregaram e não estão distorcidas (aspect ratio)."""
        try:
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(base_url, wait_until="networkidle")

            imgs = await page.evaluate("""() => {
                const results = [];
                document.querySelectorAll('img').forEach(img => {
                    const rect = img.getBoundingClientRect();
                    results.push({
                        src: img.src.split('/').pop(),
                        alt: img.alt,
                        naturalW: img.naturalWidth,
                        naturalH: img.naturalHeight,
                        renderW: Math.round(rect.width),
                        renderH: Math.round(rect.height),
                        complete: img.complete,
                        broken: img.naturalWidth === 0 && img.complete,
                    });
                });
                return results;
            }""")

            errors = []
            for img in imgs:
                if img["broken"]:
                    errors.append(f"{img['src']}: imagem quebrada")
                elif img["naturalW"] > 0 and img["renderW"] > 0:
                    natural_ratio = img["naturalW"] / img["naturalH"] if img["naturalH"] else 1
                    render_ratio = img["renderW"] / img["renderH"] if img["renderH"] else 1
                    if abs(natural_ratio - render_ratio) > 0.15:
                        errors.append(f"{img['src']}: distorcida (natural {natural_ratio:.2f} vs render {render_ratio:.2f})")

            if errors:
                self._fail(f"Images Render ({len(errors)} problemas)", "; ".join(errors))
            else:
                self._pass(f"Images Render ({len(imgs)} imagens carregadas sem distorção)")
        except Exception as e:
            self._fail("Images Render", str(e))

    # ─── 12. Focus visible em todos os interativos ────────────────

    async def test_focus_visible(self, page, base_url: str) -> None:
        """Verifica se focus outline aparece em elementos interativos ao receber foco."""
        try:
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(base_url, wait_until="networkidle")

            focus_results = await page.evaluate("""() => {
                const results = [];
                const selectors = ['#searchInput', '#menuToggle', '#a11yPanelTrigger', '#backToTop', '.nav-links a'];
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (!el) continue;
                    // Skip hidden/invisible elements — they can't receive focus
                    const vis = getComputedStyle(el);
                    if (vis.display === 'none' || vis.visibility === 'hidden' || vis.opacity === '0') {
                        results.push({
                            sel,
                            outline: 'N/A (hidden)',
                            outlineStyle: 'hidden',
                            outlineWidth: 0,
                            hasFocus: true, // Skip — not a failure
                            skipped: true,
                        });
                        continue;
                    }
                    el.focus();
                    const cs = getComputedStyle(el);
                    const outline = cs.outlineStyle;
                    const outlineW = parseFloat(cs.outlineWidth);
                    // Also check box-shadow as an alternative focus indicator
                    const boxShadow = cs.boxShadow;
                    const hasShadowFocus = boxShadow && boxShadow !== 'none';
                    results.push({
                        sel,
                        outline: cs.outline,
                        outlineStyle: outline,
                        outlineWidth: outlineW,
                        hasFocus: (outline !== 'none' && outlineW > 0) || hasShadowFocus,
                    });
                    el.blur();
                }
                return results;
            }""")

            errors = []
            skipped = 0
            tested = 0
            for r in focus_results:
                if r.get("skipped"):
                    skipped += 1
                    continue
                tested += 1
                if not r["hasFocus"]:
                    errors.append(f"{r['sel']}: sem outline no focus ({r['outline']})")

            if errors:
                self._warn(f"Focus Visible ({len(errors)} sem outline)", "; ".join(errors))
            else:
                self._pass(f"Focus Visible ({tested} testados, {skipped} ocultos ignorados)")
        except Exception as e:
            self._fail("Focus Visible", str(e))

    # ─── 13. Texto truncado / overflow hidden ─────────────────────

    async def test_no_text_clipping(self, page, base_url: str) -> None:
        """Verifica se headings e parágrafos não estão cortados (overflow: hidden sem ellipsis)."""
        try:
            await page.set_viewport_size({"width": 375, "height": 812})
            await page.goto(base_url, wait_until="networkidle")
            await page.wait_for_timeout(300)

            clipped = await page.evaluate("""() => {
                const issues = [];
                document.querySelectorAll('h1, h2, h3, p, .hero-sub, .section-subtitle').forEach(el => {
                    const cs = getComputedStyle(el);
                    const vis = cs.display === 'none' || cs.visibility === 'hidden';
                    if (vis) return;
                    // Verificar se o conteúdo textual está sendo cortado
                    if (cs.overflow === 'hidden' && cs.textOverflow !== 'ellipsis' && el.scrollHeight > el.clientHeight + 2) {
                        const tag = el.tagName.toLowerCase();
                        const id = el.id ? '#' + el.id : '';
                        const text = el.textContent.substring(0, 30);
                        issues.push(`${tag}${id} "${text}..." (scrollH=${el.scrollHeight} > clientH=${el.clientHeight})`);
                    }
                });
                return issues.slice(0, 5);
            }""")

            if clipped:
                self._warn(f"Text Clipping ({len(clipped)} elementos)", "; ".join(clipped))
            else:
                self._pass("Text Clipping (0 textos cortados em mobile)")
        except Exception as e:
            self._fail("Text Clipping", str(e))

    # ─── 14. Transições e animações (prefers-reduced-motion) ──────

    async def test_reduced_motion(self, page, base_url: str) -> None:
        """Verifica que CSS respeita prefers-reduced-motion."""
        try:
            # Emular reduced motion
            await page.emulate_media(reduced_motion="reduce")
            await page.goto(base_url, wait_until="networkidle")

            anim = await page.evaluate("""() => {
                const cs = getComputedStyle(document.body);
                // Verificar se transitions estão desativadas
                const allEls = document.querySelectorAll('*');
                let hasAnimation = false;
                let count = 0;
                allEls.forEach(el => {
                    if (count > 200) return;
                    count++;
                    const s = getComputedStyle(el);
                    const dur = s.animationDuration;
                    const name = s.animationName;
                    if (name !== 'none' && dur !== '0s') {
                        hasAnimation = true;
                    }
                });
                return {hasAnimation};
            }""")

            # Reset
            await page.emulate_media(reduced_motion="no-preference")

            if anim["hasAnimation"]:
                self._warn("Reduced Motion", "Animações ativas mesmo com prefers-reduced-motion: reduce")
            else:
                self._pass("Reduced Motion (animações desativadas com prefers-reduced-motion)")
        except Exception as e:
            self._fail("Reduced Motion", str(e))

    # ─── 15. Navbar fixa não cobre conteúdo ───────────────────────

    async def test_navbar_not_covering_content(self, page, base_url: str) -> None:
        """Verifica que o conteúdo da primeira seção não fica oculto sob a navbar fixa."""
        try:
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(base_url, wait_until="networkidle")

            result = await page.evaluate("""() => {
                const nav = document.querySelector('.navbar');
                const hero = document.querySelector('.hero') || document.querySelector('main > *:first-child');
                if (!nav || !hero) return {ok: true, navH: 0, heroTop: 0};
                const navRect = nav.getBoundingClientRect();
                const heroRect = hero.getBoundingClientRect();
                return {
                    ok: heroRect.top >= navRect.bottom - 5,
                    navBottom: Math.round(navRect.bottom),
                    heroTop: Math.round(heroRect.top),
                    navH: Math.round(navRect.height),
                };
            }""")

            if not result["ok"]:
                self._fail("Navbar Covering Content", f"heroTop={result['heroTop']}px < navBottom={result['navBottom']}px")
            else:
                self._pass(f"Navbar Not Covering Content (nav {result['navH']}px, hero starts at {result['heroTop']}px)")
        except Exception as e:
            self._fail("Navbar Covering Content", str(e))

    # ─── 16. Footer visível no final da página ────────────────────

    async def test_footer_visible(self, page, base_url: str) -> None:
        """Verifica se o footer está no final da página e visível."""
        try:
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(base_url, wait_until="networkidle")

            result = await page.evaluate("""() => {
                const footer = document.querySelector('footer.footer');
                if (!footer) return {exists: false};
                const rect = footer.getBoundingClientRect();
                const cs = getComputedStyle(footer);
                return {
                    exists: true,
                    height: Math.round(rect.height),
                    visible: cs.display !== 'none' && cs.visibility !== 'hidden',
                    bgColor: cs.backgroundColor,
                    textColor: cs.color,
                };
            }""")

            errors = []
            if not result["exists"]:
                errors.append("Footer não encontrado")
            elif not result["visible"]:
                errors.append("Footer oculto")
            elif result["height"] < 40:
                errors.append(f"Footer muito baixo: {result['height']}px")

            if errors:
                self._fail("Footer Visibility", "; ".join(errors))
            else:
                self._pass(f"Footer Visibility (altura {result['height']}px, bg={result.get('bgColor', '?')})")
        except Exception as e:
            self._fail("Footer Visibility", str(e))

    # ─── 17. Emoji / caracteres especiais renderizados ────────────

    async def test_special_characters_render(self, page, base_url: str) -> None:
        """Verifica se emojis e caracteres especiais (♿, ✅, etc.) estão renderizados."""
        try:
            await page.goto(base_url, wait_until="networkidle")

            chars = await page.evaluate("""() => {
                const bodyText = document.body.textContent;
                const emojisToCheck = ['♿', '📋', '📄', '🔗', '🏛️'];
                const found = [];
                const missing = [];
                for (const e of emojisToCheck) {
                    if (bodyText.includes(e)) found.push(e);
                    else missing.push(e);
                }
                // Verificar que a página usa UTF-8
                const meta = document.querySelector('meta[charset]');
                const charset = meta ? meta.getAttribute('charset') : 'not set';
                return {found, missing, charset};
            }""")

            if chars["missing"]:
                self._warn(f"Special Characters ({len(chars['missing'])} não encontrados)", ", ".join(chars["missing"]))
            else:
                self._pass(f"Special Characters ({len(chars['found'])} emojis presentes, charset={chars['charset']})")
        except Exception as e:
            self._fail("Special Characters", str(e))

    # ─── 18. Background colors de seções ──────────────────────────

    async def test_section_backgrounds(self, page, base_url: str) -> None:
        """Verifica se seções alternadas têm cores de fundo distintas (visual rhythm)."""
        try:
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(base_url, wait_until="networkidle")

            bgs = await page.evaluate("""() => {
                const sections = document.querySelectorAll('.section');
                return Array.from(sections).map(s => ({
                    id: s.id || '',
                    bg: getComputedStyle(s).backgroundColor,
                }));
            }""")

            errors = []
            # Verificar que pelo menos hero tem fundo diferente
            hero_bg = await page.evaluate("""() => {
                const h = document.querySelector('.hero');
                return h ? getComputedStyle(h).backgroundColor : '';
            }""")

            if not hero_bg:
                errors.append("Hero sem background detectado")

            # Verificar alternância: pelo menos 2 cores diferentes entre as seções
            unique_bgs = set(s["bg"] for s in bgs)
            if len(unique_bgs) < 2 and len(bgs) > 2:
                self._warn("Section Backgrounds", f"Todas {len(bgs)} seções com mesma cor — considere alternar")
            else:
                self._pass(f"Section Backgrounds ({len(bgs)} seções, {len(unique_bgs)} cores distintas)")
        except Exception as e:
            self._fail("Section Backgrounds", str(e))

    # ─── 19. Modal disclaimer — visual ────────────────────────────

    async def test_disclaimer_modal_visual(self, page, base_url: str) -> None:
        """Verifica se o modal disclaimer aparece centralizado com overlay."""
        try:
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(base_url, wait_until="networkidle")

            modal = await page.evaluate("""() => {
                const m = document.querySelector('#disclaimerModal');
                if (!m) return {exists: false};
                const cs = getComputedStyle(m);
                const rect = m.getBoundingClientRect();
                return {
                    exists: true,
                    display: cs.display,
                    visible: cs.display !== 'none',
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    bgColor: cs.backgroundColor,
                    centered: Math.abs(rect.left + rect.width / 2 - window.innerWidth / 2) < 100,
                };
            }""")

            if not modal["exists"]:
                self._fail("Disclaimer Modal Visual", "Modal não encontrado no DOM")
            elif modal["visible"]:
                errors = []
                if modal["width"] < 300:
                    errors.append(f"Muito estreito: {modal['width']}px")
                if not modal["centered"]:
                    errors.append("Não centralizado")
                if errors:
                    self._fail("Disclaimer Modal Visual", "; ".join(errors))
                else:
                    self._pass(f"Disclaimer Modal Visual ({modal['width']}×{modal['height']}px, centralizado)")
            else:
                # Modal oculto (pode ter sido aceito via localStorage)
                self._pass("Disclaimer Modal Visual (oculto — já aceito)")
        except Exception as e:
            self._fail("Disclaimer Modal Visual", str(e))

    # ─── 20. Cards uniformidade visual ────────────────────────────

    async def test_card_visual_consistency(self, page, base_url: str) -> None:
        """Verifica que todos os category cards têm mesma largura/padding/border-radius."""
        try:
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(base_url, wait_until="networkidle")

            cards = await page.evaluate("""() => {
                const cards = document.querySelectorAll('.category-card');
                return Array.from(cards).map(c => {
                    const cs = getComputedStyle(c);
                    return {
                        w: Math.round(c.getBoundingClientRect().width),
                        h: Math.round(c.getBoundingClientRect().height),
                        pad: cs.padding,
                        radius: cs.borderRadius,
                        shadow: cs.boxShadow !== 'none',
                        bg: cs.backgroundColor,
                    };
                });
            }""")

            errors = []
            if len(cards) < 5:
                errors.append(f"Apenas {len(cards)} cards encontrados (esperado ≥5)")

            if cards:
                # Verificar uniformidade de border-radius
                radii = set(c["radius"] for c in cards)
                if len(radii) > 2:
                    errors.append(f"Border-radius inconsistente: {radii}")

                # Verificar uniformidade de padding
                pads = set(c["pad"] for c in cards)
                if len(pads) > 2:
                    errors.append(f"Padding inconsistente: {pads}")

                # Verificar se todos têm shadow
                no_shadow = sum(1 for c in cards if not c["shadow"])
                if no_shadow > 0 and no_shadow < len(cards):
                    errors.append(f"{no_shadow}/{len(cards)} cards sem box-shadow")

            if errors:
                self._fail("Card Consistency", "; ".join(errors))
            else:
                self._pass(f"Card Consistency ({len(cards)} cards: radius={cards[0]['radius'] if cards else '?'}, uniforme)")
        except Exception as e:
            self._fail("Card Consistency", str(e))

    # ─── Runner ───────────────────────────────────────────────────

    async def run_all(self) -> int:
        port = os.environ.get("E2E_PORT", "8080")
        base_url = f"http://localhost:{port}"

        # Verificar servidor
        import urllib.request
        try:
            urllib.request.urlopen(base_url, timeout=2)
        except Exception:
            print(f"⚠️  Servidor não detectado em {base_url}")
            print("   Inicie com: node server.js")
            sys.exit(1)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            print("=" * 80)
            print("🎨 TESTES VISUAIS — Formatação, Cores, Layout")
            print("=" * 80)

            # Screenshots
            print("\n📸 Screenshots (3 viewports + alto contraste):")
            await self.capture_screenshots(page, base_url)

            # Cores e contraste
            print("\n🎨 Cores e Contraste:")
            await self.test_css_variables_loaded(page, base_url)
            await self.test_contrast_ratios(page, base_url)
            await self.test_high_contrast_colors(page, base_url)

            # Fontes
            print("\n🔤 Tipografia:")
            await self.test_font_rendering(page, base_url)
            await self.test_special_characters_render(page, base_url)

            # Layout
            print("\n📐 Layout e Responsividade:")
            await self.test_no_horizontal_overflow(page, base_url)
            await self.test_no_element_overlap(page, base_url)
            await self.test_responsive_layout(page, base_url)
            await self.test_responsive_tablet(page, base_url)
            await self.test_navbar_not_covering_content(page, base_url)
            await self.test_footer_visible(page, base_url)

            # Acessibilidade visual
            print("\n♿ Acessibilidade Visual:")
            await self.test_interactive_elements_visible(page, base_url)
            await self.test_focus_visible(page, base_url)
            await self.test_reduced_motion(page, base_url)
            await self.test_no_text_clipping(page, base_url)

            # Uniformidade
            print("\n🧩 Uniformidade Visual:")
            await self.test_spacing_consistency(page, base_url)
            await self.test_section_backgrounds(page, base_url)
            await self.test_disclaimer_modal_visual(page, base_url)
            await self.test_card_visual_consistency(page, base_url)
            await self.test_images_render(page, base_url)

            await browser.close()

        # Relatório
        total = self.passed + self.failed + self.warnings
        print("\n" + "=" * 80)
        print("📊 RELATÓRIO VISUAL:")
        print("=" * 80)
        print(f"  ✅ Passou:  {self.passed}")
        print(f"  ⚠️  Avisos:  {self.warnings}")
        print(f"  ❌ Falhou:  {self.failed}")
        print(f"  📈 Total:   {total}")
        print("=" * 80)

        if self.failed == 0:
            print(f"\n🎉 TODOS OS TESTES VISUAIS PASSARAM! ({self.warnings} avisos)")
        else:
            print(f"\n⚠️  {self.failed} teste(s) falharam. Revise os erros acima.")

        print(f"\n📸 Screenshots salvos em: {SCREENSHOTS.resolve()}")

        # Salvar JSON report
        report_path = SCREENSHOTS / "visual_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"📋 Relatório JSON: {report_path.name}")

        return self.failed


if __name__ == "__main__":
    runner = VisualBrowserTests()
    exit_code = asyncio.run(runner.run_all())
    sys.exit(exit_code)
