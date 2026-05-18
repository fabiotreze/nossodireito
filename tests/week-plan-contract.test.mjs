/**
 * Contract + unit tests for the AI "plano de 7 dias" + docs checklist.
 *
 * Why: the helpers live inside an IIFE in `js/app.js` (browser-only) and are
 * not exported, so we cannot import them directly. Instead we:
 *
 *  1. Assert source-level invariants (regressão silenciosa = falha aqui).
 *  2. Extract pure helpers via regex slicing and re-evaluate them in a Node
 *     sandbox to exercise real behavior.
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
const STYLES_CSS = readFileSync(resolve(ROOT, "css/styles.css"), "utf8");

// ──────────────────────────────────────────────────────────────
// 1. Source-level contract (prevents accidental removal)
// ──────────────────────────────────────────────────────────────

test("contract: WEEK_PLAN_STORAGE_KEY stays stable for backward-compat", () => {
  assert.match(APP_JS, /WEEK_PLAN_STORAGE_KEY\s*=\s*['"]nd_ai_week_plan_v1['"]/);
});

test("contract: DOCS_CHECKLIST_KEY stays stable for backward-compat", () => {
  assert.match(APP_JS, /DOCS_CHECKLIST_KEY\s*=\s*['"]nd_ai_docs_checklist_v1['"]/);
});

test("contract: storage hardening cap of 20 plans is present", () => {
  assert.match(APP_JS, /WEEK_PLAN_MAX_KEYS\s*=\s*20/);
  assert.match(APP_JS, /function\s+pruneStoredWeekPlans\s*\(/);
  assert.match(APP_JS, /function\s+sanitizePlanKey\s*\(/);
});

test("contract: 6 essential docs are wired in the AI checklist", () => {
  for (const id of ["laudo", "cpf_rg", "residencia", "renda", "ciptea", "responsavel"]) {
    assert.ok(
      APP_JS.includes(`id: '${id}'`) || APP_JS.includes(`id: "${id}"`),
      `missing doc id '${id}' in DOCS_CHECKLIST_ITEMS`,
    );
  }
});

test("contract: progress bar + a11y attributes are emitted", () => {
  assert.match(APP_JS, /analysis-week-plan-bar/);
  assert.match(APP_JS, /aria-valuenow/);
  assert.match(APP_JS, /aria-checked/);
  assert.match(APP_JS, /aria-expanded/);
});

test("contract: legal disclaimer reinforced inside the AI practical block", () => {
  assert.match(APP_JS, /analysis-ai-disclaimer/);
  assert.match(APP_JS, /Defensoria/i);
});

test("contract: CSS exposes progress bar + reduced-motion + focus-visible", () => {
  assert.match(STYLES_CSS, /\.analysis-week-plan-bar(-fill)?/);
  assert.match(STYLES_CSS, /@media\s*\(prefers-reduced-motion:\s*reduce\)/);
  assert.match(STYLES_CSS, /:focus-visible/);
});

test("contract: no collision — both renderDocsChecklist and renderAIDocsChecklist exist", () => {
  // renderDocsChecklist = page "Documentos" (pre-existing).
  // renderAIDocsChecklist = AI panel (Day 3 addition). Both must coexist.
  assert.ok(
    APP_JS.includes("function renderDocsChecklist()"),
    "missing pre-existing renderDocsChecklist()",
  );
  assert.ok(
    APP_JS.includes("function renderAIDocsChecklist()"),
    "missing new renderAIDocsChecklist() (Day 3)",
  );
});

// ──────────────────────────────────────────────────────────────
// 2. Behavior: sanitizePlanKey
//    Extract the helper source and evaluate it in an isolated VM.
// ──────────────────────────────────────────────────────────────

function extractFunction(name) {
  // Match: function NAME(...) { ... balanced ... }
  // Simple brace counting from the opening `{`.
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

const sandbox = { module: { exports: {} } };
vm.createContext(sandbox);
const source = `
  ${extractFunction("sanitizePlanKey")}
  module.exports.sanitizePlanKey = sanitizePlanKey;
`;
vm.runInContext(source, sandbox);
const { sanitizePlanKey } = sandbox.module.exports;

test("sanitizePlanKey: returns 'default' for non-string inputs", () => {
  assert.equal(sanitizePlanKey(null), "default");
  assert.equal(sanitizePlanKey(undefined), "default");
  assert.equal(sanitizePlanKey(42), "default");
  assert.equal(sanitizePlanKey({}), "default");
});

test("sanitizePlanKey: returns 'default' for empty/whitespace-only after strip", () => {
  assert.equal(sanitizePlanKey(""), "default");
  assert.equal(sanitizePlanKey("!!!@@@###"), "default");
  assert.equal(sanitizePlanKey("   "), "default");
});

test("sanitizePlanKey: preserves the allow-listed charset [a-zA-Z0-9_\\-|]", () => {
  assert.equal(sanitizePlanKey("auxilio-inclusao"), "auxilio-inclusao");
  assert.equal(sanitizePlanKey("bpc|ciptea|escola"), "bpc|ciptea|escola");
  assert.equal(sanitizePlanKey("plan_2026"), "plan_2026");
});

test("sanitizePlanKey: strips dangerous chars (XSS/path traversal vectors)", () => {
  assert.equal(sanitizePlanKey("<script>"), "script");
  assert.equal(sanitizePlanKey("../../etc/passwd"), "etcpasswd");
  assert.equal(sanitizePlanKey("a b c"), "abc");
  assert.equal(sanitizePlanKey('plan";drop"'), "plandrop");
});

test("sanitizePlanKey: enforces 200-char hard cap", () => {
  const long = "a".repeat(500);
  const out = sanitizePlanKey(long);
  assert.equal(out.length, 200);
  assert.equal(out, "a".repeat(200));
});

test("sanitizePlanKey: 200-char cap applies AFTER stripping (no overflow)", () => {
  // 100 valid chars + 100 invalid + 100 valid → 200 valid kept.
  const mixed = "a".repeat(100) + "!".repeat(100) + "b".repeat(100);
  const out = sanitizePlanKey(mixed);
  assert.equal(out, "a".repeat(100) + "b".repeat(100));
  assert.equal(out.length, 200);
});
