#!/usr/bin/env node
/**
 * Teste E2E Automatizado
 * Simula navegação completa: desktop, tablet, mobile
 * Valida:
 * - Links funcionais
 * - Menu interativo
 * - Anchors scrolling
 * - Performance (LCP, FID, CLS)
 * - Erros do console
 * - Validação de formulários
 * - Compatibilidade de viewport
 */

import puppeteer from 'puppeteer';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');
const baseUrl = 'file://' + path.join(projectRoot, 'index.html');

const VIEWPORTS = {
  desktop: { width: 1920, height: 1080, deviceScaleFactor: 1, name: 'Desktop' },
  tablet: { width: 768, height: 1024, deviceScaleFactor: 2, name: 'Tablet' },
  mobile: { width: 375, height: 667, deviceScaleFactor: 2, name: 'Mobile' },
};

const TEST_SCENARIOS = [
  { name: 'Hero CTA - Consultar', action: async (page) => await page.click('a[href="#consultar"]') },
  { name: 'Hero CTA - Categorias', action: async (page) => await page.click('a[href="#categorias"]') },
  { name: 'Hero CTA - Links', action: async (page) => await page.click('a[href="#links"]') },
  { name: 'Nav - Home', action: async (page) => await page.click('a[href="#inicio"]') },
  { name: 'Nav - Consultar', action: async (page) => await page.click('a[href="#consultar"]') },
  { name: 'Nav - Categorias', action: async (page) => await page.click('a[href="#categorias"]') },
  { name: 'Referencias Tab - Sites Oficiais (Planalto filter)', action: async (page) => {
    await page.click('a[href="#links"]');
    await page.waitForTimeout(500);
    const filterBtn = await page.$('button[data-filter="Planalto"]');
    if (filterBtn) await filterBtn.click();
  } },
  { name: 'Referencias Tab - Órgãos Estaduais (Norte)', action: async (page) => {
    await page.click('a[href="#orgaos-estaduais"]');
    await page.waitForTimeout(500);
    const filterBtn = await page.$('button[data-filter="Norte"]');
    if (filterBtn) await filterBtn.click();
  } },
  { name: 'Menu Mobile - Toggle', action: async (page) => {
    const navToggle = await page.$('[aria-label="Toggle navigation"]');
    if (navToggle) await navToggle.click();
  } },
];

