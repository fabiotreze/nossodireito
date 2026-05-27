#!/usr/bin/env python3
"""
NossoDireito — Descoberta Automática de Novos Benefícios PcD
=============================================================
Monitora fontes oficiais brasileiras (DOU, gov.br, Senado, LexML)
para detectar novos direitos, benefícios, leis e serviços para PcD.

Gera um relatório JSON + Markdown com candidatos para análise humana.

Uso:
    python scripts/discover_benefits.py                       # Todos os níveis
    python scripts/discover_benefits.py --dry-run             # Apenas mostra
    python scripts/discover_benefits.py --since 30            # Últimos 30 dias
    python scripts/discover_benefits.py --nivel federal       # Só federal
    python scripts/discover_benefits.py --nivel estadual      # Só 27 estados
    python scripts/discover_benefits.py --nivel municipal     # Só municípios
    python scripts/discover_benefits.py --estado SP RJ        # Filtrar UFs
    python scripts/discover_benefits.py --cidade barueri-sp   # Filtrar cidade

Fontes consultadas:
  Federal:
    1. gov.br @@search (DOU, Notícias, Serviços) — busca universal
    2. Senado Federal Dados Abertos — legislação em tramitação
    3. Portal gov.br Serviços — catálogo de serviços digitais PcD
    4. Portal gov.br Notícias — INSS, MDS, Saúde, Direitos Humanos
    5. LexML Brasil — metadados legislativos abertos
  Estadual:
    6. gov.br @@search por estado — 27 UFs (todos os estados + DF)
  Municipal:
    7. gov.br @@search por município — cidades configuradas
    8. Portais municipais oficiais — scraping de páginas PcD

Cobertura: Brasil inteiro (federal + 27 estados + municípios).
Apenas fontes oficiais (.gov.br, .leg.br, .jus.br, .mp.br, .def.br).

Nenhum dado é alterado automaticamente. O script gera candidatos para
revisão humana seguindo o fluxo definido em GOVERNANCE.md.
"""

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# ─── Configuração ──────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "direitos.json"
DICT_FILE = ROOT / "data" / "dicionario_pcd.json"
REPORT_DIR = ROOT / "data"
REPORT_JSON = REPORT_DIR / "discovery_report.json"
REPORT_MD = REPORT_DIR / "discovery_report.md"

RATE_LIMIT_DELAY = 0.5  # segundos entre requisições
REQUEST_TIMEOUT = 15     # segundos por requisição
USER_AGENT = "NossoDireito-DiscoveryBot/1.0 (+https://nossodireito.fabiotreze.com)"

# Palavras-chave PcD para busca em fontes oficiais
PCD_KEYWORDS = [
    "pessoa com deficiência",
    "pessoa com deficiencia",
    "pessoas com deficiência",
    "pessoas com deficiencia",
    "PcD",
    "autismo",
    "TEA",
    "espectro autista",
    "transtorno do espectro autista",
    "deficiência física",
    "deficiência visual",
    "deficiência auditiva",
    "deficiência intelectual",
    "deficiência mental",
    "deficiência múltipla",
    "acessibilidade",
    "inclusão social",
    "tecnologia assistiva",
    "benefício assistencial",
    "BPC",
    "LOAS",
    "Estatuto da Pessoa com Deficiência",
    "Lei Brasileira de Inclusão",
    "CIPTEA",
    "Romeo Mion",
    "Berenice Piana",
    "Novo Viver sem Limite",
    "isenção IPI deficiência",
    "isenção ICMS deficiência",
    "isenção IOF deficiência",
    "passe livre interestadual",
    "meia-entrada deficiência",
    "cota deficiência",
    "reserva de vagas deficiência",
    "aposentadoria pessoa com deficiência",
    "FGTS deficiência",
    "plano de saúde deficiência",
    "SUS terapias",
    "atendimento prioritário deficiência",
]

# Termos de busca reduzidos para consultas a APIs (evita excesso de requests)
SEARCH_QUERIES = [
    "pessoa com deficiência",
    "autismo TEA",
    "acessibilidade inclusão",
    "BPC LOAS deficiência",
    "isenção deficiência",
    "tecnologia assistiva",
]

# IDs já conhecidos em direitos.json (carregados dinamicamente)
KNOWN_IDS: set[str] = set()
KNOWN_URLS: set[str] = set()
KNOWN_LAWS: set[str] = set()

# ─── Configuração Geográfica (Brasil inteiro) ─────────────────────
# Todos os 27 estados brasileiros (26 estados + DF)
UF_ESTADOS = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal",
    "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
    "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco",
    "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima",
    "SC": "Santa Catarina", "SP": "São Paulo", "SE": "Sergipe",
    "TO": "Tocantins",
}

# Municípios com portais oficiais configurados (expandível)
# Para adicionar cidades, basta inserir uma entrada aqui.
MUNICIPIOS_BR = {
    # Grande São Paulo (solicitadas pelo usuário)
    "barueri-sp": {
        "nome": "Barueri", "uf": "SP",
        "portal": "https://portal.barueri.sp.gov.br",
        "paginas_pcd": [
            "https://portal.barueri.sp.gov.br/cidadao/pessoa-com-deficiencia",
            "https://portal.barueri.sp.gov.br/secretarias/secretaria-dos-direitos-da-pessoa-com-deficiencia",
        ],
    },
    "osasco-sp": {
        "nome": "Osasco", "uf": "SP",
        "portal": "https://osasco.sp.gov.br",
        "paginas_pcd": [],
    },
    "santo-andre-sp": {
        "nome": "Santo André", "uf": "SP",
        "portal": "https://web.santoandre.sp.gov.br",
        "paginas_pcd": [
            "https://web.santoandre.sp.gov.br/portal/secretarias-paginas/320/inclusao-e-acessibilidade/",
        ],
    },
    # Capitais estaduais (portais .gov.br)
    "sao-paulo-sp": {
        "nome": "São Paulo", "uf": "SP",
        "portal": "https://capital.sp.gov.br",
        "paginas_pcd": [
            "https://prefeitura.sp.gov.br/web/pessoa_com_deficiencia",
        ],
    },
    "belo-horizonte-mg": {
        "nome": "Belo Horizonte", "uf": "MG",
        "portal": "https://prefeitura.pbh.gov.br",
        "paginas_pcd": [],
    },
    "salvador-ba": {
        "nome": "Salvador", "uf": "BA",
        "portal": "https://www.salvador.ba.gov.br",
        "paginas_pcd": [],
    },
    "brasilia-df": {
        "nome": "Brasília", "uf": "DF",
        "portal": "https://www.df.gov.br",
        "paginas_pcd": [],
    },
    "curitiba-pr": {
        "nome": "Curitiba", "uf": "PR",
        "portal": "https://www.curitiba.pr.gov.br",
        "paginas_pcd": [],
    },
    "recife-pe": {
        "nome": "Recife", "uf": "PE",
        "portal": "https://www2.recife.pe.gov.br",
        "paginas_pcd": [],
    },
    "fortaleza-ce": {
        "nome": "Fortaleza", "uf": "CE",
        "portal": "https://www.fortaleza.ce.gov.br",
        "paginas_pcd": [],
    },
    "manaus-am": {
        "nome": "Manaus", "uf": "AM",
        "portal": "https://www.manaus.am.gov.br",
        "paginas_pcd": [],
    },
    "belem-pa": {
        "nome": "Belém", "uf": "PA",
        "portal": "https://www.belem.pa.gov.br",
        "paginas_pcd": [],
    },
    "goiania-go": {
        "nome": "Goiânia", "uf": "GO",
        "portal": "https://www.goiania.go.gov.br",
        "paginas_pcd": [],
    },
    "guarulhos-sp": {
        "nome": "Guarulhos", "uf": "SP",
        "portal": "https://www.guarulhos.sp.gov.br",
        "paginas_pcd": [],
    },
    "campinas-sp": {
        "nome": "Campinas", "uf": "SP",
        "portal": "https://www.campinas.sp.gov.br",
        "paginas_pcd": [],
    },
}

