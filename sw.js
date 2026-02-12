/**
 * NossoDireito — Service Worker (Cache-First)
 * Habilita uso offline para famílias em áreas com conexão instável.
 *
 * Estratégia: Cache-first para assets estáticos, network-first para dados JSON.
 * Versão do cache: incrementar CACHE_VERSION ao fazer deploy para invalidar cache antigo.
 */

'use strict';

const CACHE_VERSION = 'nossodireito-v1.4.3';
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/css/styles.css',
    '/js/app.js',
    '/data/direitos.json',
    '/data/matching_engine.json',
    '/manifest.json',
    '/images/favicon.ico',
    '/images/favicon-32x32.png',
    '/images/apple-touch-icon.png',
    '/images/nossodireito.png',
];

const CDN_ASSETS = [
    'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js',
];

// ── Install: Pre-cache static assets ──
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_VERSION).then(async (cache) => {
            // Cache local assets
            await cache.addAll(STATIC_ASSETS);
            // Cache CDN assets (best-effort — don't fail install if CDN is down)
            for (const url of CDN_ASSETS) {
                try {
                    await cache.add(url);
                } catch {
                    console.warn(`[SW] CDN asset not cached: ${url}`);
                }
            }
        })
    );
    // Activate immediately (don't wait for old SW to finish)
    self.skipWaiting();
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
        )
    );
    // Take control of all open tabs immediately
    self.clients.claim();
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

    // JSON data files: Network-first (always try to get fresh data)
    if (url.pathname.endsWith('.json') && url.origin === self.location.origin) {
        event.respondWith(networkFirst(request));
        return;
    }

    // HTML: Network-first (ensure latest version)
    if (request.mode === 'navigate' || url.pathname.endsWith('.html')) {
        event.respondWith(networkFirst(request));
        return;
    }

    // Static assets (CSS, JS, images, CDN): Cache-first
    event.respondWith(cacheFirst(request));
});

/**
 * Cache-first: Return cached response, fall back to network.
 * Best for immutable assets (CSS, JS, images).
 */
async function cacheFirst(request) {
    const cached = await caches.match(request);
    if (cached) return cached;

    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_VERSION);
            cache.put(request, response.clone());
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
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_VERSION);
            cache.put(request, response.clone());
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