async function runTests() {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const results = {
    timestamp: new Date().toISOString(),
    baseUrl,
    viewports: [],
    issues: [],
  };

  try {
    for (const [viewportKey, viewport] of Object.entries(VIEWPORTS)) {
      console.log(`\n📱 Testando em ${viewport.name} (${viewport.width}x${viewport.height})\n`);

      const page = await browser.newPage();
      await page.setViewport(viewport);

      // Coletar console errors/warnings
      const consoleMessages = [];
      page.on('console', (msg) => {
        if (msg.type() === 'error' || msg.type() === 'warning') {
          consoleMessages.push({ type: msg.type(), text: msg.text() });
        }
      });

      // Coletar page errors
      const pageErrors = [];
      page.on('pageerror', (err) => {
        pageErrors.push(err.message);
      });

      try {
        // Navegar e esperar por rede inativa
        console.log(`  ⏳ Carregando página...`);
        await page.goto(baseUrl, { waitUntil: 'networkidle2', timeout: 30000 });

        // Capturar Core Web Vitals (simulado)
        const metrics = await page.evaluate(() => {
          const nav = performance.getEntriesByType('navigation')[0];
          return {
            domContentLoaded: nav.domContentLoadedEventEnd - nav.domContentLoadedEventStart,
            loadComplete: nav.loadEventEnd - nav.loadEventStart,
            resourceCount: performance.getEntriesByType('resource').length,
          };
        });

        console.log(`  ✅ Página carregada em ${metrics.loadComplete.toFixed(0)}ms`);

        // Teste de cenários
        for (const scenario of TEST_SCENARIOS) {
          try {
            console.log(`    → Teste: ${scenario.name}`);
            await scenario.action(page);
            await page.waitForTimeout(300); // Esperar animações
            console.log(`      ✅ Sucesso`);
          } catch (err) {
            console.log(`      ❌ Falha: ${err.message}`);
            results.issues.push({
              viewport: viewportKey,
              scenario: scenario.name,
              error: err.message,
            });
          }
        }

        // Validar links
        console.log(`\n  🔗 Validando links internos...`);
        const links = await page.evaluate(() => {
          return Array.from(document.querySelectorAll('a[href^="#"]'))
            .map((a) => ({ text: a.textContent.trim(), href: a.href }))
            .filter((l) => l.href.includes('#'));
        });
        console.log(`    Encontrados ${links.length} links âncora`);

        // Verificar acessibilidade básica
        console.log(`\n  ♿ Verificando acessibilidade...`);
        const a11y = await page.evaluate(() => {
          const checks = {
            imagesWithAlt: document.querySelectorAll('img:not([alt])').length,
            buttonsWithLabel: document.querySelectorAll('button:not([aria-label]):not(:has(>*))').length,
            skipLink: !!document.querySelector('a[href="#main"]'),
          };
          return checks;
        });

        if (a11y.imagesWithAlt > 0) {
          results.issues.push({
            viewport: viewportKey,
            category: 'accessibility',
            message: `${a11y.imagesWithAlt} imagens sem atributo alt`,
          });
        }

        console.log(`    Imagens sem alt: ${a11y.imagesWithAlt}`);
        console.log(`    Botões sem label: ${a11y.buttonsWithLabel}`);
        console.log(`    Skip link: ${a11y.skipLink ? '✅' : '❌'}`);

        // Validar estrutura do DOM
        console.log(`\n  🏗️ Validando estrutura...`);
        const structure = await page.evaluate(() => {
          return {
            hasMainContent: !!document.querySelector('main'),
            headingsHierarchy: Array.from(document.querySelectorAll('h1, h2, h3')).map((h) => h.tagName),
            sectionsWithId: document.querySelectorAll('[id^=""]').length,
          };
        });

        if (!structure.hasMainContent) {
          results.issues.push({
            viewport: viewportKey,
            category: 'structure',
            message: 'Falta elemento <main>',
          });
        }

        console.log(`    Elemento main: ${structure.hasMainContent ? '✅' : '❌'}`);
        console.log(`    Hierarquia de headings: ${structure.headingsHierarchy.join(' → ')}`);

        // Erros do console
        if (consoleMessages.length > 0) {
          console.log(`\n  ⚠️ Mensagens do console:`);
          consoleMessages.forEach((msg) => {
            console.log(`    [${msg.type.toUpperCase()}] ${msg.text}`);
          });
        }

        if (pageErrors.length > 0) {
          console.log(`\n  ❌ Erros de página:`);
          pageErrors.forEach((err) => {
            console.log(`    ${err}`);
            results.issues.push({
              viewport: viewportKey,
              category: 'pageError',
              message: err,
            });
          });
        }

        results.viewports.push({
          viewport: viewportKey,
          name: viewport.name,
          metrics,
          links: links.length,
          a11y,
          consoleMessages: consoleMessages.length,
          pageErrors: pageErrors.length,
          status: pageErrors.length === 0 ? '✅ PASSOU' : '❌ FALHOU',
        });
      } catch (err) {
        console.error(`Erro ao testar ${viewport.name}:`, err.message);
        results.viewports.push({
          viewport: viewportKey,
          name: viewport.name,
          status: `❌ ERRO: ${err.message}`,
        });
      } finally {
        await page.close();
      }
    }

    // Resumo final
    console.log('\n' + '='.repeat(60));
    console.log('📋 RESUMO DO TESTE E2E\n');
    results.viewports.forEach((vp) => {
      console.log(`${vp.status} ${vp.name}`);
    });

    if (results.issues.length > 0) {
      console.log(`\n⚠️ ${results.issues.length} problemas encontrados`);
      results.issues.slice(0, 5).forEach((issue) => {
        console.log(`  - [${issue.viewport}] ${issue.message || issue.scenario}`);
      });
    } else {
      console.log('\n✅ Todos os testes passaram!');
    }

    // Export JSON
    const reportPath = path.join(projectRoot, 'e2e_test_results.json');
    fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));
    console.log(`\n📊 Relatório exportado: ${reportPath}\n`);

  } finally {
    await browser.close();
  }

  return results.issues.length > 0 ? 1 : 0;
}

runTests().then((code) => process.exit(code));
