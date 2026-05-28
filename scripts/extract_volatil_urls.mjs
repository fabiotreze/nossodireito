#!/usr/bin/env node
/**
 * Extrai URLs com estabilidade='volatil' de data/direitos.json
 * e emite arquivo --exclude para lychee (uma URL regex por linha).
 *
 * Usado em CI para configurar lychee dinamicamente sem hardcoded list.
 *
 * Output: .lychee-exclude.txt (regex, uma por linha)
 */
import { readFileSync, writeFileSync } from "node:fs";

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

// Escapar regex chars para uso literal em lychee --exclude
const escaped = [...volatil].map((u) =>
  u.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
);
writeFileSync(".lychee-exclude.txt", escaped.join("\n") + "\n");
console.log(`→ ${volatil.size} URLs voláteis exportadas para .lychee-exclude.txt`);