# Domínios oficiais do governo brasileiro (apenas estes são aceitos)
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


def load_dictionary_keywords():
    """Carrega dicionario_pcd.json e enriquece PCD_KEYWORDS e SEARCH_QUERIES."""
    global PCD_KEYWORDS, SEARCH_QUERIES
    if not DICT_FILE.exists():
        return
    try:
        with open(DICT_FILE, "r", encoding="utf-8") as f:
            dicio = json.load(f)
        extra_kw = set()
        # Keywords de deficiências
        for d in dicio.get("deficiencias", []):
            extra_kw.update(d.get("keywords_busca", []))
            extra_kw.update(d.get("sinonimos", []))
        # Keywords mestre
        for cat_kws in dicio.get("keywords_master", {}).values():
            if isinstance(cat_kws, list):
                extra_kw.update(cat_kws)
        # Keywords de benefícios
        for b in dicio.get("beneficios", []):
            extra_kw.update(b.get("keywords_busca", []))
        # Adiciona novas keywords (sem duplicar)
        existing = {kw.lower() for kw in PCD_KEYWORDS}
        for kw in sorted(extra_kw):
            if kw.lower() not in existing and len(kw) >= 3:
                PCD_KEYWORDS.append(kw)
                existing.add(kw.lower())
        # Enriquece SEARCH_QUERIES com termos do dicionário
        extra_queries = [
            "Síndrome de Down deficiência",
            "TDAH deficiência escola",
            "paralisia cerebral reabilitação",
            "nanismo acondroplasia deficiência",
            "surdez implante coclear Libras",
            "cegueira bengala cão-guia",
            "esquizofrenia CAPS saúde mental",
            "microcefalia Zika deficiência",
            "prótese órtese SUS",
            "cadeira de rodas motorizada",
        ]
        eq_set = {q.lower() for q in SEARCH_QUERIES}
        for q in extra_queries:
            if q.lower() not in eq_set:
                SEARCH_QUERIES.append(q)
                eq_set.add(q.lower())
    except (json.JSONDecodeError, KeyError, OSError) as e:
        print(f"⚠️  Aviso: não foi possível carregar dicionário PcD: {e}")


# Carrega dicionário ao importar o módulo
load_dictionary_keywords()


# ─── Helpers ───────────────────────────────────────────────────────
def log(msg: str, level: str = "INFO") -> None:
    symbols = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERR": "❌", "NEW": "🆕", "SKIP": "⏭️"}
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {symbols.get(level, 'ℹ️')}  {msg}")


def fetch(url: str, *, json_resp: bool = False, retries: int = 2) -> str | dict | None:
    """Faz GET com retry, rate-limit e User-Agent. Retorna texto ou dict."""
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "pt-BR,pt;q=0.9"}
    if json_resp:
        headers["Accept"] = "application/json"

    for attempt in range(retries + 1):
        try:
            if attempt > 0:
                wait = 2 ** attempt
                log(f"  Retry {attempt}/{retries} em {wait}s...", "WARN")
                time.sleep(wait)

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                data = resp.read().decode("utf-8", errors="replace")
                time.sleep(RATE_LIMIT_DELAY)
                if json_resp:
                    return json.loads(data)
                return data
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as e:
            if attempt == retries:
                log(f"  Falha ao acessar {url[:80]}: {e}", "ERR")
                return None
    return None


def normalize_text(text: str) -> str:
    """Remove acentos e normaliza para comparação."""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def text_has_pcd_keywords(text: str) -> list[str]:
    """Retorna quais keywords PcD estão presentes no texto."""
    text_lower = text.lower()
    text_norm = normalize_text(text)
    found = []
    for kw in PCD_KEYWORDS:
        kw_lower = kw.lower()
        kw_norm = normalize_text(kw)
        # Para keywords curtas (TEA, BPC, PcD), usa word boundary
        # para evitar falsos positivos (ex: "teatro" ≠ "TEA")
        if len(kw) <= 4:
            pattern = r'\b' + re.escape(kw_lower) + r'\b'
            pattern_norm = r'\b' + re.escape(kw_norm) + r'\b'
            if re.search(pattern, text_lower) or re.search(pattern_norm, text_norm):
                found.append(kw)
        else:
            if kw_lower in text_lower or kw_norm in text_norm:
                found.append(kw)
    return found


def is_known_url(url: str) -> bool:
    """Verifica se URL já está em direitos.json."""
    return url in KNOWN_URLS or url.rstrip("/") in KNOWN_URLS


