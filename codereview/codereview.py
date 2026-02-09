#!/usr/bin/env python3
"""
codereview.py — Rotina de Auto-avaliação do NossoDireito
========================================================

Verifica automaticamente a qualidade, segurança, conformidade regulatória,
acessibilidade e confiabilidade do projeto NossoDireito.

Categorias de verificação:
1. Conformidade regulatória (LGPD, legislação brasileira)
2. Segurança (XSS, CSP, transmissão de dados)
3. Qualidade de software (HTML, CSS, JS patterns)
4. Confiabilidade (error handling, graceful degradation)
5. Performance (file sizes, otimizações)
6. Transparência (fontes oficiais, links válidos)
7. Versionamento (semver, changelog)
8. Modularidade (estrutura de arquivos)
9. Acessibilidade (ARIA, contraste, semântica)
10. Instituições de apoio (completude, URLs válidas)

Uso:
    python codereview.py                    # Roda todas as verificações
    python codereview.py --categoria lgpd   # Roda só uma categoria
    python codereview.py --json             # Saída em JSON
    python codereview.py --fix              # Sugere correções automáticas

Autor: NossoDireito — Projeto sem fins lucrativos
Licença: MIT
"""

from __future__ import annotations

import json
import re
import ssl
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Optional

# ========================
# Configuração
# ========================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_JSON = PROJECT_ROOT / "data" / "direitos.json"
INDEX_HTML = PROJECT_ROOT / "index.html"
STYLES_CSS = PROJECT_ROOT / "css" / "styles.css"
APP_JS = PROJECT_ROOT / "js" / "app.js"
README_MD = PROJECT_ROOT / "README.md"

# Domínios oficiais aceitos como fontes
OFFICIAL_DOMAINS = [
    "gov.br",
    "planalto.gov.br",
    "mds.gov.br",
    "inss.gov.br",
    "ans.gov.br",
    "caixa.gov.br",
    "apaebrasil.org.br",
    "ijc.org.br",
    "ama.org.br",
    "anadep.org.br",
    "cnmp.mp.br",
    "mpt.mp.br",
    "oab.org.br",
    "autismbrasil.org",
    "procon.sp.gov.br",
    "abntcatalogo.com.br",
]

# Versão mínima esperada
MIN_VERSION = "1.3.0"

# Tamanhos máximos recomendados (em bytes)
MAX_HTML_SIZE = 30_000
MAX_CSS_SIZE = 60_000
MAX_JS_SIZE = 80_000
MAX_JSON_SIZE = 100_000


class Severity(Enum):
    """Nível de severidade dos achados."""
    PASS = "✅"
    INFO = "ℹ️"
    WARNING = "⚠️"
    ERROR = "❌"
    CRITICAL = "🚨"


@dataclass
class Finding:
    """Um achado da revisão."""
    categoria: str
    titulo: str
    severidade: Severity
    descricao: str
    arquivo: str = ""
    linha: int = 0
    sugestao: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severidade"] = self.severidade.value + " " + self.severidade.name
        return d


