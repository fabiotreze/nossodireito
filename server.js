/**
 * NossoDireito — Static File Server (Hardened)
 * Serve static files with defense-in-depth security.
 * Azure App Service (Node.js 22 LTS)
 *
 * Security posture: EASM-hardened (Defender EASM / Qualys / Shodan-proof).
 */

"use strict";

const http = require("node:http");
const fs = require("node:fs");
const fsPromises = require("node:fs/promises");
const path = require("node:path");
const zlib = require("node:zlib");
const crypto = require("node:crypto");

// ── Lib modules (Onda 7 — modularização) ──
const { MIME, CACHE, COMPRESSIBLE } = require("./lib/mime");
const { SECURITY_HEADERS } = require("./lib/security-headers");
const { resolveFile } = require("./lib/file-resolver");
const { createAnalytics } = require("./lib/analytics");
const { createRateLimiter } = require("./lib/rate-limit");
const { createRedisClient } = require("./lib/redis-client");
const { createAiAnalyzeHandler } = require("./lib/ai-analyze");
const { createGovBrProxy } = require("./lib/govbr-proxy");
const {
  createHealthHandler,
  createStatsHandler,
  createSecurityTxtHandler,
} = require("./lib/infra-handlers");

// ── IA opt-in (Azure OpenAI) ──
// Anonymizer roda em Node + browser. Aqui é o double-check de PII.
const { anonymize, containsPII } = require("./shared/anonymizer");
// Cliente Azure OpenAI é lazy-loaded (require interno).
const AI_ANALYSIS_ENABLED = process.env.AI_ANALYSIS_ENABLED === "true";
const REDIS_RATE_LIMIT_ENABLED = process.env.REDIS_RATE_LIMIT_ENABLED === "true";
const REDIS_HOSTNAME = process.env.REDIS_HOSTNAME || "";
const REDIS_PORT = Number(process.env.REDIS_PORT || 6380);
const REDIS_SECRET_NAME = process.env.REDIS_SECRET_NAME || "redis-primary-key";
const KEY_VAULT_URI = process.env.KEY_VAULT_URI || "";
const TRUST_PROXY_HEADERS = process.env.TRUST_PROXY_HEADERS === "true";

const PORT = process.env.PORT || 8080;
// Limite do body POST /api/analyze-document (CWE-400 — DoS por payload grande).
// 200 KB cobre laudo médico típico (~10 páginas de texto puro anonimizado).
const MAX_ANALYSIS_BODY_BYTES = 200 * 1024;

// ── Redis-backed rate limiting (optional) ──
// Usado quando Redis + Key Vault estão configurados; caso contrário,
// mantém fallback em memória para não travar o boot local.
const redis = createRedisClient({
  enabled: REDIS_RATE_LIMIT_ENABLED,
  hostname: REDIS_HOSTNAME,
  port: REDIS_PORT,
  secretName: REDIS_SECRET_NAME,
  keyVaultUri: KEY_VAULT_URI,
});

// ── Privacy-Respecting Visitor Analytics (lib/analytics.js) ──
const analytics = createAnalytics();
const analyticsTrack = (ua, urlPath) => analytics.track(ua, urlPath);
const analyticsRotateIfNeeded = () => analytics.rotateIfNeeded();

// ── Rate Limiting (lib/rate-limit.js) ──
function sanitizeInfraErrorMessage(err) {
  return String((err && err.message) || "unknown error")
    .replace(/https?:\/\/\S+/gi, "[redacted-url]")
    .replace(/[A-Za-z0-9.-]+\.vault\.azure\.net/gi, "[redacted-keyvault]")
    .replace(/[A-Za-z0-9.-]+\.redis\.cache\.windows\.net/gi, "[redacted-redis-host]")
    .slice(0, 200);
}