def is_known_law(law_ref: str) -> bool:
    """Verifica se referência legislativa já está em direitos.json."""
    # Normaliza: remove pontos do número
    law_norm = re.sub(r"(\d)\.(\d)", r"\1\2", law_ref.lower().strip())
    return any(law_norm in kl for kl in KNOWN_LAWS)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def is_official_domain(url: str) -> bool:
    """Verifica se URL pertence a domínio oficial do governo brasileiro ou organismo internacional confiável."""
    try:
        domain = urllib.parse.urlparse(url).hostname or ""
        domain = domain.lower()
        if any(domain.endswith(d) for d in DOMINIOS_OFICIAIS):
            return True
        if any(domain == d or domain.endswith("." + d) for d in DOMINIOS_INTERNACIONAIS):
            return True
        return False
    except Exception:
        return False


# ─── Carregamento dos dados existentes ─────────────────────────────
def load_existing_data() -> dict:
    """Carrega direitos.json e popula KNOWN_IDS, KNOWN_URLS, KNOWN_LAWS."""
    global KNOWN_IDS, KNOWN_URLS, KNOWN_LAWS

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # IDs de categorias
    KNOWN_IDS = {cat["id"] for cat in data.get("categorias", [])}

    # Todas as URLs referenciadas
    urls = set()
    for fonte in data.get("fontes", []):
        if fonte.get("url"):
            urls.add(fonte["url"])
            urls.add(fonte["url"].rstrip("/"))
    for cat in data.get("categorias", []):
        for link in cat.get("links", []):
            if link.get("url"):
                urls.add(link["url"])
                urls.add(link["url"].rstrip("/"))
        for bl in cat.get("base_legal", []):
            if bl.get("link"):
                urls.add(bl["link"])
                urls.add(bl["link"].rstrip("/"))
    KNOWN_URLS = urls

    # Referências legislativas
    laws = set()
    for fonte in data.get("fontes", []):
        nome = fonte.get("nome", "").lower()
        nome_norm = re.sub(r"(\d)\.(\d)", r"\1\2", nome)
        laws.add(nome_norm)
    for cat in data.get("categorias", []):
        for bl in cat.get("base_legal", []):
            lei = bl.get("lei", "").lower()
            lei_norm = re.sub(r"(\d)\.(\d)", r"\1\2", lei)
            laws.add(lei_norm)
    KNOWN_LAWS = laws

    return data


# ─── Fonte 1: DOU (Diário Oficial da União) ───────────────────────
def search_dou(since_days: int = 60) -> list[dict]:
    """
    Busca publicações oficiais e notícias sobre PcD usando o motor de
    busca universal do portal gov.br:
    https://www.gov.br/pt-br/@@search?SearchableText=...

    Esse endpoint agrega conteúdo de todo o governo federal — DOU,
    serviços, notícias — com filtros por tipo_conteudo (Notícia,
    Serviço, etc.) e paginação via start/b_size.
    """
    candidates = []
    log("Consultando gov.br @@search (busca universal — DOU + notícias)...")

    today = datetime.now().strftime("%Y-%m-%d")

    # Busca por cada keyword nas categorias Notícia e geral
    for query in SEARCH_QUERIES[:3]:
        for tipo in ["Notícia", ""]:
            encoded = urllib.parse.quote(query)
            params = f"SearchableText={encoded}&b_size=20"
            if tipo:
                params += f"&tipo_conteudo={urllib.parse.quote(tipo)}"
            url = f"https://www.gov.br/pt-br/@@search?{params}"

            label = f"({tipo or 'Todos'})"
            log(f"  gov.br busca '{query}' {label}...")
            html = fetch(url)
            if not html:
                continue

            # Extrai links de resultados — títulos linkados do gov.br
            results = re.findall(
                r'<a[^>]+href="(https://www\.gov\.br/[^"]+)"[^>]*>\s*'
                r'(?:<[^>]+>)*([^<]{10,300})',
                html,
                re.IGNORECASE,
            )

            if not results:
                # Alternativo: qualquer link gov.br com texto significativo
                results = re.findall(
                    r'href="(https://www\.gov\.br/[^"]+)"[^>]*>([^<]{10,300})',
                    html,
                    re.IGNORECASE,
                )

            for result_url, title in results[:15]:
                title = title.strip()
                if not title or len(title) < 10:
                    continue

                # Ignora links de navegação, footer, etc.
                skip_patterns = [
                    "/@@search", "/sitemap", "/termos-de-uso",
                    "/por-dentro-do-govbr", "/navegacao",
                    "/canais-do-executivo", "/orgaos-do-governo",
                    "vlibras.gov.br", "/apps/",
                ]
                if any(p in result_url.lower() for p in skip_patterns):
                    continue

                if is_known_url(result_url):
                    continue

                keywords = text_has_pcd_keywords(title)
                if keywords:
                    item_type = "news" if tipo == "Notícia" else "legislation"
                    candidates.append({
                        "source": "gov.br Busca",
                        "title": title[:200],
                        "url": result_url,
                        "keywords": keywords[:5],
                        "date_found": today,
                        "query": query,
                        "type": item_type,
                        "hash": content_hash(result_url + title),
                    })

    # Dedup intra-busca
    seen: set[str] = set()
    unique = []
    for c in candidates:
        if c["hash"] not in seen:
            seen.add(c["hash"])
            unique.append(c)
    candidates = unique

    log(f"  gov.br Busca: {len(candidates)} candidatos encontrados", "OK" if candidates else "INFO")
    return candidates


