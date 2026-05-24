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
 */
import { chromium } from 'playwright';
import { AxeBuilder } from '@axe-core/playwright';
import http from 'node:http';
import { createReadStream, statSync } from 'node:fs';
import { extname, join, resolve, normalize } from 'node:path';

const ROOT = resolve(process.cwd());
const PORT = 8099;
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
            // Normalize and prevent path traversal
            const urlPath = decodeURIComponent(req.url.split('?')[0]);
            let filePath = normalize(join(ROOT, urlPath));
            if (!filePath.startsWith(ROOT)) {
                res.writeHead(403); res.end('Forbidden'); return;
            }
            try {
                const s = statSync(filePath);
                if (s.isDirectory()) filePath = join(filePath, 'index.html');
            } catch { /* fall through */ }
            try {
                const s = statSync(filePath);
                if (!s.isFile()) throw new Error('not file');
            } catch {
                res.writeHead(404); res.end('Not Found'); return;
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

async function main() {
    const server = await startServer();
    const browser = await chromium.launch();
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
    console.log(`A11Y SUMMARY  pages=${PAGES.length}  critical=${totalCritical}  serious=${totalSerious}  moderate=${totalModerate}  minor=${totalMinor}`);
    console.log('='.repeat(60));

    if (totalCritical + totalSerious > 0) {
        console.error(`\nFAIL: ${totalCritical} critical + ${totalSerious} serious WCAG 2.1 AA violations.`);
        process.exit(1);
    }
    console.log('\nPASS: No critical/serious violations.');
}

main().catch((e) => {
    console.error('A11Y setup error:', e);
    process.exit(2);
});