const rateLimiter = createRateLimiter({
  redisConfigured: redis.configured,
  getRedisClient: redis.getClient,
  strategy: process.env.RATE_LIMIT_STRATEGY || "global",
  keySalt: process.env.RATE_LIMIT_KEY_SALT || "",
  onRedisError: (err) => {
    if (!redis.initError) redis.initError = err;
    console.warn(`Redis rate limiting unavailable, falling back to memory: ${sanitizeInfraErrorMessage(err)}`);
  },
});
const isRateLimitedAdaptive = (ip) => rateLimiter.check(ip);

// ── AI Analyze Handler (lib/ai-analyze.js) ──
const aiAnalyzeHandler = createAiAnalyzeHandler({
  aiEnabled: AI_ANALYSIS_ENABLED,
  maxBodyBytes: MAX_ANALYSIS_BODY_BYTES,
  securityHeaders: SECURITY_HEADERS,
  anonymize,
  containsPII,
  loadAnalyzer: () => require("./services/ai-analysis").analyzeText,
});

// ── Gov.br Proxy Handler (lib/govbr-proxy.js) ──
const govbrProxy = createGovBrProxy({ securityHeaders: SECURITY_HEADERS });

// MIME, CACHE, CSP/SECURITY_HEADERS, ALLOWED_EXT, COMPRESSIBLE, BLOCKED_DIRS,
// MAX_URL_LENGTH e resolveFile() foram extraídos para lib/* na Onda 7.
// ROOT é overridable via env (testes); produção sempre usa __dirname.
const ROOT = process.env.STATIC_ROOT
  ? path.resolve(process.env.STATIC_ROOT)
  : __dirname;
const MAX_URL_LENGTH = 2048;

// ── Scanner / vulnerability-probe paths (issue #251) ──
// Bots scan estes paths em busca de configs vazadas. Sempre retornamos 404,
// mas centralizar aqui evita poluir logs com stack traces de resolveFile().
const SCANNER_PATH_RE = /^\/(\.env|\.git|__env|application\.(yml|properties)|config\/secrets|firebase-config|wp-admin|wp-login|phpmyadmin|\.well-known\/(jwks\.json|openid-configuration)|server-status|actuator|\.aws|\.ssh)/i;

// Cache package.json version at startup (avoid readFileSync on every health check)
const PKG_VERSION = JSON.parse(fs.readFileSync(path.join(__dirname, "package.json"), "utf8")).version;

// ── Infra Handlers (lib/infra-handlers.js) ──
const healthHandler = createHealthHandler({
  aiEnabled: AI_ANALYSIS_ENABLED,
  pkgVersion: PKG_VERSION,
  loadAIHealth: () => require("./services/ai-analysis").getAIHealth(),
});
const statsHandler = createStatsHandler({
  analytics,
  rotateIfNeeded: analyticsRotateIfNeeded,
  securityHeaders: SECURITY_HEADERS,
});
const securityTxtHandler = createSecurityTxtHandler({
  canonicalHost: "nossodireito.fabiotreze.com",
  securityHeaders: SECURITY_HEADERS,
});

