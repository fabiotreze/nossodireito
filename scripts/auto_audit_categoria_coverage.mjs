#!/usr/bin/env node
/**
 * auto_audit_categoria_coverage.mjs
 *
 * Issue #164: detecta categorias com campos opcionais sistematicamente
 * vazios e gera matriz de cobertura.
 *
 * Lê schemas/direitos.schema.json e data/direitos.json e produz:
 *
 *   1. Matriz por campo opcional × categoria (presente/ausente)
 *   2. Lista de campos opcionais "sub-utilizados" (presentes em < N% das categorias)
 *   3. Lista de categorias que "deveriam" preencher determinado campo
 *      (heurística: se 80% das categorias do mesmo `aplicabilidade` preenchem,
 *      o restante vira candidato).
 *
 * NÃO modifica data/direitos.json. Apenas grava audit_coverage_report.json
 * para o workflow comentar na issue #164.
 *
 * Saídas:
 *   stdout                       — resumo legível
 *   audit_coverage_report.json   — matriz e candidatos estruturados
 *
 * Flags:
 *   --min-pct=N    — threshold para considerar campo "esperado" (default: 80)
 *   --output=PATH  — caminho do relatório (default: ./audit_coverage_report.json)
 */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));

// CLI
const args = process.argv.slice(2);
function flag(name, def) {
  const f = args.find((a) => a.startsWith(`--${name}=`));
  return f ? f.split("=").slice(1).join("=") : def;
}
const MIN_PCT = Math.max(50, Math.min(100, parseInt(flag("min-pct", "80"), 10)));
const OUTPUT = resolve(flag("output", resolve(__dirname, "..", "audit_coverage_report.json")));

const SCHEMA = resolve(__dirname, "..", "schemas", "direitos.schema.json");
const DATA = resolve(__dirname, "..", "data", "direitos.json");

// ─────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────
function isEmpty(v) {
  if (v === null || v === undefined) return true;
  if (typeof v === "string") return v.trim() === "";
  if (Array.isArray(v)) return v.length === 0;
  if (typeof v === "object") return Object.keys(v).length === 0;
  return false;
}

function main() {
  const schema = JSON.parse(readFileSync(SCHEMA, "utf8"));
  const data = JSON.parse(readFileSync(DATA, "utf8"));
  const cats = data.categorias || data;

  const catSchema = schema.definitions?.categoria;
  if (!catSchema) {
    console.error("✗ definitions.categoria não encontrado no schema");
    process.exit(1);
  }
  const required = new Set(catSchema.required || []);
  const allProps = Object.keys(catSchema.properties || {});
  const optionalProps = allProps.filter((p) => !required.has(p));

  // Matriz: optionalProp × {totalPresent, byAplicabilidade: {tipo: {present, total}}}
  const matrix = {};
  for (const p of optionalProps) {
    matrix[p] = { total_present: 0, total_categorias: cats.length, by_aplicabilidade: {} };
  }

  for (const cat of cats) {
    const aplic = cat.aplicabilidade || "unspecified";
    for (const p of optionalProps) {
      const present = !isEmpty(cat[p]);
      if (present) matrix[p].total_present += 1;

      if (!matrix[p].by_aplicabilidade[aplic]) {
        matrix[p].by_aplicabilidade[aplic] = { present: 0, total: 0 };
      }
      matrix[p].by_aplicabilidade[aplic].total += 1;
      if (present) matrix[p].by_aplicabilidade[aplic].present += 1;
    }
  }

  // Identifica "sub-utilizados" (< 10% cobertura) e "esperados" (>= MIN_PCT no mesmo aplicabilidade)
  const subutilizados = [];
  const candidatos_preenchimento = [];

  for (const p of optionalProps) {
    const cov = matrix[p];
    const pct = cov.total_categorias ? (cov.total_present / cov.total_categorias) * 100 : 0;
    cov.coverage_pct = Math.round(pct * 10) / 10;
    if (cov.coverage_pct < 10) {
      subutilizados.push({ campo: p, present: cov.total_present, pct: cov.coverage_pct });
    }
    // por aplicabilidade: se grupo tem ≥ MIN_PCT cobertura, categorias do grupo com campo vazio viram candidatos
    for (const [aplic, stats] of Object.entries(cov.by_aplicabilidade)) {
      if (stats.total < 3) continue; // grupo pequeno, ignora
      const groupPct = (stats.present / stats.total) * 100;
      if (groupPct >= MIN_PCT && stats.present < stats.total) {
        // listar quem está sem
        const missing = cats
          .filter((c) => (c.aplicabilidade || "unspecified") === aplic && isEmpty(c[p]))
          .map((c) => c.id);
        for (const id of missing) {
          candidatos_preenchimento.push({
            campo: p,
            categoria_id: id,
            aplicabilidade: aplic,
            grupo_cobertura_pct: Math.round(groupPct * 10) / 10,
          });
        }
      }
    }
  }

  const report = {
    generated_at: new Date().toISOString(),
    schema_version: 1,
    canonical_version: JSON.parse(readFileSync(resolve(__dirname, "..", "package.json"), "utf8")).version,
    config: { min_pct: MIN_PCT },
    summary: {
      total_categorias: cats.length,
      total_required_fields: required.size,
      total_optional_fields: optionalProps.length,
      subutilizados: subutilizados.length,
      candidatos_preenchimento: candidatos_preenchimento.length,
    },
    matriz_cobertura: matrix,
    subutilizados,
    candidatos_preenchimento: candidatos_preenchimento.slice(0, 200),
    candidatos_truncated: candidatos_preenchimento.length > 200,
  };

  writeFileSync(OUTPUT, JSON.stringify(report, null, 2) + "\n", "utf8");

  // stdout
  console.log("=".repeat(60));
  console.log("auto_audit_categoria_coverage.mjs");
  console.log("=".repeat(60));
  console.log(`Categorias:                    ${cats.length}`);
  console.log(`Required fields:               ${required.size}`);
  console.log(`Optional fields:               ${optionalProps.length}`);
  console.log(`Sub-utilizados (<10% cov):     ${subutilizados.length}`);
  console.log(`Candidatos preenchimento:      ${candidatos_preenchimento.length}`);
  console.log(`Relatório:                     ${OUTPUT}`);

  if (subutilizados.length > 0) {
    console.log("\nSub-utilizados (amostra):");
    for (const s of subutilizados.slice(0, 5)) {
      console.log(`  - ${s.campo}: ${s.present}/${cats.length} (${s.pct}%)`);
    }
  }
  if (candidatos_preenchimento.length > 0) {
    console.log("\nCandidatos a preenchimento (amostra):");
    for (const c of candidatos_preenchimento.slice(0, 5)) {
      console.log(`  - [${c.categoria_id}] campo '${c.campo}' (grupo '${c.aplicabilidade}' tem ${c.grupo_cobertura_pct}% de cobertura)`);
    }
  }
}

main();
