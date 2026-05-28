#!/usr/bin/env node
/**
 * Valida links relativos em README.md e docs/**\/*.md.
 * Falha (exit 1) se algum link apontar para arquivo/diretório inexistente.
 *
 * Motivação:
 * - Incidente 28/mai/2026 (manhã): README/docs referenciavam
 *   docs/REPLICATION.md, COST-ESTIMATE.md, ARCHITECTURE.drawio e 6 outros
 *   arquivos removidos na big-bang cleanup (#170). Lychee só checa externas.
 * - Incidente 28/mai/2026 (tarde): README usava `<img src="images/...png">`
 *   mas o arquivo era `.webp`. Guard v1 só varria `[text](url)` markdown,
 *   passou. v2 também varre `src=`/`href=` HTML inline.
 *
 * Uso:
 *   node scripts/check_doc_links.mjs
 *
 * Considera apenas links que NÃO começam com http(s):// nem mailto: nem #.
 * Tira fragments (#anchor) e query (?...).
 */
import { readFileSync, existsSync } from "node:fs";
import { join, dirname, resolve, relative } from "node:path";
import { glob } from "node:fs/promises";

const ROOT = resolve(new URL("..", import.meta.url).pathname);
// markdown: [text](url) ou [text](url "title")
const MD_LINK_RE = /\[([^\]\n]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g;
// HTML inline em markdown: <img src="..."> | <a href="..."> | <source src="..." srcset="...">
// Captura cada atributo separadamente. srcset pode ter múltiplas URLs.
const HTML_ATTR_RE = /\b(?:src|href|srcset|poster)\s*=\s*"([^"]+)"/gi;

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

  // Coleta candidatos: {raw, source}
  const candidates = [];
  for (const m of content.matchAll(MD_LINK_RE)) {
    candidates.push({ raw: m[2], source: "md" });
  }
  for (const m of content.matchAll(HTML_ATTR_RE)) {
    // srcset pode ter "url1 200w, url2 400w" — split por vírgula e pega só URL
    for (const part of m[1].split(",")) {
      const url = part.trim().split(/\s+/)[0];
      if (url) candidates.push({ raw: url, source: "html" });
    }
  }

  for (const { raw, source } of candidates) {
    if (/^(https?:|mailto:|tel:|#|data:)/i.test(raw)) continue;
    // remove fragment + query
    const cleaned = raw.split("#")[0].split("?")[0];
    if (!cleaned) continue;
    // URLs absolutas começando com / são relativas à raiz do projeto
    const targetAbs = cleaned.startsWith("/")
      ? join(ROOT, cleaned.slice(1))
      : resolve(baseDir, cleaned);
    if (!existsSync(targetAbs)) {
      broken.push({ file: relFile, link: raw, target: relative(ROOT, targetAbs), source });
    }
  }
}

if (broken.length > 0) {
  console.error(`❌ ${broken.length} link(s) relativo(s) quebrado(s):\n`);
  for (const b of broken) {
    console.error(`  ${b.file} → ${b.link}  [${b.source}]`);
    console.error(`    (resolveria para: ${b.target})`);
  }
  console.error("\nCorrija os links ou recrie os arquivos faltantes.");
  process.exit(1);
}

console.log("✅ Todos os links relativos em README/docs apontam para arquivos existentes.");