const server = http.createServer(async (req, res) => {
  // ── Suppress server identification (CWE-200) ──
  res.removeHeader("X-Powered-By");

  // ── Method allowlist ──
  // POST é aceito APENAS no endpoint /api/analyze-document (IA opt-in).
  // Todos os outros endpoints continuam restritos a GET/HEAD/OPTIONS.
  const isAnalyzeEndpoint = req.url === "/api/analyze-document" || req.url === "/api/analyze-document/";
  const isCspReport = req.url === "/csp-report";
  const allowedMethods = (isAnalyzeEndpoint || isCspReport) ? ["GET", "HEAD", "OPTIONS", "POST"] : ["GET", "HEAD", "OPTIONS"];
  if (!allowedMethods.includes(req.method)) {
    res.writeHead(405, {
      "Content-Type": "text/plain",
      Allow: allowedMethods.join(", "),
    });
    res.end("Method Not Allowed");
    return;
  }

  // ── Health check endpoint (lib/infra-handlers.js) ──
  // Bypasses rate-limit because Azure App Service probes /health frequently;
  // a 429 here would mark the app as unhealthy and trigger an unwanted swap.
  if (req.url === "/health") {
    healthHandler(req, res);
    return;
  }

  // ── Rate limiting (CWE-770) ──
  // Bucket global por janela, sem armazenar identificadores do request.
  // Applied BEFORE scanner paths, /api/stats and /csp-report so a bot flooding
  // those endpoints cannot bypass the limiter and exhaust resources.
  const forwarded = TRUST_PROXY_HEADERS
    ? (Array.isArray(req.headers["x-forwarded-for"])
      ? req.headers["x-forwarded-for"][0]
      : String(req.headers["x-forwarded-for"] || ""))
    : "";
  const proxyIp = TRUST_PROXY_HEADERS ? String(req.headers["cf-connecting-ip"] || "").trim() : "";
  const socketIp = String(req.socket.remoteAddress || "").trim();
  const clientIpRaw = String(proxyIp || forwarded.split(",")[0] || socketIp).trim();
  // Hash raw IP before passing to limiter, preserving privacy in downstream keys/logs.
  const clientKey = clientIpRaw
    ? crypto.createHash("sha256").update(clientIpRaw).digest("hex").slice(0, 24)
    : "";
  if (await isRateLimitedAdaptive(clientKey)) {
    res.writeHead(429, {
      "Content-Type": "text/plain",
      "Retry-After": "60",
    });
    res.end("Too Many Requests");
    return;
  }

  // ── Scanner / probe paths (issue #251) ──
  // Return 404 fast, no static-file lookup.
  if (SCANNER_PATH_RE.test(req.url)) {
    res.writeHead(404, { "Content-Type": "text/plain", ...SECURITY_HEADERS });
    res.end("Not Found");
    return;
  }

  // ── Privacy Analytics Stats Endpoint (lib/infra-handlers.js) ──
  if (req.url === "/api/stats" || req.url === "/api/stats/") {
    statsHandler(req, res);
    return;
  }

  // ── CSP Violation Reports (Reporting API + report-uri) ──
  // Accepts only the Content-Types defined by the spec:
  //  - application/csp-report          (CSP2 report-uri)
  //  - application/reports+json        (Reporting API v1)
  //  - application/json                (some browsers/proxies normalize to this)
  // Any other Content-Type is dropped with 415 so attackers cannot pipe
  // arbitrary payloads into the [CSP-VIOLATION] log stream.
  if (req.url === "/csp-report" && req.method === "POST") {
    const ct = String(req.headers["content-type"] || "").toLowerCase().split(";")[0].trim();
    const ALLOWED_CSP_CT = new Set([
      "application/csp-report",
      "application/reports+json",
      "application/json",
    ]);
    if (!ALLOWED_CSP_CT.has(ct)) {
      res.writeHead(415, { "Content-Type": "text/plain" });
      res.end("Unsupported Media Type");
      return;
    }
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
      if (body.length > 8192) { req.destroy(); return; }
    });
    req.on("end", () => {
      try {
        const report = JSON.parse(body);
        const violation = report["csp-report"] || report.body || report;
        console.warn("[CSP-VIOLATION]", JSON.stringify({
          blockedUri: violation["blocked-uri"] || violation.blockedURL || "",
          directive: violation["violated-directive"] || violation.effectiveDirective || "",
          documentUri: violation["document-uri"] || violation.documentURL || "",
        }));
      } catch { /* ignore malformed reports */ }
      res.writeHead(204);
      res.end();
    });
    return;
  }

  // ── URL validation ──
  if (req.url.length > MAX_URL_LENGTH) {
    res.writeHead(414, { "Content-Type": "text/plain" });
    res.end("URI Too Long");
    return;
  }

  // ── Host header validation (CWE-644) ──
  const host = req.headers.host || "";
  const CANONICAL_HOST = "nossodireito.fabiotreze.com";
  // WEBSITE_HOSTNAME é injetado automaticamente pelo Azure App Service
  // (ex: "app-nossodireito-br.azurewebsites.net") — zero hardcoding.
  const AZURE_HOSTNAME = process.env.WEBSITE_HOSTNAME || "";
  const ALLOWED_HOSTS = [
    CANONICAL_HOST,
    ...(AZURE_HOSTNAME ? [AZURE_HOSTNAME] : []), // Azure default domain (dinâmico)
    `localhost:${PORT}`,
    `127.0.0.1:${PORT}`,
  ];

  // ── CORS (Safari SW compat + govbr API proxy) ──
  // Safari enforces strict access-control checks on same-origin fetch
  // when routed through Service Worker. Explicit CORS headers resolve it.
  const origin = req.headers.origin || "";
  const ALLOWED_ORIGINS = [
    `https://${CANONICAL_HOST}`,
    ...(AZURE_HOSTNAME ? [`https://${AZURE_HOSTNAME}`] : []), // Azure (dinâmico)
    `http://localhost:${PORT}`,
    `http://127.0.0.1:${PORT}`,
  ];
  let corsOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : "";
  // Safari Service Worker compat: Safari enforces CORS checks on
  // same-origin fetches routed through SW, yet may omit the Origin header.
  // When no Origin is present and Host is a known host, infer same-origin.
  if (!corsOrigin && !origin && host) {
    const scheme = host.startsWith("localhost") || host.startsWith("127.") ? "http" : "https";
    const inferred = `${scheme}://${host}`;
    if (ALLOWED_ORIGINS.includes(inferred)) corsOrigin = inferred;
  }

  // Handle CORS preflight (OPTIONS)
  if (req.method === "OPTIONS") {
    // POST liberado apenas em /api/analyze-document (IA opt-in).
    const allowMethods = isAnalyzeEndpoint ? "GET, HEAD, OPTIONS, POST" : "GET, HEAD, OPTIONS";
    const preflightHeaders = {
      "Access-Control-Allow-Methods": allowMethods,
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Max-Age": "86400",
      ...SECURITY_HEADERS,
    };
    if (corsOrigin) preflightHeaders["Access-Control-Allow-Origin"] = corsOrigin;
    res.writeHead(204, preflightHeaders);
    res.end();
    return;
  }

  // Redirect default Azure domain → canonical custom domain (SEO + security)
  // Only redirect browser requests (with Accept: text/html), not health probes
  //
  // Security: req.url é controlado pelo cliente. Para evitar open-redirect
  // (CodeQL js/server-side-unvalidated-url-redirection) reconstruímos a URL
  // alvo a partir apenas de pathname + search, descartando qualquer authority
  // (//evil.com/...) ou caracteres de controle (CRLF) injetados.
  if (AZURE_HOSTNAME && host === AZURE_HOSTNAME && req.headers.accept?.includes("text/html")) {
    let safePath;
    try {
      const parsed = new URL(req.url, `https://${CANONICAL_HOST}`);
      safePath = parsed.pathname + parsed.search;
    } catch {
      safePath = "/";
    }
    const location = `https://${CANONICAL_HOST}${safePath}`;
    res.writeHead(301, {
      Location: location,
      "Cache-Control": "public, max-age=86400",
      ...SECURITY_HEADERS,
    });
    res.end();
    return;
  }

  // Strict host validation — exact match only (no subdomains)
  // Prevents attacks like malicious.nossodireito.fabiotreze.com
  if (host && !ALLOWED_HOSTS.includes(host)) {
    res.writeHead(421, { "Content-Type": "text/plain" });
    res.end("Misdirected Request");
    return;
  }

  // ── Parse urlPath BEFORE proxy (defensive architecture) ──
  let urlPath;
  try {
    urlPath = new URL(req.url, `http://${host || "localhost"}`).pathname;
  } catch {
    res.writeHead(400, { "Content-Type": "text/plain" });
    res.end("Bad Request");
    return;
  }

  // ── IA opt-in: Análise de documento via Azure OpenAI ──
  // Lógica completa em lib/ai-analyze.js (Onda 7c).
  if (isAnalyzeEndpoint && req.method === "POST") {
    aiAnalyzeHandler(req, res, corsOrigin);
    return;
  }

  // ── Gov.br API proxy (lib/govbr-proxy.js) ──
  const govbrMatch = req.url.match(/^\/api\/govbr-servico\/(\d+)$/);
  if (govbrMatch) {
    govbrProxy.handle(req, res, govbrMatch[1], corsOrigin);
    return;
  }

  // ── /.well-known/security.txt (lib/infra-handlers.js) ──
  if (urlPath === "/.well-known/security.txt") {
    securityTxtHandler(req, res);
    return;
  }

  const fullPath = await resolveFile(urlPath, ROOT);

  if (!fullPath) {
    res.writeHead(404, {
      "Content-Type": "text/plain",
      ...SECURITY_HEADERS,
    });
    res.end("Not Found");
    return;
  }

  // ── Track page view (privacy-preserving) ──
  // Only track HTML page loads (not static assets like CSS/JS/images)
  const reqExt = path.extname(fullPath).toLowerCase();
  if (reqExt === ".html" || reqExt === "") {
    analyticsTrack(req.headers["user-agent"] || "", urlPath);
  }

  const ext = path.extname(fullPath).toLowerCase();
  const contentType = MIME[ext] || "application/octet-stream";
  // Service Worker must have short cache for update detection (browser spec)
  const isSW = urlPath === "/sw.js";
  const cacheControl = isSW ? "no-cache" : CACHE[ext] || "no-cache";

  // Build response headers
  const headers = {
    "Content-Type": contentType,
    "Cache-Control": cacheControl,
    ...SECURITY_HEADERS,
  };

  // CORS header for same-origin (Safari SW compat)
  if (corsOrigin) headers["Access-Control-Allow-Origin"] = corsOrigin;

  // HTML-specific headers (no Link preload — resources are discovered
  // directly from HTML; preload hints cause Chrome "unused preload" warnings
  // because styles.css uses media=print defer and app.js uses defer)
  if (ext === ".html") {
    headers["Content-Language"] = "pt-BR";
    headers["X-Robots-Tag"] = "index, follow";
  } else if (ext === ".json") {
    headers["X-Robots-Tag"] = "noindex";
  }

  // Compression for text-based content (Brotli > Gzip > None)
  //
  // Strategy (perf fix — 2026-05-30 SEV2 incident):
  //  1. Prefer pre-compressed siblings (.br / .gz) — zero CPU at request time.
  //     Generated at build time by scripts/precompress_static.mjs.
  //  2. Fallback to on-the-fly compression with Brotli quality 4 (fast).
  //     Default quality 11 took 5–10s of CPU per 400KB JSON, blocking the
  //     single worker and causing 26s tail latency.
  const acceptEncoding = req.headers["accept-encoding"] || "";
  const acceptsBr = acceptEncoding.includes("br");
  const acceptsGzip = acceptEncoding.includes("gzip");
  const canCompress = COMPRESSIBLE.has(ext);

  // Try pre-compressed siblings first (fastest path).
  // Auto-heal: ignore stale siblings whose mtime is older than the source file
  // (avoids serving outdated content when scripts/precompress_static.mjs was
  // not re-run after editing the source — falls back to on-the-fly Brotli q4).
  let precompressedPath = null;
  let precompressedEncoding = null;
  let precompressedSize = 0;
  if (canCompress) {
    let sourceMtimeMs = 0;
    try {
      sourceMtimeMs = (await fsPromises.stat(fullPath)).mtimeMs;
    } catch {
      /* source missing — let later code handle */
    }
    const tryCandidate = async (ext) => {
      const candidate = `${fullPath}.${ext}`;
      try {
        const st = await fsPromises.stat(candidate);
        if (st.isFile() && st.mtimeMs >= sourceMtimeMs) {
          precompressedSize = st.size;
          return candidate;
        }
      } catch {
        /* sibling missing — fall through */
      }
      return null;
    };
    if (acceptsBr) {
      const found = await tryCandidate("br");
      if (found) {
        precompressedPath = found;
        precompressedEncoding = "br";
      }
    }
    if (!precompressedPath && acceptsGzip) {
      const found = await tryCandidate("gz");
      if (found) {
        precompressedPath = found;
        precompressedEncoding = "gzip";
      }
    }
  }

  const useBrotli = !precompressedPath && canCompress && acceptsBr;
  const useGzip = !precompressedPath && !useBrotli && canCompress && acceptsGzip;

  if (precompressedEncoding) {
    headers["Content-Encoding"] = precompressedEncoding;
    headers["Vary"] = "Accept-Encoding";
    if (precompressedSize > 0) {
      headers["Content-Length"] = String(precompressedSize);
    }
  } else if (useBrotli) {
    headers["Content-Encoding"] = "br";
    headers["Vary"] = "Accept-Encoding";
  } else if (useGzip) {
    headers["Content-Encoding"] = "gzip";
    headers["Vary"] = "Accept-Encoding";
  }

  res.writeHead(200, headers);

  if (req.method === "HEAD") {
    res.end();
    return;
  }

  const stream = fs.createReadStream(precompressedPath || fullPath);
  if (precompressedPath) {
    // Pre-compressed: pipe raw bytes, no transform.
    stream.pipe(res);
  } else if (useBrotli) {
    const compressor = zlib.createBrotliCompress({
      params: {
        // Quality 4 = ~50× faster than default (11) with ~5% bigger output.
        // Acceptable trade-off: a 400KB JSON compresses in ~50ms instead of 5s.
        [zlib.constants.BROTLI_PARAM_QUALITY]: 4,
      },
    });
    compressor.on("error", () => {
      if (!res.writableEnded) res.end();
    });
    stream.pipe(compressor).pipe(res);
  } else if (useGzip) {
    const compressor = zlib.createGzip({ level: 6 });
    compressor.on("error", () => {
      if (!res.writableEnded) res.end();
    });
    stream.pipe(compressor).pipe(res);
  } else {
    stream.pipe(res);
  }

  stream.on("error", () => {
    if (!res.headersSent) {
      res.writeHead(500, { "Content-Type": "text/plain" });
    }
    if (!res.writableEnded) res.end("Internal Server Error");
  });
});

// ── Connection hardening ──
server.timeout = 30_000; // 30s request timeout (anti-Slowloris)
server.headersTimeout = 70_000; // 70s header timeout (must exceed keepAliveTimeout)
server.requestTimeout = 30_000; // 30s total request timeout
server.keepAliveTimeout = 65_000; // 65s keep-alive (must exceed Azure LB timeout)
server.maxHeadersCount = 50; // Limit header count
server.maxRequestsPerSocket = 100; // Limit requests per keep-alive socket

// ── Graceful shutdown ──
function gracefulShutdown(signal) {
  console.log(`\n${signal} received — closing server gracefully...`);
  server.close(async () => {
    await redis.quit();
    console.log("Server closed.");
    process.exit(0);
  });
  // Force exit if close hangs after 5s
  setTimeout(() => process.exit(1), 5000).unref();
}
process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
process.on("SIGINT", () => gracefulShutdown("SIGINT"));
// Windows: SIGBREAK is sent on Ctrl+Break and by Azure App Service for Windows
if (process.platform === "win32") {
  process.on("SIGBREAK", () => gracefulShutdown("SIGBREAK"));
}

server.listen(PORT, () => {
  console.log(`NossoDireito server running on port ${PORT}`);
});
