#!/usr/bin/env node
/**
 * Verificação de Consistência de Dados e Integrações
 * Valida:
 * - Estrutura JSON (schema)
 * - Links internos/externos
 * - Referências de categorias
 * - Domínios oficiais (.gov.br, etc)
 * - Integridade de dados
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');
const ALLOWED_EXTERNAL_SERVICE_DOMAINS = new Set([
  'icd.who.int', // Exceção controlada: referência oficial CID-11 (OMS)
]);

function validateJSON(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    JSON.parse(content);
    return { valid: true, path: filePath };
  } catch (err) {
    return { valid: false, path: filePath, error: err.message };
  }
}

function validateSchema() {
  console.log('\n📋 VALIDAÇÃO DE INTEGRIDADE DE DADOS\n');

  const findings = {
    timestamp: new Date().toISOString(),
    checks: [],
  };

  // 1. Validar JSONs
  console.log('1️⃣ Validando estruturas JSON...');

  const jsonFiles = [
    path.join(projectRoot, 'data', 'direitos.json'),
    path.join(projectRoot, 'data', 'dicionario_pcd.json'),
    path.join(projectRoot, 'data', 'matching_engine.json'),
    path.join(projectRoot, 'data', 'fontes_oficiais.json'),
    path.join(projectRoot, 'data', 'municipios_br.json'),
  ];

  const jsonResults = jsonFiles.map(validateJSON);
  const invalidJSON = jsonResults.filter((r) => !r.valid);

  if (invalidJSON.length === 0) {
    console.log('  ✅ Todos os JSONs válidos');
    findings.checks.push({ name: 'JSON validation', status: 'OK', files: jsonFiles.length });
  } else {
    console.log(`  ❌ ${invalidJSON.length} arquivo(s) JSON inválido(s)`);
    invalidJSON.forEach((r) => {
      console.log(`    - ${r.path}: ${r.error.substring(0, 50)}`);
    });
    findings.checks.push({
      name: 'JSON validation',
      status: 'FALHOU',
      invalid: invalidJSON,
    });
  }

  // 2. Validar referências de categorias
  console.log('\n2️⃣ Validando integridade de categorias...');

  const direitosPath = path.join(projectRoot, 'data', 'direitos.json');
  const direitosPayload = JSON.parse(fs.readFileSync(direitosPath, 'utf-8'));
  const direitos = Array.isArray(direitosPayload.categorias) ? direitosPayload.categorias : [];

  const categories = direitos.map((d) => d.id).filter(Boolean);
  console.log(`  📂 ${categories.length} categorias encontradas`);

  // Validar URLs em cada categoria
  let invalidURLs = 0;
  let emptyFields = 0;

  direitos.forEach((cat) => {
    if (!cat.id || !cat.titulo) emptyFields++;

    if (cat.links && Array.isArray(cat.links)) {
      cat.links.forEach((link) => {
        try {
          if (!link.url || (!link.titulo && !link.nome)) emptyFields++;
          // Validação básica de URL
          if (link.url && !link.url.match(/^(https?:|tel:|mailto:)/)) {
            invalidURLs++;
          }
        } catch {
          invalidURLs++;
        }
      });
    }
  });

  if (emptyFields === 0 && invalidURLs === 0) {
    console.log('  ✅ Todas as categorias íntegras');
    findings.checks.push({
      name: 'Categoria integrity',
      status: 'OK',
      categories: categories.length,
    });
  } else {
    console.log(`  ⚠️ Campos vazios: ${emptyFields}, URLs inválidas: ${invalidURLs}`);
    findings.checks.push({
      name: 'Categoria integrity',
      status: 'ALERTA',
      emptyFields,
      invalidURLs,
    });
  }

  // 3. Validar domínios oficiais
  console.log('\n3️⃣ Validando domínios de fontes...');

  const fontes = Array.isArray(direitosPayload.fontes) ? direitosPayload.fontes : [];

  const domainCounts = {};
  const invalidDomains = [];

  fontes.forEach((fonte) => {
    if (fonte.url) {
      try {
        const urlObj = new URL(fonte.url);
        const domain = urlObj.hostname;
        domainCounts[domain] = (domainCounts[domain] || 0) + 1;

        // Alertar se não é oficial
        if (!domain.match(/\.(gov\.br|leg\.br|jus\.br|def\.br|mp\.br)$/)) {
          if (fonte.tipo === 'servico' && !ALLOWED_EXTERNAL_SERVICE_DOMAINS.has(domain)) {
            invalidDomains.push({ url: fonte.url, domain, tipo: fonte.tipo });
          }
        }
      } catch {
        invalidDomains.push({ url: fonte.url, erro: 'URL inválida' });
      }
    }
  });

  console.log(`  📦 ${Object.keys(domainCounts).length} domínios únicos`);
  console.log(`  planalto.gov.br: ${domainCounts['www.planalto.gov.br'] || 0}`);
  console.log(`  inss.gov.br: ${domainCounts['www.gov.br'] || 0}`);

  if (invalidDomains.length > 0) {
    console.log(`  ⚠️ ${invalidDomains.length} domínios não-oficiais detectados`);
    findings.checks.push({
      name: 'Domínios oficiais',
      status: 'ALERTA',
      nonOfficial: invalidDomains.length,
    });
  } else {
    console.log('  ✅ Todos os domínios de serviço são oficiais');
    findings.checks.push({
      name: 'Domínios oficiais',
      status: 'OK',
      domínios: Object.keys(domainCounts).length,
    });
  }

  // 4. Validar versão sincronizada
  console.log('\n4️⃣ Validando sincronização de versão...');

  const packageJson = JSON.parse(fs.readFileSync(path.join(projectRoot, 'package.json'), 'utf-8'));
  const indexHtml = fs.readFileSync(path.join(projectRoot, 'index.html'), 'utf-8');

  const packageVersion = packageJson.version;
  const indexVersionMatch = indexHtml.match(/app\.js\?v=(\d+\.\d+\.\d+)/);
  const direitosVersion = direitosPayload.versao;

  const versionMatch = packageVersion === direitosVersion &&
    (!indexVersionMatch || packageVersion === indexVersionMatch[1]);

  if (versionMatch) {
    console.log(`  ✅ Versão sincronizada: ${packageVersion}`);
    findings.checks.push({
      name: 'Versão',
      status: 'OK',
      version: packageVersion,
    });
  } else {
    console.log(`  ❌ Versão inconsistente`);
    console.log(`    package.json: ${packageVersion}`);
    console.log(`    index.html(app.js): ${indexVersionMatch?.[1] || 'não encontrada'}`);
    console.log(`    direitos.json: ${direitosVersion}`);
    findings.checks.push({
      name: 'Versão',
      status: 'FALHOU',
      versions: { packageVersion, indexVersion: indexVersionMatch?.[1], direitosVersion },
    });
  }

  // 5. Validar estrutura de arquivos
  console.log('\n5️⃣ Validando estrutura de arquivos...');

  const requiredDirs = [
    path.join(projectRoot, 'data'),
    path.join(projectRoot, 'js'),
    path.join(projectRoot, 'css'),
    path.join(projectRoot, 'docs'),
  ];

  const requiredFiles = [
    path.join(projectRoot, 'index.html'),
    path.join(projectRoot, 'server.js'),
    path.join(projectRoot, 'package.json'),
  ];

  const missingDirs = requiredDirs.filter((d) => !fs.existsSync(d));
  const missingFiles = requiredFiles.filter((f) => !fs.existsSync(f));

  if (missingDirs.length === 0 && missingFiles.length === 0) {
    console.log('  ✅ Estrutura de arquivos completa');
    findings.checks.push({
      name: 'Estrutura de arquivos',
      status: 'OK',
    });
  } else {
    console.log(`  ❌ ${missingDirs.length} dir(s) e ${missingFiles.length} arquivo(s) faltando`);
    findings.checks.push({
      name: 'Estrutura de arquivos',
      status: 'FALHOU',
      missing: { dirs: missingDirs, files: missingFiles },
    });
  }

  // Resumo
  console.log('\n' + '='.repeat(60));
  console.log('📊 RESUMO DE INTEGRIDADE\n');

  const passedChecks = findings.checks.filter((c) => c.status === 'OK').length;
  const failedChecks = findings.checks.filter((c) => c.status === 'FALHOU').length;
  const alertChecks = findings.checks.filter((c) => c.status === 'ALERTA').length;

  console.log(`✅ OK: ${passedChecks}`);
  console.log(`⚠️ ALERTA: ${alertChecks}`);
  console.log(`❌ FALHOU: ${failedChecks}\n`);

  findings.checks.forEach((check) => {
    const icon = check.status === 'OK' ? '✅' : check.status === 'ALERTA' ? '⚠️' : '❌';
    console.log(`${icon} ${check.name}: ${check.status}`);
  });

  // Export
  const reportPath = path.join(projectRoot, 'data_integrity_check.json');
  fs.writeFileSync(reportPath, JSON.stringify(findings, null, 2));
  console.log(`\n📋 Relatório exportado: ${reportPath}\n`);

  return failedChecks > 0 ? 1 : 0;
}

process.exit(validateSchema());
