#!/usr/bin/env node
/**
 * E2E smoke test (Playwright + Chromium headless)
 *
 * Cobre fluxos críticos do site estático:
 *   1. Home renderiza sem erros de console
 *   2. Trilhas (tabs) carregam e mostram cards
 *   3. Busca por "BPC" retorna resultados
 *   4. Click em card abre página de detalhe
 *   5. Disclaimer "catálogo público" aparece
 *   6. Voltar (history back) volta para home
 *   7. URL deep-link (#direito/bpc) renderiza direto a página de detalhe
 *
 * NÃO testa IA (precisa backend node + chave OpenAI).
 *
 * Reutiliza padrão do tests/a11y.mjs: HTTP server local porta 8098.
 *
 * Exit codes: 0 = pass, 1 = test failure, 2 = setup error.
 *
 * Env vars:
 *   SOFT_FAIL = "1" para never-fail (warning-only).
 */
import { chromium } from 'playwright';
import http from 'node:http';
import { createReadStream, statSync } from 'node:fs';
import { extname, join, resolve, relative, sep } from 'node:path';

const ROOT = resolve(process.cwd());
const PORT = 8098;
const SAFE_PATH = /^[A-Za-z0-9._\-/%]+$/;
const SOFT_FAIL = process.env.SOFT_FAIL === '1';

const MIME = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.mjs': 'application/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.webp': 'image/webp',
    '.ico': 'image/x-icon',
    '.woff2': 'font/woff2',
    '.txt': 'text/plain; charset=utf-8',
    '.xml': 'application/xml; charset=utf-8',
    '.webmanifest': 'application/manifest+json',
};

function startServer() {
    return new Promise((resolveServer) => {
        const server = http.createServer((req, res) => {
            let urlPath;
            try { urlPath = decodeURIComponent(req.url.split('?')[0]); }
            catch { res.writeHead(400); res.end('Bad Request'); return; }

            if (urlPath.includes('..') || urlPath.includes('\0') || urlPath.includes('\\')) {
                res.writeHead(403); res.end('Forbidden'); return;
            }
            if (!SAFE_PATH.test(urlPath)) {
                res.writeHead(403); res.end('Forbidden'); return;
            }
            const candidate = resolve(ROOT, '.' + urlPath);
            const rel = relative(ROOT, candidate);
            if (rel.startsWith('..') || rel.startsWith(sep) || resolve(ROOT, rel) !== candidate) {
                res.writeHead(403); res.end('Forbidden'); return;
            }
            let filePath = candidate;
            try {
                const s = statSync(filePath);
                if (s.isDirectory()) filePath = join(filePath, 'index.html');
            } catch { /* fall through */ }

            let finalStat;
            try { finalStat = statSync(filePath); }
            catch { res.writeHead(404); res.end('Not Found'); return; }
            if (!finalStat.isFile()) { res.writeHead(404); res.end('Not Found'); return; }

            const ct = MIME[extname(filePath).toLowerCase()] || 'application/octet-stream';
            res.writeHead(200, { 'Content-Type': ct });
            createReadStream(filePath).pipe(res);
        });
        server.listen(PORT, '127.0.0.1', () => resolveServer(server));
    });
}

const results = [];
function record(name, ok, detail) {
    results.push({ name, ok, detail });
    const tag = ok ? '✅ PASS' : '❌ FAIL';
    console.log(`  ${tag} ${name}${detail ? ' — ' + detail : ''}`);
}

async function withConsoleCapture(page) {
    const errors = [];
    page.on('console', (msg) => {
        if (msg.type() === 'error') errors.push(msg.text());
    });
    page.on('pageerror', (err) => errors.push('pageerror: ' + err.message));
    return errors;
}

async function testHomeLoads(page, baseUrl) {
    console.log('\n[1/7] Home carrega sem erros de console');
    const errors = await withConsoleCapture(page);
    await page.goto(baseUrl + '/', { waitUntil: 'networkidle', timeout: 20000 });
    const title = await page.title();
    record('home loads', /NossoDireito/i.test(title), `title="${title}"`);

    // Filtrar console errors esperados (favicon 404, etc se houver)
    const realErrors = errors.filter((e) => !/favicon|service.?worker/i.test(e));
    record('no console errors', realErrors.length === 0,
        realErrors.length > 0 ? `${realErrors.length}: ${realErrors[0].substring(0, 100)}` : 'clean');
}

async function testTrilhasRender(page) {
    console.log('\n[2/7] Trilhas (tabs) renderizam');
    const trilhas = await page.locator('.trilha-tab').count();
    record('trilhas count >= 6', trilhas >= 6, `found=${trilhas}`);

    // Aguarda categoryGrid popular
    await page.waitForSelector('.category-card', { timeout: 10000 });
    const cards = await page.locator('.category-card').count();
    record('category cards renderizados', cards >= 30, `cards=${cards}`);
}

