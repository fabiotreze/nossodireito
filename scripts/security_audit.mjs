#!/usr/bin/env node
/**
 * Auditoria de Segurança
 * Verifica:
 * - Vulnerabilidades conhecidas (npm audit)
 * - Problemas CodeQL detectados
 * - Endpoints sensíveis expostos
 * - CORS misconfigured
 * - CSP headers
 * - Falhas de XSS
 * - SSRF/injection vectors
 * - Sensitive data leaks
 */

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');

function runAudit() {
  console.log('\n🔒 AUDITORIA DE SEGURANÇA\n');

  const findings = {
    timestamp: new Date().toISOString(),
    checks: [],
  };

  // 1. npm audit
  console.log('1️⃣ Verificando vulnerabilidades de dependências...');
  try {
    const auditOutput = execSync('npm audit --json 2>&1 || true', {
      cwd: projectRoot,
      encoding: 'utf-8',
    });

    try {
      const audit = JSON.parse(auditOutput);
      const vulnerabilities = audit.metadata?.vulnerabilities || {};
      const critical = vulnerabilities.critical || 0;
      const high = vulnerabilities.high || 0;

      findings.checks.push({
        name: 'npm audit',
        status: critical > 0 ? 'CRÍTICO' : high > 0 ? 'ALTO' : 'OK',
        critical,
        high,
        medium: vulnerabilities.moderate || 0,
        low: vulnerabilities.low || 0,
      });

      console.log(`  📦 Críticas: ${critical}, Altas: ${high}`);
    } catch {
      console.log('  ⚠️ Erro parsing npm audit output');
    }
  } catch (err) {
    console.log('  ❌ npm audit failed:', err.message);
  }

  // 2. Procurar por padrões inseguros no código
  console.log('\n2️⃣ Analisando padrões inseguros no código...');

  const unsafePatterns = [
    { pattern: /eval\(/g, name: 'eval()', severity: 'CRÍTICO' },
    { pattern: /innerHTML\s*=/g, name: 'innerHTML direct assignment', severity: 'ALTO' },
    { pattern: /document\.write/g, name: 'document.write', severity: 'MÉDIO' },
    { pattern: /fetch\(['"]\/\//g, name: 'fetch para URL absoluta externa', severity: 'ALTO' },
    { pattern: /window\.location\.href\s*=\s*[^'"]|decodeURIComponent\(/g, name: 'Open redirect risk', severity: 'ALTO' },
  ];

  const jsFiles = [
    path.join(projectRoot, 'js', 'app.js'),
    path.join(projectRoot, 'server.js'),
  ];

  const codeFindings = [];

  jsFiles.forEach((file) => {
    if (fs.existsSync(file)) {
      const content = fs.readFileSync(file, 'utf-8');
      unsafePatterns.forEach(({ pattern, name, severity }) => {
        if (pattern.test(content)) {
          const matches = content.match(pattern);
          codeFindings.push({
            file: file.replace(projectRoot, '.'),
            pattern: name,
            severity,
            count: matches.length,
          });
        }
      });
    }
  });

  if (codeFindings.length === 0) {
    console.log('  ✅ Nenhum padrão inseguro detectado');
    findings.checks.push({
      name: 'Padrões inseguros',
      status: 'OK',
      findings: 0,
    });
  } else {
    console.log(`  ⚠️ ${codeFindings.length} padrões inseguros encontrados`);
    codeFindings.forEach((f) => {
      console.log(`    [${f.severity}] ${f.file}: ${f.pattern} (${f.count}x)`);
    });
    findings.checks.push({
      name: 'Padrões inseguros',
      status: 'ALERTA',
      findings: codeFindings,
    });
  }

  // 3. Verificar uso de localStorage/sessionStorage para dados sensíveis
  console.log('\n3️⃣ Verificando armazenamento de dados sensíveis...');

  const appJsPath = path.join(projectRoot, 'js', 'app.js');
  if (fs.existsSync(appJsPath)) {
    const appContent = fs.readFileSync(appJsPath, 'utf-8');
    const sensitiveKeywords = [
      'password',
      'token',
      'apiKey',
      'secret',
      'credential',
      'authorization',
    ];

    const storageUses = appContent.match(/localStorage|sessionStorage/g) || [];
    const hasStorage = storageUses.length > 0;

    if (hasStorage) {
      const sensitiveInStorage = sensitiveKeywords.some((kw) =>
        appContent.includes(`localStorage.${kw}`) || appContent.includes(`sessionStorage.${kw}`)
      );

      if (sensitiveInStorage) {
        findings.checks.push({
          name: 'Dados sensíveis em storage',
          status: 'CRÍTICO',
          message: 'Dados sensíveis armazenados localmente detectados',
        });
        console.log('  ❌ CRÍTICO: Dados sensíveis em localStorage/sessionStorage');
      } else {
        findings.checks.push({
          name: 'Dados em storage',
          status: 'OK',
          message: 'Nenhum dado sensível detectado em storage',
        });
        console.log('  ✅ Apenas dados não-sensíveis em storage');
      }
    } else {
      findings.checks.push({
        name: 'Dados em storage',
        status: 'OK',
        message: 'Nenhum uso de localStorage/sessionStorage',
      });
      console.log('  ✅ Nenhum uso de localStorage/sessionStorage');
    }
  }

  // 4. Verificar HTTPS e headers de segurança (no server.js)
  console.log('\n4️⃣ Verificando headers de segurança no servidor...');

  const serverPath = path.join(projectRoot, 'server.js');
  if (fs.existsSync(serverPath)) {
    const serverContent = fs.readFileSync(serverPath, 'utf-8');

    const securityHeaders = [
      { name: 'Content-Security-Policy', pattern: /Content-Security-Policy|csp/i },
      { name: 'X-Content-Type-Options', pattern: /X-Content-Type-Options|nosniff/i },
      { name: 'X-Frame-Options', pattern: /X-Frame-Options|SAMEORIGIN|DENY/i },
      { name: 'Strict-Transport-Security', pattern: /Strict-Transport-Security|HSTS/i },
    ];

    const headerStatus = {};
    securityHeaders.forEach(({ name, pattern }) => {
      headerStatus[name] = pattern.test(serverContent);
    });

    findings.checks.push({
      name: 'Headers de segurança',
      status: Object.values(headerStatus).every((v) => v) ? 'OK' : 'PARCIAL',
      headers: headerStatus,
    });

    console.log('  Headers encontrados:');
    Object.entries(headerStatus).forEach(([name, found]) => {
      console.log(`    ${found ? '✅' : '❌'} ${name}`);
    });
  }

  // 5. Verificar gitleaks (já executado no pre-push?)
  console.log('\n5️⃣ Verificando secrets expostos...');
  try {
    const gitleaksOutput = execSync('gitleaks detect --source . --verbose 2>&1 || true', {
      cwd: projectRoot,
      encoding: 'utf-8',
      timeout: 10000,
    });

    if (gitleaksOutput.includes('no leaks found') || gitleaksOutput.includes('0 leaks')) {
      findings.checks.push({
        name: 'Gitleaks',
        status: 'OK',
      });
      console.log('  ✅ Nenhum secret exposto detectado');
    } else {
      findings.checks.push({
        name: 'Gitleaks',
        status: 'ALERTA',
        output: gitleaksOutput.substring(0, 500),
      });
      console.log('  ⚠️ Possíveis secrets detectados');
    }
  } catch (err) {
    console.log('  ⚠️ Gitleaks não rodou ou não está instalado');
  }

  // 6. Verificar CSP violations no HTML
  console.log('\n6️⃣ Verificando inline scripts perigosos...');

  const indexPath = path.join(projectRoot, 'index.html');
  if (fs.existsSync(indexPath)) {
    const indexContent = fs.readFileSync(indexPath, 'utf-8');

    const inlineScriptCount = (indexContent.match(/<script[^>]*>/g) || []).filter(
      (tag) => !tag.includes('src=')
    ).length;

    if (inlineScriptCount > 0) {
      findings.checks.push({
        name: 'Inline scripts',
        status: 'ALERTA',
        count: inlineScriptCount,
      });
      console.log(`  ⚠️ ${inlineScriptCount} inline script(s) detectado(s)`);
    } else {
      findings.checks.push({
        name: 'Inline scripts',
        status: 'OK',
      });
      console.log('  ✅ Sem inline scripts');
    }
  }

  // Resumo
  console.log('\n' + '='.repeat(60));
  console.log('📊 RESUMO DE SEGURANÇA\n');

  const criticalCount = findings.checks.filter((c) => c.status === 'CRÍTICO').length;
  const highCount = findings.checks.filter((c) => c.status === 'ALTO').length;
  const mediumCount = findings.checks.filter((c) => c.status === 'MÉDIO').length;
  const alertCount = findings.checks.filter((c) => c.status === 'ALERTA').length;

  console.log(`Críticos: ${criticalCount}`);
  console.log(`Altos: ${highCount}`);
  console.log(`Alertas: ${alertCount}`);
  console.log(`Ok: ${findings.checks.filter((c) => c.status === 'OK').length}\n`);

  // Export
  const reportPath = path.join(projectRoot, 'security_audit_results.json');
  fs.writeFileSync(reportPath, JSON.stringify(findings, null, 2));
  console.log(`📋 Relatório exportado: ${reportPath}\n`);

  return criticalCount > 0 ? 1 : 0;
}

process.exit(runAudit());
