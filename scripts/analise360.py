#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANÁLISE 360° - NOSSODIREITO
Comparação: Benefícios Implementados vs Pesquisados
"""

import json


def is_beneficio_completo(cat):
    """
    Verifica se um benefício está completo baseado em critérios de qualidade.

    Completo = ALL:
    - ≥5 requisitos
    - ≥4 documentos
    - ≥6 passos no passo_a_passo
    - ≥4 dicas
    - ≥2 links
    - base_legal não vazia
    - valor não vazio
    """
    try:
        requisitos_ok = len(cat.get('requisitos', [])) >= 5
        documentos_ok = len(cat.get('documentos', [])) >= 4
        passos_ok = len(cat.get('passo_a_passo', [])) >= 6
        dicas_ok = len(cat.get('dicas', [])) >= 4
        links_ok = len(cat.get('links', [])) >= 2
        base_legal_ok = len(cat.get('base_legal', [])) >= 1
        valor_ok = len(cat.get('valor', '').strip()) >= 10

        return all([requisitos_ok, documentos_ok, passos_ok, dicas_ok, links_ok, base_legal_ok, valor_ok])
    except:
        return False


def main():
    # Carregar dados
    with open('data/direitos.json', 'r', encoding='utf-8') as f:
        direitos = json.load(f)

    # IMPLEMENTADOS
    print("=" * 90)
    print("📊 ANÁLISE 360° - NOSSOD IREITO v1.4.3")
    print("=" * 90)
    print()

    implementados = direitos['categorias']

    # Análise dinâmica de completude
    completos = []
    parciais = []

    for cat in implementados:
        if is_beneficio_completo(cat):
            completos.append(cat)
        else:
            parciais.append(cat)

    print(f"✅ BENEFÍCIOS IMPLEMENTADOS: {len(implementados)}")
    print()
    for cat in implementados:
        status = "✅" if cat in completos else "⚠️"
        print(f"  {status} {cat['id']:32} — {cat['titulo'][:55]}")

    # Lista de prioridades para expansão futura
    print()
    print("=" * 90)
    print("📋 BENEFÍCIOS PESQUISADOS PARA EXPANSÃO FUTURA")
    print("=" * 90)
    print()

    faltam = [
        ("Táxis Acessíveis e Descontos", "MÉDIA", "Mobilidade urbana"),
        ("Locadoras de Veículos Adaptados", "BAIXA", "Nicho específico"),
        ("Acompanhante Gratuito Transporte Aéreo", "MÉDIA", "Mobilidade - direito essencial"),
        ("Desconto Internet/Telefonia", "MÉDIA", "Inclusão digital"),
        ("Atendimento Domiciliar (SAD)", "MÉDIA", "Saúde - casos graves"),
        ("Cestas Básicas e Alimentação", "MÉDIA", "Vulnerabilidade social"),
    ]

    for i, (beneficio, prioridade, razao) in enumerate(faltam, 1):
        icon = "🔥" if prioridade == "ALTA" else "⚠️" if prioridade == "MÉDIA" else "📌"
        print(f"{i:2}. {icon} {beneficio:42} | {prioridade:6} | {razao}")

    # ESTATÍSTICAS DINÂMICAS
    print()
    print("=" * 90)
    print("📈 ESTATÍSTICAS DE COBERTURA")
    print("=" * 90)
    print()

    total_implementados = len(implementados)
    total_completos = len(completos)
    total_parciais = len(parciais)
    total_pesquisados = total_implementados + len(faltam)  # Benefícios implementados + identificados para futuro

    cobertura_completa = (total_completos / total_pesquisados) * 100
    cobertura_total = (total_implementados / total_pesquisados) * 100

    print(f"✅ Implementados completos: {total_completos}/{total_pesquisados} ({cobertura_completa:.1f}%)")
    print(f"⚠️ Implementados parciais:  {total_parciais}/{total_pesquisados} ({total_parciais/total_pesquisados*100:.1f}%)")
    print(f"📋 Identificados p/ futuro:  {len(faltam)}/{total_pesquisados} ({len(faltam)/total_pesquisados*100:.1f}%)")
    print()
    print(f"🎯 COBERTURA TOTAL (implementados): {cobertura_total:.1f}%")
    print(f"✨ COMPLETUDE (benefícios completos): {cobertura_completa:.1f}%")

    # IPVA ESTADUAL
    print()
    print("=" * 90)
    print("🚗 IPVA ESTADUAL - data/ipva_pcd_estados.json")
    print("=" * 90)
    print()

    with open('data/ipva_pcd_estados.json', 'r', encoding='utf-8') as f:
        ipva = json.load(f)

    estados_count = len(ipva.get('estados', {}))
    last_update = ipva.get('metadata', {}).get('lastUpdate', 'N/A')

    print(f"📊 Arquivo: {estados_count} estados mapeados")
    print(f"📅 Última atualização: {last_update}")
    print()

    # RECOMENDAÇÕES BASEADAS EM GAPS
    print()
    print("=" * 90)
    print("🎯 RECOMENDAÇÕES - COMPLETAR BENEFÍCIOS PARCIAIS")
    print("=" * 90)
    print()

    if parciais:
        print(f"⚠️ {len(parciais)} BENEFÍCIO(S) PARCIAL(IS) IDENTIFICADO(S):")
        print()
        for cat in parciais:
            print(f"  📌 {cat['id']}")

            # Diagnóstico detalhado
            requisitos = len(cat.get('requisitos', []))
            documentos = len(cat.get('documentos', []))
            passos = len(cat.get('passo_a_passo', []))
            dicas = len(cat.get('dicas', []))
            links = len(cat.get('links', []))

            gaps = []
            if requisitos < 5: gaps.append(f"requisitos: {requisitos}/5")
            if documentos < 4: gaps.append(f"documentos: {documentos}/4")
            if passos < 6: gaps.append(f"passos: {passos}/6")
            if dicas < 4: gaps.append(f"dicas: {dicas}/4")
            if links < 2: gaps.append(f"links: {links}/2")

            print(f"     Gaps: {', '.join(gaps) if gaps else 'campos vazios/curtos'}")
            print()
    else:
        print("✅ TODOS OS BENEFÍCIOS ESTÃO COMPLETOS!")
        print()

    print("💡 PRÓXIMOS PASSOS PARA 100%:")
    print()
    print(f"  1. Completar {len(parciais)} benefício(s) parcial(is) → {total_completos + len(parciais)} completos")
    print(f"  2. Meta atual: {total_completos} completos | Meta 100%: ≥20 completos")

    if total_completos >= 20:
        print(f"  ✅ JÁ ATINGE META DE COMPLETUDE! ({total_completos}/20+)")
    else:
        faltam_completos = 20 - total_completos
        print(f"  ⚠️ Faltam {faltam_completos} benefícios completos para meta de 20")

    print()
    cobertura_meta = 75.0
    if cobertura_total >= cobertura_meta:
        print(f"  ✅ COBERTURA JÁ ATINGE META! ({cobertura_total:.1f}% ≥ {cobertura_meta}%)")
    else:
        gap_cobertura = cobertura_meta - cobertura_total
        print(f"  ⚠️ Gap de cobertura: {gap_cobertura:.1f}% (atual: {cobertura_total:.1f}% | meta: {cobertura_meta}%)")
        print(f"     Adicionar ~{int((gap_cobertura/100) * total_pesquisados) + 1} benefícios novos")


if __name__ == '__main__':
    main()
