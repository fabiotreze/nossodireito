/**
 * Testes do anonimizador de PII (LGPD).
 *
 * Executar: npm run test:js
 * (Node 22+ tem test runner nativo, zero deps.)
 */

"use strict";

import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const { anonymize, containsPII } = require("../shared/anonymizer");

// ── CPF ──
test("CPF formatado é anonimizado", () => {
  const r = anonymize("Portador: João Silva, CPF: 123.456.789-09");
  assert.match(r.text, /\[CPF\]/);
  assert.equal(containsPII(r.text).clean, true);
});

test("CPF sem máscara (11 dígitos) é anonimizado", () => {
  const r = anonymize("CPF 12345678909 vigente");
  assert.match(r.text, /\[CPF\]/);
});

// ── CNPJ ──
test("CNPJ é anonimizado antes do CPF (ordem importa)", () => {
  const r = anonymize("Operadora CNPJ 12.345.678/0001-90");
  assert.match(r.text, /\[CNPJ\]/);
  assert.doesNotMatch(r.text, /\[CPF\]/);
});

// ── RG ──
test("RG com SSP/UF é anonimizado", () => {
  const r = anonymize("RG: 12.345.678-9 SSP/SP");
  assert.match(r.text, /\[RG\]/);
});

// ── CEP ──
test("CEP formatado é anonimizado", () => {
  const r = anonymize("CEP 01310-100");
  assert.match(r.text, /\[CEP\]/);
});

// ── Telefone ──
test("Celular brasileiro é anonimizado", () => {
  const r = anonymize("Contato: (11) 91234-5678");
  assert.match(r.text, /\[FONE\]/);
});

test("Telefone fixo é anonimizado", () => {
  const r = anonymize("Tel.: (11) 3456-7890");
  assert.match(r.text, /\[FONE\]/);
});

// ── E-mail ──
test("E-mail é anonimizado", () => {
  const r = anonymize("Enviar para joao.silva@example.com.br");
  assert.match(r.text, /\[EMAIL\]/);
});

// ── Cartão SUS ──
test("Cartão SUS (CNS) é anonimizado", () => {
  const r = anonymize("CNS: 123 4567 8901 2345");
  assert.match(r.text, /\[CNS\]/);
});

// ── Nome após rótulo ──
test("Nome do paciente é anonimizado", () => {
  const r = anonymize("Nome do paciente: Maria Aparecida da Silva");
  assert.match(r.text, /\[NOME\]/);
});

test("Paciente com sobrenome composto é anonimizado", () => {
  const r = anonymize("Paciente: João da Silva Santos");
  assert.match(r.text, /\[NOME\]/);
});

// ── Data de nascimento ──
test("Data de nascimento é anonimizada", () => {
  const r = anonymize("Nasc.: 15/03/1985");
  assert.match(r.text, /\[DATA_NASC\]/);
});

test("DN abreviado é anonimizado", () => {
  const r = anonymize("DN: 15/03/1985");
  assert.match(r.text, /\[DATA_NASC\]/);
});

// ── Endereço ──
test("Endereço após rótulo é anonimizado", () => {
  const r = anonymize("Endereço: Rua das Flores, 123, Apto 45, São Paulo");
  assert.match(r.text, /\[ENDERECO\]/);
});

// ── Filiação ──
test("Nome da mãe é anonimizado", () => {
  const r = anonymize("Nome da mãe: Joana Pereira");
  assert.match(r.text, /\[FILIACAO\]/);
});

// ── O que DEVE ser preservado ──
test("CID-10 NÃO deve ser removido (input médico crítico)", () => {
  const r = anonymize("Paciente diagnosticado com F84.0 e Q90.9");
  assert.match(r.text, /F84\.0/);
  assert.match(r.text, /Q90\.9/);
});

test("Termos médicos genéricos são preservados", () => {
  const r = anonymize("Transtorno do espectro autista grau 2 com comprometimento severo");
  assert.equal(r.text, "Transtorno do espectro autista grau 2 com comprometimento severo");
});

// ── Idempotência ──
test("Anonimizar 2x produz mesmo resultado", () => {
  const original = "CPF 123.456.789-09 e RG 12.345.678-9";
  const r1 = anonymize(original);
  const r2 = anonymize(r1.text);
  assert.equal(r1.text, r2.text);
});

// ── Defesa: containsPII ──
test("containsPII detecta CPF não anonimizado", () => {
  const check = containsPII("texto com 123.456.789-09 no meio");
  assert.equal(check.clean, false);
  assert.ok(check.found.includes("CPF"));
});

test("containsPII confirma texto limpo após anonymize()", () => {
  const r = anonymize("CPF: 123.456.789-09, CEP: 01310-100, Tel (11) 91234-5678");
  const check = containsPII(r.text);
  assert.equal(check.clean, true, `Encontrado: ${check.found.join(",")}`);
});

// ── Cenário real: laudo médico ──
test("Laudo médico real é totalmente anonimizado", () => {
  const laudo = `
    LAUDO MÉDICO
    Paciente: Pedro Henrique Oliveira
    CPF: 987.654.321-00 | RG: 33.444.555-6 SSP/RJ
    DN: 12/05/1990 | Tel: (21) 98765-4321
    Endereço: Av. Brasil 1000, Rio de Janeiro
    Diagnóstico: F84.0 (Autismo infantil) - CID-10
    Conclusão: paciente apresenta TEA nível 2 conforme DSM-5.
  `;
  const r = anonymize(laudo);
  const check = containsPII(r.text);
  assert.equal(check.clean, true, `PII residual encontrada: ${check.found.join(",")}`);
  // CID deve permanecer
  assert.match(r.text, /F84\.0/);
  // Diagnóstico técnico preservado
  assert.match(r.text, /TEA n[íi]vel 2/);
});

// ── Edge cases ──
test("Input não-string retorna vazio sem erro", () => {
  const r = anonymize(null);
  assert.equal(r.text, "");
  assert.deepEqual(r.stats, {});
});

test("Stats reportam contagem correta", () => {
  const r = anonymize("CPF 111.222.333-44 e outro CPF 555.666.777-88");
  assert.equal(r.stats.CPF, 2);
});
