#!/usr/bin/env python3
"""
codereview.py — Quality Gate do NossoDireito
============================================

Pipeline de qualidade pré-deploy com verificações em 17 categorias:

  CHECKS CORE:
  1.  Conformidade regulatória (LGPD, legislação brasileira)
  2.  Segurança (XSS, CSP, SRI, criptografia, TTL)
  3.  Qualidade de software (HTML, CSS, JS patterns)
  4.  Confiabilidade (error handling, graceful degradation)
  5.  Performance (file sizes, otimizações)
  6.  Transparência (fontes oficiais, links válidos)
  7.  Versionamento (semver, changelog)
  8.  Modularidade (estrutura de arquivos)
  9.  Acessibilidade (ARIA, contraste, semântica)
  10. Instituições de apoio (completude, URLs válidas)
  11. Schema / Governança (integridade de dados)

  CHECKS QUALITY GATE (v2.0):
  12. Links / URLs (opcional, rede)
  13. Dados Sensíveis — detecção de segredos, chaves, tokens, senhas
  14. Higiene de Arquivos — arquivos órfãos, duplicados, ausentes
  15. Documentação — README, CHANGELOG, GOVERNANCE, SECURITY_AUDIT
  16. Disclaimer / Regulatório — aviso legal, transparência, LGPD
  17. WAF 5 Pilares — Well-Architected Framework assessment

Uso:
    python codereview.py                    # Roda todas as verificações
    python codereview.py --categoria lgpd   # Roda só uma categoria
    python codereview.py --json             # Saída em JSON
    python codereview.py --ci               # Modo CI (exit code 1 se falhar)
    python codereview.py --min-score 80     # Score mínimo para CI
    python codereview.py --check-links      # Verifica URLs (mais lento)

Autor: NossoDireito — Projeto sem fins lucrativos
Licença: MIT
"""

from __future__ import annotations

import json
import re
import ssl
import subprocess
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
CHANGELOG_MD = PROJECT_ROOT / "CHANGELOG.md"
GOVERNANCE_MD = PROJECT_ROOT / "GOVERNANCE.md"
SECURITY_AUDIT_MD = PROJECT_ROOT / "SECURITY_AUDIT.md"
TERRAFORM_DIR = PROJECT_ROOT / "terraform"
GITIGNORE = PROJECT_ROOT / ".gitignore"

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
    "who.int",
    "cfm.org.br",
    "cfp.org.br",
    "coffito.gov.br",
]

# Versão mínima esperada
MIN_VERSION = "1.0.0"

# Tamanhos máximos recomendados (em bytes)
# Nota: JS/CSS são minificados no deploy (terser/clean-css) — limites são para source
MAX_HTML_SIZE = 35_000
MAX_CSS_SIZE = 60_000
MAX_JS_SIZE = 115_000  # Aumentado para 115KB (TTS enterprise: chunking, preprocessing, seleção manual)
MAX_JSON_SIZE = 110_000  # Aumentado para 110KB (15 categorias vs. 10 originais = +50% conteúdo)

