#!/usr/bin/env node
/**
 * Diagnóstico de Indexação Google
 * Verifica impedimentos à indexação:
 * - robots.txt
 * - meta robots noindex
 * - X-Robots-Tag headers
 * - canonical tags
 * - duplicação de conteúdo
 * - redirects
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');

function diagnoseIndexation() {
  console.log('\n📡 DIAGNÓSTICO DE INDEXAÇÃO GOOGLE\n');

  const findings = {
    timestamp: new Date().toISOString(),
    checks: [],
    issues: [],
  };

  // 1. Verificar robots.txt
  console.log('1️⃣ Verificando robots.txt...');
  const robotsPath = path.join(projectRoot, 'robots.txt');
  if (fs.existsSync(robotsPath)) {
    const robotsContent = fs.readFileSync(robotsPath, 'utf-8');
    console.log('  📄 robots.txt encontrado\n');
    console.log('  Conteúdo:');
    robotsContent.split('\n').slice(0, 20).forEach((line) => console.log(`    ${line}`));

    // Alertas
    if (robotsContent.match(/^Disallow:\s+\/\s*$/m)) {
      findings.issues.push({
        type: 'CRÍTICO',
        issue: 'robots.txt bloqueando tudo (Disallow: /)',
        evidence: 'Disallow: / encontrado',
      });
      console.log('\n  🔴 ALERTA: Disallow: / detectado — TUDO BLOQUEADO\n');
    }

    if (robotsContent.includes('Disallow: /direitos')) {
      findings.issues.push({
        type: 'CRÍTICO',
        issue: 'robots.txt bloqueando /direitos/',
        evidence: 'Disallow: /direitos',
      });
      console.log('  🔴 ALERTA: /direitos/ bloqueado\n');
    } else {
      console.log('  ✅ /direitos/ está permitido\n');
    }

    findings.checks.push({
      name: 'robots.txt',
      status: findings.issues.filter(i => i.issue.includes('robots')).length === 0 ? 'OK' : 'PROBLEMAS',
      content: robotsContent.substring(0, 200),
    });
  } else {
    console.log('  ⚠️ robots.txt NÃO encontrado\n');
    findings.issues.push({
      type: 'MÉDIO',
      issue: 'robots.txt ausente',
      evidence: 'Nenhum arquivo robots.txt no root',
    });
  }

  // 2. Verificar meta robots em index.html
  console.log('2️⃣ Verificando meta robots tags em HTML...');
  const indexPath = path.join(projectRoot, 'index.html');
  if (fs.existsSync(indexPath)) {
    const indexContent = fs.readFileSync(indexPath, 'utf-8');

    const hasNoindex = indexContent.includes('content="noindex"') || indexContent.includes("content='noindex'");
    const hasNofollow = indexContent.includes('content="nofollow"') || indexContent.includes("content='nofollow'");

    if (hasNoindex) {
      findings.issues.push({
        type: 'CRÍTICO',
        issue: 'Meta robots noindex em index.html',
        evidence: 'content="noindex" detectado',
      });
      console.log('  🔴 ALERTA: noindex tag detectada\n');
    }

    if (hasNofollow) {
      findings.issues.push({
        type: 'ALTO',
        issue: 'Meta robots nofollow em index.html',
        evidence: 'content="nofollow" detectado',
      });
      console.log('  🟡 ALERTA: nofollow tag detectada\n');
    }

    if (!hasNoindex && !hasNofollow) {
      console.log('  ✅ Nenhum noindex/nofollow detectado\n');
      findings.checks.push({
        name: 'Meta robots tags',
        status: 'OK',
      });
    }
  }

  // 3. Verificar canonical tags
  console.log('3️⃣ Verificando canonical tags...');
  if (fs.existsSync(indexPath)) {
    const indexContent = fs.readFileSync(indexPath, 'utf-8');
    const canonicalMatch = indexContent.match(/<link[^>]*rel="canonical"[^>]*>/gi);

    if (canonicalMatch) {
      console.log(`  ✅ ${canonicalMatch.length} canonical tag(s) encontrada(s)`);
      canonicalMatch.slice(0, 3).forEach((tag) => {
        console.log(`    ${tag.substring(0, 80)}...`);
      });
      console.log();

      findings.checks.push({
        name: 'Canonical tags',
        status: 'PRESENTE',
        count: canonicalMatch.length,
      });
    } else {
      console.log('  ⚠️ Nenhum canonical tag em index.html\n');
      findings.issues.push({
        type: 'MÉDIO',
        issue: 'Canonical tags ausentes',
        evidence: 'Nenhum <link rel="canonical"> em index.html',
      });
    }
  }

  // 4. Verificar pré-renderização e duplicação
  console.log('4️⃣ Verificando pré-renderização (direitos/*.html)...');
  const direitosDir = path.join(projectRoot, 'direitos');
  if (fs.existsSync(direitosDir)) {
    const htmlFiles = fs
      .readdirSync(direitosDir)
      .filter((f) => f.endsWith('.html') || fs.statSync(path.join(direitosDir, f)).isDirectory());

    console.log(`  📂 ${htmlFiles.length} direito(s) com HTML encontrado(s)\n`);

    if (htmlFiles.length > 0) {
      findings.issues.push({
        type: 'ALTO',
        issue: 'Possível duplicação de conteúdo',
        evidence: `${htmlFiles.length} páginas pré-renderizadas + index.html renderiza tudo via JS`,
      });
      console.log('  🟡 ALERTA: Possível duplicação via prerender\n');
      console.log('  → Solução A: Remover arquivo .html pré-renderizado');
      console.log('  → Solução B: index.html use canonical apontando para /direitos/*.html\n');
    }

    findings.checks.push({
      name: 'Pré-renderização',
      status: 'PRESENTE',
      count: htmlFiles.length,
      recommendation: 'Usar canonical ou remover duplicação',
    });
  }

  // 5. Verificar se há redirects
  console.log('5️⃣ Verificando redirects em server.js...');
  const serverPath = path.join(projectRoot, 'server.js');
  let serverContent = '';
  if (fs.existsSync(serverPath)) {
    serverContent = fs.readFileSync(serverPath, 'utf-8');

    const hasRedirects = serverContent.match(/res\.redirect|res\.status\(30[0-9]\)/g);
    if (hasRedirects) {
      console.log(`  🔄 ${hasRedirects.length} redirect(s) detectado(s)\n`);
      findings.checks.push({
        name: 'Redirects',
        status: 'PRESENTE',
        count: hasRedirects.length,
      });
    } else {
      console.log('  ✅ Nenhum redirect detectado\n');
      findings.checks.push({
        name: 'Redirects',
        status: 'OK',
      });
    }
  }

  // 6. Verificar sitemap.xml
  console.log('6️⃣ Verificando sitemap.xml...');
  const sitemapPath = path.join(projectRoot, 'sitemap.xml');
  if (fs.existsSync(sitemapPath)) {
    const sitemapContent = fs.readFileSync(sitemapPath, 'utf-8');
    const urlCount = (sitemapContent.match(/<url>/g) || []).length;
    console.log(`  ✅ sitemap.xml encontrado (${urlCount} URLs)\n`);
    findings.checks.push({
      name: 'Sitemap',
      status: 'OK',
      count: urlCount,
    });
  } else {
    console.log('  ⚠️ sitemap.xml NÃO encontrado\n');
    findings.issues.push({
      type: 'MÉDIO',
      issue: 'Sitemap ausente',
      evidence: 'Nenhum sitemap.xml no root',
    });
  }

  // 7. Verificar headers de segurança que podem impedir indexação
  console.log('7️⃣ Verificando headers que podem impedir indexação...');
  const headerIssues = [];
  if (serverContent && serverContent.includes('X-Robots-Tag:')) {
    headerIssues.push('X-Robots-Tag header detectado — pode bloquear indexação');
  }
  if (serverContent && serverContent.includes('noindex')) {
    headerIssues.push('noindex em header detectado');
  }

  if (headerIssues.length > 0) {
    console.log(`  🟡 ${headerIssues.length} header issue(s):\n`);
    headerIssues.forEach((issue) => console.log(`    - ${issue}`));
    console.log();
  } else {
    console.log('  ✅ Nenhum header bloqueante detectado\n');
  }

  // Resumo
  console.log('='.repeat(60));
  console.log('📊 RESUMO DO DIAGNÓSTICO\n');

  const criticalIssues = findings.issues.filter((i) => i.type === 'CRÍTICO');
  const highIssues = findings.issues.filter((i) => i.type === 'ALTO');
  const mediumIssues = findings.issues.filter((i) => i.type === 'MÉDIO');

  console.log(`Críticos: ${criticalIssues.length}`);
  console.log(`Altos: ${highIssues.length}`);
  console.log(`Médios: ${mediumIssues.length}\n`);

  if (criticalIssues.length > 0) {
    console.log('🔴 CRÍTICOS:\n');
    criticalIssues.forEach((issue) => {
      console.log(`  - ${issue.issue}`);
      console.log(`    Evidence: ${issue.evidence}\n`);
    });
  }

  if (highIssues.length > 0) {
    console.log('🟡 ALTOS:\n');
    highIssues.forEach((issue) => {
      console.log(`  - ${issue.issue}`);
      console.log(`    Evidence: ${issue.evidence}\n`);
    });
  }

  // Ações recomendadas
  console.log('\n💡 AÇÕES RECOMENDADAS\n');

  if (criticalIssues.length > 0) {
    console.log('1. REMOVER bloqueios:\n');
    criticalIssues.forEach((issue) => {
      if (issue.issue.includes('noindex')) {
        console.log('   - Remover meta name="robots" content="noindex" de index.html');
      }
      if (issue.issue.includes('X-Robots-Tag')) {
        console.log('   - Remover header X-Robots-Tag: noindex de server.js');
      }
    });
    console.log();
  }

  if (findings.issues.some((i) => i.issue.includes('duplicação'))) {
    console.log('2. RESOLVER duplicação:\n');
    console.log('   Opção A: Remover direitos/*.html (usar apenas JS rendering)');
    console.log('   Opção B: Adicionar canonical em cada página apontando para versão canônica\n');
  }

  console.log('3. APÓS correções:\n');
  console.log('   - Aguardar ~24h para Google re-crawl');
  console.log('   - IR para Google Search Console');
  console.log('   - Clicar "Request indexing" em 5 URLs');
  console.log('   - Monitorar "Coverage" por 7-14 dias\n');

  // Export
  const reportPath = path.join(projectRoot, 'indexation_diagnosis.json');
  fs.writeFileSync(reportPath, JSON.stringify(findings, null, 2));
  console.log(`📋 Relatório exportado: ${reportPath}\n`);

  return criticalIssues.length > 0 ? 1 : 0;
}

process.exit(diagnoseIndexation());
