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
        client_IP: "203.0.113.10",
        client_City: "Cotia",
        client_CountryOrRegion: "Brazil",
        user_Id: "user-123",
        session_Id: "session-789",
        properties: {
          "User-Agent": "Mozilla/5.0",
          Referer: "https://example.com",
          "X-Forwarded-For": "203.0.113.10",
          "client-ip": "203.0.113.10",
          client_City: "Cotia",
          client_CountryOrRegion: "Brazil",
          user_Id: "user-123",
          session_Id: "session-789",
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
  assert.equal(envelope.data.baseData.client_IP, undefined);
  assert.equal(envelope.data.baseData.client_City, undefined);
  assert.equal(envelope.data.baseData.client_CountryOrRegion, undefined);
  assert.equal(envelope.data.baseData.user_Id, undefined);
  assert.equal(envelope.data.baseData.session_Id, undefined);
  assert.deepEqual(envelope.data.baseData.properties, {
    safe: "value",
  });
});