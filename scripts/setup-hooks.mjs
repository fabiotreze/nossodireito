#!/usr/bin/env node
/**
 * setup-hooks.mjs — npm `prepare` hook for NossoDireito.
 *
 * 1. Sets git config core.hooksPath to .githooks/ so all hooks in that dir
 *    fire automatically (otherwise .git/hooks/ is used, which isn't tracked).
 * 2. Marks hook scripts executable on POSIX (Windows ignores file mode bits;
 *    git Bash on Windows uses git's index +x bit which we don't touch here).
 *
 * Idempotent + silent on failure (no-op if not inside a git repo, e.g. when
 * running from a tarball / docker layer install).
 */
import { execSync } from 'node:child_process';
import { readdirSync, chmodSync } from 'node:fs';
import { join } from 'node:path';

const HOOK_DIR = '.githooks';
const POSIX_EXEC = 0o755;

try {
  execSync(`git config core.hooksPath ${HOOK_DIR}`, { stdio: 'ignore' });
} catch {
  // Not a git checkout (e.g. npm install from tarball) — silently skip.
  process.exit(0);
}

if (process.platform !== 'win32') {
  try {
    for (const file of readdirSync(HOOK_DIR)) {
      try {
        chmodSync(join(HOOK_DIR, file), POSIX_EXEC);
      } catch {
        /* per-file failure is non-fatal */
      }
    }
  } catch {
    // Hooks dir missing (fresh repo) — fine.
  }
}