# ─── Fonte 2: Senado Federal Dados Abertos ─────────────────────────
def search_senado(since_days: int = 60) -> list[dict]:
    """
    Consulta a API do Senado Federal (Dados Abertos) para matérias
    legislativas recentes relacionadas a PcD.
    Endpoint: /dadosabertos/materia/pesquisa/lista
    Docs: https://legis.senado.leg.br/dadosabertos/
    """
    candidates = []
    log("Consultando Senado Federal Dados Abertos...")

    since_dt = datetime.now() - timedelta(days=since_days)
    since_yyyymmdd = since_dt.strftime("%Y%m%d")
    today_yyyymmdd = datetime.now().strftime("%Y%m%d")
    today = datetime.now().strftime("%Y-%m-%d")

    for query in SEARCH_QUERIES[:3]:
        encoded = urllib.parse.quote(query)
        url = (
            f"https://legis.senado.leg.br/dadosabertos/materia/pesquisa/lista"
            f"?palavraChave={encoded}"
            f"&dataInicioApresentacao={since_yyyymmdd}"
            f"&dataFimApresentacao={today_yyyymmdd}"
        )

        log(f"  Senado busca: '{query}'")
        data = fetch(url, json_resp=True)
        if not data:
            continue

        # Navega a estrutura do JSON: PesquisaBasicaMateria > Materias > Materia[]
        items = []
        if isinstance(data, dict):
            pesquisa = data.get("PesquisaBasicaMateria", data)
            materias = pesquisa.get("Materias", {})
            if isinstance(materias, dict):
                items = materias.get("Materia", [])
            elif isinstance(materias, list):
                items = materias

        if not isinstance(items, list):
            items = [items] if items else []

        for item in items[:10]:
            if not isinstance(item, dict):
                continue

            # Campos da matéria
            ident = item.get("IdentificacaoMateria", {})
            if isinstance(ident, dict):
                sigla = ident.get("SiglaSubtipoMateria", "")
                numero = ident.get("NumeroMateria", "")
                ano = ident.get("AnoMateria", "")
            else:
                sigla = numero = ano = ""

            ementa = item.get("EmentaMateria", item.get("Ementa", "")).strip()
            if not ementa:
                # Tenta DadosBasicosMateria
                dados = item.get("DadosBasicosMateria", {})
                if isinstance(dados, dict):
                    ementa = dados.get("EmentaMateria", "").strip()

            if not ementa:
                continue

            law_ref = f"{sigla} {numero}/{ano}".strip()
            materia_url = f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{numero}" if numero else ""

            if is_known_law(law_ref) or is_known_url(materia_url):
                continue

            keywords = text_has_pcd_keywords(ementa)
            if keywords:
                candidates.append({
                    "source": "Senado",
                    "title": f"{law_ref} — {ementa[:120]}",
                    "url": materia_url,
                    "keywords": keywords[:5],
                    "date_found": today,
                    "query": query,
                    "type": "legislation",
                    "law_ref": law_ref,
                    "hash": content_hash(law_ref + ementa),
                })

    log(f"  Senado: {len(candidates)} candidatos encontrados", "OK" if candidates else "INFO")
    return candidates


# ─── Fonte 3: Portal gov.br Serviços ──────────────────────────────
def search_govbr_services() -> list[dict]:
    """
    Consulta o catálogo de serviços do portal gov.br para novos
    serviços digitais relevantes para PcD.
    """
    candidates = []
    log("Consultando catálogo de serviços gov.br...")

    today = datetime.now().strftime("%Y-%m-%d")

    for query in SEARCH_QUERIES[:3]:
        encoded = urllib.parse.quote(query)
        # API pública do portal de serviços
        url = (
            f"https://www.gov.br/pt-br/servicos/"
            f"@@search?SearchableText={encoded}"
            f"&portal_type=Servico"
        )

        log(f"  gov.br serviços: '{query}'")
        html = fetch(url)
        if not html:
            continue

        # Parse resultados HTML
        results = re.findall(
            r'<a[^>]+href="(https://www\.gov\.br/[^"]+/servicos/[^"]+)"[^>]*>\s*'
            r'(?:<[^>]+>)*([^<]+)',
            html,
            re.IGNORECASE,
        )

        if not results:
            # Padrão alternativo
            results = re.findall(
                r'href="(https://www\.gov\.br/[^"]+)"[^>]*class="[^"]*titulo[^"]*"[^>]*>([^<]+)',
                html,
                re.IGNORECASE,
            )

        for service_url, title in results[:8]:
            title = title.strip()
            if not title or len(title) < 5:
                continue

            if is_known_url(service_url):
                continue

            keywords = text_has_pcd_keywords(title)
            if keywords:
                candidates.append({
                    "source": "gov.br",
                    "title": title[:150],
                    "url": service_url,
                    "keywords": keywords[:5],
                    "date_found": today,
                    "query": query,
                    "type": "service",
                    "hash": content_hash(service_url + title),
                })

    log(f"  gov.br serviços: {len(candidates)} candidatos", "OK" if candidates else "INFO")
    return candidates


# ─── Fonte 4: Notícias INSS / MDS ─────────────────────────────────
def search_govbr_news() -> list[dict]:
    """
    Verifica notícias recentes nos portais do INSS e MDS que possam
    indicar novos benefícios ou mudanças significativas.
    """
    candidates = []
    log("Consultando notícias gov.br (INSS, MDS, Saúde)...")

    today = datetime.now().strftime("%Y-%m-%d")

    news_sources = [
        ("INSS", "https://www.gov.br/inss/pt-br/noticias"),
        ("MDS", "https://www.gov.br/mds/pt-br/noticias-e-conteudos/noticias"),
        ("Saúde", "https://www.gov.br/saude/pt-br/assuntos/noticias"),
        ("Direitos Humanos", "https://www.gov.br/mdh/pt-br/assuntos/noticias"),
    ]

    for source_name, news_url in news_sources:
        log(f"  Notícias {source_name}...")
        html = fetch(news_url)
        if not html:
            continue

        # Extrai links de notícias (aceita /noticias/ e /noticias-e-conteudos/)
        news_links = re.findall(
            r'<a[^>]+href="(https://www\.gov\.br/[^"]+/noticias[^"]*)"[^>]*>\s*'
            r'(?:<[^>]+>)*([^<]{10,200})',
            html,
            re.IGNORECASE,
        )

        if not news_links:
            news_links = re.findall(
                r'href="([^"]+)"[^>]*>([^<]*(?:defici|autis|pcd|bpc|acessibil|inclusão)[^<]*)',
                html,
                re.IGNORECASE,
            )

        for link_url, title in news_links[:10]:
            title = title.strip()
            if not title or len(title) < 10:
                continue

            if not link_url.startswith("http"):
                link_url = f"https://www.gov.br{link_url}"

            keywords = text_has_pcd_keywords(title)
            if keywords:
                candidates.append({
                    "source": f"Notícias {source_name}",
                    "title": title[:150],
                    "url": link_url,
                    "keywords": keywords[:5],
                    "date_found": today,
                    "type": "news",
                    "hash": content_hash(link_url),
                })

    log(f"  Notícias: {len(candidates)} candidatos", "OK" if candidates else "INFO")
    return candidates


