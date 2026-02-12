#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import subprocess
import sys

# Executar analise360.py e capturar output
result = subprocess.run(
    [sys.executable, 'scripts/analise360.py'],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)

print("=" * 80)
print("RETURN CODE:", result.returncode)
print("=" * 80)
print("OUTPUT DO ANALISE360.PY (STDOUT):")
print("=" * 80)
print(repr(result.stdout))
print(f"\nTamanho stdout: {len(result.stdout)} caracteres")
print("\n" + "=" * 80)
print("STDERR:")
print("=" * 80)
print(repr(result.stderr))
print("\n" + "=" * 80)
print("TESTES DE REGEX:")
print("=" * 80)

output = result.stdout

# Testar regex de cobertura
coverage_match = re.search(r'COBERTURA TOTAL.*?(\d+\.\d+)%', output)
print(f"\n1. Regex Cobertura: {coverage_match.group(1) if coverage_match else 'NOT FOUND'}")
if coverage_match:
    print(f"   Match completo: '{coverage_match.group(0)}'")

# Testar regex de implementados
impl_match = re.search(r'Implementados completos:\s*(\d+)/\d+', output)
print(f"\n2. Regex Implementados: {impl_match.group(1) if impl_match else 'NOT FOUND'}")
if impl_match:
    print(f"   Match completo: '{impl_match.group(0)}'")

# Testar regex de estados IPVA
ipva_match = re.search(r'(\d+)\s+estados mapeados', output)
print(f"\n3. Regex IPVA: {ipva_match.group(1) if ipva_match else 'NOT FOUND'}")
if ipva_match:
    print(f"   Match completo: '{ipva_match.group(0)}'")
