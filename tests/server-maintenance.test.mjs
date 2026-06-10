"use strict";

import { before, after, test } from "node:test";
import assert from "node:assert/strict";
import fsPromises from "node:fs/promises";
import os from "node:os";
import path from "node:path";
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
          if (Date.now() > deadline) return reject(new Error("server not ready"));
          setTimeout(tryOnce, 100);
        },
      );
      req.on("error", () => {
        if (Date.now() > deadline) return reject(new Error("server not ready"));
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
            body: Buffer.concat(chunks).toString("utf8"),
          }),
        );
      },
    );
    req.on("error", reject);
    req.end();
  });
}

before(async () => {
  tempRoot = await fsPromises.mkdtemp(path.join(os.tmpdir(), "nd-maint-"));
  await fsPromises.writeFile(path.join(tempRoot, "index.html"), "<!doctype html><title>ok</title>");

  serverPort = await getFreePort();

  serverProcess = spawn(process.execPath, [path.join(repoRoot, "server.js")], {
    cwd: repoRoot,
    env: {
      ...process.env,
      PORT: String(serverPort),
      STATIC_ROOT: tempRoot,
      NODE_ENV: "test",
      MAINTENANCE_MODE: "true",
      ALLOWED_HOSTS: "127.0.0.1,localhost",
    },
    stdio: ["ignore", "pipe", "pipe"],
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

test("maintenance mode returns 503 for public routes", async () => {
  const res = await fetchRaw(serverPort, "/");
  assert.equal(res.status, 503);
  assert.match(String(res.headers["content-type"] || ""), /text\/html/i);
  assert.match(res.body, /manuten/i);
});

test("maintenance mode keeps /health available", async () => {
  const res = await fetchRaw(serverPort, "/health");
  assert.equal(res.status, 200);
});
