#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX ACCESSIBILITY P2 — Link Redundante

Corrige links redundantes adicionando aria-hidden="true" em duplicatas.

PRIORIDADE: P2 (baixa - não obstrutório, mas melhora UX)
ESFORÇO: 15 minutos
META: AccessMonitor ≥9.2/10

PROBLEMA:
- 1 link redundante detectado pelo WAVE
- Links duplicados confundem usuários de leitores de tela

SOLUÇÃO:
- Identifica links duplicados (mesmo href)
- Adiciona aria-hidden="true" na segunda ocorrência
- Mantém primeiro link acessível
"""

import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def find_duplicate_links(html_content):
    """
    Encontra links duplicados no HTML.

    Returns:
        dict: {href: [posições]} - mapa de hrefs duplicados
    """
    # Regex para encontrar tags <a> com href
    link_pattern = re.compile(r'<a\s+([^>]*\s)?href="([^"]+)"([^>]*)>(.*?)</a>', re.IGNORECASE | re.DOTALL)

    links = defaultdict(list)
    for match in link_pattern.finditer(html_content):
        href = match.group(2)
        full_link = match.group(0)
        text = match.group(4)
        pos = match.start()

        # Ignora links com aria-hidden já aplicado
        if 'aria-hidden' not in full_link:
            links[href].append({
                'pos': pos,
                'full': full_link,
                'text': text.strip(),
                'match': match
            })

    # Retorna apenas hrefs duplicados
    duplicates = {href: occurrences for href, occurrences in links.items() if len(occurrences) > 1}
    return duplicates


def fix_duplicate_links(html_content):
    """
    Adiciona aria-hidden="true" em links duplicados (a partir do 2º).

    Returns:
        tuple: (html_modificado, contador_de_fixes)
    """
    duplicates = find_duplicate_links(html_content)

    if not duplicates:
        return html_content, 0

    fixes = 0
    modified_html = html_content
    offset = 0  # Track position shift due to modifications

    for href, occurrences in duplicates.items():
        # Skip first occurrence, fix the rest
        for occurrence in occurrences[1:]:
            old_link = occurrence['full']

            # Add aria-hidden="true" to the opening <a> tag
            # Find the position right after <a
            a_tag_end = old_link.find('>')
            if a_tag_end != -1:
                # Insert aria-hidden before the >
                new_link = old_link[:a_tag_end] + ' aria-hidden="true"' + old_link[a_tag_end:]

                # Replace in the content
                pos_in_modified = occurrence['pos'] + offset
                modified_html = (
                    modified_html[:pos_in_modified] +
                    new_link +
                    modified_html[pos_in_modified + len(old_link):]
                )

                # Update offset
                offset += len(new_link) - len(old_link)
                fixes += 1

    return modified_html, fixes


def create_backup(file_path):
    """Cria backup do arquivo com timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_suffix(f'.backup_{timestamp}{file_path.suffix}')
    backup_path.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')
    return backup_path


def main():
    """Executa correção de links redundantes no index.html"""
    print("=" * 80)
    print("🔧 FIX ACCESSIBILITY P2 — Link Redundante")
    print("=" * 80)
    print()

    # Paths
    root = Path(__file__).parent.parent
    index_path = root / "index.html"

    if not index_path.exists():
        print(f"❌ ERRO: {index_path} não encontrado")
        return 1

    # Read HTML
    print(f"📄 Lendo: {index_path.name}")
    html_content = index_path.read_text(encoding='utf-8')

    # Find duplicates
    duplicates = find_duplicate_links(html_content)

    if not duplicates:
        print("✅ Nenhum link duplicado encontrado!")
        print()
        print("=" * 80)
        print("✨ PROCESSO CONCLUÍDO — Nada a fazer")
        print("=" * 80)
        return 0

    print(f"\n⚠️ Encontrados {len(duplicates)} href(s) duplicado(s):")
    print()

    for href, occurrences in duplicates.items():
        print(f"   📎 {href}")
        print(f"      Ocorrências: {len(occurrences)}")
        for i, occ in enumerate(occurrences, 1):
            print(f"      {i}. Texto: \"{occ['text'][:50]}...\"")
        print()

    # Create backup
    print("💾 Criando backup...")
    backup_path = create_backup(index_path)
    print(f"   ✅ Backup: {backup_path.name}")
    print()

    # Apply fixes
    print("🔧 Aplicando correções...")
    modified_html, fixes_count = fix_duplicate_links(html_content)

    if fixes_count == 0:
        print("   ℹ️ Nenhuma correção necessária (links já possuem aria-hidden)")
        return 0

    # Write modified HTML
    index_path.write_text(modified_html, encoding='utf-8')
    print(f"   ✅ {fixes_count} link(s) corrigido(s)")
    print()

    # Summary
    print("=" * 80)
    print("📊 RESUMO DE CORREÇÕES")
    print("=" * 80)
    print()
    print(f"✅ Links duplicados corrigidos: {fixes_count}")
    print(f"📄 Arquivo modificado: {index_path.name}")
    print(f"💾 Backup criado: {backup_path.name}")
    print()
    print("🎯 PRÓXIMO PASSO:")
    print("   Valide online:")
    print("   - AccessMonitor: https://accessmonitor.acessibilidade.gov.pt/")
    print("   - WAVE: https://wave.webaim.org/")
    print()
    print("   Meta: AccessMonitor ≥9.2/10, WAVE 0 erros")
    print()
    print("=" * 80)
    print("✨ PROCESSO CONCLUÍDO COM SUCESSO")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
