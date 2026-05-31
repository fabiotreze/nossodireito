"use strict";

/**
 * Cliente Redis com autenticação via Azure Key Vault.
 *
 * Pattern: lazy init (a credential, o SecretClient e o Redis só são
 * carregados quando algum consumidor chama getClient()). Isso mantém
 * o boot leve em ambientes que não usam Redis (dev local, testes).
 *
 * Uso:
 *   const redis = createRedisClient({
 *     enabled: process.env.REDIS_RATE_LIMIT_ENABLED === "true",
 *     hostname: process.env.REDIS_HOSTNAME,
 *     port: Number(process.env.REDIS_PORT || 6380),
 *     secretName: process.env.REDIS_SECRET_NAME || "redis-primary-key",
 *     keyVaultUri: process.env.KEY_VAULT_URI,
 *   });
 *   if (redis.configured()) {
 *     const client = await redis.getClient();
 *     await client.set("key", "value");
 *   }
 */
function createRedisClient({
  enabled,
  hostname,
  port = 6380,
  secretName = "redis-primary-key",
  keyVaultUri,
}) {
  let client = null;
  let initPromise = null;
  let initError = null;
  let secretClient = null;
  let credential = null;

  function getCredential() {
    if (!credential) {
      // Em App Service usamos Managed Identity direto: pular EnvironmentCredential
      // evita ruído de "CredentialUnavailableError" em telemetria (issue #250).
      if (process.env.WEBSITE_SITE_NAME) {
        const { ManagedIdentityCredential } = require("@azure/identity");
        credential = new ManagedIdentityCredential();
      } else {
        const { DefaultAzureCredential } = require("@azure/identity");
        credential = new DefaultAzureCredential();
      }
    }
    return credential;
  }

  function configured() {
    return Boolean(enabled && hostname && keyVaultUri);
  }

  async function getPassword() {
    if (!secretClient) {
      const { SecretClient } = require("@azure/keyvault-secrets");
      secretClient = new SecretClient(keyVaultUri, getCredential());
    }
    const secret = await secretClient.getSecret(secretName);
    if (!secret?.value) {
      throw new Error("Redis secret not found in Key Vault");
    }
    return secret.value;
  }

  async function getClient() {
    if (!configured()) {
      throw new Error("Redis rate limiting not configured");
    }
    if (client) return client;
    if (initPromise) return initPromise;

    initPromise = (async () => {
      const { createClient } = require("redis");
      const password = await getPassword();
      const c = createClient({
        socket: { host: hostname, port, tls: true },
        username: "default",
        password,
      });

      c.on("error", (err) => {
        initError = err;
        console.warn(`Redis client error: ${err.message}`);
      });

      await c.connect();
      client = c;
      return c;
    })().catch((err) => {
      initError = err;
      initPromise = null;
      throw err;
    });

    return initPromise;
  }

  return {
    configured,
    getClient,
    get initError() {
      return initError;
    },
    set initError(err) {
      initError = err;
    },
    async quit() {
      if (client) {
        try {
          await client.quit();
        } catch {
          /* noop */
        }
        client = null;
      }
    },
  };
}

module.exports = { createRedisClient };
