"""Il `fit` deve pesare il compromesso, non il solo riempimento.

La prima versione ordinava per volume occupato e basta. Su un vano grande
vinceva sempre chi frammenta di piu': su un sottoletto da 698 L proponeva 208
contenitori da 0,92 EUR (191 EUR) e 912 alzate in vetro (902 EUR). Riempimento
ottimo, soluzione inutile.

Questi test fissano il comportamento corretto: il costo totale e il numero di
pezzi contano quanto il riempimento.
"""
from __future__ import annotations

import pytest

# L'algoritmo sta nel package backend, non piu' in scripts/shopcli.py: la CLI e
# l'API lo condividono, e l'immagine Docker copia solo backend/.
from home_product_finder_backend import tassellazione as shopcli

Prodotto = shopcli.Prodotto
Vano = shopcli.Vano


def prodotto(nome: str, prezzo: float, a: float, b: float, h: float) -> Prodotto:
    return Prodotto(shop="test", nome=nome, prezzo=prezzo, a=a, b=b, h=h, link="", img="")


# Il vano sottoletto reale: e' il caso che ha fatto emergere il difetto.
SOTTOLETTO = Vano.parse("L1=161x197x22")

# Due soluzioni realistiche, prese dal catalogo Action vero.
GRANDE = prodotto("scatola grande", 5.95, 59, 39, 18)     # 12 pz -> 71,40 EUR
MINUSCOLO = prodotto("contenitino", 0.92, 20, 15, 11)     # 208 pz -> 191,36 EUR


def nomi(fits) -> list[str]:
    return [f.prodotto.nome for f in fits]


def test_il_minuscolo_riempie_di_piu_ma_costa_molto_di_piu():
    """Premessa dei test seguenti: senza di questa non provano nulla."""
    g = shopcli.fit_prodotto(SOTTOLETTO, GRANDE)
    m = shopcli.fit_prodotto(SOTTOLETTO, MINUSCOLO)
    assert m.vol > g.vol, "il contenitino deve riempire di piu'"
    assert m.costo > g.costo * 2, "e costare molto di piu'"
    assert m.totale_pezzi > g.totale_pezzi * 10


def test_default_non_mette_per_primo_il_riempimento_massimo():
    """Il cuore della correzione: 208 pezzi non possono vincere per default."""
    top = shopcli.classifica(SOTTOLETTO, [GRANDE, MINUSCOLO], min_vol=0.0)
    assert top[0].prodotto.nome == "scatola grande"


def test_euro_litro_confronta_taglie_diverse():
    g = shopcli.fit_prodotto(SOTTOLETTO, GRANDE)
    m = shopcli.fit_prodotto(SOTTOLETTO, MINUSCOLO)
    assert g.euro_litro < m.euro_litro
    # 12 scatole da 59x39x18 = 12 * 41,42 L
    assert g.litri == pytest.approx(12 * 59 * 39 * 18 / 1000, rel=1e-6)


def test_frontiera_toglie_le_soluzioni_dominate():
    """Stesse misure, prezzo doppio: non c'e' ragione di proporla."""
    caro = prodotto("stesso ma caro", 11.90, 59, 39, 18)
    top = shopcli.classifica(SOTTOLETTO, [GRANDE, caro], min_vol=0.0)
    assert nomi(top) == ["scatola grande"]


def test_tutte_mostra_anche_le_dominate():
    caro = prodotto("stesso ma caro", 11.90, 59, 39, 18)
    top = shopcli.classifica(SOTTOLETTO, [GRANDE, caro], min_vol=0.0, tutte=True)
    assert set(nomi(top)) == {"scatola grande", "stesso ma caro"}


def test_max_pz_scarta_le_soluzioni_ingestibili():
    top = shopcli.classifica(SOTTOLETTO, [GRANDE, MINUSCOLO], min_vol=0.0, max_pz=20)
    assert nomi(top) == ["scatola grande"]


def test_budget_scarta_le_soluzioni_fuori_spesa():
    top = shopcli.classifica(SOTTOLETTO, [GRANDE, MINUSCOLO], min_vol=0.0, budget=100.0)
    assert nomi(top) == ["scatola grande"]


def test_sort_riempimento_resta_disponibile():
    """Il vecchio criterio non e' sbagliato, e' solo il default sbagliato."""
    top = shopcli.classifica(
        SOTTOLETTO, [GRANDE, MINUSCOLO], min_vol=0.0, ordina="riempimento"
    )
    assert top[0].prodotto.nome == "contenitino"


def test_stesso_nome_misure_diverse_sono_alternative_distinte():
    """Action vende 7 contenitori diversi tutti chiamati "Contenitore Heidrun".

    Il dedup per solo titolo ne cancellava sei — e non a caso: quello perso
    (78x37x18) stava sulla frontiera, cioe' era una soluzione valida che
    nessuno avrebbe mai visto.
    """
    piccolo = prodotto("Contenitore Heidrun", 2.72, 33, 23, 20)
    grande = prodotto("Contenitore Heidrun", 7.95, 78, 37, 18)
    top = shopcli.classifica(SOTTOLETTO, [piccolo, grande], min_vol=0.0, tutte=True)
    misure = {(f.prodotto.a, f.prodotto.b, f.prodotto.h) for f in top}
    assert misure == {(33, 23, 20), (78, 37, 18)}


def test_stesse_misure_stesso_nome_vengono_deduplicate():
    """Il dedup deve comunque funzionare: sorgenti che si sovrappongono."""
    a = prodotto("Contenitore Heidrun", 7.95, 78, 37, 18)
    b = prodotto("Contenitore Heidrun", 7.95, 78, 37, 18)
    top = shopcli.classifica(SOTTOLETTO, [a, b], min_vol=0.0, tutte=True)
    assert len(top) == 1


def test_prodotto_troppo_alto_non_entra():
    alto = prodotto("troppo alto", 1.0, 30, 30, 30)
    assert shopcli.fit_prodotto(SOTTOLETTO, alto) is None
