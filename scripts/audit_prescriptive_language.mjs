#!/usr/bin/env node
/**
 * Auditoria de Linguagem Prescritiva
 * Detecta termos imperativos, sugestões e indicações em:
 * - index.html
 * - direitos.json
 * - dicionario_pcd.json
 * - Documentação
 * 
 * Termos PROIBIDOS (linguagem prescritiva):
 * - Imperativos: procure, agende, solicite, peça, envie, dirija-se, compareça, etc.
 * - Sugestões: recomendamos, sugerimos, indicamos, aconselhamos, deveria, deve, devem
 * - Promessas: você terá, você tem direito, terá acesso, garantia, assegurada
 * - Verbos de ação pessoal: tente, vá, volte, clique, entre
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');

const PROHIBITED_PATTERNS = [
  // Imperativos diretos
  { regex: /\bprocure\b/gi, category: 'imperativo', severity: 'high' },
  { regex: /\bagende\b/gi, category: 'imperativo', severity: 'high' },
  { regex: /\bsolicite\b/gi, category: 'imperativo', severity: 'high' },
  { regex: /\bpeça\b/gi, category: 'imperativo', severity: 'high' },
  { regex: /\benvie\b/gi, category: 'imperativo', severity: 'high' },
  { regex: /\bdirig(a-se|ir-se)\b/gi, category: 'imperativo', severity: 'high' },
  { regex: /\bcompaреça\b/gi, category: 'imperativo', severity: 'high' },
  { regex: /\bvá\b/gi, category: 'imperativo', severity: 'high' },
  { regex: /\bvai\b/gi, category: 'imperativo', severity: 'medium' }, // contexto: "vai para"
  { regex: /\bclique\b/gi, category: 'imperativo', severity: 'medium' },
  { regex: /\bfaça\b/gi, category: 'imperativo', severity: 'high' },
  { regex: /\bdescubra\b/gi, category: 'imperativo', severity: 'medium' },

  // Sugestões e recomendações
  { regex: /\brecomend(amos|a|amos|aram|adas?|ar|ação)\b/gi, category: 'sugestão', severity: 'high' },
  { regex: /\bsugeri(mos|mos|r|riam|do)\b/gi, category: 'sugestão', severity: 'high' },
  { regex: /\bindic(amos|a|ação)\b/gi, category: 'sugestão', severity: 'high' },
  { regex: /\baconselhamos?\b/gi, category: 'sugestão', severity: 'high' },
  { regex: /\bdeveria?\b/gi, category: 'sugestão', severity: 'medium' },
  { regex: /\bdevem\b/gi, category: 'sugestão', severity: 'medium' },

  // Promessas
  { regex: /\bvocê terá\b/gi, category: 'promessa', severity: 'high' },
  { regex: /\bvocê tem direito\b/gi, category: 'promessa', severity: 'high' },
  { regex: /\bterá acesso\b/gi, category: 'promessa', severity: 'high' },
  { regex: /\bgarantia\b/gi, category: 'promessa', severity: 'medium' },
  { regex: /\bassegurada?\b/gi, category: 'promessa', severity: 'medium' },
  { regex: /\bvocê vai conseguir\b/gi, category: 'promessa', severity: 'high' },

  // Contexto jurídico (palavras perigosas sem source)
  { regex: /\bprecisa de\b/gi, category: 'prescritivo', severity: 'medium' },
  { regex: /\bobrigat(ório|ória|oriamente)\b/gi, category: 'prescritivo', severity: 'medium' },
];

function scanFile(filePath) {
  if (!fs.existsSync(filePath)) {
    return null;
  }

  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const findings = [];

    PROHIBITED_PATTERNS.forEach(({ regex, category, severity }) => {
      let match;
      const localRegex = new RegExp(regex.source, regex.flags);
      
      while ((match = localRegex.exec(content)) !== null) {
        // Contar linhas até a match
        const lineNum = content.substring(0, match.index).split('\n').length;
        const lineStart = content.lastIndexOf('\n', match.index) + 1;
        const lineEnd = content.indexOf('\n', match.index);
        const line = content.substring(lineStart, lineEnd === -1 ? content.length : lineEnd);

        findings.push({
          file: filePath.replace(projectRoot, '.'),
          line: lineNum,
          match: match[0],
          lineContent: line.trim().substring(0, 100),
          category,
          severity,
        });
      }
    });

    return findings;
  } catch (err) {
    console.error(`Erro lendo ${filePath}:`, err.message);
    return [];
  }
}

function auditProject() {
  const filesToAudit = [
    path.join(projectRoot, 'index.html'),
    path.join(projectRoot, 'data', 'direitos.json'),
    path.join(projectRoot, 'data', 'dicionario_pcd.json'),
    path.join(projectRoot, 'docs', 'README.md'),
    path.join(projectRoot, 'docs', 'ARCHITECTURE.md'),
    path.join(projectRoot, 'docs', 'SECURITY.md'),
    path.join(projectRoot, 'GOVERNANCE.md'),
  ];

  let totalFindings = 0;
  const findingsByFile = {};

  filesToAudit.forEach((filePath) => {
    const findings = scanFile(filePath);
    if (findings && findings.length > 0) {
      findingsByFile[filePath] = findings;
      totalFindings += findings.length;
    }
  });

  // Saída formatada
  console.log('\n🔍 AUDITORIA DE LINGUAGEM PRESCRITIVA\n');
  console.log(`📊 Total de achados: ${totalFindings}\n`);

  if (totalFindings === 0) {
    console.log('✅ Nenhum termo prescritivo detectado!\n');
    return 0;
  }

  // Agrupar por severidade
  const bySeverity = { high: 0, medium: 0, low: 0 };
  const byCategory = {};

  Object.entries(findingsByFile).forEach(([file, findings]) => {
    findings.forEach((f) => {
      bySeverity[f.severity]++;
      byCategory[f.category] = (byCategory[f.category] || 0) + 1;
    });
  });

  console.log('Severidade:');
  console.log(`  🔴 CRÍTICO: ${bySeverity.high}`);
  console.log(`  🟡 MÉDIO: ${bySeverity.medium}`);
  console.log(`  🟢 BAIXO: ${bySeverity.low}\n`);

  console.log('Por categoria:');
  Object.entries(byCategory).forEach(([cat, count]) => {
    console.log(`  ${cat}: ${count}`);
  });

  console.log('\n── DETALHES ──\n');

  Object.entries(findingsByFile).forEach(([file, findings]) => {
    console.log(`\n📄 ${file}`);
    findings.forEach((f) => {
      const icon = f.severity === 'high' ? '🔴' : f.severity === 'medium' ? '🟡' : '🟢';
      console.log(`  ${icon} L${f.line}: "${f.match}" [${f.category}]`);
      console.log(`     → ${f.lineContent}...`);
    });
  });

  // Export JSON
  const reportPath = path.join(projectRoot, 'audit_prescriptive_language.json');
  fs.writeFileSync(reportPath, JSON.stringify({ timestamp: new Date().toISOString(), totalFindings, bySeverity, byCategory, findings: findingsByFile }, null, 2));
  console.log(`\n📋 Relatório exportado: ${reportPath}\n`);

  return totalFindings > 0 ? 1 : 0;
}

process.exit(auditProject());
