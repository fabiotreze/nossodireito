"use strict";

const crypto = require("node:crypto");

const RATE_LIMIT_WINDOW = 60_000; // 1 minute
const RATE_LIMIT_MAX = 120;

/**
 * Rate limiter adaptativo sem identificador por cliente.
 *
 * Para cumprir a política de minimização, o controle de abuso usa um bucket
 * global por janela, sem armazenar IP ou qualquer outro identificador do
 * request. Isso reduz precisão/fairness, mas elimina coleta residual na origem.
 *
 * Uso:
 *   const rl = createRateLimiter({
 *     redisConfigured: () => Boolean(process.env.REDIS_HOSTNAME),
 *     getRedisClient: () => redisClientPromise,
 *     onRedisError: (err) => { ... },
 *   });
 *   if (await rl.check()) return tooManyRequests();
 */
function createRateLimiter({
  windowMs = RATE_LIMIT_WINDOW,
  max = RATE_LIMIT_MAX,
  strategy = "global", // global | keyed
  keySalt = "",
  redisConfigured = () => false,
  getRedisClient = async () => null,
  onRedisError = () => {},
} = {}) {
  let memoryEntry = null;
  const memoryKeyed = new Map();

  function makeKey(identifier = "") {
    if (strategy !== "keyed") return "rate:global";
    const normalized = String(identifier || "").trim();
    if (!normalized) return "rate:global";
    // Store only deterministic hashes, never raw client identifiers.
    const digest = crypto
      .createHash("sha256")
      .update(`${keySalt}:${normalized}`)
      .digest("hex")
      .slice(0, 24);
    return `rate:key:${digest}`;
  }

  function checkMemory(identifier) {
    if (strategy === "keyed") {
      const now = Date.now();
      const key = makeKey(identifier);
      const current = memoryKeyed.get(key);
      if (!current || now - current.start > windowMs) {
        memoryKeyed.set(key, { start: now, count: 1 });
        return false;
      }
      current.count++;
      memoryKeyed.set(key, current);
      return current.count > max;
    }

    const now = Date.now();
    if (!memoryEntry || now - memoryEntry.start > windowMs) {
      memoryEntry = { start: now, count: 1 };
      return false;
    }
    memoryEntry.count++;
    return memoryEntry.count > max;
  }

  async function checkRedis(identifier) {
    const client = await getRedisClient();
    const key = makeKey(identifier);
    const count = await client.incr(key);
    if (count === 1) {
      await client.expire(key, Math.ceil(windowMs / 1000));
    }
    return count > max;
  }

  async function check(identifier = "") {
    if (!redisConfigured()) return checkMemory(identifier);
    try {
      return await checkRedis(identifier);
    } catch (err) {
      onRedisError(err);
      return checkMemory(identifier);
    }
  }

  // Cleanup periódico
  const cleanupTimer = setInterval(() => {
    const now = Date.now();
    if (strategy === "keyed") {
      for (const [key, entry] of memoryKeyed.entries()) {
        if (now - entry.start > windowMs) memoryKeyed.delete(key);
      }
    }
    if (memoryEntry && now - memoryEntry.start > windowMs) {
      memoryEntry = null;
    }
  }, 300_000);
  if (cleanupTimer.unref) cleanupTimer.unref();

  return {
    check,
    _state: {
      get memoryEntry() {
        return memoryEntry;
      },
    },
  };
}

module.exports = { createRateLimiter };
