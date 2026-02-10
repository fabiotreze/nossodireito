#!/usr/bin/env python3
"""
validate_sources.py — Validação Automática de Fontes Oficiais
=============================================================

Valida os dados do NossoDireito contra APIs oficiais:

  1. URLs       — HTTP HEAD em todas as URLs do direitos.json (links quebrados)
  2. Legislação — Senado Federal Dados Abertos (leis vigentes)
  3. CID        — OMS ICD API (códigos CID-10 e CID-11 válidos)

Uso:
    python scripts/validate_sources.py                  # Roda tudo (URLs + Senado)
    python scripts/validate_sources.py --urls            # Só URLs
    python scripts/validate_sources.py --legislacao      # Só legislação (Senado API)
    python scripts/validate_sources.py --cid             # Só CID (ICD API — requer credenciais)
    python scripts/validate_sources.py --update-dates    # Atualiza consultado_em das fontes válidas
    python scripts/validate_sources.py --json            # Saída em JSON

Credenciais ICD API (para --cid):
    Crie um arquivo .env na raiz do projeto com:
        ICD_CLIENT_ID=<seu_client_id>
        ICD_CLIENT_SECRET=<seu_client_secret>
    Ou exporte como variáveis de ambiente.
    Registre-se em: https://icd.who.int/icdapi

Autor: NossoDireito — Projeto sem fins lucrativos
Licença: MIT
"""

from __future__ import annotations

import http.client
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# ─── Constantes ─────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent


def _load_dotenv() -> None:
    """Carrega variáveis do .env (sem dependências externas)."""
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv()
DATA_JSON = PROJECT_ROOT / "data" / "direitos.json"

# APIs oficiais
SENADO_API = "https://legis.senado.leg.br/dadosabertos"
ICD_TOKEN_URL = "https://icdaccessmanagement.who.int/connect/token"
ICD_API_BASE = "https://id.who.int/icd"

# Timeout padrão para HTTP
HTTP_TIMEOUT = 15

# Rate limiting
RATE_LIMIT_DELAY = 0.3  # segundos entre requests

# User-Agent mais compatível (planalto.gov.br bloqueia bots)
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


# ─── Modelos ────────────────────────────────────────────────────────
@dataclass
class ValidationResult:
    """Resultado de uma validação individual."""
    source: str       # "url", "legislacao", "cid"
    item: str         # nome/identificador
    status: str       # "ok", "warning", "error"
    message: str
    url: str = ""
    http_code: int = 0


@dataclass
class ValidationReport:
    """Relatório agregado de validação."""
    timestamp: str = field(default_factory=lambda: date.today().isoformat())
    results: list[ValidationResult] = field(default_factory=list)

    @property
    def ok_count(self) -> int:
        return sum(1 for r in self.results if r.status == "ok")

    @property
    def warning_count(self) -> int:
        return sum(1 for r in self.results if r.status == "warning")

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.status == "error")

    def add(self, result: ValidationResult) -> None:
        self.results.append(result)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "total": len(self.results),
            "ok": self.ok_count,
            "warnings": self.warning_count,
            "errors": self.error_count,
            "results": [
                {
                    "source": r.source,
                    "item": r.item,
                    "status": r.status,
                    "message": r.message,
                    "url": r.url,
                    "http_code": r.http_code,
                }
                for r in self.results
            ],
        }


# ─── Helpers ────────────────────────────────────────────────────────
def load_json() -> dict:
    """Carrega o direitos.json."""
    try:
        with open(DATA_JSON, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Erro ao carregar {DATA_JSON}: {e}")
        sys.exit(1)


def save_json(data: dict) -> None:
    """Salva direitos.json com formatação brasileira."""
    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"💾 {DATA_JSON.name} atualizado.")


