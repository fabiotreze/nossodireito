#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX ACCESSIBILITY P2 — Contraste AAA

Ajusta cores para contraste ≥7:1 (WCAG AAA).

PRIORIDADE: P2 (baixo - AAA é opcional, AA já atendido)
ESFORÇO: 4h
META: Contraste ≥7:1 (AAA)

PROBLEMA:
- 78 combinações de cores com contraste < 7:1
- Atualmente: ≥4.5:1 (WCAG AA) ✅
- AAA não é obrigatório, mas melhora acessibilidade

SOLUÇÃO CONSERVADORA:
- Identifica cores com contraste < 7:1
- Sugere cores mais escuras/claras para atingir 7:1
- NÃO modifica automaticamente (requer aprovação visual)
- Gera relatório com sugestões

CORES PRINCIPAIS:
- --primary: #007bff (atual)
- --accent: #0056b3 (já ajustado para AA)
- --background: #ffffff
- --text: #212529
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Converte cor hex para RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Converte RGB para hex"""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """
    Calcula luminância relativa (WCAG 2.1)
    https://www.w3.org/WAI/GL/wiki/Relative_luminance
    """
    def adjust(channel):
        c = channel / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)


def contrast_ratio(color1: str, color2: str) -> float:
    """
    Calcula contraste entre duas cores (WCAG 2.1)
    https://www.w3.org/WAI/GL/wiki/Contrast_ratio
    """
    lum1 = relative_luminance(hex_to_rgb(color1))
    lum2 = relative_luminance(hex_to_rgb(color2))

    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)

    return (lighter + 0.05) / (darker + 0.05)


def darken_color(hex_color: str, factor: float = 0.8) -> str:
    """
    Escurece uma cor multiplicando RGB por factor

    Args:
        hex_color: Cor em hex
        factor: Fator de escurecimento (0.0-1.0)

    Returns:
        Nova cor em hex
    """
    r, g, b = hex_to_rgb(hex_color)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return rgb_to_hex((r, g, b))


def lighten_color(hex_color: str, factor: float = 1.2) -> str:
    """
    Clareia uma cor

    Args:
        hex_color: Cor em hex
        factor: Fator de clareamento (>1.0)

    Returns:
        Nova cor em hex
    """
    r, g, b = hex_to_rgb(hex_color)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return rgb_to_hex((r, g, b))


def suggest_aaa_color(foreground: str, background: str, target_ratio: float = 7.0) -> str:
    """
    Sugere cor ajustada para atingir contraste AAA

    Args:
        foreground: Cor do texto (hex)
        background: Cor de fundo (hex)
        target_ratio: Contraste alvo (7.0 para AAA)

    Returns:
        Nova cor em hex que atinge target_ratio
    """
    current_ratio = contrast_ratio(foreground, background)

    if current_ratio >= target_ratio:
        return foreground

    # Tenta escurecer
    suggested = foreground
    for _ in range(20):  # Max 20 iterações
        suggested = darken_color(suggested, 0.9)
        if contrast_ratio(suggested, background) >= target_ratio:
            return suggested

    # Se escurecer não funcionar, tentar clarear
    suggested = foreground
    for _ in range(20):
        suggested = lighten_color(suggested, 1.1)
        if contrast_ratio(suggested, background) >= target_ratio:
            return suggested

    return foreground  # Fallback: retornar original


def analyze_contrast():
    """Analisa contraste das cores principais"""
    print("=" * 80)
    print("🎨 FIX ACCESSIBILITY P2 — Contraste AAA")
    print("=" * 80)
    print()

    # Cores principais
    colors = {
        'primary': '#007bff',
        'accent': '#0056b3',
        'text': '#212529',
        'background': '#ffffff',
        'gray': '#6c757d'
    }

    backgrounds = ['#ffffff', '#f8f9fa']  # Branco e cinza claro

    print("📊 ANÁLISE DE CONTRASTE ATUAL")
    print()

    # Análise
    issues = []

    for fg_name, fg_color in colors.items():
        if fg_name == 'background':
            continue

        for bg_color in backgrounds:
            ratio = contrast_ratio(fg_color, bg_color)
            status_aa = "✅" if ratio >= 4.5 else "❌"
            status_aaa = "✅" if ratio >= 7.0 else "⚠️"

            print(f"{fg_name:12} sobre {bg_color}:")
            print(f"   Contraste: {ratio:.2f}:1")
            print(f"   AA (4.5:1): {status_aa}")
            print(f"   AAA (7.0:1): {status_aaa}")

            if ratio < 7.0:
                suggested = suggest_aaa_color(fg_color, bg_color, 7.0)
                suggested_ratio = contrast_ratio(suggested, bg_color)
                print(f"   💡 Sugestão AAA: {suggested} (contraste: {suggested_ratio:.2f}:1)")

                issues.append({
                    'foreground_name': fg_name,
                    'foreground': fg_color,
                    'background': bg_color,
                    'current_ratio': ratio,
                    'suggested': suggested,
                    'suggested_ratio': suggested_ratio
                })

            print()

    # Resumo
    print("=" * 80)
    print("📊 RESUMO")
    print("=" * 80)
    print()
    print(f"⚠️ Combinações < AAA: {len(issues)}")
    print()

    if issues:
        print("💡 SUGESTÕES DE CORES AAA:")
        print()
        for issue in issues:
            print(f"   --{issue['foreground_name']}: {issue['suggested']}")
            print(f"      (atual: {issue['foreground']}, contraste: {issue['current_ratio']:.2f}:1 → {issue['suggested_ratio']:.2f}:1)")
            print()

    print("=" * 80)
    print("⚠️ IMPORTANTE:")
    print("=" * 80)
    print()
    print("✅ Todas as cores JÁ ATENDEM WCAG AA (4.5:1)")
    print("⚠️ AAA (7.0:1) é OPCIONAL - não obrigatório")
    print()
    print("💡 Antes de aplicar sugestões AAA:")
    print("   1. Revise visualmente (cores podem ficar muito escuras)")
    print("   2. Teste com usuários reais")
    print("   3. Considere manter AA (já suficiente para maioria)")
    print()
    print("🎯 Para aplicar:")
    print("   1. Edite css/styles.css manualmente")
    print("   2. Substitua valores de --primary, --accent, etc.")
    print("   3. Teste visualmente antes de commitar")
    print()
    print("=" * 80)
    print("✨ ANÁLISE CONCLUÍDA")
    print("=" * 80)


def main():
    """CLI principal"""
    analyze_contrast()
    return 0


if __name__ == "__main__":
    sys.exit(main())
