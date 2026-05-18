/**
 * Contract + unit tests for geo-search v2 (IBGE-backed detectLocation).
 *
 * Why: detectLocation lives inside an IIFE in `js/app.js` (browser-only) and
 * is not exported. We:
 *
 *  1. Assert source-level invariants (no regression to the old hardcoded
 *     CIDADES_UF dictionary; new IBGE wiring stays in place).
 *  2. Validate the data snapshot at data/municipios_br.json against
 *     schemas/municipios_br.schema.json structure (hand-rolled checks; no
 *     extra deps).
 *  3. Extract the geo helpers via brace-balanced regex slicing and evaluate
 *     them in a Node sandbox with the real municipios dataset injected, to
 *     exercise real detection behavior.
 *
 * Run: npm run test:js
 */

"use strict";

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import vm from "node:vm";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");
const APP_JS = readFileSync(resolve(ROOT, "js/app.js"), "utf8");
const MUNI = JSON.parse(readFileSync(resolve(ROOT, "data/municipios_br.json"), "utf8"));
const ORGAOS_SCHEMA = JSON.parse(
  readFileSync(resolve(ROOT, "schemas/orgaos_estaduais.schema.json"), "utf8"),
);
const DIREITOS = JSON.parse(readFileSync(resolve(ROOT, "data/direitos.json"), "utf8"));

const UF_LIST = [
  "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT","PA",
  "PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO",
];

// ──────────────────────────────────────────────────────────────
// 1. Source-level contract
// ──────────────────────────────────────────────────────────────

test("contract: hardcoded CIDADES_UF dictionary has been removed", () => {
  assert.ok(
    !/const\s+CIDADES_UF\s*=/.test(APP_JS),
    "CIDADES_UF still present in app.js — geo-search v2 should rely on the IBGE snapshot only",
  );
});

