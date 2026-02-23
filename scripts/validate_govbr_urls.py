#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate all URLs from the gov.br PcD services page."""

import ssl
import sys
import time
import urllib.error
import urllib.request

MAX_RETRIES = 3
RETRY_DELAY = 4  # seconds


def _fetch_with_retry(url: str, ctx: ssl.SSLContext) -> int:
    """Fetch URL with retry logic for transient errors.

    Returns HTTP status code (200 = success).
    Raises on permanent failure after all retries.
    """
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, method="HEAD")
            req.add_header(
                "User-Agent",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            )
            resp = urllib.request.urlopen(req, timeout=15, context=ctx)
            return resp.getcode()
        except urllib.error.HTTPError as e:
            if e.code in (405, 403):
                # Server rejects HEAD — try GET
                try:
                    req2 = urllib.request.Request(url, method="GET")
                    req2.add_header(
                        "User-Agent",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
                    )
                    resp2 = urllib.request.urlopen(req2, timeout=15, context=ctx)
                    code = resp2.getcode()
                    resp2.close()
                    return code
                except urllib.error.HTTPError as e2:
                    if e2.code >= 500 and attempt < MAX_RETRIES:
                        last_exc = e2
                        time.sleep(RETRY_DELAY * attempt)
                        continue
                    raise
                except (TimeoutError, OSError) as e2:
                    last_exc = e2
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY * attempt)
                        continue
                    raise
            elif e.code >= 500 and attempt < MAX_RETRIES:
                last_exc = e
                time.sleep(RETRY_DELAY * attempt)
                continue
            else:
                raise
        except (TimeoutError, OSError, ConnectionError) as e:
            last_exc = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
                continue
            raise
    raise last_exc  # type: ignore[misc]


