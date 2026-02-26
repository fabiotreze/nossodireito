/**
 * NossoDireito — Service Worker (Network-First)
 * Habilita uso offline para famílias em áreas com conexão instável.
 *
 * Estratégia: Network-first para todos os assets do mesmo domínio (garante
 * conteúdo fresco após deploy); cache-first apenas para CDN externas.
 * Versão do cache: incrementar CACHE_VERSION ao fazer deploy para invalidar cache antigo.
 */

'use strict';

const CACHE_VERSION = 'nossodireito-v1.14.3';
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/css/styles.css',
    '/js/app.js',
    '/js/sw-register.js',
    '/data/direitos.json',
    '/data/matching_engine.json',
    '/data/dicionario_pcd.json',
    '/manifest.json',
    '/images/favicon.ico',
    '/images/favicon-32x32.png',
    '/images/apple-touch-icon.png',
    '/images/icon-192x192.png',
    '/images/icon-512x512-maskable.png',
    '/images/nossodireito-512.png',
    '/images/nossodireito-200.webp',
    '/images/nossodireito-400.webp',
    '/images/nossodireito-200.png',
    '/images/nossodireito-400.png',
    '/images/og-image.png',
];

const CDN_ASSETS = [
    'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js',
];

// ── Install: Pre-cache static assets ──
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_VERSION).then(async (cache) => {
            // Cache all assets in parallel (best-effort — don't fail install if any is missing)
            const allAssets = [...STATIC_ASSETS, ...CDN_ASSETS];
            await Promise.allSettled(allAssets.map(url =>
                cache.add(url).catch(() => console.warn(`[SW] Asset not cached: ${url}`))
            ));
        }).then(() => self.skipWaiting()) // Activate immediately after caching
    );
});

// ── Activate: Clean old caches ──
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys
                    .filter((key) => key !== CACHE_VERSION)
                    .map((key) => caches.delete(key))
            )
        ).then(() => self.clients.claim()) // Claim after old caches are deleted
    );
});

// ── Fetch: Strategy per resource type ──
self.addEventListener('fetch', (event) => {
    const { request } = event;

    // Only handle GET requests
    if (request.method !== 'GET') return;

    const url = new URL(request.url);

    // Don't cache SEO files — crawlers must always get fresh versions
    if (url.pathname === '/robots.txt' || url.pathname === '/sitemap.xml') return;

    // VLibras/CDN: let browser handle natively (avoid synthetic 503 from SW)
    if (url.hostname.includes('vlibras.gov.br') || url.hostname.includes('jsdelivr.net')) return;

    // External CDN assets (versioned URLs, immutable): Cache-first
    if (url.origin !== self.location.origin) {
        event.respondWith(cacheFirst(request));
        return;
    }

    // All same-origin assets (HTML, CSS, JS, JSON, images): Network-first
    // Garante conteúdo fresco após cada deploy; cai no cache apenas offline.
    event.respondWith(networkFirst(request));
});

/**
 * Cache-first: Return cached response, fall back to network.
 * Used only for external CDN assets (versioned/immutable URLs).
 */
async function cacheFirst(request) {
    const cached = await caches.match(request);
    if (cached) return cached;

    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_VERSION);
            await cache.put(request, response.clone());
        }
        return response;
    } catch {
        // Offline and not cached — return offline fallback for navigations
        return new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
    }
}

/**
 * Network-first: Try network, fall back to cache.
 * Best for dynamic content (JSON data, HTML).
 */
async function networkFirst(request) {
    // Use URL string (not Request object) for same-origin fetches.
    // Safari enforces strict CORS checks when passing a Request with
    // mode:'cors' through the SW, even for same-origin. Using the URL
    // string creates a fresh request that Safari handles correctly.
    const fetchTarget = request.url;
    try {
        const response = await fetch(fetchTarget);
        if (response.ok) {
            const cache = await caches.open(CACHE_VERSION);
            await cache.put(request, response.clone());
        }
        return response;
    } catch {
        const cached = await caches.match(request);
        if (cached) return cached;

        // If navigating and no cache, return offline page
        if (request.mode === 'navigate') {
            const offlineHtml = `<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><title>NossoDireito — Offline</title>
<style>body{font-family:system-ui;text-align:center;padding:60px 20px;background:#f8fafc;color:#1e293b}
h1{font-size:1.5rem;margin-bottom:16px}p{color:#64748b;margin-bottom:12px}
.btn{display:inline-block;padding:12px 24px;background:#1e40af;color:#fff;border-radius:8px;text-decoration:none;margin-top:16px}</style>
</head>
<body>
<h1>📱 Você está offline</h1>
<p>Não foi possível carregar o NossoDireito.</p>
<p>Verifique sua conexão e tente novamente.</p>
<a href="/" class="btn" onclick="location.reload();return false;">🔄 Tentar novamente</a>
</body></html>`;
            return new Response(offlineHtml, {
                status: 503,
                headers: { 'Content-Type': 'text/html; charset=utf-8' },
            });
        }

        return new Response('Offline', { status: 503 });
    }
}
