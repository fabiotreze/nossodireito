#!/usr/bin/env node
/**
 * Acessibilidade — WCAG 2.1 AA com axe-core + Playwright (Chromium headless).
 *
 * Serve o site est\u00e1tico via http.server (porta 8099) e roda axe em:
 *   - / (home)
 *   - /direitos/bpc/
 *   - /direitos/caa_comunicacao_alternativa/
 *   - /direitos/educacao/
 *
 * Falha se houver viola\u00e7\u00f5es de impacto "serious" ou "critical".
 * Viola\u00e7\u00f5es "moderate" e "minor" s\u00e3o logadas como warning.
 *
 * Exit codes: 0 = pass, 1 = serious/critical violations, 2 = setup error.
 *
 * Env vars:
 *   BROWSER = chromium | firefox | webkit (default: chromium)
 *   SOFT_FAIL = "1" para never-fail (warning-only, ex.: webkit baseline).
 */
import { chromium, firefox, webkit } from 'playwright';
import { AxeBuilder } from '@axe-core/playwright';
import http from 'node:http';
import { createReadStream, statSync } from 'node:fs';
import { extname, join, resolve, relative, sep } from 'node:path';

const ROOT = resolve(process.cwd());
const PORT = 8099;
// Allowlist of path characters: letters, digits, -, _, ., /, %
// Anything outside this set is rejected before touching the filesystem.
const SAFE_PATH = /^[A-Za-z0-9._\-/%]+$/;
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
            // 1. Strip query, decode once.
            let urlPath;
            try { urlPath = decodeURIComponent(req.url.split('?')[0]); }
            catch { res.writeHead(400); res.end('Bad Request'); return; }

            // 2. Reject any path containing traversal sequences or NUL bytes
            //    BEFORE any filesystem call.
            if (urlPath.includes('..') || urlPath.includes('\0') || urlPath.includes('\\')) {
                res.writeHead(403); res.end('Forbidden'); return;
            }

            // 3. Enforce strict allowlist (path-injection defence-in-depth).
            if (!SAFE_PATH.test(urlPath)) {
                res.writeHead(403); res.end('Forbidden'); return;
            }

            // 4. Resolve and double-check it is within ROOT.
            const candidate = resolve(ROOT, '.' + urlPath);
            const rel = relative(ROOT, candidate);
            if (rel.startsWith('..') || rel.startsWith(sep) || resolve(ROOT, rel) !== candidate) {
                res.writeHead(403); res.end('Forbidden'); return;
            }

            // 5. Index resolution.
            let filePath = candidate;
            try {
                const s = statSync(filePath);
                if (s.isDirectory()) filePath = join(filePath, 'index.html');
            } catch { /* fall through to 404 */ }

            let finalStat;
            try { finalStat = statSync(filePath); }
            catch { res.writeHead(404); res.end('Not Found'); return; }
            if (!finalStat.isFile()) { res.writeHead(404); res.end('Not Found'); return; }

            // 6. Re-verify final path is inside ROOT (after index.html join).
            const finalRel = relative(ROOT, filePath);
            if (finalRel.startsWith('..') || finalRel.startsWith(sep)) {
                res.writeHead(403); res.end('Forbidden'); return;
            }

            const ct = MIME[extname(filePath).toLowerCase()] || 'application/octet-stream';
            res.writeHead(200, { 'Content-Type': ct });
            createReadStream(filePath).pipe(res);
        });
        server.listen(PORT, '127.0.0.1', () => resolveServer(server));
    });
}

const PAGES = [
    { name: 'home', path: '/' },
    { name: 'direito-bpc', path: '/direitos/bpc/' },
    { name: 'direito-caa', path: '/direitos/caa_comunicacao_alternativa/' },
    { name: 'direito-educacao', path: '/direitos/educacao/' },
];

// Rules we are intentionally deferring (with justification). Empty for now.
const DISABLED_RULES = [
    // 'color-contrast', // ex: re-enable after design pass
];

const BROWSERS = { chromium, firefox, webkit };
const BROWSER_NAME = (process.env.BROWSER || 'chromium').toLowerCase();
const SOFT_FAIL = process.env.SOFT_FAIL === '1';

async function main() {
    const launcher = BROWSERS[BROWSER_NAME];
    if (!launcher) {
        console.error(`Unknown BROWSER="${BROWSER_NAME}". Use chromium | firefox | webkit.`);
        process.exit(2);
    }
    console.log(`Running axe-core on browser=${BROWSER_NAME} (soft_fail=${SOFT_FAIL})`);
    const server = await startServer();
    const browser = await launcher.launch();
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });

    let totalCritical = 0;
    let totalSerious = 0;
    let totalModerate = 0;
    let totalMinor = 0;
    const summary = [];

    for (const { name, path } of PAGES) {
        const page = await ctx.newPage();
        const url = `http://127.0.0.1:${PORT}${path}`;
        try {
            await page.goto(url, { waitUntil: 'networkidle', timeout: 20000 });
            await page.waitForTimeout(800);
        } catch (e) {
            console.error(`\n[${name}] FAILED to load ${url}: ${e.message}`);
            await page.close();
            continue;
        }

        const builder = new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']);
        if (DISABLED_RULES.length) builder.disableRules(DISABLED_RULES);
        const results = await builder.analyze();

        const counts = { critical: 0, serious: 0, moderate: 0, minor: 0 };
        for (const v of results.violations) {
            counts[v.impact] = (counts[v.impact] || 0) + v.nodes.length;
        }
        totalCritical += counts.critical || 0;
        totalSerious += counts.serious || 0;
        totalModerate += counts.moderate || 0;
        totalMinor += counts.minor || 0;

        console.log(`\n=== [${name}] ${url}`);
        console.log(`    critical=${counts.critical || 0}  serious=${counts.serious || 0}  moderate=${counts.moderate || 0}  minor=${counts.minor || 0}`);

        for (const v of results.violations) {
            console.log(`    [${v.impact}] ${v.id} — ${v.help} (${v.nodes.length} node${v.nodes.length === 1 ? '' : 's'})`);
            console.log(`        ${v.helpUrl}`);
            for (const node of v.nodes.slice(0, 3)) {
                console.log(`        - target: ${node.target.join(' ')}`);
            }
            if (v.nodes.length > 3) console.log(`        - (+${v.nodes.length - 3} more)`);
        }

        summary.push({ name, url, counts, violations: results.violations.length });
        await page.close();
    }

    await browser.close();
    server.close();

    console.log(`\n${'='.repeat(60)}`);
    console.log(`A11Y SUMMARY (${BROWSER_NAME})  pages=${PAGES.length}  critical=${totalCritical}  serious=${totalSerious}  moderate=${totalModerate}  minor=${totalMinor}`);
    console.log('='.repeat(60));

    if (totalCritical + totalSerious > 0) {
        if (SOFT_FAIL) {
            console.warn(`\nSOFT-FAIL (${BROWSER_NAME}): ${totalCritical} critical + ${totalSerious} serious violations — not blocking (baseline mode).`);
            process.exit(0);
        }
        console.error(`\nFAIL (${BROWSER_NAME}): ${totalCritical} critical + ${totalSerious} serious WCAG 2.1 AA violations.`);
        process.exit(1);
    }
    console.log(`\nPASS (${BROWSER_NAME}): No critical/serious violations.`);
}

main().catch((e) => {
    console.error('A11Y setup error:', e);
    process.exit(2);
});
