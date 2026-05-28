"use strict";

const RATE_LIMIT_WINDOW = 60_000; // 1 minute
const RATE_LIMIT_MAX = 120;

/**
 * Rate limiter adaptativo: tenta Redis (se configurado), cai para in-memory.
 *
 * Uso:
 *   const rl = createRateLimiter({
 *     redisConfigured: () => Boolean(process.env.REDIS_HOSTNAME),
 *     getRedisClient: () => redisClientPromise,
 *     onRedisError: (err) => { ... },
 *   });
 *   if (await rl.check(ip)) return tooManyRequests();
 */
function createRateLimiter({
  windowMs = RATE_LIMIT_WINDOW,
  max = RATE_LIMIT_MAX,
  redisConfigured = () => false,
  getRedisClient = async () => null,
  onRedisError = () => {},
} = {}) {
  const map = new Map();

  function checkMemory(ip) {
    const now = Date.now();
    if (map.size > 50000) map.clear(); // safety cap contra DDoS distribuído
    const entry = map.get(ip);
    if (!entry || now - entry.start > windowMs) {
      map.set(ip, { start: now, count: 1 });
      return false;
    }
    entry.count++;
    return entry.count > max;
  }

  async function checkRedis(ip) {
    const client = await getRedisClient();
    const key = `rate:${ip}`;
    const count = await client.incr(key);
    if (count === 1) {
      await client.expire(key, Math.ceil(windowMs / 1000));
    }
    return count > max;
  }

  async function check(ip) {
    if (!redisConfigured()) return checkMemory(ip);
    try {
      return await checkRedis(ip);
    } catch (err) {
      onRedisError(err);
      return checkMemory(ip);
    }
  }

  // Cleanup periódico
  const cleanupTimer = setInterval(() => {
    const now = Date.now();
    for (const [ip, entry] of map) {
      if (now - entry.start > windowMs) map.delete(ip);
    }
  }, 300_000);
  if (cleanupTimer.unref) cleanupTimer.unref();

  return { check, _map: map };
}

module.exports = { createRateLimiter };
