"use strict";

import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { sanitizeTelemetryEnvelope } = require("../lib/telemetry-sanitizer");

test("sanitizeTelemetryEnvelope remove identificadores e geolocalizacao", () => {
  const envelope = {
    tags: {
      "ai.location.ip": "203.0.113.10",
      "ai.location.city": "Cotia",
      "ai.location.province": "Sao Paulo",
      "ai.location.country": "Brazil",
      "ai.user.id": "user-123",
      "ai.user.authUserId": "auth-456",
      "ai.session.id": "session-789",
      "ai.operation.id": "keep-me",
    },
    data: {
      baseData: {
        url: "https://nossodireito.fabiotreze.com/?utm_source=test",
        properties: {
          "User-Agent": "Mozilla/5.0",
          Referer: "https://example.com",
          "X-Forwarded-For": "203.0.113.10",
          "client-ip": "203.0.113.10",
          safe: "value",
        },
      },
    },
  };

  assert.equal(sanitizeTelemetryEnvelope(envelope), true);
  assert.deepEqual(envelope.tags, {
    "ai.operation.id": "keep-me",
  });
  assert.equal(envelope.data.baseData.url, "https://nossodireito.fabiotreze.com/");
  assert.deepEqual(envelope.data.baseData.properties, {
    safe: "value",
  });
});