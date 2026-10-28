"""Characteristics read out of the product name (`attributi.py`).

The shops give a name and nothing else, so the name is the spec sheet. What
matters here: a denial is not a confirmation, silence is not a denial, and the
vocabulary matches stems so plurals do not need their own entry.
"""
from __future__ import annotations

import pytest


@pytest.fixture()
def regole() -> dict:
    from home_product_finder_backend import attributi

    # The real vault vocabulary: these tests are also a check on that file.
    return attributi.regole()


def leggi(nome: str, regole: dict) -> dict:
    from home_product_finder_backend import attributi

    return attributi.leggi(nome, regole)


def test_lid_is_yes_no_or_unknown(regole):
    assert leggi("SAMLA Scatola con coperchio", regole)["coperchio"] is True
    assert leggi("BOX GAIA GRIGIO CON TAPPO COLORATO", regole)["coperchio"] is True
    # "SENZA COPERCHIO" contains "coperchio": the denial has to win.
    assert (
        leggi("BOX CONTENITORE SENZA COPERCHIO E SENZA RUOTE", regole)["coperchio"]
        is False
    )
    # Silence stays silence. Calling this one lidless would be an invention.
    assert leggi("KUGGIS Scatola", regole)["coperchio"] is None


def test_materials_are_a_list_because_products_are_composite(regole):
    uno = leggi("BAULE CASSAPANCA IN ABETE MASSELLO", regole)["materiali"]
    assert uno == ["legno"]

    due = leggi(
        "BAULE DA ESTERNO IN LEGNO CON COPERCHIO IN METALLO 110X50X50", regole
    )["materiali"]
    assert set(due) == {"legno", "metallo"}

    # A series name says nothing by itself, and the honest answer is "unknown".
    assert leggi("REGNBROMS Contenitore", regole)["materiali"] == []


def test_known_series_beat_the_word_vocabulary(regole):
    """The `nomi` table is knowledge, not inference — it wins, and it is needed.

    Two thirds of the boxes that fit a jar declare nothing: "SAMLA Contenitore"
    is a series name. Without this table the material filter would have almost
    nothing to filter on.
    """
    assert leggi("SAMLA Contenitore con coperchio", regole)["materiali"] == ["plastica"]
    assert leggi("PAPPIS Scatola con coperchio", regole)["materiali"] == ["cartone"]
    assert leggi("KNAGGLIG Contenitore", regole)["materiali"] == ["legno"]
    # Matched on the START of the name: a series is how the name opens, and a
    # loose substring would fire inside unrelated words.
    assert leggi("Scatola per SAMLA", regole)["materiali"] == []


def test_traits_match_on_stems(regole):
    # "impilabil" covers impilabile and impilabili; one entry, both plurals.
    assert "impilabile" in leggi("Contenitori impilabili", regole)["tratti"]
    assert "impilabile" in leggi("Contenitore impilabile", regole)["tratti"]

    tratti = leggi(
        "BOX CONTENITORE 24 LT CON COPERCHIO E RUOTE 60X40X18,5 CM", regole
    )["tratti"]
    assert "ruote" in tratti


def test_catalogue_rows_carry_the_characteristics(tmp_path, monkeypatch):
    """The attributes are read after the merge, on the fullest name."""
    import json

    from home_product_finder_backend import catalog, store

    scrape = tmp_path / "_scrape"
    scrape.mkdir()
    riga = {
        "shop": "action",
        "nome": "Contenitore",  # short name: says nothing
        "prezzo": 4.0,
        "a": 39.0,
        "b": 29.0,
        "h": 26.0,
        "link": "https://ex.test/p/1",
        "img": "",
    }
    (scrape / "action-contenitore.json").write_text(
        json.dumps([riga]), encoding="utf-8"
    )
    (scrape / "action-scatola.json").write_text(
        json.dumps(
            [{**riga, "nome": "Contenitore in plastica con coperchio e ruote"}]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(store, "SCRAPE_DIR", scrape)

    item = catalog.list_catalogo()[0]
    assert item["coperchio"] is True
    assert item["materiali"] == ["plastica"]
    assert "ruote" in item["tratti"]


def test_unreadable_vocabulary_leaves_everything_unknown(tmp_path, monkeypatch):
    from home_product_finder_backend import attributi

    rotto = tmp_path / "attributi.json"
    rotto.write_text("{ non json", encoding="utf-8")
    monkeypatch.setattr(attributi, "ATTRIBUTI_FILE", rotto)

    assert attributi.leggi("Scatola con coperchio", attributi.regole()) == {
        "coperchio": None,
        "materiali": [],
        "tratti": [],
    }
