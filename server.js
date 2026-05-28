/**
 * NossoDireito — Static File Server (Hardened)
 * Serve static files with defense-in-depth security.
 * Azure App Service (Node.js 22 LTS)
 *
 * Security posture: EASM-hardened (Defender EASM / Qualys / Shodan-proof)
 * Integrates with Azure Application Insights for telemetry.
 */

"use strict";

const http = require("node:http");
const fs = require("node:fs");
const fsPromises = require("node:fs/promises");
const path = require("node:path");
const zlib = require("node:zlib");
const crypto = require("node:crypto");

// ── Lib modules (Onda 7 — modularização) ──
const { MIME, CACHE, ALLOWED_EXT, COMPRESSIBLE } = require("./lib/mime");
const { SECURITY_HEADERS } = require("./lib/security-headers");
const { resolveFile } = require("./lib/file-resolver");
const { createAnalytics } = require("./lib/analytics");
const { createRateLimiter } = require("./lib/rate-limit");
const { createRedisClient } = require("./lib/redis-client");
void ALLOWED_EXT;

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

const PORT = process.env.PORT || 8080;
// Limite do body POST /api/analyze-document (CWE-400 — DoS por payload grande).
// 200 KB cobre laudo médico típico (~10 páginas de texto puro anonimizado).
const MAX_ANALYSIS_BODY_BYTES = 200 * 1024;

// ── Application Insights (server-side telemetry) ──
// Connection string is injected by Terraform via app_settings.
// If not present (local dev), telemetry is silently skipped.
let appInsights = null;
const AI_CONN = process.env.APPLICATIONINSIGHTS_CONNECTION_STRING || "";
if (AI_CONN) {
  try {
    appInsights = require("applicationinsights");
    appInsights
      .setup(AI_CONN)
      .setAutoCollectRequests(true)
      .setAutoCollectPerformance(true, true)
      .setAutoCollectExceptions(true)
      .setAutoCollectDependencies(false)
      .setAutoCollectConsole(false)
      .setDistributedTracingMode(appInsights.DistributedTracingModes.AI_AND_W3C)
      .setSendLiveMetrics(true)
      .start();

    // ── LGPD: Zero IP Collection telemetry processor ──
    // Strips IP, User-Agent, Referer, and query strings before ingestion.
    // See SECURITY.md ("Telemetria anônima") and docs/COMPLIANCE.md §3.
    appInsights.defaultClient.addTelemetryProcessor((envelope) => {
      if (envelope.tags) {
        envelope.tags["ai.location.ip"] = "0.0.0.0";
        delete envelope.tags["ai.user.id"];
        delete envelope.tags["ai.user.authUserId"];
        delete envelope.tags["ai.session.id"];
      }
      const baseData = envelope.data && envelope.data.baseData;
      if (baseData) {
        if (typeof baseData.url === "string") {
          baseData.url = baseData.url.split("?")[0];
        }
        if (baseData.properties) {
          delete baseData.properties["User-Agent"];
          delete baseData.properties["Referer"];
          delete baseData.properties["X-Forwarded-For"];
          delete baseData.properties["client-ip"];
        }
      }
      return true;
    });

    // Periodic flush — minimize data loss on App Service restart.
    setInterval(() => {
      if (appInsights.defaultClient) appInsights.defaultClient.flush();
    }, 3600_000).unref(); // 1h, .unref() to not block graceful shutdown

    console.log("✅ Application Insights initialized (LGPD: zero IP collection)");
  } catch (err) {
    console.log("ℹ️ applicationinsights package not available — telemetry disabled");
    appInsights = null;
  }
}

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
const analytics = createAnalytics({
  getAppInsightsClient: () => (appInsights ? appInsights.defaultClient : null),
});
const analyticsTrack = (ip, ua, urlPath) => analytics.track(ip, ua, urlPath);
const analyticsRotateIfNeeded = () => analytics.rotateIfNeeded();

