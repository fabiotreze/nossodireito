"use strict";

/**
 * server-compression.test.mjs — Regression test for the 2026-05-30 SEV2 fix.
 *
 * Validates two perf invariants of the static handler:
 *   1. Pre-compressed siblings (.br, .gz) are served directly when available,
 *      with the correct Content-Encoding and zero CPU at request time.
 *   2. On-the-fly Brotli falls back to a low quality (q4) and never returns
 *      uncompressed bytes when the client accepts br and the file is in the
 *      COMPRESSIBLE allowlist.
 *
 * Approach: spawn the production server.js with a temp ROOT containing a
 * crafted asset tree, hit it over HTTP, and assert headers / payload size.
 */

import { before, after, test } from "node:test";
import assert from "node:assert/strict";
import fsPromises from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import zlib from "node:zlib";
import http from "node:http";
import { spawn } from "node:child_process";

const repoRoot = path.resolve(new URL("..", import.meta.url).pathname);

let tempRoot;
let serverProcess;
let serverPort;

function getFreePort() {
  return new Promise((resolve, reject) => {
    const probe = http.createServer();
    probe.listen(0, "127.0.0.1", () => {
      const { port } = probe.address();
      probe.close(() => resolve(port));
    });
    probe.on("error", reject);
  });
}

function waitForReady(port, timeoutMs = 8000) {
  const deadline = Date.now() + timeoutMs;
  return new Promise((resolve, reject) => {
    const tryOnce = () => {
      const req = http.request(
        {
          host: "127.0.0.1",
          port,
          path: "/health",
          method: "GET",
          timeout: 500,
        },
        (res) => {
          res.resume();
          if (res.statusCode === 200) return resolve();
          if (Date.now() > deadline) {
            return reject(new Error(`server not ready (status ${res.statusCode})`));
          }
          setTimeout(tryOnce, 100);
        },
      );
      req.on("error", () => {
        if (Date.now() > deadline) return reject(new Error("server not ready (no response)"));
        setTimeout(tryOnce, 100);
      });
      req.end();
    };
    tryOnce();
  });
}

function fetchRaw(port, urlPath, headers = {}) {
  return new Promise((resolve, reject) => {
    const req = http.request(
      {
        host: "127.0.0.1",
        port,
        path: urlPath,
        method: "GET",
        headers,
        timeout: 5000,
      },
      (res) => {
        const chunks = [];
        res.on("data", (c) => chunks.push(c));
        res.on("end", () =>
          resolve({
            status: res.statusCode,
            headers: res.headers,
            body: Buffer.concat(chunks),
          }),
        );
      },
    );
    req.on("error", reject);
    req.end();
  });
}

before(async () => {
  tempRoot = await fsPromises.mkdtemp(path.join(os.tmpdir(), "nd-compress-"));

  // Minimal asset tree the server can serve.
  await fsPromises.writeFile(path.join(tempRoot, "index.html"), "<!doctype html><title>t</title>");

  // Large JSON — exercises the compression path.
  const big = JSON.stringify({
    rows: Array.from({ length: 2000 }, (_, i) => ({
      id: i,
      name: `direito-${i}`,
      desc: "lorem ipsum dolor sit amet consectetur adipiscing elit ".repeat(4),
    })),
  });
  await fsPromises.mkdir(path.join(tempRoot, "data"), { recursive: true });
  const jsonPath = path.join(tempRoot, "data", "big.json");
  await fsPromises.writeFile(jsonPath, big);

  // Pre-compressed sibling (.br) — server must prefer this.
  const brBytes = zlib.brotliCompressSync(big, {
    params: { [zlib.constants.BROTLI_PARAM_QUALITY]: 11 },
  });
  await fsPromises.writeFile(`${jsonPath}.br`, brBytes);

  // JSON with NO pre-compressed sibling — exercises on-the-fly q4.
  const otherPath = path.join(tempRoot, "data", "other.json");
  await fsPromises.writeFile(otherPath, big);

  serverPort = await getFreePort();

  serverProcess = spawn(process.execPath, [path.join(repoRoot, "server.js")], {
    cwd: repoRoot,
    env: {
      ...process.env,
      PORT: String(serverPort),
      STATIC_ROOT: tempRoot,
      NODE_ENV: "test",
      // Disable optional integrations that try to reach external services.
      DISABLE_REDIS: "1",
      KEYVAULT_NAME: "",
      OPENAI_ENDPOINT: "",
      AZURE_CLIENT_ID: "",
      ALLOWED_HOSTS: "127.0.0.1,localhost",
    },
    stdio: ["ignore", "pipe", "pipe"],
  });

  serverProcess.stderr.on("data", (d) => {
    if (process.env.DEBUG_TEST) process.stderr.write(`[srv] ${d}`);
  });

  await waitForReady(serverPort);
});

after(async () => {
  if (serverProcess && !serverProcess.killed) {
    serverProcess.kill("SIGTERM");
    await new Promise((r) => setTimeout(r, 200));
    if (!serverProcess.killed) serverProcess.kill("SIGKILL");
  }
  if (tempRoot) await fsPromises.rm(tempRoot, { recursive: true, force: true });
});

test("serves the pre-compressed .br sibling when client accepts br", async () => {
  const res = await fetchRaw(serverPort, "/data/big.json", {
    "Accept-Encoding": "br, gzip",
  });
  assert.equal(res.status, 200);
  assert.equal(res.headers["content-encoding"], "br");
  assert.equal(res.headers["vary"], "Accept-Encoding");

  // Body must match the pre-baked .br sibling byte-for-byte.
  const expected = await fsPromises.readFile(
    path.join(tempRoot, "data", "big.json.br"),
  );
  assert.equal(Number(res.headers["content-length"]), expected.length);
  assert.deepEqual(Buffer.from(res.body), expected);
});

test("falls back to on-the-fly Brotli (q4) when no sibling exists", async () => {
  const res = await fetchRaw(serverPort, "/data/other.json", {
    "Accept-Encoding": "br",
  });
  assert.equal(res.status, 200);
  assert.equal(res.headers["content-encoding"], "br");

  const original = await fsPromises.readFile(
    path.join(tempRoot, "data", "other.json"),
  );
  const decoded = zlib.brotliDecompressSync(res.body);
  assert.deepEqual(decoded, original);
  // Sanity: response should be substantially smaller than the source.
  assert.ok(
    res.body.length < original.length * 0.5,
    `compressed body too large: ${res.body.length} vs ${original.length}`,
  );
});

test("serves uncompressed when client does not accept any supported encoding", async () => {
  const res = await fetchRaw(serverPort, "/data/big.json", {
    "Accept-Encoding": "identity",
  });
  assert.equal(res.status, 200);
  assert.equal(res.headers["content-encoding"], undefined);
  const original = await fsPromises.readFile(path.join(tempRoot, "data", "big.json"));
  assert.deepEqual(Buffer.from(res.body), original);
});