# ─── Fonte 5: LexML Brasil ────────────────────────────────────────
def search_lexml(since_days: int = 60) -> list[dict]:
    """
    Consulta o portal LexML Brasil para legislação relacionada a PcD.
    Usa a busca web: https://www.lexml.gov.br/busca/search?keyword=...
    O LexML agrega 85 mil+ documentos legais de tribunais, Senado,
    Câmara, AGU e bibliotecas jurídicas.
    """
    candidates = []
    log("Consultando LexML Brasil (busca web)...")

    today = datetime.now().strftime("%Y-%m-%d")

    # Termos de busca focados em legislação PcD
    kw_queries = [
        "pessoa com deficiência",
        "autismo",
        "acessibilidade",
    ]

    for keyword in kw_queries:
        encoded = urllib.parse.quote(keyword)
        url = f"https://www.lexml.gov.br/busca/search?keyword={encoded}"

        log(f"  LexML busca: '{keyword}'")
        html = fetch(url)
        if not html:
            continue

        # Extrai resultados: links para URNs legislativas
        # Padrão: <a href="https://www.lexml.gov.br/urn/...">Título</a>
        results = re.findall(
            r'<a[^>]+href="(https://www\.lexml\.gov\.br/urn/[^"]+)"[^>]*>\s*'
            r'(?:<[^>]+>)*\s*([^<]{10,300})',
            html,
            re.IGNORECASE,
        )

        if not results:
            # Alternativo: links com urn:lex no texto
            results = re.findall(
                r'href="(https://www\.lexml\.gov\.br/urn/urn[^"]+)"[^>]*>([^<]+)',
                html,
                re.IGNORECASE,
            )

        # Extrai também ementas associadas (texto após o link)
        # O LexML mostra "Ementa: texto..." perto dos links
        ementas = re.findall(
            r'(?:Ementa|ementa)\s*(?:</[^>]+>\s*)*([^<]{20,500})',
            html,
            re.IGNORECASE,
        )

        for i, (lex_url, title) in enumerate(results[:10]):
            title = title.strip()
            if not title or len(title) < 5:
                continue

            # Enriquece com ementa se disponível
            ementa = ementas[i].strip() if i < len(ementas) else ""
            full_title = title
            if ementa and len(ementa) > len(title):
                full_title = f"{title} — {ementa[:120]}"

            if is_known_url(lex_url) or is_known_law(title):
                continue

            search_text = f"{title} {ementa}"
            keywords = text_has_pcd_keywords(search_text)
            if keywords:
                candidates.append({
                    "source": "LexML",
                    "title": full_title[:200],
                    "url": lex_url,
                    "keywords": keywords[:5],
                    "date_found": today,
                    "type": "legislation",
                    "hash": content_hash(lex_url + title),
                })

    # Dedup
    seen: set[str] = set()
    unique = []
    for c in candidates:
        if c["hash"] not in seen:
            seen.add(c["hash"])
            unique.append(c)
    candidates = unique

    log(f"  LexML: {len(candidates)} candidatos", "OK" if candidates else "INFO")
    return candidates


# ─── Fonte 6: Portais Estaduais (27 UFs) ──────────────────────────
def search_estados(since_days: int = 60, filtro_uf: list[str] | None = None) -> list[dict]:
    """
    Busca PcD em nível estadual usando gov.br @@search com nome do estado.
    Cobre todos os 27 estados + DF. Apenas URLs de domínios oficiais.
    """
    candidates = []
    estados = {uf: nome for uf, nome in UF_ESTADOS.items()
               if not filtro_uf or uf in filtro_uf}
    log(f"Consultando fontes estaduais ({len(estados)} UFs)...")
    today = datetime.now().strftime("%Y-%m-%d")

    skip_patterns = [
        "/@@search", "/sitemap", "/termos-de-uso",
        "/por-dentro-do-govbr", "/navegacao",
        "/canais-do-executivo", "/orgaos-do-governo",
        "vlibras.gov.br", "/apps/",
    ]

    for uf, estado in estados.items():
        search_term = f"pessoa com deficiência {estado}"
        encoded = urllib.parse.quote(search_term)
        url = f"https://www.gov.br/pt-br/@@search?SearchableText={encoded}&b_size=10"

        log(f"  {uf} ({estado})...")
        html = fetch(url)
        if not html:
            continue

        results = re.findall(
            r'<a[^>]+href="(https://www\.gov\.br/[^"]+)"[^>]*>\s*'
            r'(?:<[^>]+>)*([^<]{10,300})',
            html, re.IGNORECASE,
        )
        if not results:
            results = re.findall(
                r'href="(https://www\.gov\.br/[^"]+)"[^>]*>([^<]{10,300})',
                html, re.IGNORECASE,
            )

        for result_url, title in results[:8]:
            title = title.strip()
            if not title or len(title) < 10:
                continue
            if any(p in result_url.lower() for p in skip_patterns):
                continue
            if is_known_url(result_url) or not is_official_domain(result_url):
                continue

            keywords = text_has_pcd_keywords(title)
            if keywords:
                candidates.append({
                    "source": f"Estado {uf}",
                    "title": title[:200],
                    "url": result_url,
                    "keywords": keywords[:5],
                    "date_found": today,
                    "query": search_term,
                    "type": "legislation",
                    "nivel": "estadual",
                    "uf": uf,
                    "hash": content_hash(result_url + title),
                })

    # Dedup intra-busca
    seen: set[str] = set()
    unique = []
    for c in candidates:
        if c["hash"] not in seen:
            seen.add(c["hash"])
            unique.append(c)

    log(f"  Estados: {len(unique)} candidatos", "OK" if unique else "INFO")
    return unique


