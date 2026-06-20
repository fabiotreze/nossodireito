"use strict";

import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { createAnalytics } = require("../lib/analytics");
const { createStatsHandler } = require("../lib/infra-handlers");

test("analytics agrega sem identificador por visitante", () => {
  const analytics = createAnalytics();

  analytics.track("Mozilla/5.0 (iPhone)", "/guia?utm_source=test");
  analytics.track("Mozilla/5.0 (Windows NT 10.0)", "/guia");

  const snapshot = analytics.snapshot();
  assert.equal(snapshot.pageViews, 2);
  assert.equal(snapshot.uniqueVisitors, 0);
  assert.equal(snapshot.byDevice.mobile, 1);
  assert.equal(snapshot.byDevice.desktop, 1);
  assert.deepEqual(
    snapshot.byPath.map((p) => p.path),
    ["/guia"],
  );
});

test("stats handler expõe snapshot agregado sem acessar estado interno", async () => {
  const analytics = createAnalytics();
  analytics.track("Mozilla/5.0 (Android Mobile)", "/privacidade.html?utm=1");

  const handler = createStatsHandler({
    analytics,
    rotateIfNeeded: () => analytics.rotateIfNeeded(),
    securityHeaders: {},
  });

  const res = {
    statusCode: 0,
    headers: {},
    body: "",
    writeHead(statusCode, headers) {
      this.statusCode = statusCode;
      this.headers = headers;
    },
    end(body = "") {
      this.body = body;
    },
  };

  handler({ url: "/api/stats", headers: { host: "localhost" } }, res);

  assert.equal(res.statusCode, 200);
  const payload = JSON.parse(res.body);
  assert.equal(payload.today.pageViews, 1);
  assert.equal(payload.today.uniqueVisitors, 0);
  assert.deepEqual(payload.today.topPages, [{ path: "/privacidade.html", views: 1 }]);
  assert.match(payload.privacy, /contadores agregados sem IP, sessão ou identificador/);
});