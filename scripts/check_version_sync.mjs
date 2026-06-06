#!/usr/bin/env node
/**
 * check_version_sync.mjs — garante que a versão semântica esteja sincronizada
 * em todos os pontos do repositório que carregam versão visível ao usuário,
 * ao deploy ou ao cache do browser.
 *
 * Motivação: ao bumpar `data/direitos.json` no PR #207 sem atualizar
 * `package.json`, `/health` ficou divergente do rodapé do site. Este script
 * detecta esse drift no CI antes do merge.
 *
 * Fonte canônica: `package.json#version`.
 *
 * Uso: `node scripts/check_version_sync.mjs` (exit 0 se OK; exit 1 se drift).
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));

function read(rel) {
  return readFileSync(join(ROOT, rel), "utf8");
}

const pkg = JSON.parse(read("package.json"));
const CANONICAL = pkg.version;

if (!CANONICAL || !/^\d+\.\d+\.\d+$/.test(CANONICAL)) {
  console.error(`✗ package.json#version inválida: "${CANONICAL}"`);
  process.exit(1);
}

// [arquivo, regex-com-captura, descrição]. A captura DEVE ser o número da versão.
const checks = [
  ["data/direitos.json", /"versao"\s*:\s*"([0-9]+\.[0-9]+\.[0-9]+)"/, 'data/direitos.json "versao"'],
  ["data/dicionario_pcd.json", /"versao"\s*:\s*"([0-9]+\.[0-9]+\.[0-9]+)"/, 'data/dicionario_pcd.json "versao"'],
  ["docs/README.md", /\*\*Versão:\*\*\s*([0-9]+\.[0-9]+\.[0-9]+)/, "docs/README.md header"],
  ["docs/ARCHITECTURE.md", /\*\*Versão:\*\*\s*([0-9]+\.[0-9]+\.[0-9]+)/, "docs/ARCHITECTURE.md header"],
  ["docs/OPERATIONS.md", /\*\*Versão:\*\*\s*([0-9]+\.[0-9]+\.[0-9]+)/, "docs/OPERATIONS.md header"],
  ["docs/SECURITY-LGPD.md", /\*\*Versão:\*\*\s*([0-9]+\.[0-9]+\.[0-9]+)/, "docs/SECURITY-LGPD.md header"],
  ["GOVERNANCE.md", /\*\*Versão:\*\*\s*([0-9]+\.[0-9]+\.[0-9]+)/, "GOVERNANCE.md header"],
  ["SECURITY_AUDIT.md", /Auditoria de Segurança v([0-9]+\.[0-9]+\.[0-9]+)/, "SECURITY_AUDIT.md title"],
  ["js/tos-banner.js", /var\s+TOS_VERSION\s*=\s*['"]([0-9]+\.[0-9]+\.[0-9]+)['"]/, "js/tos-banner.js TOS_VERSION"],
];

// index.html tem 3 cache-busters (?v=X.Y.Z). Validamos todos.
const indexHtml = read("index.html");
const cacheBusters = [...indexHtml.matchAll(/[?&]v=([0-9]+\.[0-9]+\.[0-9]+)/g)].map((m) => m[1]);

// README.md tem múltiplos títulos com (vX.Y.Z) — validamos todos.
const readme = read("README.md");
const readmeVersions = [...readme.matchAll(/\(v([0-9]+\.[0-9]+\.[0-9]+)\)/g)].map((m) => m[1]);

const drifts = [];

for (const [file, rx, label] of checks) {
  const content = read(file);
  const match = content.match(rx);
  if (!match) {
    drifts.push(`  ✗ ${label}: padrão não encontrado em ${file}`);
    continue;
  }
  if (match[1] !== CANONICAL) {
    drifts.push(`  ✗ ${label}: "${match[1]}" ≠ canonical "${CANONICAL}"`);
  }
}

if (cacheBusters.length === 0) {
  drifts.push("  ✗ index.html: nenhum cache-buster ?v=X.Y.Z encontrado");
} else {
  cacheBusters.forEach((v, i) => {
    if (v !== CANONICAL) {
      drifts.push(`  ✗ index.html cache-buster #${i + 1}: "${v}" ≠ canonical "${CANONICAL}"`);
    }
  });
}

readmeVersions.forEach((v, i) => {
  if (v !== CANONICAL) {
    drifts.push(`  ✗ README.md título com versão #${i + 1}: "${v}" ≠ canonical "${CANONICAL}"`);
  }
});

if (drifts.length === 0) {
  console.log(`✓ versão sincronizada em todos os pontos (canonical: ${CANONICAL})`);
  process.exit(0);
}

console.error(`✗ drift de versão detectado (canonical em package.json: ${CANONICAL}):`);
drifts.forEach((d) => console.error(d));
console.error("\nDica: bumpe os arquivos divergentes para alinhar com package.json#version.");
process.exit(1);