# ─── Fonte 7: Portais Municipais ──────────────────────────────────
def search_municipios(since_days: int = 60, filtro_cidades: list[str] | None = None) -> list[dict]:
    """
    Busca PcD em nível municipal via gov.br @@search + portais configurados.
    Apenas URLs de domínios oficiais (DOMINIOS_OFICIAIS).
    """
    candidates = []
    cidades = {k: v for k, v in MUNICIPIOS_BR.items()
               if not filtro_cidades or k in filtro_cidades}

    log(f"Consultando fontes municipais ({len(cidades)} cidades)...")
    today = datetime.now().strftime("%Y-%m-%d")

    skip_nav = [
        "/@@search", "/sitemap", "/termos-de-uso",
        "/por-dentro-do-govbr", "/navegacao",
        "/canais-do-executivo", "/orgaos-do-governo",
        "vlibras.gov.br", "/apps/",
    ]
    skip_portal = [
        "/@@", "/sitemap", "/login", "/cadastro",
        "javascript:", "#", ".pdf", ".jpg", ".png",
        "vlibras.gov.br",
    ]

    for slug, info in cidades.items():
        nome = info["nome"]
        uf = info["uf"]

        # --- Estratégia 1: gov.br @@search com nome da cidade ---
        search_term = f"pessoa com deficiência {nome} {uf}"
        encoded = urllib.parse.quote(search_term)
        url = f"https://www.gov.br/pt-br/@@search?SearchableText={encoded}&b_size=10"

        log(f"  {nome}/{uf} (gov.br)...")
        html = fetch(url)
        if html:
            results = re.findall(
                r'<a[^>]+href="(https://www\.gov\.br/[^"]+)"[^>]*>\s*'
                r'(?:<[^>]+>)*([^<]{10,300})',
                html, re.IGNORECASE,
            )
            if not results:
                results = re.findall(
                    r'href="(https://www\.gov\.br/[^"]+)"[^>]*>([^<]{10,300})',
                    html, re.IGNORECASE,
                )

            for result_url, title in results[:5]:
                title = title.strip()
                if not title or len(title) < 10:
                    continue
                if any(p in result_url.lower() for p in skip_nav):
                    continue
                if is_known_url(result_url) or not is_official_domain(result_url):
                    continue

                keywords = text_has_pcd_keywords(title)
                if keywords:
                    candidates.append({
                        "source": f"Município {nome}/{uf}",
                        "title": title[:200],
                        "url": result_url,
                        "keywords": keywords[:5],
                        "date_found": today,
                        "query": search_term,
                        "type": "service",
                        "nivel": "municipal",
                        "uf": uf,
                        "municipio": nome,
                        "hash": content_hash(result_url + title),
                    })

        # --- Estratégia 2: Scraping de portais municipais PcD ---
        portal = info.get("portal", "")
        for pagina_url in info.get("paginas_pcd", []):
            log(f"  {nome}/{uf} (portal PcD)...")
            phtml = fetch(pagina_url)
            if not phtml:
                continue

            portal_links = re.findall(
                r'href="([^"]+)"[^>]*>([^<]{5,200})',
                phtml, re.IGNORECASE,
            )

            for link_url, title in portal_links:
                title = title.strip()
                if not title or len(title) < 5:
                    continue
                # Normaliza URL relativa
                if link_url.startswith("/"):
                    link_url = f"{portal.rstrip('/')}{link_url}"
                elif not link_url.startswith("http"):
                    continue
                if not is_official_domain(link_url):
                    continue
                if is_known_url(link_url):
                    continue
                if any(p in link_url.lower() for p in skip_portal):
                    continue

                keywords = text_has_pcd_keywords(title)
                if keywords:
                    candidates.append({
                        "source": f"Portal {nome}/{uf}",
                        "title": title[:200],
                        "url": link_url,
                        "keywords": keywords[:5],
                        "date_found": today,
                        "type": "service",
                        "nivel": "municipal",
                        "uf": uf,
                        "municipio": nome,
                        "hash": content_hash(link_url + title),
                    })

    # Dedup
    seen: set[str] = set()
    unique = []
    for c in candidates:
        if c["hash"] not in seen:
            seen.add(c["hash"])
            unique.append(c)

    log(f"  Municípios: {len(unique)} candidatos", "OK" if unique else "INFO")
    return unique


# ─── Deduplicação e Classificação ──────────────────────────────────
def deduplicate(candidates: list[dict]) -> list[dict]:
    """Remove duplicatas por hash e URL."""
    seen_hashes: set[str] = set()
    seen_urls: set[str] = set()
    unique = []

    for c in candidates:
        h = c.get("hash", "")
        u = c.get("url", "").rstrip("/")
        if h in seen_hashes or u in seen_urls:
            continue
        seen_hashes.add(h)
        seen_urls.add(u)
        unique.append(c)

    return unique


def classify_priority(candidate: dict) -> str:
    """Classifica prioridade: ALTA, MÉDIA, BAIXA."""
    title_lower = candidate.get("title", "").lower()
    kw_count = len(candidate.get("keywords", []))
    source = candidate.get("source", "")

    # Alta: legislação nova + múltiplas keywords + fonte prioritária
    if candidate.get("type") == "legislation" and kw_count >= 3:
        return "ALTA"
    if any(term in title_lower for term in ["lei", "decreto", "bpc", "loas", "lbi"]):
        return "ALTA"

    # Média: serviços novos ou notícias relevantes
    if source in ("gov.br", "Senado") or kw_count >= 2:
        return "MÉDIA"

    return "BAIXA"


def classify_category(candidate: dict) -> str:
    """Sugere a categoria mais relevante do direitos.json."""
    title_lower = candidate.get("title", "").lower()
    keywords_lower = [kw.lower() for kw in candidate.get("keywords", [])]
    all_text = title_lower + " " + " ".join(keywords_lower)

    mapping = {
        "bpc": ["bpc", "loas", "benefício assistencial", "prestação continuada"],
        "educacao": ["educação", "escola", "prouni", "fies", "enem", "inclusão escolar"],
        "ciptea": ["ciptea", "autismo", "tea", "espectro autista", "romeo mion", "berenice piana"],
        "transporte": ["transporte", "passe livre", "mobilidade", "ônibus", "metrô"],
        "trabalho": ["trabalho", "emprego", "cota", "reserva de vagas", "pcd no trabalho"],
        "sus_terapias": ["sus", "terapia", "saúde", "caps", "cer", "reabilitação"],
        "plano_saude": ["plano de saúde", "ans", "rol de procedimentos", "operadora"],
        "isencoes_tributarias": ["isenção", "ipi", "icms", "iof", "ipva", "tribut"],
        "moradia": ["moradia", "minha casa", "habitação", "acessibilidade residencial"],
        "fgts": ["fgts", "saque", "fundo de garantia"],
        "tecnologia_assistiva": ["tecnologia assistiva", "órtese", "prótese", "cadeira de rodas"],
        "aposentadoria_especial_pcd": ["aposentadoria", "previdência", "inss"],
        "isencao_ir": ["imposto de renda", "ir", "isenção ir"],
        "atendimento_prioritario": ["atendimento prioritário", "prioridade", "fila"],
        "meia_entrada": ["meia-entrada", "meia entrada", "cultura", "lazer"],
        "tarifa_social_energia": ["tarifa social", "energia", "luz"],
        "auxilio_inclusao": ["auxílio-inclusão", "auxílio inclusão"],
        "estacionamento_especial": ["estacionamento", "vaga especial"],
    }

    for cat_id, terms in mapping.items():
        if any(term in all_text for term in terms):
            return cat_id

    return "nova_categoria"


