#!/usr/bin/env python3
"""
NossoDireito — Validador de Política de URLs (whitelist de domínios)
=================================================================
Valida que TODOS os links em direitos.json pertencem a domínios
oficiais do governo brasileiro (.gov.br, .leg.br, .jus.br, .def.br,
.mp.br, .mil.br) ou organismos internacionais confiáveis.

Gate de **política** — falha se alguém adiciona link não-oficial.
Complementar a scripts/validate_sources.py (drift / acessibilidade HTTP).

Também pode verificar acessibilidade HTTP (status 200) com --check-live.

Uso:
    python scripts/validate_url_policy.py                 # Validação de domínios
    python scripts/validate_url_policy.py --check-live    # + verifica HTTP status
    python scripts/validate_url_policy.py --dict          # Valida dicionário também
    python scripts/validate_url_policy.py --verbose       # Lista todas as URLs

Retorna exit code 0 se tudo OK, 1 se há URLs não-governamentais.
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "direitos.json"
DICT_FILE = ROOT / "data" / "dicionario_pcd.json"

# Domínios oficiais aceitos
DOMINIOS_OFICIAIS = (
    ".gov.br",
    ".leg.br",
    ".jus.br",
    ".mp.br",
    ".def.br",
    ".mil.br",
)

# Domínios internacionais confiáveis (organismos oficiais)
DOMINIOS_INTERNACIONAIS = (
    "icd.who.int",  # OMS — Classificação Internacional de Doenças
)

# Esquemas aceitos (além de https://)
ESQUEMAS_ACEITOS = ("https", "http")

USER_AGENT = "NossoDireito-URLValidator/1.0 (+https://nossodireito.fabiotreze.com)"


def is_official_url(url: str) -> bool:
    """Verifica se URL pertence a domínio oficial do governo brasileiro ou organismo internacional confiável."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ESQUEMAS_ACEITOS:
            return False
        domain = (parsed.hostname or "").lower()
        if any(domain.endswith(d) for d in DOMINIOS_OFICIAIS):
            return True
        if any(domain == d or domain.endswith("." + d) for d in DOMINIOS_INTERNACIONAIS):
            return True
        return False
    except Exception:
        return False


def extract_all_urls(data: dict) -> list[dict]:
    """Extrai todas as URLs de direitos.json com contexto."""
    urls = []

    def _add(url, context, path):
        if url and isinstance(url, str) and url.startswith("http"):
            urls.append({"url": url, "context": context, "path": path})

    # Fontes
    for i, fonte in enumerate(data.get("fontes", [])):
        _add(fonte.get("url"), f"fonte: {fonte.get('nome', '?')}", f"fontes[{i}].url")
        for sub in fonte.get("servicos", []):
            if isinstance(sub, dict):
                _add(sub.get("url"), f"fonte.serviço: {sub.get('nome', '?')}", f"fontes[{i}].servicos")

    # Categorias
    for i, cat in enumerate(data.get("categorias", [])):
        cat_id = cat.get("id", "?")
        # Links
        for j, link in enumerate(cat.get("links", [])):
            _add(link.get("url"), f"[{cat_id}] link: {link.get('titulo', '?')}", f"categorias[{i}].links[{j}]")
        # Base legal
        for j, bl in enumerate(cat.get("base_legal", [])):
            _add(bl.get("link"), f"[{cat_id}] lei: {bl.get('lei', '?')}", f"categorias[{i}].base_legal[{j}]")

    # Instituições de apoio
    for i, inst in enumerate(data.get("instituicoes_apoio", [])):
        _add(inst.get("url"), f"instituição: {inst.get('nome', '?')}", f"instituicoes_apoio[{i}].url")
        _add(inst.get("contato"), f"instituição contato: {inst.get('nome', '?')}", f"instituicoes_apoio[{i}].contato")

    # Órgãos estaduais (expandidos: url, sefaz, detran)
    for i, uf_data in enumerate(data.get("orgaos_estaduais", [])):
        uf = uf_data.get("uf", "?")
        _add(uf_data.get("url"), f"órgão estadual: {uf}", f"orgaos_estaduais[{i}].url")
        _add(uf_data.get("sefaz"), f"SEFAZ estadual: {uf}", f"orgaos_estaduais[{i}].sefaz")
        _add(uf_data.get("detran"), f"DETRAN estadual: {uf}", f"orgaos_estaduais[{i}].detran")

    # IPVA SEFAZ URLs (inline em isencoes_tributarias)
    isencoes = next((c for c in data.get("categorias", []) if c.get("id") == "isencoes_tributarias"), None)
    if isencoes:
        for i, est in enumerate(isencoes.get("ipva_estados", [])):
            uf = est.get("uf", "?")
            _add(est.get("sefaz"), f"IPVA SEFAZ: {uf}", f"isencoes_tributarias.ipva_estados[{i}].sefaz")
        for i, est in enumerate(isencoes.get("ipva_estados_detalhado", [])):
            uf = est.get("uf", "?")
            _add(est.get("sefaz"), f"IPVA SEFAZ detalhado: {uf}", f"isencoes_tributarias.ipva_estados_detalhado[{i}].sefaz")

    return urls