// ── Rate Limiting (lib/rate-limit.js) ──
const rateLimiter = createRateLimiter({
  redisConfigured: redis.configured,
  getRedisClient: redis.getClient,
  onRedisError: (err) => {
    if (!redis.initError) redis.initError = err;
    console.warn(`Redis rate limiting unavailable, falling back to memory: ${err.message}`);
  },
});
const isRateLimitedAdaptive = (ip) => rateLimiter.check(ip);

// MIME, CACHE, CSP/SECURITY_HEADERS, ALLOWED_EXT, COMPRESSIBLE, BLOCKED_DIRS,
// MAX_URL_LENGTH e resolveFile() foram extraídos para lib/* na Onda 7.
const ROOT = __dirname;
const MAX_URL_LENGTH = 2048;

// Cache package.json version at startup (avoid readFileSync on every health check)
const PKG_VERSION = JSON.parse(fs.readFileSync(path.join(__dirname, "package.json"), "utf8")).version;

const server = http.createServer(async (req, res) => {
  // ── Suppress server identification (CWE-200) ──
  res.removeHeader("X-Powered-By");

  // ── Method allowlist ──
  // POST é aceito APENAS no endpoint /api/analyze-document (IA opt-in).
  // Todos os outros endpoints continuam restritos a GET/HEAD/OPTIONS.
  const isAnalyzeEndpoint = req.url === "/api/analyze-document" || req.url === "/api/analyze-document/";
  const allowedMethods = isAnalyzeEndpoint ? ["GET", "HEAD", "OPTIONS", "POST"] : ["GET", "HEAD", "OPTIONS"];
  if (!allowedMethods.includes(req.method)) {
    res.writeHead(405, {
      "Content-Type": "text/plain",
      Allow: allowedMethods.join(", "),
    });
    res.end("Method Not Allowed");
    return;
  }

  // ── Health check endpoint (Azure App Service probe) ──
  // Must respond 200 on ALL hosts (including *.azurewebsites.net)
  // before the domain redirect, otherwise probe marks app unhealthy.
  if (req.url === "/healthz" || req.url === "/health") {
    let ai = {
      enabled: AI_ANALYSIS_ENABLED,
      configured: false,
      circuitOpen: false,
      retryAfterSeconds: 0,
    };
    try {
      const { getAIHealth } = require("./services/ai-analysis");
      ai = getAIHealth();
    } catch {
      // Service optional for health endpoint; do not fail health probe.
    }
    res.writeHead(200, {
      "Content-Type": "application/json",
      "Cache-Control": "no-cache, no-store",
    });
    res.end(
      JSON.stringify({
        status: "healthy",
        version: PKG_VERSION,
        localAnalysisAvailable: true,
        ai,
      }),
    );
    return;
  }

  // ── Privacy Analytics Stats Endpoint ──
  // Returns aggregated, anonymous visitor statistics.
  // No PII is ever exposed. Protected by optional STATS_KEY env var.
  if (req.url === "/api/stats" || req.url === "/api/stats/") {
    // Optional auth: if STATS_KEY is set, require ?key= parameter
    const statsKey = process.env.STATS_KEY || "";
    if (statsKey) {
      let requestKey = "";
      try {
        requestKey = new URL(req.url, `http://${req.headers.host || "localhost"}`).searchParams.get("key") || "";
      } catch {
        /* ignore */
      }
      if (requestKey !== statsKey) {
        res.writeHead(403, { "Content-Type": "text/plain", ...SECURITY_HEADERS });
        res.end("Forbidden");
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
      privacy: "Nenhum dado pessoal é coletado. IPs são anonimizados via SHA-256 com salt rotativo diário.",
    };
    res.writeHead(200, {
      "Content-Type": "application/json",
      "Cache-Control": "no-cache, no-store",
      ...SECURITY_HEADERS,
    });
    res.end(JSON.stringify(stats, null, 2));
    return;
  }

  // ── Rate limiting (CWE-770) ──
  // Use X-Forwarded-For only when behind a trusted reverse proxy (Azure App Service).
  // In local dev / direct exposure, fall back to socket address to prevent spoofing.
  const TRUST_PROXY = process.env.TRUST_PROXY === "1" || process.env.WEBSITE_SITE_NAME; // Azure injects WEBSITE_SITE_NAME
  const clientIp = TRUST_PROXY
    ? req.headers["x-forwarded-for"]?.split(",")[0]?.trim() || req.socket.remoteAddress || ""
    : req.socket.remoteAddress || "";
  if (await isRateLimitedAdaptive(clientIp)) {
    res.writeHead(429, {
      "Content-Type": "text/plain",
      "Retry-After": "60",
    });
    res.end("Too Many Requests");
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
  // Fluxo:
  //  1. Cliente anonimiza no browser (shared/anonymizer.js)
  //  2. POST { text: "..." } com Content-Type: application/json
  //  3. Server re-anonimiza e VALIDA que não há PII residual
  //  4. Chama Doc Intelligence (MSI, brazilsouth)
  //  5. Retorna estrutura { cids, dates, paragraphs } — zero conteúdo bruto logado
  if (isAnalyzeEndpoint && req.method === "POST") {
    if (!AI_ANALYSIS_ENABLED) {
      res.writeHead(503, { "Content-Type": "application/json", ...SECURITY_HEADERS });
      res.end(
        JSON.stringify({
          error: "AI analysis disabled",
          localAnalysisFallback: true,
        }),
      );
      return;
    }
    if ((req.headers["content-type"] || "").split(";")[0].trim() !== "application/json") {
      res.writeHead(415, { "Content-Type": "application/json", ...SECURITY_HEADERS });
      res.end(JSON.stringify({ error: "Content-Type must be application/json" }));
      return;
    }
    // Coleta body com limite estrito (CWE-400).
    const chunks = [];
    let received = 0;
    let aborted = false;
    req.on("data", (chunk) => {
      received += chunk.length;
      if (received > MAX_ANALYSIS_BODY_BYTES) {
        aborted = true;
        res.writeHead(413, { "Content-Type": "application/json", ...SECURITY_HEADERS });
        res.end(JSON.stringify({ error: "Payload too large", maxBytes: MAX_ANALYSIS_BODY_BYTES }));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", async () => {
      if (aborted) return;
      let payload;
      try {
        payload = JSON.parse(Buffer.concat(chunks).toString("utf8"));
      } catch {
        res.writeHead(400, { "Content-Type": "application/json", ...SECURITY_HEADERS });
        res.end(JSON.stringify({ error: "Invalid JSON" }));
        return;
      }
      const rawText = typeof payload.text === "string" ? payload.text : "";
      if (!rawText || rawText.length < 10) {
        res.writeHead(400, { "Content-Type": "application/json", ...SECURITY_HEADERS });
        res.end(JSON.stringify({ error: "Field 'text' is required (min 10 chars)" }));
        return;
      }
      // Double-check: roda anonimizador no server mesmo se cliente já fez.
      // Defense in depth — cliente pode ter sido modificado/burlado.
      const { text: cleanText, stats: anonStats } = anonymize(rawText);
      const check = containsPII(cleanText);
      if (!check.clean) {
        // Recusa explícita — não enviamos PII para serviço de IA, NUNCA.
        if (appInsights && appInsights.defaultClient) {
          appInsights.defaultClient.trackEvent({
            name: "AI.Analysis.Rejected.PII",
            properties: { reasons: check.found.join(",") },
          });
        }
        res.writeHead(422, { "Content-Type": "application/json", ...SECURITY_HEADERS });
        res.end(
          JSON.stringify({
            error: "Text contains residual PII after anonymization",
            found: check.found,
            hint: "Run shared/anonymizer.js on the client BEFORE POSTing",
          }),
        );
        return;
      }
      try {
        const { analyzeText } = require("./services/ai-analysis");
        const result = await analyzeText(cleanText);
        // LGPD: anexa metadados de transparência ao payload (Art. 6º V + Art. 9º)
        result.lgpd = {
          retention_seconds: 0,
          legal_basis: "LGPD Art. 7º I (consentimento)",
          anonymized_client_side: true,
          anonymized_server_side: true,
          data_residency: "brazil-south",
          ai_provider: "azure-openai",
          ai_model: result.model || "gpt-4o-mini",
        };
        if (appInsights && appInsights.defaultClient) {
          appInsights.defaultClient.trackEvent({
            name: "AI.Analysis.Success",
            properties: {
              contentHash: result.contentHash,
              cidsFound: String((result.cids || []).length),
              direitosSugeridos: String((result.direitos_sugeridos || []).length),
              durationMs: String(result.durationMs),
              tokensInput: String(result.tokens ? result.tokens.input : 0),
              tokensOutput: String(result.tokens ? result.tokens.output : 0),
              confianca: String(result.confianca || "baixa"),
              anonPatterns: Object.keys(anonStats).join(","),
            },
          });
        }
        const okHeaders = {
          "Content-Type": "application/json",
          "Cache-Control": "no-store",
          "X-Data-Retention": "0",
          "X-LGPD-Legal-Basis": "Art-7-I-Consentimento",
          "X-AI-Provider": "azure-openai",
          ...SECURITY_HEADERS,
        };
        if (corsOrigin) okHeaders["Access-Control-Allow-Origin"] = corsOrigin;
        res.writeHead(200, okHeaders);
        res.end(JSON.stringify(result));
      } catch (err) {
        const errMsg = String(err && err.message).slice(0, 500);
        const errCode = String((err && err.code) || "");
        const retryAfter = Number((err && err.retryAfter) || 0);
        if (appInsights && appInsights.defaultClient) {
          appInsights.defaultClient.trackEvent({
            name: "AI.Analysis.Error",
            properties: {
              message: errMsg,
              code: errCode,
              status: String((err && err.status) || ""),
            },
          });
        }
        const status = errCode === "CIRCUIT_OPEN" || errCode === "ETIMEDOUT" ? 503 : 502;
        const errorHeaders = {
          "Content-Type": "application/json",
          ...SECURITY_HEADERS,
        };
        if (retryAfter > 0) errorHeaders["Retry-After"] = String(retryAfter);
        res.writeHead(status, errorHeaders);
        res.end(
          JSON.stringify({
            error: "AI service unavailable",
            localAnalysisFallback: true,
            retryAfterSeconds: retryAfter || undefined,
          }),
        );
      }
    });
    req.on("error", () => {
      if (!res.headersSent) {
        res.writeHead(400, { "Content-Type": "application/json", ...SECURITY_HEADERS });
        res.end(JSON.stringify({ error: "Bad Request" }));
      }
    });
    return;
  }

  // ── Gov.br API proxy (CORS bypass for servicos.gov.br) ──
  // Proxy gov.br sem await (não dá SyntaxError nunca)
  //
  // Security: a URL do upstream é construída a partir de input do cliente.
  // Para mitigar SSRF (CodeQL js/request-forgery) garantimos que servicoId
  // é estritamente numérico (regex \d+), com comprimento máximo, e fazemos
  // um cast explícito para Number → toString antes de interpolar, removendo
  // qualquer dúvida de fluxo taint para o fetch downstream.
  const govbrMatch = req.url.match(/^\/api\/govbr-servico\/(\d+)$/);
  if (govbrMatch) {
    const servicoIdRaw = govbrMatch[1];
    // Limit servicoId length to prevent abuse (valid gov.br IDs are < 10 digits)
    if (servicoIdRaw.length > 10) {
      res.writeHead(400, { "Content-Type": "text/plain" });
      res.end("Bad Request");
      return;
    }
    // Cast numérico defensivo: garante que apenas dígitos chegam ao upstream
    const servicoIdNum = Number.parseInt(servicoIdRaw, 10);
    if (!Number.isSafeInteger(servicoIdNum) || servicoIdNum < 0) {
      res.writeHead(400, { "Content-Type": "text/plain" });
      res.end("Bad Request");
      return;
    }
    const servicoId = String(servicoIdNum);
    const govbrUrl = `https://servicos.gov.br/api/v1/servicos/${servicoId}`;

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000); // 5s timeout

    fetch(govbrUrl, {
      signal: controller.signal,
      headers: { "User-Agent": "NossoDireito-Proxy/1.0" },
    })
      .then((r) => {
        // Limit response body size (1 MB) to prevent memory abuse
        const contentLength = parseInt(r.headers.get("content-length") || "0", 10);
        if (contentLength > 1_048_576) {
          throw new Error("Response too large");
        }
        return r.text().then((body) => ({ r, body }));
      })
      .then(({ r, body }) => {
        clearTimeout(timeout);
        if (res.destroyed) return; // client disconnected
        const status = r.status;
        const cacheControl = r.ok ? "public, max-age=3600" : "no-cache";
        const proxyHeaders = {
          "Content-Type": "application/json",
          "Cache-Control": cacheControl,
          ...SECURITY_HEADERS,
        };
        if (corsOrigin) proxyHeaders["Access-Control-Allow-Origin"] = corsOrigin;
        res.writeHead(status, proxyHeaders);
        if (req.method === "HEAD") {
          res.end();
          return;
        }
        if (r.ok) {
          res.end(body);
        } else {
          res.end(JSON.stringify({ error: "Gov.br API unavailable" }));
        }
      })
      .catch(() => {
        clearTimeout(timeout);
        if (res.destroyed) return; // client already disconnected
        if (!res.headersSent) {
          res.writeHead(503, {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
          });
        }
        if (!res.writableEnded) res.end(JSON.stringify({ error: "Service unavailable" }));
      });
    return;
  }

  // ── /.well-known/security.txt (RFC 9116) ──
  // resolveFile rejeita paths começando com "." por segurança, então
  // servimos via rota explícita.
  if (urlPath === "/.well-known/security.txt") {
    const expires = new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString();
    const txt = `# NossoDireito — Security Policy
# RFC 9116: https://www.rfc-editor.org/rfc/rfc9116

Contact: mailto:dpo@fabiotreze.com
Contact: mailto:38567767+fabiotreze@users.noreply.github.com
Expires: ${expires}
Preferred-Languages: pt-BR, en
Canonical: https://${CANONICAL_HOST}/.well-known/security.txt
Policy: https://github.com/fabiotreze/nossodireito/security/policy
Acknowledgments: https://github.com/fabiotreze/nossodireito/security/advisories
`;
    res.writeHead(200, {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=86400",
      ...SECURITY_HEADERS,
    });
    res.end(req.method === "HEAD" ? "" : txt);
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
    analyticsTrack(clientIp, req.headers["user-agent"] || "", urlPath);
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
  const acceptEncoding = req.headers["accept-encoding"] || "";
  const useBrotli = COMPRESSIBLE.has(ext) && acceptEncoding.includes("br");
  const useGzip = !useBrotli && COMPRESSIBLE.has(ext) && acceptEncoding.includes("gzip");

  if (useBrotli) {
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

  const stream = fs.createReadStream(fullPath);
  if (useBrotli) {
    const compressor = zlib.createBrotliCompress();
    compressor.on("error", () => {
      if (!res.writableEnded) res.end();
    });
    stream.pipe(compressor).pipe(res);
  } else if (useGzip) {
    const compressor = zlib.createGzip();
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