# ─── Geração de Relatórios ─────────────────────────────────────────
def generate_report(candidates: list[dict], existing_data: dict, since_days: int) -> dict:
    """Gera relatório estruturado com candidatos classificados."""
    report = {
        "generated_at": datetime.now().isoformat(),
        "search_window_days": since_days,
        "existing_categories": len(existing_data.get("categorias", [])),
        "existing_sources": len(existing_data.get("fontes", [])),
        "existing_urls": len(KNOWN_URLS),
        "candidates_found": len(candidates),
        "candidates_by_priority": {"ALTA": 0, "MÉDIA": 0, "BAIXA": 0},
        "candidates_by_source": {},
        "candidates_by_type": {},
        "candidates": [],
    }

    for c in candidates:
        priority = classify_priority(c)
        category = classify_category(c)
        c["priority"] = priority
        c["suggested_category"] = category

        report["candidates_by_priority"][priority] = report["candidates_by_priority"].get(priority, 0) + 1
        report["candidates_by_source"][c["source"]] = report["candidates_by_source"].get(c["source"], 0) + 1
        report["candidates_by_type"][c["type"]] = report["candidates_by_type"].get(c["type"], 0) + 1
        report["candidates"].append(c)

    # Ordena: ALTA primeiro, depois MÉDIA, depois BAIXA
    priority_order = {"ALTA": 0, "MÉDIA": 1, "BAIXA": 2}
    report["candidates"].sort(key=lambda c: priority_order.get(c.get("priority", "BAIXA"), 3))

    return report


def generate_markdown(report: dict) -> str:
    """Gera relatório Markdown legível."""
    lines = [
        f"# 🔍 NossoDireito — Relatório de Descoberta de Novos Benefícios",
        f"",
        f"**Gerado em:** {report['generated_at'][:19]}",
        f"**Janela de busca:** últimos {report['search_window_days']} dias",
        f"**Categorias existentes:** {report['existing_categories']}",
        f"**Fontes existentes:** {report['existing_sources']}",
        f"**Candidatos encontrados:** {report['candidates_found']}",
        f"",
    ]

    if not report["candidates"]:
        lines.append("✅ Nenhum benefício novo detectado. Base de dados está atualizada!")
        lines.append("")
        lines.append("*Nota: Isso não garante que não existam novos benefícios. A verificação")
        lines.append("manual periódica continua necessária conforme GOVERNANCE.md.*")
        return "\n".join(lines)

    # Resumo por prioridade
    lines.append("## 📊 Resumo")
    lines.append("")
    lines.append("| Prioridade | Quantidade |")
    lines.append("|------------|------------|")
    for p in ["ALTA", "MÉDIA", "BAIXA"]:
        count = report["candidates_by_priority"].get(p, 0)
        icon = "🔴" if p == "ALTA" else "🟡" if p == "MÉDIA" else "🟢"
        lines.append(f"| {icon} {p} | {count} |")
    lines.append("")

    # Resumo por fonte
    lines.append("| Fonte | Candidatos |")
    lines.append("|-------|------------|")
    for src, count in sorted(report["candidates_by_source"].items()):
        lines.append(f"| {src} | {count} |")
    lines.append("")

    # Detalhes dos candidatos
    lines.append("## 🆕 Candidatos para Revisão")
    lines.append("")

    current_priority = None
    for i, c in enumerate(report["candidates"], 1):
        if c["priority"] != current_priority:
            current_priority = c["priority"]
            icon = "🔴" if current_priority == "ALTA" else "🟡" if current_priority == "MÉDIA" else "🟢"
            lines.append(f"### {icon} Prioridade {current_priority}")
            lines.append("")

        lines.append(f"**{i}. {c['title']}**")
        lines.append(f"- **Fonte:** {c['source']}")
        lines.append(f"- **Tipo:** {c['type']}")
        lines.append(f"- **URL:** {c['url']}")
        lines.append(f"- **Keywords:** {', '.join(c['keywords'])}")
        lines.append(f"- **Categoria sugerida:** `{c.get('suggested_category', 'N/A')}`")
        lines.append(f"- **Encontrado em:** {c['date_found']}")
        lines.append("")

    # Ações recomendadas
    lines.extend([
        "## ✅ Ações Recomendadas",
        "",
        "Para cada candidato de prioridade **ALTA**:",
        "1. Verificar se é realmente um novo direito/benefício PcD",
        "2. Validar a fonte oficial (planalto.gov.br, gov.br)",
        "3. Adicionar a `data/direitos.json` seguindo o schema",
        "4. Executar `python scripts/validate_all.py` para validar",
        "5. Atualizar `ultima_atualizacao` em `direitos.json`",
        "",
        "---",
        "*Relatório gerado automaticamente por `scripts/discover_benefits.py`.*",
        "*Consulte GOVERNANCE.md para critérios de adição de novas categorias.*",
    ])

    return "\n".join(lines)


def generate_github_issue_body(report: dict) -> str:
    """Gera corpo de issue GitHub para revisão."""
    md = generate_markdown(report)

    # Adiciona checklist interativo para issues
    candidates = report.get("candidates", [])
    if candidates:
        checklist = ["\n## Checklist de Revisão\n"]
        for i, c in enumerate(candidates, 1):
            icon = "🔴" if c["priority"] == "ALTA" else "🟡" if c["priority"] == "MÉDIA" else "🟢"
            checklist.append(f"- [ ] {icon} **{c['title'][:80]}** ({c['source']})")
        md += "\n" + "\n".join(checklist)

    return md


