"""
NossoDireito — Full-Stack Emulated Browser Validation
Tests page rendering, CSS loading, JS initialization, all sections,
interactive features, mobile/desktop viewports, dark mode, accessibility,
and CSP compliance. Uses Playwright Chromium.
"""
import asyncio
import json
import sys
from playwright.async_api import async_playwright

PASS = 0
FAIL = 0
WARN = 0


def ok(label):
    global PASS
    PASS += 1
    print(f"  ✅ {label}")


def fail(label, detail=""):
    global FAIL
    FAIL += 1
    msg = f"  ❌ {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)


def warn(label, detail=""):
    global WARN
    WARN += 1
    msg = f"  ⚠️  {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        errors_js = []
        console_errors = []
        failed_reqs = []

        # ── DESKTOP VIEWPORT ──
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("pageerror", lambda e: errors_js.append(str(e)))
        page.on("console", lambda m: console_errors.append(f"[{m.type}] {m.text}") if m.type == "error" else None)
        page.on("requestfailed", lambda r: failed_reqs.append(f"{r.url} => {r.failure}"))

        print("\n═══════════════════════════════════════")
        print("  NossoDireito — Validação Completa")
        print("═══════════════════════════════════════\n")

        # ─── 1. PAGE LOAD ───
        print("1️⃣  Carregamento da Página")
        resp = await page.goto("http://localhost:8080/index.html", wait_until="networkidle", timeout=30000)
        if resp.status == 200:
            ok("HTTP 200")
        else:
            fail("HTTP status", str(resp.status))

        # ─── 2. CSS LOADING ───
        print("\n2️⃣  CSS & Estilos")

        css_links = await page.evaluate("""
            Array.from(document.querySelectorAll('link[rel=stylesheet]')).map(l => ({
                href: l.href, media: l.media
            }))
        """)
        css_loaded = any("styles.css" in c["href"] and c["media"] in ("all", "") for c in css_links)
        if css_loaded:
            ok("styles.css carregado e ativo (media=all)")
        else:
            fail("styles.css NÃO está ativo", str(css_links))

        inline_count = await page.evaluate("document.querySelectorAll('head style').length")
        if inline_count >= 1:
            ok(f"CSS crítico inline presente ({inline_count} bloco(s))")
        else:
            warn("CSS crítico inline ausente")

        bg = await page.evaluate("getComputedStyle(document.body).backgroundColor")
        if bg != "rgba(0, 0, 0, 0)":
            ok(f"Body background aplicado: {bg}")
        else:
            fail("Body sem background — CSS não aplicado")

        # ─── 3. HERO / H1 (LCP element) ───
        print("\n3️⃣  Hero / H1 (LCP)")

        hero = await page.evaluate("""(() => {
            const h = document.querySelector('.hero');
            if (!h) return null;
            const s = getComputedStyle(h);
            return {d: s.display, bg: s.backgroundImage, p: s.padding};
        })()""")
        if hero and "gradient" in hero.get("bg", ""):
            ok(f"Hero com gradiente: {hero['bg'][:60]}...")
        elif hero:
            fail("Hero sem gradiente", hero.get("bg", ""))
        else:
            fail("Elemento .hero não encontrado")

        h1 = await page.evaluate("""(() => {
            const h = document.querySelector('h1');
            if (!h) return null;
            const s = getComputedStyle(h);
            return {text: h.textContent.substring(0,50), fs: s.fontSize, color: s.color};
        })()""")
        if h1 and float(h1["fs"].replace("px", "")) > 20:
            ok(f"H1 visível: \"{h1['text']}...\" ({h1['fs']})")
        else:
            fail("H1 ausente ou sem estilo", str(h1))

        # ─── 4. NAVBAR ───
        print("\n4️⃣  Navbar")

        nav = await page.evaluate("""(() => {
            const n = document.querySelector('.navbar');
            if (!n) return null;
            const s = getComputedStyle(n);
            return {pos: s.position, top: s.top, z: s.zIndex, bg: s.backgroundColor};
        })()""")
        if nav and nav["pos"] == "sticky":
            ok(f"Navbar sticky (z-index: {nav['z']})")
        else:
            fail("Navbar não é sticky", str(nav))

        navlinks = await page.evaluate("""(() => {
            const nl = document.querySelector('.nav-links');
            if (!nl) return null;
            return {d: getComputedStyle(nl).display, kids: nl.children.length};
        })()""")
        if navlinks and navlinks["d"] == "flex" and navlinks["kids"] > 0:
            ok(f"Nav links visíveis no desktop ({navlinks['kids']} itens)")
        else:
            fail("Nav links não visíveis no desktop", str(navlinks))

        mt = await page.evaluate("document.querySelector('.menu-toggle') ? getComputedStyle(document.querySelector('.menu-toggle')).display : null")
        if mt == "none":
            ok("Menu toggle oculto no desktop")
        else:
            fail("Menu toggle deveria estar oculto no desktop", mt)

        # ─── 5. SECTIONS ───
        print("\n5️⃣  Seções Principais")

        expected_sections = ["inicio", "busca", "categorias", "checklist", "documentos",
                             "links", "classificacao", "orgaos-estaduais", "instituicoes", "transparencia"]
        sections = await page.evaluate("""
            Array.from(document.querySelectorAll('section')).map(s => ({
                id: s.id, d: getComputedStyle(s).display, h: s.offsetHeight
            }))
        """)
        section_map = {s["id"]: s for s in sections if s["id"]}
        for sid in expected_sections:
            s = section_map.get(sid)
            if s and s["d"] != "none" and s["h"] > 0:
                ok(f"#{sid}: visível ({s['h']}px)")
            elif s and s["d"] == "none":
                if sid == "detalhe":
                    ok(f"#{sid}: oculto (correto — mostra sob demanda)")
                else:
                    fail(f"#{sid}: display=none", str(s))
            else:
                fail(f"#{sid}: ausente ou vazio")

        # detalhe section (should be hidden by default)
        detalhe = section_map.get("detalhe")
        if detalhe and detalhe["d"] == "none":
            ok("#detalhe: oculto por padrão (correto)")
        elif detalhe:
            warn("#detalhe: deveria estar oculto", detalhe["d"])

        # ─── 6. INLINE DISCLAIMER ───
        print("\n6️⃣  Inline Disclaimer")

        disclaimer = await page.evaluate("""(() => {
            const d = document.getElementById('disclaimerInline');
            if (!d) return null;
            return {text: d.textContent.substring(0, 100)};
        })()""")
        if disclaimer:
            ok(f"Disclaimer inline presente no DOM")
        else:
            fail("Disclaimer #disclaimerInline não encontrado")

        footer_link = await page.evaluate("document.querySelector(\"a[href='#disclaimerInline']\") ? 'FOUND' : null")
        if footer_link:
            ok("Footer link aponta para #disclaimerInline")
        else:
            fail("Footer link para disclaimer ausente")

        # ─── 7. SEARCH ───
        print("\n7️⃣  Busca")

        search = await page.evaluate("""(() => {
            const input = document.getElementById('searchInput');
            const btn = document.getElementById('searchBtn');
            if (!input || !btn) return {input: !!input, btn: !!btn};
            return {
                input: true, btn: true,
                inputDisplay: getComputedStyle(input).display,
                btnDisplay: getComputedStyle(btn).display
            };
        })()""")
        if search.get("input") and search.get("btn"):
            ok(f"Input e botão de busca presentes")
        else:
            fail("Busca incompleta", str(search))

        # Test search functionality
        await page.fill("#searchInput", "BPC")
        await page.click("#searchBtn")
        await page.wait_for_timeout(500)
        results = await page.evaluate("""(() => {
            const r = document.getElementById('searchResults');
            if (!r) return {found: false};
            return {found: true, kids: r.children.length, d: getComputedStyle(r).display};
        })()""")
        if results.get("found") and results.get("kids", 0) > 0:
            ok(f"Busca por 'BPC' retornou {results['kids']} resultado(s)")
        elif results.get("found"):
            warn("Busca por 'BPC' sem resultados visíveis", str(results))
        else:
            fail("Container de resultados #searchResults ausente")

        # Clear search
        await page.fill("#searchInput", "")

        # ─── 8. CATEGORIES ───
        print("\n8️⃣  Categorias")

        cats = await page.evaluate("""(() => {
            const grid = document.getElementById('categoryGrid');
            if (!grid) return null;
            const cards = grid.querySelectorAll('.category-card');
            return {gridFound: true, count: cards.length};
        })()""")
        if cats and cats["count"] >= 20:
            ok(f"CategoryGrid com {cats['count']} cards")
        elif cats:
            warn(f"CategoryGrid com apenas {cats['count']} cards (esperado >= 20)")
        else:
            fail("CategoryGrid não encontrado")

        # Click a category card
        card_click = await page.evaluate("""(() => {
            const card = document.querySelector('.category-card');
            if (card) { card.click(); return true; }
            return false;
        })()""")
        if card_click:
            await page.wait_for_timeout(500)
            detalhe_vis = await page.evaluate("""(() => {
                const d = document.getElementById('detalhe');
                if (!d) return null;
                return {d: getComputedStyle(d).display, h: d.offsetHeight};
            })()""")
            if detalhe_vis and detalhe_vis["d"] != "none" and detalhe_vis["h"] > 0:
                ok(f"Click em card abre seção detalhe ({detalhe_vis['h']}px)")
            else:
                fail("Seção detalhe não abriu após click", str(detalhe_vis))

            # Click voltar
            voltar = await page.evaluate("""(() => {
                const btn = document.getElementById('voltarBtn');
                if (btn) { btn.click(); return true; }
                return false;
            })()""")
            if voltar:
                await page.wait_for_timeout(300)
                detalhe_hidden = await page.evaluate("getComputedStyle(document.getElementById('detalhe')).display")
                if detalhe_hidden == "none":
                    ok("Botão 'Voltar' fecha seção detalhe")
                else:
                    warn("Seção detalhe não fechou após voltar", detalhe_hidden)

        # ─── 9. ACCESSIBILITY PANEL ───
        print("\n9️⃣  Painel de Acessibilidade")

        a11y = await page.evaluate("""(() => {
            const trigger = document.getElementById('a11yPanelTrigger');
            const drawer = document.getElementById('a11yDrawer');
            const overlay = document.getElementById('a11yOverlay');
            return {
                trigger: trigger ? {d: getComputedStyle(trigger).display} : null,
                drawer: drawer ? {d: getComputedStyle(drawer).display, transform: getComputedStyle(drawer).transform} : null,
                overlay: overlay ? {d: getComputedStyle(overlay).display} : null
            };
        })()""")
        if a11y.get("trigger"):
            ok(f"Botão trigger a11y presente (display={a11y['trigger']['d']})")
        else:
            fail("Botão trigger a11y ausente")

        if a11y.get("drawer"):
            ok(f"Drawer a11y presente (display={a11y['drawer']['d']})")
        else:
            fail("Drawer a11y ausente")

        # Open a11y panel
        trigger_click = await page.evaluate("""(() => {
            const t = document.getElementById('a11yPanelTrigger');
            if (t) { t.click(); return true; }
            return false;
        })()""")
        if trigger_click:
            await page.wait_for_timeout(500)
            drawer_open = await page.evaluate("""(() => {
                const d = document.getElementById('a11yDrawer');
                if (!d) return null;
                const s = getComputedStyle(d);
                return {d: s.display, v: s.visibility, transform: s.transform};
            })()""")
            if drawer_open:
                ok(f"Drawer após click: display={drawer_open['d']}, transform={drawer_open.get('transform','')[:30]}")

            # Font controls
            font_btns = await page.evaluate("""(() => {
                return {
                    decrease: !!document.getElementById('a11yFontDecrease'),
                    reset: !!document.getElementById('a11yFontReset'),
                    increase: !!document.getElementById('a11yFontIncrease'),
                    contrast: !!document.getElementById('a11yContrast'),
                    libras: !!document.getElementById('a11yLibras'),
                    readAloud: !!document.getElementById('a11yReadAloud')
                };
            })()""")
            all_present = all(font_btns.values())
            if all_present:
                ok("Todos os controles a11y presentes (fonte, contraste, libras, voz)")
            else:
                missing = [k for k, v in font_btns.items() if not v]
                fail(f"Controles a11y faltando: {missing}")

            # Close drawer
            await page.evaluate("document.getElementById('a11yDrawerClose')?.click()")
            await page.wait_for_timeout(300)

        # ─── 10. CHECKLIST ───
        print("\n🔟  Checklist (Primeiros Passos)")

        checklist = await page.evaluate("""(() => {
            const items = document.querySelectorAll('.checklist-item, [class*=checklist] input[type=checkbox]');
            return {count: items.length};
        })()""")
        if checklist["count"] > 0:
            ok(f"Checklist com {checklist['count']} itens")
        else:
            warn("Checklist vazio ou não encontrado")

        # ─── 11. DOCUMENT UPLOAD ZONE ───
        print("\n1️⃣1️⃣  Upload de Documentos")

        upload = await page.evaluate("""(() => {
            const zone = document.getElementById('uploadZone');
            const input = document.getElementById('fileInput');
            return {zone: !!zone, input: !!input};
        })()""")
        if upload["zone"] and upload["input"]:
            ok("Zona de upload e input presentes")
        else:
            fail("Upload zone/input ausente", str(upload))

        # ─── 12. FOOTER ───
        print("\n1️⃣2️⃣  Footer")

        footer = await page.evaluate("""(() => {
            const f = document.querySelector('footer');
            if (!f) return null;
            const version = document.getElementById('footerVersion');
            return {
                found: true,
                text: f.textContent.substring(0, 100),
                version: version ? version.textContent : null
            };
        })()""")
        if footer and footer["found"]:
            ok(f"Footer presente")
            if footer.get("version") and "1.12.0" in footer["version"]:
                ok(f"Versão no footer: {footer['version']}")
            elif footer.get("version"):
                warn(f"Versão no footer: {footer['version']}")
        else:
            fail("Footer ausente")

        # ─── 13. BACK TO TOP ───
        print("\n1️⃣3️⃣  Back to Top")

        btt = await page.evaluate("""(() => {
            const b = document.querySelector('.back-to-top');
            if (!b) return null;
            return {d: getComputedStyle(b).display, pos: getComputedStyle(b).position};
        })()""")
        if btt:
            ok(f"Botão back-to-top presente (display={btt['d']})")
        else:
            fail("Botão back-to-top ausente")

        # ─── 14. JS ERRORS ───
        print("\n1️⃣4️⃣  Erros JavaScript")

        if not errors_js:
            ok("Nenhum erro JS (pageerror)")
        else:
            for e in errors_js:
                fail(f"JS Error: {e[:100]}")

        if not failed_reqs:
            ok("Nenhuma requisição falhou")
        else:
            for r in failed_reqs:
                fail(f"Request failed: {r[:100]}")

        console_real_errors = [e for e in console_errors if "favicon" not in e.lower()]
        if not console_real_errors:
            ok("Nenhum console.error relevante")
        else:
            for e in console_real_errors:
                warn(f"Console: {e[:100]}")

        # ─── 15. SKIP LINKS ───
        print("\n1️⃣5️⃣  Skip Links (Acessibilidade)")

        skip = await page.evaluate("""(() => {
            const links = document.querySelectorAll('.skip-link');
            return Array.from(links).map(l => ({
                text: l.textContent.trim(),
                href: l.getAttribute('href'),
                d: getComputedStyle(l).display,
                top: getComputedStyle(l).top
            }));
        })()""")
        if len(skip) >= 3:
            visible_skip = [s for s in skip if float(s["top"].replace("px","").replace("%","") if s["top"] not in ("auto","") else "0") >= 0]
            if not visible_skip:
                ok(f"{len(skip)} skip links presentes e ocultos (off-screen)")
            else:
                warn(f"{len(visible_skip)} skip links com top >= 0 (deviam estar ocultos)")
        else:
            fail(f"Apenas {len(skip)} skip links (esperado >= 3)")

        # ─── 16. VLIBRAS WIDGET ───
        print("\n1️⃣6️⃣  VLibras Widget")

        vl = await page.evaluate("!!document.querySelector('[vw]')")
        if vl:
            ok("Widget VLibras div presente")
        else:
            warn("Widget VLibras div ausente")

        # ─── DESKTOP SCREENSHOT ───
        await page.screenshot(path="screenshots/validation_desktop.png", full_page=False)
        ok("Screenshot desktop salvo")

        # ═══════════════════════════
        # ── MOBILE VIEWPORT ──
        # ═══════════════════════════
        print("\n═══════════════════════════════════════")
        print("  📱 Validação Mobile (375×812)")
        print("═══════════════════════════════════════\n")

        await page.set_viewport_size({"width": 375, "height": 812})
        await page.wait_for_timeout(800)

        # Mobile nav hidden
        mobile_nav = await page.evaluate("""(() => {
            const nl = document.querySelector('.nav-links');
            if (!nl) return {found: false};
            const s = getComputedStyle(nl);
            return {found: true, d: s.display, transform: s.transform, v: s.visibility};
        })()""") 
        if not mobile_nav.get("found"):
            fail("Nav links não encontrado no mobile")
        elif mobile_nav["d"] == "none":
            ok(f"Nav links ocultos no mobile (display=none)")
        else:
            # Check if hidden via transform (translateY negative or matrix with negative Y)
            t = mobile_nav.get("transform", "")
            hidden = False
            if "translateY" in t and "-" in t:
                hidden = True
            elif t.startswith("matrix("):
                # matrix(a,b,c,d,tx,ty) — check if ty is negative
                parts = t.replace("matrix(", "").replace(")", "").split(",")
                if len(parts) == 6:
                    try:
                        ty = float(parts[5].strip())
                        hidden = ty < -50
                    except ValueError:
                        pass
            if hidden:
                ok(f"Nav links ocultos no mobile via transform ({t[:40]})")
            else:
                fail(f"Nav links deveriam estar ocultos no mobile", str(mobile_nav))

        # Mobile menu toggle visible
        mobile_mt = await page.evaluate("getComputedStyle(document.querySelector('.menu-toggle')).display")
        if mobile_mt != "none":
            ok(f"Menu toggle visível no mobile (display={mobile_mt})")
        else:
            fail("Menu toggle oculto no mobile (deveria estar visível)")

        # Mobile H1 size
        mobile_h1 = await page.evaluate("""(() => {
            const h = document.querySelector('h1');
            return {fs: getComputedStyle(h).fontSize};
        })()""")
        fs = float(mobile_h1["fs"].replace("px", ""))
        if fs < 35:
            ok(f"H1 mobile com tamanho adequado ({mobile_h1['fs']})")
        else:
            warn(f"H1 mobile muito grande ({mobile_h1['fs']})")

        # Mobile hero layout
        hero_dir = await page.evaluate("getComputedStyle(document.querySelector('.hero-grid')).flexDirection")
        if hero_dir == "column":
            ok(f"Hero grid em coluna no mobile (flex-direction={hero_dir})")
        else:
            fail(f"Hero grid deveria ser column no mobile, é {hero_dir}")

        # Mobile hamburger menu
        mt_click = await page.evaluate("""(() => {
            const mt = document.querySelector('.menu-toggle');
            if (mt) { mt.click(); return true; }
            return false;
        })()""")
        if mt_click:
            await page.wait_for_timeout(500)
            mobile_nav_after = await page.evaluate("getComputedStyle(document.querySelector('.nav-links')).display")
            if mobile_nav_after != "none":
                ok(f"Menu hamburger abre nav (display={mobile_nav_after})")
                # Close it
                await page.evaluate("document.querySelector('.menu-toggle').click()")
                await page.wait_for_timeout(300)
            else:
                warn("Menu hamburger não abriu nav links")

        await page.screenshot(path="screenshots/validation_mobile.png", full_page=False)
        ok("Screenshot mobile salvo")

        # ═══════════════════════════
        # ── DARK MODE ──
        # ═══════════════════════════
        print("\n═══════════════════════════════════════")
        print("  🌙 Validação Dark Mode")
        print("═══════════════════════════════════════\n")

        await page.set_viewport_size({"width": 1280, "height": 900})

        # Emulate dark mode
        await page.emulate_media(color_scheme="dark")
        await page.wait_for_timeout(500)

        dark_bg = await page.evaluate("getComputedStyle(document.body).backgroundColor")
        # Dark background should be dark (low RGB values)
        if "15, 23, 42" in dark_bg or "0, 0, 0" in dark_bg or "rgb(0" in dark_bg:
            ok(f"Dark mode background: {dark_bg}")
        else:
            # Check CSS variables
            dark_surface = await page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--surface').trim()")
            if dark_surface and dark_surface != "#ffffff":
                ok(f"Dark mode --surface: {dark_surface}")
            else:
                warn(f"Dark mode pode não estar aplicado (bg={dark_bg})")

        dark_text = await page.evaluate("getComputedStyle(document.body).color")
        if "241, 245, 249" in dark_text or "255, 255, 255" in dark_text or "248" in dark_text:
            ok(f"Dark mode text color: {dark_text}")
        else:
            warn(f"Dark mode text color: {dark_text}")

        await page.screenshot(path="screenshots/validation_darkmode.png", full_page=False)
        ok("Screenshot dark mode salvo")

        # Reset to light
        await page.emulate_media(color_scheme="light")

        # ═══════════════════════════
        # ── DATA INTEGRITY ──
        # ═══════════════════════════
        print("\n═══════════════════════════════════════")
        print("  📊 Integridade dos Dados")
        print("═══════════════════════════════════════\n")

        data_check = await page.evaluate("""(async () => {
            try {
                const r = await fetch('/data/direitos.json');
                const d = await r.json();
                return {
                    ok: true,
                    cats: d.categorias ? d.categorias.length : 0,
                    version: d.meta ? d.meta.versao : null,
                    lastUpdate: d.meta ? d.meta.ultima_atualizacao : null
                };
            } catch(e) {
                return {ok: false, error: e.message};
            }
        })()""")
        if data_check.get("ok"):
            ok(f"direitos.json: {data_check['cats']} categorias, v{data_check.get('version')}")
        else:
            fail("direitos.json falhou", data_check.get("error"))

        matching = await page.evaluate("""(async () => {
            try {
                const r = await fetch('/data/matching_engine.json');
                const d = await r.json();
                return {ok: true, keys: Object.keys(d).length};
            } catch(e) {
                return {ok: false, error: e.message};
            }
        })()""")
        if matching.get("ok"):
            ok(f"matching_engine.json: {matching['keys']} chaves")
        else:
            fail("matching_engine.json falhou", matching.get("error"))

        # ═══════════════════════════
        # ── CSP SIMULATION ──
        # ═══════════════════════════
        print("\n═══════════════════════════════════════")
        print("  🔒 Simulação CSP (server.js)")
        print("═══════════════════════════════════════\n")

        # Check if there are any inline event handlers that CSP would block
        inline_handlers = await page.evaluate("""(() => {
            const all = document.querySelectorAll('*');
            const handlers = [];
            const events = ['onclick','onload','onerror','onchange','onsubmit','onfocus','onblur',
                            'onmouseover','onmouseout','onkeydown','onkeyup','onkeypress','onscroll',
                            'onresize','oninput'];
            for (const el of all) {
                for (const ev of events) {
                    if (el.getAttribute(ev)) {
                        handlers.push({
                            tag: el.tagName,
                            id: el.id || '',
                            cls: (el.className?.substring ? el.className.substring(0,30) : ''),
                            event: ev,
                            value: el.getAttribute(ev).substring(0, 50)
                        });
                    }
                }
            }
            return handlers;
        })()""")

        if not inline_handlers:
            ok("Nenhum handler inline encontrado (CSP-safe)")
        else:
            for h in inline_handlers:
                fail(f"Handler inline: <{h['tag']} {h['event']}=\"{h['value']}\"> — CSP bloquearia em produção!",
                     f"id={h['id']} class={h['cls']}")

        # Check inline scripts (not type=application/ld+json)
        inline_scripts = await page.evaluate("""(() => {
            const scripts = document.querySelectorAll('script:not([src]):not([type="application/ld+json"])');
            return Array.from(scripts).map(s => ({
                type: s.type,
                content: s.textContent.substring(0, 80)
            }));
        })()""")
        if not inline_scripts:
            ok("Nenhum script inline (exceto LD+JSON)")
        else:
            for s in inline_scripts:
                warn(f"Script inline: type={s['type']}, conteúdo: {s['content']}")

        # ═══════════════════════════
        # ── PERFORMANCE CHECKS ──
        # ═══════════════════════════
        print("\n═══════════════════════════════════════")
        print("  ⚡ Performance")
        print("═══════════════════════════════════════\n")

        # Check for transition: all
        transition_all = await page.evaluate("""(() => {
            let count = 0;
            const sheets = document.styleSheets;
            for (const sheet of sheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        if (rule.style && rule.style.transition && rule.style.transition.includes('all')) {
                            count++;
                        }
                    }
                } catch(e) {} // cross-origin
            }
            return count;
        })()""")
        if transition_all == 0:
            ok("Nenhum transition: all encontrado")
        else:
            warn(f"{transition_all} transition: all encontrado(s)")

        # CLS check — hero-actions min-height
        hero_mh = await page.evaluate("""(() => {
            const ha = document.querySelector('.hero-actions');
            if (!ha) return null;
            return getComputedStyle(ha).minHeight;
        })()""")
        if hero_mh and hero_mh != "auto" and hero_mh != "0px":
            ok(f"Hero actions min-height: {hero_mh} (CLS fix)")
        else:
            warn(f"Hero actions sem min-height: {hero_mh}")

        await browser.close()

        # ═══════════════════════════
        # ── SUMMARY ──
        # ═══════════════════════════
        print("\n═══════════════════════════════════════")
        print(f"  📋 RESULTADO FINAL")
        print(f"  ✅ Passou: {PASS}")
        print(f"  ❌ Falhou: {FAIL}")
        print(f"  ⚠️  Avisos: {WARN}")
        print("═══════════════════════════════════════\n")

        if FAIL > 0:
            print(f"❌ {FAIL} FALHA(S) ENCONTRADA(S) — NÃO COMITAR")
            sys.exit(1)
        else:
            print("✅ TODAS AS VALIDAÇÕES PASSARAM — PRONTO PARA COMMIT")
            sys.exit(0)

asyncio.run(main())