MAX_RETRIES = 3
RETRY_DELAY = 4  # seconds


def check_url_live(url: str) -> tuple[int, str]:
    """Verifica se URL responde (status 200).

    Inclui retry com backoff exponencial e fallback HEAD→GET.

    Returns (status_code, mensagem).
    """
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, method="HEAD", headers={
                "User-Agent": USER_AGENT,
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status, "OK"
        except urllib.error.HTTPError as e:
            if e.code in (405, 403):
                # Server rejects HEAD — try GET
                try:
                    req2 = urllib.request.Request(url, method="GET", headers={
                        "User-Agent": USER_AGENT,
                    })
                    with urllib.request.urlopen(req2, timeout=15) as resp2:
                        return resp2.status, "OK"
                except urllib.error.HTTPError as e2:
                    if e2.code >= 500 and attempt < MAX_RETRIES:
                        last_exc = e2
                        time.sleep(RETRY_DELAY * attempt)
                        continue
                    return e2.code, f"HTTP {e2.code}"
                except (TimeoutError, OSError, ConnectionError) as e2:
                    last_exc = e2
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY * attempt)
                        continue
                    return 0, f"Erro: {e2}"
            elif e.code >= 500 and attempt < MAX_RETRIES:
                last_exc = e
                time.sleep(RETRY_DELAY * attempt)
                continue
            else:
                return e.code, f"HTTP {e.code}"
        except urllib.error.URLError as e:
            last_exc = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
                continue
            return 0, f"Erro: {e.reason}"
        except (TimeoutError, OSError, ConnectionError) as e:
            last_exc = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
                continue
            return 0, f"Erro: {e}"
    return 0, f"Erro: {last_exc}"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Valida URLs em direitos.json")
    parser.add_argument("--check-live", action="store_true",
                        help="Verificar status HTTP de cada URL")
    parser.add_argument("--dict", action="store_true",
                        help="Validar dicionário PcD também")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Mostrar todas as URLs (não apenas erros)")
    args = parser.parse_args()

    print("=" * 60)
    print("🔍 VALIDAÇÃO DE URLs — NOSSODIREITO")
    print("=" * 60)

    # 1. Carregar direitos.json
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    urls = extract_all_urls(data)
    print(f"\n📊 Total de URLs extraídas: {len(urls)}")

    # 2. Validar domínios
    non_gov = []
    gov_count = 0
    for entry in urls:
        if is_official_url(entry["url"]):
            gov_count += 1
            if args.verbose:
                print(f"  ✅ {entry['url'][:80]}")
        else:
            non_gov.append(entry)

    print(f"\n{'✅' if not non_gov else '❌'} Domínios oficiais: {gov_count}/{len(urls)}")

    if non_gov:
        print(f"\n⚠️  URLs NÃO-GOVERNAMENTAIS ({len(non_gov)}):")
        for entry in non_gov:
            print(f"  ❌ {entry['url']}")
            print(f"     📍 {entry['context']} ({entry['path']})")

    # 3. Verificar URLs duplicadas
    seen = {}
    duplicates = []
    for entry in urls:
        url_clean = entry["url"].rstrip("/")
        if url_clean in seen:
            duplicates.append((entry, seen[url_clean]))
        else:
            seen[url_clean] = entry

    if duplicates:
        print(f"\n⚠️  URLs DUPLICADAS ({len(duplicates)}):")
        for dup, orig in duplicates[:10]:
            print(f"  🔄 {dup['url'][:60]}")
            print(f"     1ª: {orig['context']}")
            print(f"     2ª: {dup['context']}")

    # 4. Verificar dicionário
    if args.dict and DICT_FILE.exists():
        print(f"\n📖 Validando dicionário PcD...")
        with open(DICT_FILE, "r", encoding="utf-8") as f:
            dicio = json.load(f)
        dict_urls = []
        for lei in dicio.get("leis", []):
            if lei.get("url"):
                dict_urls.append({"url": lei["url"], "context": f"lei: {lei.get('nome', '?')}", "path": "leis"})
        for b in dicio.get("beneficios", []):
            if b.get("url"):
                dict_urls.append({"url": b["url"], "context": f"benefício: {b.get('nome', '?')}", "path": "beneficios"})
        for o in dicio.get("orgaos_denuncia", []):
            if o.get("url"):
                dict_urls.append({"url": o["url"], "context": f"órgão: {o.get('nome', '?')}", "path": "orgaos_denuncia"})

        dict_non_gov = [e for e in dict_urls if not is_official_url(e["url"])]
        print(f"  URLs no dicionário: {len(dict_urls)}")
        print(f"  {'✅' if not dict_non_gov else '❌'} Oficiais: {len(dict_urls) - len(dict_non_gov)}/{len(dict_urls)}")
        if dict_non_gov:
            for entry in dict_non_gov:
                print(f"  ❌ {entry['url']} ({entry['context']})")
            non_gov.extend(dict_non_gov)

    # 5. Check live (opcional)
    if args.check_live:
        print(f"\n🌐 Verificando acessibilidade HTTP ({len(urls)} URLs)...")
        errors = []
        for i, entry in enumerate(urls):
            status, msg = check_url_live(entry["url"])
            if status == 0 or status >= 400:
                errors.append((entry, status, msg))
                print(f"  ❌ [{status}] {entry['url'][:60]} — {msg}")
            elif args.verbose:
                print(f"  ✅ [{status}] {entry['url'][:60]}")
            time.sleep(0.3)
            if (i + 1) % 20 == 0:
                print(f"  ... {i + 1}/{len(urls)} verificadas")

        print(f"\n{'✅' if not errors else '⚠️'} HTTP acessíveis: {len(urls) - len(errors)}/{len(urls)}")
        if errors:
            print(f"  {len(errors)} URLs com problema de acesso")

    # 6. Resumo final
    print("\n" + "=" * 60)
    if not non_gov:
        print("✅ RESULTADO: TODAS AS URLs SÃO DE FONTES OFICIAIS")
        print("   Transparência total — nenhum site externo ao governo.")
        sys.exit(0)
    else:
        print(f"❌ RESULTADO: {len(non_gov)} URL(s) NÃO-GOVERNAMENTAL(IS)")
        print("   Corrija antes de publicar. Apenas .gov.br, .leg.br, .jus.br, .def.br, .mp.br, .mil.br.")
        sys.exit(1)


if __name__ == "__main__":
    main()
