#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX ACCESSIBILITY P0+P1 — Correção AUTOMATIZADA COMPLETA
Baseado em análise de 3 validadores: AccessMonitor, AccessibilityChecker, WAVE

PROBLEMAS CORRIGIDOS AUTOMATICAMENTE:
P0 (Críticos - 9 issues):
1. aria-hidden com elementos focáveis (2 elementos)
2. Contraste de cores insuficiente (AA)
3. Links não distinguíveis sem cor
4. Controles interativos aninhados
5. VLibras fora de landmarks
6. Form labels faltando

P1 (Altos - 2 issues):
7. Texto visível em nomes acessíveis
8. VLibras em landmark (já em P0)

Uso: python scripts/_archive/migrations/fix_accessibility_p0.py
(ARCHIVED — migrated from scripts/fix_accessibility_p0.py)
"""

import re
from datetime import datetime
from pathlib import Path


def fix_aria_hidden_focusable(content: str) -> tuple[str, int]:
    """Fix 1: aria-hidden com elementos focáveis"""
    fixes = 0

    # disclaimerModal: adicionar tabindex="-1" em TODOS os botões/links
    # Estratégia: adicionar tabindex="-1" em button dentro do modal

    # Padrão 1: button sem tabindex dentro de disclaimerModal
    old_content = content
    content = re.sub(
        r'(<button\s+id="acceptDisclaimer"[^>]*?)(\s*>)',
        r'\1 tabindex="-1"\2',
        content
    )
    if content != old_content:
        fixes += 1
        old_content = content

    # Padrão 2: fileInput - adicionar tabindex="-1" se não existir
    if 'id="fileInput"' in content and 'tabindex="-1"' not in content:
        content = re.sub(
            r'(<input[^>]*id="fileInput"[^>]*?)(aria-hidden="true">)',
            r'\1 tabindex="-1" \2',
            content
        )
        fixes += 1

    print(f"✅ Fix 1: aria-hidden focusable elements ({fixes} elementos corrigidos)")
    return content, fixes


def fix_color_contrast(content: str) -> tuple[str, int]:
    """Fix 2: Contraste de cores"""
    fixes = 0

    # .transparency-note h3: mudar cor para ter contraste ≥ 4.5:1
    old_content = content
    content = re.sub(
        r'(color:\s*)var\(--accent\)',
        r'\1#0056b3',
        content
    )
    if content != old_content:
        fixes = content.count('#0056b3') - old_content.count('#0056b3')

    # Adicionar regra específica se não existir
    if '.transparency-note h3' not in content:
        css_fragment = '''
/* Acessibilidade: Contraste AA ≥4.5:1 */
.transparency-note h3 {
    color: #0056b3;
}
'''
        # Adicionar antes do último }
        last_brace = content.rfind('}')
        if last_brace > 0:
            content = content[:last_brace+1] + css_fragment + content[last_brace+1:]
            fixes += 1

    print(f"✅ Fix 2: Color contrast (AA compliance) ({fixes} correções)")
    return content, fixes


def fix_link_distinction(content: str) -> tuple[str, int]:
    """Fix 3: Links distinguíveis sem depender de cor"""
    fixes = 0

    # Verificar se já existe a regra
    if 'text-underline-offset' not in content:
        css_addition = """
/* Acessibilidade: Links distinguíveis sem cor (WCAG 2.1 AA) */
p a, .section-desc a, .benefits-grid a,
.disclaimer-text a, article a, .info-box a {
    text-decoration: underline;
    text-underline-offset: 2px;
}

