/**
 * NossoDireito — Static File Server (Hardened)
 * Serve static files with defense-in-depth security.
 * Azure App Service (Node.js 22 LTS)
 *
 * Security posture: EASM-hardened (Defender EASM / Qualys / Shodan-proof)
 * Integrates with Azure Application Insights for telemetry.
 */

'use strict';

const http = require('node:http');
const fs = require('node:fs');
const fsPromises = require('node:fs/promises');
const path = require('node:path');
const zlib = require('node:zlib');
const crypto = require('node:crypto');

const PORT = process.env.PORT || 8080;

// ── Application Insights (server-side telemetry) ──
// Connection string is injected by Terraform via app_settings.
// If not present (local dev), telemetry is silently skipped.
let appInsights = null;
const AI_CONN = process.env.APPLICATIONINSIGHTS_CONNECTION_STRING || '';
if (AI_CONN) {
    try {
        appInsights = require('applicationinsights');
        appInsights.setup(AI_CONN)
            .setAutoCollectRequests(true)
            .setAutoCollectPerformance(true, true)
            .setAutoCollectExceptions(true)
            .setAutoCollectDependencies(false)
            .setAutoCollectConsole(false)
            .setDistributedTracingMode(appInsights.DistributedTracingModes.AI_AND_W3C)
            .setSendLiveMetrics(true)
            .start();
        // Periodic flush — minimize data loss on App Service restart.
        setInterval(() => {
            if (appInsights.defaultClient) appInsights.defaultClient.flush();
        }, 3600_000).unref(); // 1h, .unref() to not block graceful shutdown

        console.log('✅ Application Insights initialized');
    } catch (err) {
        console.log('ℹ️ applicationinsights package not available — telemetry disabled');
        appInsights = null;
    }
}

// ── Privacy-Respecting Visitor Analytics ──
// LGPD-compliant: zero cookies, zero fingerprinting, zero PII stored.
// IPs are anonymized via SHA-256 with a daily-rotating random salt.
// Only aggregated counters are kept in-memory (reset daily).
// Metrics are forwarded to Application Insights as custom events.
const analytics = {
    salt: crypto.randomBytes(32).toString('hex'),
    date: new Date().toISOString().slice(0, 10),
    pageViews: 0,
    uniqueVisitors: new Set(),
    byDevice: { desktop: 0, mobile: 0, tablet: 0 },
    byPath: new Map(),
    hourly: new Array(24).fill(0),
    history: [],            // last 30 days of {date, views, visitors}
};

/**
 * Rotate daily salt and archive yesterday's stats.
 * Called on every request — cheap Date comparison.
 */
function analyticsRotateIfNeeded() {
    const today = new Date().toISOString().slice(0, 10);
    if (today === analytics.date) return;

    // Archive previous day
    analytics.history.push({
        date: analytics.date,
        views: analytics.pageViews,
        visitors: analytics.uniqueVisitors.size,
        devices: { ...analytics.byDevice },
        topPages: [...analytics.byPath.entries()]
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10)
            .map(([p, c]) => ({ path: p, views: c })),
    });
    // Keep only last 30 days
    if (analytics.history.length > 30) analytics.history.shift();

    // Send summary to Application Insights (if available)
    if (appInsights) {
        const client = appInsights.defaultClient;
        if (client) {
            client.trackMetric({ name: 'daily_unique_visitors', value: analytics.uniqueVisitors.size });
            client.trackMetric({ name: 'daily_page_views', value: analytics.pageViews });
            client.trackMetric({ name: 'daily_desktop', value: analytics.byDevice.desktop });
            client.trackMetric({ name: 'daily_mobile', value: analytics.byDevice.mobile });
            client.trackMetric({ name: 'daily_tablet', value: analytics.byDevice.tablet });
        }
    }

    // Reset for new day with fresh salt (prevents cross-day correlation)
    analytics.salt = crypto.randomBytes(32).toString('hex');
    analytics.date = today;
    analytics.pageViews = 0;
    analytics.uniqueVisitors = new Set();
    analytics.byDevice = { desktop: 0, mobile: 0, tablet: 0 };
    analytics.byPath = new Map();
    analytics.hourly = new Array(24).fill(0);
}

