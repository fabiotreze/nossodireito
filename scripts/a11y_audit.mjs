// scripts/a11y_audit.mjs
// Roda axe-core via Playwright nas 10 páginas mais importantes do nossodireito.
// Saída: tabela markdown ordenada por impacto + JSON detalhado em /tmp/nd_a11y.json
import { chromium } from 'playwright';
import { AxeBuilder } from '@axe-core/playwright';
import { writeFileSync } from 'fs';

const BASE = process.env.NOSSODIREITO_URL || 'http://127.0.0.1:8765';

// 10 páginas representativas: home, busca, top-5 categorias estratégicas + 3 categorias variadas
const PAGES = [
  { name: 'home', url: '/' },
  { name: 'bpc', url: '/direitos/bpc/' },
  { name: 'isencao_ir', url: '/direitos/isencao_ir/' },
  { name: 'auxilio_inclusao', url: '/direitos/auxilio_inclusao/' },
  { name: 'educacao', url: '/direitos/educacao/' },
  { name: 'transporte', url: '/direitos/transporte/' },
  { name: 'sus_terapias', url: '/direitos/sus_terapias/' },
  { name: 'meia_entrada', url: '/direitos/meia_entrada/' },
  { name: 'estacionamento_especial', url: '/direitos/estacionamento_especial/' },
  { name: 'acessibilidade_digital', url: '/direitos/acessibilidade_digital/' },
];

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext();
const allViolations = [];

for (const p of PAGES) {
  const page = await ctx.newPage();
  const url = BASE + p.url;
  try {
    const resp = await page.goto(url, { waitUntil: 'networkidle', timeout: 20000 });
    if (!resp || !resp.ok()) {
      console.error(`[skip] ${p.name}: HTTP ${resp?.status()}`);
      await page.close();
      continue;
    }
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice'])
      .analyze();
    for (const v of results.violations) {
      allViolations.push({
        page: p.name,
        url: p.url,
        id: v.id,
        impact: v.impact,
        help: v.help,
        helpUrl: v.helpUrl,
        tags: v.tags,
        nodes: v.nodes.length,
        sample: v.nodes[0]?.target || []
      });
    }
    console.error(`[ok]   ${p.name}: ${results.violations.length} violações`);
  } catch (err) {
    console.error(`[err]  ${p.name}: ${err.message}`);
  } finally {
    await page.close();
  }
}

await browser.close();

// Agrupar e ordenar por impacto
const RANK = { critical: 0, serious: 1, moderate: 2, minor: 3, null: 4, undefined: 4 };
const grouped = new Map();
for (const v of allViolations) {
  const k = v.id;
  if (!grouped.has(k)) grouped.set(k, { ...v, pages: new Set(), totalNodes: 0 });
  const g = grouped.get(k);
  g.pages.add(v.page);
  g.totalNodes += v.nodes;
}
const sorted = [...grouped.values()]
  .map(g => ({ ...g, pages: [...g.pages] }))
  .sort((a, b) => RANK[a.impact] - RANK[b.impact] || b.totalNodes - a.totalNodes);

writeFileSync('/tmp/nd_a11y.json', JSON.stringify({
  base: BASE, pages: PAGES.length, total_violations: allViolations.length,
  by_rule: sorted
}, null, 2));

// Print tabela markdown
console.log('\n# Auditoria axe-core a11y\n');
console.log(`**Base:** ${BASE}  |  **Páginas:** ${PAGES.length}  |  **Total de instâncias:** ${allViolations.reduce((a,v)=>a+v.nodes,0)}  |  **Regras únicas violadas:** ${sorted.length}\n`);
console.log('| # | Impacto | Regra | Nodes | Páginas afetadas | Help |');
console.log('|---:|---|---|---:|---|---|');
sorted.slice(0, 20).forEach((v, i) => {
  console.log(`| ${i+1} | ${v.impact || '-'} | \`${v.id}\` | ${v.totalNodes} | ${v.pages.length} (${v.pages.slice(0,3).join(', ')}${v.pages.length>3?'…':''}) | ${v.help} |`);
});