test("contract: IBGE municipios snapshot is wired into the data pipeline", () => {
  assert.match(APP_JS, /_earlyMunicipios\s*=\s*_earlyFetch\(['"]data\/municipios_br\.json['"]\)/);
  assert.match(APP_JS, /municipiosData\s*=\s*deepFreeze/);
  assert.match(APP_JS, /municipiosByKey/);
});

test("contract: detectLocation v2 helpers exist", () => {
  assert.match(APP_JS, /function\s+_normalizeGeo\s*\(/);
  assert.match(APP_JS, /function\s+_titleCaseGeo\s*\(/);
  assert.match(APP_JS, /function\s+detectLocation\s*\(/);
});

test("contract: honest municipal fallback message is present", () => {
  assert.match(APP_JS, /Ainda não temos dados específicos da prefeitura/);
});

test("contract: ESTADOS_BR still covers all 27 UFs", () => {
  for (const uf of UF_LIST) {
    assert.ok(APP_JS.includes(`'${uf}'`), `UF ${uf} missing from ESTADOS_BR/app.js`);
  }
});

// ──────────────────────────────────────────────────────────────
// 2. data/municipios_br.json integrity
// ──────────────────────────────────────────────────────────────

test("municipios snapshot: top-level shape matches schema", () => {
  for (const key of ["fonte", "gerado_em", "total", "municipios"]) {
    assert.ok(key in MUNI, `missing top-level key '${key}'`);
  }
  assert.match(MUNI.fonte, /^https:\/\//);
  assert.match(MUNI.gerado_em, /^\d{4}-\d{2}-\d{2}$/);
  assert.equal(typeof MUNI.total, "number");
  assert.equal(MUNI.total, MUNI.municipios.length, "total ≠ municipios.length");
});

test("municipios snapshot: 5570 ± 30 entries (IBGE baseline)", () => {
  assert.ok(MUNI.total >= 5500 && MUNI.total <= 5600, `unexpected total: ${MUNI.total}`);
});

test("municipios snapshot: covers all 27 UFs", () => {
  const seen = new Set(MUNI.municipios.map((m) => m.u));
  for (const uf of UF_LIST) {
    assert.ok(seen.has(uf), `no município for UF ${uf}`);
  }
  assert.equal(seen.size, 27, `unexpected UF count: ${seen.size}`);
});

test("municipios snapshot: every entry has {id, n, u, k} with valid shapes", () => {
  for (const m of MUNI.municipios) {
    assert.equal(typeof m.id, "number", `bad id: ${JSON.stringify(m)}`);
    assert.ok(m.id >= 1000000 && m.id <= 9999999, `id out of range: ${m.id}`);
    assert.equal(typeof m.n, "string");
    assert.ok(m.n.length >= 2, `short n: ${m.n}`);
    assert.match(m.u, /^[A-Z]{2}$/, `bad UF: ${m.u}`);
    assert.match(m.k, /^[a-z0-9 ]+$/, `bad k (non-normalized chars): "${m.k}"`);
  }
});

test("municipios snapshot: no duplicate IBGE ids", () => {
  const ids = new Set();
  for (const m of MUNI.municipios) {
    assert.ok(!ids.has(m.id), `duplicate IBGE id: ${m.id}`);
    ids.add(m.id);
  }
});

test("municipios snapshot: well-known anchors are present", () => {
  const byKey = new Map(MUNI.municipios.map((m) => [m.k + "|" + m.u, m]));
  for (const probe of [
    ["sao paulo", "SP", 3550308],
    ["rio de janeiro", "RJ", 3304557],
    ["brasilia", "DF", 5300108],
    ["belo horizonte", "MG", 3106200],
    ["fortaleza", "CE", 2304400],
    ["manaus", "AM", 1302603],
    ["porto alegre", "RS", 4314902],
  ]) {
    const [k, u, id] = probe;
    const m = byKey.get(k + "|" + u);
    assert.ok(m, `missing anchor município: ${k}/${u}`);
    assert.equal(m.id, id, `wrong IBGE id for ${k}/${u}: expected ${id}, got ${m.id}`);
  }
});

// ──────────────────────────────────────────────────────────────
// 3. data/direitos.json :: orgaos_estaduais matches schema
// ──────────────────────────────────────────────────────────────

test("orgaos_estaduais: schema file is loadable JSON Schema draft-07", () => {
  assert.equal(ORGAOS_SCHEMA.$schema, "http://json-schema.org/draft-07/schema#");
  assert.equal(ORGAOS_SCHEMA.type, "array");
});

test("orgaos_estaduais: 27 entries, one per UF, all fields well-formed", () => {
  const arr = DIREITOS.orgaos_estaduais || [];
  assert.equal(arr.length, 27, `expected 27 UFs, got ${arr.length}`);
  const seen = new Set();
  for (const o of arr) {
    assert.match(o.uf, /^[A-Z]{2}$/, `bad UF: ${o.uf}`);
    assert.ok(!seen.has(o.uf), `duplicate UF: ${o.uf}`);
    seen.add(o.uf);
    assert.ok(typeof o.nome === "string" && o.nome.length >= 3, `bad nome for ${o.uf}`);
    assert.match(o.url, /^https:\/\//, `non-https url for ${o.uf}: ${o.url}`);
    if (o.sefaz) assert.match(o.sefaz, /^https:\/\//, `non-https sefaz for ${o.uf}`);
    if (o.detran) assert.match(o.detran, /^https:\/\//, `non-https detran for ${o.uf}`);
    if (o.beneficios_destaque) {
      assert.ok(Array.isArray(o.beneficios_destaque));
      assert.ok(o.beneficios_destaque.length >= 1, `empty beneficios_destaque for ${o.uf}`);
    }
  }
  for (const uf of UF_LIST) assert.ok(seen.has(uf), `missing UF in orgaos_estaduais: ${uf}`);
});

// ──────────────────────────────────────────────────────────────
// 4. Behavior: _normalizeGeo + detectLocation (sandboxed)
// ──────────────────────────────────────────────────────────────

function extractFunction(name) {
  const startRe = new RegExp(`function\\s+${name}\\s*\\([^)]*\\)\\s*\\{`);
  const m = APP_JS.match(startRe);
  if (!m) throw new Error(`function ${name} not found in app.js`);
  const start = m.index;
  let i = APP_JS.indexOf("{", start);
  let depth = 1;
  i += 1;
  while (i < APP_JS.length && depth > 0) {
    const ch = APP_JS[i];
    if (ch === "{") depth += 1;
    else if (ch === "}") depth -= 1;
    i += 1;
  }
  return APP_JS.slice(start, i);
}

function extractObjectLiteral(constName) {
  // Match: const NAME = { ... balanced ... };
  const startRe = new RegExp(`const\\s+${constName}\\s*=\\s*\\{`);
  const m = APP_JS.match(startRe);
  if (!m) throw new Error(`const ${constName} not found in app.js`);
  const start = m.index;
  let i = APP_JS.indexOf("{", start);
  let depth = 1;
  i += 1;
  while (i < APP_JS.length && depth > 0) {
    const ch = APP_JS[i];
    if (ch === "{") depth += 1;
    else if (ch === "}") depth -= 1;
    i += 1;
  }
  return APP_JS.slice(start, i) + ";";
}

const sandbox = {
  module: { exports: {} },
  console,
  // Inject real IBGE data so detectLocation can resolve cities.
  __municipios: MUNI.municipios,
};
vm.createContext(sandbox);
const source = `
  ${extractObjectLiteral("ESTADOS_BR")}
  const UF_SET = new Set(Object.values(ESTADOS_BR));
  ${extractFunction("_normalizeGeo")}
  ${extractFunction("_titleCaseGeo")}
  const municipiosData = __municipios;
  const municipiosByKey = new Map(municipiosData.map((m) => [m.k, m]));
  ${extractFunction("detectLocation")}
  module.exports = { _normalizeGeo, _titleCaseGeo, detectLocation, ESTADOS_BR };
`;
vm.runInContext(source, sandbox);
const { _normalizeGeo, detectLocation, ESTADOS_BR } = sandbox.module.exports;

test("_normalizeGeo: strips accents, lowercases, drops apostrophes/hyphens", () => {
  assert.equal(_normalizeGeo("São Paulo"), "sao paulo");
  assert.equal(_normalizeGeo("D'Oeste"), "doeste");
  assert.equal(_normalizeGeo("Ji-Paraná"), "jiparana");
  assert.equal(_normalizeGeo("  Belo   Horizonte  "), "belo horizonte");
  assert.equal(_normalizeGeo(""), "");
  assert.equal(_normalizeGeo(null), "");
});

test("detectLocation: returns null for empty/whitespace", () => {
  assert.equal(detectLocation(""), null);
  assert.equal(detectLocation("   "), null);
});

test("detectLocation: every UF sigla (2 chars) is detected", () => {
  for (const uf of UF_LIST) {
    const r = detectLocation(uf);
    assert.ok(r, `no detection for sigla ${uf}`);
    assert.equal(r.type, "uf");
    assert.equal(r.uf, uf);
  }
});

test("detectLocation: every estado-nome (NFD) is detected", () => {
  for (const [nome, uf] of Object.entries(ESTADOS_BR)) {
    const r = detectLocation(nome);
    assert.ok(r, `no detection for estado ${nome}`);
    assert.equal(r.uf, uf);
    assert.ok(r.type === "estado" || r.type === "cidade",
      `unexpected type for ${nome}: ${r.type}`);
  }
});

test("detectLocation: accented estado names also work", () => {
  assert.equal(detectLocation("São Paulo").uf, "SP");
  assert.equal(detectLocation("Pará").uf, "PA");
  assert.equal(detectLocation("Ceará").uf, "CE");
  assert.equal(detectLocation("Rondônia").uf, "RO");
});

test("detectLocation: exact município hits return IBGE id", () => {
  const probes = [
    ["São Paulo", "SP", 3550308],
    ["Rio de Janeiro", "RJ", 3304557],
    ["Belo Horizonte", "MG", 3106200],
    ["Brasília", "DF", 5300108],
    ["Fortaleza", "CE", 2304400],
    ["Manaus", "AM", 1302603],
    ["Porto Alegre", "RS", 4314902],
    ["Florianópolis", "SC", 4205407],
    ["Curitiba", "PR", 4106902],
    ["Salvador", "BA", 2927408],
  ];
  for (const [query, uf, id] of probes) {
    const r = detectLocation(query);
    assert.ok(r, `no detection for ${query}`);
    assert.equal(r.uf, uf, `wrong UF for ${query}: ${r.uf}`);
    assert.equal(r.ibge_id, id, `wrong IBGE id for ${query}: ${r.ibge_id}`);
  }
});

test("detectLocation: município com apóstrofo/hífen normaliza", () => {
  const r = detectLocation("Alta Floresta D'Oeste");
  assert.ok(r);
  assert.equal(r.uf, "RO");
  assert.equal(r.type, "cidade");
});

test("detectLocation: longest match wins when one nome contém outro", () => {
  // "São Paulo" (SP) vs "São Paulo do Potengi" (RN). Input com a versão longa
  // deve resolver para o município mais específico, não para a capital.
  const r = detectLocation("são paulo do potengi");
  assert.ok(r, "no detection for são paulo do potengi");
  assert.equal(r.uf, "RN");
  assert.equal(r.type, "cidade");
});

test("detectLocation: tipped queries (estado + benefício) detect the location", () => {
  const r = detectLocation("auxilio brasil bahia");
  assert.ok(r);
  assert.equal(r.uf, "BA");
});

test("detectLocation: gibberish returns null", () => {
  assert.equal(detectLocation("xxxyyyzzz"), null);
  assert.equal(detectLocation("123456"), null);
});

test("detectLocation: short non-UF tokens don't false-positive", () => {
  // "BR" não é UF; "ZZ" tampouco.
  assert.equal(detectLocation("BR"), null);
  assert.equal(detectLocation("ZZ"), null);
  // 1-letter inputs nunca casam.
  assert.equal(detectLocation("a"), null);
});

test("detectLocation: result shape includes the documented fields", () => {
  const r = detectLocation("São Paulo");
  assert.deepEqual(Object.keys(r).sort(), ["ibge_id", "matched", "name", "type", "uf"]);
});
