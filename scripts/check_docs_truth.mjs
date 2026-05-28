#!/usr/bin/env node
/**
 * Guard de verdade da documentação.
 *
 * Falha (exit 1) se README/docs/*.md, CONTRIBUTING.md, GOVERNANCE.md,
 * SECURITY.md ou SECURITY_AUDIT.md voltarem a mencionar tokens que correspondem
 * a arquivos/conceitos REMOVIDOS do repo (PWA, master_compliance, .yml.disabled,
 * scripts/legacy, ARCHITECTURE.drawio, CHANGELOG.md, KNOWN_ISSUES.md, etc.).
 *
 * Motivação: incidente 28/mai/2026 — após PR #170 (big-bang cleanup) os docs
 * continuaram afirmando coisas que não existem mais (PWA offline, score
 * "1248.5/1268.5", "14 .yml.disabled", "scripts/legacy/"). Sem guard, esse
 * drift cresce a cada release.
 *
 * Como funciona:
 *  - Cada regra tem `pattern` (literal ou regex) e `reason`.
 *  - Se a regra tem `existsHint`, a violação é IGNORADA caso o arquivo apontado
 *    realmente exista no repo (permite restaurar feature + manter doc).
 *  - Allowlist: linhas marcadas com `<!-- docs-truth: allow -->` no fim da
 *    linha são ignoradas (use parcimoniosamente, ex: comentário histórico).
 *
 * Uso:
 *   node scripts/check_docs_truth.mjs
 *
 * Mantenha esta lista curta. Cada item aqui é uma cicatriz de drift real.
 */
import { readFileSync, existsSync } from "node:fs";
import { resolve, relative } from "node:path";
import { glob } from "node:fs/promises";

const ROOT = resolve(new URL("..", import.meta.url).pathname);

// Cada regra é uma promessa: "se isto aparecer em docs, é mentira (a menos que
// o arquivo opcional `existsHint` exista — então o feature voltou e está OK)."
const RULES = [
  {
    pattern: /\bsw\.js\b/g,
    existsHint: "sw.js",
    reason: "Service Worker foi removido em #170. Não citar sw.js em docs.",
  },
  {
    pattern: /\bmanifest\.json\b/g,
    existsHint: "manifest.json",
    reason: "manifest PWA removido em #170.",
  },
  {
    pattern: /\bsw-register\.js\b/g,
    existsHint: "js/sw-register.js",
    reason: "Registro de SW removido em #170.",
  },
  {
    pattern: /\bmaster_compliance(\.py)?\b/g,
    existsHint: "scripts/master_compliance.py",
    reason: "Substituído por scripts/validate_all.py. Referencie validate_all.",
  },
  {
    pattern: /scripts\/legacy\//g,
    existsHint: "scripts/legacy",
    reason: "Pasta scripts/legacy/ não existe (removida em #170).",
  },
  {
    pattern: /\.yml\.disabled\b/g,
    reason: "Workflows .yml.disabled foram apagados em #170. Não há cemitério.",
  },
  {
    pattern: /\bARCHITECTURE\.drawio\b/g,
    existsHint: "docs/ARCHITECTURE.drawio",
    reason: "Diagrama drawio raiz foi removido (use docs/diagrams/*.drawio).",
  },
  {
    pattern: /docs\/CONTRIBUTING\.md/g,
    existsHint: "docs/CONTRIBUTING.md",
    reason: "docs/CONTRIBUTING.md foi removido. Use a raiz CONTRIBUTING.md.",
  },
  {
    pattern: /docs\/COMPLIANCE\.md/g,
    existsHint: "docs/COMPLIANCE.md",
    reason: "docs/COMPLIANCE.md não existe. Compliance descrito em README/quality-gate.",
  },
  {
    pattern: /docs\/KNOWN_ISSUES\.md/g,
    existsHint: "docs/KNOWN_ISSUES.md",
    reason: "docs/KNOWN_ISSUES.md não existe.",
  },
  {
    pattern: /docs\/AGENTS\.md/g,
    existsHint: "docs/AGENTS.md",
    reason: "docs/AGENTS.md não existe.",
  },
  {
    pattern: /\bscripts\/bump_version\.py\b/g,
    existsHint: "scripts/bump_version.py",
    reason: "scripts/bump_version.py não existe.",
  },
  {
    pattern: /\bindex\.min\.html\b/g,
    existsHint: "index.min.html",
    reason: "index.min.html não existe. Não há build minificado separado.",
  },
  {
    pattern: /CHANGELOG\.md/g,
    existsHint: "CHANGELOG.md",
    reason: "CHANGELOG.md foi removido em #170 (use git log / releases).",
  },
  {
    pattern: /\b1248\.5\s*\/\s*1268\.5\b/g,
    reason: "Score 1248.5/1268.5 do master_compliance é histórico e não verificável.",
  },
  {
    pattern: /\b36 categorias\b/gi,
    reason: "\"36 categorias\" do master_compliance não bate com validate_all.py atual.",
  },
  {
    pattern: /\bPWA\b/g,
    reason: "PWA foi removido em #170. Use 'app web' / 'site responsivo'.",
  },
  {
    pattern: /funciona offline|offline support|offline mode|fallback offline/gi,
    reason: "App não funciona offline desde #170 (sem service worker).",
  },
];

const FILES_GLOBS = ["*.md", "docs/**/*.md"];
const ALLOW_MARK = "<!-- docs-truth: allow -->";

async function collectFiles() {
  const out = new Set();
  for (const pat of FILES_GLOBS) {
    for await (const entry of glob(pat, { cwd: ROOT })) {
      out.add(entry);
    }
  }
  return [...out].sort();
}

const violations = [];

for (const rel of await collectFiles()) {
  const abs = resolve(ROOT, rel);
  if (!existsSync(abs)) continue;
  const text = readFileSync(abs, "utf8");
  const lines = text.split("\n");

  for (const rule of RULES) {
    // Se a feature foi restaurada (arquivo existe), pular regra.
    if (rule.existsHint && existsSync(resolve(ROOT, rule.existsHint))) continue;

    rule.pattern.lastIndex = 0;
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.includes(ALLOW_MARK)) continue;
      // Resetar lastIndex para cada linha (regex /g é stateful).
      const re = new RegExp(rule.pattern.source, rule.pattern.flags);
      if (re.test(line)) {
        violations.push({
          file: rel,
          line: i + 1,
          excerpt: line.trim().slice(0, 120),
          reason: rule.reason,
        });
      }
    }
  }
}

if (violations.length > 0) {
  console.error(`❌ ${violations.length} violação(ões) de drift de docs:\n`);
  for (const v of violations) {
    console.error(`  ${v.file}:${v.line}`);
    console.error(`    motivo: ${v.reason}`);
    console.error(`    linha : ${v.excerpt}`);
  }
  console.error(
    `\nCorrija o texto, ou — se a feature foi restaurada — recrie o arquivo correspondente.\n` +
      `Casos legítimos (ex.: contexto histórico) podem usar o marcador ${ALLOW_MARK} ao fim da linha.`,
  );
  process.exit(1);
}

console.log("✅ Docs sincronizados com o estado real do repositório.");
