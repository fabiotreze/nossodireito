#!/usr/bin/env node

/**
 * Branding guard for template consumers.
 * Fails if config.json still contains default NossoDireito values.
 */

import fs from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";

const ROOT = process.cwd();
const CONFIG_PATH = path.join(ROOT, "config.json");

const DEFAULTS = {
  "branding.organizationName": "NossoDireito",
  "branding.organizationSlug": "nossodireito",
  "branding.websiteUrl": "https://nossodireito.fabiotreze.com",
  "contact.email": "contato@nossodireito.com.br",
  "contact.dpo": "dpo@nossodireito.com.br",
  "seo.siteTitle": "Direitos PcD 2026 — BPC, CIPTEA, Escola | NossoDireito",
};

function isCanonicalRepo() {
  const envRepo = process.env.GITHUB_REPOSITORY || "";
  if (envRepo.toLowerCase() === "fabiotreze/nossodireito") return true;
  try {
    const origin = execSync("git config --get remote.origin.url", { encoding: "utf8" }).trim().toLowerCase();
    return origin.includes("fabiotreze/nossodireito");
  } catch {
    return false;
  }
}

function get(obj, dottedKey) {
  return dottedKey.split(".").reduce((acc, key) => (acc == null ? undefined : acc[key]), obj);
}

function fail(msg) {
  console.error(`\n❌ Branding check failed: ${msg}`);
  process.exit(1);
}

if (!process.env.BRANDING_GUARD_STRICT && isCanonicalRepo()) {
  console.log("ℹ️ Branding check skipped in canonical upstream repository.");
  console.log("   Set BRANDING_GUARD_STRICT=1 to force strict validation.");
  process.exit(0);
}

if (!fs.existsSync(CONFIG_PATH)) {
  fail("config.json not found. Create it from template before deploy.");
}

let config;
try {
  config = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
} catch (err) {
  fail(`config.json is invalid JSON (${err.message}).`);
}

const violations = [];
for (const [key, defaultValue] of Object.entries(DEFAULTS)) {
  const current = get(config, key);
  if (current === defaultValue) {
    violations.push({ key, defaultValue });
  }
}

if (violations.length > 0) {
  console.error("\n❌ Branding check failed: default values detected in config.json");
  for (const v of violations) {
    console.error(`- ${v.key} is still default: ${JSON.stringify(v.defaultValue)}`);
  }
  console.error("\nHow to fix (no terminal):");
  console.error("1. Open config.json in GitHub.");
  console.error("2. Click 'Edit this file'.");
  console.error("3. Replace org name, slug, URL and contacts.");
  console.error("4. Commit changes.");
  process.exit(1);
}

console.log("✅ Branding check passed: config.json is customized.");
