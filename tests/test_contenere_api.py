"""Which box holds N objects: GET /api/packing (+ /api/contenere).

What matters: the geometry counts the objects right, the margin between external
and usable size is actually applied, the two forbidden freedoms (lying down,
stacking) really are forbidden unless asked for, and the number of containers
follows the quantity instead of the other way round.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _scrape_rows() -> list[dict]:
    return [
        # 41x41x24 external -> 40x40x23 usable: exactly 4 jars 20x20x22 upright.
        {
            "shop": "action",
            "nome": "Cassa 41x41x24",
            "prezzo": 5.0,
            "a": 41.0,
            "b": 41.0,
            "h": 24.0,
            "link": "https://ex.test/p/cassa",
            "img": "",
        },
        # Same footprint but 1 cm shorter inside: the jar no longer stands up.
        {
            "shop": "ikea",
            "nome": "Cassa bassa 41x41x22",
            "prezzo": 3.0,
            "a": 41.0,
            "b": 41.0,
            "h": 22.0,
            "link": "https://ex.test/p/bassa",
            "img": "",
        },
        # Tall enough for two layers of jars, if they may be stacked.
        {
            "shop": "maurys",
            "nome": "Torre 41x41x46",
            "prezzo": 9.0,
            "a": 41.0,
            "b": 41.0,
            "h": 46.0,
            "link": "https://ex.test/p/torre",
            "img": "",
        },
    ]


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from fastapi.testclient import TestClient
    from home_product_finder_backend import store
    from home_product_finder_backend.app import app

    scrape = tmp_path / "_scrape"
    scrape.mkdir()
    (scrape / "box.json").write_text(json.dumps(_scrape_rows()), encoding="utf-8")
    monkeypatch.setattr(store, "SCRAPE_DIR", scrape)
    return TestClient(app)


def _righe(client, **params) -> dict[str, dict]:
    q = {"a": 20, "b": 20, "h": 22, "n": 4, **params}
    r = client.get("/api/packing", params=q)
    assert r.status_code == 200, r.text
    return {row["nome"]: row for row in r.json()["risultati"]}


def test_geometry_and_quantity(client):
    righe = _righe(client, n=10)
    cassa = righe["Cassa 41x41x24"]

    # 40x40 usable / 20x20 jar = 2x2 per layer, one layer (jars do not stack).
    assert (cassa["nx"], cassa["ny"], cassa["livelli"]) == (2, 2, 1)
    assert cassa["per_scatola"] == 4
    # 10 jars in boxes of 4 -> 3 boxes, 12 slots, 2 spare. Never 2.5 boxes.
    assert cassa["scatole"] == 3
    assert cassa["capienza"] == 12
    assert cassa["avanzo"] == 2
    assert cassa["costo"] == pytest.approx(15.0)
    assert cassa["costo_per_oggetto"] == pytest.approx(1.5)


def test_margin_turns_external_size_into_usable_size(client):
    """The 22 cm box is 22 cm outside: a 22 cm jar does not go in."""
    assert "Cassa bassa 41x41x22" not in _righe(client)
    # Told there are no walls, the same box becomes a (dubious) answer.
    assert "Cassa bassa 41x41x22" in _righe(client, margine=0)


def test_stacking_is_off_until_asked_for(client):
    """Nothing sits safely on a jar lid, so height alone must not multiply."""
    assert _righe(client)["Torre 41x41x46"]["per_scatola"] == 4
    assert _righe(client, impilabili="true")["Torre 41x41x46"]["per_scatola"] == 8


def test_lying_down_is_off_until_asked_for(client):
    """A jar on its side empties itself — but a book does not, hence the flag."""
    # A 30 cm tall object only stands in the 46 cm tower; on its side it also
    # goes in the 24 cm crate, because 30 fits across the 40 cm floor.
    assert set(_righe(client, h=30, n=1)) == {"Torre 41x41x46"}
    coricato = _righe(client, h=30, n=1, in_piedi="false")
    assert coricato["Cassa 41x41x24"]["in_piedi"] is False
    assert coricato["Torre 41x41x46"]["in_piedi"] is True


def test_frontier_marks_only_the_live_options(client):
    """Beaten on cost, count and filling at once = not an option anybody picks."""
    righe = _righe(client, n=4)
    # Both hold the 4 jars in one box; the tower costs 9 € against 5 € and wastes
    # half its height doing it.
    assert righe["Cassa 41x41x24"]["ottimale"] is True
    assert righe["Torre 41x41x46"]["ottimale"] is False


def test_rejects_a_nonsense_request(client):
    assert client.get("/api/packing", params={"a": 0, "b": 20, "h": 22}).status_code == 422
    assert client.get(
        "/api/packing", params={"a": 20, "b": 20, "h": 22, "n": 0}
    ).status_code == 422


def _scrape_materiali() -> list[dict]:
    """Same box three times over, differing only in what it is made of.

    Deliberately ordered so the useless answer is also the cheapest: that is the
    real catalogue's shape, and the reason the filter cannot live in the browser.
    """
    base = {"a": 41.0, "b": 41.0, "h": 24.0, "link": "", "img": ""}
    return [
        {"shop": "action", "nome": "Scatola in cartone 41x41x24", "prezzo": 0.99, **base},
        {"shop": "action", "nome": "Cassetta in plastica 41x41x24", "prezzo": 4.0, **base},
        # Says nothing about its material — unknown, not "wrong".
        {"shop": "ikea", "nome": "KUGGIS 41x41x24", "prezzo": 9.0, **base},
    ]


@pytest.fixture()
def client_materiali(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Boxes AND vocabulary are test-local.

    The real `vault/catalogo-attributi.json` grows every time a product series
    is identified — reading it here would make these tests fail the day someone
    adds a word, which says nothing about the filter being right or wrong.
    """
    from fastapi.testclient import TestClient
    from home_product_finder_backend import attributi, store
    from home_product_finder_backend.app import app

    scrape = tmp_path / "_scrape"
    scrape.mkdir()
    (scrape / "box.json").write_text(json.dumps(_scrape_materiali()), encoding="utf-8")
    monkeypatch.setattr(store, "SCRAPE_DIR", scrape)

    vocabolario = tmp_path / "attributi.json"
    vocabolario.write_text(
        json.dumps(
            {
                "materiali": [
                    {"nome": "cartone", "parole": ["cartone"]},
                    {"nome": "plastica", "parole": ["plastica"]},
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(attributi, "ATTRIBUTI_FILE", vocabolario)
    return TestClient(app)


def test_material_filter_keeps_the_unknown_boxes(client_materiali):
    """Asking for plastic must not throw away every box that stays silent."""
    righe = _righe(client_materiali, materiali="plastica")
    assert set(righe) == {"Cassetta in plastica 41x41x24", "KUGGIS 41x41x24"}
    # And the page can say so out loud instead of pretending KUGGIS is plastic.
    r = client_materiali.get(
        "/api/packing", params={"a": 20, "b": 20, "h": 22, "n": 4, "materiali": "plastica"}
    )
    assert r.json()["n_ignoti"] == 1


def test_material_filter_can_refuse_the_unknown_boxes(client_materiali):
    righe = _righe(client_materiali, materiali="plastica", ignoti="false")
    assert set(righe) == {"Cassetta in plastica 41x41x24"}


def test_excluding_a_material_drops_it_before_the_ranking(client_materiali):
    """The cardboard is the cheapest, so it is the row the filter must remove."""
    assert "Scatola in cartone 41x41x24" in _righe(client_materiali)
    righe = _righe(client_materiali, escludi="cartone")
    assert "Scatola in cartone 41x41x24" not in righe
    # Removed from the ranking, not merely hidden: the plastic box now wins.
    assert righe["Cassetta in plastica 41x41x24"]["ottimale"] is True


def test_catalogue_declares_its_own_vocabulary(client_materiali):
    r = client_materiali.get("/api/packing", params={"a": 20, "b": 20, "h": 22, "n": 4})
    materiali = {m["nome"]: m["n"] for m in r.json()["materiali_catalogo"]}
    assert materiali == {"cartone": 1, "plastica": 1}


def test_italian_alias(client):
    q = {"a": 20, "b": 20, "h": 22, "n": 4}
    assert client.get("/api/contenere", params=q).json() == client.get(
        "/api/packing", params=q
    ).json()
