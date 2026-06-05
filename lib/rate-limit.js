"use strict";

const RATE_LIMIT_WINDOW = 60_000; // 1 minute
const RATE_LIMIT_MAX = 120;

/**
 * Rate limiter adaptativo sem identificador por cliente.
 *
 * Para cumprir a política de zero coleta de dados pessoais, o controle de
 * abuso usa um bucket global por janela, sem armazenar IP ou qualquer outro
 * identificador do request. Isso reduz precisão/fairness, mas elimina coleta
 * residual na origem.
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
  redisConfigured = () => false,
  getRedisClient = async () => null,
  onRedisError = () => {},
} = {}) {
  let memoryEntry = null;

  function checkMemory() {
    const now = Date.now();
    if (!memoryEntry || now - memoryEntry.start > windowMs) {
      memoryEntry = { start: now, count: 1 };
      return false;
    }
    memoryEntry.count++;
    return memoryEntry.count > max;
  }

  async function checkRedis() {
    const client = await getRedisClient();
    const key = "rate:global";
    const count = await client.incr(key);
    if (count === 1) {
      await client.expire(key, Math.ceil(windowMs / 1000));
    }
    return count > max;
  }

  async function check() {
    if (!redisConfigured()) return checkMemory();
    try {
      return await checkRedis();
    } catch (err) {
      onRedisError(err);
      return checkMemory();
    }
  }

  // Cleanup periódico
  const cleanupTimer = setInterval(() => {
    const now = Date.now();
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
