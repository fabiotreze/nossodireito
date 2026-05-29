"use strict";

import { afterEach, test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { resolveFile } = require("../lib/file-resolver");

const tempRoots = [];

async function makeRoot() {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "nd-file-resolver-"));
  tempRoots.push(root);

  await fs.writeFile(path.join(root, "index.html"), "home");
  await fs.mkdir(path.join(root, "beneficios"), { recursive: true });
  await fs.writeFile(path.join(root, "beneficios", "index.html"), "beneficios");
  await fs.writeFile(path.join(root, "sobre.html"), "sobre");
  await fs.writeFile(path.join(root, "app.js"), "console.log('ok');");
  await fs.mkdir(path.join(root, "docs"), { recursive: true });
  await fs.writeFile(path.join(root, "docs", "private.html"), "blocked");
  await fs.writeFile(path.join(root, ".env"), "SECRET=1");
  await fs.writeFile(path.join(root, "malicioso.sh"), "echo nope");

  return root;
}

afterEach(async () => {
  while (tempRoots.length) {
    const root = tempRoots.pop();
    await fs.rm(root, { recursive: true, force: true });
  }
});

test("resolve '/' para index.html da raiz", async () => {
  const root = await makeRoot();
  const resolved = await resolveFile("/", root);
  assert.equal(resolved, path.join(root, "index.html"));
});

test("resolve clean URL de diretório para index.html interno", async () => {
  const root = await makeRoot();
  const resolved = await resolveFile("/beneficios", root);
  assert.equal(resolved, path.join(root, "beneficios", "index.html"));
});

test("resolve clean URL para arquivo .html quando existir", async () => {
  const root = await makeRoot();
  const resolved = await resolveFile("/sobre", root);
  assert.equal(resolved, path.join(root, "sobre.html"));
});

test("fallback de clean URL desconhecida volta para a SPA raiz", async () => {
  const root = await makeRoot();
  const resolved = await resolveFile("/rota-inexistente", root);
  assert.equal(resolved, path.join(root, "index.html"));
});

test("bloqueia traversal e double-encoding malicioso", async () => {
  const root = await makeRoot();
  assert.equal(await resolveFile("/../package.json", root), null);
  assert.equal(await resolveFile("/%2e%2e/%2eenv", root), null);
});

test("bloqueia dotfiles, diretórios sensíveis e extensões fora da allowlist", async () => {
  const root = await makeRoot();
  assert.equal(await resolveFile("/.env", root), null);
  assert.equal(await resolveFile("/docs/private.html", root), null);
  assert.equal(await resolveFile("/malicioso.sh", root), null);
});

test("permite arquivos estáticos da allowlist", async () => {
  const root = await makeRoot();
  const resolved = await resolveFile("/app.js", root);
  assert.equal(resolved, path.join(root, "app.js"));
});

test("rejeita symlink mesmo quando aponta para arquivo existente", async () => {
  const root = await makeRoot();
  await fs.writeFile(path.join(root, "real.html"), "real");
  await fs.symlink(path.join(root, "real.html"), path.join(root, "atalho.html"));

  const resolved = await resolveFile("/atalho.html", root);
  assert.equal(resolved, null);
});