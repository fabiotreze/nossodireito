#!/usr/bin/env python3
"""Build data/municipios_br.json from the public IBGE municipios endpoint.

Output schema (kept intentionally minimal to keep the gzipped payload small):

    {
      "fonte": "https://servicodados.ibge.gov.br/api/v1/localidades/municipios",
      "gerado_em": "YYYY-MM-DD",
      "total": <int>,
      "municipios": [
        { "id": <ibge_id>, "n": "<nome>", "u": "<uf>", "k": "<nome_normalizado>" }
      ]
    }

`k` is a search key: lowercase, NFD-stripped of accents, apostrophes and dashes
removed (e.g. "Alta Floresta D'Oeste" -> "alta floresta doeste"). This mirrors
the normalization done client-side in detectLocation() and lets the browser
match user input without re-normalizing 5.5k entries on every keystroke.

Run:
    python3 scripts/build_municipios.py
"""

from __future__ import annotations

import datetime as _dt
import gzip
import io
import json
import sys
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "municipios_br.json"
SRC = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"


def _normalize(name: str) -> str:
    """lowercase + strip accents + remove apostrophes/dashes/extra spaces."""
    s = unicodedata.normalize("NFD", name)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    for ch in ("'", "-", "."):
        s = s.replace(ch, "")
    return " ".join(s.split())


def _fetch(url: str) -> list[dict]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "nossodireito/1.0", "Accept-Encoding": "gzip"},
    )
    # nosec B310 - public IBGE endpoint, HTTPS
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        return json.loads(data.decode("utf-8"))


def main() -> int:
    print(f"[municipios] fetch {SRC}")
    raw = _fetch(SRC)
    print(f"[municipios] total bruto: {len(raw)}")

    out: list[dict] = []
    for m in raw:
        try:
            uf = m["microrregiao"]["mesorregiao"]["UF"]["sigla"]
        except (KeyError, TypeError):
            continue
        nome = m.get("nome", "").strip()
        if not nome or not uf:
            continue
        out.append({
            "id": m["id"],
            "n": nome,
            "u": uf,
            "k": _normalize(nome),
        })

    # Sort by (uf, nome) for deterministic diffs.
    out.sort(key=lambda x: (x["u"], x["k"]))

    payload = {
        "fonte": SRC,
        "gerado_em": _dt.date.today().isoformat(),
        "total": len(out),
        "municipios": out,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    # Compact (no spaces) — typical gzip transport will shrink it further.
    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(
        f"[municipios] gravado: {OUT} ({OUT.stat().st_size:,} bytes, {len(out)} municípios)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
