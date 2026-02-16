#!/usr/bin/env python3
"""Full audit of direitos.json coverage."""
import json

d = json.load(open('data/direitos.json', encoding='utf-8'))
print(f"Versao: {d.get('versao')}")
print(f"Ultima atualizacao: {d.get('ultima_atualizacao')}")
print(f"Categorias: {len(d.get('categorias',[]))}")
print(f"Fontes: {len(d.get('fontes',[]))}")
print()

print("=== CATEGORIAS ===")
for c in d['categorias']:
    links = len(c.get('links',[]))
    insts = len(c.get('instituicoes',[]))
    tags = len(c.get('tags',[]))
    reqs = len(c.get('requisitos',[]))
    docs = len(c.get('documentos',[]))
    steps = len(c.get('passo_a_passo',[]))
    tips = len(c.get('dicas',[]))
    bl = c.get('base_legal','')[:60]
    print(f"  {c['id']:<35} links={links:<3} inst={insts:<3} tags={tags:<3} reqs={reqs} docs={docs} steps={steps} tips={tips}")
    print(f"    titulo: {c['titulo']}")
    print(f"    base_legal: {bl}")
    # Check states in instituicoes
    ufs = sorted(set(i.get('uf','') for i in c.get('instituicoes',[]) if i.get('uf')))
    if ufs:
        print(f"    UFs: {', '.join(ufs)} ({len(ufs)} estados)")
    print()

# Check all states
ALL_UFS = {'AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT','PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO'}
print("=== COBERTURA DE ESTADOS ===")
all_ufs_found = set()
for c in d['categorias']:
    for inst in c.get('instituicoes',[]):
        uf = inst.get('uf','')
        if uf:
            all_ufs_found.add(uf)
print(f"UFs encontrados: {sorted(all_ufs_found)} ({len(all_ufs_found)})")
missing = ALL_UFS - all_ufs_found
if missing:
    print(f"UFs FALTANDO: {sorted(missing)}")
else:
    print("Todos 27 UFs presentes!")

print()
print("=== FONTES (legislação) ===")
for f in d.get('fontes',[]):
    print(f"  {f['nome'][:90]}")
    print(f"    url: {f['url'][:80]}")

print()
print("=== URLs ÚNICAS ===")
all_urls = set()
for f in d.get('fontes',[]):
    all_urls.add(f['url'])
for c in d['categorias']:
    for link in c.get('links',[]):
        all_urls.add(link.get('url',''))
    for inst in c.get('instituicoes',[]):
        url = inst.get('url','')
        if url:
            all_urls.add(url)
print(f"Total URLs únicas: {len(all_urls)}")

print()
print("=== KEYWORD MAP ===")
km = d.get('keyword_map', {})
print(f"Total keywords: {len(km)}")

# Check CID codes in keywords
cid_codes = [k for k in km if k.upper().startswith(('F','G','H','Q','E','Z','S','M','N','I')) and len(k) <= 4 and any(c.isdigit() for c in k)]
print(f"CID codes in keywords: {len(cid_codes)}")
for code in sorted(cid_codes):
    cats = km[code].get('categorias', [])
    print(f"  {code}: -> {cats}")
