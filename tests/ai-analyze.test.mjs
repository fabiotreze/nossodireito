"use strict";

/**
 * Regressão para PR #276 (Application Insights nuke):
 * lib/ai-analyze.js chamava trackEvent() sem importar, gerando ReferenceError
 * em TODA chamada à Análise IA — usuário via "1 arquivo(s) com erro: Análise IA".
 *
 * Garante que o handler:
 *  - Retorna 503 quando aiEnabled=false (early return)
 *  - Não lança ReferenceError em código sem AI quando trackEvent é chamado
 *  - Roteia corretamente sucesso e erro do analyzer mock
 */

import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import http from "node:http";

const require = createRequire(import.meta.url);
const { createAiAnalyzeHandler } = require("../lib/ai-analyze");

function makeRequest(server, body, headers = { "content-type": "application/json" }) {
  return new Promise((resolve, reject) => {
    const port = server.address().port;
    const req = http.request(
      { host: "127.0.0.1", port, path: "/api/analyze-document", method: "POST", headers, timeout: 5000 },
      (res) => {
        const chunks = [];
        res.on("data", (c) => chunks.push(c));
        res.on("end", () =>
          resolve({
            status: res.statusCode,
            body: Buffer.concat(chunks).toString("utf8"),
          }),
        );
      },
    );
    req.on("timeout", () => {
      req.destroy(new Error("request timeout (server provavelmente crashou — ReferenceError?)"));
    });
    req.on("error", reject);
    req.write(body);
    req.end();
  });
}

function startServer(handler) {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => handler(req, res));
    server.listen(0, "127.0.0.1", () => resolve(server));
  });
}

test("ai-analyze retorna 503 quando AI desabilitado", async () => {
  const handle = createAiAnalyzeHandler({
    aiEnabled: false,
    maxBodyBytes: 200 * 1024,
    securityHeaders: {},
    anonymize: (t) => ({ text: t, stats: {} }),
    containsPII: () => ({ clean: true, found: [] }),
    loadAnalyzer: () => async () => ({}),
  });
  const server = await startServer(handle);
  try {
    const res = await makeRequest(server, JSON.stringify({ text: "laudo médico aaaaaaaaaa" }));
    assert.equal(res.status, 503);
    const body = JSON.parse(res.body);
    assert.equal(body.error, "AI analysis disabled");
    assert.equal(body.localAnalysisFallback, true);
  } finally {
    server.close();
  }
});

test("ai-analyze sucesso retorna 200 sem ReferenceError (PR #276 regressão)", async () => {
  const handle = createAiAnalyzeHandler({
    aiEnabled: true,
    maxBodyBytes: 200 * 1024,
    securityHeaders: {},
    anonymize: (t) => ({ text: t, stats: { CPF: 0 } }),
    containsPII: () => ({ clean: true, found: [] }),
    loadAnalyzer: () => async (text) => ({
      cids: ["F84.0"],
      direitos_sugeridos: ["bpc"],
      confianca: "alta",
      contentHash: "abc123",
      durationMs: 100,
      tokens: { input: 50, output: 30 },
      model: "gpt-4o-mini",
    }),
  });
  const server = await startServer(handle);
  try {
    const res = await makeRequest(
      server,
      JSON.stringify({ text: "Laudo médico com CID F84.0 paciente diagnosticado." }),
    );
    assert.equal(res.status, 200, `Expected 200, got ${res.status}: ${res.body}`);
    const body = JSON.parse(res.body);
    assert.deepEqual(body.cids, ["F84.0"]);
    assert.ok(body.lgpd, "LGPD metadata deve estar presente");
    assert.equal(body.lgpd.retention_seconds, 0);
  } finally {
    server.close();
  }
});

test("ai-analyze erro do analyzer retorna 502 sem ReferenceError", async () => {
  const handle = createAiAnalyzeHandler({
    aiEnabled: true,
    maxBodyBytes: 200 * 1024,
    securityHeaders: {},
    anonymize: (t) => ({ text: t, stats: {} }),
    containsPII: () => ({ clean: true, found: [] }),
    loadAnalyzer: () => async () => {
      const err = new Error("Azure OpenAI 429");
      err.code = "RATE_LIMIT";
      throw err;
    },
  });
  const server = await startServer(handle);
  try {
    const res = await makeRequest(
      server,
      JSON.stringify({ text: "Laudo médico paciente xxxxx." }),
    );
    assert.equal(res.status, 502, `Expected 502, got ${res.status}: ${res.body}`);
    const body = JSON.parse(res.body);
    assert.equal(body.error, "AI service unavailable");
    assert.equal(body.localAnalysisFallback, true);
  } finally {
    server.close();
  }
});

test("ai-analyze circuit-breaker retorna 503", async () => {
  const handle = createAiAnalyzeHandler({
    aiEnabled: true,
    maxBodyBytes: 200 * 1024,
    securityHeaders: {},
    anonymize: (t) => ({ text: t, stats: {} }),
    containsPII: () => ({ clean: true, found: [] }),
    loadAnalyzer: () => async () => {
      const err = new Error("circuit open");
      err.code = "CIRCUIT_OPEN";
      throw err;
    },
  });
  const server = await startServer(handle);
  try {
    const res = await makeRequest(
      server,
      JSON.stringify({ text: "Laudo médico do paciente." }),
    );
    assert.equal(res.status, 503);
  } finally {
    server.close();
  }
});

test("ai-analyze rejeita Content-Type errado (415)", async () => {
  const handle = createAiAnalyzeHandler({
    aiEnabled: true,
    maxBodyBytes: 200 * 1024,
    securityHeaders: {},
    anonymize: (t) => ({ text: t, stats: {} }),
    containsPII: () => ({ clean: true, found: [] }),
    loadAnalyzer: () => async () => ({}),
  });
  const server = await startServer(handle);
  try {
    const res = await makeRequest(server, "text", { "content-type": "text/plain" });
    assert.equal(res.status, 415);
  } finally {
    server.close();
  }
});

test("ai-analyze rejeita PII residual (422)", async () => {
  const handle = createAiAnalyzeHandler({
    aiEnabled: true,
    maxBodyBytes: 200 * 1024,
    securityHeaders: {},
    anonymize: (t) => ({ text: t, stats: {} }),
    containsPII: () => ({ clean: false, found: ["CPF"] }),
    loadAnalyzer: () => async () => ({}),
  });
  const server = await startServer(handle);
  try {
    const res = await makeRequest(
      server,
      JSON.stringify({ text: "Texto com PII vazando aaaaa." }),
    );
    assert.equal(res.status, 422);
    const body = JSON.parse(res.body);
    assert.equal(body.error, "Text contains residual PII after anonymization");
    assert.equal(Object.prototype.hasOwnProperty.call(body, "found"), false);
  } finally {
    server.close();
  }
});