def _make_request(url: str, method: str = "GET", headers: dict | None = None,
                  data: bytes | None = None, timeout: int = HTTP_TIMEOUT) -> tuple[int, str]:
    """Faz request HTTP e retorna (status_code, body)."""
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, method=method, headers=headers or {}, data=data)
    if "User-Agent" not in (headers or {}):
        req.add_header("User-Agent", BROWSER_UA)
    req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
    req.add_header("Accept-Language", "pt-BR,pt;q=0.9,en;q=0.8")
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            try:
                body = resp.read().decode("utf-8", errors="replace")
            except http.client.IncompleteRead as ir:
                body = ir.partial.decode("utf-8", errors="replace")
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, ""
    except (urllib.error.URLError, TimeoutError, OSError, http.client.IncompleteRead) as e:
        return 0, str(e)


def _http_head(url: str, timeout: int = HTTP_TIMEOUT) -> tuple[int, str]:
    """HEAD request — mais rápido para checar se URL existe."""
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, method="HEAD")
    req.add_header("User-Agent", BROWSER_UA)
    req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
    req.add_header("Accept-Language", "pt-BR,pt;q=0.9,en;q=0.8")
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.status, ""
    except urllib.error.HTTPError as e:
        # Alguns sites bloqueiam HEAD — tenta GET como fallback
        if e.code in (403, 405, 406):
            return _make_request(url, timeout=timeout)
        return e.code, ""
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        # Connection reset — retry com GET (planalto.gov.br bloqueia HEAD)
        if "Connection reset" in str(e) or "Errno 54" in str(e):
            return _make_request(url, timeout=timeout)
        return 0, str(e)


# ─── Extração de URLs ──────────────────────────────────────────────
def extract_all_urls(json_data: dict) -> list[dict]:
    """Extrai todas as URLs do direitos.json com contexto."""
    urls = []

    # Fontes
    for fonte in json_data.get("fontes", []):
        url = fonte.get("url", "")
        if url and url.startswith("http"):
            urls.append({
                "url": url,
                "section": "fontes",
                "name": fonte.get("nome", ""),
                "consultado_em": fonte.get("consultado_em", ""),
            })

    # Instituições
    for inst in json_data.get("instituicoes", []):
        url = inst.get("url", "")
        if url and url.startswith("http"):
            urls.append({
                "url": url,
                "section": "instituicoes",
                "name": inst.get("nome", ""),
            })

    # Órgãos estaduais
    for orgao in json_data.get("orgaos_estaduais", []):
        url = orgao.get("url", "")
        if url and url.startswith("http"):
            urls.append({
                "url": url,
                "section": "orgaos_estaduais",
                "name": f"{orgao.get('uf', '')} — {orgao.get('nome', '')}",
            })

    # Categorias — base_legal + links
    for cat in json_data.get("categorias", []):
        for bl in cat.get("base_legal", []):
            url = bl.get("link", "")
            if url and url.startswith("http"):
                urls.append({
                    "url": url,
                    "section": f"categorias.{cat.get('id', '')}.base_legal",
                    "name": bl.get("lei", ""),
                })
        for lk in cat.get("links", []):
            url = lk.get("url", "")
            if url and url.startswith("http"):
                urls.append({
                    "url": url,
                    "section": f"categorias.{cat.get('id', '')}.links",
                    "name": lk.get("titulo", ""),
                })

    # Deduplica por URL
    seen = set()
    deduped = []
    for item in urls:
        if item["url"] not in seen:
            seen.add(item["url"])
            deduped.append(item)

    return deduped


# ─── 1. Validar URLs (HTTP HEAD) ───────────────────────────────────
def validate_urls(report: ValidationReport, json_data: dict) -> None:
    """Testa todas as URLs com HTTP HEAD/GET."""
    all_urls = extract_all_urls(json_data)
    print(f"\n🔗 Validando {len(all_urls)} URLs...")
    print("-" * 60)

    for i, item in enumerate(all_urls, 1):
        url = item["url"]
        name = item["name"][:50]

        # Skip tel: e mailto:
        if not url.startswith("http"):
            continue

        status, _ = _http_head(url)

        if 200 <= status < 400:
            report.add(ValidationResult(
                source="url", item=name, status="ok",
                message=f"HTTP {status}", url=url, http_code=status,
            ))
            icon = "✅"
        elif 400 <= status < 500:
            report.add(ValidationResult(
                source="url", item=name, status="error",
                message=f"HTTP {status} — página não encontrada",
                url=url, http_code=status,
            ))
            icon = "❌"
        elif status >= 500:
            report.add(ValidationResult(
                source="url", item=name, status="warning",
                message=f"HTTP {status} — erro do servidor (pode ser temporário)",
                url=url, http_code=status,
            ))
            icon = "⚠️"
        else:
            report.add(ValidationResult(
                source="url", item=name, status="error",
                message=f"Falha na conexão: {_[:80] if _ else 'timeout'}",
                url=url, http_code=0,
            ))
            icon = "❌"

        print(f"  [{i:3d}/{len(all_urls)}] {icon} {name:<50} → HTTP {status or 'FAIL'}")
        time.sleep(RATE_LIMIT_DELAY)


