"""Spaces to fill, and the box tessellation ranked per compartment.

Two sources, on purpose:

* the **furniture** (cupboards, bed, shelving) belongs to the `Home` node and is
  read from its API — `GET :10004/api/furniture` — never from its vault files.
  That is the fractal-network rule: a node owns its data, siblings ask.
* the **local** spaces in `vault/spazi.json` are the ones that are not furniture
  at all: free-standing stacks of boxes, which only this node cares about.

The last successful answer from Home is cached in `vault/_cache/`, so the page
keeps working — flagged as stale — when Home is not running.

The tessellation itself is NOT reimplemented here: it comes from
`tassellazione.py`, which owns that algorithm (grid fit over both orientations,
Pareto frontier over filling/cost/piece-count) and is shared with the `shopcli`
CLI. One algorithm, one place — the two must never drift apart.
"""
from __future__ import annotations

import json
import logging
import os

import httpx

from . import catalog, store
from .tassellazione import Fit, Prodotto, Vano, classifica, frontiera

logger = logging.getLogger(__name__)

SPAZI_FILE = store.ROOT / "vault" / "spazi.json"
CACHE_FILE = store.ROOT / "vault" / "_cache" / "home-arredi.json"

# Home's backend port comes from the fractal registry (docs/ports.registry.json,
# id "home"). Overridable for Docker/remote, where localhost is not the node.
HOME_API = os.environ.get("HOME_API_URL", "http://localhost:10004")
HOME_TIMEOUT = 3.0

# Ranking rows per compartment. Enough to see the alternatives, few enough that
# the page stays readable — the interesting solutions are always at the top.
MAX_RIGHE = 40

# Minimum filling for a solution to be listed. The CLI defaults to 0.5, which is
# right when hunting the best tessellation but wrong here: on a narrow bay like
# V3 it silently hides every partial answer, and the page ends up claiming there
# is nothing when there is something mediocre. Show the mediocre ones, ranked
# last — a visible 30% beats an invisible one.
MIN_RIEMPIMENTO = 0.2

# Thickness eaten by a shelf plus the clearance to slide a box in and out.
# Used only for adjustable shelving, to turn a box height into a shelf pitch.
SPESSORE_RIPIANO = 3.0


# --------------------------------------------------------------------------- #
# Sorgenti
# --------------------------------------------------------------------------- #
def _arredi_da_home() -> tuple[list[dict], bool]:
    """(furniture, from_cache). Never raises: Home being down is not an error."""
    try:
        r = httpx.get(f"{HOME_API}/api/furniture", timeout=HOME_TIMEOUT)
        r.raise_for_status()
        arredi = r.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Home unreachable (%s), falling back to cache", exc)
        return _leggi_cache(), True

    _scrivi_cache(arredi)
    return arredi, False


