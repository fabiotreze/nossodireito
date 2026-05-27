"use strict";

// ── Security Headers (EASM-hardened) ──
// Covers: OWASP Secure Headers, Mozilla Observatory, Qualys SSL Labs
// Note: upgrade-insecure-requests is added dynamically only in production
// (not on localhost) — would force HTTPS on a server without TLS.
const IS_PRODUCTION = !!(process.env.WEBSITE_SITE_NAME || process.env.NODE_ENV === "production");

const CSP_DIRECTIVES = [
  "default-src 'none'",
  "script-src 'self' blob: https://cdnjs.cloudflare.com https://vlibras.gov.br https://*.vlibras.gov.br https://cdn.jsdelivr.net 'unsafe-eval' 'wasm-unsafe-eval'",
  "script-src-elem 'self' blob: https://vlibras.gov.br https://*.vlibras.gov.br https://cdnjs.cloudflare.com https://cdn.jsdelivr.net",
  "style-src 'self' 'unsafe-inline' https://*.vlibras.gov.br https://cdn.jsdelivr.net",
  "img-src 'self' data: blob: https://vlibras.gov.br https://*.vlibras.gov.br https://cdn.jsdelivr.net",
  "connect-src 'self' https://vlibras.gov.br https://*.vlibras.gov.br https://cdn.jsdelivr.net https://cdnjs.cloudflare.com data:",
  "worker-src 'self' blob: https://cdnjs.cloudflare.com https://vlibras.gov.br https://*.vlibras.gov.br",
  "child-src blob:",
  "frame-src 'self' https://*.vlibras.gov.br blob:",
  "media-src 'self' https://*.vlibras.gov.br",
  "font-src 'self' https://vlibras.gov.br https://*.vlibras.gov.br https://cdn.jsdelivr.net",
  "form-action 'none'",
  "base-uri 'self'",
  "frame-ancestors 'none'",
  "manifest-src 'self'",
];
if (IS_PRODUCTION) CSP_DIRECTIVES.push("upgrade-insecure-requests");

const SECURITY_HEADERS = Object.freeze({
  "Content-Security-Policy": CSP_DIRECTIVES.join("; "),
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  // accelerometer/gyroscope/magnetometer = self → VLibras Unity WebGL precisa
  "Permissions-Policy":
    "camera=(), microphone=(), geolocation=(), payment=(), usb=(), serial=(), hid=(), accelerometer=(self), gyroscope=(self), magnetometer=(self), screen-wake-lock=()",
  "Cross-Origin-Opener-Policy": "same-origin",
  "Cross-Origin-Resource-Policy": "cross-origin",
  // COEP unsafe-none: VLibras assets cross-origin sem CORP; require-corp quebra Safari/iOS.
  "Cross-Origin-Embedder-Policy": "unsafe-none",
  "X-Permitted-Cross-Domain-Policies": "none",
  "X-DNS-Prefetch-Control": "off",
  "X-Download-Options": "noopen",
});

module.exports = { IS_PRODUCTION, CSP_DIRECTIVES, SECURITY_HEADERS };
