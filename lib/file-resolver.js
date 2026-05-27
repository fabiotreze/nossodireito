"use strict";

const path = require("node:path");
const fsPromises = require("node:fs/promises");
const { ALLOWED_EXT } = require("./mime");

// Blocked directories
const BLOCKED_DIRS = new Set(["terraform", "node_modules", "tests", ".github", "docs", "__pycache__"]);

// Max URL length (CWE-400 — prevent URL buffer attacks)
const MAX_URL_LENGTH = 2048;

/**
 * Resolve URL path para arquivo físico, com defesa-em-profundidade contra:
 * - Null-byte injection (CWE-158)
 * - URL oversize (CWE-400)
 * - Control chars (CWE-116)
 * - Directory traversal (CWE-22), inclusive double-encoded
 * - Dotfiles e dirs sensíveis (.env, .git, terraform, node_modules)
 * - Extensões fora do whitelist
 * - Symlinks
 *
 * Clean-URL: tenta /foo/index.html, /foo.html, fallback SPA /index.html.
 *
 * @param {string} urlPath - path da URL (já sem querystring)
 * @param {string} root - diretório raiz (absoluto)
 * @returns {Promise<string|null>} caminho absoluto do arquivo ou null se inválido
 */
async function resolveFile(urlPath, root) {
  if (urlPath.includes("\0")) return null;
  if (urlPath.length > MAX_URL_LENGTH) return null;
  if (/[\x00-\x1f\x7f]/.test(urlPath)) return null;

  let filePath;
  try {
    filePath = path.normalize(decodeURIComponent(urlPath));
  } catch {
    return null;
  }

  if (filePath.includes("..")) return null;

  if (filePath === "/" || filePath === "\\") filePath = "/index.html";

  const fullPath = path.join(root, filePath);

  if (!fullPath.startsWith(root + path.sep) && fullPath !== root) return null;

  const relative = path.relative(root, fullPath);
  const segments = relative.split(path.sep);
  if (segments.some((seg) => seg.startsWith("."))) return null;

  if (BLOCKED_DIRS.has(segments[0].toLowerCase())) return null;

  const ext = path.extname(fullPath).toLowerCase();
  if (ext && !ALLOWED_EXT.has(ext)) return null;

  // Clean-URL: extensionless paths
  if (!ext) {
    const dirIndex = path.join(fullPath, "index.html");
    try {
      const stat = await fsPromises.lstat(dirIndex);
      if (stat.isFile() && !stat.isSymbolicLink()) return dirIndex;
    } catch {
      /* not a directory or missing */
    }
    const asHtml = `${fullPath}.html`;
    try {
      const stat = await fsPromises.lstat(asHtml);
      if (stat.isFile() && !stat.isSymbolicLink()) return asHtml;
    } catch {
      /* missing */
    }
    return path.join(root, "index.html");
  }

  try {
    const stat = await fsPromises.lstat(fullPath);
    if (stat.isFile() && !stat.isSymbolicLink()) return fullPath;
  } catch {
    /* missing */
  }

  return null;
}

module.exports = { resolveFile, BLOCKED_DIRS, MAX_URL_LENGTH };
