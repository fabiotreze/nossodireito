#!/usr/bin/env python3
"""Pre-commit PII scan (LGPD).

Scans staged files for Brazilian PII patterns. Blocks commit if found.
Run by .githooks/pre-commit. Standalone usage:
    python3 scripts/scan_pii.py file1 file2 ...
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Patterns target real PII, not schema/test fixtures.
# Each pattern: (name, regex, severity).
PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    # CPF: 11 digits, formatted or not. Excludes obvious placeholders.
    ("CPF", re.compile(r"\b(?!000\.?000\.?000)(?!111\.?111\.?111)\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "CRITICAL"),
    # RG: 8-10 digits with optional separators + check digit
    ("RG", re.compile(r"\bRG[:\s]+\d{1,2}\.?\d{3}\.?\d{3}-?[\dxX]\b"), "HIGH"),
    # CNPJ: 14 digits
    ("CNPJ", re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"), "MEDIUM"),
    # Real email addresses (not example.com / test domains)
    ("EMAIL", re.compile(r"\b[a-zA-Z0-9._%+-]+@(?!example\.|test\.|localhost|domain\.|email\.com)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"), "MEDIUM"),
    # Brazilian phone with DDD (11 digits)
    ("PHONE_BR", re.compile(r"\b\(?\d{2}\)?[\s-]?9?\d{4}[\s-]?\d{4}\b"), "LOW"),
    # API keys / tokens (generic high-entropy heuristic)
    ("BEARER_TOKEN", re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}"), "CRITICAL"),
    ("AZURE_KEY", re.compile(r"[a-zA-Z0-9+/]{86}=="), "HIGH"),  # base64 64-byte key
]

# Allowlist: paths that legitimately contain PII-like patterns (tests, schemas, docs).
ALLOWLIST_GLOBS = [
    "tests/",
    "schemas/",
    "docs/",
    "data/municipios_br.json",  # public IBGE data
    "scripts/scan_pii.py",      # this file
]

# In-file allowlist marker
IGNORE_MARKER = "pii-scan:ignore"


def is_allowlisted(path: str) -> bool:
    return any(path.startswith(p) or p in path for p in ALLOWLIST_GLOBS)


def scan_file(path: Path) -> list[tuple[int, str, str, str]]:
    """Return list of (line_no, pattern_name, severity, matched_text)."""
    findings: list[tuple[int, str, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return findings
    for lineno, line in enumerate(text.splitlines(), start=1):
        if IGNORE_MARKER in line:
            continue
        for name, pattern, severity in PATTERNS:
            m = pattern.search(line)
            if m:
                redacted = m.group(0)[:4] + "***" + m.group(0)[-2:] if len(m.group(0)) > 6 else "***"
                findings.append((lineno, name, severity, redacted))
    return findings


def main(argv: list[str]) -> int:
    files = [Path(a) for a in argv[1:] if Path(a).is_file()]
    if not files:
        return 0
    total_critical = 0
    for f in files:
        if is_allowlisted(str(f)):
            continue
        findings = scan_file(f)
        for lineno, name, severity, redacted in findings:
            print(f"[{severity}] {f}:{lineno} {name} -> {redacted}")
            if severity == "CRITICAL":
                total_critical += 1
    if total_critical > 0:
        print(f"\n  BLOQUEADO: {total_critical} achado(s) CRITICAL de PII/segredo.")
        print("  Use 'pii-scan:ignore' no fim da linha se for falso positivo.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
