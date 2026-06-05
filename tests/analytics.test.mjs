"use strict";

import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { createAnalytics } = require("../lib/analytics");

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