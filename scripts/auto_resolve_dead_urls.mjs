#!/usr/bin/env node
/**
 * auto_resolve_dead_urls.mjs
 *
 * Para cada URL com status "error" no validation_report.json, consulta a
 * Wayback Machine API (https://archive.org/wayback/available?url=...) e
 * sugere o snapshot arquivado mais recente como fallback.
 *
 * Não modifica data/direitos.json: gera audit_dead_urls_report.json para o
 * workflow comentar na issue #163 com as sugestões.
 *
 * Estratégia:
 *   1. Lê validation_report.json (produzido por validate_sources.py)
 *   2. Filtra entries onde source=url e status=error
 *   3. Para cada URL, faz GET em
 *      https://archive.org/wayback/available?url=<URL>
 *      (API pública, rate-limited a ~15 req/s — usamos 2 req/s)
 *   4. Coleta archived_snapshots.closest.url se disponível
 *   5. Grava relatório com {original_url, archived_url, http_code, timestamp}
 *
 * Saídas:
 *   stdout            — resumo legível
 *   audit_dead_urls_report.json — sugestões estruturadas
 *
 * Flags:
 *   --input=PATH      — caminho do validation_report.json (default: ./validation_report.json)
 *   --output=PATH     — caminho do report de saída (default: ./audit_dead_urls_report.json)
 *   --rate-ms=N       — intervalo entre requests Wayback (default: 500ms)
 *
 * Exit code: 0 sempre. Workflow lê audit_dead_urls_report.json.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));

// CLI
const args = process.argv.slice(2);
function flag(name, def) {
  const f = args.find((a) => a.startsWith(`--${name}=`));
  return f ? f.split("=").slice(1).join("=") : def;
}
const INPUT = resolve(flag("input", resolve(__dirname, "..", "validation_report.json")));
const OUTPUT = resolve(flag("output", resolve(__dirname, "..", "audit_dead_urls_report.json")));
const RATE_MS = Math.max(100, parseInt(flag("rate-ms", "500"), 10));

const WAYBACK_API = "https://archive.org/wayback/available";

/* Defense-in-depth: validation_report.json é gerado por validate_sources.py
 * a partir de data/direitos.json (schema-validated allowlist .gov.br/.jus.br
 * etc.), mas o arquivo poderia ser commitado adulterado. Como medida extra
 * antes de incluir a URL como query param no Wayback API, validamos que ela
 * é uma URL HTTP(S) bem-formada com host na allowlist oficial brasileira. */
const ALLOWED_HOST_RE = /^(?:[a-z0-9-]+\.)*(?:gov\.br|jus\.br|def\.br|leg\.br|mp\.br|org\.br|edu\.br|com\.br|icd\.who\.int|archive\.org|planalto\.gov\.br)$/i;

function isAllowedUrl(raw) {
  try {
    const u = new URL(raw);
    if (u.protocol !== "https:" && u.protocol !== "http:") return false;
    return ALLOWED_HOST_RE.test(u.hostname);
  } catch {
    return false;
  }
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function queryWayback(url) {
  if (!isAllowedUrl(url)) return { error: "url rejected (host not in allowlist)" };
  const apiUrl = `${WAYBACK_API}?url=${encodeURIComponent(url)}`;
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 10000);
    const resp = await fetch(apiUrl, {
      headers: { "User-Agent": "nossodireito-auto-curation/1.0 (+https://nossodireito.fabiotreze.com)" },
      signal: ctrl.signal,
    });
    clearTimeout(timer);
    if (!resp.ok) return { error: `wayback HTTP ${resp.status}` };
    const data = await resp.json();
    const closest = data?.archived_snapshots?.closest;
    if (!closest || closest.available !== true) {
      return { error: "no snapshot available" };
    }
    return {
      archived_url: closest.url,
      archived_timestamp: closest.timestamp,
      archived_status: closest.status,
    };
  } catch (e) {
    return { error: String(e?.message || e).slice(0, 200) };
  }
}

async function main() {
  if (!existsSync(INPUT)) {
    console.error(`✗ Input não encontrado: ${INPUT}`);
    console.error(`  Rode primeiro: python scripts/validate_sources.py --urls --json > ${INPUT}`);
    // Gera relatório vazio (workflow não comenta nada)
    writeFileSync(
      OUTPUT,
      JSON.stringify(
        {
          generated_at: new Date().toISOString(),
          schema_version: 1,
          input_missing: true,
          dead_urls: [],
        },
        null,
        2
      ) + "\n",
      "utf8"
    );
    process.exit(0);
  }

  const report = JSON.parse(readFileSync(INPUT, "utf8"));
  const deadUrls = (report.results || [])
    .filter((r) => r.source === "url" && r.status === "error" && r.url)
    .map((r) => ({
      original_url: r.url,
      http_code: r.http_code,
      message: r.message,
      item: r.item,
    }));

  console.log("=".repeat(60));
  console.log("auto_resolve_dead_urls.mjs");
  console.log("=".repeat(60));
  console.log(`Input:         ${INPUT}`);
  console.log(`Output:        ${OUTPUT}`);
  console.log(`URLs mortos:   ${deadUrls.length}`);
  console.log(`Rate-limit:    ${RATE_MS}ms entre Wayback calls`);

  const results = [];
  for (let i = 0; i < deadUrls.length; i++) {
    const d = deadUrls[i];
    console.log(`  [${i + 1}/${deadUrls.length}] ${d.original_url.slice(0, 80)}`);
    const wb = await queryWayback(d.original_url);
    results.push({ ...d, ...wb });
    if (i + 1 < deadUrls.length) await sleep(RATE_MS);
  }

  const resolved = results.filter((r) => r.archived_url).length;
  const unresolved = results.length - resolved;

  const output = {
    generated_at: new Date().toISOString(),
    schema_version: 1,
    canonical_version: JSON.parse(
      readFileSync(resolve(__dirname, "..", "package.json"), "utf8")
    ).version,
    summary: {
      total_dead: deadUrls.length,
      resolved_via_wayback: resolved,
      unresolved: unresolved,
      coverage_pct: deadUrls.length ? Math.round((resolved / deadUrls.length) * 1000) / 10 : 0,
    },
    dead_urls: results,
  };

  writeFileSync(OUTPUT, JSON.stringify(output, null, 2) + "\n", "utf8");

  console.log("");
  console.log(`Resolved via Wayback:  ${resolved}/${deadUrls.length} (${output.summary.coverage_pct}%)`);
  console.log(`Unresolved:            ${unresolved}`);
  console.log(`Relatório:             ${OUTPUT}`);
}

main().catch((e) => {
  console.error("Erro fatal:", e);
  process.exit(0); // não falha CI; relatório vazio será criado em próxima run
});
