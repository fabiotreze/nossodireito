#!/usr/bin/env node
/**
 * Valida links relativos em README.md e docs/**\/*.md.
 * Falha (exit 1) se algum link apontar para arquivo/diretório inexistente.
 *
 * Motivação: incidente 28/mai/2026 — README/docs ainda referenciavam
 * docs/REPLICATION.md, COST-ESTIMATE.md, ARCHITECTURE.drawio e 6 outros
 * arquivos removidos na big-bang cleanup (#170). Lychee só checa externas.
 *
 * Uso:
 *   node scripts/check_doc_links.mjs
 *
 * Considera apenas links que NÃO começam com http(s):// nem mailto: nem #.
 * Tira fragments (#anchor) e query (?...).
 */
import { readFileSync, existsSync, statSync } from "node:fs";
import { join, dirname, resolve, relative } from "node:path";
import { glob } from "node:fs/promises";

const ROOT = resolve(new URL("..", import.meta.url).pathname);
const LINK_RE = /\[([^\]\n]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g;

const broken = [];

async function collectFiles() {
  const files = ["README.md"];
  for await (const entry of glob("docs/**/*.md", { cwd: ROOT })) {
    files.push(entry);
  }
  return files;
}

for (const relFile of await collectFiles()) {
  const abs = join(ROOT, relFile);
  if (!existsSync(abs)) continue;
  const content = readFileSync(abs, "utf8");
  const baseDir = dirname(abs);

  for (const m of content.matchAll(LINK_RE)) {
    const raw = m[2];
    if (/^(https?:|mailto:|tel:|#|data:)/i.test(raw)) continue;
    // remove fragment + query
    const cleaned = raw.split("#")[0].split("?")[0];
    if (!cleaned) continue;
    const targetAbs = resolve(baseDir, cleaned);
    if (!existsSync(targetAbs)) {
      broken.push({ file: relFile, link: raw, target: relative(ROOT, targetAbs) });
    }
  }
}

if (broken.length > 0) {
  console.error(`❌ ${broken.length} link(s) relativo(s) quebrado(s):\n`);
  for (const b of broken) {
    console.error(`  ${b.file} → ${b.link}`);
    console.error(`    (resolveria para: ${b.target})`);
  }
  console.error("\nCorrija os links ou recrie os arquivos faltantes.");
  process.exit(1);
}

console.log("✅ Todos os links relativos em README/docs apontam para arquivos existentes.");