def _leggi_cache() -> list[dict]:
    if not CACHE_FILE.exists():
        return []
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _scrivi_cache(arredi: list[dict]) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(
            json.dumps(arredi, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError:  # a read-only vault must not break the page
        logger.warning("could not refresh the Home cache")


def _spazi_locali() -> list[dict]:
    if not SPAZI_FILE.exists():
        return []
    try:
        return json.loads(SPAZI_FILE.read_text(encoding="utf-8")).get("spazi", [])
    except (json.JSONDecodeError, OSError):
        logger.warning("vault/spazi.json unreadable")
        return []


def _da_arredo(arredo: dict, da_cache: bool) -> dict:
    """One piece of Home furniture, in the shape this node's page expects."""
    vani = arredo.get("vani", [])
    stanza = arredo.get("stanza")
    return {
        "slug": arredo.get("slug", "arredo"),
        "nome": arredo.get("titolo", "Arredo"),
        "stanza": stanza,
        "stato": "misurato" if any(v.get("misurato") for v in vani) else "da-misurare",
        "nota": arredo.get("gioco"),
        "fonte": "cache-home" if da_cache else "home",
        "vani": vani,
    }


# --------------------------------------------------------------------------- #
# Tassellazione
# --------------------------------------------------------------------------- #
def _prodotti(items: list[dict]) -> list[Prodotto]:
    return [
        Prodotto(
            shop=i["negozio"],
            nome=i["nome"],
            prezzo=i["prezzo"],
            a=i["a"],
            b=i["b"],
            h=i["h"],
            link=i["link"] or "",
            img=i["img"] or "",
        )
        for i in items
    ]


def _id(p: Prodotto) -> str:
    """Identity of a solution: the name alone is not one.

    Action sells seven different boxes all called "Contenitore Heidrun" — the
    dedup in `classifica` already keys on (name + size) for that reason. Anything
    downstream that keys on the name alone (the Pareto mark, a starred row, a
    React key) would collapse the seven into one.
    """
    return f"{p.nome}|{p.a}x{p.b}x{p.h}"


def _riga(fit, ottimale: bool, attrs: dict[str, dict]) -> dict:
    p = fit.prodotto
    return {
        "id": _id(p),
        # Lid, material and traits, read from the name in `attributi.py`. They
        # travel with the row because the ranking is where the choice is made:
        # "84 pieces at 89%" is not a decision until you know they have a lid.
        **attrs.get(p.nome, {}),
        "nome": p.nome,
        "negozio": p.shop,
        "prezzo": p.prezzo,
        "dim": f"{p.a}x{p.b}x{p.h}",
        "a": p.a,
        "b": p.b,
        "h": p.h,
        "nx": fit.nx,
        "ny": fit.ny,
        "livelli": fit.livelli,
        "pezzi": fit.totale_pezzi,
        "costo": fit.costo,
        "area_pct": round(fit.area * 100, 1),
        "vol_pct": round(fit.vol * 100, 1),
        "litri": round(fit.litri, 1),
        "eur_per_l": round(fit.euro_litro, 3),
        # On the Pareto frontier: nothing else fills more, costs less AND uses
        # fewer pieces. Everything else is beaten on every count at once.
        "ottimale": ottimale,
        "link": p.link or None,
        "img": p.img or None,
    }


def _fit_regolabile(vano_cfg: dict, p: Prodotto) -> Fit | None:
    """Fit on shelving whose shelves clamp anywhere on the upright.

    Here the clear height per level is not a constraint to satisfy but an output
    to choose: the box decides the pitch. What is actually fixed is the upright
    and the number of shelves, so the levels are `min(ripiani, montante // passo)`
    and the answer worth reading is the pitch to set the shelves at.
    """
    montante = float(vano_cfg["montante"])
    ripiani = int(vano_cfg.get("ripiani") or 1)
    passo = p.h + SPESSORE_RIPIANO
    livelli = min(ripiani, int(montante // passo))
    if livelli < 1:
        return None

    L, P = float(vano_cfg["L"]), float(vano_cfg["P"])
    best: Fit | None = None
    for x, y in ((p.a, p.b), (p.b, p.a)):
        nx, ny = int(L // x), int(P // y)
        if nx < 1 or ny < 1:
            continue
        area = (nx * x * ny * y) / (L * P)
        # Volume measured against the whole upright: leaving two of four levels
        # unused is a real loss, and must show as one.
        vol = area * (livelli * p.h) / montante
        if best is None or vol > best.vol:
            best = Fit(p, nx, ny, livelli, area, vol)
    return best


def _classifica_regolabile(
    vano_cfg: dict, prodotti: list[Prodotto], attrs: dict[str, dict]
) -> dict:
    fits = [
        f for p in prodotti if (f := _fit_regolabile(vano_cfg, p)) and f.vol >= MIN_RIEMPIMENTO
    ]
    fits.sort(key=lambda f: f.euro_litro)

    visti: set[str] = set()
    unici: list[Fit] = []
    for f in fits:
        if _id(f.prodotto) in visti:
            continue
        visti.add(_id(f.prodotto))
        unici.append(f)

    ottimali = {_id(f.prodotto) for f in frontiera(unici)}
    righe = []
    for f in unici[:MAX_RIGHE]:
        riga = _riga(f, _id(f.prodotto) in ottimali, attrs)
        # The actionable number for shelving: where to clamp the shelves.
        riga["passo_cm"] = round(f.prodotto.h + SPESSORE_RIPIANO, 1)
        righe.append(riga)

    return {**vano_cfg, "n_soluzioni": len(unici), "soluzioni": righe}


def _classifica_vano(
    vano_cfg: dict, prodotti: list[Prodotto], attrs: dict[str, dict]
) -> dict:
    """Rank the catalogue for one compartment; skip it when not measured.

    A compartment can be half-known (the Everest shelf publishes its footprint
    but not the clear height, which only exists once the shelves are clamped).
    Ranking it would mean inventing the missing number, so it comes back with no
    solutions and stays visible as an open slot.
    """
    if vano_cfg.get("regolabile") and vano_cfg.get("montante") and vano_cfg.get("L"):
        return _classifica_regolabile(vano_cfg, prodotti, attrs)

    if not vano_cfg.get("misurato", True) or not vano_cfg.get("H"):
        return {**vano_cfg, "n_soluzioni": 0, "soluzioni": []}

    vano = Vano(
        vano_cfg.get("id", "vano"),
        float(vano_cfg["L"]),
        float(vano_cfg["P"]),
        float(vano_cfg["H"]),
    )
    # Two passes over the same products: the full ranking is what the user reads,
    # the frontier only marks which of those rows are actually non-dominated.
    tutte = classifica(vano, prodotti, min_vol=MIN_RIEMPIMENTO, tutte=True)
    ottimali = {
        _id(f.prodotto) for f in classifica(vano, prodotti, min_vol=MIN_RIEMPIMENTO)
    }

    return {
        **vano_cfg,
        "n_soluzioni": len(tutte),
        "soluzioni": [
            _riga(f, _id(f.prodotto) in ottimali, attrs) for f in tutte[:MAX_RIGHE]
        ],
    }


def list_spazi() -> list[dict]:
    """Home's furniture + this node's own spaces, each ranked where measured."""
    arredi, da_cache = _arredi_da_home()
    spazi = [_da_arredo(a, da_cache) for a in arredi]
    spazi += [{**s, "fonte": "locale"} for s in _spazi_locali()]

    # Solo cio' che e' davvero una scatola: le categorie larghe delle CLI
    # pescano anche stura-lavandini e appendiabiti, che hanno tre dimensioni e
    # un prezzo e altrimenti si classificherebbero come ottime soluzioni.
    scatole = catalog.solo_scatole(catalog.list_catalogo())
    prodotti = _prodotti(scatole)
    # Solutions are identified by name (that is also the dedup key upstream), so
    # the characteristics ride along in a lookup instead of inside `Prodotto` —
    # the shared tessellation model, whose shape the CLI also serialises.
    attrs = {
        i["nome"]: {
            "coperchio": i.get("coperchio"),
            "materiali": i.get("materiali", []),
            "tratti": i.get("tratti", []),
        }
        for i in scatole
    }
    return [
        {**s, "vani": [_classifica_vano(v, prodotti, attrs) for v in s.get("vani", [])]}
        for s in spazi
    ]