/**
 * Detect device type from User-Agent (broad categories only — no fingerprinting).
 */
function detectDevice(ua) {
    if (!ua) return 'desktop';
    if (/tablet|ipad|playbook|silk/i.test(ua)) return 'tablet';
    if (/mobile|iphone|ipod|android.*mobile|windows phone|blackberry/i.test(ua)) return 'mobile';
    return 'desktop';
}

/**
 * Record a page view with privacy-preserving visitor dedup.
 * @param {string} ip - Raw client IP (never stored)
 * @param {string} ua - User-Agent header
 * @param {string} urlPath - Requested path
 */
function analyticsTrack(ip, ua, urlPath) {
    analyticsRotateIfNeeded();

    // Anonymize: SHA-256(salt + ip) — irreversible, non-correlatable across days
    const hash = crypto.createHash('sha256').update(analytics.salt + ip).digest('hex').slice(0, 16);
    const isNew = !analytics.uniqueVisitors.has(hash);
    analytics.uniqueVisitors.add(hash);

    analytics.pageViews++;

    // Device category
    const device = detectDevice(ua);
    if (isNew) analytics.byDevice[device]++;

    // Path tracking (top pages)
    const safePath = urlPath.split('?')[0].slice(0, 100); // strip query, limit length
    analytics.byPath.set(safePath, (analytics.byPath.get(safePath) || 0) + 1);
    // Cap map size to prevent memory abuse
    if (analytics.byPath.size > 500) {
        const sorted = [...analytics.byPath.entries()].sort((a, b) => b[1] - a[1]).slice(0, 100);
        analytics.byPath = new Map(sorted);
    }

    // Hourly distribution
    const hour = new Date().getHours();
    analytics.hourly[hour]++;

    // Real-time metric to App Insights (sampled — only on new visitors)
    if (isNew && appInsights) {
        const client = appInsights.defaultClient;
        if (client) {
            client.trackEvent({
                name: 'unique_visit',
                properties: { device, path: safePath },
            });
        }
    }

    // Track page view → populates `pageViews` table in App Insights.
    // NO raw IP sent — Azure auto-collects from the HTTP request and applies
    // IP masking at ingestion (stores 0.0.0.0 by default, DisableIpMasking=false).
    // Only anonymous aggregates (country/state) are derived and stored.
    // LGPD-safe: no PII transmitted, no PII stored.
    if (appInsights) {
        const client = appInsights.defaultClient;
        if (client) {
            client.trackPageView({
                name: safePath,
                url: safePath,
                properties: { device },
            });
        }
    }
}

// ── Rate Limiting (in-memory, per IP) ──
// Note: In-memory map acceptable for small-scale (institutional site).
// For high-traffic production: consider Redis + node-rate-limiter-flexible
// Limitations: memory growth with many IPs, resets on restart, vulnerable to distributed attacks
const RATE_LIMIT_WINDOW = 60_000;  // 1 minute
const RATE_LIMIT_MAX = 120;        // max requests per window
const rateLimitMap = new Map();

function isRateLimited(ip) {
    const now = Date.now();
    // Safety cap: prevent unbounded memory growth under distributed attack
    if (rateLimitMap.size > 50000) rateLimitMap.clear();
    const entry = rateLimitMap.get(ip);
    if (!entry || now - entry.start > RATE_LIMIT_WINDOW) {
        rateLimitMap.set(ip, { start: now, count: 1 });
        return false;
    }
    entry.count++;
    return entry.count > RATE_LIMIT_MAX;
}

// Cleanup stale entries every 5 minutes
setInterval(() => {
    const now = Date.now();
    for (const [ip, entry] of rateLimitMap) {
        if (now - entry.start > RATE_LIMIT_WINDOW) rateLimitMap.delete(ip);
    }
}, 300_000);

// MIME types (strict allowlist)
const MIME = Object.freeze({
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.ico': 'image/x-icon',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
    '.txt': 'text/plain; charset=utf-8',
    '.xml': 'application/xml; charset=utf-8',
});

