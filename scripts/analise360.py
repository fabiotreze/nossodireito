#!/usr/bin/env python3
"""
ANÁLISE 360° - NOSSODIREITO
Comparação: Benefícios Implementados vs Pesquisados
"""

import json

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
    print(f"✅ BENEFÍCIOS IMPLEMENTADOS: {len(implementados)}")
    print()
    for cat in implementados:
        print(f"  ✅ {cat['id']:32} — {cat['titulo'][:55]}")
    
    # PESQUISADOS MAS NÃO IMPLEMENTADOS
    print()
    print("=" * 90)
    print("❌ BENEFÍCIOS PESQUISADOS MAS NÃO IMPLEMENTADOS (BENEFICIOS_COMPLETOS_PCD.md)")
    print("=" * 90)
    print()
    
    faltam = [
        ("Táxis Acessíveis e Descontos", "MÉDIA", "Mobilidade urbana"),
        ("Locadoras de Veículos Adaptados", "BAIXA", "Nicho específico"),
        ("Acompanhante Gratuito Transporte Aéreo", "MÉDIA", "Mobilidade - direito essencial"),
        ("Desconto Internet/Telefonia", "MÉDIA", "Inclusão digital"),
        ("Atendimento Domiciliar (SAD)", "MÉDIA", "Saúde - casos graves"),
        ("Defensoria Pública (expandir)", "ALTA", "Acesso à justiça"),
        ("Gratuidade de Justiça (expandir)", "ALTA", "Acesso à justiça"),
        ("Assentos Reservados Transportes (expandir)", "BAIXA", "Já parcialmente coberto"),
        ("Reserva Espaços Teatros/Cinemas (expandir)", "BAIXA", "Já parcialmente coberto"),
        ("Hotéis e Pousadas Acessíveis", "BAIXA", "Turismo"),
        ("ProUni, FIES, SISU - Cotas PcD", "ALTA", "Educação - grande demanda"),
        ("Isenção Imposto de Renda", "ALTA", "Financeiro - despesas médicas"),
        ("Bolsa Família para PcD", "ALTA", "Financeiro - vulnerabilidade"),
        ("Cestas Básicas e Alimentação", "MÉDIA", "Vulnerabilidade social"),
    ]
    
    for i, (beneficio, prioridade, razao) in enumerate(faltam, 1):
        icon = "🔥" if prioridade == "ALTA" else "⚠️" if prioridade == "MÉDIA" else "📌"
        print(f"{i:2}. {icon} {beneficio:42} | {prioridade:6} | {razao}")
    
    # ESTATÍSTICAS
    print()
    print("=" * 90)
    print("📈 ESTATÍSTICAS DE COBERTURA")
    print("=" * 90)
    print()
    
    total_pesquisados = 31
    implementados_completos = 17
    implementados_parciais = 4  # (defensoria, gratuidade justiça, assentos, reserva espaços)
    nao_implementados = 14
    
    cobertura_completa = (implementados_completos / total_pesquisados) * 100
    cobertura_parcial = ((implementados_completos + implementados_parciais) / total_pesquisados) * 100
    
    print(f"✅ Implementados completos: {implementados_completos}/{total_pesquisados} ({cobertura_completa:.1f}%)")
    print(f"⚠️ Implementados parciais:  {implementados_parciais}/{total_pesquisados} ({implementados_parciais/total_pesquisados*100:.1f}%)")
    print(f"❌ Não implementados:       {nao_implementados}/{total_pesquisados} ({nao_implementados/total_pesquisados*100:.1f}%)")
    print()
    print(f"🎯 COBERTURA TOTAL (completa + parcial): {cobertura_parcial:.1f}%")
    
    # IPVA ESTADUAL
    print()
    print("=" * 90)
    print("🚗 IPVA ESTADUAL - data/ipva_pcd_estados.json")
    print("=" * 90)
    print()
    
    with open('data/ipva_pcd_estados.json', 'r', encoding='utf-8') as f:
        ipva = json.load(f)
    
    print(f"📊 Arquivo: 21 KB, 346 linhas, 27 leis estaduais")
    print(f"📅 Data pesquisa: {ipva['_metadata']['data_pesquisa']}")
    print()
    print("❌ STATUS: NÃO INTEGRADO")
    print("   - NÃO usado em: js/app.js, sw.js, index.html")
    print("   - NÃO cacheado no Service Worker")
    print("   - Mencionado apenas no CHANGELOG.md (v1.0.4)")
    print()
    print("✅ BENEFÍCIO IPVA COBERTO EM: isencoes_tributarias")
    print("   - Informação genérica sobre isenção IPVA PcD federal")
    print("   - NÃO detalha leis estaduais específicas")
    print()
    print("🔧 OPÇÕES:")
    print("   1. INTEGRAR: Criar seção ipva_estados[] em isencoes_tributarias")
    print("      - Dropdown com estados permitindo busca por UF")
    print("      - Mostrar lei, link SEFAZ, requisitos por estado")
    print("      - Impacto: +15 horas desenvolvimento")
    print()
    print("   2. DELETAR: Se não há plano de usar dados estaduais")
    print("      - Economia: 21 KB, simplifica manutenção")
    
    # FUNCIONALIDADES APP.JS
    print()
    print("=" * 90)
    print("⚙️ FUNCIONALIDADES IMPLEMENTADAS (js/app.js)")
    print("=" * 90)
    print()
    
    funcionalidades = [
        ("✅", "Busca inteligente (matching_engine.json)", "886-1400"),
        ("✅", "Normalização e expansão de queries", "1179-1320"),
        ("✅", "Renderização de benefícios", "907-936"),
        ("✅", "Detalhes de benefício (documentos, requisitoslinks)", "937-1077"),
        ("✅", "Checklist de documentos (localStorage)", "1498-1650"),
        ("✅", "Acessibilidade (VLibras, TTS, contraste, fonte)", "109-585"),
        ("✅", "Service Worker (cache offline)", "sw.js"),
        ("✅", "PWA (manifest.json, install prompt)", "695-727"),
        ("✅", "PDF viewer (laudo médico preview)", "587-611"),
        ("✅", "Toast notifications", "612-621"),
        ("✅", "Navegação modal (documentos_mestre)", "775-849"),
        ("✅", "SEO (robots.txt, sitemap.xml)", "✓"),
        ("✅", "CSP Security Headers", "index.html L17"),
        ("⚠️", "IPVA Estadual - dropdown por UF", "NÃO IMPLEMENTADO"),
        ("⚠️", "Filtros por categoria (tag search)", "NÃO IMPLEMENTADO"),
        ("⚠️", "Compartilhamento social", "NÃO IMPLEMENTADO"),
        ("⚠️", "Print-friendly view", "NÃO IMPLEMENTADO"),
    ]
    
    for status, funcionalidade, linha in funcionalidades:
        print(f"  {status} {funcionalidade:55} (linha {linha})")
    
    # RECOMENDAÇÕES
    print()
    print("=" * 90)
    print("🎯 RECOMENDAÇÕES - ROADMAP v1.5.0")
    print("=" * 90)
    print()
    
    print("PRIORIDADE ALTA (4-6 semanas):")
    print("  1. 🔥 ProUni/FIES/SISU - Cotas PcD (educação superior)")
    print("  2. 🔥 Isenção Imposto de Renda (despesas médicas PcD)")
    print("  3. 🔥 Bolsa Família PcD (vulnerabilidade social)")
    print("  4. 🔥 Defensoria Pública (expandir seção)")
    print()
    print("PRIORIDADE MÉDIA (2-3 meses):")
    print("  5. ⚠️ Desconto Internet/Telefonia")
    print("  6. ⚠️ Acompanhante Gratuito Transporte Aéreo")
    print("  7. ⚠️ IPVA Estadual (integrar ipva_pcd_estados.json)")
    print("  8. ⚠️ Filtros por categoria/tag")
    print()
    print("PRIORIDADE BAIXA (backlog):")
    print("  9. 📌 Táxis Acessíveis, SAD, Hotéis, Cestas Básicas")
    print(" 10. 📌 Compartilhamento social, Print view")
    
    # DECISÃO IPVA
    print()
    print("=" * 90)
    print("🚨 DECISÃO IMEDIATA NECESSÁRIA")
    print("=" * 90)
    print()
    print("❓ IPVA_PCD_ESTADOS.JSON:")
    print()
    print("   OPÇÃO A: INTEGRAR (recomendado se desenvolvimento v1.5.0 planejado)")
    print("     - Adicionar seção 'Isenção IPVA por Estado' em isencoes_tributarias")
    print("     - Select dropdown com 27 estados")
    print("     - Mostrar: lei estadual, link SEFAZ, requisitos, valor veículo")
    print("     - Esforço: ~15 horas (backend: 2h, frontend: 8h, testes: 5h)")
    print()
    print("   OPÇÃO B: DELETAR (se sem planos curto prazo)")
    print("     - Remove 21 KB não utilizado")
    print("     - Simplifica manutenção")
    print("     - Pode pesquisar novamente se necessário futuro")
    print()
    print("   DECISÃO DO USUÁRIO: ?")

if __name__ == '__main__':
    main()