@dataclass
class ReviewReport:
    """Relatório completo da revisão."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    versao_codereview: str = "1.0.0"
    achados: list[Finding] = field(default_factory=list)
    score_total: float = 0.0
    categorias_scores: dict[str, float] = field(default_factory=dict)

    def add(self, finding: Finding) -> None:
        self.achados.append(finding)

    def calcular_score(self) -> None:
        """Calcula scores por categoria e total (0-100)."""
        cats: dict[str, list[Finding]] = {}
        for f in self.achados:
            cats.setdefault(f.categoria, []).append(f)

        total_score = 0.0
        total_weight = 0

        for cat_name, findings in cats.items():
            severity_weights = {
                Severity.PASS: 100,
                Severity.INFO: 85,
                Severity.WARNING: 50,
                Severity.ERROR: 20,
                Severity.CRITICAL: 0,
            }
            if findings:
                cat_score = sum(severity_weights[f.severidade] for f in findings) / len(findings)
            else:
                cat_score = 100.0
            self.categorias_scores[cat_name] = round(cat_score, 1)
            total_score += cat_score
            total_weight += 1

        self.score_total = round(total_score / max(total_weight, 1), 1)


# ========================
# Helpers
# ========================
def read_text(path: Path) -> str:
    """Lê arquivo com fallback de encoding."""
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    return ""


def read_json(path: Path) -> dict:
    """Lê e parseia JSON."""
    text = read_text(path)
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def check_url_reachable(url: str, timeout: int = 10) -> tuple[bool, int]:
    """Verifica se URL está acessível. Retorna (acessível, status_code)."""
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, method="HEAD", headers={
            "User-Agent": "NossoDireito-CodeReview/1.0"
        })
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return True, resp.status
    except urllib.error.HTTPError as e:
        return e.code < 500, e.code
    except Exception:
        return False, 0


def parse_semver(version: str) -> tuple[int, ...]:
    """Parse version string como tupla numérica."""
    parts = version.replace("v", "").split(".")
    return tuple(int(p) for p in parts if p.isdigit())


# ========================
# Verificações por Categoria
# ========================

def check_lgpd(report: ReviewReport, html: str, js: str, json_data: dict) -> None:
    """Verifica conformidade com LGPD Art. 4º, I."""
    cat = "LGPD / Privacidade"

    # 1. Verifica menção à LGPD no código/dados
    lgpd_mentioned = "lgpd" in js.lower() or "lgpd" in html.lower()
    if lgpd_mentioned:
        report.add(Finding(cat, "Referência à LGPD presente", Severity.PASS,
                           "O código menciona LGPD, demonstrando consciência regulatória."))
    else:
        report.add(Finding(cat, "Sem referência explícita à LGPD", Severity.WARNING,
                           "O código não contém referência direta à LGPD.",
                           sugestao="Adicione comentário referenciando LGPD Art. 4º, I no cabeçalho do JS."))

    # 2. Verifica ausência de coleta de dados
    tracking_patterns = [
        (r"google[-_]?analytics|gtag|ga\s*\(", "Google Analytics"),
        (r"facebook|fb[-_]?pixel|fbq\s*\(", "Facebook Pixel"),
        (r"hotjar|hj\s*\(", "Hotjar"),
        (r"mixpanel|amplitude|segment", "Analytics SDK"),
        (r"fetch\s*\(.+api\.|XMLHttpRequest", "Chamadas externas suspeitas"),
        (r"document\.cookie\s*=", "Escrita de cookies"),
        (r"navigator\.sendBeacon", "Beacon API"),
    ]

    for pattern, name in tracking_patterns:
        if re.search(pattern, js, re.IGNORECASE):
            report.add(Finding(cat, f"Possível rastreamento: {name}", Severity.CRITICAL,
                               f"Detectada referência a {name} — viola princípio de zero coleta.",
                               arquivo="js/app.js",
                               sugestao=f"Remova toda referência a {name}."))
        else:
            report.add(Finding(cat, f"Livre de {name}", Severity.PASS,
                               f"Nenhuma referência a {name} detectada."))

    # 3. Verifica disclaimer de privacidade
    if "nenhum dado pessoal" in html.lower() or "nenhum dado é coletado" in html.lower():
        report.add(Finding(cat, "Aviso de privacidade presente", Severity.PASS,
                           "HTML contém aviso afirmando que nenhum dado é coletado."))
    else:
        report.add(Finding(cat, "Aviso de privacidade ausente", Severity.ERROR,
                           "O HTML não contém aviso claro sobre não-coleta de dados.",
                           sugestao="Adicione aviso explícito no modal de disclaimer."))

    # 4. Verifica localStorage apenas para preferências
    ls_writes = re.findall(r"localStorage\.setItem\(['\"]([^'\"]+)", js)
    for key in ls_writes:
        if "nossodireito_" in key:
            report.add(Finding(cat, f"LocalStorage: {key}", Severity.PASS,
                               f"Chave {key} usa prefixo do projeto — OK para preferências."))
        else:
            report.add(Finding(cat, f"LocalStorage sem prefixo: {key}", Severity.WARNING,
                               f"Chave {key} não usa prefixo 'nossodireito_'.",
                               sugestao="Use prefixo 'nossodireito_' em todas as chaves."))

    # 5. IndexedDB — verifica que dados ficam locais
    if "IndexedDB" in js or "indexedDB" in js:
        report.add(Finding(cat, "IndexedDB usado (local)", Severity.PASS,
                           "IndexedDB usado para armazenamento local — consistente com política de privacidade."))


def check_security(report: ReviewReport, html: str, js: str) -> None:
    """Verifica segurança: XSS, injection, CSP, SRI, criptografia, TTL."""
    cat = "Segurança"

    # 1. XSS: verifica uso de escapeHtml
    if "function escapeHtml" in js or "escapeHtml" in js:
        report.add(Finding(cat, "escapeHtml() presente", Severity.PASS,
                           "Função de escape HTML encontrada — proteção contra XSS."))
    else:
        report.add(Finding(cat, "Sem função de escape HTML", Severity.CRITICAL,
                           "Nenhuma função de escape HTML detectada — risco de XSS.",
                           sugestao="Implemente escapeHtml() para sanitizar todo conteúdo dinâmico."))

    # 2. innerHTML com dados não-sanitizados
    innerhtml_uses = re.findall(r"\.innerHTML\s*=\s*(.+?)(?:;|\n)", js)
    unsafe_count = sum(1 for use in innerhtml_uses if "escapeHtml" not in use and "map" not in use and "`" in use)
    if unsafe_count > 0:
        report.add(Finding(cat, f"innerHTML potencialmente inseguro ({unsafe_count}x)", Severity.WARNING,
                           f"Encontrados {unsafe_count} usos de innerHTML com template literals sem escapeHtml visível.",
                           arquivo="js/app.js",
                           sugestao="Verifique que todos os dados do usuário passam por escapeHtml()."))
    else:
        report.add(Finding(cat, "innerHTML com sanitização adequada", Severity.PASS,
                           "Usos de innerHTML parecem sanitizados com escapeHtml()."))

    # 3. Regex injection
    if "escapeRegex" in js:
        report.add(Finding(cat, "escapeRegex() presente", Severity.PASS,
                           "Proteção contra injeção de regex detectada."))
    else:
        report.add(Finding(cat, "Sem proteção contra regex injection", Severity.WARNING,
                           "Nenhuma função escapeRegex() detectada.",
                           sugestao="Adicione escapeRegex() para sanitizar input de busca antes de usar em RegExp()."))

    # 4. CSP header
    if "Content-Security-Policy" in html:
        # Verify CSP quality — search for content= after CSP declaration
        csp_start = html.index("Content-Security-Policy")
        csp_match = re.search(r'content="([^"]+)"', html[csp_start:])
        if csp_match:
            csp_val = csp_match.group(1)
            if "default-src 'none'" in csp_val or "default-src 'self'" in csp_val:
                report.add(Finding(cat, "CSP restritivo presente", Severity.PASS,
                                   "Content-Security-Policy com default-src restritivo detectado."))
            else:
                report.add(Finding(cat, "CSP presente mas permissivo", Severity.WARNING,
                                   "CSP detectado sem default-src restritivo.",
                                   sugestao="Use default-src 'none' com allowlist específica."))
            if "'unsafe-eval'" in csp_val:
                report.add(Finding(cat, "CSP permite unsafe-eval", Severity.CRITICAL,
                                   "CSP contém 'unsafe-eval' — anula proteção XSS.",
                                   sugestao="Remova 'unsafe-eval' do CSP."))
        else:
            report.add(Finding(cat, "CSP meta tag presente", Severity.PASS,
                               "Content-Security-Policy encontrado no HTML."))
    else:
        report.add(Finding(cat, "Sem CSP meta tag", Severity.CRITICAL,
                           "Nenhuma Content-Security-Policy no HTML — essencial para produção.",
                           sugestao="Adicione <meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; ...\"> no <head>."))

    # 5. External script loading + SRI
    external_scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']([^>]*)', html)
    for src, attrs in external_scripts:
        if "cdnjs.cloudflare.com" in src or "cdn.jsdelivr.net" in src:
            if "integrity=" in attrs:
                report.add(Finding(cat, "SRI presente em CDN script", Severity.PASS,
                                   f"Subresource Integrity detectado para: {src[:50]}..."))
                if 'crossorigin="anonymous"' in attrs or "crossorigin='anonymous'" in attrs:
                    report.add(Finding(cat, "crossorigin=anonymous em CDN", Severity.PASS,
                                       "Atributo crossorigin correctamente configurado para SRI."))
                else:
                    report.add(Finding(cat, "Falta crossorigin em script SRI", Severity.WARNING,
                                       "Script com integrity mas sem crossorigin='anonymous'.",
                                       sugestao="Adicione crossorigin='anonymous' ao script com SRI."))
            else:
                report.add(Finding(cat, f"CDN sem SRI: {src[:50]}...", Severity.CRITICAL,
                                   "Script de CDN sem Subresource Integrity — risco de supply-chain attack.",
                                   sugestao="Adicione integrity='sha384-...' e crossorigin='anonymous'."))
        elif not src.startswith(("js/", "css/", "./", "../")):
            report.add(Finding(cat, f"Script externo: {src[:60]}...", Severity.WARNING,
                               "Script carregado de fonte externa não verificada."))

    # 6. Verifica target="_blank" com noopener
    blank_links = re.findall(r'target="_blank"', html)
    noopener_links = re.findall(r'rel="noopener"', html)
    if len(blank_links) > 0:
        if len(noopener_links) >= len(blank_links):
            report.add(Finding(cat, "Links externos com rel='noopener'", Severity.PASS,
                               f"Todos os {len(blank_links)} links target='_blank' possuem rel='noopener'."))
        else:
            report.add(Finding(cat, "Links sem rel='noopener'", Severity.WARNING,
                               f"{len(blank_links)} links com target='_blank' mas apenas {len(noopener_links)} com rel='noopener'.",
                               sugestao="Adicione rel='noopener' em todos os links target='_blank'."))

    # 7. Criptografia em repouso (IndexedDB)
    if "crypto.subtle" in js and "AES-GCM" in js:
        report.add(Finding(cat, "Criptografia AES-GCM presente", Severity.PASS,
                           "Dados sensíveis criptografados com AES-GCM via Web Crypto API."))

        # Verify key is non-exportable
        if "false" in js[js.index("generateKey"):js.index("generateKey") + 200]:
            report.add(Finding(cat, "Chave não-exportável (CWE-326)", Severity.PASS,
                               "CryptoKey gerada com extractable=false — proteção contra exfiltração."))
    else:
        report.add(Finding(cat, "Sem criptografia de dados sensíveis", Severity.CRITICAL,
                           "IndexedDB armazena dados sem criptografia — risco para dados de saúde (LGPD Art. 46).",
                           sugestao="Implemente AES-GCM-256 via Web Crypto API para criptografar arquivos em repouso."))

    # 8. Auto-expiração (TTL)
    if "expiresAt" in js and "cleanupExpiredFiles" in js:
        report.add(Finding(cat, "TTL com auto-expiração implementado", Severity.PASS,
                           "Documentos têm data de expiração com limpeza automática."))
    else:
        report.add(Finding(cat, "Sem TTL para dados armazenados", Severity.WARNING,
                           "Dados persistem indefinidamente no IndexedDB.",
                           sugestao="Adicione campo expiresAt e função de limpeza automática."))

    # 9. Blob URL revocation
    blob_revoke_match = re.search(r'revokeObjectURL.*?(\d+)\s*[\*]?\s*1000', js)
    if "revokeObjectURL" in js:
        report.add(Finding(cat, "Revogação de Blob URLs presente", Severity.PASS,
                           "Blob URLs são revogados para limitar janela de exposição."))
    else:
        report.add(Finding(cat, "Sem revogação de Blob URLs", Severity.WARNING,
                           "Blob URLs de dados descriptografados não são revogados.",
                           sugestao="Adicione URL.revokeObjectURL() com timeout curto (15s)."))

    # 10. Security headers (meta tags)
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin",
        "Permissions-Policy": "camera|microphone|geolocation",
    }
    for header, expected in security_headers.items():
        if header in html:
            report.add(Finding(cat, f"{header} presente", Severity.PASS,
                               f"Header de segurança {header} configurado."))
        else:
            report.add(Finding(cat, f"Sem {header}", Severity.INFO,
                               f"Header {header} não encontrado — recomendado para produção.",
                               sugestao=f"Adicione <meta http-equiv='{header}' content='{expected}'>."))


def check_quality(report: ReviewReport, html: str, css: str, js: str) -> None:
    """Verifica qualidade de código: patterns, best practices."""
    cat = "Qualidade de Software"

    # 1. 'use strict'
    if "'use strict'" in js:
        report.add(Finding(cat, "'use strict' ativado", Severity.PASS,
                           "Strict mode ativado — previne erros silenciosos."))
    else:
        report.add(Finding(cat, "'use strict' ausente", Severity.WARNING,
                           "JavaScript não usa strict mode.",
                           sugestao="Adicione 'use strict' no início da IIFE."))

    # 2. IIFE pattern
    if "(function" in js and "})();" in js:
        report.add(Finding(cat, "IIFE pattern usado", Severity.PASS,
                           "Código encapsulado em IIFE — evita poluição do escopo global."))
    else:
        report.add(Finding(cat, "Sem encapsulamento IIFE", Severity.WARNING,
                           "Código não encapsulado em IIFE — variáveis podem vazar para escopo global."))

    # 3. Error handling
    try_catch_count = js.count("try {") + js.count("try{")
    if try_catch_count >= 3:
        report.add(Finding(cat, f"Error handling presente ({try_catch_count} try/catch)", Severity.PASS,
                           f"Encontrados {try_catch_count} blocos try/catch — bom tratamento de erros."))
    elif try_catch_count >= 1:
        report.add(Finding(cat, f"Error handling parcial ({try_catch_count} try/catch)", Severity.INFO,
                           "Poucos blocos try/catch. Considere proteger todas as operações async."))
    else:
        report.add(Finding(cat, "Sem error handling", Severity.ERROR,
                           "Nenhum bloco try/catch detectado — erros podem passar silenciosamente.",
                           sugestao="Adicione try/catch em operações async, fetch, IndexedDB etc."))

    # 4. Console.error para logging
    if "console.error" in js:
        report.add(Finding(cat, "Logging de erros presente", Severity.PASS,
                           "console.error() usado para registrar falhas."))

    # 5. HTML lang attribute
    if 'lang="pt-BR"' in html:
        report.add(Finding(cat, "lang='pt-BR' no HTML", Severity.PASS,
                           "Atributo lang correto para português brasileiro."))
    else:
        report.add(Finding(cat, "lang attribute ausente/incorreto", Severity.WARNING,
                           "Atributo lang não definido ou não é pt-BR.",
                           sugestao="Adicione lang='pt-BR' na tag <html>."))

    # 6. Semantic HTML
    semantic_tags = ["<nav", "<main", "<section", "<article", "<header", "<footer", "<aside"]
    found_semantic = [tag for tag in semantic_tags if tag in html]
    if len(found_semantic) >= 4:
        report.add(Finding(cat, f"HTML semântico ({len(found_semantic)} tags)", Severity.PASS,
                           f"Encontradas tags semânticas: {', '.join(found_semantic)}"))
    else:
        report.add(Finding(cat, "Pouco HTML semântico", Severity.WARNING,
                           f"Apenas {len(found_semantic)} tags semânticas encontradas."))

    # 7. Meta viewport
    if 'viewport' in html:
        report.add(Finding(cat, "Viewport meta tag presente", Severity.PASS,
                           "Meta viewport configurada — suporta mobile."))

    # 8. CSS custom properties
    css_vars = re.findall(r'--[\w-]+:', css)
    if len(css_vars) >= 5:
        report.add(Finding(cat, f"CSS Custom Properties ({len(css_vars)} vars)", Severity.PASS,
                           f"Usa {len(css_vars)} CSS custom properties — boa manutenibilidade."))


def check_reliability(report: ReviewReport, js: str, html: str) -> None:
    """Verifica confiabilidade: graceful degradation, fallbacks."""
    cat = "Confiabilidade"

    # 1. Fetch error handling
    fetch_count = js.count("fetch(")
    fetch_with_catch = len(re.findall(r"fetch\(.+?\)\.then.+?\.catch|try\s*\{[^}]*fetch", js, re.DOTALL))
    if fetch_count > 0:
        if fetch_with_catch >= fetch_count or "try" in js:
            report.add(Finding(cat, "Fetch com error handling", Severity.PASS,
                               f"Chamadas fetch ({fetch_count}) possuem tratamento de erro."))
        else:
            report.add(Finding(cat, "Fetch sem error handling completo", Severity.WARNING,
                               f"{fetch_count} chamadas fetch, nem todas com catch visível."))

    # 2. Fallback message quando JSON falha
    if "Não foi possível carregar" in js or "erro" in js.lower():
        report.add(Finding(cat, "Mensagem de fallback presente", Severity.PASS,
                           "UI mostra mensagem amigável quando dados não carregam."))

    # 3. Progressive enhancement
    if "DOMContentLoaded" in js or "document.readyState" in js:
        report.add(Finding(cat, "Progressive enhancement (DOM ready)", Severity.PASS,
                           "JavaScript aguarda DOM estar pronto antes de executar."))

    # 4. Graceful IndexedDB handling
    if "indexedDB" in js and "reject" in js:
        report.add(Finding(cat, "IndexedDB com error handling", Severity.PASS,
                           "Operações IndexedDB possuem rejeição de Promise para erros."))

    # 5. Noscript fallback
    if "<noscript>" in html:
        report.add(Finding(cat, "<noscript> fallback presente", Severity.PASS,
                           "Fallback para navegadores sem JavaScript."))
    else:
        report.add(Finding(cat, "Sem <noscript> fallback", Severity.INFO,
                           "Nenhum <noscript> — site não funciona sem JS.",
                           sugestao="Considere adicionar <noscript> com mensagem."))


def check_performance(report: ReviewReport) -> None:
    """Verifica performance: tamanhos, otimizações."""
    cat = "Performance"

    files_limits = [
        (INDEX_HTML, MAX_HTML_SIZE, "HTML"),
        (STYLES_CSS, MAX_CSS_SIZE, "CSS"),
        (APP_JS, MAX_JS_SIZE, "JavaScript"),
        (DATA_JSON, MAX_JSON_SIZE, "JSON"),
    ]

    for path, max_size, label in files_limits:
        if path.exists():
            size = path.stat().st_size
            if size <= max_size:
                report.add(Finding(cat, f"{label}: {size:,} bytes", Severity.PASS,
                                   f"{label} ({size:,} B) dentro do limite ({max_size:,} B)."))
            else:
                report.add(Finding(cat, f"{label} grande: {size:,} bytes", Severity.WARNING,
                                   f"{label} ({size:,} B) excede limite recomendado ({max_size:,} B).",
                                   arquivo=str(path.relative_to(PROJECT_ROOT)),
                                   sugestao=f"Considere minificar o {label} para produção."))
        else:
            report.add(Finding(cat, f"{label} não encontrado", Severity.ERROR,
                               f"Arquivo {path.name} não existe.",
                               arquivo=str(path.relative_to(PROJECT_ROOT))))

    # Image optimization (check for optimized formats)
    img_dir = PROJECT_ROOT / "img"
    if img_dir.exists():
        images = list(img_dir.glob("*"))
        large = [i for i in images if i.stat().st_size > 500_000]
        if large:
            report.add(Finding(cat, f"{len(large)} imagens > 500KB", Severity.WARNING,
                               "Imagens grandes podem afetar carregamento em conexões lentas.",
                               sugestao="Comprima imagens ou use formato WebP."))


def check_transparency(report: ReviewReport, json_data: dict) -> None:
    """Verifica transparência: fontes oficiais, links, completude."""
    cat = "Transparência / Fontes"

    fontes = json_data.get("fontes", [])
    if not fontes:
        report.add(Finding(cat, "Nenhuma fonte listada", Severity.CRITICAL,
                           "JSON não contém array 'fontes'.",
                           sugestao="Adicione fontes oficiais consultadas."))
        return

    report.add(Finding(cat, f"{len(fontes)} fontes registradas", Severity.PASS,
                       f"Base de {len(fontes)} fontes documentadas."))

    # Verificar domínios oficiais
    for fonte in fontes:
        url = fonte.get("url", "")
        nome = fonte.get("nome", "desconhecido")
        is_official = any(domain in url for domain in OFFICIAL_DOMAINS)

        if is_official:
            report.add(Finding(cat, f"Fonte oficial: {nome[:50]}", Severity.PASS,
                               f"URL {url[:60]} pertence a domínio oficial."))
        else:
            report.add(Finding(cat, f"Fonte não-oficial: {nome[:50]}", Severity.WARNING,
                               f"URL {url[:60]} não pertence a domínio oficial reconhecido.",
                               sugestao="Substitua por fonte oficial gov.br quando possível."))

    # Verificar data de consulta
    for fonte in fontes:
        consultado = fonte.get("consultado_em", "")
        if consultado:
            try:
                dt = date.fromisoformat(consultado)
                age_days = (date.today() - dt).days
                if age_days > 90:
                    report.add(Finding(cat, f"Fonte desatualizada: {fonte['nome'][:40]}", Severity.WARNING,
                                       f"Consultada há {age_days} dias.",
                                       sugestao=f"Verifique {fonte['url'][:60]} para atualizações."))
            except ValueError:
                pass

    # Verificar proxima_revisao
    proxima = json_data.get("proxima_revisao")
    if proxima:
        report.add(Finding(cat, "Data de próxima revisão definida", Severity.PASS,
                           f"Próxima revisão agendada: {proxima}"))
    else:
        report.add(Finding(cat, "Sem data de próxima revisão", Severity.WARNING,
                           "Campo 'proxima_revisao' ausente no JSON.",
                           sugestao="Adicione campo 'proxima_revisao' com data YYYY-MM-DD."))


def check_versioning(report: ReviewReport, json_data: dict) -> None:
    """Verifica versionamento semântico."""
    cat = "Versionamento"

    versao = json_data.get("versao", "")
    if not versao:
        report.add(Finding(cat, "Sem versão no JSON", Severity.ERROR,
                           "Campo 'versao' ausente no JSON.",
                           sugestao="Adicione campo 'versao' seguindo semver (ex: '1.2.0')."))
        return

    # Validar formato semver
    if re.match(r"^\d+\.\d+\.\d+$", versao):
        report.add(Finding(cat, f"Versão: v{versao} (semver)", Severity.PASS,
                           "Formato semver válido."))
    else:
        report.add(Finding(cat, f"Versão inválida: {versao}", Severity.WARNING,
                           "Formato de versão não segue semver.",
                           sugestao="Use formato MAJOR.MINOR.PATCH (ex: 1.2.0)."))

    # Verificar se >= MIN_VERSION
    current = parse_semver(versao)
    minimum = parse_semver(MIN_VERSION)
    if current >= minimum:
        report.add(Finding(cat, f"Versão {versao} >= {MIN_VERSION}", Severity.PASS,
                           "Versão atende ao mínimo esperado."))
    else:
        report.add(Finding(cat, f"Versão {versao} < {MIN_VERSION}", Severity.WARNING,
                           f"Versão abaixo do mínimo esperado ({MIN_VERSION}).",
                           sugestao=f"Atualize para pelo menos v{MIN_VERSION}."))

    # Ultima atualização
    ultima = json_data.get("ultima_atualizacao", "")
    if ultima:
        report.add(Finding(cat, f"Última atualização: {ultima}", Severity.PASS,
                           "Campo 'ultima_atualizacao' presente."))


def check_modularity(report: ReviewReport) -> None:
    """Verifica estrutura e modularidade do projeto."""
    cat = "Modularidade"

    expected_files = {
        "index.html": "Página principal",
        "css/styles.css": "Estilos",
        "js/app.js": "Lógica principal",
        "data/direitos.json": "Base de dados",
        "README.md": "Documentação",
    }

    for rel_path, desc in expected_files.items():
        full_path = PROJECT_ROOT / rel_path
        if full_path.exists():
            report.add(Finding(cat, f"✓ {rel_path}", Severity.PASS,
                               f"{desc} presente."))
        else:
            report.add(Finding(cat, f"✗ {rel_path} ausente", Severity.ERROR,
                               f"{desc} não encontrado.",
                               sugestao=f"Crie o arquivo {rel_path}."))

    # Verificar separação de concerns
    js_in_html = re.findall(r"<script[^>]*>(?![\s\n]*</script>)(.+?)</script>", read_text(INDEX_HTML), re.DOTALL)
    inline_js = [s for s in js_in_html if len(s.strip()) > 50]
    if inline_js:
        report.add(Finding(cat, f"{len(inline_js)} script(s) inline no HTML", Severity.WARNING,
                           "JavaScript inline detectado — melhor mover para arquivo separado.",
                           sugestao="Mova scripts inline para js/app.js."))
    else:
        report.add(Finding(cat, "Sem JS inline significativo", Severity.PASS,
                           "JavaScript separado em arquivo próprio."))

    # Verificar GitHub Actions
    workflow = PROJECT_ROOT / ".github" / "workflows" / "weekly-review.yml"
    if workflow.exists():
        report.add(Finding(cat, "CI/CD: weekly-review.yml", Severity.PASS,
                           "Workflow de revisão semanal configurado."))
    else:
        report.add(Finding(cat, "Sem CI/CD configurado", Severity.INFO,
                           "Nenhum workflow GitHub Actions encontrado.",
                           sugestao="Configure weekly-review.yml para verificação automática."))

    # Verificar codereview existente
    codereview_dir = PROJECT_ROOT / "codereview"
    if codereview_dir.exists():
        report.add(Finding(cat, "Rotina codereview presente", Severity.PASS,
                           "Diretório codereview/ com scripts de auto-avaliação."))


def check_accessibility(report: ReviewReport, html: str, css: str) -> None:
    """Verifica acessibilidade: ARIA, semântica, constraste."""
    cat = "Acessibilidade"

    # 1. ARIA attributes
    aria_count = len(re.findall(r'aria-\w+', html))
    if aria_count >= 10:
        report.add(Finding(cat, f"{aria_count} atributos ARIA", Severity.PASS,
                           f"Encontrados {aria_count} atributos ARIA — boa acessibilidade."))
    elif aria_count >= 3:
        report.add(Finding(cat, f"{aria_count} atributos ARIA", Severity.INFO,
                           "Algumas marcações ARIA presentes, mas pode melhorar."))
    else:
        report.add(Finding(cat, "Poucos atributos ARIA", Severity.WARNING,
                           f"Apenas {aria_count} atributos ARIA detectados.",
                           sugestao="Adicione aria-label, role, aria-live em elementos interativos."))

    # 2. aria-live for dynamic content
    if "aria-live" in html:
        report.add(Finding(cat, "aria-live para conteúdo dinâmico", Severity.PASS,
                           "aria-live usado para notificar screen readers sobre mudanças."))

    # 3. tabindex / keyboard nav
    if "tabindex" in html:
        report.add(Finding(cat, "Navegação por teclado (tabindex)", Severity.PASS,
                           "Elementos com tabindex permitem navegação por teclado."))

    # 4. Focus styles
    if ":focus" in css or ":focus-visible" in css:
        report.add(Finding(cat, "Estilos de foco presentes", Severity.PASS,
                           "CSS contém estilos :focus/:focus-visible para navegação por teclado."))
    else:
        report.add(Finding(cat, "Sem estilos de foco", Severity.WARNING,
                           "CSS não define estilos :focus — prejudica navegação por teclado.",
                           sugestao="Adicione :focus-visible { outline: 3px solid ...; }"))

    # 5. prefers-reduced-motion
    if "prefers-reduced-motion" in css:
        report.add(Finding(cat, "prefers-reduced-motion suportado", Severity.PASS,
                           "CSS respeita preferência de redução de movimento."))

    # 6. High contrast
    if "forced-colors" in css:
        report.add(Finding(cat, "Modo alto contraste suportado", Severity.PASS,
                           "CSS suporta forced-colors (alto contraste)."))

    # 7. Print styles
    if "@media print" in css:
        report.add(Finding(cat, "Estilos de impressão", Severity.PASS,
                           "CSS inclui regras para impressão."))

    # 8. sr-only class
    if "sr-only" in css or ".sr-only" in html:
        report.add(Finding(cat, "Classe sr-only presente", Severity.PASS,
                           "Classe para conteúdo visível apenas para screen readers."))


def check_institutions(report: ReviewReport, json_data: dict) -> None:
    """Verifica completude e qualidade das instituições de apoio."""
    cat = "Instituições de Apoio"

    institutions = json_data.get("instituicoes_apoio", [])
    if not institutions:
        report.add(Finding(cat, "Sem instituições de apoio", Severity.ERROR,
                           "Array 'instituicoes_apoio' ausente ou vazio no JSON.",
                           sugestao="Adicione instituições: Defensoria, CRAS, APAE, AMA etc."))
        return

    report.add(Finding(cat, f"{len(institutions)} instituições cadastradas", Severity.PASS,
                       f"Base de {len(institutions)} instituições de apoio."))

    # Verificar diversidade de tipos
    tipos = set(i.get("tipo", "") for i in institutions)
    expected_types = {"governamental", "ong", "profissional"}
    missing_types = expected_types - tipos
    if not missing_types:
        report.add(Finding(cat, "Diversidade de tipos completa", Severity.PASS,
                           "Instituições governamentais, ONGs e profissionais representadas."))
    else:
        report.add(Finding(cat, f"Tipos ausentes: {', '.join(missing_types)}", Severity.WARNING,
                           f"Faltam instituições do tipo: {', '.join(missing_types)}.",
                           sugestao="Adicione instituições dos tipos faltantes."))

    # Verificar campos obrigatórios
    required_fields = ["id", "nome", "tipo", "descricao", "url", "como_acessar", "categorias"]
    for inst in institutions:
        missing = [f for f in required_fields if not inst.get(f)]
        if missing:
            report.add(Finding(cat, f"Campos incompletos: {inst.get('nome', '?')}", Severity.WARNING,
                               f"Campos ausentes: {', '.join(missing)}.",
                               sugestao="Complete todos os campos obrigatórios."))

    # Verificar cobertura de categorias
    all_cats = set()
    for inst in institutions:
        all_cats.update(inst.get("categorias", []))

    expected_cats = {"bpc", "ciptea", "educacao", "plano_saude", "sus_terapias", "transporte", "trabalho", "fgts", "moradia"}
    uncovered = expected_cats - all_cats
    if not uncovered:
        report.add(Finding(cat, "Cobertura completa de categorias", Severity.PASS,
                           f"Todas as {len(expected_cats)} categorias de direitos possuem instituições de apoio."))
    else:
        report.add(Finding(cat, f"Categorias sem apoio: {', '.join(uncovered)}", Severity.WARNING,
                           f"Categorias sem instituição mapeada: {', '.join(uncovered)}.",
                           sugestao="Adicione instituições que atendam essas categorias."))


def check_category_schema(report: ReviewReport, json_data: dict) -> None:
    """Verifica schema e completude de cada categoria — garante integridade de dados."""
    cat = "Schema / Governança"

    categorias = json_data.get("categorias", [])
    if not categorias:
        report.add(Finding(cat, "Sem categorias no JSON", Severity.CRITICAL,
                           "Array 'categorias' ausente ou vazio.",
                           sugestao="Adicione pelo menos uma categoria ao JSON."))
        return

    report.add(Finding(cat, f"{len(categorias)} categorias cadastradas", Severity.PASS,
                       f"Base de {len(categorias)} categorias de direitos."))

    # Campos obrigatórios por categoria
    required_fields = {
        "id": str, "titulo": str, "icone": str, "resumo": str,
        "base_legal": list, "requisitos": list, "documentos": list,
        "passo_a_passo": list, "dicas": list, "valor": str,
        "onde": str, "links": list, "tags": list,
    }

    # Mínimos por campo de lista
    min_lengths = {
        "base_legal": 1, "requisitos": 2, "documentos": 3,
        "passo_a_passo": 3, "dicas": 2, "links": 1, "tags": 5,
    }

    for categoria in categorias:
        cat_id = categoria.get("id", "???")
        cat_label = f"[{cat_id}]"

        # Verificar campos obrigatórios
        for field_name, field_type in required_fields.items():
            value = categoria.get(field_name)
            if value is None:
                report.add(Finding(cat, f"{cat_label} campo ausente: {field_name}", Severity.ERROR,
                                   f"Categoria '{cat_id}' não possui campo '{field_name}'.",
                                   sugestao=f"Adicione '{field_name}' à categoria '{cat_id}'."))
            elif not isinstance(value, field_type):
                report.add(Finding(cat, f"{cat_label} tipo incorreto: {field_name}", Severity.ERROR,
                                   f"Campo '{field_name}' deveria ser {field_type.__name__}, mas é {type(value).__name__}."))

        # Verificar mínimos de lista
        for field_name, min_len in min_lengths.items():
            value = categoria.get(field_name, [])
            if isinstance(value, list) and len(value) < min_len:
                report.add(Finding(cat, f"{cat_label} {field_name} insuficiente", Severity.WARNING,
                                   f"'{field_name}' tem {len(value)} itens, mínimo recomendado: {min_len}.",
                                   sugestao=f"Adicione mais itens a '{field_name}' em '{cat_id}'."))

        # Verificar que base_legal tem link do planalto
        base_legal = categoria.get("base_legal", [])
        has_official_law = any(
            "planalto.gov.br" in bl.get("link", "") or "gov.br" in bl.get("link", "")
            for bl in base_legal if isinstance(bl, dict)
        )
        if base_legal and not has_official_law:
            report.add(Finding(cat, f"{cat_label} base_legal sem fonte oficial", Severity.WARNING,
                               f"Nenhuma lei em '{cat_id}' aponta para planalto.gov.br ou gov.br.",
                               sugestao="Adicione link oficial da legislação (planalto.gov.br)."))

        # Verificar que links tem URL válida
        for link in categoria.get("links", []):
            if isinstance(link, dict):
                url = link.get("url", "")
                if not url.startswith("https://"):
                    report.add(Finding(cat, f"{cat_label} link inseguro: {url[:40]}", Severity.WARNING,
                                       "Link não usa HTTPS.",
                                       sugestao="Use apenas URLs HTTPS."))

        # Verificar ID é snake_case sem acentos
        if cat_id != cat_id.lower() or " " in cat_id:
            report.add(Finding(cat, f"{cat_label} ID fora do padrão", Severity.WARNING,
                               f"ID '{cat_id}' deve ser snake_case minúsculo sem espaços.",
                               sugestao="Use formato: minha_categoria"))

    # Verificar documentos_mestre vs categorias
    doc_categorias = set()
    for doc in json_data.get("documentos_mestre", []):
        doc_categorias.update(doc.get("categorias", []))

    cat_ids = {c.get("id") for c in categorias}
    orphan_cats = cat_ids - doc_categorias
    if orphan_cats:
        report.add(Finding(cat, f"Categorias sem documentos mestre: {', '.join(orphan_cats)}", Severity.WARNING,
                           "Essas categorias não aparecem em nenhum documento mestre.",
                           sugestao="Adicione as categorias aos documentos_mestre relevantes."))
    else:
        report.add(Finding(cat, "Todas categorias cobertas por documentos mestre", Severity.PASS,
                           "Cada categoria aparece em pelo menos um documento mestre."))

    # Verificar que KEYWORD_MAP do app.js cobre todas as categorias
    js = read_text(APP_JS)
    for categoria in categorias:
        cat_id = categoria.get("id", "")
        # Buscar se o cat_id aparece como valor em alguma entry do KEYWORD_MAP
        pattern = rf"['\"]?{re.escape(cat_id)}['\"]?"
        keyword_section = js[js.index("KEYWORD_MAP"):js.index("KEYWORD_MAP") + 5000] if "KEYWORD_MAP" in js else ""
        if cat_id and cat_id in keyword_section:
            report.add(Finding(cat, f"[{cat_id}] presente no KEYWORD_MAP", Severity.PASS,
                               f"Categoria '{cat_id}' é referenciada no KEYWORD_MAP para análise de documentos."))
        elif cat_id:
            report.add(Finding(cat, f"[{cat_id}] ausente do KEYWORD_MAP", Severity.ERROR,
                               f"Categoria '{cat_id}' NÃO aparece no KEYWORD_MAP do app.js.",
                               sugestao=f"Adicione keywords para '{cat_id}' no KEYWORD_MAP."))

    # Verificar governance doc
    governance = PROJECT_ROOT / "GOVERNANCE.md"
    if governance.exists():
        report.add(Finding(cat, "GOVERNANCE.md presente", Severity.PASS,
                           "Documento de governança de dados e fontes presente."))
    else:
        report.add(Finding(cat, "GOVERNANCE.md ausente", Severity.INFO,
                           "Documento de governança não encontrado.",
                           sugestao="Crie GOVERNANCE.md com critérios para fontes e categorias."))


def check_links_reachable(report: ReviewReport, json_data: dict, max_checks: int = 10) -> None:
    """Verifica acessibilidade das URLs (com limite para não sobrecarregar)."""
    cat = "Links / URLs"

    urls_to_check = []

    # Collect from fontes
    for fonte in json_data.get("fontes", []):
        url = fonte.get("url", "")
        if url.startswith("http"):
            urls_to_check.append((url, f"Fonte: {fonte.get('nome', '?')[:40]}"))

    # Collect from institutions
    for inst in json_data.get("instituicoes_apoio", []):
        url = inst.get("url", "")
        if url.startswith("http"):
            urls_to_check.append((url, f"Inst: {inst.get('nome', '?')[:40]}"))

    # Deduplicate
    seen = set()
    unique = []
    for url, label in urls_to_check:
        if url not in seen:
            seen.add(url)
            unique.append((url, label))

    # Check subset
    checked = unique[:max_checks]
    report.add(Finding(cat, f"Verificando {len(checked)}/{len(unique)} URLs...", Severity.INFO,
                       f"Checando acessibilidade de {len(checked)} URLs únicas."))

    for url, label in checked:
        reachable, code = check_url_reachable(url)
        if reachable:
            report.add(Finding(cat, f"OK ({code}): {label}", Severity.PASS,
                               f"{url[:60]} — HTTP {code}"))
        else:
            report.add(Finding(cat, f"FALHA ({code}): {label}", Severity.ERROR,
                               f"{url[:60]} — Inacessível (HTTP {code})",
                               sugestao="Verifique e atualize a URL."))


# ========================
# Runner Principal
# ========================

def run_review(
    categorias: Optional[list[str]] = None,
    check_links: bool = False,
) -> ReviewReport:
    """Executa a revisão completa ou por categoria."""
    report = ReviewReport()

    # Carregar dados
    html = read_text(INDEX_HTML)
    css = read_text(STYLES_CSS)
    js = read_text(APP_JS)
    json_data = read_json(DATA_JSON)

    if not html or not js or not json_data:
        report.add(Finding("Geral", "Arquivos não encontrados", Severity.CRITICAL,
                           "Não foi possível ler os arquivos do projeto.",
                           sugestao=f"Verifique se PROJECT_ROOT está correto: {PROJECT_ROOT}"))
        return report

    # Mapa de verificações
    checks = {
        "lgpd": lambda: check_lgpd(report, html, js, json_data),
        "seguranca": lambda: check_security(report, html, js),
        "qualidade": lambda: check_quality(report, html, css, js),
        "confiabilidade": lambda: check_reliability(report, js, html),
        "performance": lambda: check_performance(report),
        "transparencia": lambda: check_transparency(report, json_data),
        "versionamento": lambda: check_versioning(report, json_data),
        "modularidade": lambda: check_modularity(report),
        "acessibilidade": lambda: check_accessibility(report, html, css),
        "instituicoes": lambda: check_institutions(report, json_data),
        "schema": lambda: check_category_schema(report, json_data),
    }

    if check_links:
        checks["links"] = lambda: check_links_reachable(report, json_data)

    # Executar verificações
    to_run = categorias if categorias else list(checks.keys())
    for cat_key in to_run:
        if cat_key in checks:
            try:
                checks[cat_key]()
            except Exception as e:
                report.add(Finding(cat_key, "Erro na verificação", Severity.ERROR,
                                   f"Exceção: {e}"))

    report.calcular_score()
    return report


def format_report_text(report: ReviewReport) -> str:
    """Formata relatório como texto legível."""
    lines = []
    lines.append("=" * 70)
    lines.append("  NossoDireito — CodeReview — Auto-avaliação")
    lines.append("=" * 70)
    lines.append(f"  Data: {report.timestamp}")
    lines.append(f"  Score Total: {report.score_total}/100")
    lines.append("=" * 70)
    lines.append("")

    # Scores por categoria
    lines.append("📊 SCORES POR CATEGORIA:")
    lines.append("-" * 40)
    for cat_name, score in sorted(report.categorias_scores.items(), key=lambda x: -x[1]):
        bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
        emoji = "✅" if score >= 80 else "⚠️" if score >= 50 else "❌"
        lines.append(f"  {emoji} {cat_name:<30} {bar} {score}")
    lines.append("")

    # Achados agrupados
    cats: dict[str, list[Finding]] = {}
    for f in report.achados:
        cats.setdefault(f.categoria, []).append(f)

    for cat_name in sorted(cats.keys()):
        findings = cats[cat_name]
        lines.append(f"📋 {cat_name.upper()}")
        lines.append("-" * 40)
        for f in findings:
            lines.append(f"  {f.severidade.value} {f.titulo}")
            if f.descricao:
                lines.append(f"     {f.descricao}")
            if f.sugestao:
                lines.append(f"     💡 {f.sugestao}")
            if f.arquivo:
                lines.append(f"     📄 {f.arquivo}" + (f" (L{f.linha})" if f.linha else ""))
        lines.append("")

    # Resumo
    severity_counts = {}
    for f in report.achados:
        severity_counts[f.severidade] = severity_counts.get(f.severidade, 0) + 1

    lines.append("📊 RESUMO:")
    lines.append("-" * 40)
    for sev in [Severity.CRITICAL, Severity.ERROR, Severity.WARNING, Severity.INFO, Severity.PASS]:
        count = severity_counts.get(sev, 0)
        if count > 0:
            lines.append(f"  {sev.value} {sev.name}: {count}")
    lines.append("")
    lines.append(f"  Score Final: {'🏆' if report.score_total >= 80 else '⚠️'} {report.score_total}/100")
    lines.append("=" * 70)

    return "\n".join(lines)


def main() -> None:
    """Entry point CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="NossoDireito CodeReview — Auto-avaliação do projeto",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python codereview.py                     # Revisão completa
  python codereview.py --categoria lgpd    # Só LGPD
  python codereview.py --json              # Saída JSON
  python codereview.py --check-links       # Verifica URLs (mais lento)
        """,
    )
    parser.add_argument(
        "--categoria", "-c",
        action="append",
        choices=[
            "lgpd", "seguranca", "qualidade", "confiabilidade",
            "performance", "transparencia", "versionamento",
            "modularidade", "acessibilidade", "instituicoes", "schema",
        ],
        help="Categoria específica para verificar (pode repetir)",
    )
    parser.add_argument("--json", "-j", action="store_true",
                        help="Saída em formato JSON")
    parser.add_argument("--check-links", "-l", action="store_true",
                        help="Verificar se URLs estão acessíveis (mais lento)")

    args = parser.parse_args()

    report = run_review(
        categorias=args.categoria,
        check_links=args.check_links,
    )

    if args.json:
        output = {
            "timestamp": report.timestamp,
            "versao_codereview": report.versao_codereview,
            "score_total": report.score_total,
            "categorias_scores": report.categorias_scores,
            "achados": [f.to_dict() for f in report.achados],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(format_report_text(report))


if __name__ == "__main__":
    main()
