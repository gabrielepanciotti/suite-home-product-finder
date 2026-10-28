"""I barattoli noti, per la preselezione della pagina "In cosa lo metto".

Digitare 21,8 e 16,0 a mano è il modo più facile di sbagliare la risposta: fra un
Fido da 150 cl (⌀ 10,6) e un Quattro Stagioni 300 cl (⌀ 16,0) cambia il numero di
barattoli per scatola, quindi cambia cosa comprare. Meglio sceglierlo per nome.

Un file per produttore, `vault/barattoli-*.json`, prodotti dagli script di
raccolta (oggi solo `scripts/bormioli_misure.py`). Qui si uniscono e si
raggruppano in due livelli, marca e poi prodotto, che è l'ordine in cui uno se lo
ricorda: «è un Bormioli, quello grande a bocca larga».

Le misure sono ESTERNE, come quelle delle scatole: il diametro è il punto più
largo del vetro. Vanno nel modulo così come sono.
"""
from __future__ import annotations

import json
import logging

from . import store

logger = logging.getLogger(__name__)

VAULT = store.ROOT / "vault"
PATTERN = "barattoli-*.json"

# I campi senza i quali una riga non serve a nulla: si scarta invece di lasciar
# arrivare al frontend un barattolo senza diametro.
OBBLIGATORI = ("nome", "marca", "altezza_cm", "diametro_cm")


def _righe() -> list[dict]:
    righe: list[dict] = []
    for f in sorted(VAULT.glob(PATTERN)):
        try:
            dati = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("vault/%s illeggibile: saltato", f.name)
            continue
        if not isinstance(dati, list):
            logger.warning("vault/%s non è un elenco: saltato", f.name)
            continue
        for r in dati:
            if all(r.get(k) is not None for k in OBBLIGATORI):
                righe.append(r)
    return righe


def _etichetta(r: dict) -> str:
    """Come si chiama sul chip: linea, capacità, misure.

    Il nome del sito ripete la linea in coda ("Vaso ermetico 150 cl  Fido") e su
    un chip stretto è rumore, ma la linea serve — è il primo modo in cui uno
    riconosce il proprio barattolo. Quindi si toglie dalla coda e si mette in
    testa, una volta sola.
    """
    linea = (r.get("linea") or "").strip()
    nome = " ".join(r["nome"].split())
    if linea and nome.lower().endswith(linea.lower()):
        nome = nome[: -len(linea)].strip()
    return f"{linea} · {nome}" if linea else nome


def elenco() -> dict:
    """`{marche: [{marca, barattoli: [...]}]}`, ordinato per altezza."""
    righe = _righe()
    per_marca: dict[str, list[dict]] = {}
    for r in righe:
        per_marca.setdefault(r["marca"], []).append(
            {
                # L'identità è marca + nome: due produttori possono avere lo
                # stesso nome di serie, e il nome da solo non basta mai.
                "id": f"{r['marca']}|{r['nome']}",
                "marca": r["marca"],
                "linea": r.get("linea"),
                "nome": " ".join(r["nome"].split()),
                "etichetta": _etichetta(r),
                "altezza_cm": r["altezza_cm"],
                "diametro_cm": r["diametro_cm"],
                "capacita_cl": r.get("capacita_cl"),
                "url": r.get("url"),
                # Presente solo quando la fonte dichiara misure discordi dello
                # stesso vaso: il chip deve poterlo dire, non nasconderlo.
                "conflitto": r.get("conflitto"),
            }
        )

    marche = [
        {"marca": marca, "barattoli": sorted(b, key=lambda x: x["altezza_cm"])}
        for marca, b in sorted(per_marca.items())
    ]
    return {"marche": marche, "n": len(righe)}