# Padrões de dados sensíveis (regex)
SENSITIVE_PATTERNS = [
    (r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", "Chave privada detectada"),
    (r"-----BEGIN\s+CERTIFICATE-----", "Certificado PEM detectado"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key detectada"),
    (r"(?:password|senha|secret|token)\s*[:=]\s*['\"][^'\"]{4,}", "Segredo hardcoded"),
    (r"(?:api[_-]?key|apikey)\s*[:=]\s*['\"][^'\"]{8,}", "API Key hardcoded"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API Key"),
    (r"(?:mongodb|postgres|mysql)://[^\s]+", "Connection string de banco"),
    (r"(?:Bearer|Basic)\s+[a-zA-Z0-9+/=]{20,}", "Token de autenticação"),
    (r"""['"]\S+\.pfx['"]|['"]\S+\.p12['"]|['"]\S+\.pem['"]""", "Referência a arquivo de certificado"),
]

# Extensões de arquivo sensíveis
SENSITIVE_EXTENSIONS = {".pfx", ".p12", ".pem", ".key", ".env", ".credentials"}

# Versão do Quality Gate
QUALITY_GATE_VERSION = "2.0.0"


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
    versao_codereview: str = QUALITY_GATE_VERSION
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
    # Analisa cada uso de innerHTML com template literals (`...`).
    # Considera seguro se: contém escapeHtml, usa .map(), ou é string puramente estática
    # (sem ${...} interpolations ou apenas ${...} com escapeHtml).
    innerhtml_uses = re.findall(r"\.innerHTML\s*=\s*(.+?)(?:;|\n)", js)
    unsafe_count = 0
    for use in innerhtml_uses:
        if "`" not in use:
            continue  # atribuição simples (ex: = '') — seguro
        if "escapeHtml" in use or "map" in use:
            continue  # sanitizado ou delegado a render function
        # Verifica se template literal tem interpolações com dados dinâmicos
        interpolations = re.findall(r"\$\{([^}]+)\}", use)
        has_dynamic = any(
            "escapeHtml" not in interp
            and not re.match(r"^['\"][^'\"]*['\"]$", interp.strip())
            and not re.match(r"^\w+\s*\?\s*['\"].*?['\"]\s*:\s*['\"].*?['\"]$", interp.strip())
            for interp in interpolations
        )
        if has_dynamic:
            unsafe_count += 1
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
                # VLibras Unity (acessibilidade governamental) requer unsafe-eval
                # Lei 13.146/2015 (LBI) exige acessibilidade em sites públicos
                has_vlibras = "vlibras.gov.br" in html.lower()
                if has_vlibras:
                    report.add(Finding(cat, "CSP com unsafe-eval para VLibras (LBI)", Severity.PASS,
                                       "CSP contém 'unsafe-eval' exigido por VLibras Unity (Lei 13.146/2015). Trade-off documentado: acessibilidade governamental prioritária."))
                else:
                    report.add(Finding(cat, "CSP permite unsafe-eval", Severity.CRITICAL,
                                       "CSP contém 'unsafe-eval' — anula proteção XSS.",
                                       sugestao="Remova 'unsafe-eval' do CSP ou documente exceção (ex: VLibras)."))
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
            # Gov.br domains are trusted government sources (e.g. VLibras a11y)
            is_govbr = ".gov.br" in src
            if "integrity=" in attrs:
                report.add(Finding(cat, f"SRI presente em script externo", Severity.PASS,
                                   f"Subresource Integrity detectado para: {src[:50]}..."))
                if 'crossorigin="anonymous"' in attrs or "crossorigin='anonymous'" in attrs:
                    report.add(Finding(cat, "crossorigin=anonymous em script externo", Severity.PASS,
                                       "Atributo crossorigin correctamente configurado para SRI."))
                else:
                    report.add(Finding(cat, "Falta crossorigin em script externo SRI", Severity.WARNING,
                                       "Script com integrity mas sem crossorigin='anonymous'.",
                                       sugestao="Adicione crossorigin='anonymous' ao script com SRI."))
            elif is_govbr:
                # Gov.br scripts that update without versioning (e.g. VLibras)
                # cannot use SRI — hash breaks on every server-side update.
                # Official gov.br integration examples omit SRI intentionally.
                report.add(Finding(cat, f"Script gov.br confiável: {src[:50]}...", Severity.PASS,
                                   "Script de domínio gov.br — fonte oficial confiável, SRI omitido intencionalmente (updates sem versionamento)."))
            else:
                report.add(Finding(cat, f"Script externo: {src[:60]}...", Severity.WARNING,
                                   "Script carregado de fonte externa não verificada."))

    # 6. Verifica target="_blank" com noopener (aceita noopener e noopener noreferrer)
    blank_links = re.findall(r'target="_blank"', html)
    noopener_links = re.findall(r'rel="noopener(?:\s+noreferrer)?"', html)
    # Also check JS for dynamically generated links
    blank_links_js = re.findall(r'target="_blank"', js)
    noopener_links_js = re.findall(r'rel="noopener(?:\s+noreferrer)?"', js)
    total_blank = len(blank_links) + len(blank_links_js)
    total_noopener = len(noopener_links) + len(noopener_links_js)
    if total_blank > 0:
        if total_noopener >= total_blank:
            report.add(Finding(cat, "Links externos com rel='noopener'", Severity.PASS,
                               f"Todos os {total_blank} links target='_blank' possuem rel='noopener'."))
        else:
            report.add(Finding(cat, "Links sem rel='noopener'", Severity.WARNING,
                               f"{total_blank} links com target='_blank' mas apenas {total_noopener} com rel='noopener'.",
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

    # ── EASM Hardening Checks (server.js) ──
    server_js = PROJECT_ROOT / "server.js"
    srv = read_text(server_js) if server_js.exists() else ""

    if srv:
        # 11. HSTS (Strict-Transport-Security)
        if "Strict-Transport-Security" in srv:
            report.add(Finding(cat, "HSTS presente (server.js)", Severity.PASS,
                               "Strict-Transport-Security header configurado no servidor."))
        else:
            report.add(Finding(cat, "Sem HSTS no servidor", Severity.CRITICAL,
                               "Strict-Transport-Security não encontrado no server.js.",
                               sugestao="Adicione 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload'."))

        # 12. Cross-Origin headers (COOP, CORP, COEP)
        co_headers = ["Cross-Origin-Opener-Policy", "Cross-Origin-Resource-Policy", "Cross-Origin-Embedder-Policy"]
        co_found = [h for h in co_headers if h in srv]
        if len(co_found) == 3:
            report.add(Finding(cat, f"Cross-Origin isolation ({len(co_found)}/3)", Severity.PASS,
                               "COOP, CORP e COEP configurados — isolamento cross-origin completo."))
        else:
            missing = [h for h in co_headers if h not in srv]
            report.add(Finding(cat, f"Cross-Origin isolation parcial ({len(co_found)}/3)", Severity.WARNING,
                               f"Faltam: {', '.join(missing)}.",
                               sugestao="Adicione COOP, CORP e COEP no server.js."))

        # 13. Rate limiting
        if "isRateLimited" in srv or "rateLimit" in srv.lower():
            report.add(Finding(cat, "Rate limiting implementado", Severity.PASS,
                               "Proteção contra abuso de requisições (CWE-770)."))
        else:
            report.add(Finding(cat, "Sem rate limiting", Severity.WARNING,
                               "Servidor não possui rate limiting — vulnerável a DoS.",
                               sugestao="Implemente rate limiting por IP no server.js."))

        # 14. Host header validation (CWE-644)
        if "ALLOWED_HOSTS" in srv or "host header" in srv.lower():
            report.add(Finding(cat, "Host header validation presente", Severity.PASS,
                               "Validação de Host header implementada (CWE-644)."))
        else:
            report.add(Finding(cat, "Sem validação de Host header", Severity.WARNING,
                               "Host header não validado — risco de host header injection.",
                               sugestao="Adicione whitelist de hosts permitidos no server.js."))

        # 15. Connection hardening (Slowloris prevention)
        if "timeout" in srv and "headersTimeout" in srv:
            report.add(Finding(cat, "Connection timeouts configurados", Severity.PASS,
                               "Timeouts de request/headers previnem ataques Slowloris."))
        else:
            report.add(Finding(cat, "Sem connection timeouts", Severity.WARNING,
                               "Servidor vulnerável a ataques Slowloris (CWE-400).",
                               sugestao="Configure server.timeout e server.headersTimeout."))

        # 16. Server identity suppression (CWE-200)
        if "X-Powered-By" in srv or "removeHeader" in srv:
            report.add(Finding(cat, "Server identity suprimida", Severity.PASS,
                               "Header X-Powered-By removido — EASM não identifica a stack."))

        # 17. upgrade-insecure-requests
        if "upgrade-insecure-requests" in srv or "upgrade-insecure-requests" in html:
            report.add(Finding(cat, "upgrade-insecure-requests presente", Severity.PASS,
                               "CSP inclui upgrade-insecure-requests — browsers forçam HTTPS."))

    # ── Client-side hardening (app.js) ──
    # 18. Prototype pollution guard (CWE-1321)
    if "safeJsonParse" in js and "__proto__" in js:
        report.add(Finding(cat, "Prototype pollution guard presente", Severity.PASS,
                           "safeJsonParse filtra __proto__/constructor + deepFreeze nos dados — proteção CWE-1321."))
    else:
        report.add(Finding(cat, "Sem proteção contra prototype pollution", Severity.WARNING,
                           "Object.prototype não está congelado — risco CWE-1321.",
                           sugestao="Adicione Object.freeze(Object.prototype) no início da IIFE."))

    # 19. Open redirect prevention (CWE-601)
    if "isSafeUrl" in js or "safeUrl" in js.lower():
        report.add(Finding(cat, "Open redirect guard presente", Severity.PASS,
                           "Função de validação de URL detectada (CWE-601)."))
    else:
        report.add(Finding(cat, "Sem validação de URL segura", Severity.INFO,
                           "Sem função isSafeUrl() — considere validar URLs antes de navegação.",
                           sugestao="Adicione função isSafeUrl() que valida contra whitelist de domínios."))

    # 20. Safe JSON parse (anti-pollution via JSON payloads)
    if "safeJsonParse" in js:
        report.add(Finding(cat, "Safe JSON parse implementado", Severity.PASS,
                           "JSON.parse com reviver que filtra __proto__/constructor."))

    # 21. Deep freeze on data (CWE-471)
    if "deepFreeze" in js or "Object.freeze" in js:
        report.add(Finding(cat, "Data objects frozen (CWE-471)", Severity.PASS,
                           "Dados da aplicação são imutáveis após carregamento."))

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

    # 9. No alert() calls (UX — replaced by showToast)
    # Exclude comment lines (// ...) from detection
    js_no_comments = re.sub(r'//.*$', '', js, flags=re.MULTILINE)
    alert_calls = re.findall(r'\balert\s*\(', js_no_comments)
    if 'showToast' in js and not alert_calls:
        report.add(Finding(cat, "showToast() sem alert() — UX moderna", Severity.PASS,
                           "Notificações inline (toast) em vez de alert() intrusivo."))
    elif alert_calls:
        report.add(Finding(cat, f"{len(alert_calls)} alert() restantes", Severity.WARNING,
                           "alert() detectado — UX intrusiva.",
                           sugestao="Substitua alert() por showToast() para notificações inline."))

    # 10. Browser back-button (history.pushState)
    if 'pushState' in js and 'popstate' in js:
        report.add(Finding(cat, "Navegação com back-button (pushState)", Severity.PASS,
                           "history.pushState + popstate — botão voltar funciona na SPA."))

    # 11. WhatsApp share
    if 'whatsapp' in js.lower() or 'wa.me' in js:
        report.add(Finding(cat, "Compartilhamento WhatsApp", Severity.PASS,
                           "Botão de compartilhamento via WhatsApp para disseminar direitos."))

    # 12. Checklist progress bar
    if 'checklist-progress' in css or 'progress-fill' in css:
        report.add(Finding(cat, "Barra de progresso do checklist", Severity.PASS,
                           "Progresso visual de tarefas concluídas — gamificação da jornada."))


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

    # PWA / Service Worker / SEO best practices
    html = read_text(INDEX_HTML)

    # Canonical URL
    if 'rel="canonical"' in html:
        report.add(Finding(cat, "Canonical URL presente", Severity.PASS,
                           "Tag <link rel=canonical> configurada para SEO."))
    else:
        report.add(Finding(cat, "Canonical URL ausente", Severity.WARNING,
                           "Sem <link rel=canonical> — pode afetar SEO.",
                           sugestao='Adicione <link rel="canonical" href="https://..."> no <head>.'))

    # Preconnect para CDN
    if "preconnect" in html:
        report.add(Finding(cat, "Preconnect configurado", Severity.PASS,
                           "Preconnect para CDN melhora tempo de carregamento."))

    # PWA manifest
    manifest = PROJECT_ROOT / "manifest.json"
    if manifest.exists() and 'rel="manifest"' in html:
        report.add(Finding(cat, "PWA manifest presente", Severity.PASS,
                           "manifest.json + link no HTML — app instalável no celular."))
    elif manifest.exists():
        report.add(Finding(cat, "PWA manifest sem link no HTML", Severity.WARNING,
                           "manifest.json existe mas não está referenciado no index.html.",
                           sugestao='Adicione <link rel="manifest" href="/manifest.json"> no <head>.'))

    # Service Worker
    sw = PROJECT_ROOT / "sw.js"
    if sw.exists() and "serviceWorker" in html:
        report.add(Finding(cat, "Service Worker (offline)", Severity.PASS,
                           "sw.js presente + registro no HTML — suporte offline para áreas rurais."))

    # JSON-LD structured data
    if "application/ld+json" in html:
        report.add(Finding(cat, "JSON-LD (SEO estruturado)", Severity.PASS,
                           "Dados estruturados schema.org presentes — melhora visibilidade no Google."))

    # robots.txt + sitemap.xml
    robots = PROJECT_ROOT / "robots.txt"
    sitemap = PROJECT_ROOT / "sitemap.xml"
    if robots.exists():
        report.add(Finding(cat, "robots.txt presente", Severity.PASS,
                           "Diretivas de rastreamento para Google/Bing configuradas."))
    if sitemap.exists():
        report.add(Finding(cat, "sitemap.xml presente", Severity.PASS,
                           "Mapa do site para motores de busca configurado."))

    # Twitter Card tags
    if 'twitter:card' in html:
        report.add(Finding(cat, "Twitter Card tags presentes", Severity.PASS,
                           "Metadados para compartilhamento no Twitter/X configurados."))

    # Skip-to-content link (a11y)
    if 'skip-link' in html or 'skip-nav' in html:
        report.add(Finding(cat, "Skip-to-content link (a11y)", Severity.PASS,
                           "Link para pular navegação — acessibilidade para leitores de tela."))

    # FAQPage schema
    if "FAQPage" in html:
        report.add(Finding(cat, "FAQPage schema (snippet SEO)", Severity.PASS,
                           "Schema FAQPage presente — potencial para featured snippets no Google."))

    # OG image dimensions
    if 'og:image:width' in html and 'og:image:height' in html:
        report.add(Finding(cat, "OG image dimensions definidas", Severity.PASS,
                           "Dimensões da imagem OG declaradas — exibição correta no Facebook/LinkedIn."))
    elif 'og:image' in html:
        report.add(Finding(cat, "OG image sem dimensões", Severity.WARNING,
                           "og:image presente mas sem og:image:width/height.",
                           sugestao='Adicione <meta property="og:image:width" content="1200"> e height="630".'))

    # og:site_name
    if 'og:site_name' in html:
        report.add(Finding(cat, "og:site_name presente", Severity.PASS,
                           "Nome do site configurado para compartilhamento social."))

    # OG image file exists
    og_image = PROJECT_ROOT / "images" / "og-image.png"
    if og_image.exists():
        report.add(Finding(cat, "Arquivo og-image.png presente", Severity.PASS,
                           "Imagem de compartilhamento social (1200×630) disponível."))
    elif 'og:image' in html:
        report.add(Finding(cat, "og-image.png referenciado mas ausente", Severity.ERROR,
                           "HTML referencia og-image.png que não existe no diretório images/.",
                           sugestao="Crie images/og-image.png com 1200×630px."))

    # pdf.js lazy-loaded (ensurePdfJs)
    js = read_text(APP_JS)
    if "ensurePdfJs" in js:
        report.add(Finding(cat, "pdf.js lazy-loaded (ensurePdfJs)", Severity.PASS,
                           "pdf.js carregado sob demanda — ~400KB a menos no carregamento inicial."))
    elif 'pdf.js' in html or 'pdf.min.js' in html:
        report.add(Finding(cat, "pdf.js carregado no <head>", Severity.WARNING,
                           "pdf.js bloqueando carregamento inicial (~400KB).",
                           sugestao="Mova para lazy-loading com função ensurePdfJs()."))


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

    # Verificar separação de concerns (exclude JSON-LD structured data and SW registration)
    js_in_html = re.findall(r"<script(?![^>]*type=[\"']application/ld\+json[\"'])[^>]*>(?![\s\n]*</script>)(.+?)</script>", read_text(INDEX_HTML), re.DOTALL)
    inline_js = [s for s in js_in_html if len(s.strip()) > 50 and "serviceWorker" not in s]
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

    # matching_engine.json (keywords extraídas do app.js)
    me_json = PROJECT_ROOT / "data" / "matching_engine.json"
    if me_json.exists():
        report.add(Finding(cat, "matching_engine.json presente", Severity.PASS,
                           "Motor de matching externalizado — facilita manutenção de keywords."))
    else:
        report.add(Finding(cat, "matching_engine.json ausente", Severity.WARNING,
                           "Motor de matching não externalizado.",
                           sugestao="Extraia KEYWORD_MAP para data/matching_engine.json."))

    # validate_sources.py (validação automática de fontes oficiais)
    vs_script = PROJECT_ROOT / "scripts" / "validate_sources.py"
    if vs_script.exists():
        vs_content = read_text(vs_script)
        has_urls = "validate_urls" in vs_content
        has_leg = "validate_legislacao" in vs_content
        has_cid = "validate_cid" in vs_content
        if has_urls and has_leg and has_cid:
            report.add(Finding(cat, "validate_sources.py completo (URLs + Legislação + CID)", Severity.PASS,
                               "Script de validação automática com 3 módulos: URLs, Senado API, ICD API."))
        else:
            report.add(Finding(cat, "validate_sources.py incompleto", Severity.WARNING,
                               "Script de validação existe mas faltam módulos.",
                               sugestao="Adicione validate_urls, validate_legislacao e validate_cid."))
    else:
        report.add(Finding(cat, "validate_sources.py ausente", Severity.INFO,
                           "Sem script de validação automática de fontes.",
                           sugestao="Crie scripts/validate_sources.py para validar URLs, leis e CIDs."))


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
            "planalto.gov.br" in bl.get("url", "") or "gov.br" in bl.get("url", "")
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
                # tel: e mailto: são protocolos legítimos (ex: 0800, e-mail de contato)
                if url.startswith(("tel:", "mailto:")):
                    continue
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

    # Verificar que KEYWORD_MAP cobre todas as categorias
    # O KEYWORD_MAP pode estar inline no app.js OU no data/matching_engine.json
    js = read_text(APP_JS)
    keyword_section = ""
    if "KEYWORD_MAP" in js:
        keyword_section = js[js.index("KEYWORD_MAP"):js.index("KEYWORD_MAP") + 5000]
    me_json_path = PROJECT_ROOT / "data" / "matching_engine.json"
    if me_json_path.exists():
        keyword_section += read_text(me_json_path)
    for categoria in categorias:
        cat_id = categoria.get("id", "")
        if cat_id and cat_id in keyword_section:
            report.add(Finding(cat, f"[{cat_id}] presente no KEYWORD_MAP", Severity.PASS,
                               f"Categoria '{cat_id}' é referenciada no KEYWORD_MAP para análise de documentos."))
        elif cat_id:
            report.add(Finding(cat, f"[{cat_id}] ausente do KEYWORD_MAP", Severity.ERROR,
                               f"Categoria '{cat_id}' NÃO aparece no KEYWORD_MAP (app.js ou matching_engine.json).",
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
# Quality Gate — Novos Checks (v2.0)
# ========================

def _get_tracked_files() -> list[Path]:
    """Retorna lista de arquivos rastreados pelo git."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=10,
        )
        if result.returncode == 0:
            return [PROJECT_ROOT / f for f in result.stdout.strip().splitlines() if f.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    # Fallback: listar arquivos manualmente (excluindo .git, __pycache__, .terraform)
    excluded_dirs = {".git", "__pycache__", ".terraform", "node_modules", ".venv"}
    files = []
    for p in PROJECT_ROOT.rglob("*"):
        if p.is_file() and not any(ex in p.parts for ex in excluded_dirs):
            files.append(p)
    return files


def check_sensitive_data(report: ReviewReport) -> None:
    """Verifica ausência de dados sensíveis em arquivos rastreados."""
    cat = "Dados Sensíveis"

    tracked = _get_tracked_files()
    if not tracked:
        report.add(Finding(cat, "Não foi possível listar arquivos", Severity.WARNING,
                           "git ls-files falhou e fallback retornou vazio."))
        return

    report.add(Finding(cat, f"Analisando {len(tracked)} arquivos rastreados", Severity.PASS,
                       "Escaneando por segredos, chaves, tokens e senhas."))

    # 1. Verificar extensões sensíveis em arquivos rastreados
    for f in tracked:
        if f.suffix.lower() in SENSITIVE_EXTENSIONS:
            report.add(Finding(cat, f"Arquivo sensível rastreado: {f.name}", Severity.CRITICAL,
                               f"Arquivo {f.relative_to(PROJECT_ROOT)} com extensão sensível está no git.",
                               arquivo=str(f.relative_to(PROJECT_ROOT)),
                               sugestao=f"Remova {f.name} do git: git rm --cached {f.relative_to(PROJECT_ROOT)}"))

    # 2. Verificar padrões de segredos no conteúdo dos arquivos
    text_extensions = {".py", ".js", ".html", ".css", ".json", ".yml", ".yaml",
                       ".md", ".tf", ".tfvars", ".sh", ".txt", ".cfg", ".ini", ".toml"}
    secret_found = False

    for f in tracked:
        if f.suffix.lower() not in text_extensions:
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except (OSError, PermissionError):
            continue

        for pattern, label in SENSITIVE_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Ignorar falsos positivos em arquivos de configuração/automação
                safe_files = {".gitignore", "codereview.py", "quality-gate.yml", "pre-commit",
                              "terraform.yml", "deploy.yml", "weekly-review.yml",
                              "validate_sources.py"}
                # Workflows CI referenciam paths de runtime (ex: cert.pfx decodificado de secret)
                ci_dirs = {".github"}
                is_ci = any(p in str(f.relative_to(PROJECT_ROOT)).replace("\\", "/") for p in ci_dirs)
                if f.name in safe_files or is_ci:
                    continue
                secret_found = True
                report.add(Finding(cat, f"{label}: {f.name}", Severity.CRITICAL,
                                   f"Padrão suspeito em {f.relative_to(PROJECT_ROOT)}.",
                                   arquivo=str(f.relative_to(PROJECT_ROOT)),
                                   sugestao="Remova o segredo e rotacione a credencial."))

    if not secret_found:
        report.add(Finding(cat, "Nenhum segredo detectado nos arquivos", Severity.PASS,
                           "Escaneamento de padrões de segredos concluído — OK."))

    # 3. Verificar .gitignore cobre padrões essenciais
    if GITIGNORE.exists():
        gitignore_content = read_text(GITIGNORE)
        essential_patterns = ["*.pfx", "*.pem", "*.key", "*.env", "*.tfvars", "*.tfstate"]
        for pattern in essential_patterns:
            if pattern in gitignore_content:
                report.add(Finding(cat, f".gitignore cobre {pattern}", Severity.PASS,
                                   f"Padrão {pattern} presente no .gitignore."))
            else:
                report.add(Finding(cat, f".gitignore sem {pattern}", Severity.ERROR,
                                   f"Padrão {pattern} NÃO está no .gitignore.",
                                   arquivo=".gitignore",
                                   sugestao=f"Adicione {pattern} ao .gitignore."))
    else:
        report.add(Finding(cat, ".gitignore ausente", Severity.CRITICAL,
                           "Nenhum .gitignore encontrado — alto risco de commitar segredos.",
                           sugestao="Crie .gitignore com padrões para certificados, env, terraform state."))


def check_file_hygiene(report: ReviewReport) -> None:
    """Verifica higiene de arquivos: órfãos, desnecessários, backup, lixo."""
    cat = "Higiene de Arquivos"

    # 1. Arquivos que NÃO deveriam estar no projeto
    junk_patterns = [
        ("*.bak", "Arquivo de backup"),
        ("*.tmp", "Arquivo temporário"),
        ("*.log", "Arquivo de log"),
        ("*.orig", "Arquivo de merge"),
        ("*.swp", "Swap do vim"),
        ("*.swo", "Swap do vim"),
        ("Thumbs.db", "Cache do Windows"),
        (".DS_Store", "Cache do macOS"),
        ("desktop.ini", "Config do Windows"),
    ]

    tracked = _get_tracked_files()
    junk_found = False
    for f in tracked:
        for pattern, desc in junk_patterns:
            if pattern.startswith("*"):
                if f.suffix == pattern[1:]:
                    junk_found = True
                    report.add(Finding(cat, f"Arquivo desnecessário: {f.name}", Severity.WARNING,
                                       f"{desc} rastreado no git.",
                                       arquivo=str(f.relative_to(PROJECT_ROOT)),
                                       sugestao=f"Remova: git rm --cached {f.relative_to(PROJECT_ROOT)}"))
            elif f.name == pattern:
                junk_found = True
                report.add(Finding(cat, f"Arquivo desnecessário: {f.name}", Severity.WARNING,
                                   f"{desc} rastreado no git.",
                                   arquivo=str(f.relative_to(PROJECT_ROOT)),
                                   sugestao=f"Remova: git rm --cached {f.relative_to(PROJECT_ROOT)}"))

    if not junk_found:
        report.add(Finding(cat, "Sem arquivos desnecessários no git", Severity.PASS,
                           "Nenhum .bak, .tmp, .log, .orig ou lixo de SO detectado."))

    # 2. Verificar diretórios vazios (excluindo .git)
    for d in PROJECT_ROOT.iterdir():
        if d.is_dir() and d.name not in (".git", "__pycache__", ".terraform", "node_modules"):
            if not any(d.iterdir()):
                report.add(Finding(cat, f"Diretório vazio: {d.name}/", Severity.INFO,
                                   f"Diretório {d.name} está vazio.",
                                   sugestao="Remova o diretório ou adicione conteúdo."))

    # 3. Verificar que __pycache__ não está rastreado
    pycache_tracked = [f for f in tracked if "__pycache__" in str(f)]
    if pycache_tracked:
        report.add(Finding(cat, f"__pycache__ rastreado ({len(pycache_tracked)} arquivos)", Severity.WARNING,
                           "Cache Python não deve ser versionado.",
                           sugestao="Adicione __pycache__/ ao .gitignore e limpe: git rm -r --cached __pycache__/"))
    else:
        report.add(Finding(cat, "__pycache__ não rastreado", Severity.PASS,
                           "Cache Python corretamente excluído do git."))

    # 4. Verificar CHANGELOG existe
    if CHANGELOG_MD.exists():
        report.add(Finding(cat, "CHANGELOG.md presente", Severity.PASS,
                           "Histórico de versões documentado."))
    else:
        report.add(Finding(cat, "CHANGELOG.md ausente", Severity.ERROR,
                           "Sem histórico de mudanças documentado.",
                           sugestao="Crie CHANGELOG.md com histórico de todas as versões."))


def check_documentation(report: ReviewReport) -> None:
    """Verifica completude e frescor da documentação."""
    cat = "Documentação"

    # 1. README.md
    if README_MD.exists():
        readme = read_text(README_MD)
        readme_lower = readme.lower()

        required_sections = {
            "instalação": ["instalação", "install", "como usar", "getting started"],
            "licença": ["licença", "license", "mit"],
            "descrição": ["nossodireito", "sobre", "about"],
        }

        for section, keywords in required_sections.items():
            if any(kw in readme_lower for kw in keywords):
                report.add(Finding(cat, f"README: seção '{section}' presente", Severity.PASS,
                                   f"README contém informação sobre {section}."))
            else:
                report.add(Finding(cat, f"README: seção '{section}' ausente", Severity.WARNING,
                                   f"README não contém seção sobre {section}.",
                                   sugestao=f"Adicione seção sobre {section} ao README.md."))

        # Verificar tamanho mínimo
        if len(readme) < 200:
            report.add(Finding(cat, "README muito curto", Severity.WARNING,
                               f"README tem apenas {len(readme)} caracteres — insuficiente.",
                               sugestao="Expanda o README com descrição, uso, arquitetura."))
        else:
            report.add(Finding(cat, f"README: {len(readme):,} caracteres", Severity.PASS,
                               "README com tamanho adequado."))
    else:
        report.add(Finding(cat, "README.md ausente", Severity.CRITICAL,
                           "Documento principal de documentação não encontrado.",
                           sugestao="Crie README.md com descrição, uso e contribuição."))

    # 2. GOVERNANCE.md
    if GOVERNANCE_MD.exists():
        gov = read_text(GOVERNANCE_MD)
        report.add(Finding(cat, f"GOVERNANCE.md: {len(gov):,} chars", Severity.PASS,
                           "Documento de governança presente."))
    else:
        report.add(Finding(cat, "GOVERNANCE.md ausente", Severity.WARNING,
                           "Sem documento de governança.",
                           sugestao="Crie GOVERNANCE.md com critérios para fontes."))

    # 3. SECURITY_AUDIT.md
    if SECURITY_AUDIT_MD.exists():
        report.add(Finding(cat, "SECURITY_AUDIT.md presente", Severity.PASS,
                           "Auditoria de segurança documentada."))
    else:
        report.add(Finding(cat, "SECURITY_AUDIT.md ausente", Severity.WARNING,
                           "Sem documentação de auditoria de segurança.",
                           sugestao="Crie SECURITY_AUDIT.md documentando decisões de segurança."))

    # 4. CHANGELOG.md — verificar conteúdo
    if CHANGELOG_MD.exists():
        changelog = read_text(CHANGELOG_MD)
        # Verificar se tem entradas de versão
        version_entries = re.findall(r"##\s*\[?\d+\.\d+\.\d+", changelog)
        if version_entries:
            report.add(Finding(cat, f"CHANGELOG: {len(version_entries)} versão(ões)", Severity.PASS,
                               f"CHANGELOG documenta {len(version_entries)} versões."))
        else:
            report.add(Finding(cat, "CHANGELOG sem entradas de versão", Severity.WARNING,
                               "CHANGELOG existe mas não documenta versões.",
                               sugestao="Adicione entradas no formato ## [X.Y.Z] - YYYY-MM-DD."))

    # 5. Verificar data da última modificação do JSON
    json_data = read_json(DATA_JSON)
    ultima = json_data.get("ultima_atualizacao", "")
    if ultima:
        try:
            dt = date.fromisoformat(ultima)
            age_days = (date.today() - dt).days
            if age_days <= 30:
                report.add(Finding(cat, f"Dados atualizados há {age_days} dia(s)", Severity.PASS,
                                   f"Última atualização: {ultima} — recente."))
            elif age_days <= 90:
                report.add(Finding(cat, f"Dados com {age_days} dias", Severity.WARNING,
                                   f"Última atualização: {ultima} — considere revisar.",
                                   sugestao="Execute revisão semanal conforme GOVERNANCE.md."))
            else:
                report.add(Finding(cat, f"Dados desatualizados ({age_days} dias)", Severity.ERROR,
                                   f"Última atualização: {ultima} — dados possivelmente obsoletos.",
                                   sugestao="URGENTE: Revise todas as fontes e atualize."))
        except ValueError:
            report.add(Finding(cat, f"Data inválida: {ultima}", Severity.WARNING,
                               "Campo 'ultima_atualizacao' com formato inválido."))


def check_disclaimer(report: ReviewReport, html: str, js: str) -> None:
    """Verifica disclaimers legais, avisos regulatórios e transparência."""
    cat = "Disclaimer / Regulatório"

    html_lower = html.lower()
    js_lower = js.lower()

    # 1. Aviso de que não é aconselhamento jurídico
    legal_warnings = [
        "não constitui aconselhamento",
        "não é aconselhamento jurídico",
        "caráter meramente informativo",
        "informativo e educacional",
        "consulte um advogado",
        "consulte um profissional",
        "não substitui orientação",
        "não constitui",
        "consultoria jurídica",
        "guia informacional",
        "assessoria ou consultoria",
    ]
    has_legal_warning = any(w in html_lower or w in js_lower for w in legal_warnings)
    if has_legal_warning:
        report.add(Finding(cat, "Aviso legal presente", Severity.PASS,
                           "Disclaimer informando que não é aconselhamento jurídico."))
    else:
        report.add(Finding(cat, "Aviso legal ausente", Severity.CRITICAL,
                           "Nenhum disclaimer informando que o conteúdo não é aconselhamento jurídico.",
                           sugestao="URGENTE: Adicione disclaimer claro no modal de abertura."))

    # 2. Modal de disclaimer na abertura
    if "modal" in html_lower and ("disclaimer" in html_lower or "aviso" in html_lower):
        report.add(Finding(cat, "Modal de disclaimer presente", Severity.PASS,
                           "Existe modal de aviso/disclaimer no HTML."))
    elif "modal" in js_lower and ("disclaimer" in js_lower or "aviso" in js_lower):
        report.add(Finding(cat, "Modal de disclaimer no JS", Severity.PASS,
                           "Modal de aviso/disclaimer gerenciado via JavaScript."))
    else:
        report.add(Finding(cat, "Sem modal de disclaimer", Severity.WARNING,
                           "Não detectado modal de disclaimer/aviso ao abrir o site.",
                           sugestao="Adicione modal que exige aceite do disclaimer antes do uso."))

    # 3. Transparência sobre fontes
    if "transparência" in html_lower or "fontes" in html_lower:
        report.add(Finding(cat, "Seção de transparência presente", Severity.PASS,
                           "HTML contém menção a transparência/fontes."))
    else:
        report.add(Finding(cat, "Sem seção de transparência", Severity.WARNING,
                           "HTML não menciona transparência das fontes.",
                           sugestao="Adicione seção visível com fontes consultadas."))

    # 4. Aviso sobre dados PcD serem sensíveis
    sensitive_warnings = [
        "dado sensível", "dados sensíveis", "dado pessoal", "dados pessoais",
        "saúde", "deficiência", "pcd",
    ]
    has_sensitive_notice = any(w in html_lower for w in sensitive_warnings)
    if has_sensitive_notice:
        report.add(Finding(cat, "Menção a dados sensíveis presente", Severity.PASS,
                           "HTML menciona natureza sensível dos dados (PcD/saúde)."))

    # 5. Licença do projeto
    license_file = PROJECT_ROOT / "LICENSE"
    license_md = PROJECT_ROOT / "LICENSE.md"
    if license_file.exists() or license_md.exists():
        report.add(Finding(cat, "Arquivo LICENSE presente", Severity.PASS,
                           "Licença do projeto documentada."))
    elif "mit" in html_lower or "licença" in html_lower:
        report.add(Finding(cat, "Menção a licença no HTML", Severity.INFO,
                           "Licença mencionada no HTML mas sem arquivo dedicado."))
    else:
        report.add(Finding(cat, "Sem licença definida", Severity.WARNING,
                           "Nenhum arquivo LICENSE ou menção a licença.",
                           sugestao="Adicione arquivo LICENSE (MIT recomendado para projeto sem fins lucrativos)."))

    # 6. Ano do copyright
    current_year = str(date.today().year)
    if current_year in html or current_year in js:
        report.add(Finding(cat, f"Copyright {current_year} atualizado", Severity.PASS,
                           f"Referência ao ano {current_year} encontrada."))


def check_waf(report: ReviewReport, html: str, js: str) -> None:
    """Well-Architected Framework — avalia 5 pilares do Azure WAF."""
    cat = "WAF 5 Pilares"

    # ── Pilar 1: Segurança ──
    security_score = 0
    security_checks = 0

    # CSP
    security_checks += 1
    if "Content-Security-Policy" in html:
        security_score += 1

    # HTTPS only (staticwebapp.config.json OR sw.js — SW requires HTTPS)
    swa_config = PROJECT_ROOT / "staticwebapp.config.json"
    sw_js = PROJECT_ROOT / "sw.js"
    security_checks += 1
    if swa_config.exists():
        config = read_json(swa_config)
        headers = config.get("globalHeaders", {})
        if "Content-Security-Policy" in headers or "X-Content-Type-Options" in headers:
            security_score += 1
    elif sw_js.exists():
        # Service Workers só funcionam sobre HTTPS — sua presença garante HTTPS
        security_score += 1

    # Encryption at rest
    security_checks += 1
    if "AES-GCM" in js:
        security_score += 1

    # .gitignore secrets
    security_checks += 1
    if GITIGNORE.exists() and "*.pfx" in read_text(GITIGNORE):
        security_score += 1

    sec_pct = round(security_score / max(security_checks, 1) * 100)
    sev = Severity.PASS if sec_pct >= 75 else Severity.WARNING if sec_pct >= 50 else Severity.ERROR
    report.add(Finding(cat, f"Segurança: {sec_pct}% ({security_score}/{security_checks})", sev,
                       "Pilar 1 — Proteção de dados, identidade, infraestrutura."))

    # ── Pilar 2: Confiabilidade ──
    rel_score = 0
    rel_checks = 0

    # Error handling
    rel_checks += 1
    if js.count("try {") + js.count("try{") >= 3:
        rel_score += 1

    # Fallback messages
    rel_checks += 1
    if "Não foi possível" in js or "erro" in js.lower():
        rel_score += 1

    # IaC (terraform)
    rel_checks += 1
    if TERRAFORM_DIR.exists() and (TERRAFORM_DIR / "main.tf").exists():
        rel_score += 1

    # CI/CD
    rel_checks += 1
    ci_yml = PROJECT_ROOT / ".github" / "workflows" / "quality-gate.yml"
    deploy_yml = PROJECT_ROOT / ".github" / "workflows" / "deploy.yml"
    if ci_yml.exists() or deploy_yml.exists():
        rel_score += 1

    # Resilient fetch (retry com backoff)
    rel_checks += 1
    if "resilientFetch" in js:
        rel_score += 1

    rel_pct = round(rel_score / max(rel_checks, 1) * 100)
    sev = Severity.PASS if rel_pct >= 75 else Severity.WARNING if rel_pct >= 50 else Severity.ERROR
    report.add(Finding(cat, f"Confiabilidade: {rel_pct}% ({rel_score}/{rel_checks})", sev,
                       "Pilar 2 — Resiliência, recuperação, operações consistentes."))

    # ── Pilar 3: Performance / Eficiência ──
    perf_score = 0
    perf_checks = 0

    # File sizes within limits
    for path, max_size in [(INDEX_HTML, MAX_HTML_SIZE), (STYLES_CSS, MAX_CSS_SIZE),
                            (APP_JS, MAX_JS_SIZE), (DATA_JSON, MAX_JSON_SIZE)]:
        perf_checks += 1
        if path.exists() and path.stat().st_size <= max_size:
            perf_score += 1

    # Caching headers in SWA config or server.js
    perf_checks += 1
    server_js = PROJECT_ROOT / "server.js"
    if swa_config.exists():
        config_text = read_text(swa_config)
        if "Cache-Control" in config_text or "max-age" in config_text:
            perf_score += 1
    elif server_js.exists() and "Cache-Control" in read_text(server_js):
        perf_score += 1

    perf_pct = round(perf_score / max(perf_checks, 1) * 100)
    sev = Severity.PASS if perf_pct >= 75 else Severity.WARNING if perf_pct >= 50 else Severity.ERROR
    report.add(Finding(cat, f"Performance: {perf_pct}% ({perf_score}/{perf_checks})", sev,
                       "Pilar 3 — Otimização de recursos, latência, throughput."))

    # ── Pilar 4: Otimização de Custos ──
    cost_score = 0
    cost_checks = 0

    # App Service com SKU variável (F1 Free possível)
    cost_checks += 1
    tf_vars = TERRAFORM_DIR / "variables.tf"
    tf_vars_text = read_text(tf_vars) if tf_vars.exists() else ""
    if "app_service_sku" in tf_vars_text and "F1" in tf_vars_text:
        cost_score += 1  # Permite downgrade para Free tier

    # Terraform tags com estimativa de custo documentada
    cost_checks += 1
    tf_main = TERRAFORM_DIR / "main.tf"
    tf_main_text = read_text(tf_main) if tf_main.exists() else ""
    if "COST" in tf_main_text or "custo" in tf_main_text.lower() or "$" in tf_main_text:
        cost_score += 1

    # Multi-env support (para otimizar custo por ambiente)
    cost_checks += 1
    if "environment" in tf_vars_text and ("prod" in tf_vars_text or "staging" in tf_vars_text):
        cost_score += 1

    cost_pct = round(cost_score / max(cost_checks, 1) * 100)
    sev = Severity.PASS if cost_pct >= 75 else Severity.WARNING if cost_pct >= 50 else Severity.ERROR
    report.add(Finding(cat, f"Custo: {cost_pct}% ({cost_score}/{cost_checks})", sev,
                       "Pilar 4 — Eliminar desperdício, maximizar valor de negócio."))

    # ── Pilar 5: Excelência Operacional ──
    ops_score = 0
    ops_checks = 0

    # IaC
    ops_checks += 1
    if TERRAFORM_DIR.exists():
        ops_score += 1

    # CI/CD pipeline
    ops_checks += 1
    if deploy_yml.exists():
        ops_score += 1

    # Quality Gate automated
    ops_checks += 1
    codereview_py = PROJECT_ROOT / "codereview" / "codereview.py"
    if codereview_py.exists():
        ops_score += 1

    # Weekly review workflow
    ops_checks += 1
    weekly = PROJECT_ROOT / ".github" / "workflows" / "weekly-review.yml"
    if weekly.exists():
        ops_score += 1

    # Documentation (README + GOVERNANCE + CHANGELOG)
    ops_checks += 1
    doc_count = sum(1 for p in [README_MD, GOVERNANCE_MD, CHANGELOG_MD] if p.exists())
    if doc_count >= 2:
        ops_score += 1

    # deploy.yml: verifica cobertura de caminhos (todos os arquivos deployáveis)
    ops_checks += 1
    if deploy_yml.exists():
        deploy_text = read_text(deploy_yml)
        required_paths = ["robots.txt", "sitemap.xml", "sw.js", "manifest.json"]
        missing_paths = [p for p in required_paths if p not in deploy_text]
        if not missing_paths:
            ops_score += 1
        else:
            report.add(Finding(cat, f"deploy.yml falta paths: {', '.join(missing_paths)}", Severity.WARNING,
                               "Arquivos novos não disparam deploy ao serem alterados.",
                               sugestao=f"Adicione {', '.join(missing_paths)} aos paths do deploy.yml."))

    ops_pct = round(ops_score / max(ops_checks, 1) * 100)
    sev = Severity.PASS if ops_pct >= 75 else Severity.WARNING if ops_pct >= 50 else Severity.ERROR
    report.add(Finding(cat, f"Excelência Operacional: {ops_pct}% ({ops_score}/{ops_checks})", sev,
                       "Pilar 5 — Automação, monitoramento, melhoria contínua."))

    # Score geral WAF
    overall = round((sec_pct + rel_pct + perf_pct + cost_pct + ops_pct) / 5)
    sev = Severity.PASS if overall >= 75 else Severity.WARNING if overall >= 50 else Severity.ERROR
    report.add(Finding(cat, f"WAF Score Geral: {overall}%", sev,
                       f"Média dos 5 pilares: Seg={sec_pct}% Conf={rel_pct}% Perf={perf_pct}% "
                       f"Custo={cost_pct}% Ops={ops_pct}%"))


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

    # Mapa de verificações — Core + Quality Gate
    checks = {
        # Core (v1.0)
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
        # Quality Gate (v2.0)
        "dados_sensiveis": lambda: check_sensitive_data(report),
        "higiene": lambda: check_file_hygiene(report),
        "documentacao": lambda: check_documentation(report),
        "disclaimer": lambda: check_disclaimer(report, html, js),
        "waf": lambda: check_waf(report, html, js),
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
    lines.append("  NossoDireito — Quality Gate — Relatório de Qualidade")
    lines.append("=" * 70)
    lines.append(f"  Data: {report.timestamp}")
    lines.append(f"  Versão Quality Gate: {report.versao_codereview}")
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
    """Entry point CLI — suporta modo CI com score mínimo."""
    import argparse
    import sys

    ALL_CATEGORIES = [
        "lgpd", "seguranca", "qualidade", "confiabilidade",
        "performance", "transparencia", "versionamento",
        "modularidade", "acessibilidade", "instituicoes", "schema",
        "dados_sensiveis", "higiene", "documentacao", "disclaimer", "waf",
    ]

    parser = argparse.ArgumentParser(
        description="NossoDireito Quality Gate — Pipeline de qualidade pré-deploy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python codereview.py                     # Revisão completa (17 categorias)
  python codereview.py --categoria lgpd    # Só LGPD
  python codereview.py --json              # Saída JSON
  python codereview.py --ci                # Modo CI (exit code 1 se falhar)
  python codereview.py --min-score 80      # Score mínimo para CI
  python codereview.py --check-links       # Verifica URLs (mais lento)
        """,
    )
    parser.add_argument(
        "--categoria", "-c",
        action="append",
        choices=ALL_CATEGORIES,
        help="Categoria específica para verificar (pode repetir)",
    )
    parser.add_argument("--json", "-j", action="store_true",
                        help="Saída em formato JSON")
    parser.add_argument("--check-links", "-l", action="store_true",
                        help="Verificar se URLs estão acessíveis (mais lento)")
    parser.add_argument("--ci", action="store_true",
                        help="Modo CI — exit code 1 se score < min-score ou CRITICAL encontrado")
    parser.add_argument("--min-score", type=float, default=75.0,
                        help="Score mínimo para o modo CI (padrão: 75.0)")

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
            "ci_passed": report.score_total >= args.min_score,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(format_report_text(report))

    # Modo CI: verificar resultado
    if args.ci:
        criticals = sum(1 for f in report.achados if f.severidade == Severity.CRITICAL)
        if criticals > 0:
            print(f"\n🚫 QUALITY GATE FALHOU: {criticals} achado(s) CRITICAL encontrado(s).")
            sys.exit(1)
        if report.score_total < args.min_score:
            print(f"\n🚫 QUALITY GATE FALHOU: Score {report.score_total} < mínimo {args.min_score}")
            sys.exit(1)
        print(f"\n✅ QUALITY GATE PASSOU: Score {report.score_total} >= {args.min_score} (0 CRITICAL)")
        sys.exit(0)


if __name__ == "__main__":
    main()
