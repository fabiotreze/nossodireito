#!/usr/bin/env python3
"""Validate all URLs from the gov.br PcD services page."""

import urllib.request
import urllib.error
import ssl
import sys

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

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ok_count = 0
fail_count = 0
results = []

print(f"Validando {len(urls)} URLs...\n")

for i, (label, url) in enumerate(urls, 1):
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        code = resp.getcode()
        if code == 200:
            status = "OK"
            ok_count += 1
        else:
            status = f"WARN {code}"
            fail_count += 1
        results.append((status, label, url))
    except urllib.error.HTTPError as e:
        # Some servers reject HEAD, retry with GET
        if e.code == 405 or e.code == 403:
            try:
                req2 = urllib.request.Request(url, method="GET")
                req2.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
                resp2 = urllib.request.urlopen(req2, timeout=10, context=ctx)
                code2 = resp2.getcode()
                resp2.close()
                if code2 == 200:
                    status = "OK"
                    ok_count += 1
                else:
                    status = f"WARN {code2}"
                    fail_count += 1
                results.append((status, label, url))
            except urllib.error.HTTPError as e2:
                fail_count += 1
                results.append((f"FAIL {e2.code}", label, url))
            except Exception as e2:
                fail_count += 1
                results.append((f"FAIL {type(e2).__name__}", label, url))
        else:
            fail_count += 1
            status = f"FAIL {e.code}"
            results.append((status, label, url))
    except Exception as e:
        fail_count += 1
        status = f"FAIL {type(e).__name__}"
        results.append((status, label, url))

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
