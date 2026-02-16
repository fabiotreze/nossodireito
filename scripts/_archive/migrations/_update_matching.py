#!/usr/bin/env python3
"""Add keywords for 4 new categories to matching_engine.json."""
import json

with open('data/matching_engine.json', encoding='utf-8') as f:
    m = json.load(f)

kw = m['keyword_map']
cid = m['cid_range_map']
terms = m['uppercase_only_terms']

new_kw = {
    # acessibilidade_arquitetonica
    'acessibilidade arquitetonica': {'cats': ['acessibilidade_arquitetonica', 'moradia'], 'weight': 10},
    'barreira arquitetonica': {'cats': ['acessibilidade_arquitetonica', 'moradia'], 'weight': 9},
    'NBR 9050': {'cats': ['acessibilidade_arquitetonica', 'moradia'], 'weight': 10},
    'piso tatil': {'cats': ['acessibilidade_arquitetonica'], 'weight': 9},
    'calcada acessivel': {'cats': ['acessibilidade_arquitetonica'], 'weight': 8},
    'edificacao acessivel': {'cats': ['acessibilidade_arquitetonica', 'moradia'], 'weight': 9},
    'lei 10.098': {'cats': ['acessibilidade_arquitetonica', 'moradia'], 'weight': 10},
    'decreto 5.296': {'cats': ['acessibilidade_arquitetonica', 'moradia'], 'weight': 10},
    'banheiro acessivel': {'cats': ['acessibilidade_arquitetonica', 'moradia'], 'weight': 9},
    'espaco publico acessivel': {'cats': ['acessibilidade_arquitetonica'], 'weight': 8},
    'obra acessivel': {'cats': ['acessibilidade_arquitetonica'], 'weight': 7},
    'reforma acessibilidade': {'cats': ['acessibilidade_arquitetonica'], 'weight': 8},
    # capacidade_legal
    'curatela': {'cats': ['capacidade_legal'], 'weight': 10},
    'interdicao': {'cats': ['capacidade_legal'], 'weight': 10},
    'tomada de decisao apoiada': {'cats': ['capacidade_legal'], 'weight': 10},
    'TDA curatela': {'cats': ['capacidade_legal'], 'weight': 10},
    'capacidade civil': {'cats': ['capacidade_legal'], 'weight': 10},
    'capacidade legal': {'cats': ['capacidade_legal'], 'weight': 10},
    'incapacidade civil': {'cats': ['capacidade_legal'], 'weight': 9},
    'curador': {'cats': ['capacidade_legal'], 'weight': 9},
    'apoiador': {'cats': ['capacidade_legal'], 'weight': 7},
    'Art. 84 LBI': {'cats': ['capacidade_legal'], 'weight': 10},
    'Art. 85 LBI': {'cats': ['capacidade_legal'], 'weight': 10},
    'esterilizacao forcada': {'cats': ['capacidade_legal', 'crimes_contra_pcd'], 'weight': 10},
    # crimes_contra_pcd
    'crime PcD': {'cats': ['crimes_contra_pcd'], 'weight': 10},
    'crime deficiencia': {'cats': ['crimes_contra_pcd'], 'weight': 10},
    'discriminacao PcD': {'cats': ['crimes_contra_pcd', 'atendimento_prioritario'], 'weight': 10},
    'violencia PcD': {'cats': ['crimes_contra_pcd'], 'weight': 10},
    'abandono PcD': {'cats': ['crimes_contra_pcd'], 'weight': 10},
    'maus tratos PcD': {'cats': ['crimes_contra_pcd'], 'weight': 10},
    'maus-tratos PcD': {'cats': ['crimes_contra_pcd'], 'weight': 10},
    'Art. 88 LBI': {'cats': ['crimes_contra_pcd'], 'weight': 10},
    'Art. 89 LBI': {'cats': ['crimes_contra_pcd'], 'weight': 10},
    'Art. 90 LBI': {'cats': ['crimes_contra_pcd'], 'weight': 10},
    'Art. 91 LBI': {'cats': ['crimes_contra_pcd'], 'weight': 10},
    'lei 7.853': {'cats': ['crimes_contra_pcd'], 'weight': 10},
    'boletim de ocorrencia PcD': {'cats': ['crimes_contra_pcd'], 'weight': 9},
    'retencao documentos PcD': {'cats': ['crimes_contra_pcd'], 'weight': 9},
    'apropriacao beneficio PcD': {'cats': ['crimes_contra_pcd'], 'weight': 9},
    'delegacia PcD': {'cats': ['crimes_contra_pcd'], 'weight': 8},
    'recusar matricula PcD': {'cats': ['crimes_contra_pcd', 'educacao'], 'weight': 10},
    # acessibilidade_digital
    'acessibilidade digital': {'cats': ['acessibilidade_digital'], 'weight': 10},
    'eMAG': {'cats': ['acessibilidade_digital'], 'weight': 10},
    'WCAG': {'cats': ['acessibilidade_digital'], 'weight': 10},
    'Libras': {'cats': ['acessibilidade_digital'], 'weight': 9},
    'interprete Libras': {'cats': ['acessibilidade_digital'], 'weight': 10},
    'audiodescricao': {'cats': ['acessibilidade_digital', 'meia_entrada'], 'weight': 9},
    'closed caption': {'cats': ['acessibilidade_digital'], 'weight': 9},
    'legenda oculta': {'cats': ['acessibilidade_digital'], 'weight': 9},
    'lei 10.436': {'cats': ['acessibilidade_digital'], 'weight': 10},
    'decreto 5.626': {'cats': ['acessibilidade_digital'], 'weight': 10},
    'site acessivel': {'cats': ['acessibilidade_digital'], 'weight': 9},
    'app acessivel': {'cats': ['acessibilidade_digital'], 'weight': 8},
    'leitor de tela': {'cats': ['acessibilidade_digital', 'tecnologia_assistiva'], 'weight': 9},
    'ANATEL PcD': {'cats': ['acessibilidade_digital'], 'weight': 8},
    'plano telefonico PcD': {'cats': ['acessibilidade_digital'], 'weight': 8},
    'Central de Libras': {'cats': ['acessibilidade_digital'], 'weight': 9},
    'comunicacao acessivel': {'cats': ['acessibilidade_digital'], 'weight': 8},
    # reabilitacao (expand existing)
    'habilitacao': {'cats': ['reabilitacao', 'sus_terapias'], 'weight': 8},
    'centro especializado reabilitacao': {'cats': ['reabilitacao', 'sus_terapias'], 'weight': 10},
    'CER reabilitacao': {'cats': ['reabilitacao', 'sus_terapias'], 'weight': 10},
    'protese SUS': {'cats': ['reabilitacao', 'sus_terapias'], 'weight': 10},
    'ortese SUS': {'cats': ['reabilitacao', 'sus_terapias'], 'weight': 10},
    'cadeira de rodas SUS': {'cats': ['reabilitacao', 'sus_terapias'], 'weight': 10},
    'aparelho auditivo SUS': {'cats': ['reabilitacao', 'sus_terapias'], 'weight': 10},
    'estimulacao precoce': {'cats': ['reabilitacao', 'sus_terapias'], 'weight': 9},
    'intervencao precoce': {'cats': ['reabilitacao', 'sus_terapias'], 'weight': 9},
    'reabilitacao profissional INSS': {'cats': ['reabilitacao', 'aposentadoria_especial_pcd'], 'weight': 10},
    'CNES reabilitacao': {'cats': ['reabilitacao'], 'weight': 8},
    'decreto 3.298': {'cats': ['reabilitacao', 'acessibilidade_arquitetonica'], 'weight': 9},
}

added = 0
for k, v in new_kw.items():
    if k not in kw:
        kw[k] = v
        added += 1
    else:
        existing_cats = set(kw[k].get('cats', []))
        new_cats = set(v.get('cats', []))
        merged = existing_cats | new_cats
        if merged != existing_cats:
            kw[k]['cats'] = sorted(merged)
            print(f'  MERGED: {k} -> {kw[k]["cats"]}')
            added += 1

print(f'Added/merged {added} keywords. Total: {len(kw)}')

# Add new uppercase terms
new_terms = ['TDA', 'WCAG', 'ANATEL', 'NBR']
for t in new_terms:
    if t not in terms:
        terms.append(t)
        print(f'  Added uppercase term: {t}')

# Update CID ranges
if 'reabilitacao' not in cid.get('G', []):
    cid['G'].append('reabilitacao')
    print('  Added reabilitacao to CID G range')
if 'K' not in cid:
    cid['K'] = ['bpc', 'sus_terapias', 'reabilitacao']
    print('  Added CID K range')

with open('data/matching_engine.json', 'w', encoding='utf-8') as f:
    json.dump(m, f, ensure_ascii=False, indent=4)
print('Saved matching_engine.json')