p a:hover, .section-desc a:hover, .benefits-grid a:hover,
.disclaimer-text a:hover, article a:hover, .info-box a:hover {
    text-decoration: none;
    font-weight: 600;
}
"""
        # Adicionar antes de </style>
        if '</style>' in content:
            content = content.replace('</style>', f'{css_addition}\n</style>', 1)
            fixes = 1

    print(f"✅ Fix 3: Links distinguishable without color ({fixes} regras adicionadas)")
    return content, fixes


def fix_nested_controls(content: str) -> tuple[str, int]:
    """Fix 4: Controles interativos aninhados"""
    fixes = 0

    # uploadZone: mover input para FORA do div
    # Encontrar o padrão completo
    pattern = r'(<div[^>]*id="uploadZone"[^>]*>)(.*?)(<input[^>]*id="fileInput"[^>]*>)(.*?)(</div>)'

    def fix_uploadzone(match):
        nonlocal fixes
        opening = match.group(1)
        before_input = match.group(2)
        input_tag = match.group(3)
        after_input = match.group(4)
        closing = match.group(5)

        # Adicionar onclick se não existir
        if 'onclick=' not in opening:
            opening = opening.replace(
                'aria-label="',
                'onclick="document.getElementById(\'fileInput\').click()" aria-label="'
            )

        # Retornar div sem input + input separado depois
        fixed = opening + before_input + after_input + closing + '\n' + input_tag
        fixes = 1
        return fixed

    content = re.sub(pattern, fix_uploadzone, content, flags=re.DOTALL)

    print(f"✅ Fix 4: Nested interactive controls ({fixes} corrigidos)")
    return content, fixes


def fix_vlibras_landmark(content: str) -> tuple[str, int]:
    """Fix 5: VLibras fora de landmarks"""
    fixes = 0

    # Verificar se VLibras já está em aside
    if '<aside aria-label="Widget' not in content and '<div vw class="enabled">' in content:
        # Envolver VLibras em <aside>
        vlibras_pattern = r'(\s*<div vw class="enabled">.*?</div>\s*)(<script src="https://vlibras\.gov\.br)'

        vlibras_replacement = r'''<aside aria-label="Widget de acessibilidade VLibras" role="complementary">
\1</aside>
\2'''

        old_content = content
        content = re.sub(vlibras_pattern, vlibras_replacement, content, flags=re.DOTALL)
        if content != old_content:
            fixes = 1

    print(f"✅ Fix 5: VLibras in landmark ({fixes} corrigidos)")
    return content, fixes


def fix_missing_form_labels(content: str) -> tuple[str, int]:
    """Fix 6: Labels faltando em formulários"""
    fixes = 0

    # fileInput: como tem aria-hidden="true", não precisa de label
    # Verificar outros inputs que precisam de label

    # Buscar inputs sem label associado (exceto fileInput)
    inputs_sem_label = re.findall(
        r'<input[^>]*id="([^"]+)"[^>]*>',
        content
    )

    for input_id in inputs_sem_label:
        if input_id != 'fileInput' and input_id != 'acceptDisclaimer':
            # Verificar se já tem label
            if f'for="{input_id}"' not in content:
                # Adicionar label antes do input
                pattern = f'(<input[^>]*id="{input_id}"[^>]*>)'

                # Determinar label pelo ID
                label_text = input_id.replace('Input', '').replace('_', ' ').capitalize()

                replacement = f'<label for="{input_id}" class="sr-only">{label_text}</label>\n                    \1'

                old_content = content
                content = re.sub(pattern, replacement, content)
                if content != old_content:
                    fixes += 1

    print(f"✅ Fix 6: Form labels ({fixes} labels adicionados)")
    return content, fixes


def fix_accessible_names_p1(content: str) -> tuple[str, int]:
    """Fix 7 (P1): Texto visível em nomes acessíveis"""
    fixes = 0

    # Buscar botões com aria-label que não contém o texto visível
    # Close button (×)
    if 'aria-label="Fechar' in content and '>×<' in content:
        old_content = content
        content = re.sub(
            r'aria-label="Fechar([^"]*)"([^>]*)>×<',
            r'aria-label="× Fechar\1"\2>×<',
            content
        )
        if content != old_content:
            fixes += 1

    # Outros botões com símbolos (A-, A, A+)
    patterns = [
        (r'aria-label="([^"]*tamanho[^"]*)"([^>]*)>A-<', r'aria-label="A- \1"\2>A-<'),
        (r'aria-label="([^"]*padrão[^"]*)"([^>]*)>A<', r'aria-label="A \1"\2>A<'),
        (r'aria-label="([^"]*tamanho[^"]*)"([^>]*)>A\+<', r'aria-label="A+ \1"\2>A+<'),
    ]

    for pattern, replacement in patterns:
        old_content = content
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        if content != old_content:
            fixes += 1

    print(f"✅ Fix 7 (P1): Accessible names ({fixes} elementos corrigidos)")
    return content, fixes


def main():
    index_path = Path('index.html')
    css_path = Path('css/styles.css')

    if not index_path.exists():
        print("❌ index.html não encontrado!")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 80)
    print("🔧 FIX ACCESSIBILITY P0+P1 — Correção AUTOMATIZADA COMPLETA")
    print("=" * 80)
    print(f"📅 Data/Hora: {timestamp}")
    print()

    # Backup
    backup_path = index_path.with_suffix('.html.backup')
    with open(index_path, 'r', encoding='utf-8') as f:
        original_content = f.read()

    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original_content)

    print(f"💾 Backup criado: {backup_path}")
    print()
    print("🔄 Aplicando correções...")
    print()

    # Aplicar fixes HTML
    content = original_content
    total_fixes = 0

    content, fixes = fix_aria_hidden_focusable(content)
    total_fixes += fixes

    content, fixes = fix_link_distinction(content)
    total_fixes += fixes

    content, fixes = fix_nested_controls(content)
    total_fixes += fixes

    content, fixes = fix_vlibras_landmark(content)
    total_fixes += fixes

    content, fixes = fix_missing_form_labels(content)
    total_fixes += fixes

    content, fixes = fix_accessible_names_p1(content)
    total_fixes += fixes

    # Salvar HTML
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print()
    print(f"✅ Arquivo HTML atualizado: {index_path}")
    print()

    # CSS fixes
    css_fixes = 0
    if css_path.exists():
        print("📝 Aplicando fixes no CSS...")
        print()

        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()

        css_backup_path = css_path.with_suffix('.css.backup')
        with open(css_backup_path, 'w', encoding='utf-8') as f:
            f.write(css_content)

        css_content, fixes = fix_color_contrast(css_content)
        css_fixes += fixes

        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css_content)

        print(f"✅ CSS atualizado: {css_path}")
        print()

    # Resumo final
    print()
    print("=" * 80)
    print("🎉 FIXES APLICADOS COM SUCESSO!")
    print("=" * 80)
    print()
    print(f"📊 RESUMO:")
    print(f"   ✅ P0 (Críticos): {total_fixes - fixes if fixes > 0 else total_fixes} correções HTML")
    print(f"   ✅ P1 (Altos): Incluído nas {total_fixes} correções")
    print(f"   ✅ CSS: {css_fixes} correções")
    print(f"   📈 TOTAL: {total_fixes + css_fixes} correções automatizadas")
    print()
    print("📋 PRÓXIMOS PASSOS:")
    print("   1. 🌐 Testar site no navegador (navegação teclado + visual)")
    print("   2. ✅ Validar com AccessMonitor: https://accessmonitor.acessibilidade.gov.pt/")
    print("   3. ✅ Validar com AccessibilityChecker: https://www.accessibilitychecker.org/")
    print("   4. ✅ Validar com WAVE: https://wave.webaim.org/")
    print("   5. 🔍 Executar: python scripts/validate_all.py")
    print()
    print("🎯 META ESPERADA:")
    print("   • AccessMonitor: 8.7 → ≥9.0/10")
    print("   • AccessibilityChecker: <90 → ≥95")
    print("   • WAVE: Manter 10/10 AIM Score")
    print()


if __name__ == '__main__':
    main()
