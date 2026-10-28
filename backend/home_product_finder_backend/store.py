"""Comparison access: the single data source is the JSON files in vault/confronti/.

No database: each comparison is a JSON file (see scripts/build_confronti_json.py).
Adding a comparison = adding a JSON file, no code changes.

Domain field names (titolo, gruppi, prodotti, stato, ...) are Italian on purpose:
they mirror the vault JSON schema, which is the persisted source of truth.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent
CONFRONTI_DIR = ROOT / "vault" / "confronti"
IMAGES_DIR = CONFRONTI_DIR / "images"
SCRAPE_DIR = CONFRONTI_DIR / "_scrape"
LOG_FILE = ROOT / "vault" / "log.md"


def _path(slug: str) -> Path:
    return CONFRONTI_DIR / f"{slug}.json"


def list_confronti() -> list[dict]:
    """Summary of every available comparison (for the home page)."""
    out: list[dict] = []
    for p in sorted(CONFRONTI_DIR.glob("*.json")):
        data = _read(p.stem)
        prodotti = [pr for g in data["gruppi"] for pr in g["prodotti"]]
        out.append({
            "slug": data["slug"],
            "titolo": data["titolo"],
            "sottotitolo": data.get("sottotitolo", ""),
            "metrica": data.get("metrica", ""),
            "n_prodotti": len(prodotti),
            "n_da_comprare": sum(1 for pr in prodotti if pr.get("stato") == "da-comprare"),
        })
    return out


def _read(slug: str) -> dict:
    path = _path(slug)
    if not path.exists():
        raise FileNotFoundError(slug)
    return json.loads(path.read_text(encoding="utf-8"))


def get_confronto(slug: str) -> dict:
    return _read(slug)


def _write(slug: str, data: dict) -> None:
    _path(slug).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def set_scelta(slug: str, selezioni: dict[str, int]) -> dict:
    """Mark chosen products as `da-comprare` with quantities; reset the others.

    `selezioni` = {product_id: quantity}. Writes to the vault JSON and logs the choice.
    """
    data = _read(slug)
    scelti: list[str] = []
    for gruppo in data["gruppi"]:
        for prod in gruppo["prodotti"]:
            qty = selezioni.get(prod["id"])
            if qty and qty > 0:
                prod["stato"] = "da-comprare"
                prod["quantita"] = int(qty)
                scelti.append(f"{prod['nome']} x{int(qty)}")
            else:
                prod["stato"] = None
                prod["quantita"] = 1
    _write(slug, data)
    _log_scelta(data["titolo"], scelti)
    logger.info("choice %s: %s", slug, scelti or "(none)")
    return data


def _log_scelta(titolo: str, scelti: list[str]) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    body = "; ".join(scelti) if scelti else "(selezione svuotata)"
    line = f"\n- **{stamp}** — scelta confronto «{titolo}» → da-comprare: {body}\n"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)


def lista_acquisti() -> list[dict]:
    """All `da-comprare` products across every comparison (shopping list)."""
    out: list[dict] = []
    for p in sorted(CONFRONTI_DIR.glob("*.json")):
        data = _read(p.stem)
        for gruppo in data["gruppi"]:
            for prod in gruppo["prodotti"]:
                if prod.get("stato") == "da-comprare":
                    out.append({
                        "confronto": data["titolo"], "slug": data["slug"],
                        "gruppo": gruppo["nome"], "nome": prod["nome"],
                        "negozio": prod["negozio"], "prezzo": prod["prezzo"],
                        "quantita": prod.get("quantita", 1), "link": prod.get("link"),
                        "immagine": prod.get("immagine"),
                    })
    return out
