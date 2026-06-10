"use strict";

import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { createRateLimiter } = require("../lib/rate-limit");

test("memory mode: bloqueia apenas acima do limite", async () => {
  const rl = createRateLimiter({ windowMs: 60_000, max: 3, redisConfigured: () => false });

  assert.equal(await rl.check("1.1.1.1"), false);
  assert.equal(await rl.check("1.1.1.1"), false);
  assert.equal(await rl.check("1.1.1.1"), false);
  assert.equal(await rl.check("1.1.1.1"), true);
});

test("memory mode: reinicia contagem quando a janela expira", async () => {
  let now = 1_000;
  const originalNow = Date.now;
  Date.now = () => now;

  try {
    const rl = createRateLimiter({ windowMs: 100, max: 2, redisConfigured: () => false });

    assert.equal(await rl.check("2.2.2.2"), false);
    assert.equal(await rl.check("2.2.2.2"), false);
    assert.equal(await rl.check("2.2.2.2"), true);

    now += 101;
    assert.equal(await rl.check("2.2.2.2"), false);
  } finally {
    Date.now = originalNow;
  }
});

test("redis mode: usa incr/expire e aplica limite", async () => {
  let counter = 0;
  let expireCalls = 0;

  const fakeRedis = {
    incr: async () => {
      counter += 1;
      return counter;
    },
    expire: async () => {
      expireCalls += 1;
      return 1;
    },
  };

  const rl = createRateLimiter({
    windowMs: 60_000,
    max: 2,
    redisConfigured: () => true,
    getRedisClient: async () => fakeRedis,
  });

  assert.equal(await rl.check("3.3.3.3"), false);
  assert.equal(await rl.check("3.3.3.3"), false);
  assert.equal(await rl.check("3.3.3.3"), true);
  assert.equal(expireCalls, 1);
});

test("redis mode com falha: cai para memória e chama callback de erro", async () => {
  let onErrorCalls = 0;

  const rl = createRateLimiter({
    windowMs: 60_000,
    max: 1,
    redisConfigured: () => true,
    getRedisClient: async () => {
      throw new Error("redis down");
    },
    onRedisError: () => {
      onErrorCalls += 1;
    },
  });

  assert.equal(await rl.check("4.4.4.4"), false);
  assert.equal(await rl.check("4.4.4.4"), true);
  assert.equal(onErrorCalls, 2);
});

test("memory mode: contador e global, sem chave por IP", async () => {
  const rl = createRateLimiter({ windowMs: 60_000, max: 2, redisConfigured: () => false });

  assert.equal(await rl.check("1.1.1.1"), false);
  assert.equal(await rl.check("2.2.2.2"), false);
  assert.equal(await rl.check("3.3.3.3"), true);
  assert.equal(typeof rl._state.memoryEntry.count, "number");
});

test("keyed memory mode: contadores por chave são independentes", async () => {
  const rl = createRateLimiter({
    windowMs: 60_000,
    max: 1,
    strategy: "keyed",
    keySalt: "test-salt",
    redisConfigured: () => false,
  });

  assert.equal(await rl.check("ip-a"), false);
  assert.equal(await rl.check("ip-b"), false);
  assert.equal(await rl.check("ip-a"), true);
  assert.equal(await rl.check("ip-b"), true);
});

test("keyed redis mode: usa prefixo rate:key para contagem segregada", async () => {
  const seenKeys = [];
  const counters = new Map();
  const fakeRedis = {
    incr: async (key) => {
      seenKeys.push(key);
      const cur = (counters.get(key) || 0) + 1;
      counters.set(key, cur);
      return cur;
    },
    expire: async () => 1,
  };

  const rl = createRateLimiter({
    windowMs: 60_000,
    max: 1,
    strategy: "keyed",
    keySalt: "test-salt",
    redisConfigured: () => true,
    getRedisClient: async () => fakeRedis,
  });

  assert.equal(await rl.check("ip-a"), false);
  assert.equal(await rl.check("ip-b"), false);
  assert.equal(await rl.check("ip-a"), true);

  assert.ok(seenKeys.every((k) => k.startsWith("rate:key:")));
  assert.equal(new Set(seenKeys).size >= 2, true);
});