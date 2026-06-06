#!/usr/bin/env python3
"""
Refatoração contextual de linguagem prescritiva em direitos.json
Aplica regras de transformação preservando significado e estrutura JSON.

Usage:
    python3 scripts/refactor_direitos_json.py [--apply] [--dry-run]

Without --apply: dry-run (shows changes, doesn't write)
With --apply: actually writes changes
"""

import json
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIREITOS_PATH = PROJECT_ROOT / "data" / "direitos.json"

# Transformation rules: (regex pattern, replacement, description)
# Applied to text values inside descriptive fields
TRANSFORMATIONS = [
    # ========== PROCURE / PROCURAR ==========
    # "Procure o CRAS/CREAS/Conselho/etc" → "O X está disponível"
    (
        re.compile(r"\bProcure\s+o\s+(CRAS|CREAS|Conselho\s+Tutelar|Procon|Ministério\s+Público|MP\s+do\s+Trabalho|MPT|Sindicato)\b"),
        r"O \1 está disponível",
    ),
    # "Procure a Defensoria/Secretaria/Prefeitura"
    (
        re.compile(r"\bProcure\s+a\s+(Defensoria\s+Pública(?:\s+da\s+União)?|DPU|Secretaria(?:\s+de\s+[A-Za-zÀ-ÿ\s]+)?|Prefeitura|Polícia|Delegacia|operadora|agência\s+do\s+INSS|empresa)\b"),
        r"A \1 está disponível",
    ),
    # Lowercase em meio de frase: "...procure o CRAS"
    (
        re.compile(r"(\b(?:se\s+não\s+resolver|caso\s+contrário|para\s+isso|em\s+caso\s+de\s+[a-zà-ÿ\s]+|se\s+[a-zà-ÿ\s]+),?\s+)procure\s+", re.IGNORECASE),
        r"\1o atendimento é feito em ",
    ),
    # "Para X, procure Y" → "Para X, o canal é Y"
    (
        re.compile(r"(\bPara\s+[a-zà-ÿ\s]+:?,?\s+)procure\s+", re.IGNORECASE),
        r"\1o canal de acesso é ",
    ),
    # Catch-all: "procure" no início → "o canal é"
    (
        re.compile(r"(^|[\.\!\?]\s+)Procure\s+(o|a|os|as)\s+", re.MULTILINE),
        r"\1O(a) ",
    ),
    # Catch-all: "procure" lowercase em meio → "via"
    (
        re.compile(r"\s+procure\s+(o|a|os|as)\s+", re.IGNORECASE),
        r" via ",
    ),

    # ========== SOLICITE / SOLICITAR ==========
    (
        re.compile(r"\bSOLICITE\b"),
        r"Para solicitar",
    ),
    # "Solicite o X" → "O X pode ser solicitado"
    (
        re.compile(r"\bSolicite\s+(?:o\s+|a\s+)(BPC|auxílio[\s-]?inclusão|benefício|isenção|carteira|cartão|cadastro|registro|reembolso|exame|laudo)\b"),
        r"O(a) \1 pode ser solicitado(a)",
    ),
    # "Solicite no/na/pelo X" → "A solicitação é feita em X"
    (
        re.compile(r"\bSolicite\s+(no|na|em|pelo|pela|via)\s+"),
        r"A solicitação é feita \1 ",
    ),
    # "para solicitar" lowercase
    (
        re.compile(r"\bsolicite\s+(?:o\s+|a\s+)?", re.IGNORECASE),
        r"é necessário solicitar ",
    ),

    # ========== PEÇA / PEDIR ==========
    # "Peça a negativa POR ESCRITO" → "A negativa pode ser obtida por escrito"
    (
        re.compile(r"\bpeça\s+a\s+negativa\s+POR\s+ESCRITO", re.IGNORECASE),
        r"a negativa pode ser obtida por escrito",
    ),
    # Genérico: "Peça o X" → "Obter o X"
    (
        re.compile(r"\bPeça\s+(o|a|os|as)\s+"),
        r"Obter \1 ",
    ),
    (
        re.compile(r"\bpeça\s+(o|a|os|as)\s+", re.IGNORECASE),
        r"obter \1 ",
    ),

    # ========== FAÇA / FAZER ==========
    (
        re.compile(r"\bFaça\s+(o|a)\s+(cadastro|inscrição|requerimento|pedido|reclamação|denúncia)\b", re.IGNORECASE),
        r"O \2 é feito",
    ),
    (
        re.compile(r"\be\s+faça\s+(o|a)\s+", re.IGNORECASE),
        r" para realizar \1 ",
    ),

    # ========== AGENDE ==========
    (
        re.compile(r"\bAgende\s+(no|na|pelo|pela|via)\s+"),
        r"Agendamento disponível \1 ",
    ),
    (
        re.compile(r"\bagende\s+(no|na|pelo|pela)\s+", re.IGNORECASE),
        r"é possível agendar \1 ",
    ),

    # ========== VÁ / VAI ==========
    # "Vá ao/até X" → "X é o local de atendimento"
    (
        re.compile(r"\bV[áa]\s+(ao|até|para\s+o|para\s+a)\s+"),
        r"O local de atendimento é ",
    ),

    # ========== DIRIGIR-SE ==========
    (
        re.compile(r"\bDirigir-se\s+(a|ao|à)\s+"),
        r"Atendimento disponível em ",
    ),

    # ========== ENVIE ==========
    (
        re.compile(r"\bEnvie\s+(o|a|os|as)\s+(documento|formulário|laudo|requerimento)\b", re.IGNORECASE),
        r"O \2 é enviado",
    ),

    # ========== RECORRA ==========
    (
        re.compile(r"\brecorra\s+(administrativamente|judicialmente|via\s+\w+)\s+", re.IGNORECASE),
        r"é possível recorrer \1 ",
    ),

    # ========== DEVEM / DEVE ==========
    # "Empresas X devem Y" → "Empresas X são obrigadas a Y" (mais factual)
    (
        re.compile(r"\b(empresas|órgãos|escolas|planos|operadoras|cartórios)\s+devem\s+", re.IGNORECASE),
        r"\1 são obrigados por lei a ",
    ),
    # "DEVEM" em CAPS
    (
        re.compile(r"\bDEVEM\b"),
        r"SÃO OBRIGADOS POR LEI A",
    ),

    # ========== OBRIGATÓRIO / OBRIGATÓRIA ==========
    (
        re.compile(r"\b[Mm]atrícula\s+obrigatória\b"),
        r"Matrícula garantida por lei",
    ),
    (
        re.compile(r"\b[Cc]obertura\s+obrigatória\b"),
        r"Cobertura garantida por lei",
    ),
    # Genérico: "X é obrigatório" → "X é exigido por lei"
    (
        re.compile(r"\b(é|são)\s+obrigatóri[oa]s?\b"),
        r"\1 exigido(s) por lei",
    ),

    # ========== PRECISA DE ==========
    (
        re.compile(r"\bprecisa\s+de\s+", re.IGNORECASE),
        r"requer ",
    ),

    # ========== RECOMENDA-SE / RECOMENDAMOS ==========
    (
        re.compile(r"\b[Rr]ecomenda(?:-se)?\s+(?:que\s+)?", re.IGNORECASE),
        r"Uma opção é ",
    ),
    (
        re.compile(r"\b[Rr]ecomendamos\s+(?:que\s+)?", re.IGNORECASE),
        r"Uma opção é ",
    ),

    # ========== INDICA (não "não indica") ==========
    # Skip: "não indica" é disclaimer importante — manter
    # Para "indica" positivo: "indica X" → "menciona X"
    # (não aplicar regex global pois pode quebrar "não indica")
]


