"""Box characteristics read out of the product name.

The shop CLIs return a name, a price, three dimensions and a link — nothing
else. But the commercial name is a spec sheet in prose: "BOX CONTENITORE 24 LT
CON COPERCHIO E RUOTE 60X40X18,5 CM" already says lid, wheels and plastic. This
module turns that prose into fields the table can show, sort and filter on.

Two rules keep it honest:

* **Absence is not a negation.** A name that never mentions a lid gives
  `coperchio = None` (unknown), not `False`. "SENZA COPERCHIO" gives `False`.
  Guessing "no lid" from silence would quietly rank IKEA boxes as open crates.
* **The vocabulary lives in the vault** (`vault/catalogo-attributi.json`), like
  the box/non-box rules: adding a material is editing data, not code. Words are
  stems — `impilabil` catches impilabile and impilabili.

Reading the prose only goes so far, and the material is where it fails: 69 of the
89 boxes that fit a jar declare nothing at all, because a name like "SAMLA
Contenitore" or "PAPPIS Scatola con coperchio" is a series name, not a
description. Hence the `nomi` table: a hand-curated list of series whose material
is a known fact, matched on the start of the name. It is knowledge, not
inference, so it wins over the word vocabulary — and it stays deliberately short.
Only add a row for something you actually know; the honest answer for the rest is
still "unknown".
"""
from __future__ import annotations

import json
import logging

from . import store

logger = logging.getLogger(__name__)

ATTRIBUTI_FILE = store.ROOT / "vault" / "catalogo-attributi.json"


def regole() -> dict:
    if not ATTRIBUTI_FILE.exists():
        return {}
    try:
        return json.loads(ATTRIBUTI_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.warning("vault/catalogo-attributi.json unreadable: no attributes")
        return {}


def _coperchio(nome: str, regole_coperchio: dict) -> bool | None:
    # Negations first: "SENZA COPERCHIO" contains "coperchio", so testing the
    # affirmative words first would turn every denial into a confirmation.
    for parola in regole_coperchio.get("no", []):
        if parola in nome:
            return False
    for parola in regole_coperchio.get("si", []):
        if parola in nome:
            return True
    return None


def _elenco(nome: str, gruppi: list[dict]) -> list[str]:
    """Every group whose vocabulary appears in the name, in declaration order."""
    trovati = []
    for gruppo in gruppi:
        if any(parola in nome for parola in gruppo.get("parole", [])):
            trovati.append(gruppo["nome"])
    return trovati


def _per_nome(testo: str, tabella: list[dict]) -> list[str] | None:
    """Curated material for a known product series, matched on the name's start.

    `startswith`, not `in`: the series name opens the commercial name ("SAMLA
    Contenitore"), and a loose substring would let "samla" fire inside an
    unrelated word. First match wins, so the table is read as an ordered list of
    rules — put the specific ones above the general.
    """
    for riga in tabella:
        if testo.startswith(riga["prefisso"].lower()):
            return list(riga.get("materiali", []))
    return None


def leggi(nome: str, regole_attributi: dict) -> dict:
    """`{coperchio, materiali, tratti}` for one product name.

    `materiali` is a list because composite products are common ("BAULE DA
    ESTERNO IN LEGNO CON COPERCHIO IN METALLO"): reporting only the first would
    be a coin toss between two true answers.
    """
    testo = nome.lower()
    noti = _per_nome(testo, regole_attributi.get("nomi", []))
    return {
        "coperchio": _coperchio(testo, regole_attributi.get("coperchio", {})),
        # Known beats inferred: the table says what the series IS, the words only
        # say what the name happens to mention.
        "materiali": (
            noti
            if noti is not None
            else _elenco(testo, regole_attributi.get("materiali", []))
        ),
        "tratti": _elenco(testo, regole_attributi.get("tratti", [])),
    }
