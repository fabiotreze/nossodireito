/**
 * G3 — Testes do pós-validador da resposta da IA:
 * descarta resumo se contiver URLs fora da allowlist oficial.
 *
 * Executar: npm run test:js
 */

"use strict";

import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const { postValidateAIResponse } = require("../services/ai-analysis");

test("resumo sem URL passa intacto", () => {
  const r = postValidateAIResponse({
    resumo: "Possível elegibilidade ao BPC nos termos da Lei 8.742/1993.",
    confianca: "media",
  });
  assert.equal(r.ok, true);
  assert.equal(r.violations.length, 0);
  assert.equal(r.sanitized.resumo, "Possível elegibilidade ao BPC nos termos da Lei 8.742/1993.");
});

test("URL .gov.br passa", () => {
  const r = postValidateAIResponse({
    resumo: "Veja em https://www.gov.br/inss/pt-br os requisitos.",
    confianca: "alta",
  });
  assert.equal(r.ok, true);
  assert.equal(r.violations.length, 0);
});

test("URL .planalto.gov.br passa", () => {
  const r = postValidateAIResponse({
    resumo: "Lei 8.742/1993: https://www.planalto.gov.br/ccivil_03/leis/l8742.htm",
    confianca: "alta",
  });
  assert.equal(r.ok, true);
});

test("URL icd.who.int passa (exceção controlada — adotada pelo MS)", () => {
  const r = postValidateAIResponse({
    resumo: "CID em https://icd.who.int/browse10/2019/en",
    confianca: "media",
  });
  assert.equal(r.ok, true);
  assert.equal(r.violations.length, 0);
});

test("URL .jus.br / .def.br / .leg.br / .mp.br passam", () => {
  const r = postValidateAIResponse({
    resumo:
      "Veja https://www.stf.jus.br/x, https://www.defensoria.def.br/y, https://www.camara.leg.br/z, https://www.mpf.mp.br/k",
    confianca: "alta",
  });
  assert.equal(r.ok, true);
});

test("URL externa qualquer é DESCARTADA (resumo sanitizado, confianca=baixa)", () => {
  const r = postValidateAIResponse({
    resumo: "Consulte https://blogjuridico.com.br/artigo-bpc/ para detalhes.",
    confianca: "alta",
  });
  assert.equal(r.ok, false);
  assert.equal(r.violations.length, 1);
  assert.match(r.sanitized.resumo, /descartada/i);
  assert.equal(r.sanitized.confianca, "baixa");
});

test("URL .com.br não-oficial é DESCARTADA", () => {
  const r = postValidateAIResponse({
    resumo: "Veja https://uol.com.br/noticia-pcd",
    confianca: "media",
  });
  assert.equal(r.ok, false);
  assert.match(r.sanitized.resumo, /descartada/i);
});

test("mistura de URL válida + inválida sanitiza tudo", () => {
  const r = postValidateAIResponse({
    resumo:
      "Consulte https://www.planalto.gov.br/ccivil/l8742.htm e também https://blogspot.com/x.",
    confianca: "alta",
  });
  assert.equal(r.ok, false);
  assert.equal(r.violations.length, 1);
  assert.equal(r.violations[0], "https://blogspot.com/x.");
  assert.match(r.sanitized.resumo, /descartada/i);
});

test("URL malformada é tratada como violação", () => {
  const r = postValidateAIResponse({
    resumo: "Detalhes em http://[mal-formed]",
    confianca: "media",
  });
  assert.equal(r.ok, false);
  assert.ok(r.violations.length >= 1);
});

test("resumo ausente / não-string é tolerado (ok=true, sem violações)", () => {
  const r1 = postValidateAIResponse({ confianca: "baixa" });
  assert.equal(r1.ok, true);
  const r2 = postValidateAIResponse({ resumo: null, confianca: "baixa" });
  assert.equal(r2.ok, true);
});

test("preserva outros campos do parsed quando ok=true", () => {
  const r = postValidateAIResponse({
    resumo: "ok",
    cids: ["F84.0"],
    direitos_sugeridos: [{ categoria_id: "ciptea", confianca: "alta" }],
    confianca: "alta",
  });
  assert.equal(r.ok, true);
  assert.deepEqual(r.sanitized.cids, ["F84.0"]);
  assert.equal(r.sanitized.direitos_sugeridos.length, 1);
});

test("preserva cids/direitos mesmo quando sanitiza resumo", () => {
  const r = postValidateAIResponse({
    resumo: "Veja em https://random.example.com/",
    cids: ["F84.0"],
    direitos_sugeridos: [{ categoria_id: "ciptea", confianca: "alta" }],
    confianca: "alta",
  });
  assert.equal(r.ok, false);
  assert.deepEqual(r.sanitized.cids, ["F84.0"]);
  assert.equal(r.sanitized.direitos_sugeridos.length, 1);
  assert.equal(r.sanitized.confianca, "baixa");
});