def main():
    """Validate all gov.br URLs for PcD services."""
    urls = [
    # === Servicos para PcD ===
    ("Servico: Acompanhamento PcD - UFES",
     "https://www.gov.br/pt-br/servicos/solicitar-assistencia-e-acompanhamento-a-pessoa-com-deficiencia"),
    ("Servico: Acessibilidade Biblioteca Nacional",
     "https://www.gov.br/pt-br/servicos/obter-auxilio-para-dificuldades-de-acessibilidade-em-pesquisas-na-biblioteca-nacional"),
    ("Servico: Acessar Centro-Dia",
     "https://www.gov.br/pt-br/servicos/acessar-centro-dia"),
    ("Servico: Aposentadoria PcD por Tempo",
     "https://www.gov.br/pt-br/servicos/solicitar-aposentadoria-da-pessoa-com-deficiencia-por-tempo-de-contribuicao"),
    ("Servico: Aposentadoria PcD por Idade",
     "https://www.gov.br/pt-br/servicos/solicitar-aposentadoria-por-idade-de-pessoa-com-deficiencia"),
    ("Servico: BPC/LOAS",
     "https://www.gov.br/pt-br/servicos/solicitar-beneficio-assistencial-a-pessoa-com-deficiencia"),
    ("Servico: Suspender BPC para trabalho",
     "https://www.gov.br/pt-br/servicos/suspender%20o-beneficio-assistencial-a-pessoa-com-deficiencia-para-inclusao-no-mercado-de-trabalho"),
    ("Servico: Atencao PcD Auditiva SUS",
     "https://www.gov.br/pt-br/servicos/habilitar-se-para-atencao-especializada-as-pessoas-com-deficiencia-auditiva-no-sistema-unico-de-saude"),
    ("Servico: Reabilitacao urbana",
     "https://www.gov.br/pt-br/servicos/obter-apoio-para-reabilitacao-urbana"),
    ("Servico: Acessibilidade escolas",
     "https://www.gov.br/pt-br/servicos/obter-recursos-para-obras-de-acessibilidade-em-escolas-publicas"),
    ("Servico: Turismo Acessivel - Avaliar",
     "https://www.gov.br/pt-br/servicos/avaliar-estabelecimentos-conforme-suas-caracteristicas-de-acessibilidade"),
    ("Servico: Turismo Acessivel - Cadastro",
     "https://www.gov.br/pt-br/servicos/cadastrar-se-no-site-turismo-acessivel"),

    # === Orgaos Relacionados ===
    ("Orgao: Biblioteca Nacional",
     "https://www.gov.br/pt-br/orgaos/fundacao-biblioteca-nacional"),
    ("Orgao: INSS",
     "https://www.gov.br/pt-br/orgaos/instituto-nacional-do-seguro-social"),
    ("Orgao: MEC",
     "https://www.gov.br/pt-br/orgaos/ministerio-da-educacao"),
    ("Orgao: MGI",
     "https://www.gov.br/pt-br/orgaos/ministerio-da-gestao-e-da-inovacao-em-servicos-publicos"),
    ("Orgao: MS",
     "https://www.gov.br/pt-br/orgaos/ministerio-da-saude"),
    ("Orgao: MCID",
     "https://www.gov.br/pt-br/orgaos/ministerio-das-cidades"),
    ("Orgao: MDS",
     "https://www.gov.br/pt-br/orgaos/ministerio-do-desenvolvimento-e-assistencia-social-familia-e-combate-a-fome"),
    ("Orgao: MTur",
     "https://www.gov.br/pt-br/orgaos/ministerio-do-turismo"),
    ("Orgao: MDHC",
     "https://www.gov.br/pt-br/orgaos/ministerio-dos-direitos-humanos-e-da-cidadania"),
    ("Orgao: UFES",
     "https://www.gov.br/pt-br/orgaos/universidade-federal-do-espirito-santo"),

    # === Links do cabecalho ===
    ("Legislacao: PI 323/2020",
     "https://www.in.gov.br/en/web/dou/-/portaria-interministerial-n-323-de-10-de-setembro-de-2020-276902528"),
    ("Programas MMFDH",
     "https://www.gov.br/mdh/pt-br/navegue-por-temas/pessoa-com-deficiencia/acoes-e-programas"),
    ("Acessibilidade Digital",
     "https://www.gov.br/governodigital/pt-br/acessibilidade-e-usuario/acessibilidade-digital"),
    ("Modelo eMAG",
     "https://www.gov.br/governodigital/pt-br/acessibilidade-e-usuario/acessibilidade-digital/modelo-de-acessibilidade"),
    ]

    sys.stdout.reconfigure(encoding='utf-8')

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    ok_count = 0
    fail_count = 0
    results = []

    print(f"Validando {len(urls)} URLs (max {MAX_RETRIES} tentativas, "
          f"intervalo {RETRY_DELAY}s)...\n")

    for i, (label, url) in enumerate(urls, 1):
        try:
            code = _fetch_with_retry(url, ctx)
            if code == 200:
                status = "OK"
                ok_count += 1
            else:
                status = f"WARN {code}"
                fail_count += 1
            results.append((status, label, url))
        except urllib.error.HTTPError as e:
            fail_count += 1
            results.append((f"FAIL {e.code}", label, url))
        except Exception as e:
            fail_count += 1
            results.append((f"FAIL {type(e).__name__}", label, url))

        icon = "." if status == "OK" else "X"
        sys.stdout.write(f"  [{i:2d}/{len(urls)}] {icon} {label}\n")
        sys.stdout.flush()

    print(f"\n\n{'='*60}")
    print(f"RESULTADO: {ok_count} OK / {fail_count} FALHA (de {len(urls)} URLs)")
    print(f"{'='*60}\n")

    for status, label, url in results:
        if status == "OK":
            print(f"  [OK]   {label}")
        else:
            print(f"  [FAIL] {label}")
            print(f"         Status: {status}")
            print(f"         URL: {url}")

    failures = [(s, l, u) for s, l, u in results if s != "OK"]
    if failures:
        print(f"\n--- {len(failures)} URL(s) com problema ---")
        for s, l, u in failures:
            print(f"  [{s}] {l}")
            print(f"    {u}")
    else:
        print("\n--- Todas as 26 URLs estao funcionando! ---")


if __name__ == '__main__':
    main()
