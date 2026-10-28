"""Which box holds N objects — the inverse question of `spazi.py`.

There the container is given and the catalogue supplies the content: which boxes
tessellate this compartment. Here the content is given and the catalogue supplies
the container: I have 24 jars 10x10x22, which box do I buy, and how many?

The geometry is the same grid tessellation read from the other end — the box
plays the part of the compartment, the object plays the part of the box — so the
formulas mirror `shopcli.fit_prodotto`. What differs is the degrees of freedom,
and they differ enough that reusing that function would mean lying:

* an object may be forbidden to lie down (a jar on its side empties itself), so
  only the two horizontal rotations are tried unless told otherwise;
* an object may be forbidden to stack (nothing sits on a jar lid safely), and
  then a tall box is worth exactly one layer, not `H // h` of them;
* the number of containers is an unknown here, not a datum: it comes out of the
  quantity, and with it the real cost of the answer.

Everything the catalogue publishes is an EXTERNAL dimension — no shop states
wall thickness — so a margin is subtracted from all three sides before fitting.
Its default is a centimetre: enough for the walls of a plastic bin, honest about
being an estimate rather than a measurement.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from . import catalog

# Rows returned. The interesting containers are always at the top; beyond this
# the list is only noise (boxes that hold two jars each).
MAX_RIGHE = 60

# Subtracted from each side of the box to go from external to usable internal
# size. One centimetre total, i.e. half a centimetre of wall per side.
MARGINE_DEFAULT = 1.0


@dataclass(frozen=True)
class Oggetto:
    """What has to be stored, once. Measures in cm, `h` always the height."""

    a: float
    b: float
    h: float

    @property
    def volume_l(self) -> float:
        return self.a * self.b * self.h / 1000.0


@dataclass(frozen=True)
class Opzioni:
    in_piedi: bool = True
    impilabili: bool = False
    margine: float = MARGINE_DEFAULT
    max_scatole: int | None = None
    # Material is not a cosmetic preference here: the cheapest boxes in the
    # catalogue are cardboard, so they win the cost axis and fill the top of the
    # ranking with answers nobody wants for jars. Filtering client-side would not
    # help — the cardboard would still consume the MAX_RIGHE slots.
    materiali: frozenset[str] = frozenset()
    escludi: frozenset[str] = frozenset()
    # Absence is not a negation (see attributi.py): a box whose name never says
    # what it is made of is unknown, not "wrong material". Dropping the unknowns
    # by default would throw away most of IKEA, whose names are just KUGGIS.
    ignoti: bool = True


def _orientamenti(o: Oggetto, in_piedi: bool) -> list[tuple[float, float, float]]:
    """The (x, y, z) the object may take, z being what goes vertical.

    Upright: only the two horizontal rotations — the object keeps its own height.
    Free: all three axes may point up, deduplicated because a cube has one
    orientation, not six.
    """
    if in_piedi:
        candidati = [(o.a, o.b, o.h), (o.b, o.a, o.h)]
    else:
        candidati = [
            (o.a, o.b, o.h), (o.b, o.a, o.h),
            (o.a, o.h, o.b), (o.h, o.a, o.b),
            (o.b, o.h, o.a), (o.h, o.b, o.a),
        ]
    visti: set[tuple[float, float, float]] = set()
    return [c for c in candidati if not (c in visti or visti.add(c))]


def _griglia(
    L: float, P: float, H: float, x: float, y: float, z: float, impilabili: bool
) -> tuple[int, int, int] | None:
    """How many objects of (x, y, z) fit in a usable box of (L, P, H)."""
    nx, ny = int(L // x), int(P // y)
    if nx < 1 or ny < 1:
        return None
    livelli = int(H // z) if impilabili else (1 if z <= H else 0)
    if livelli < 1:
        return None
    return nx, ny, livelli


def _disposizione(
    item: dict, o: Oggetto, opt: Opzioni
) -> tuple[int, int, int, bool] | None:
    """Best arrangement of the object inside one box: (nx, ny, livelli, in_piedi).

    Best = most objects per box. On a tie the first orientation wins, and the
    orientations are generated upright-first, so a box that holds four either way
    is reported the way you would actually load it.
    """
    L = item["a"] - opt.margine
    P = item["b"] - opt.margine
    H = item["h"] - opt.margine
    if min(L, P, H) <= 0:
        return None

    migliore: tuple[int, int, int, bool] | None = None
    for x, y, z in _orientamenti(o, opt.in_piedi):
        griglia = _griglia(L, P, H, x, y, z, opt.impilabili)
        if griglia is None:
            continue
        nx, ny, livelli = griglia
        dritto = z == o.h
        if migliore is None or nx * ny * livelli > migliore[0] * migliore[1] * migliore[2]:
            migliore = (nx, ny, livelli, dritto)
    return migliore


def _riga(item: dict, o: Oggetto, n: int, opt: Opzioni) -> dict | None:
    disposizione = _disposizione(item, o, opt)
    if disposizione is None:
        return None
    nx, ny, livelli, dritto = disposizione

    per_scatola = nx * ny * livelli
    scatole = math.ceil(n / per_scatola)
    capienza = scatole * per_scatola
    costo = round(scatole * item["prezzo"], 2)
    # Filling measured on ONE full box, not on the lot: the last box being half
    # empty is a rounding artefact of the quantity, not a property of the box.
    utile_l = (
        (item["a"] - opt.margine)
        * (item["b"] - opt.margine)
        * (item["h"] - opt.margine)
        / 1000.0
    )
    riempimento = per_scatola * o.volume_l / utile_l if utile_l > 0 else 0.0

    return {
        # Same identity rule as everywhere else in this node: the name alone is
        # not one — Action sells seven different "Contenitore Heidrun".
        "id": f"{item['nome']}|{item['a']}x{item['b']}x{item['h']}",
        "nome": item["nome"],
        "negozio": item["negozio"],
        "prezzo": item["prezzo"],
        "a": item["a"],
        "b": item["b"],
        "h": item["h"],
        "dim": f"{item['a']}x{item['b']}x{item['h']}",
        "coperchio": item.get("coperchio"),
        "materiali": item.get("materiali", []),
        "tratti": item.get("tratti", []),
        "nx": nx,
        "ny": ny,
        "livelli": livelli,
        "in_piedi": dritto,
        "per_scatola": per_scatola,
        "scatole": scatole,
        "capienza": capienza,
        "avanzo": capienza - n,
        "costo": costo,
        "costo_per_oggetto": round(costo / n, 3),
        "riempimento_pct": round(riempimento * 100, 1),
        "litri": round(scatole * item["a"] * item["b"] * item["h"] / 1000.0, 1),
        "eur_per_l": item.get("eur_per_l"),
        "link": item.get("link"),
        "img": item.get("img"),
        "classe": item.get("classe"),
    }


def _domina(a: dict, b: dict) -> bool:
    """True when `a` beats `b` on every axis at once.

    Three axes pulling apart, as in the tessellation: spend less, buy fewer
    containers, waste less room inside them. A row beaten on all three is one
    nobody would ever pick, so it is not marked as a live option.
    """
    non_peggio = (
        a["costo"] <= b["costo"]
        and a["scatole"] <= b["scatole"]
        and a["riempimento_pct"] >= b["riempimento_pct"]
    )
    meglio = (
        a["costo"] < b["costo"]
        or a["scatole"] < b["scatole"]
        or a["riempimento_pct"] > b["riempimento_pct"]
    )
    return non_peggio and meglio


def _passa_materiale(item: dict, opt: Opzioni) -> bool:
    """Whether the box survives the material filter.

    Declared materials are a list, and a composite box ("baule in legno con
    coperchio in metallo") declares two: excluding on ANY match is the strict
    reading, and it is the right one — a wooden crate with a metal lid is still
    not plastic.
    """
    dichiarati = set(item.get("materiali") or [])
    if opt.escludi & dichiarati:
        return False
    if not opt.materiali:
        return True
    if dichiarati & opt.materiali:
        return True
    return opt.ignoti and not dichiarati


def cerca(oggetto: Oggetto, n: int, opt: Opzioni | None = None) -> dict:
    """Every box that holds the N objects, ranked by what the lot costs."""
    opt = opt or Opzioni()
    catalogo = catalog.solo_scatole(catalog.list_catalogo())
    scatole = [i for i in catalogo if _passa_materiale(i, opt)]

    righe: list[dict] = []
    visti: set[str] = set()
    for item in scatole:
        riga = _riga(item, oggetto, n, opt)
        if riga is None or riga["id"] in visti:
            continue
        if opt.max_scatole is not None and riga["scatole"] > opt.max_scatole:
            continue
        visti.add(riga["id"])
        righe.append(riga)

    ottimali = {r["id"] for r in righe if not any(_domina(g, r) for g in righe if g is not r)}
    for r in righe:
        r["ottimale"] = r["id"] in ottimali

    # Cheapest lot first, then fewer containers: that is the order in which the
    # question is usually asked ("quanto mi costa" before "quante ne prendo").
    righe.sort(key=lambda r: (r["costo"], r["scatole"]))

    return {
        "oggetto": {
            "a": oggetto.a,
            "b": oggetto.b,
            "h": oggetto.h,
            "volume_l": round(oggetto.volume_l, 2),
        },
        "n": n,
        "opzioni": {
            "in_piedi": opt.in_piedi,
            "impilabili": opt.impilabili,
            "margine": opt.margine,
            "max_scatole": opt.max_scatole,
            "materiali": sorted(opt.materiali),
            "escludi": sorted(opt.escludi),
            "ignoti": opt.ignoti,
        },
        "n_valide": len(righe),
        "n_catalogo": len(catalogo),
        # How many of the boxes that fit never say what they are made of. The
        # filter keeps them, so the page must be able to admit it out loud.
        "n_ignoti": sum(1 for r in righe if not r["materiali"]),
        # The vocabulary lives in the vault, so the chips are not hard-coded in
        # the UI: here is what the catalogue actually declares, with counts.
        "materiali_catalogo": _conteggio_materiali(catalogo),
        "risultati": righe[:MAX_RIGHE],
    }


def _conteggio_materiali(scatole: list[dict]) -> list[dict]:
    """`[{nome, n}]` over the whole box catalogue, most common first."""
    conteggio: dict[str, int] = {}
    for item in scatole:
        for m in item.get("materiali") or []:
            conteggio[m] = conteggio.get(m, 0) + 1
    return [
        {"nome": nome, "n": n}
        for nome, n in sorted(conteggio.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