# ─── Merge com relatório anterior ─────────────────────────────────
def merge_with_previous(report: dict) -> dict:
    """
    Combina novos candidatos com relatório anterior, evitando
    re-reportar itens já analisados.
    """
    if not REPORT_JSON.exists():
        return report

    try:
        with open(REPORT_JSON, "r", encoding="utf-8") as f:
            previous = json.load(f)
    except (json.JSONDecodeError, OSError):
        return report

    # Hashes já reportados anteriormente
    previous_hashes = {c.get("hash") for c in previous.get("candidates", [])}

    # Filtra apenas candidatos realmente novos
    new_candidates = [
        c for c in report["candidates"]
        if c.get("hash") not in previous_hashes
    ]

    if len(new_candidates) < len(report["candidates"]):
        removed = len(report["candidates"]) - len(new_candidates)
        log(f"  {removed} candidatos já reportados anteriormente (filtrados)", "SKIP")

    report["candidates"] = new_candidates
    report["candidates_found"] = len(new_candidates)

    # Recalcula contadores
    report["candidates_by_priority"] = {"ALTA": 0, "MÉDIA": 0, "BAIXA": 0}
    report["candidates_by_source"] = {}
    report["candidates_by_type"] = {}
    for c in new_candidates:
        p = c.get("priority", "BAIXA")
        report["candidates_by_priority"][p] = report["candidates_by_priority"].get(p, 0) + 1
        src = c.get("source", "?")
        report["candidates_by_source"][src] = report["candidates_by_source"].get(src, 0) + 1
        t = c.get("type", "?")
        report["candidates_by_type"][t] = report["candidates_by_type"].get(t, 0) + 1

    return report


# ─── Main ──────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Descoberta automática de novos benefícios PcD"
    )
    parser.add_argument("--since", type=int, default=60,
                        help="Buscar nos últimos N dias (padrão: 60)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Apenas mostra o que faria, sem salvar")
    parser.add_argument("--json", action="store_true",
                        help="Saída apenas em JSON (para CI)")
    parser.add_argument("--no-merge", action="store_true",
                        help="Não mesclar com relatório anterior")
    parser.add_argument("--nivel", choices=["federal", "estadual", "municipal", "todos"],
                        default="todos",
                        help="Nível de busca (padrão: todos)")
    parser.add_argument("--estado", nargs="*", metavar="UF",
                        help="Filtrar UF(s): --estado SP RJ MG")
    parser.add_argument("--cidade", nargs="*", metavar="SLUG",
                        help="Filtrar municípios: --cidade barueri-sp")
    args = parser.parse_args()

    # When --json, redirect progress output to stderr so stdout is clean JSON
    _original_stdout = sys.stdout
    if args.json:
        sys.stdout = sys.stderr

    print("=" * 70)
    print("🔍 NOSSODIREITO — DESCOBERTA AUTOMÁTICA DE BENEFÍCIOS PcD")
    print("=" * 70)
    print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📆 Janela de busca: últimos {args.since} dias")
    print(f"🌎 Nível: {args.nivel.upper()}")
    print(f"📖 Dicionário PcD: {'carregado' if DICT_FILE.exists() else 'não encontrado'} ({len(PCD_KEYWORDS)} keywords, {len(SEARCH_QUERIES)} queries)")
    if args.estado:
        print(f"  UFs: {', '.join(args.estado)}")
    if args.cidade:
        print(f"  Cidades: {', '.join(args.cidade)}")
    print()

    # 1. Carregar dados atuais
    log("Carregando dados existentes de direitos.json...")
    existing_data = load_existing_data()
    log(f"  {len(KNOWN_IDS)} categorias, {len(KNOWN_URLS)} URLs, {len(KNOWN_LAWS)} leis conhecidas", "OK")
    print()

    # 2. Consultar todas as fontes
    all_candidates = []
    sources = []

    # Nível federal (5 fontes)
    if args.nivel in ("federal", "todos"):
        sources.extend([
            ("DOU", lambda: search_dou(args.since)),
            ("Senado", lambda: search_senado(args.since)),
            ("gov.br Serviços", search_govbr_services),
            ("gov.br Notícias", search_govbr_news),
            ("LexML", lambda: search_lexml(args.since)),
        ])

    # Nível estadual (27 UFs)
    if args.nivel in ("estadual", "todos"):
        filtro_uf = [u.upper() for u in args.estado] if args.estado else None
        sources.append(("Estados", lambda fu=filtro_uf: search_estados(args.since, fu)))

    # Nível municipal (cidades configuradas)
    if args.nivel in ("municipal", "todos"):
        filtro_cidades = args.cidade if args.cidade else None
        sources.append(("Municípios", lambda fc=filtro_cidades: search_municipios(args.since, fc)))

    for name, search_fn in sources:
        try:
            results = search_fn()
            all_candidates.extend(results)
        except Exception as e:
            log(f"Erro na fonte {name}: {e}", "ERR")
        print()

    # Normalizar nível para candidatos federais existentes
    for c in all_candidates:
        if "nivel" not in c:
            c["nivel"] = "federal"

    # 3. Deduplicar
    unique = deduplicate(all_candidates)
    if len(unique) < len(all_candidates):
        log(f"Deduplicação: {len(all_candidates)} → {len(unique)} candidatos", "INFO")

    # 3b. Validar domínios oficiais
    validated = [c for c in unique if is_official_domain(c.get("url", ""))]
    if len(validated) < len(unique):
        removed = len(unique) - len(validated)
        log(f"Validação: {removed} URLs de fontes não-oficiais removidas", "WARN")
    unique = validated

    # 4. Gerar relatório
    report = generate_report(unique, existing_data, args.since)

    # 5. Merge com relatório anterior
    if not args.no_merge:
        report = merge_with_previous(report)

    # 6. Saída
    print("=" * 70)
    print("📊 RESULTADOS DA DESCOBERTA")
    print("=" * 70)
    print()

    if args.json:
        sys.stdout = _original_stdout
        print(json.dumps(report, ensure_ascii=False, indent=2))
        sys.stdout = sys.stderr
    else:
        md = generate_markdown(report)
        print(md)

    # 7. Salvar relatórios
    if not args.dry_run:
        REPORT_DIR.mkdir(exist_ok=True)

        with open(REPORT_JSON, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        log(f"Relatório JSON salvo: {REPORT_JSON.relative_to(ROOT)}", "OK")

        with open(REPORT_MD, "w", encoding="utf-8") as f:
            f.write(generate_markdown(report))
        log(f"Relatório MD salvo: {REPORT_MD.relative_to(ROOT)}", "OK")
    else:
        log("Modo dry-run — relatórios não salvos", "WARN")

    print()
    total = report["candidates_found"]
    alta = report["candidates_by_priority"].get("ALTA", 0)
    if total == 0:
        log("Nenhum benefício novo detectado. Base atualizada! ✅", "OK")
        return 0
    else:
        log(f"{total} candidatos encontrados ({alta} prioridade ALTA)", "NEW")
        return 1 if alta > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
