#!/usr/bin/env python3
"""Update dicionario_pcd.json: add new categories to beneficios_elegiveis."""
import json
from datetime import date

with open('data/dicionario_pcd.json', encoding='utf-8') as f:
    d = json.load(f)

new_cats = [
    'acessibilidade_arquitetonica',
    'capacidade_legal',
    'crimes_contra_pcd',
    'acessibilidade_digital',
    'reabilitacao'
]

# Mapping: which disability types get which new categories
# All PcD get access to these rights
universal_cats = ['acessibilidade_arquitetonica', 'crimes_contra_pcd', 'capacidade_legal']
# Physical/sensory/motor get reabilitacao
reab_ids = [
    'tea', 'deficiencia_intelectual', 'deficiencia_visual', 'deficiencia_auditiva',
    'deficiencia_fisica_paralisia', 'deficiencia_fisica_amputacao', 'nanismo',
    'deficiencia_psicossocial', 'deficiencia_multipla', 'sindrome_down',
    'sindrome_zika', 'tdah'
]
# Digital accessibility: all sensory/cognitive
digital_ids = [
    'tea', 'deficiencia_intelectual', 'deficiencia_visual', 'deficiencia_auditiva',
    'deficiencia_fisica_paralisia', 'deficiencia_fisica_amputacao',
    'deficiencia_psicossocial', 'deficiencia_multipla', 'sindrome_down',
    'sindrome_zika', 'tdah'
]

updated = 0
for defic in d['deficiencias']:
    did = defic['id']
    current = set(defic.get('beneficios_elegiveis', []))
    added = set()

    # Universal categories for all
    for cat in universal_cats:
        if cat not in current:
            added.add(cat)

    # Reabilitacao
    if did in reab_ids and 'reabilitacao' not in current:
        added.add('reabilitacao')

    # Acessibilidade digital
    if did in digital_ids and 'acessibilidade_digital' not in current:
        added.add('acessibilidade_digital')

    if added:
        defic['beneficios_elegiveis'] = sorted(current | added)
        print(f'  {did}: +{len(added)} ({", ".join(sorted(added))})')
        updated += 1

# Update version
d['versao'] = '1.1.0'
d['atualizado_em'] = date.today().isoformat()

print(f'\nUpdated {updated} deficiencias')
print(f'Version: {d["versao"]}, Date: {d["atualizado_em"]}')

with open('data/dicionario_pcd.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=4)
print('Saved dicionario_pcd.json')
