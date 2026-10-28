"""Per-compartment verdicts: which boxes are kept in mind, which are ruled out.

The ranking is computed, the verdict is not. Looking at 96 solutions for one
shelf and deciding "this one interests me, that one never" is work: it must
survive a reload, and it must live where the rest of this node's decisions live
— in the vault, as readable JSON — not in the browser's local storage where the
other device would never see it.

Shape (`vault/preferenze-vani.json`):

    {"vani": {"<spazio>/<vano>": {"preferiti": ["NOME"], "scartati": ["NOME"]}}}

Boxes are keyed by name because that is already the identity used to deduplicate
the ranking in `spazi.py`. Nothing here decides anything: it stores what the
person decided.
"""
from __future__ import annotations

import json
import logging

from . import store

logger = logging.getLogger(__name__)

PREFERENZE_FILE = store.ROOT / "vault" / "preferenze-vani.json"


def leggi() -> dict:
    """Every verdict, or an empty set of them. Never raises: this is a UI aid."""
    if not PREFERENZE_FILE.exists():
        return {"vani": {}}
    try:
        dati = json.loads(PREFERENZE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.warning("vault/preferenze-vani.json unreadable: starting empty")
        return {"vani": {}}
    return {"vani": dati.get("vani", {})}


def scrivi_vano(chiave: str, preferiti: list[str], scartati: list[str]) -> dict:
    """Replace one compartment's verdicts, leaving the others untouched.

    Whole-compartment replacement rather than add/remove deltas: the client
    already holds the full state of the table it is looking at, and a replace
    cannot drift out of sync the way a sequence of deltas can.
    """
    dati = leggi()
    entry = {"preferiti": preferiti, "scartati": scartati}
    if preferiti or scartati:
        dati["vani"][chiave] = entry
    else:
        # An emptied compartment leaves no trace: no rows of `{"preferiti": []}`
        # accumulating in the vault for every table ever opened.
        dati["vani"].pop(chiave, None)

    PREFERENZE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = PREFERENZE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(dati, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(PREFERENZE_FILE)
    return dati
