"use strict";

const crypto = require("node:crypto");

/**
 * Privacy-Respecting Visitor Analytics (LGPD-compliant).
 *
 * - Zero cookies, zero fingerprinting, zero PII stored.
 * - IPs anonimizados via SHA-256 com salt aleatório rotacionado diariamente.
 * - Apenas contadores agregados em memória (reset diário).
 * - Métricas opcionalmente encaminhadas ao Application Insights.
 *
 * Uso:
 *   const analytics = createAnalytics({ getAppInsightsClient: () => client || null });
 *   analytics.track(ip, ua, urlPath);
 *   analytics.snapshot(); // estado atual (para /api/admin/analytics)
 */
function createAnalytics({ getAppInsightsClient = () => null } = {}) {
  const state = {
    salt: crypto.randomBytes(32).toString("hex"),
    date: new Date().toISOString().slice(0, 10),
    pageViews: 0,
    uniqueVisitors: new Set(),
    byDevice: { desktop: 0, mobile: 0, tablet: 0 },
    byPath: new Map(),
    hourly: new Array(24).fill(0),
    history: [],
  };

  function rotateIfNeeded() {
    const today = new Date().toISOString().slice(0, 10);
    if (today === state.date) return;

    state.history.push({
      date: state.date,
      views: state.pageViews,
      visitors: state.uniqueVisitors.size,
      devices: { ...state.byDevice },
      topPages: [...state.byPath.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([p, c]) => ({ path: p, views: c })),
    });
    if (state.history.length > 30) state.history.shift();

    const client = getAppInsightsClient();
    if (client) {
      client.trackMetric({ name: "daily_unique_visitors", value: state.uniqueVisitors.size });
      client.trackMetric({ name: "daily_page_views", value: state.pageViews });
      client.trackMetric({ name: "daily_desktop", value: state.byDevice.desktop });
      client.trackMetric({ name: "daily_mobile", value: state.byDevice.mobile });
      client.trackMetric({ name: "daily_tablet", value: state.byDevice.tablet });
    }

    state.salt = crypto.randomBytes(32).toString("hex");
    state.date = today;
    state.pageViews = 0;
    state.uniqueVisitors = new Set();
    state.byDevice = { desktop: 0, mobile: 0, tablet: 0 };
    state.byPath = new Map();
    state.hourly = new Array(24).fill(0);
  }

  function track(ip, ua, urlPath) {
    rotateIfNeeded();

    const hash = crypto
      .createHash("sha256")
      .update(state.salt + ip)
      .digest("hex")
      .slice(0, 16);
    const isNew = !state.uniqueVisitors.has(hash);
    state.uniqueVisitors.add(hash);

    state.pageViews++;

    const device = detectDevice(ua);
    if (isNew) state.byDevice[device]++;

    const safePath = urlPath.split("?")[0].slice(0, 100);
    state.byPath.set(safePath, (state.byPath.get(safePath) || 0) + 1);
    if (state.byPath.size > 500) {
      const sorted = [...state.byPath.entries()].sort((a, b) => b[1] - a[1]).slice(0, 100);
      state.byPath = new Map(sorted);
    }

    const hour = new Date().getHours();
    state.hourly[hour]++;

    const client = getAppInsightsClient();
    if (isNew && client) {
      client.trackEvent({ name: "unique_visit", properties: { device, path: safePath } });
    }
    if (client) {
      client.trackPageView({ name: safePath, url: safePath, properties: { device } });
    }
  }

  function snapshot() {
    return {
      date: state.date,
      pageViews: state.pageViews,
      uniqueVisitors: state.uniqueVisitors.size,
      byDevice: { ...state.byDevice },
      byPath: [...state.byPath.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 20)
        .map(([p, c]) => ({ path: p, views: c })),
      hourly: [...state.hourly],
      history: [...state.history],
    };
  }

  return { track, snapshot, rotateIfNeeded };
}

/**
 * Detect device type from User-Agent (broad categories — no fingerprinting).
 * Security: regex sem backtracking polinomial (CodeQL js/polynomial-redos).
 */
function detectDevice(ua) {
  if (!ua) return "desktop";
  if (/tablet|ipad|playbook|silk/i.test(ua)) return "tablet";
  if (/mobile|iphone|ipod|windows phone|blackberry/i.test(ua)) return "mobile";
  if (/android/i.test(ua) && /mobile/i.test(ua)) return "mobile";
  return "desktop";
}

module.exports = { createAnalytics, detectDevice };
