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
  // NOTA: Usamos lookaround Unicode-aware (?<![a-zA-ZÀ-ÿ]) ao invés de \b
  // porque \b em JS não trata acentos corretamente ("\bvá\b" casa com "vários").
  { regex: /(?<![a-zA-ZÀ-ÿ])procure(?![a-zA-ZÀ-ÿ])/gi, category: 'imperativo', severity: 'high' },
  { regex: /(?<![a-zA-ZÀ-ÿ])agende(?![a-zA-ZÀ-ÿ])/gi, category: 'imperativo', severity: 'high' },
  { regex: /(?<![a-zA-ZÀ-ÿ])solicite(?![a-zA-ZÀ-ÿ])/gi, category: 'imperativo', severity: 'high' },
  { regex: /(?<![a-zA-ZÀ-ÿ])peça(?![a-zA-ZÀ-ÿ])/gi, category: 'imperativo', severity: 'high' },
  { regex: /(?<![a-zA-ZÀ-ÿ])envie(?![a-zA-ZÀ-ÿ])/gi, category: 'imperativo', severity: 'high' },
  { regex: /(?<![a-zA-ZÀ-ÿ])dirij[ae]-se(?![a-zA-ZÀ-ÿ])/gi, category: 'imperativo', severity: 'high' },
  { regex: /(?<![a-zA-ZÀ-ÿ])compareça(?![a-zA-ZÀ-ÿ])/gi, category: 'imperativo', severity: 'high' },
  // "vá" como verbo imperativo (não confundir com "válido", "vários")
  { regex: /(?<![a-zA-ZÀ-ÿ])vá\s+(?:à|ao|aos|às|para|até)\s+/gi, category: 'imperativo', severity: 'high' },
  { regex: /(?<![a-zA-ZÀ-ÿ])clique(?![a-zA-ZÀ-ÿ])/gi, category: 'imperativo', severity: 'medium' },
  { regex: /(?<![a-zA-ZÀ-ÿ])faça(?![a-zA-ZÀ-ÿ])/gi, category: 'imperativo', severity: 'high' },
  { regex: /(?<![a-zA-ZÀ-ÿ])descubra(?![a-zA-ZÀ-ÿ])/gi, category: 'imperativo', severity: 'medium' },

  // Sugestões e recomendações
  { regex: /(?<![a-zA-ZÀ-ÿ])recomend(amos|a|aram|adas?|ar|ação)(?![a-zA-ZÀ-ÿ])/gi, category: 'sugestão', severity: 'high' },
  { regex: /(?<![a-zA-ZÀ-ÿ])sugeri(mos|r|riam|do)(?![a-zA-ZÀ-ÿ])/gi, category: 'sugestão', severity: 'high' },
  // "indicamos / indicação" prescritivo — EXCETO "indicação médica/clínica/CID/etc" (factual)
  { regex: /(?<![a-zA-ZÀ-ÿ])indicamos(?![a-zA-ZÀ-ÿ])/gi, category: 'sugestão', severity: 'high' },
  { regex: /(?<![a-zA-ZÀ-ÿ])indicação(?!\s+(?:médica|clínica|cirúrgica|do\s+CID|de\s+reabilitação|do\s+médico|terapêutica|prescritiva|de\s+cota))(?![a-zA-ZÀ-ÿ])/gi, category: 'sugestão', severity: 'high' },
  { regex: /(?<![a-zA-ZÀ-ÿ])aconselhamos?(?![a-zA-ZÀ-ÿ])/gi, category: 'sugestão', severity: 'high' },
  { regex: /(?<![a-zA-ZÀ-ÿ])deveria?(?![a-zA-ZÀ-ÿ])/gi, category: 'sugestão', severity: 'medium' },
  { regex: /(?<![a-zA-ZÀ-ÿ])devem(?![a-zA-ZÀ-ÿ])/gi, category: 'sugestão', severity: 'medium' },

  // Promessas
  { regex: /(?<![a-zA-ZÀ-ÿ])você terá(?![a-zA-ZÀ-ÿ])/gi, category: 'promessa', severity: 'high' },
  { regex: /(?<![a-zA-ZÀ-ÿ])você tem direito(?![a-zA-ZÀ-ÿ])/gi, category: 'promessa', severity: 'high' },
  { regex: /(?<![a-zA-ZÀ-ÿ])terá acesso(?![a-zA-ZÀ-ÿ])/gi, category: 'promessa', severity: 'high' },
  // "garantia" — somente em frases promissoras, não em "garantia legal", "garantia constitucional"
  { regex: /(?<![a-zA-ZÀ-ÿ])garantia\s+de\s+(?!cumprimento|isonomia|origem|fábrica|qualidade)/gi, category: 'promessa', severity: 'medium' },
  { regex: /(?<![a-zA-ZÀ-ÿ])assegurada?(?![a-zA-ZÀ-ÿ])/gi, category: 'promessa', severity: 'medium' },
  { regex: /(?<![a-zA-ZÀ-ÿ])você vai conseguir(?![a-zA-ZÀ-ÿ])/gi, category: 'promessa', severity: 'high' },

  // Contexto jurídico (palavras perigosas sem source)
  { regex: /(?<![a-zA-ZÀ-ÿ])precisa de(?![a-zA-ZÀ-ÿ])/gi, category: 'prescritivo', severity: 'medium' },
  { regex: /(?<![a-zA-ZÀ-ÿ])obrigat(ório|ória|oriamente)(?![a-zA-ZÀ-ÿ])/gi, category: 'prescritivo', severity: 'medium' },
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
        const lineTrimmed = line.trim();

        // SKIP: linhas que são URLs, slugs, ou referências técnicas
        if (
          lineTrimmed.includes('"url"') ||
          lineTrimmed.includes('"urls"') ||
          lineTrimmed.includes('"slug"') ||
          lineTrimmed.includes('"id"') ||
          lineTrimmed.includes('http://') ||
          lineTrimmed.includes('https://')
        ) {
          continue;
        }

        findings.push({
          file: filePath.replace(projectRoot, '.'),
          line: lineNum,
          match: match[0],
          lineContent: lineTrimmed.substring(0, 100),
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