# ─── 2. Validar Legislação (Senado Dados Abertos) ──────────────────
def _parse_lei_number(nome: str) -> tuple[str, str, str] | None:
    """Extrai tipo, número e ano de uma referência legislativa.

    Exemplos:
        "Lei 13.146/2015" → ("LEI", "13146", "2015")
        "Lei 8.036/1990"  → ("LEI", "8036", "1990")
        "Decreto 5.296/2004" → ("DEC", "5296", "2004")
    """
    # Padrão: Lei/Decreto + número (com pontos opcionais) + /ano
    m = re.search(
        r"(Lei|Decreto|Lei Complementar)\s+(?:n[ºo°]\s*)?(\d[\d.]*)/(\d{4})",
        nome,
        re.IGNORECASE,
    )
    if not m:
        return None

    tipo_raw = m.group(1).lower()
    numero = m.group(2).replace(".", "")
    ano = m.group(3)

    tipo_map = {
        "lei": "LEI",
        "decreto": "DEC",
        "lei complementar": "LCP",
    }
    tipo = tipo_map.get(tipo_raw, "LEI")
    return tipo, numero, ano


def validate_legislacao(report: ValidationReport, json_data: dict) -> None:
    """Valida leis no Senado Federal Dados Abertos."""
    fontes = json_data.get("fontes", [])
    leis = [f for f in fontes if f.get("tipo") == "legislacao"]

    print(f"\n⚖️  Validando {len(leis)} leis no Senado Federal Dados Abertos...")
    print("-" * 60)

    for i, fonte in enumerate(leis, 1):
        nome = fonte.get("nome", "")[:60]

        # ── Caso especial: Constituição Federal ──────────────
        if "constitui" in fonte.get("nome", "").lower():
            cf_url = "https://www.planalto.gov.br/ccivil_03/Constituicao/Constituicao.htm"
            cf_status, _ = _make_request(cf_url)
            if cf_status and 200 <= cf_status < 400:
                report.add(ValidationResult(
                    source="legislacao", item=nome, status="ok",
                    message="Constituição Federal vigente — verificada via planalto.gov.br",
                    url=cf_url, http_code=cf_status,
                ))
                print(f"  [{i:3d}/{len(leis)}] ✅ {nome:<60} → CF/88 vigente (planalto.gov.br)")
            else:
                report.add(ValidationResult(
                    source="legislacao", item=nome, status="warning",
                    message=f"Planalto retornou HTTP {cf_status} — verifique manualmente",
                    url=cf_url, http_code=cf_status,
                ))
                print(f"  [{i:3d}/{len(leis)}] ⚠️  {nome:<60} → HTTP {cf_status}")
            time.sleep(RATE_LIMIT_DELAY)
            continue

        parsed = _parse_lei_number(fonte.get("nome", ""))

        if not parsed:
            report.add(ValidationResult(
                source="legislacao", item=nome, status="warning",
                message="Não foi possível extrair tipo/número/ano para consultar API",
            ))
            print(f"  [{i:3d}/{len(leis)}] ⏭️  {nome:<60} (sem número extraível)")
            continue

        tipo, numero, ano = parsed
        api_url = f"{SENADO_API}/legislacao/{tipo}/{numero}/{ano}.json"

        status, body = _make_request(api_url, headers={"Accept": "application/json"})

        if status == 200 and body:
            try:
                data = json.loads(body)
                # O Senado retorna uma estrutura com DetalheNormaJuridica
                norma = (data.get("DetalheNormaJuridica", {})
                         .get("Norma", {}))
                situacao = norma.get("SituacaoNorma", {}).get("DescricaoSituacao", "")
                ementa = norma.get("EmentaNorma", "")[:80]

                if situacao.lower() in ("em vigor", "vigente", ""):
                    report.add(ValidationResult(
                        source="legislacao", item=nome, status="ok",
                        message=f"Encontrada no Senado — {situacao or 'vigente'}. {ementa}",
                        url=api_url, http_code=200,
                    ))
                    icon = "✅"
                elif "revogad" in situacao.lower():
                    report.add(ValidationResult(
                        source="legislacao", item=nome, status="error",
                        message=f"⚠️ LEI REVOGADA — {situacao}. Atualize o direitos.json!",
                        url=api_url, http_code=200,
                    ))
                    icon = "🚨"
                else:
                    report.add(ValidationResult(
                        source="legislacao", item=nome, status="warning",
                        message=f"Situação: {situacao}. Verifique manualmente.",
                        url=api_url, http_code=200,
                    ))
                    icon = "⚠️"
            except (json.JSONDecodeError, KeyError, TypeError):
                report.add(ValidationResult(
                    source="legislacao", item=nome, status="ok",
                    message="Encontrada na API (resposta não-padrão — verificar manualmente)",
                    url=api_url, http_code=200,
                ))
                icon = "✅"
        elif status == 404:
            report.add(ValidationResult(
                source="legislacao", item=nome, status="warning",
                message=f"Não encontrada na API do Senado ({tipo} {numero}/{ano}) — pode ser nomenclatura diferente",
                url=api_url, http_code=404,
            ))
            icon = "⚠️"
        else:
            report.add(ValidationResult(
                source="legislacao", item=nome, status="warning",
                message=f"API retornou HTTP {status} — verificar manualmente",
                url=api_url, http_code=status,
            ))
            icon = "⚠️"

        print(f"  [{i:3d}/{len(leis)}] {icon} {nome:<60} → {tipo} {numero}/{ano}")
        time.sleep(RATE_LIMIT_DELAY)


