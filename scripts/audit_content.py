#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit direitos.json for off-topic URLs and inappropriate content."""
import json
import re
from collections import Counter
from urllib.parse import urlparse


def main():
    """Run content audit on direitos.json."""
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    with open('data/direitos.json', encoding='utf-8') as f:
        data = json.load(f)

    text = json.dumps(data, ensure_ascii=False)
    urls = re.findall(r'https?://[^\s"<>\\]+', text)

    domains = Counter()
    for u in urls:
        d = urlparse(u).netloc.lower()
        domains[d] += 1

    print("=" * 70)
    print("DOMINIOS ENCONTRADOS NO direitos.json")
    print("=" * 70)

    gov_domains = {}
    non_gov_domains = {}
    for d, c in sorted(domains.items()):
        if any(x in d for x in ['.gov.br', '.gov.', 'planalto', 'datasus']):
            gov_domains[d] = c
        else:
            non_gov_domains[d] = c

    print(f"\nGOVERNAMENTAIS ({len(gov_domains)}):")
    for d, c in sorted(gov_domains.items()):
        print(f"  OK  {d} ({c}x)")

    print(f"\nNAO-GOVERNAMENTAIS ({len(non_gov_domains)}):")
    for d, c in sorted(non_gov_domains.items()):
        suspicious = any(x in d for x in [
            'google', 'whatsapp', 'facebook', 'twitter', 'instagram',
            'tiktok', 'youtube', 'amazon.com', 'aliexpress', 'shopee',
            'mercadolivre', 'bit.ly', 'tinyurl', 'goo.gl'
        ])
        flag = "ALERTA" if suspicious else "CHECK"
        print(f"  {flag}  {d} ({c}x)")

    # Inappropriate content check
    print("\n" + "=" * 70)
    print("VERIFICACAO DE CONTEUDO INAPROPRIADO")
    print("=" * 70)
    bad_words = [
        'homofob', 'racis', 'sexis', 'merda', 'porra', 'caralho',
        'foda', 'puta', 'viado', 'bicha', 'sapatao', 'traveco',
        'retardado', 'aleijado', 'mongoloide', 'demente'
    ]
    found_bad = False
    for w in bad_words:
        for m in re.finditer(w, text, re.IGNORECASE):
            found_bad = True
            start = max(0, m.start() - 40)
            end = min(len(text), m.end() + 40)
            ctx = text[start:end].replace('\n', ' ')
            print(f"  ALERTA '{w}' => ...{ctx}...")
    if not found_bad:
        print("  OK Nenhum conteudo inapropriado encontrado")

    # Categories
    print("\n" + "=" * 70)
    print(f"CATEGORIAS ATUAIS ({len(data['categorias'])})")
    print("=" * 70)
    for i, cat in enumerate(data['categorias'], 1):
        print(f"  {i:2}. {cat['id']:35s} {cat['titulo']}")

    # Check for missing important PcD rights
    print("\n" + "=" * 70)
    print("DIREITOS PcD CONHECIDOS vs CATEGORIAS NO SITE")
    print("=" * 70)
    known_rights = [
        ("BPC/LOAS", "bpc"),
        ("CIPTEA (Carteira TEA)", "ciptea"),
        ("Educacao Inclusiva", "educacao"),
        ("Plano de Saude", "plano_saude"),
        ("SUS Terapias/Medicamentos", "sus_terapias"),
        ("Passe Livre / Transporte", "transporte"),
        ("Cotas Trabalho", "trabalho"),
        ("Saque FGTS PcD", "fgts"),
        ("Moradia Acessivel", "moradia"),
        ("Isencoes Tributarias (IPI/ICMS/IPVA/IOF)", "isencoes_tributarias"),
        ("Atendimento Prioritario", "atendimento_prioritario"),
        ("Vaga Estacionamento Especial", "estacionamento_especial"),
        ("Aposentadoria Especial PcD", "aposentadoria_especial_pcd"),
        ("Prioridade Judicial", "prioridade_judicial"),
        ("Tecnologia Assistiva (SUS/INSS)", "tecnologia_assistiva"),
        ("Meia-Entrada Eventos", "meia_entrada"),
        ("ProUni/FIES/SISU (Educacao Superior)", "prouni_fies_sisu"),
        ("Isencao IR sobre Aposentadoria", "isencao_ir"),
        ("Bolsa Familia (acrescimo PcD)", "bolsa_familia"),
        ("Tarifa Social Energia", "tarifa_social_energia"),
        # Potentially missing
        ("Acompanhante Hospitalar", None),
        ("Tutela/Curatela/Tomada Decisao Apoiada", None),
        ("Credito Consignado (condicoes especiais)", None),
        ("Centro-Dia (SUAS)", None),
        ("Turismo Acessivel", None),
        ("Gratuidade Concursos Publicos (taxa isencao)", None),
        ("Acessibilidade Digital (sites/apps)", None),
        ("Reserva Vagas Concursos Publicos", None),
        ("Auxilio-Inclusao (trabalho formal + BPC)", None),
        ("Lingua Brasileira de Sinais (Libras)", None),
        ("Piso Salarial Cuidador (Lei 15131/2025)", None),
    ]

    cat_ids = {cat['id'] for cat in data['categorias']}
    present = []
    missing = []
    for name, cat_id in known_rights:
        if cat_id and cat_id in cat_ids:
            present.append(name)
        elif cat_id is None:
            # Check if content is mentioned anywhere
            search_terms = name.lower().split()
            found_in_text = any(t in text.lower() for t in search_terms if len(t) > 4)
            if found_in_text:
                missing.append(f"{name} (mencionado no conteudo, sem categoria propria)")
            else:
                missing.append(f"{name} (NAO encontrado)")
        else:
            missing.append(f"{name} (categoria '{cat_id}' ausente!)")

    print(f"\n  PRESENTES ({len(present)}):")
    for p in present:
        print(f"    OK  {p}")

    print(f"\n  POTENCIALMENTE FALTANDO ({len(missing)}):")
    for m in missing:
        print(f"    ??  {m}")


if __name__ == '__main__':
    main()
