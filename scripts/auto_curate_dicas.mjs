#!/usr/bin/env node
/**
 * auto_curate_dicas.mjs
 *
 * Automação semanal: detecta e neutraliza padrões prescritivos em `dicas[]`
 * de data/direitos.json. Complementa neutralize_imperatives.mjs (que cobre
 * passo_a_passo[]).
 *
 * Estratégia em duas fases:
 *
 *   FASE A — auto-fix seguro (determinístico):
 *     Remove sufixos de boilerplate idênticos que aparecem em ≥ MIN_REPEATS
 *     categorias (ex.: "Se seus direitos forem negados, denuncie pelo Disque
 *     100 (24h, gratuito) ou WhatsApp (61) 99611-0100"). Esses são avisos
 *     genéricos colados em massa, não conteúdo factual do direito.
 *
 *   FASE B — detecção (relatório):
 *     Identifica dicas com padrões prescritivos remanescentes (verbos
 *     imperativos, "Se negado...", "peça...", "denuncie...", "ligue...")
 *     e grava em audit_dicas_report.json para virar comentário em issue.
 *     NÃO modifica conteúdo — apenas lista candidatos.
 *
 * Saídas:
 *   stdout            — resumo legível
 *   audit_dicas_report.json — relatório estruturado (sempre gravado)
 *   data/direitos.json — modificado SE --apply e FASE A encontrou boilerplate
 *
 * Flags:
 *   --apply           — grava data/direitos.json (default: dry-run)
 *   --min-repeats=N   — threshold para considerar boilerplate (default: 3)
 *   --report-only     — pula FASE A, só gera relatório
 *
 * Exit code: 0 sempre. Workflow lê audit_dicas_report.json para decidir PR/issue.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA = resolve(__dirname, "..", "data", "direitos.json");
const REPORT = resolve(__dirname, "..", "audit_dicas_report.json");

// ─────────────────────────────────────────────────────────────
// CLI
// ─────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const APPLY = args.includes("--apply");
const REPORT_ONLY = args.includes("--report-only");
const MIN_REPEATS = (() => {
  const flag = args.find((a) => a.startsWith("--min-repeats="));
  return flag ? Math.max(2, parseInt(flag.split("=")[1], 10) || 3) : 3;
})();

// ─────────────────────────────────────────────────────────────
// Patterns
// ─────────────────────────────────────────────────────────────
/**
 * Regex que identifica uma dica como "prescritiva" (orientação ao usuário).
 * Conservador: prefere falso negativo a falso positivo.
 */
const PRESCRIPTIVE_PATTERNS = [
  // Verbos imperativos no início (capitalizado)
  /^(Peça|Solicite|Procure|Ligue|Denuncie|Compareça|Acesse|Recorra|Mantenha|Verifique|Anote|Guarde|Pergunte|Cadastre-se|Inscreva-se|Tire|Marque|Pague|Use|Faça|Realize|Atualize|Obtenha|Agende|Acompanhe|Reúna|Identifique|Consulte|Apresente|Confirme|Entregue|Junte|Separe|Compre|Imprima|Anexe|Baixe|Preencha|Leve|Envie|Aguarde|Receba|Escolha|Pesquise|Renove)\b/,
  // Conectivos prescritivos
  /^Se\s+(negado|recusado|indeferido|seus\s+direitos)/i,
  // Promessas de direito ("você terá", "você tem")
  /\bvocê\s+(tem|terá|tem direito|deve|pode)\b/i,
  // Recomendações disfarçadas
  /\b(é\s+importante|recomenda-se|sugere-se|orienta-se|aconselha-se)\b/i,
];

/**
 * Boilerplates conhecidos para FASE A — strings (ou regex) idênticas
 * coladas em massa que devem ser removidas como sufixo de dica.
 * Adicione novos padrões aqui após observar via FASE B.
 */
