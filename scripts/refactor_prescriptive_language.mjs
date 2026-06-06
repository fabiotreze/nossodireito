#!/usr/bin/env node
/**
 * Semi-automatic refactoring for prescriptive language
 * Applies transformation rules to convert imperative → descriptive voice
 *
 * Usage:
 *   node scripts/refactor_prescriptive_language.mjs [--apply] [--file=<path>]
 *
 * Without --apply: dry-run (shows changes, doesn't write)
 * With --apply: actually writes changes to files
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');

// Transformation rules: [pattern, replacement, category, severity]
const TRANSFORMATION_RULES = [
  // RULE 1: "Procure X" → "X está disponível em/via"
  {
    pattern: /Procure\s+o\s+(\w+[\w\s]*?)\s*\(/gi,
    replacement: 'O $1 está disponível ($',
    category: 'imperativo',
    severity: 'high',
    context: 'procure_org_with_paren',
  },
  {
    pattern: /Procure\s+([^,.]*?)\s+(?:mais\s+próximo|na\s+sua|do\s+seu)/gi,
    replacement: '$1 está disponível na sua região através de',
    category: 'imperativo',
    severity: 'high',
    context: 'procure_nearby',
  },

  // RULE 2: "Agende pelo X" → "É possível agendar via X"
  {
    pattern: /Agende\s+pelo\s+(\w+[\w\s]*?)\s*\(/gi,
    replacement: 'Agendamento disponível via $1 (',
    category: 'imperativo',
    severity: 'high',
    context: 'agende',
  },

  // RULE 3: "Solicite X" → "X pode ser solicitado via"
  {
    pattern: /Solicite\s+([^,.]*?)\s+(?:na\s+|pelo\s+|em\s+)/gi,
    replacement: '$1 pode ser solicitado $',
    category: 'imperativo',
    severity: 'high',
    context: 'solicite',
  },

  // RULE 4: "Obrigatório X" → "X é necessário/requisitado"
  {
    pattern: /[Oo]brigatório\s+([^,.]*)/g,
    replacement: '$1 é necessário',
    category: 'prescritivo',
    severity: 'medium',
    context: 'obrigatorio',
  },

  // RULE 5: "Recomendamos X" → "X é recomendado/possível"
  {
    pattern: /[Rr]ecomendamos\s+que\s+([^,.]*)/gi,
    replacement: '$1 é uma opção recomendada',
    category: 'sugestão',
    severity: 'medium',
    context: 'recomendamos',
  },

  // RULE 6: "Sempre procure" → Keep as disclaimer (legitimate)
  // This is a SKIP rule - don't transform
  {
    pattern: /Sempre procure um profissional/gi,
    replacement: null, // null = skip, don't transform
    category: 'imperativo',
    severity: 'medium',
    context: 'disclaimer_professional',
    skip: true,
  },
];

class RefactoringEngine {
  constructor(dryRun = true) {
    this.dryRun = dryRun;
    this.stats = {
      filesProcessed: 0,
      replacementsApplied: 0,
      skipped: 0,
      errors: 0,
    };
    this.changes = [];
  }

  refactorFile(filePath) {
    console.log(`\n📄 Processing: ${filePath}`);

    // Read directly: avoids TOCTOU race condition (exists→read window).
    // ENOENT propagates to caller and is counted as an error.
    let content;
    try {
      content = fs.readFileSync(filePath, 'utf-8');
    } catch (err) {
      console.log(`  ❌ Read failed: ${err.code || err.message}`);
      this.stats.errors++;
      return;
    }
    const originalContent = content;

    const lines = content.split('\n');

    // Apply transformations line by line for better tracking
    const transformedLines = lines.map((line, idx) => {
      let transformedLine = line;
      let applied = false;

      TRANSFORMATION_RULES.forEach((rule) => {
        if (rule.skip) {
          // Skip this rule, but log it
          if (rule.pattern.test(line)) {
            this.stats.skipped++;
          }
          return;
        }

        const matches = [...line.matchAll(rule.pattern)];
        if (matches.length > 0) {
          matches.forEach((match) => {
            const replacement = rule.replacement.replace('$', match[1] || '');
            transformedLine = transformedLine.replace(match[0], replacement);

            this.changes.push({
              file: filePath,
              line: idx + 1,
              before: match[0],
              after: replacement,
              category: rule.category,
              severity: rule.severity,
              context: rule.context,
            });

            applied = true;
            this.stats.replacementsApplied++;
          });
        }
      });

      return transformedLine;
    });

    const newContent = transformedLines.join('\n');

    if (newContent !== originalContent) {
      if (this.dryRun) {
        console.log(`  📋 Would modify ${this.stats.replacementsApplied} line(s)`);
      } else {
        fs.writeFileSync(filePath, newContent, 'utf-8');
        console.log(`  ✅ Modified ${this.stats.replacementsApplied} line(s)`);
      }
      this.stats.filesProcessed++;
    } else {
      console.log(`  ✅ No changes needed`);
    }
  }

  printReport() {
    console.log('\n' + '='.repeat(70));
    console.log('📊 REFACTORING REPORT\n');

    console.log(`Files processed: ${this.stats.filesProcessed}`);
    console.log(`Replacements applied: ${this.stats.replacementsApplied}`);
    console.log(`Skipped (legitimate): ${this.stats.skipped}`);
    console.log(`Errors: ${this.stats.errors}\n`);

    if (this.changes.length > 0) {
      console.log('📝 Changes:\n');
      const grouped = {};
      this.changes.forEach((change) => {
        if (!grouped[change.category]) {
          grouped[change.category] = [];
        }
        grouped[change.category].push(change);
      });

      Object.entries(grouped).forEach(([category, changes]) => {
        console.log(`${category.toUpperCase()} (${changes.length}):`);
        changes.slice(0, 3).forEach((change) => {
          console.log(`  L${change.line}: "${change.before.substring(0, 40)}..."`);
          console.log(`         → "${change.after.substring(0, 40)}..."`);
        });
        if (changes.length > 3) {
          console.log(`  ... and ${changes.length - 3} more\n`);
        }
      });
    }

    if (this.dryRun) {
      console.log('🔍 DRY RUN: No files were modified.');
      console.log('   Run with --apply flag to write changes.\n');
    } else {
      console.log('✅ Changes applied.\n');
    }
  }
}

// Main execution
function main() {
  const args = process.argv.slice(2);
  const applyChanges = args.includes('--apply');
  const targetFile = args.find((arg) => arg.startsWith('--file='))?.replace('--file=', '');

  console.log('🔧 PRESCRIPTIVE LANGUAGE REFACTORING ENGINE\n');

  const engine = new RefactoringEngine(!applyChanges);

  if (targetFile) {
    // Single file mode
    const filePath = path.join(projectRoot, targetFile);
    engine.refactorFile(filePath);
  } else {
    // Default: process main files
    const filesToProcess = [
      path.join(projectRoot, 'index.html'),
      // NOTE: data/direitos.json will need special JSON-aware parsing
    ];

    filesToProcess.forEach((file) => {
      if (fs.existsSync(file)) {
        engine.refactorFile(file);
      }
    });
  }

  engine.printReport();

  return engine.stats.errors > 0 ? 1 : 0;
}

process.exit(main());
