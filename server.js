/**
 * NossoDireito — Static File Server (Hardened)
 * Serve static files with defense-in-depth security.
 * Azure App Service (Node.js 20 LTS)
 *
 * Security posture: EASM-hardened (Defender EASM / Qualys / Shodan-proof)
 * Integrates with Azure Application Insights for telemetry.
 */

'use strict';

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');

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
        console.log('✅ Application Insights initialized');
    } catch (err) {
        console.log('ℹ️ applicationinsights package not available — telemetry disabled');
        appInsights = null;
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
    '.html': 'public, max-age=300',    // 5 min
    '.json': 'public, max-age=3600',   // 1 hour
    '.css': 'public, max-age=86400',   // 1 day
    '.js': 'public, max-age=86400',    // 1 day
    '.png': 'public, max-age=604800',  // 1 week
    '.ico': 'public, max-age=604800',
    '.svg': 'public, max-age=604800',
    '.webp': 'public, max-age=604800',
    '.xml': 'public, max-age=3600',     // 1 hour
    '.txt': 'public, max-age=86400',     // 1 day
});

// ── Security Headers (EASM-hardened) ──
// Covers: OWASP Secure Headers, Mozilla Observatory, Qualys SSL Labs
const SECURITY_HEADERS = Object.freeze({
    // ── Anti-XSS / Injection ──
    // Note: 'unsafe-eval' adicionado para VLibras Unity (trade-off: funcionalidade vs segurança)
    'Content-Security-Policy': [
        "default-src 'none'",
        "script-src 'self' blob: https://cdnjs.cloudflare.com https://vlibras.gov.br https://*.vlibras.gov.br https://cdn.jsdelivr.net 'unsafe-eval' 'wasm-unsafe-eval'",
        "script-src-elem 'self' https://vlibras.gov.br https://*.vlibras.gov.br https://cdnjs.cloudflare.com https://cdn.jsdelivr.net",
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
        "upgrade-insecure-requests",
    ].join('; '),
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',

    // ── Transport Security ──
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',

    // ── Privacy / Referrer ──
    'Referrer-Policy': 'no-referrer',

    // ── Feature Restrictions ──
    // Note: VLibras Unity WebAssembly requer accelerometer/gyroscope para funcionar.
    // Relaxado para (self) mantendo bloqueio de third-party trackers.
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), bluetooth=(), serial=(), hid=(), accelerometer=(self), gyroscope=(self), magnetometer=(), screen-wake-lock=()',

    // ── Cross-Origin Isolation ──
    'Cross-Origin-Opener-Policy': 'same-origin',
    'Cross-Origin-Resource-Policy': 'cross-origin',
    // COEP require-corp para isolamento cross-origin mais restritivo
    'Cross-Origin-Embedder-Policy': 'require-corp',

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
const BLOCKED_DIRS = new Set(['terraform', 'codereview', 'node_modules', 'tests', '.github', 'docs', '__pycache__']);

// Max URL length (CWE-400 — prevent URL buffer attacks)
const MAX_URL_LENGTH = 2048;

const ROOT = __dirname;

function resolveFile(urlPath) {
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
        const stat = fs.lstatSync(fullPath);
        if (stat.isFile() && !stat.isSymbolicLink()) return fullPath;
    } catch {
        // File doesn't exist — fall through to SPA fallback
    }

    // Fallback: serve index.html for SPA navigation
    return path.join(ROOT, 'index.html');
}

const server = http.createServer((req, res) => {
    // ── Suppress server identification (CWE-200) ──
    res.removeHeader('X-Powered-By');

    // ── Method allowlist ──
    if (req.method !== 'GET' && req.method !== 'HEAD') {
        res.writeHead(405, {
            'Content-Type': 'text/plain',
            'Allow': 'GET, HEAD',
        });
        res.end('Method Not Allowed');
        return;
    }

    // ── Health check endpoint (Azure App Service probe) ──
    // Must respond 200 on ALL hosts (including *.azurewebsites.net)
    // before the domain redirect, otherwise probe marks app unhealthy.
    if (req.url === '/healthz') {
        res.writeHead(200, {
            'Content-Type': 'text/plain',
            'Cache-Control': 'no-cache, no-store',
        });
        res.end('OK');
        return;
    }

    // ── Rate limiting (CWE-770) ──
    const clientIp = req.headers['x-forwarded-for']?.split(',')[0]?.trim() || req.socket.remoteAddress || '';
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
        const govbrUrl = `https://servicos.gov.br/api/v1/servicos/${servicoId}`;

        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5000); // 5s timeout

        fetch(govbrUrl, {
            signal: controller.signal,
            headers: { 'User-Agent': 'NossoDireito-Proxy/1.0' }
        })
        .then(r => r.text().then(body => ({ r, body })))
        .then(({ r, body }) => {
            clearTimeout(timeout);
            const status = r.ok ? r.status : r.status;
            const cacheControl = r.ok ? 'public, max-age=3600' : 'no-cache';
            res.writeHead(status, {
                'Content-Type': 'application/json',
                'Cache-Control': cacheControl,
                ...SECURITY_HEADERS,
            });
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
            res.writeHead(503, {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache',
            });
            res.end(JSON.stringify({ error: 'Service unavailable' }));
        });
        return;
    }

    const fullPath = resolveFile(urlPath);

    if (!fullPath) {
        res.writeHead(404, {
            'Content-Type': 'text/plain',
            ...SECURITY_HEADERS,
        });
        res.end('Not Found');
        return;
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
        stream.pipe(zlib.createBrotliCompress()).pipe(res);
    } else if (useGzip) {
        stream.pipe(zlib.createGzip()).pipe(res);
    } else {
        stream.pipe(res);
    }

    stream.on('error', () => {
        if (!res.headersSent) {
            res.writeHead(500, { 'Content-Type': 'text/plain' });
        }
        res.end('Internal Server Error');
    });
});

// ── Connection hardening ──
server.timeout = 30_000;           // 30s request timeout (anti-Slowloris)
server.headersTimeout = 15_000;    // 15s header timeout
server.requestTimeout = 30_000;    // 30s total request timeout
server.keepAliveTimeout = 5_000;   // 5s keep-alive
server.maxHeadersCount = 50;       // Limit header count
server.maxRequestsPerSocket = 100; // Limit requests per keep-alive socket

server.listen(PORT, () => {
    console.log(`NossoDireito server running on port ${PORT}`);
});
