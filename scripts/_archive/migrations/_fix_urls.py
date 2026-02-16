#!/usr/bin/env python3
"""Fix confirmed broken URLs in direitos.json."""
import json

with open('data/direitos.json', encoding='utf-8') as f:
    raw = f.read()

fixes = {
    "https://sisen.receita.fazenda.gov.br/": "https://www.sisen.receita.fazenda.gov.br/",
    "https://www.turismoacessivel.gov.br/": "https://www.gov.br/turismo/pt-br",
    "https://aplicacoes.mds.gov.br/sagi/painel_bpc/": "https://aplicacoes.mds.gov.br/sagi/vis/data3/",
    "https://www.gov.br/anac/pt-br/assuntos/passageiros/pnae/documentacao-medica": "https://www.gov.br/anac/pt-br/assuntos/passageiros/acessibilidade",
    "https://www.gov.br/anac/pt-br/assuntos/passageiros/pnae": "https://www.gov.br/anac/pt-br/assuntos/passageiros/acessibilidade",
    "https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/isencoes/isencao-irpf-molestia-grave": "https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/declaracoes-e-demonstrativos/dirpf",
    "https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/declaracoes-e-demonstrativos/dirpf/perguntas-e-respostas-irpf-2024": "https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/perguntas-e-respostas",
    "https://www.gov.br/aneel/pt-br/assuntos/tarifas/tarifa-social-de-energia-eletrica": "https://www.gov.br/aneel/pt-br/assuntos/tarifas",
}

count = 0
for old, new in fixes.items():
    n = raw.count(old)
    if n > 0:
        raw = raw.replace(old, new)
        count += n
        print(f"  FIXED ({n}x): {old}")
        print(f"     -> {new}")
    else:
        print(f"  NOT FOUND: {old}")

with open('data/direitos.json', 'w', encoding='utf-8') as f:
    f.write(raw)

print(f"\nTotal replacements: {count}")
