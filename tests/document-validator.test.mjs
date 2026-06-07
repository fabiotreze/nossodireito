/**
 * Testes do document-validator: gate multidimensional que decide se o texto
 * extraído de um PDF/imagem é realmente clínico antes de alimentar matchRights().
 *
 * Estratégia coberta:
 *   - ACEITA: laudo TEA (F84 + neuropediatra), atestado (CRM + atestado médico),
 *     laudo de psicólogo (CRP + CID-10), laudo neurológico CID-11.
 *   - REJEITA: boleto de plano de saúde, manual de remédio, boletim escolar,
 *     contrato de prestação de serviço, currículo com a palavra "deficiência",
 *     PDF em branco/curto demais, qualquer texto sem CRM nem CID válido.
 *
 * Princípio: false-negative em laudo legítimo é ruim mas tolerável (usuário
 * navega categorias); false-positive em texto não-clínico é PIOR porque gera
 * sugestões de direitos sem fundamento — quebra a confiança no produto.
 */

"use strict";

import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { validate } = require("../shared/document-validator");

// ── ACEITAÇÃO: laudos clínicos legítimos ──

test("aceita laudo TEA com CID F84 e termo 'laudo médico'", () => {
  const txt = `LAUDO MÉDICO
  Paciente apresenta diagnóstico de Transtorno do Espectro Autista — CID-10 F84.0.
  Avaliação clínica realizada em 12/03/2025. Encaminhamento para terapia ocupacional
  e fonoaudiologia. Hipótese diagnóstica confirmada.`;
  const r = validate(txt);
  assert.equal(r.accepted, true, `score=${r.score} reasons=${r.reasons}`);
  assert.equal(r.signals.cid, true);
  assert.ok(r.score >= 5);
});

test("aceita atestado com CRM/SP e termos clínicos", () => {
  const txt = `Atestado Médico
  Atesto, para os devidos fins, que o paciente João da Silva esteve sob meus
  cuidados, apresentando sintomas compatíveis com quadro clínico de transtorno
  ansioso. Prescrição: afastamento por 15 dias.
  Dr. José Souza — CRM/SP 123456`;
  const r = validate(txt);
  assert.equal(r.accepted, true, `score=${r.score} reasons=${r.reasons}`);
  assert.equal(r.signals.professional, true);
});

test("aceita laudo de psicólogo (CRP + CID + vocabulário)", () => {
  const txt = `Relatório Psicológico
  Após avaliação psicológica, conclui-se hipótese diagnóstica de F33.1.
  Evolução clínica do paciente apresenta sinais clínicos compatíveis.
  Psic. Ana Costa — CRP 06/12345`;
  const r = validate(txt);
  assert.equal(r.accepted, true, `score=${r.score} reasons=${r.reasons}`);
  assert.equal(r.signals.professional, true);
  assert.equal(r.signals.cid, true);
});

test("aceita laudo neurológico com CID-11 e prognóstico", () => {
  const txt = `Laudo Neurológico
  Diagnóstico: CID-11 6A02.0 (autism spectrum disorder, sem deficiência
  intelectual). Prognóstico depende de intervenção precoce com terapia
  ocupacional e fonoaudiológica.`;
  const r = validate(txt);
  assert.equal(r.accepted, true, `score=${r.score} reasons=${r.reasons}`);
  assert.equal(r.signals.cid, true);
});

test("aceita relatório fisioterapêutico (COFFITO + termos)", () => {
  const txt = `Relatório Fisioterapêutico
  Paciente em acompanhamento. Avaliação clínica indica melhora.
  Diagnóstico funcional compatível. Condução terapêutica mantida.
  Fisio. Carlos — COFFITO 12345`;
  const r = validate(txt);
  assert.equal(r.accepted, true, `score=${r.score} reasons=${r.reasons}`);
});

// ── REJEIÇÃO: textos não-clínicos que ANTES passavam pelo gate antigo ──

test("rejeita boleto de plano de saúde (tem 'paciente' e 'médico' mas nada estrutural)", () => {
  const txt = `Boleto de cobrança — Plano de Saúde Vida Sim.
  Mensalidade do paciente: R$ 450,00. Vencimento: 10/04/2025.
  Atendimento médico ilimitado. Não pague em duplicidade.`;
  const r = validate(txt);
  assert.equal(r.accepted, false);
  assert.ok(r.reasons.length > 0);
});

test("rejeita manual de remédio (bula) sem CRM nem CID estrutural", () => {
  const txt = `Bula do medicamento Exemplomicin.
  Indicação: tratamento de infecções. Posologia recomendada pelo médico.
  Não use sem prescrição. Pode causar comorbidades em pacientes alérgicos.`;
  const r = validate(txt);
  assert.equal(r.accepted, false);
});

