#!/usr/bin/env node
/**
 * neutralize_imperatives.mjs (v1.43.0)
 *
 * Converte `passo_a_passo[]` de cada direito do imperativo para infinitivo,
 * para que o texto descreva o PROCEDIMENTO publicado pela fonte oficial em vez
 * de PRESCREVER ação do usuário.
 *
 * Motivação legal: a versão imperativa ("Procure o CRAS") configura orientação
 * de NossoDireito ao usuário. A versão infinitiva ("Procurar o CRAS") descreve
 * o procedimento publicado pelo órgão oficial — o site não orienta, apenas
 * indexa o conteúdo público.
 *
 * Substituições conservadoras (não tocam o conteúdo factual):
 *   Inscreva-se → Realizar inscrição
 *   Procure     → Procurar
 *   Obtenha     → Obter
 *   Agende      → Agendar
 *   Compareça   → Comparecer
 *   Acompanhe   → Acompanhar
 *   Reúna       → Reunir
 *   Identifique → Identificar
 *   Acesse      → Acessar
 *   Dirija-se   → Dirigir-se
 *   Consulte    → Consultar
 *   Solicite    → Solicitar
 *   Verifique   → Verificar
 *   Mantenha    → Manter
 *   Apresente   → Apresentar
 *   Faça        → Realizar
 *   Vá          → Comparecer
 *   Preencha    → Preencher
 *   Leve        → Levar
 *   Envie       → Enviar
 *
 * Uso: node scripts/neutralize_imperatives.mjs
 *   --dry-run  apenas mostra diffs sem gravar
 *   --apply    grava data/direitos.json
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA = resolve(__dirname, '..', 'data', 'direitos.json');

// Mapping: imperativo (capitalizado, início de frase) → infinitivo
// Inclui variantes 1ª/3ª pessoa singular do imperativo afirmativo.
const REPLACEMENTS = [
  // pronominais
  [/^Inscreva-se\b/, 'Realizar inscrição'],
  [/^Dirija-se\b/, 'Dirigir-se'],
  [/^Cadastre-se\b/, 'Realizar cadastro'],
  [/^Informe-se\b/, 'Informar-se'],
  [/^Apresente-se\b/, 'Comparecer'],
  // simples
  [/^Procure\b/, 'Procurar'],
  [/^Obtenha\b/, 'Obter'],
  [/^Agende\b/, 'Agendar'],
  [/^Compareça\b/, 'Comparecer'],
  [/^Acompanhe\b/, 'Acompanhar'],
  [/^Reúna\b/, 'Reunir'],
  [/^Identifique\b/, 'Identificar'],
  [/^Acesse\b/, 'Acessar'],
  [/^Consulte\b/, 'Consultar'],
  [/^Solicite\b/, 'Solicitar'],
  [/^Verifique\b/, 'Verificar'],
  [/^Mantenha\b/, 'Manter'],
  [/^Apresente\b/, 'Apresentar'],
  [/^Faça\b/, 'Realizar'],
  [/^Vá\b/, 'Comparecer a'],
  [/^Preencha\b/, 'Preencher'],
  [/^Leve\b/, 'Levar'],
  [/^Envie\b/, 'Enviar'],
  [/^Aguarde\b/, 'Aguardar'],
  [/^Receba\b/, 'Receber'],
  [/^Imprima\b/, 'Imprimir'],
  [/^Anexe\b/, 'Anexar'],
  [/^Baixe\b/, 'Baixar'],
  [/^Realize\b/, 'Realizar'],
  [/^Atualize\b/, 'Atualizar'],
  [/^Renove\b/, 'Renovar'],
  [/^Pesquise\b/, 'Pesquisar'],
  [/^Escolha\b/, 'Escolher'],
  [/^Marque\b/, 'Marcar'],
  [/^Confirme\b/, 'Confirmar'],
  [/^Pague\b/, 'Pagar'],
  [/^Assine\b/, 'Assinar'],
  [/^Use\b/, 'Utilizar'],
  [/^Tire\b/, 'Tirar'],
  [/^Junte\b/, 'Reunir'],
  [/^Separe\b/, 'Separar'],
  [/^Compre\b/, 'Adquirir'],
  [/^Peça\b/, 'Solicitar'],
  [/^Recorra\b/, 'Apresentar recurso a'],
];

// Itens numerados ("1. Faça X") precisam ter o número preservado
function neutralize(line) {
  // captura prefixo numerado opcional
  const m = line.match(/^(\s*\d+\.\s+)(.*)$/s);
  const prefix = m ? m[1] : '';
  let rest = m ? m[2] : line;

  // 1ª passada: imperativo no INÍCIO da frase (capitalizado)
  for (const [re, repl] of REPLACEMENTS) {
    if (re.test(rest)) {
      rest = rest.replace(re, repl);
      break;
    }
  }

  // 2ª passada: imperativos MID-SENTENCE após conectivo (" e procure", " ou agende", ", solicite")
  // Versão minúscula dos mesmos verbos.
  const MID_PATTERNS = [
    [/(\s|^)(e|ou|e,)\s+inscreva-se\b/gi, '$1$2 realizar inscrição'],
    [/(\s|^)(e|ou|e,)\s+procure\b/gi, '$1$2 procurar'],
    [/(\s|^)(e|ou|e,)\s+obtenha\b/gi, '$1$2 obter'],
    [/(\s|^)(e|ou|e,)\s+agende\b/gi, '$1$2 agendar'],
    [/(\s|^)(e|ou|e,)\s+compareça\b/gi, '$1$2 comparecer'],
    [/(\s|^)(e|ou|e,)\s+acompanhe\b/gi, '$1$2 acompanhar'],
    [/(\s|^)(e|ou|e,)\s+reúna\b/gi, '$1$2 reunir'],
    [/(\s|^)(e|ou|e,)\s+identifique\b/gi, '$1$2 identificar'],
    [/(\s|^)(e|ou|e,)\s+acesse\b/gi, '$1$2 acessar'],
    [/(\s|^)(e|ou|e,)\s+consulte\b/gi, '$1$2 consultar'],
    [/(\s|^)(e|ou|e,)\s+solicite\b/gi, '$1$2 solicitar'],
    [/(\s|^)(e|ou|e,)\s+verifique\b/gi, '$1$2 verificar'],
    [/(\s|^)(e|ou|e,)\s+mantenha\b/gi, '$1$2 manter'],
    [/(\s|^)(e|ou|e,)\s+apresente\b/gi, '$1$2 apresentar'],
    [/(\s|^)(e|ou|e,)\s+faça\b/gi, '$1$2 realizar'],
    [/(\s|^)(e|ou|e,)\s+vá\b/gi, '$1$2 comparecer a'],
    [/(\s|^)(e|ou|e,)\s+preencha\b/gi, '$1$2 preencher'],
    [/(\s|^)(e|ou|e,)\s+leve\b/gi, '$1$2 levar'],
    [/(\s|^)(e|ou|e,)\s+envie\b/gi, '$1$2 enviar'],
    [/(\s|^)(e|ou|e,)\s+aguarde\b/gi, '$1$2 aguardar'],
    [/(\s|^)(e|ou|e,)\s+receba\b/gi, '$1$2 receber'],
    [/(\s|^)(e|ou|e,)\s+atualize\b/gi, '$1$2 atualizar'],
    [/(\s|^)(e|ou|e,)\s+anexe\b/gi, '$1$2 anexar'],
    [/(\s|^)(e|ou|e,)\s+entregue\b/gi, '$1$2 entregar'],
    [/(\s|^)(e|ou|e,)\s+escolha\b/gi, '$1$2 escolher'],
    [/(\s|^)(e|ou|e,)\s+marque\b/gi, '$1$2 marcar'],
    [/(\s|^)(e|ou|e,)\s+pague\b/gi, '$1$2 pagar'],
    [/(\s|^)(e|ou|e,)\s+use\b/gi, '$1$2 utilizar'],
    [/(\s|^)(e|ou|e,)\s+peça\b/gi, '$1$2 solicitar'],
    [/(\s|^)(e|ou|e,)\s+confirme\b/gi, '$1$2 confirmar'],
    [/(\s|^)(e|ou|e,)\s+realize\b/gi, '$1$2 realizar'],
  ];
  for (const [re, repl] of MID_PATTERNS) {
    rest = rest.replace(re, repl);
  }

  return prefix + rest;
}

function main() {
  const args = process.argv.slice(2);
  const apply = args.includes('--apply');
  const dry = args.includes('--dry-run') || !apply;

  const raw = readFileSync(DATA, 'utf8');
  const json = JSON.parse(raw);
  const cats = json.categorias || json;

  let totalChanged = 0;
  let totalLines = 0;
  const samples = [];

  cats.forEach((c) => {
    if (!Array.isArray(c.passo_a_passo)) return;
    c.passo_a_passo = c.passo_a_passo.map((line) => {
      totalLines++;
      const out = neutralize(line);
      if (out !== line) {
        totalChanged++;
        if (samples.length < 8) samples.push({ id: c.id, before: line, after: out });
      }
      return out;
    });
  });

  console.log(`Total de passos: ${totalLines}`);
  console.log(`Passos transformados: ${totalChanged}`);
  console.log(`Passos preservados: ${totalLines - totalChanged}`);
  console.log('\nAmostras:');
  for (const s of samples) {
    console.log(`  [${s.id}]`);
    console.log(`    -- ${s.before}`);
    console.log(`    ++ ${s.after}`);
  }

  if (apply) {
    writeFileSync(DATA, JSON.stringify(json, null, 2) + '\n', 'utf8');
    console.log(`\n✅ Aplicado em ${DATA}`);
  } else if (dry) {
    console.log('\nℹ️  Modo dry-run. Use --apply para gravar.');
  }
}

main();