# ─── 3. Validar CID (OMS ICD API) ──────────────────────────────────
def _get_icd_token() -> str | None:
    """Obtém token OAuth2 da ICD API."""
    client_id = os.environ.get("ICD_CLIENT_ID", "")
    client_secret = os.environ.get("ICD_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        return None

    payload = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "icdapi_access",
        "grant_type": "client_credentials",
    }).encode("utf-8")

    status, body = _make_request(
        ICD_TOKEN_URL,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=payload,
    )

    if status == 200 and body:
        try:
            return json.loads(body).get("access_token")
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def _extract_cid_codes(classificacoes: list[dict]) -> list[dict]:
    """Extrai códigos CID individuais das classificações."""
    codes = []
    for cls in classificacoes:
        tipo = cls.get("tipo", "")
        cid10_raw = cls.get("cid10", "")
        cid11_raw = cls.get("cid11", "")

        # Skip "Combinação" e "Variados"
        if cid10_raw in ("Combinação", "Variados") or cid11_raw in ("Combinação", "Variados"):
            continue

        # CID-10: extrair primeiro código de ranges como "F70 a F79"
        cid10_codes = re.findall(r"[A-Z]\d{2}(?:\.\d)?", cid10_raw)
        for code in cid10_codes[:2]:  # limitar a 2 códigos por tipo
            codes.append({"tipo": tipo, "version": "10", "code": code})

        # CID-11: extrair códigos como "6A02", "9B50"
        cid11_codes = re.findall(r"\d[A-Z0-9]{2,4}", cid11_raw)
        for code in cid11_codes[:2]:
            codes.append({"tipo": tipo, "version": "11", "code": code})

    return codes