test("rejeita boletim escolar que cita 'deficiência'", () => {
  const txt = `Boletim Escolar — 4º Ano
  Aluno: João da Silva. Notas: Matemática 8, Português 7, Ciências 9.
  Observação: aluno inscrito no programa de educação inclusiva para
  estudantes com deficiência. Aprovado por média.`;
  const r = validate(txt);
  assert.equal(r.accepted, false);
});

test("rejeita contrato de prestação de serviço com palavras genéricas", () => {
  const txt = `Contrato de prestação de serviço.
  Cláusula 1: o contratado se compromete a prestar atendimento médico
  domiciliar ao paciente, observando todas as normas técnicas. Cláusula 2:
  valor mensal R$ 2.000,00. Cláusula 3: rescisão com aviso prévio de 30 dias.`;
  const r = validate(txt);
  assert.equal(r.accepted, false);
});

test("rejeita currículo profissional com a palavra 'deficiência'", () => {
  const txt = `Currículo — Maria Souza
  Formação: Pedagogia. Experiência: 5 anos em escola inclusiva atendendo
  alunos com deficiência. Habilidades: trabalho em equipe, organização.
  Contato: maria@exemplo.com`;
  const r = validate(txt);
  assert.equal(r.accepted, false);
});

test("rejeita texto vazio ou nulo", () => {
  assert.equal(validate("").accepted, false);
  assert.equal(validate(null).accepted, false);
  assert.equal(validate(undefined).accepted, false);
  assert.equal(validate(42).accepted, false);
});

test("rejeita texto curto sem nenhum sinal forte", () => {
  const txt = "Olá, este é um teste qualquer sem nada de médico.";
  const r = validate(txt);
  assert.equal(r.accepted, false);
});

// ── EDGE CASES ──

test("CRM sem corroboração ainda passa (score 3 + vocabulário em zero) NÃO aprova", () => {
  // CRM isolado dá score 3 — abaixo do mínimo 5 — então rejeita.
  const txt = "Documento qualquer. CRM/SP 999999. Fim.";
  const r = validate(txt);
  assert.equal(r.signals.professional, true);
  assert.equal(r.accepted, false, "score baixo mesmo com sinal forte rejeita");
});

test("CID isolado (sem vocabulário/tipo doc) NÃO aprova", () => {
  // CID-10 dá score 3 — abaixo do mínimo 5 — então rejeita.
  const txt = "Anotação: F84.0";
  const r = validate(txt);
  assert.equal(r.signals.cid, true);
  assert.equal(r.accepted, false, "CID solto sem contexto rejeita");
});

test("muitos termos genéricos SEM CRM nem CID NÃO aprovam (sinal forte ausente)", () => {
  const txt = `Texto rico em palavras: diagnóstico, prognóstico, prescrição,
  anamnese, sintomas, sinais clínicos, evolução clínica, avaliação clínica,
  comorbidades, terapia ocupacional. Mas sem CRM nem CID.`;
  const r = validate(txt);
  assert.ok(r.score >= 5, `score=${r.score} esperava >=5`);
  assert.equal(r.signals.professional, false);
  assert.equal(r.signals.cid, false);
  assert.equal(r.accepted, false, "sem sinal forte rejeita mesmo com score alto");
});

test("CID em URL não conta como sinal (boundary)", () => {
  const txt = "Veja https://exemplo.com/abcF84.0/path. Texto qualquer.";
  const r = validate(txt);
  assert.equal(r.signals.cid, false, "CID dentro de URL não é boundary válido");
  assert.equal(r.accepted, false);
});

test("signals expõe os matches para debug/UX", () => {
  const txt = `Laudo Médico
  Diagnóstico CID F84.0. CRM/SP 12345. Anamnese realizada.`;
  const r = validate(txt);
  assert.equal(r.accepted, true);
  assert.ok(r.signals.docTypes.length >= 1, "deve listar tipos de documento");
  assert.equal(r.signals.professional, true);
  assert.equal(r.signals.cid, true);
});

test("score é determinístico para o mesmo input", () => {
  const txt = `Laudo médico. Paciente com CID F84.0. Diagnóstico confirmado.
  Anamnese realizada. CRM/RJ 12345.`;
  const r1 = validate(txt);
  const r2 = validate(txt);
  assert.equal(r1.score, r2.score, "score deve ser determinístico");
  assert.equal(r1.accepted, r2.accepted);
});
