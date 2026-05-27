"use strict";

// MIME types (strict allowlist)
const MIME = Object.freeze({
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".ico": "image/x-icon",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
  ".txt": "text/plain; charset=utf-8",
  ".xml": "application/xml; charset=utf-8",
});

// Cache policies (seconds)
const CACHE = Object.freeze({
  ".html": "public, max-age=300, stale-while-revalidate=300",
  ".json": "public, max-age=3600, stale-while-revalidate=600",
  ".css": "public, max-age=2592000, immutable",
  ".js": "public, max-age=2592000, immutable",
  ".png": "public, max-age=2592000, immutable",
  ".jpg": "public, max-age=2592000, immutable",
  ".jpeg": "public, max-age=2592000, immutable",
  ".ico": "public, max-age=2592000, immutable",
  ".svg": "public, max-age=2592000, immutable",
  ".webp": "public, max-age=2592000, immutable",
  ".xml": "public, max-age=3600, stale-while-revalidate=600",
  ".txt": "public, max-age=86400",
});

// Allowed file extensions (whitelist — reject everything else)
const ALLOWED_EXT = new Set(Object.keys(MIME));

// Compressible types
const COMPRESSIBLE = new Set([".html", ".css", ".js", ".json", ".svg", ".txt", ".xml"]);

module.exports = { MIME, CACHE, ALLOWED_EXT, COMPRESSIBLE };
