#!/usr/bin/env node
/**
 * precompress_static.mjs — Generate .br and .gz siblings for static assets.
 *
 * Walks a directory tree, finds files whose extension is in the COMPRESSIBLE
 * allowlist, and writes a Brotli (.br, quality 11) and Gzip (.gz, level 9)
 * sibling next to each one.
 *
 * Why: doing this at build time once is FAR cheaper than compressing at
 * request time, especially for large JSON datasets (419KB direitos.json
 * took 5–10s of CPU at Brotli quality 11 — root cause of the 2026-05-30
 * SEV2 latency incident).
 *
 * The server (server.js) will prefer these siblings before falling back to
 * on-the-fly Brotli q4.
 *
 * Usage:
 *   node scripts/precompress_static.mjs [target-dir]
 *
 * Defaults to the repo root. Skips files smaller than MIN_BYTES (compression
 * overhead exceeds savings).
 */

"use strict";

import fs from "node:fs";
import fsPromises from "node:fs/promises";
import path from "node:path";
import zlib from "node:zlib";
import { pipeline } from "node:stream/promises";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Must match lib/mime.js COMPRESSIBLE set.
const COMPRESSIBLE = new Set([".html", ".css", ".js", ".json", ".svg", ".txt", ".xml"]);

// Directories to skip entirely.
const SKIP_DIRS = new Set([
  "node_modules",
  ".git",
  ".github",
  "terraform",
  "tests",
  "__pycache__",
  "scripts",
  "schemas",
]);

// Only compress files >= this size. Smaller files: overhead > savings.
const MIN_BYTES = 1024;

const targetDir = path.resolve(process.argv[2] || path.join(__dirname, ".."));

let processed = 0;
let skipped = 0;
let totalBytesIn = 0;
let totalBytesBr = 0;
let totalBytesGz = 0;

async function walk(dir) {
  let entries;
  try {
    entries = await fsPromises.readdir(dir, { withFileTypes: true });
  } catch (err) {
    if (err.code === "ENOENT") return;
    throw err;
  }
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (SKIP_DIRS.has(entry.name)) continue;
      if (entry.name.startsWith(".")) continue;
      await walk(fullPath);
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name).toLowerCase();
      if (!COMPRESSIBLE.has(ext)) continue;
      // Skip if already a sibling artifact.
      if (entry.name.endsWith(".br") || entry.name.endsWith(".gz")) continue;
      await compressFile(fullPath);
    }
  }
}

async function compressFile(filePath) {
  const stat = await fsPromises.stat(filePath);
  if (stat.size < MIN_BYTES) {
    skipped++;
    return;
  }
  totalBytesIn += stat.size;

  const brPath = `${filePath}.br`;
  const gzPath = `${filePath}.gz`;

  // Brotli quality 11 — max compression, runs at build time so cost is OK.
  await pipeline(
    fs.createReadStream(filePath),
    zlib.createBrotliCompress({
      params: {
        [zlib.constants.BROTLI_PARAM_QUALITY]: 11,
        [zlib.constants.BROTLI_PARAM_SIZE_HINT]: stat.size,
      },
    }),
    fs.createWriteStream(brPath),
  );
  const brStat = await fsPromises.stat(brPath);
  totalBytesBr += brStat.size;

  // Gzip level 9 for clients that don't support Brotli.
  await pipeline(
    fs.createReadStream(filePath),
    zlib.createGzip({ level: 9 }),
    fs.createWriteStream(gzPath),
  );
  const gzStat = await fsPromises.stat(gzPath);
  totalBytesGz += gzStat.size;

  processed++;
  const rel = path.relative(targetDir, filePath);
  const brPct = ((1 - brStat.size / stat.size) * 100).toFixed(1);
  const gzPct = ((1 - gzStat.size / stat.size) * 100).toFixed(1);
  console.log(
    `  ${rel}: ${fmt(stat.size)} → br ${fmt(brStat.size)} (-${brPct}%) · gz ${fmt(gzStat.size)} (-${gzPct}%)`,
  );
}

function fmt(bytes) {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}K`;
  return `${(bytes / 1024 / 1024).toFixed(2)}M`;
}

console.log(`📦 Pre-compressing static assets under: ${targetDir}`);
const start = Date.now();
await walk(targetDir);
const elapsed = ((Date.now() - start) / 1000).toFixed(2);

const brSavings = totalBytesIn ? ((1 - totalBytesBr / totalBytesIn) * 100).toFixed(1) : "0.0";
const gzSavings = totalBytesIn ? ((1 - totalBytesGz / totalBytesIn) * 100).toFixed(1) : "0.0";

console.log("");
console.log(`✅ Processed: ${processed} files (skipped ${skipped} small files)`);
console.log(`   Original: ${fmt(totalBytesIn)}`);
console.log(`   Brotli:   ${fmt(totalBytesBr)} (-${brSavings}%)`);
console.log(`   Gzip:     ${fmt(totalBytesGz)} (-${gzSavings}%)`);
console.log(`   Elapsed:  ${elapsed}s`);