// Cache policies (seconds)
const CACHE = Object.freeze({
    '.html': 'public, max-age=300, stale-while-revalidate=300',  // 5 min + serve stale while revalidating
    '.json': 'public, max-age=3600, stale-while-revalidate=600', // 1 hour + 10 min stale
    '.css': 'public, max-age=2592000, immutable',    // 30 days — never revalidate
    '.js': 'public, max-age=2592000, immutable',     // 30 days — never revalidate
    '.png': 'public, max-age=2592000, immutable',    // 30 days — never revalidate
    '.ico': 'public, max-age=2592000, immutable',    // 30 days — never revalidate
    '.svg': 'public, max-age=2592000, immutable',    // 30 days — never revalidate
    '.webp': 'public, max-age=2592000, immutable',   // 30 days — never revalidate
    '.xml': 'public, max-age=3600, stale-while-revalidate=600', // 1 hour + 10 min stale
    '.txt': 'public, max-age=86400',      // 1 day
});

// ── Security Headers (EASM-hardened) ──
// Covers: OWASP Secure Headers, Mozilla Observatory, Qualys SSL Labs
// Note: upgrade-insecure-requests is added dynamically only in production
// (not on localhost) — see buildCSP(). On localhost/HTTP it would break all
// resource loading by forcing HTTPS on a server without TLS.
const IS_PRODUCTION = !!(process.env.WEBSITE_SITE_NAME || process.env.NODE_ENV === 'production');

const CSP_DIRECTIVES = [
    "default-src 'none'",
    "script-src 'self' blob: https://cdnjs.cloudflare.com https://vlibras.gov.br https://*.vlibras.gov.br https://cdn.jsdelivr.net 'unsafe-eval' 'wasm-unsafe-eval'",
    "script-src-elem 'self' blob: https://vlibras.gov.br https://*.vlibras.gov.br https://cdnjs.cloudflare.com https://cdn.jsdelivr.net",
    "style-src 'self' 'unsafe-inline' https://*.vlibras.gov.br https://cdn.jsdelivr.net",
    "img-src 'self' data: blob: https://vlibras.gov.br https://*.vlibras.gov.br https://cdn.jsdelivr.net",
    "connect-src 'self' https://vlibras.gov.br https://*.vlibras.gov.br https://cdn.jsdelivr.net https://cdnjs.cloudflare.com data:",
    "worker-src 'self' blob: https://cdnjs.cloudflare.com https://vlibras.gov.br https://*.vlibras.gov.br",
    "child-src blob:",
    "frame-src 'self' https://*.vlibras.gov.br blob:",
    "media-src 'self' https://*.vlibras.gov.br",
    "font-src 'self' https://vlibras.gov.br https://*.vlibras.gov.br https://cdn.jsdelivr.net",
    "form-action 'none'",
    "base-uri 'self'",
    "frame-ancestors 'none'",
    "manifest-src 'self'",
];
if (IS_PRODUCTION) CSP_DIRECTIVES.push("upgrade-insecure-requests");

const SECURITY_HEADERS = Object.freeze({
    // ── Anti-XSS / Injection ──
    // Note: 'unsafe-eval' adicionado para VLibras Unity (trade-off: funcionalidade vs segurança)
    'Content-Security-Policy': CSP_DIRECTIVES.join('; '),
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',

    // ── Transport Security ──
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',

    // ── Privacy / Referrer ──
    // strict-origin-when-cross-origin: sends origin on cross-origin requests
    // (privacy-preserving) while allowing same-origin referral data for analytics.
    'Referrer-Policy': 'strict-origin-when-cross-origin',

    // ── Feature Restrictions ──
    // Note: accelerometer/gyroscope/magnetometer allowed for self —
    // VLibras Unity WebGL (Emscripten) calls _emscripten_set_devicemotion_callback
    // which requires accelerometer permission. Chromium enforces this via
    // Permissions-Policy; Safari does not. Blocking breaks VLibras on Windows.
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), bluetooth=(), serial=(), hid=(), accelerometer=(self), gyroscope=(self), magnetometer=(self), screen-wake-lock=()',

    // ── Cross-Origin Isolation ──
    'Cross-Origin-Opener-Policy': 'same-origin',
    'Cross-Origin-Resource-Policy': 'cross-origin',
    // COEP unsafe-none: VLibras (vlibras.gov.br) assets cross-origin não enviam
    // CORP headers. Safari não suporta 'credentialless'. require-corp quebraria
    // o carregamento do avatar Unity no Safari/iOS.
    'Cross-Origin-Embedder-Policy': 'unsafe-none',

    // ── Miscellaneous OWASP ──
    'X-Permitted-Cross-Domain-Policies': 'none',
    'X-DNS-Prefetch-Control': 'off',
    'X-Download-Options': 'noopen',
});