async function testSearch(page) {
    console.log('\n[3/7] Busca por "BPC"');
    const input = page.locator('#searchInput');
    await input.fill('BPC');
    // Aguarda debounce + render
    await page.waitForTimeout(600);
    const searchResults = page.locator('#searchResults');
    const visible = await searchResults.isVisible();
    record('searchResults visível', visible);

    const html = (await searchResults.innerHTML()).toLowerCase();
    const hasBpc = html.includes('bpc') || html.includes('benefício de prestação continuada');
    record('resultado contém BPC', hasBpc,
        hasBpc ? 'match' : `len=${html.length}`);
}

async function testDetailNavigation(page, baseUrl) {
    console.log('\n[4/7] Click em card abre detalhe');
    // Limpa busca para voltar ao grid
    await page.locator('#searchInput').fill('');
    await page.waitForTimeout(400);

    // Click primeiro card visível
    const firstCard = page.locator('.category-card').first();
    const cardId = await firstCard.getAttribute('data-id');
    await firstCard.click();
    await page.waitForTimeout(500);

    const url = page.url();
    record('URL muda para #direito/...', url.includes('#direito/'), `url=${url.substring(url.indexOf('#'))}`);

    const detalheVisible = await page.locator('#detalhe').isVisible();
    record('seção detalhe visível', detalheVisible, cardId ? `id=${cardId}` : '');

    // Disclaimer "catálogo público"
    const bannerText = await page.locator('.banner-glossario').first().textContent().catch(() => '');
    const hasDisclaimer = bannerText && /catálogo público/i.test(bannerText);
    record('disclaimer "catálogo público" presente', !!hasDisclaimer,
        hasDisclaimer ? '' : `text="${(bannerText || '').substring(0, 60)}"`);
}

async function testBackNavigation(page) {
    console.log('\n[5/7] History back retorna para home');
    await page.goBack({ waitUntil: 'networkidle' });
    await page.waitForTimeout(400);

    const categoriasVisible = await page.locator('#categorias').isVisible();
    record('home (#categorias) visível', categoriasVisible);

    const detalheHidden = await page.locator('#detalhe').isHidden();
    record('detalhe escondido', detalheHidden);
}

async function testDeepLink(page, baseUrl) {
    console.log('\n[6/7] Deep-link #direito/bpc renderiza direto');
    await page.goto(baseUrl + '/#direito/bpc', { waitUntil: 'networkidle' });
    await page.waitForTimeout(800);

    const detalheVisible = await page.locator('#detalhe').isVisible();
    record('detalhe abre via deep-link', detalheVisible);

    const h2 = await page.locator('#detalhe h2').first().textContent().catch(() => '');
    record('título contém BPC', /bpc|benefício/i.test(h2 || ''), `h2="${(h2 || '').substring(0, 80)}"`);
}

async function testKeyboardAccessibility(page, baseUrl) {
    console.log('\n[7/7] Skip link + foco visível');
    await page.goto(baseUrl + '/', { waitUntil: 'networkidle' });
    // Pressiona Tab — primeiro foco deve ser skip link
    await page.keyboard.press('Tab');
    const focused = await page.evaluate(() => document.activeElement?.tagName + '#' + document.activeElement?.id);
    record('primeiro Tab foca em elemento válido', /A|BUTTON|INPUT/.test(focused.split('#')[0]),
        `focused=${focused}`);
}

async function main() {
    console.log('🎭 E2E smoke test (Playwright + Chromium)');
    console.log(`   soft_fail=${SOFT_FAIL}`);

    const server = await startServer();
    const baseUrl = `http://127.0.0.1:${PORT}`;
    const browser = await chromium.launch();
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();

    try {
        await testHomeLoads(page, baseUrl);
        await testTrilhasRender(page);
        await testSearch(page);
        await testDetailNavigation(page, baseUrl);
        await testBackNavigation(page);
        await testDeepLink(page, baseUrl);
        await testKeyboardAccessibility(page, baseUrl);
    } catch (e) {
        console.error('\n⚠️  Test runner crashed:', e.message);
        results.push({ name: 'runner', ok: false, detail: e.message });
    } finally {
        await browser.close();
        server.close();
    }

    const passed = results.filter((r) => r.ok).length;
    const failed = results.filter((r) => !r.ok).length;

    console.log(`\n${'='.repeat(60)}`);
    console.log(`E2E SUMMARY  passed=${passed}  failed=${failed}  total=${results.length}`);
    console.log('='.repeat(60));

    if (failed > 0) {
        console.log('\nFalhas:');
        for (const r of results.filter((x) => !x.ok)) {
            console.log(`  ❌ ${r.name}${r.detail ? ' — ' + r.detail : ''}`);
        }
        if (SOFT_FAIL) {
            console.warn(`\nSOFT-FAIL: ${failed} falha(s) — não bloqueia (baseline mode).`);
            process.exit(0);
        }
        process.exit(1);
    }
    console.log('\n✅ PASS: todos os fluxos críticos OK.');
}

main().catch((e) => {
    console.error('E2E setup error:', e);
    process.exit(2);
});
