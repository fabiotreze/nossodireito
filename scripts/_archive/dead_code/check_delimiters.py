#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check delimiters in app.js"""

from pathlib import Path

root = Path(__file__).parent.parent
js_file = root / 'js' / 'app.js'

content = js_file.read_text(encoding='utf-8')

print(f"Contagem de delimitadores em app.js:")
print(f"  {{: {content.count('{')}")
print(f"  }}: {content.count('}')}")
print(f"  (: {content.count('(')}")
print(f"  ): {content.count(')')}")
print(f"  [: {content.count('[')}")
print(f"  ]: {content.count(']')}")

if content.count('{') == content.count('}'):
    print(f"\n✅ Chaves balanceadas")
else:
    print(f"\n❌ Chaves desbalanceadas (diff: {content.count('{') - content.count('}')}")

if content.count('(') == content.count(')'):
    print(f"✅ Parênteses balanceados")
else:
    print(f"❌ Parênteses desbalanceados (diff: {content.count('(') - content.count(')')})")

if content.count('[') == content.count(']'):
    print(f"✅ Colchetes balanceados")
else:
    print(f"❌ Colchetes desbalanceados (diff: {content.count('[') - content.count(']')})")