// Allowed file extensions (whitelist — reject everything else)
const ALLOWED_EXT = new Set(Object.keys(MIME));

// Compressible types
const COMPRESSIBLE = new Set(['.html', '.css', '.js', '.json', '.svg', '.txt', '.xml']);

// Blocked directories
const BLOCKED_DIRS = new Set(['terraform', 'node_modules', 'tests', '.github', 'docs', '__pycache__']);

// Max URL length (CWE-400 — prevent URL buffer attacks)
const MAX_URL_LENGTH = 2048;

const ROOT = __dirname;

// Cache package.json version at startup (avoid readFileSync on every health check)
const PKG_VERSION = JSON.parse(fs.readFileSync(path.join(__dirname, 'package.json'), 'utf8')).version;

async function resolveFile(urlPath) {
    // Reject null-byte injection (CWE-158)
    if (urlPath.includes('\0')) return null;

    // Reject oversized URLs (CWE-400)
    if (urlPath.length > MAX_URL_LENGTH) return null;

    // Reject non-ASCII control characters (CWE-116)
    if (/[\x00-\x1f\x7f]/.test(urlPath)) return null;

    // Normalize and prevent directory traversal (CWE-22)
    let filePath;
    try {
        filePath = path.normalize(decodeURIComponent(urlPath));
    } catch {
        return null; // malformed URI encoding
    }

    // Reject double-encoded traversal (e.g. %252e%252e)
    if (filePath.includes('..')) return null;

    if (filePath === '/' || filePath === '\\') filePath = '/index.html';

    const fullPath = path.join(ROOT, filePath);

    // Ensure within root (CWE-22)
    if (!fullPath.startsWith(ROOT + path.sep) && fullPath !== ROOT) return null;

    // Block dotfiles and sensitive directories (.env, .git, .github, etc.)
    const relative = path.relative(ROOT, fullPath);
    const segments = relative.split(path.sep);
    if (segments.some(seg => seg.startsWith('.'))) return null;

    // Block sensitive directories
    if (BLOCKED_DIRS.has(segments[0].toLowerCase())) return null;

    // Extension whitelist — only serve known safe types
    const ext = path.extname(fullPath).toLowerCase();
    if (ext && !ALLOWED_EXT.has(ext)) return null;

    // Reject files without extension (except index.html fallback)
    if (!ext && fullPath !== path.join(ROOT, 'index.html')) return null;

    // File must exist and be a regular file (no symlink following)
    try {
        const stat = await fsPromises.lstat(fullPath);
        if (stat.isFile() && !stat.isSymbolicLink()) return fullPath;
    } catch {
        // File doesn't exist
    }

    // SPA fallback only for navigation-like requests (no extension)
    // Requests with file extensions that don't exist → 404
    if (ext) return null;
    return path.join(ROOT, 'index.html');
}

