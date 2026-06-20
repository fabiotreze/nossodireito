"use strict";

/**
 * Handlers de endpoints "infra": health probe, stats analytics e security.txt.
 *
 * Extraído de server.js (Onda 7e) sem mudança de comportamento.
 */

function createHealthHandler({ aiEnabled, pkgVersion, loadAIHealth }) {
  return function handle(req, res) {
    void req;
    let ai = {
      enabled: aiEnabled,
      configured: false,
      circuitOpen: false,
      retryAfterSeconds: 0,
    };
    try {
      ai = loadAIHealth();
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
        version: pkgVersion,
        localAnalysisAvailable: true,
        ai,
      }),
    );
  };
}

function createStatsHandler({ analytics, rotateIfNeeded, securityHeaders, statsKeyEnv = "STATS_KEY" }) {
  return function handle(req, res) {
    const statsKey = process.env[statsKeyEnv] || "";
    if (statsKey) {
      let requestKey = "";
      try {
        requestKey =
          new URL(req.url, `http://${req.headers.host || "localhost"}`).searchParams.get("key") || "";
      } catch {
        /* ignore */
      }
      if (requestKey !== statsKey) {
        res.writeHead(403, { "Content-Type": "text/plain", ...securityHeaders });
        res.end("Forbidden");
        return;
      }
    }
    rotateIfNeeded();
    const snapshot = analytics.snapshot();
    const stats = {
      date: snapshot.date,
      today: {
        pageViews: snapshot.pageViews,
        uniqueVisitors: snapshot.uniqueVisitors,
        devices: { ...snapshot.byDevice },
        topPages: snapshot.byPath.slice(0, 10),
        hourly: [...snapshot.hourly],
      },
      history: snapshot.history,
      privacy:
        "O painel expõe apenas contadores agregados sem IP, sessão ou identificador por visitante. Logs técnicos de acesso seguem a Política de Privacidade.",
    };
    res.writeHead(200, {
      "Content-Type": "application/json",
      "Cache-Control": "no-cache, no-store",
      ...securityHeaders,
    });
    res.end(JSON.stringify(stats, null, 2));
  };
}

function createSecurityTxtHandler({ canonicalHost, securityHeaders, ttlYears = 1 }) {
  return function handle(req, res) {
    const expires = new Date(Date.now() + ttlYears * 365 * 24 * 60 * 60 * 1000).toISOString();
    const txt = `# NossoDireito — Security Policy
# RFC 9116: https://www.rfc-editor.org/rfc/rfc9116

Contact: mailto:dpo@fabiotreze.com
Contact: mailto:38567767+fabiotreze@users.noreply.github.com
Expires: ${expires}
Preferred-Languages: pt-BR, en
Canonical: https://${canonicalHost}/.well-known/security.txt
Policy: https://github.com/fabiotreze/nossodireito/security/policy
Acknowledgments: https://github.com/fabiotreze/nossodireito/security/advisories
`;
    res.writeHead(200, {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=86400",
      ...securityHeaders,
    });
    res.end(req.method === "HEAD" ? "" : txt);
  };
}

module.exports = { createHealthHandler, createStatsHandler, createSecurityTxtHandler };