def validate_cid(report: ValidationReport, json_data: dict) -> None:
    """Valida códigos CID contra a ICD API da OMS."""
    classificacoes = json_data.get("classificacao_deficiencia", [])
    codes = _extract_cid_codes(classificacoes)

    print(f"\n🏥 Validando {len(codes)} códigos CID na ICD API (OMS)...")
    print("-" * 60)

    token = _get_icd_token()
    if not token:
        print("  ⚠️  Credenciais ICD API não configuradas.")
        print("  ℹ️  Para validar CID, crie .env na raiz do projeto com:")
        print("      ICD_CLIENT_ID=<seu_client_id>")
        print("      ICD_CLIENT_SECRET=<seu_client_secret>")
        print("  📝 Registre-se em: https://icd.who.int/icdapi")
        print("")
        report.add(ValidationResult(
            source="cid", item="ICD API",
            status="warning",
            message="Credenciais não configuradas — validação CID ignorada. "
                    "Registre-se em https://icd.who.int/icdapi",
        ))
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Accept-Language": "pt",
        "API-Version": "v2",
    }

    for i, entry in enumerate(codes, 1):
        tipo = entry["tipo"][:30]
        version = entry["version"]
        code = entry["code"]

        if version == "11":
            # CID-11 usa linearization MMS
            api_url = f"{ICD_API_BASE}/release/11/2024-01/mms/codeinfo/{code}"
        else:
            # CID-10 usa release 2019
            api_url = f"{ICD_API_BASE}/release/10/2019/{code}"

        status_code, body = _make_request(api_url, headers=headers)

        if status_code == 200 and body:
            try:
                data = json.loads(body)
                title = data.get("title", {})
                if isinstance(title, dict):
                    name = title.get("@value", code)
                elif isinstance(title, str):
                    name = title
                else:
                    name = code

                report.add(ValidationResult(
                    source="cid", item=f"{tipo} — CID-{version}: {code}",
                    status="ok",
                    message=f"Válido: {name[:60]}",
                    url=api_url, http_code=200,
                ))
                icon = "✅"
                label = name[:40]
            except (json.JSONDecodeError, KeyError):
                report.add(ValidationResult(
                    source="cid", item=f"{tipo} — CID-{version}: {code}",
                    status="ok",
                    message="Encontrado na API (resposta não-padrão)",
                    url=api_url, http_code=200,
                ))
                icon = "✅"
                label = "(resposta ok)"
        elif status_code == 404:
            report.add(ValidationResult(
                source="cid", item=f"{tipo} — CID-{version}: {code}",
                status="error",
                message=f"Código CID-{version} '{code}' NÃO encontrado na ICD API",
                url=api_url, http_code=404,
            ))
            icon = "❌"
            label = "NÃO ENCONTRADO"
        else:
            report.add(ValidationResult(
                source="cid", item=f"{tipo} — CID-{version}: {code}",
                status="warning",
                message=f"API retornou HTTP {status_code}",
                url=api_url, http_code=status_code,
            ))
            icon = "⚠️"
            label = f"HTTP {status_code}"

        print(f"  [{i:3d}/{len(codes)}] {icon} CID-{version} {code:<8} ({tipo:<30}) → {label}")
        time.sleep(RATE_LIMIT_DELAY)


# ─── 4. Atualizar datas de consulta ────────────────────────────────
def update_consultation_dates(json_data: dict, report: ValidationReport) -> dict:
    """Atualiza 'consultado_em' para fontes que passaram na validação de URL."""
    today = date.today().isoformat()
    updated_count = 0

    ok_urls = {r.url for r in report.results if r.source == "url" and r.status == "ok"}

    for fonte in json_data.get("fontes", []):
        url = fonte.get("url", "")
        if url in ok_urls:
            old_date = fonte.get("consultado_em", "")
            if old_date != today:
                fonte["consultado_em"] = today
                updated_count += 1

    if updated_count > 0:
        # Atualizar ultima_atualizacao do JSON principal
        json_data["ultima_atualizacao"] = today
        print(f"\n📅 Atualizou 'consultado_em' de {updated_count} fontes para {today}")
    else:
        print("\n📅 Nenhuma data de consulta precisou ser atualizada.")

    return json_data