def apply_transformations(text: str, stats: dict) -> tuple[str, int]:
    """Apply all transformations to a text string. Returns (new_text, count)."""
    new_text = text
    count = 0
    for pattern, replacement in TRANSFORMATIONS:
        matches = pattern.findall(new_text)
        if matches:
            new_text = pattern.sub(replacement, new_text)
            count += len(matches)
            key = pattern.pattern[:50]
            stats[key] = stats.get(key, 0) + len(matches)
    return new_text, count


def transform_json_strings(obj, stats: dict, path: str = "") -> tuple:
    """Recursively transform all string values in a JSON object.
    
    Skips technical/structural fields (urls, ids, codes, schemas, etc).
    """
    total_changes = 0

    # Fields that should NEVER be transformed (technical/structural)
    SKIP_FIELDS = {
        "url",
        "urls",
        "id",
        "tipo",
        "categoria",
        "icone",
        "icon",
        "slug",
        "versao",
        "code",
        "cid",
        "schema",
        "@type",
        "@context",
        "ultima_atualizacao",
        "atualizado_em",
        "data",
        "lei",
        "lei_principal",
        "fonte_oficial",
        "fonte",
        "domain",
        "color",
        "valor",
        "telefone",
        "email",
        "endereco",
        "cnpj",
        "cpf",
        "rg",
    }

    if isinstance(obj, dict):
        new_obj = {}
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key

            # Skip technical fields
            if key.lower() in SKIP_FIELDS:
                new_obj[key] = value
                continue

            if isinstance(value, str):
                # Transform descriptive strings (skip URLs and short codes)
                if len(value) > 20 and not value.startswith(("http", "tel:", "mailto:", "/", "#")):
                    new_value, count = apply_transformations(value, stats)
                    if count > 0:
                        total_changes += count
                    new_obj[key] = new_value
                else:
                    new_obj[key] = value
            elif isinstance(value, (dict, list)):
                new_value, count = transform_json_strings(value, stats, current_path)
                total_changes += count
                new_obj[key] = new_value
            else:
                new_obj[key] = value
        return new_obj, total_changes

    elif isinstance(obj, list):
        new_list = []
        for idx, item in enumerate(obj):
            if isinstance(item, str):
                if len(item) > 20 and not item.startswith(("http", "tel:", "mailto:", "/", "#")):
                    new_item, count = apply_transformations(item, stats)
                    total_changes += count
                    new_list.append(new_item)
                else:
                    new_list.append(item)
            else:
                new_item, count = transform_json_strings(item, stats, f"{path}[{idx}]")
                total_changes += count
                new_list.append(new_item)
        return new_list, total_changes

    else:
        return obj, 0


