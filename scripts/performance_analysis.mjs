#!/usr/bin/env node
/**
 * Análise de Performance com Lighthouse
 * Simula: desktop, tablet, mobile
 * Valida:
 * - Performance score
 * - Accessibility score
 * - Best practices
 * - SEO score
 * - Core Web Vitals
 */

import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');

const CONFIGURATIONS = {
  desktop: {
    name: 'Desktop',
    emulationConfig: { mobile: false },
  },
  mobile: {
    name: 'Mobile',
    emulationConfig: { mobile: true },
  },
};

async function runLighthouse(url, config) {
  const options = {
    logLevel: 'error',
    output: 'json',
    onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
    emulationConfig: config.emulationConfig,
  };

  const runnerResult = await lighthouse(url, options);
  return runnerResult.lhr;
}

async function analyzePerformance() {
  const baseUrl = 'file://' + path.join(projectRoot, 'index.html');
  console.log('\n⚡ ANÁLISE DE PERFORMANCE\n');

  const results = {
    timestamp: new Date().toISOString(),
    baseUrl,
    reports: [],
  };

  // Iniciar Chrome
  let chrome;
  try {
    chrome = await chromeLauncher.launch({ chromeFlags: ['--headless', '--no-sandbox'] });

    for (const [configKey, config] of Object.entries(CONFIGURATIONS)) {
      console.log(`📱 Testando em ${config.name}...\n`);

      try {
        const lhr = await runLighthouse(baseUrl, config);

        const scores = {
          performance: lhr.categories.performance.score * 100,
          accessibility: lhr.categories.accessibility.score * 100,
          bestPractices: lhr.categories['best-practices'].score * 100,
          seo: lhr.categories.seo.score * 100,
        };

        console.log('📊 Scores:');
        Object.entries(scores).forEach(([cat, score]) => {
          const icon = score >= 90 ? '🟢' : score >= 70 ? '🟡' : '🔴';
          console.log(`  ${icon} ${cat}: ${score.toFixed(0)}`);
        });

        // Core Web Vitals
        const vitals = {
          lcp: lhr.audits['largest-contentful-paint']?.numericValue || 0,
          fid: lhr.audits['first-input-delay']?.numericValue || 0,
          cls: lhr.audits['cumulative-layout-shift']?.numericValue || 0,
        };

        console.log('\n⏱️ Core Web Vitals:');
        console.log(`  LCP (Largest Contentful Paint): ${vitals.lcp.toFixed(0)}ms`);
        console.log(`  FID (First Input Delay): ${vitals.fid.toFixed(0)}ms`);
        console.log(`  CLS (Cumulative Layout Shift): ${vitals.cls.toFixed(3)}`);

        // Oportunidades
        const opportunities = lhr.categories.performance.auditRefs.filter(
          (a) => lhr.audits[a.id]?.scoreDisplayMode === 'numeric' && lhr.audits[a.id].score < 1
        );

        if (opportunities.length > 0) {
          console.log(`\n💡 Oportunidades de melhoria (top 3):`);
          opportunities.slice(0, 3).forEach((opp) => {
            const audit = lhr.audits[opp.id];
            console.log(`  - ${audit.title}`);
          });
        }

        results.reports.push({
          config: configKey,
          name: config.name,
          scores,
          vitals,
          status: scores.performance >= 70 ? 'PASSOU' : 'CRÍTICO',
        });

        console.log('\n');
      } catch (err) {
        console.error(`❌ Erro ao testar ${config.name}:`, err.message);
        results.reports.push({
          config: configKey,
          name: config.name,
          status: `ERRO: ${err.message}`,
        });
      }
    }
  } finally {
    if (chrome) {
      await chrome.kill();
    }
  }

  // Resumo
  console.log('='.repeat(60));
  console.log('📋 RESUMO DE PERFORMANCE\n');

  results.reports.forEach((report) => {
    const status = report.status === 'PASSOU' ? '✅' : '❌';
    console.log(
      `${status} ${report.name}: ` +
        (report.scores
          ? `Perf=${report.scores.performance.toFixed(0)}, A11y=${report.scores.accessibility.toFixed(0)}, SEO=${report.scores.seo.toFixed(0)}`
          : report.status)
    );
  });

  // Export
  const reportPath = path.join(projectRoot, 'performance_analysis.json');
  fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));
  console.log(`\n📊 Relatório exportado: ${reportPath}\n`);

  return results.reports.every((r) => r.status === 'PASSOU') ? 0 : 1;
}

analyzePerformance().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
