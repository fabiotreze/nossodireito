"use strict";

/**
 * Proxy gov.br (CORS bypass para servicos.gov.br).
 *
 * Extraído de server.js (Onda 7d) sem mudança de comportamento.
 *
 * Segurança: a URL do upstream é construída a partir de input do cliente.
 * Para mitigar SSRF (CodeQL js/request-forgery), garantimos que servicoId
 * é estritamente numérico (regex \d+), com comprimento máximo, e fazemos
 * cast explícito para Number → toString antes de interpolar.
 *
 * Uso:
 *   const govbr = createGovBrProxy({ securityHeaders });
 *   const match = req.url.match(/^\/api\/govbr-servico\/(\d+)$/);
 *   if (match) govbr.handle(req, res, match[1], corsOrigin);
 */
function createGovBrProxy({ securityHeaders, timeoutMs = 5000, maxBodyBytes = 1_048_576 }) {
  function handle(req, res, servicoIdRaw, corsOrigin) {
    // Limit servicoId length (valid gov.br IDs are < 10 digits)
    if (servicoIdRaw.length > 10) {
      res.writeHead(400, { "Content-Type": "text/plain" });
      res.end("Bad Request");
      return;
    }
    const servicoIdNum = Number.parseInt(servicoIdRaw, 10);
    if (!Number.isSafeInteger(servicoIdNum) || servicoIdNum < 0) {
      res.writeHead(400, { "Content-Type": "text/plain" });
      res.end("Bad Request");
      return;
    }
    const servicoId = String(servicoIdNum);
    const govbrUrl = `https://servicos.gov.br/api/v1/servicos/${servicoId}`;

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);

    fetch(govbrUrl, {
      signal: controller.signal,
      headers: { "User-Agent": "NossoDireito-Proxy/1.0" },
    })
      .then((r) => {
        const contentLength = parseInt(r.headers.get("content-length") || "0", 10);
        if (contentLength > maxBodyBytes) {
          throw new Error("Response too large");
        }
        return r.text().then((body) => ({ r, body }));
      })
      .then(({ r, body }) => {
        clearTimeout(timeout);
        if (res.destroyed) return;
        const status = r.status;
        const cacheControl = r.ok ? "public, max-age=3600" : "no-cache";
        const proxyHeaders = {
          "Content-Type": "application/json",
          "Cache-Control": cacheControl,
          ...securityHeaders,
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
        if (res.destroyed) return;
        if (!res.headersSent) {
          res.writeHead(503, {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
          });
        }
        if (!res.writableEnded) res.end(JSON.stringify({ error: "Service unavailable" }));
      });
  }

  return { handle };
}

module.exports = { createGovBrProxy };
