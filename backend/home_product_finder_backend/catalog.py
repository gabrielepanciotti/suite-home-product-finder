"""Box catalogue: the flat list of every box scraped from the shop CLIs.

Source of truth = the raw JSON dumps in `vault/confronti/_scrape/`, produced by
`scripts/shopcli.py` (one file per shop+query, each a list of products with
`shop, nome, prezzo, a, b, h, link, img`). This module only reads and normalizes
them; nothing here writes.

Difference from `store.py`: that one serves the *curated* comparisons (grouped,
selectable, persisted choices). This one serves the *raw catalogue* — everything
available, so a box can be filtered by its own dimensions before any comparison
exists. Adding a shop query = adding a scrape file, no code change.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from . import attributi, store

logger = logging.getLogger(__name__)

CLASSI_FILE = store.ROOT / "vault" / "catalogo-classi.json"


def _regole() -> dict:
    if not CLASSI_FILE.exists():
        return {}
    try:
        return json.loads(CLASSI_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.warning("vault/catalogo-classi.json unreadable: nothing is filtered")
        return {}


def classifica_item(item: dict, regole: dict) -> tuple[str, str]:
    """(classe, perche) — is this row actually a box?

    Broad category scrapes (`cat:casalinghi`) drag in whatever the department
    sells: a sink plunger 13.5x14x40 has three dimensions and a price, so it
    ranks as a container unless something says otherwise. Decision order, most
    specific first: an explicit decision on the product, then the category it
    came from, then the words in its name. What none of these settle comes back
    as `da-classificare` — an invitation to decide once, not a silent guess.
    """
    decisione = (regole.get("decisioni") or {}).get(item["id"])
    if decisione is not None:
        classe = "scatola" if decisione.get("scatola") else "non-scatola"
        return classe, decisione.get("perche", "decisione manuale")

    nome = item["nome"].lower()
    for parola in regole.get("nome_esclude", []):
        if parola in nome:
            return "non-scatola", f"nome contiene «{parola}»"

    categorie_ok = set(regole.get("categorie_scatola", []))
    da_categoria = sorted(categorie_ok.intersection(item["fonti"]))
    if da_categoria:
        return "scatola", f"categoria {da_categoria[0]}"

    for parola in regole.get("nome_include", []):
        if parola in nome:
            return "scatola", f"nome contiene «{parola}»"

    return "da-classificare", "categoria larga e nome non conclusivo"


def _volume_litri(a: float, b: float, h: float) -> float:
    """Gross volume from the external dimensions, in litres (cm3 / 1000)."""
    return round(a * b * h / 1000, 1)


def _normalize(raw: dict, fonte: str) -> dict | None:
    """One scrape row -> one catalogue item, or None when unusable.

    A row is unusable without the three dimensions: the whole point of the
    catalogue is filtering by size (e.g. "internal height >= 22 cm for the
    Bormioli jars"), so a dimensionless row would only be noise.
    """
    try:
        a, b, h = float(raw["a"]), float(raw["b"]), float(raw["h"])
        prezzo = float(raw["prezzo"])
    except (KeyError, TypeError, ValueError):
        return None
    if min(a, b, h) <= 0:
        return None

    volume = _volume_litri(a, b, h)
    return {
        "id": raw.get("link") or f"{raw.get('shop')}:{raw.get('nome')}",
        "nome": (raw.get("nome") or "").strip(),
        "negozio": raw.get("shop") or "?",
        "prezzo": prezzo,
        "a": a,
        "b": b,
        "h": h,
        "volume_l": volume,
        # Value metric of the storage domain (see scatole-vestiti-confronto.md).
        "eur_per_l": round(prezzo / volume, 3) if volume else None,
        "link": raw.get("link") or None,
        "img": raw.get("img") or None,
        "fonti": [fonte],
    }


def _merge(existing: dict, new: dict) -> None:
    """Fold a duplicate row into the one already kept.

    The same product surfaces under several queries with names of varying
    completeness ("Contenitore" vs "Contenitore 19 litri | 39x29x26 cm"): keep
    the most informative name and the first image found, and remember every
    query that returned it.
    """
    if len(new["nome"]) > len(existing["nome"]):
        existing["nome"] = new["nome"]
    if not existing["img"] and new["img"]:
        existing["img"] = new["img"]
    if new["fonti"][0] not in existing["fonti"]:
        existing["fonti"].append(new["fonti"][0])


def list_catalogo() -> list[dict]:
    """Every scraped box, deduplicated by product link, cheapest first."""
    # Read through the module (not a from-import): tests repoint store.SCRAPE_DIR.
    scrape_dir = store.SCRAPE_DIR
    if not scrape_dir.exists():
        return []

    items: dict[str, dict] = {}
    for path in sorted(scrape_dir.glob("*.json")):
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("scrape file unreadable, skipped: %s", path.name)
            continue
        if not isinstance(rows, list):
            continue
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            item = _normalize(raw, path.stem)
            if item is None:
                continue
            if item["id"] in items:
                _merge(items[item["id"]], item)
            else:
                items[item["id"]] = item

    regole = _regole()
    # Attributes are read after the merge, never before: the merge keeps the
    # longest name, and the longest name is exactly the one that spells out the
    # lid and the material.
    regole_attributi = attributi.regole()
    for item in items.values():
        item["classe"], item["classe_perche"] = classifica_item(item, regole)
        item.update(attributi.leggi(item["nome"], regole_attributi))

    return sorted(items.values(), key=lambda i: i["prezzo"])


def solo_scatole(items: list[dict]) -> list[dict]:
    """Rows safe to tessellate with: what is a box, plus what is still unknown.

    The undecided stay in — excluding them would hide real boxes behind a
    labelling gap — but they carry `classe` so the UI can flag them.
    """
    return [i for i in items if i["classe"] != "non-scatola"]


def catalogo_negozi() -> list[dict]:
    """Per-shop row counts, so the UI can render filters without counting."""
    counts: dict[str, int] = {}
    for item in list_catalogo():
        counts[item["negozio"]] = counts.get(item["negozio"], 0) + 1
    return [{"negozio": k, "n": v} for k, v in sorted(counts.items())]