const server = http.createServer(async (req, res) => {
    // ── Suppress server identification (CWE-200) ──
    res.removeHeader('X-Powered-By');

    // ── Method allowlist ──
    if (req.method !== 'GET' && req.method !== 'HEAD' && req.method !== 'OPTIONS') {
        res.writeHead(405, {
            'Content-Type': 'text/plain',
            'Allow': 'GET, HEAD, OPTIONS',
        });
        res.end('Method Not Allowed');
        return;
    }

    // ── Health check endpoint (Azure App Service probe) ──
    // Must respond 200 on ALL hosts (including *.azurewebsites.net)
    // before the domain redirect, otherwise probe marks app unhealthy.
    if (req.url === '/healthz' || req.url === '/health') {
        res.writeHead(200, {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store',
        });
        res.end(JSON.stringify({ status: 'healthy', version: PKG_VERSION }));
        return;
    }

    // ── Privacy Analytics Stats Endpoint ──
    // Returns aggregated, anonymous visitor statistics.
    // No PII is ever exposed. Protected by optional STATS_KEY env var.
    if (req.url === '/api/stats' || req.url === '/api/stats/') {
        // Optional auth: if STATS_KEY is set, require ?key= parameter
        const statsKey = process.env.STATS_KEY || '';
        if (statsKey) {
            let requestKey = '';
            try {
                requestKey = new URL(req.url, `http://${req.headers.host || 'localhost'}`).searchParams.get('key') || '';
            } catch { /* ignore */ }
            if (requestKey !== statsKey) {
                res.writeHead(403, { 'Content-Type': 'text/plain', ...SECURITY_HEADERS });
                res.end('Forbidden');
                return;
            }
        }
        analyticsRotateIfNeeded();
        const topPages = [...analytics.byPath.entries()]
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10)
            .map(([p, c]) => ({ path: p, views: c }));
        const stats = {
            date: analytics.date,
            today: {
                pageViews: analytics.pageViews,
                uniqueVisitors: analytics.uniqueVisitors.size,
                devices: { ...analytics.byDevice },
                topPages,
                hourly: [...analytics.hourly],
            },
            history: analytics.history,
            privacy: 'Nenhum dado pessoal é coletado. IPs são anonimizados via SHA-256 com salt rotativo diário.',
        };
        res.writeHead(200, {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store',
            ...SECURITY_HEADERS,
        });
        res.end(JSON.stringify(stats, null, 2));
        return;
    }

    // ── Rate limiting (CWE-770) ──
    // Use X-Forwarded-For only when behind a trusted reverse proxy (Azure App Service).
    // In local dev / direct exposure, fall back to socket address to prevent spoofing.
    const TRUST_PROXY = process.env.TRUST_PROXY === '1' || process.env.WEBSITE_SITE_NAME; // Azure injects WEBSITE_SITE_NAME
    const clientIp = TRUST_PROXY
        ? (req.headers['x-forwarded-for']?.split(',')[0]?.trim() || req.socket.remoteAddress || '')
        : (req.socket.remoteAddress || '');
    if (isRateLimited(clientIp)) {
        res.writeHead(429, {
            'Content-Type': 'text/plain',
            'Retry-After': '60',
        });
        res.end('Too Many Requests');
        return;
    }

    // ── URL validation ──
    if (req.url.length > MAX_URL_LENGTH) {
        res.writeHead(414, { 'Content-Type': 'text/plain' });
        res.end('URI Too Long');
        return;
    }

    // ── Host header validation (CWE-644) ──
    const host = req.headers.host || '';
    const CANONICAL_HOST = 'nossodireito.fabiotreze.com';
    const ALLOWED_HOSTS = [
        CANONICAL_HOST,
        'app-nossodireito.azurewebsites.net',  // Azure default domain
        `localhost:${PORT}`,
        `127.0.0.1:${PORT}`
    ];

    // ── CORS (Safari SW compat + govbr API proxy) ──
    // Safari enforces strict access-control checks on same-origin fetch
    // when routed through Service Worker. Explicit CORS headers resolve it.
    const origin = req.headers.origin || '';
    const ALLOWED_ORIGINS = [
        `https://${CANONICAL_HOST}`,
        `https://app-nossodireito.azurewebsites.net`,
        `http://localhost:${PORT}`,
        `http://127.0.0.1:${PORT}`,
    ];
    let corsOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : '';
    // Safari Service Worker compat: Safari enforces CORS checks on
    // same-origin fetches routed through SW, yet may omit the Origin header.
    // When no Origin is present and Host is a known host, infer same-origin.
    if (!corsOrigin && !origin && host) {
        const scheme = host.startsWith('localhost') || host.startsWith('127.') ? 'http' : 'https';
        const inferred = `${scheme}://${host}`;
        if (ALLOWED_ORIGINS.includes(inferred)) corsOrigin = inferred;
    }

    // Handle CORS preflight (OPTIONS)
    if (req.method === 'OPTIONS') {
        const preflightHeaders = {
            'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '86400',
            ...SECURITY_HEADERS,
        };
        if (corsOrigin) preflightHeaders['Access-Control-Allow-Origin'] = corsOrigin;
        res.writeHead(204, preflightHeaders);
        res.end();
        return;
    }

    // Redirect default Azure domain → canonical custom domain (SEO + security)
    // Only redirect browser requests (with Accept: text/html), not health probes
    if (host === 'app-nossodireito.azurewebsites.net' && req.headers.accept?.includes('text/html')) {
        const location = `https://${CANONICAL_HOST}${req.url}`;
        res.writeHead(301, {
            'Location': location,
            'Cache-Control': 'public, max-age=86400',
            ...SECURITY_HEADERS,
        });
        res.end();
        return;
    }

    // Strict host validation — exact match only (no subdomains)
    // Prevents attacks like malicious.nossodireito.fabiotreze.com
    if (host && !ALLOWED_HOSTS.includes(host)) {
        res.writeHead(421, { 'Content-Type': 'text/plain' });
        res.end('Misdirected Request');
        return;
    }

    // ── Parse urlPath BEFORE proxy (defensive architecture) ──
    let urlPath;
    try {
        urlPath = new URL(req.url, `http://${host || 'localhost'}`).pathname;
    } catch {
        res.writeHead(400, { 'Content-Type': 'text/plain' });
        res.end('Bad Request');
        return;
    }

    // ── Gov.br API proxy (CORS bypass for servicos.gov.br) ──
    // Proxy gov.br sem await (não dá SyntaxError nunca)
    const govbrMatch = req.url.match(/^\/api\/govbr-servico\/(\d+)$/);
    if (govbrMatch) {
        const servicoId = govbrMatch[1];
        // Limit servicoId length to prevent abuse (valid gov.br IDs are < 10 digits)
        if (servicoId.length > 10) {
            res.writeHead(400, { 'Content-Type': 'text/plain' });
            res.end('Bad Request');
            return;
        }
        const govbrUrl = `https://servicos.gov.br/api/v1/servicos/${servicoId}`;

        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5000); // 5s timeout

        fetch(govbrUrl, {
            signal: controller.signal,
            headers: { 'User-Agent': 'NossoDireito-Proxy/1.0' }
        })
            .then(r => {
                // Limit response body size (1 MB) to prevent memory abuse
                const contentLength = parseInt(r.headers.get('content-length') || '0', 10);
                if (contentLength > 1_048_576) {
                    throw new Error('Response too large');
                }
                return r.text().then(body => ({ r, body }));
            })
            .then(({ r, body }) => {
                clearTimeout(timeout);
                if (res.destroyed) return; // client disconnected
                const status = r.status;
                const cacheControl = r.ok ? 'public, max-age=3600' : 'no-cache';
                const proxyHeaders = {
                    'Content-Type': 'application/json',
                    'Cache-Control': cacheControl,
                    ...SECURITY_HEADERS,
                };
                if (corsOrigin) proxyHeaders['Access-Control-Allow-Origin'] = corsOrigin;
                res.writeHead(status, proxyHeaders);
                if (req.method === 'HEAD') {
                    res.end();
                    return;
                }
                if (r.ok) {
                    res.end(body);
                } else {
                    res.end(JSON.stringify({ error: 'Gov.br API unavailable' }));
                }
            })
            .catch(() => {
                clearTimeout(timeout);
                if (res.destroyed) return; // client already disconnected
                if (!res.headersSent) {
                    res.writeHead(503, {
                        'Content-Type': 'application/json',
                        'Cache-Control': 'no-cache',
                    });
                }
                if (!res.writableEnded) res.end(JSON.stringify({ error: 'Service unavailable' }));
            });
        return;
    }

    const fullPath = await resolveFile(urlPath);

    if (!fullPath) {
        res.writeHead(404, {
            'Content-Type': 'text/plain',
            ...SECURITY_HEADERS,
        });
        res.end('Not Found');
        return;
    }

    // ── Track page view (privacy-preserving) ──
    // Only track HTML page loads (not static assets like CSS/JS/images)
    const reqExt = path.extname(fullPath).toLowerCase();
    if (reqExt === '.html' || reqExt === '') {
        analyticsTrack(clientIp, req.headers['user-agent'] || '', urlPath);
    }

    const ext = path.extname(fullPath).toLowerCase();
    const contentType = MIME[ext] || 'application/octet-stream';
    // Service Worker must have short cache for update detection (browser spec)
    const isSW = urlPath === '/sw.js';
    const cacheControl = isSW ? 'no-cache' : (CACHE[ext] || 'no-cache');

    // Build response headers
    const headers = {
        'Content-Type': contentType,
        'Cache-Control': cacheControl,
        ...SECURITY_HEADERS,
    };

    // CORS header for same-origin (Safari SW compat)
    if (corsOrigin) headers['Access-Control-Allow-Origin'] = corsOrigin;

    // HTML-specific headers (no Link preload — resources are discovered
    // directly from HTML; preload hints cause Chrome "unused preload" warnings
    // because styles.css uses media=print defer and app.js uses defer)
    if (ext === '.html') {
        headers['Content-Language'] = 'pt-BR';
        headers['X-Robots-Tag'] = 'index, follow';
    } else if (ext === '.json') {
        headers['X-Robots-Tag'] = 'noindex';
    }

    // Compression for text-based content (Brotli > Gzip > None)
    const acceptEncoding = req.headers['accept-encoding'] || '';
    const useBrotli = COMPRESSIBLE.has(ext) && acceptEncoding.includes('br');
    const useGzip = !useBrotli && COMPRESSIBLE.has(ext) && acceptEncoding.includes('gzip');

    if (useBrotli) {
        headers['Content-Encoding'] = 'br';
        headers['Vary'] = 'Accept-Encoding';
    } else if (useGzip) {
        headers['Content-Encoding'] = 'gzip';
        headers['Vary'] = 'Accept-Encoding';
    }

    res.writeHead(200, headers);

    if (req.method === 'HEAD') {
        res.end();
        return;
    }

    const stream = fs.createReadStream(fullPath);
    if (useBrotli) {
        const compressor = zlib.createBrotliCompress();
        compressor.on('error', () => { if (!res.writableEnded) res.end(); });
        stream.pipe(compressor).pipe(res);
    } else if (useGzip) {
        const compressor = zlib.createGzip();
        compressor.on('error', () => { if (!res.writableEnded) res.end(); });
        stream.pipe(compressor).pipe(res);
    } else {
        stream.pipe(res);
    }

    stream.on('error', () => {
        if (!res.headersSent) {
            res.writeHead(500, { 'Content-Type': 'text/plain' });
        }
        if (!res.writableEnded) res.end('Internal Server Error');
    });
});

// ── Connection hardening ──
server.timeout = 30_000;           // 30s request timeout (anti-Slowloris)
server.headersTimeout = 70_000;    // 70s header timeout (must exceed keepAliveTimeout)
server.requestTimeout = 30_000;    // 30s total request timeout
server.keepAliveTimeout = 65_000;  // 65s keep-alive (must exceed Azure LB timeout)
server.maxHeadersCount = 50;       // Limit header count
server.maxRequestsPerSocket = 100; // Limit requests per keep-alive socket

// ── Graceful shutdown ──
function gracefulShutdown(signal) {
    console.log(`\n${signal} received — closing server gracefully...`);
    server.close(() => {
        console.log('Server closed.');
        process.exit(0);
    });
    // Force exit if close hangs after 5s
    setTimeout(() => process.exit(1), 5000).unref();
}
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));
// Windows: SIGBREAK is sent on Ctrl+Break and by Azure App Service for Windows
if (process.platform === 'win32') {
    process.on('SIGBREAK', () => gracefulShutdown('SIGBREAK'));
}

server.listen(PORT, () => {
    console.log(`NossoDireito server running on port ${PORT}`);
});
