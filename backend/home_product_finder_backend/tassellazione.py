"""Grid tessellation: the product model, a compartment, and the Pareto ranking.

This is the algorithm the whole node turns around — `/api/spaces` fills a given
compartment with catalogue boxes, `shopcli.py fit` does the same from the command
line, and `contenere.py` reads it from the other end (given the content, find the
container). One algorithm, one place: the three must never drift apart.

It lives in the backend package rather than in `scripts/shopcli.py`, where it was
born, for a deployment reason that is easy to forget: the Docker image copies
`backend/` and nothing else, so anything the API imports from `scripts/` is simply
absent in production. A bind mount papers over it in dev and hides the hole. The
dependency now points the way the packaging does — the CLI imports the package,
not the other way round.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass


def misura(s: str) -> float:
    """Italian decimal comma to float: `12,5` -> 12.5."""
    return float(s.replace(",", "."))


@dataclass
class Prodotto:
    shop: str
    nome: str
    prezzo: float
    a: float
    b: float
    h: float
    link: str = ""
    img: str = ""

    @property
    def dims(self) -> tuple[float, float, float]:
        return (self.a, self.b, self.h)


@dataclass
class Vano:
    nome: str
    L: float
    P: float
    H: float

    @classmethod
    def parse(cls, spec: str) -> Vano:
        """`C1=32x83x18` -> Vano('C1', 32, 83, 18). Misure UTILI, gioco escluso."""
        nome, _, dims = spec.partition("=")
        if not dims:
            nome, dims = "vano", nome
        parts = re.split(r"[xX×]", dims)
        if len(parts) != 3:
            raise ValueError(f"vano non valido: {spec!r} (atteso NOME=LxPxH)")
        L, P, H = (misura(p) for p in parts)
        return cls(nome, L, P, H)


@dataclass
class Fit:
    prodotto: Prodotto
    nx: int
    ny: int
    livelli: int
    area: float
    vol: float

    @property
    def totale_pezzi(self) -> int:
        return self.nx * self.ny * self.livelli

    @property
    def costo(self) -> float:
        return round(self.totale_pezzi * self.prodotto.prezzo, 2)

    @property
    def litri(self) -> float:
        """Litri effettivamente contenibili dai pezzi disposti."""
        p = self.prodotto
        return self.totale_pezzi * (p.a * p.b * p.h) / 1000.0

    @property
    def euro_litro(self) -> float:
        """Il numero che rende confrontabili soluzioni di taglia diversa.

        Il riempimento da solo premia sempre chi frammenta: piu' scatole piccole
        approssimano meglio qualunque vano. Ma 208 contenitori da 0,92 EUR
        riempiono il 98% e costano 191 EUR, contro 10 scatole grandi che
        riempiono il 91% e ne costano 79. Il costo per litro separa le due cose.
        """
        return self.costo / self.litri if self.litri else float("inf")


def fit_prodotto(vano: Vano, p: Prodotto) -> Fit | None:
    """Miglior disposizione a griglia allineata, provando i due orientamenti."""
    if p.h > vano.H:
        return None
    livelli = int(vano.H // p.h)
    best: Fit | None = None
    for x, y in ((p.a, p.b), (p.b, p.a)):
        nx, ny = int(vano.L // x), int(vano.P // y)
        if nx < 1 or ny < 1:
            continue
        area = (nx * x * ny * y) / (vano.L * vano.P)
        vol = area * (livelli * p.h) / vano.H
        if best is None or vol > best.vol:
            best = Fit(p, nx, ny, livelli, area, vol)
    return best


def _domina(a: Fit, b: Fit) -> bool:
    """True se `a` e' migliore o uguale a `b` su OGNI criterio, e meglio su uno.

    I criteri sono tre e tirano in direzioni opposte: riempire di piu', spendere
    di meno, maneggiare meno pezzi. Una soluzione dominata e' peggiore sotto ogni
    aspetto: non c'e' motivo per cui qualcuno la sceglierebbe, quindi si toglie.
    """
    non_peggio = (
        a.vol >= b.vol
        and a.costo <= b.costo
        and a.totale_pezzi <= b.totale_pezzi
    )
    meglio = a.vol > b.vol or a.costo < b.costo or a.totale_pezzi < b.totale_pezzi
    return non_peggio and meglio


def frontiera(fits: Sequence[Fit]) -> list[Fit]:
    """Frontiera di Pareto: tiene solo le soluzioni non dominate."""
    return [f for f in fits if not any(_domina(g, f) for g in fits if g is not f)]


ORDINAMENTI = {
    "valore": lambda f: f.euro_litro,          # meno euro per litro
    "costo": lambda f: f.costo,                # spesa totale piu' bassa
    "pezzi": lambda f: f.totale_pezzi,         # meno oggetti da maneggiare
    "riempimento": lambda f: -f.vol,           # massimo riempimento
}


def classifica(
    vano: Vano,
    prodotti: Iterable[Prodotto],
    min_vol: float = 0.5,
    *,
    max_pz: int | None = None,
    budget: float | None = None,
    ordina: str = "valore",
    tutte: bool = False,
) -> list[Fit]:
    """Soluzioni di tassellazione ordinate per il criterio scelto.

    Di default restituisce la sola FRONTIERA DI PARETO su (riempimento, costo,
    pezzi). Ordinare per il solo riempimento — come faceva la prima versione —
    e' fuorviante: su un vano grande vincono sempre le soluzioni con centinaia di
    contenitori minuscoli, che riempiono benissimo e costano un ordine di
    grandezza di piu'. `--tutte` disattiva il filtro.
    """
    fits = [f for p in prodotti if (f := fit_prodotto(vano, p)) and f.vol >= min_vol]
    if max_pz is not None:
        fits = [f for f in fits if f.totale_pezzi <= max_pz]
    if budget is not None:
        fits = [f for f in fits if f.costo <= budget]

    # Dedup PRIMA della frontiera, ma la chiave e' (nome + misure), non il solo
    # nome: Action vende sette contenitori diversi tutti chiamati "Contenitore
    # Heidrun", e deduplicare per titolo ne cancellava sei — alternative vere,
    # sparite senza un avviso.
    fits.sort(key=lambda f: f.euro_litro)
    visti: set[tuple] = set()
    unici = []
    for f in fits:
        p = f.prodotto
        chiave = (p.nome, p.a, p.b, p.h)
        if chiave in visti:
            continue
        visti.add(chiave)
        unici.append(f)

    if not tutte:
        unici = frontiera(unici)
    unici.sort(key=ORDINAMENTI[ordina])
    return unici
