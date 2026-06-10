"use strict";

/**
 * Handler de IA opt-in para POST /api/analyze-document.
 *
 * Extraído de server.js (Onda 7c) sem mudança de comportamento.
 *
 * Fluxo:
 *  1. Cliente anonimiza no browser (shared/anonymizer.js)
 *  2. POST { text: "..." } com Content-Type: application/json
 *  3. Server re-anonimiza e VALIDA que não há PII residual (defense in depth)
 *  4. Chama services/ai-analysis (Azure OpenAI, brazilsouth, MSI)
 *  5. Retorna estrutura { cids, dates, paragraphs, ... } sem conteúdo bruto
 *
 * Uso:
 *   const handle = createAiAnalyzeHandler({
 *     aiEnabled, maxBodyBytes, securityHeaders,
 *     anonymize, containsPII,
 *     loadAnalyzer: () => require("./services/ai-analysis").analyzeText,
 *   });
 *   if (isAnalyzeEndpoint && req.method === "POST") handle(req, res, corsOrigin);
 */

// Stub no-op para telemetria após nuke do Application Insights (PR #276).
// Mantido como hook caso futura solução de observabilidade seja injetada.
// CWE-476 (NULL pointer): garante que chamadas inline nunca lancem ReferenceError.
const trackEvent = (_name, _props) => {};

function createAiAnalyzeHandler({
  aiEnabled,
  maxBodyBytes,
  securityHeaders,
  anonymize,
  containsPII,
  loadAnalyzer,
}) {
  return function handle(req, res, corsOrigin) {
    if (!aiEnabled) {
      res.writeHead(503, { "Content-Type": "application/json", ...securityHeaders });
      res.end(JSON.stringify({ error: "AI analysis disabled", localAnalysisFallback: true }));
      return;
    }
    if ((req.headers["content-type"] || "").split(";")[0].trim() !== "application/json") {
      res.writeHead(415, { "Content-Type": "application/json", ...securityHeaders });
      res.end(JSON.stringify({ error: "Content-Type must be application/json" }));
      return;
    }

    // Coleta body com limite estrito (CWE-400).
    const chunks = [];
    let received = 0;
    let aborted = false;
    req.on("data", (chunk) => {
      received += chunk.length;
      if (received > maxBodyBytes) {
        aborted = true;
        res.writeHead(413, { "Content-Type": "application/json", ...securityHeaders });
        res.end(JSON.stringify({ error: "Payload too large", maxBytes: maxBodyBytes }));
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
        res.writeHead(400, { "Content-Type": "application/json", ...securityHeaders });
        res.end(JSON.stringify({ error: "Invalid JSON" }));
        return;
      }
      const rawText = typeof payload.text === "string" ? payload.text : "";
      if (!rawText || rawText.length < 10) {
        res.writeHead(400, { "Content-Type": "application/json", ...securityHeaders });
        res.end(JSON.stringify({ error: "Field 'text' is required (min 10 chars)" }));
        return;
      }

      // Double-check: roda anonimizador no server mesmo se cliente já fez.
      const { text: cleanText, stats: anonStats } = anonymize(rawText);
      const check = containsPII(cleanText);
      if (!check.clean) {
        res.writeHead(422, { "Content-Type": "application/json", ...securityHeaders });
        res.end(
          JSON.stringify({
            error: "Text contains residual PII after anonymization",
            hint: "Run shared/anonymizer.js on the client BEFORE POSTing",
          }),
        );
        return;
      }

      try {
        const analyzeText = loadAnalyzer();
        const result = await analyzeText(cleanText);
        // LGPD: anexa metadados de transparência (Art. 6º V + Art. 9º)
        result.lgpd = {
          retention_seconds: 0,
          legal_basis: "LGPD Art. 7º I (consentimento)",
          anonymized_client_side: true,
          anonymized_server_side: true,
          data_residency: "brazil-south",
          ai_provider: "azure-openai",
          ai_model: result.model || "gpt-4o-mini",
        };
        trackEvent("AI.Analysis.Success", {
          contentHash: result.contentHash,
          cidsFound: String((result.cids || []).length),
          direitosSugeridos: String((result.direitos_sugeridos || []).length),
          durationMs: String(result.durationMs),
          tokensInput: String(result.tokens ? result.tokens.input : 0),
          tokensOutput: String(result.tokens ? result.tokens.output : 0),
          confianca: String(result.confianca || "baixa"),
          anonPatterns: Object.keys(anonStats).join(","),
        });
        const okHeaders = {
          "Content-Type": "application/json",
          "Cache-Control": "no-store",
          "X-Data-Retention": "0",
          "X-LGPD-Legal-Basis": "Art-7-I-Consentimento",
          "X-AI-Provider": "azure-openai",
          ...securityHeaders,
        };
        if (corsOrigin) okHeaders["Access-Control-Allow-Origin"] = corsOrigin;
        res.writeHead(200, okHeaders);
        res.end(JSON.stringify(result));
      } catch (err) {
        const errMsg = String(err && err.message).slice(0, 500);
        const errCode = String((err && err.code) || "");
        const retryAfter = Number((err && err.retryAfter) || 0);
        trackEvent("AI.Analysis.Error", {
          message: errMsg,
          code: errCode,
          status: String((err && err.status) || ""),
        });
        const status = errCode === "CIRCUIT_OPEN" || errCode === "ETIMEDOUT" ? 503 : 502;
        const errorHeaders = { "Content-Type": "application/json", ...securityHeaders };
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
        res.writeHead(400, { "Content-Type": "application/json", ...securityHeaders });
        res.end(JSON.stringify({ error: "Bad Request" }));
      }
    });
  };
}

module.exports = { createAiAnalyzeHandler };
