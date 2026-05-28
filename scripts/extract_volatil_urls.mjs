#!/usr/bin/env node
/**
 * Extrai URLs com estabilidade='volatil' de data/direitos.json
 * e ANEXA ao .lycheeignore (formato regex, uma por linha) para que
 * lychee as descubra automaticamente.
 *
 * IMPORTANTE: usa appendFileSync para PRESERVAR as exclusões manuais
 * versionadas em .lycheeignore (hosts gov.br com anti-bot por IP).
 *
 * Usado em CI para configurar lychee dinamicamente sem hardcoded list.
 */
import { appendFileSync, readFileSync } from "node:fs";

const obj = JSON.parse(readFileSync("data/direitos.json", "utf8"));
const volatil = new Set();

function walk(n) {
  if (n && typeof n === "object") {
    if (n.estabilidade === "volatil" && typeof n.url === "string") {
      volatil.add(n.url);
    }
    for (const v of Object.values(n)) walk(v);
  } else if (Array.isArray(n)) {
    for (const v of n) walk(v);
  }
}
walk(obj);

// Escapar regex chars para uso literal em lychee (.lycheeignore = regex)
const escaped = [...volatil].map((u) =>
  u.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
);
if (escaped.length > 0) {
  const block =
    "\n# === URLs voláteis (gerado automaticamente por extract_volatil_urls.mjs) ===\n" +
    escaped.join("\n") +
    "\n";
  appendFileSync(".lycheeignore", block);
}
console.log(`→ ${volatil.size} URLs voláteis anexadas ao .lycheeignore`);