# ─── Relatório ──────────────────────────────────────────────────────
def format_report(report: ValidationReport) -> str:
    """Formata o relatório como texto."""
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("  NossoDireito — Validação de Fontes Oficiais")
    lines.append("=" * 70)
    lines.append(f"  Data: {report.timestamp}")
    lines.append(f"  Total: {len(report.results)} verificações")
    lines.append(f"  ✅ OK: {report.ok_count}  ⚠️ Avisos: {report.warning_count}  ❌ Erros: {report.error_count}")
    lines.append("=" * 70)

    # Agrupar por source
    for source in ("url", "legislacao", "cid"):
        source_results = [r for r in report.results if r.source == source]
        if not source_results:
            continue

        labels = {"url": "🔗 URLs", "legislacao": "⚖️  Legislação", "cid": "🏥 CID"}
        lines.append(f"\n{labels.get(source, source)}:")
        lines.append("-" * 50)

        ok = sum(1 for r in source_results if r.status == "ok")
        warn = sum(1 for r in source_results if r.status == "warning")
        err = sum(1 for r in source_results if r.status == "error")
        lines.append(f"  ✅ {ok}  ⚠️ {warn}  ❌ {err}")

        # Mostrar apenas warnings e errors
        for r in source_results:
            if r.status != "ok":
                icon = "⚠️" if r.status == "warning" else "❌"
                lines.append(f"  {icon} {r.item}")
                lines.append(f"     {r.message}")
                if r.url:
                    lines.append(f"     🔗 {r.url}")

    lines.append("")
    score = report.ok_count / max(len(report.results), 1) * 100
    emoji = "🏆" if score >= 90 else "⚠️" if score >= 70 else "❌"
    lines.append(f"  Score de Validação: {emoji} {score:.1f}%")
    lines.append("=" * 70)

    return "\n".join(lines)


# ─── CLI ────────────────────────────────────────────────────────────
def main() -> None:
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="NossoDireito — Validação de Fontes Oficiais",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python scripts/validate_sources.py                  # Tudo (URLs + Legislação)
  python scripts/validate_sources.py --urls            # Só URLs (HTTP HEAD)
  python scripts/validate_sources.py --legislacao      # Só legislação (Senado API)
  python scripts/validate_sources.py --cid             # Só CID (ICD API — requer credenciais)
  python scripts/validate_sources.py --all             # URLs + Legislação + CID
  python scripts/validate_sources.py --update-dates    # Atualiza datas das fontes válidas
  python scripts/validate_sources.py --json            # Saída JSON
        """,
    )
    parser.add_argument("--urls", action="store_true", help="Validar URLs (HTTP HEAD)")
    parser.add_argument("--legislacao", action="store_true", help="Validar leis no Senado Dados Abertos")
    parser.add_argument("--cid", action="store_true", help="Validar CID na ICD API (requer credenciais)")
    parser.add_argument("--all", action="store_true", help="Executar todas as validações")
    parser.add_argument("--update-dates", action="store_true", help="Atualizar consultado_em das fontes válidas")
    parser.add_argument("--json", action="store_true", help="Saída em JSON")

    args = parser.parse_args()

    # Default: URLs + legislação
    run_urls = args.urls or args.all or (not args.urls and not args.legislacao and not args.cid)
    run_leg = args.legislacao or args.all or (not args.urls and not args.legislacao and not args.cid)
    run_cid = args.cid or args.all

    json_data = load_json()
    report = ValidationReport()

    print("=" * 70)
    print("  NossoDireito — Validação de Fontes Oficiais")
    print("=" * 70)

    if run_urls:
        validate_urls(report, json_data)

    if run_leg:
        validate_legislacao(report, json_data)

    if run_cid:
        validate_cid(report, json_data)

    # Atualizar datas se solicitado
    if args.update_dates:
        json_data = update_consultation_dates(json_data, report)
        save_json(json_data)

    # Output
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(format_report(report))

    # Exit code: 1 se houver erros
    if report.error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