def main():
    apply_changes = "--apply" in sys.argv
    print(f"\n🔧 REFATORAÇÃO DE LINGUAGEM PRESCRITIVA — direitos.json")
    print(f"   Modo: {'APLICAR' if apply_changes else 'DRY RUN'}\n")

    # Load JSON
    print(f"📖 Lendo {DIREITOS_PATH.name}...")
    with DIREITOS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Stats container
    stats = {}

    # Transform
    print("🔄 Aplicando transformações...\n")
    new_data, total_changes = transform_json_strings(data, stats)

    # Report
    print(f"📊 RELATÓRIO:")
    print(f"   Total de transformações: {total_changes}\n")

    if stats:
        print("   Por padrão:")
        for pattern, count in sorted(stats.items(), key=lambda x: -x[1]):
            print(f"     {count:3d}x  {pattern}")
        print()

    # Apply or skip
    if apply_changes:
        # Backup
        backup_path = DIREITOS_PATH.with_suffix(
            f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        shutil.copy(DIREITOS_PATH, backup_path)
        print(f"💾 Backup: {backup_path.name}")

        # Update version
        if "versao" in new_data:
            old_version = new_data["versao"]
            # Bump patch
            parts = old_version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            new_version = ".".join(parts)
            new_data["versao"] = new_version
            print(f"📦 Versão: {old_version} → {new_version}")

        # Write
        with DIREITOS_PATH.open("w", encoding="utf-8") as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"✅ Arquivo atualizado: {DIREITOS_PATH.name}\n")
    else:
        print("🔍 DRY RUN: Nenhum arquivo modificado.")
        print("   Execute com --apply para aplicar mudanças.\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
