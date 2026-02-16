#!/usr/bin/env python3
"""Comprehensive data integrity validation for nossodireito."""
import json
import sys
import os

os.chdir(os.path.join(os.path.dirname(__file__), '..'))

errors = []
warnings = []

# 1. Load all data files
try:
    with open('data/direitos.json', encoding='utf-8') as f:
        direitos = json.load(f)
    print('OK: direitos.json loaded')
except Exception as e:
    errors.append(f'FAIL: direitos.json: {e}')
    direitos = {}

try:
    with open('data/dicionario_pcd.json', encoding='utf-8') as f:
        dicio = json.load(f)
    print('OK: dicionario_pcd.json loaded')
except Exception as e:
    errors.append(f'FAIL: dicionario_pcd.json: {e}')
    dicio = {}

try:
    with open('data/ipva_pcd_estados.json', encoding='utf-8') as f:
        ipva = json.load(f)
    print('OK: ipva_pcd_estados.json loaded')
except Exception as e:
    errors.append(f'FAIL: ipva_pcd_estados.json: {e}')
    ipva = {}

try:
    with open('data/matching_engine.json', encoding='utf-8') as f:
        matching = json.load(f)
    print('OK: matching_engine.json loaded')
except Exception as e:
    errors.append(f'FAIL: matching_engine.json: {e}')
    matching = {}

# 2. Validate direitos.json structure
cats = direitos.get('categorias', [])
fontes = direitos.get('fontes', [])
classif = direitos.get('classificacao_deficiencia', [])
print(f'\nDireitos: {len(cats)} categorias, {len(fontes)} fontes, {len(classif)} classificações')

# Check required fields per category
required_cat = ['id','titulo','resumo','icone','base_legal','requisitos','documentos','passo_a_passo','dicas','valor','onde','links','tags']
for c in cats:
    cid = c.get('id','UNKNOWN')
    for field in required_cat:
        if field not in c:
            errors.append(f'Cat {cid}: missing field "{field}"')
        elif isinstance(c[field], list) and len(c[field]) == 0:
            warnings.append(f'Cat {cid}: empty list "{field}"')
    # Check base_legal structure
    for bl in c.get('base_legal', []):
        if not isinstance(bl, dict):
            errors.append(f'Cat {cid}: base_legal item is not dict')
        else:
            for bf in ['lei','artigo','link']:
                if bf not in bl:
                    errors.append(f'Cat {cid}: base_legal missing "{bf}"')
    # Check links structure
    for lnk in c.get('links', []):
        if not isinstance(lnk, dict):
            errors.append(f'Cat {cid}: link item is not dict')
        else:
            if 'titulo' not in lnk:
                errors.append(f'Cat {cid}: link missing titulo')
            if 'url' not in lnk:
                errors.append(f'Cat {cid}: link missing url')
            elif not lnk['url'].startswith('http'):
                errors.append(f'Cat {cid}: link url invalid: {lnk["url"]}')

# 3. Check for duplicate category IDs
cat_ids = [c['id'] for c in cats if 'id' in c]
dupes = [x for x in cat_ids if cat_ids.count(x) > 1]
if dupes:
    errors.append(f'Duplicate category IDs: {set(dupes)}')
else:
    print('OK: No duplicate category IDs')

# 4. Validate all URLs are https
all_urls = []
for c in cats:
    for bl in c.get('base_legal', []):
        if 'link' in bl:
            all_urls.append((c['id'], 'base_legal', bl['link']))
    for lnk in c.get('links', []):
        if 'url' in lnk:
            all_urls.append((c['id'], 'link', lnk['url']))
for f in fontes:
    if 'url' in f:
        all_urls.append(('fonte:'+f.get('nome','?'), 'fonte', f['url']))

http_only = [(cid, typ, url) for cid, typ, url in all_urls if url.startswith('http://')]
if http_only:
    for cid, typ, url in http_only:
        errors.append(f'HTTP (not HTTPS) URL in {cid}/{typ}: {url}')
else:
    print(f'OK: All {len(all_urls)} URLs use HTTPS')

# 5. Check fontes structure
for f in fontes:
    if 'nome' not in f:
        errors.append('Fonte missing nome')
    if 'url' not in f:
        errors.append(f'Fonte missing url: {f.get("nome","?")}')

# 6. Check duplicate fonte URLs
fonte_urls = [f['url'] for f in fontes if 'url' in f]
dupe_fonte_urls = [u for u in fonte_urls if fonte_urls.count(u) > 1]
if dupe_fonte_urls:
    warnings.append(f'Duplicate fonte URLs: {set(dupe_fonte_urls)}')
else:
    print('OK: No duplicate fonte URLs')

# 7. IPVA validation - all 27 states
BRAZIL_STATES = ['AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT','PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO']
ipva_states = list(ipva.get('estados', {}).keys())
missing_states = [s for s in BRAZIL_STATES if s not in ipva_states]
extra_states = [s for s in ipva_states if s not in BRAZIL_STATES]
if missing_states:
    errors.append(f'IPVA missing states: {missing_states}')
else:
    print(f'OK: IPVA covers all {len(BRAZIL_STATES)} states')
if extra_states:
    warnings.append(f'IPVA extra states: {extra_states}')

# 8. Dicionario validation
defics = dicio.get('deficiencias', [])
print(f'Dicionário: {len(defics)} deficiências')
for d_item in defics:
    did = d_item.get('id', 'UNKNOWN')
    for field in ['id','nome','cid10','descricao','keywords_busca']:
        if field not in d_item:
            warnings.append(f'Dicionario {did}: missing "{field}"')

# 9. Matching engine validation
kw_map = matching.get('KEYWORD_MAP', {})
cid_map = matching.get('CID_RANGE_MAP', {})
print(f'Matching: {len(kw_map)} keywords, {len(cid_map)} CID ranges')

# Check that matching keywords reference valid category IDs
for kw, targets in kw_map.items():
    if isinstance(targets, list):
        for t in targets:
            if isinstance(t, dict) and 'category' in t:
                if t['category'] not in cat_ids:
                    warnings.append(f'Matching keyword "{kw}" references unknown category "{t["category"]}"')
            elif isinstance(t, str):
                if t not in cat_ids:
                    warnings.append(f'Matching keyword "{kw}" references unknown category "{t}"')

# 10. Schema validation
try:
    import jsonschema
    with open('schemas/direitos.schema.json', encoding='utf-8') as f:
        schema = json.load(f)
    jsonschema.validate(direitos, schema)
    print('OK: direitos.json validates against schema')
except jsonschema.ValidationError as e:
    errors.append(f'Schema validation failed: {e.message[:200]}')
except ImportError:
    warnings.append('jsonschema not installed - skipping schema validation')
except Exception as e:
    errors.append(f'Schema error: {e}')

# 11. classificacao_deficiencia validation
for cl in classif:
    if 'tipo' not in cl:
        errors.append('Classificação missing tipo')
    if 'cid10' not in cl:
        errors.append(f'Classificação {cl.get("tipo","?")} missing cid10')

# Print results
print(f'\n=== RESULTS ===')
print(f'Errors: {len(errors)}')
for e in errors:
    print(f'  ERROR: {e}')
print(f'Warnings: {len(warnings)}')
for w in warnings:
    print(f'  WARN: {w}')
print(f'\nTotal: {len(errors)} errors, {len(warnings)} warnings')