const BOILERPLATE_SUFFIXES = [
  // Disque 100 / WhatsApp denúncia — encontrado em dezenas de dicas
  /^Se\s+seus\s+direitos\s+forem\s+negados,?\s+denuncie\s+pelo\s+Disque\s+100[^"]*$/i,
];

// ─────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────

/** True se dica casa algum padrão prescritivo. */
function isPrescriptive(dica) {
  if (typeof dica !== "string") return false;
  return PRESCRIPTIVE_PATTERNS.some((re) => re.test(dica));
}

/** True se dica inteira é boilerplate genérico (não específico do direito). */
function isBoilerplate(dica) {
  if (typeof dica !== "string") return false;
  return BOILERPLATE_SUFFIXES.some((re) => re.test(dica));
}

/** Conta ocorrências exatas de cada dica no dataset (para detectar boilerplate). */
function countDuplicates(cats) {
  const counts = new Map();
  for (const c of cats) {
    if (!Array.isArray(c.dicas)) continue;
    for (const d of c.dicas) {
      if (typeof d !== "string") continue;
      counts.set(d, (counts.get(d) || 0) + 1);
    }
  }
  return counts;
}

// ─────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────

function main() {
  const raw = readFileSync(DATA, "utf8");
  const json = JSON.parse(raw);
  const cats = json.categorias || json;

  const counts = countDuplicates(cats);

  // FASE A — remoção de boilerplate
  let totalDicas = 0;
  let removedBoilerplate = 0;
  const boilerplateRemoved = []; // {id, dica}

  if (!REPORT_ONLY) {
    for (const c of cats) {
      if (!Array.isArray(c.dicas)) continue;
      const before = c.dicas.length;
      c.dicas = c.dicas.filter((d) => {
        totalDicas++;
        if (isBoilerplate(d) || (counts.get(d) >= MIN_REPEATS && isPrescriptive(d))) {
          boilerplateRemoved.push({ id: c.id, dica: d, occurrences: counts.get(d) });
          return false;
        }
        return true;
      });
      removedBoilerplate += before - c.dicas.length;
    }
  } else {
    for (const c of cats) {
      if (Array.isArray(c.dicas)) totalDicas += c.dicas.length;
    }
  }

  // FASE B — detecção de prescritivas remanescentes
  const candidates = []; // {id, titulo, index, dica, reason}
  for (const c of cats) {
    if (!Array.isArray(c.dicas)) continue;
    c.dicas.forEach((d, i) => {
      if (isPrescriptive(d)) {
        const matchedPattern = PRESCRIPTIVE_PATTERNS.find((re) => re.test(d));
        candidates.push({
          id: c.id,
          titulo: c.titulo,
          index: i,
          dica: d,
          pattern: matchedPattern ? matchedPattern.toString().slice(0, 80) : "unknown",
        });
      }
    });
  }

  // Relatório estruturado
  const report = {
    generated_at: new Date().toISOString(),
    schema_version: 1,
    canonical_version: JSON.parse(readFileSync(resolve(__dirname, "..", "package.json"), "utf8")).version,
    config: { apply: APPLY, report_only: REPORT_ONLY, min_repeats: MIN_REPEATS },
    summary: {
      total_categorias: cats.length,
      total_dicas: totalDicas,
      boilerplate_removed: removedBoilerplate,
      prescriptive_remaining: candidates.length,
      ratio_pct: totalDicas ? Math.round((candidates.length / totalDicas) * 1000) / 10 : 0,
    },
    auto_applied: boilerplateRemoved.slice(0, 50), // cap p/ não inchar
    manual_candidates: candidates.slice(0, 200), // cap p/ não inchar issue
    manual_candidates_truncated: candidates.length > 200,
  };

  writeFileSync(REPORT, JSON.stringify(report, null, 2) + "\n", "utf8");

  // Stdout legível
  console.log("=".repeat(60));
  console.log("auto_curate_dicas.mjs — relatório");
  console.log("=".repeat(60));
  console.log(`Categorias analisadas:    ${cats.length}`);
  console.log(`Dicas totais:             ${totalDicas}`);
  console.log(`Boilerplate removido:     ${removedBoilerplate} (FASE A)`);
  console.log(`Prescritivas restantes:   ${candidates.length} (FASE B)`);
  console.log(`Ratio prescritivo:        ${report.summary.ratio_pct}%`);
  console.log(`Relatório:                ${REPORT}`);

  if (boilerplateRemoved.length > 0) {
    console.log("\nFASE A — boilerplate removido (amostra):");
    for (const b of boilerplateRemoved.slice(0, 3)) {
      console.log(`  [${b.id}] (${b.occurrences}x) ${b.dica.slice(0, 80)}…`);
    }
  }
  if (candidates.length > 0) {
    console.log("\nFASE B — candidatos prescritivos (amostra):");
    for (const c of candidates.slice(0, 5)) {
      console.log(`  [${c.id}#${c.index}] ${c.dica.slice(0, 80)}…`);
    }
  }

  if (APPLY && removedBoilerplate > 0) {
    writeFileSync(DATA, JSON.stringify(json, null, 2) + "\n", "utf8");
    console.log(`\n✅ Aplicado em ${DATA} (${removedBoilerplate} dicas removidas)`);
  } else if (!APPLY) {
    console.log("\nℹ️  Modo dry-run. Use --apply para gravar.");
  } else {
    console.log("\nℹ️  Nada a aplicar (zero boilerplate detectado).");
  }
}

main();
