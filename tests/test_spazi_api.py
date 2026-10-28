"""Spaces + per-compartment tessellation: GET /api/spaces (+ /api/spazi).

What matters: a measured compartment gets a ranking whose geometry is right
(how many boxes fit in the grid, how many levels, area and volume filled), an
unmeasured one stays visible as an open slot, and boxes taller than the
compartment never appear.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _scrape_rows() -> list[dict]:
    return [
        # 4 per layer in a 40x40 compartment (2x2), 2 levels in h20 -> 8 pieces.
        {
            "shop": "action",
            "nome": "Box 20x20x10",
            "prezzo": 1.0,
            "a": 20.0,
            "b": 20.0,
            "h": 10.0,
            "link": "https://ex.test/p/small",
            "img": "",
        },
        # Exactly fills the floor, one level: 100% area, 100% volume.
        {
            "shop": "ikea",
            "nome": "Box 40x40x20",
            "prezzo": 9.0,
            "a": 40.0,
            "b": 40.0,
            "h": 20.0,
            "link": "https://ex.test/p/exact",
            "img": "",
        },
        # Taller than the compartment: must be excluded entirely.
        {
            "shop": "maurys",
            "nome": "Box 30x30x50",
            "prezzo": 5.0,
            "a": 30.0,
            "b": 30.0,
            "h": 50.0,
            "link": "https://ex.test/p/tall",
            "img": "",
        },
        # Same geometry as the exact box but dearer: strictly worse on every
        # criterion at once -> dominated, must not be marked optimal.
        {
            "shop": "maurys",
            "nome": "Box 40x40x20 caro",
            "prezzo": 15.0,
            "a": 40.0,
            "b": 40.0,
            "h": 20.0,
            "link": "https://ex.test/p/dear",
            "img": "",
        },
    ]


def _arredi_home() -> list[dict]:
    """What GET :10004/api/furniture returns — Home owns this shape."""
    return [
        {
            "slug": "mobile-prova",
            "titolo": "Mobile di prova",
            "stanza": "salotto",
            "vani": [
                {
                    "id": "T1",
                    "nome": "T1",
                    "L": 40,
                    "P": 40,
                    "H": 20,
                    "misurato": True,
                },
                # Footprint known, clear height not yet measured (Everest case).
                {
                    "id": "T2",
                    "nome": "T2",
                    "L": 89,
                    "P": 34,
                    "H": None,
                    "misurato": False,
                },
            ],
        }
    ]


def _spazi_locali() -> dict:
    return {
        "spazi": [
            {
                "slug": "pile",
                "nome": "Pile libere",
                "stato": "da-misurare",
                "vani": [],
            }
        ]
    }


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from fastapi.testclient import TestClient

    from home_product_finder_backend import spazi as spazi_mod
    from home_product_finder_backend import store
    from home_product_finder_backend.app import app

    scrape_dir = tmp_path / "_scrape"
    scrape_dir.mkdir()
    (scrape_dir / "box.json").write_text(json.dumps(_scrape_rows()), encoding="utf-8")
    monkeypatch.setattr(store, "SCRAPE_DIR", scrape_dir)

    spazi_file = tmp_path / "spazi.json"
    spazi_file.write_text(json.dumps(_spazi_locali()), encoding="utf-8")
    monkeypatch.setattr(spazi_mod, "SPAZI_FILE", spazi_file)
    monkeypatch.setattr(spazi_mod, "CACHE_FILE", tmp_path / "_cache" / "home.json")

    # Home is a separate node: the test stubs its API instead of running it.
    monkeypatch.setattr(spazi_mod, "_arredi_da_home", lambda: (_arredi_home(), False))

    return TestClient(app)


def test_tessellation_geometry(client):
    spazi = client.get("/api/spaces").json()
    vano = spazi[0]["vani"][0]
    per_nome = {s["nome"]: s for s in vano["soluzioni"]}

    # The box taller than the compartment is not a solution at all.
    assert "Box 30x30x50" not in per_nome

    piccolo = per_nome["Box 20x20x10"]
    assert (piccolo["nx"], piccolo["ny"], piccolo["livelli"]) == (2, 2, 2)
    assert piccolo["pezzi"] == 8
    assert piccolo["costo"] == pytest.approx(8.0)
    assert piccolo["area_pct"] == pytest.approx(100.0)
    assert piccolo["vol_pct"] == pytest.approx(100.0)

    esatto = per_nome["Box 40x40x20"]
    assert esatto["pezzi"] == 1
    assert esatto["area_pct"] == pytest.approx(100.0)

    # Both survive: same filling, but one is cheaper (8 € vs 9 €) and the other
    # needs a single piece instead of eight. Neither beats the other outright,
    # so the frontier keeps both — that is the point of ranking on three axes.
    assert piccolo["ottimale"] is True
    assert esatto["ottimale"] is True

    # Identical geometry, 6 € dearer: beaten on every axis at once.
    assert per_nome["Box 40x40x20 caro"]["ottimale"] is False


def test_same_name_different_size_stay_two_solutions(tmp_path, monkeypatch):
    """Action sells seven boxes called "Contenitore Heidrun": name ≠ identity.

    Keying on the name alone would mark all of them optimal as soon as one is,
    and would star all of them at once in the UI.
    """
    from fastapi.testclient import TestClient

    from home_product_finder_backend import spazi as spazi_mod
    from home_product_finder_backend import store
    from home_product_finder_backend.app import app

    scrape = tmp_path / "_scrape"
    scrape.mkdir()
    righe = [
        # Omonima n.1: riempie tutto a poco prezzo.
        {**_scrape_rows()[0], "nome": "Heidrun", "link": "https://ex.test/p/h1"},
        # Omonima n.2: 32 cubetti che riempiono meta' del vano e costano il
        # doppio — battuta dalla n.1 su tutti e tre i fronti insieme.
        {
            **_scrape_rows()[0],
            "nome": "Heidrun",
            "prezzo": 0.5,
            "a": 10.0,
            "b": 10.0,
            "h": 10.0,
            "link": "https://ex.test/p/h2",
        },
    ]
    (scrape / "box.json").write_text(json.dumps(righe), encoding="utf-8")
    monkeypatch.setattr(store, "SCRAPE_DIR", scrape)
    monkeypatch.setattr(spazi_mod, "SPAZI_FILE", tmp_path / "assente.json")
    monkeypatch.setattr(spazi_mod, "CACHE_FILE", tmp_path / "_cache" / "home.json")
    monkeypatch.setattr(spazi_mod, "_arredi_da_home", lambda: (_arredi_home(), False))

    soluzioni = TestClient(app).get("/api/spaces").json()[0]["vani"][0]["soluzioni"]
    per_id = {s["id"]: s for s in soluzioni}
    # Le due omonime restano due righe distinte, con verdetti indipendenti.
    assert len([s for s in soluzioni if s["nome"] == "Heidrun"]) == 2
    assert per_id["Heidrun|20.0x20.0x10.0"]["ottimale"] is True
    assert per_id["Heidrun|10.0x10.0x10.0"]["ottimale"] is False


def test_unmeasured_compartment_is_not_guessed(client):
    """Footprint known, height unknown -> listed, but never ranked."""
    vano = client.get("/api/spaces").json()[0]["vani"][1]
    assert vano["id"] == "T2"
    assert vano["n_soluzioni"] == 0
    assert vano["soluzioni"] == []


def test_local_spaces_are_appended_to_home_furniture(client):
    spazi = client.get("/api/spaces").json()
    assert [s["fonte"] for s in spazi] == ["home", "locale"]
    assert spazi[1]["slug"] == "pile"
    assert spazi[1]["vani"] == []


def test_adjustable_shelving_derives_the_shelf_pitch(tmp_path, monkeypatch):
    """On shelving the height is an output: the box sets where shelves clamp."""
    from fastapi.testclient import TestClient

    from home_product_finder_backend import spazi as spazi_mod
    from home_product_finder_backend import store
    from home_product_finder_backend.app import app

    scrape_dir = tmp_path / "_scrape"
    scrape_dir.mkdir()
    (scrape_dir / "box.json").write_text(json.dumps(_scrape_rows()), encoding="utf-8")
    monkeypatch.setattr(store, "SCRAPE_DIR", scrape_dir)
    monkeypatch.setattr(spazi_mod, "SPAZI_FILE", tmp_path / "assente.json")
    monkeypatch.setattr(spazi_mod, "CACHE_FILE", tmp_path / "_cache" / "home.json")
    monkeypatch.setattr(
        spazi_mod,
        "_arredi_da_home",
        lambda: (
            [
                {
                    "slug": "scaffale",
                    "titolo": "Scaffale",
                    "vani": [
                        {
                            "id": "S1",
                            "nome": "S1",
                            "L": 40,
                            "P": 40,
                            "H": None,
                            "regolabile": True,
                            "montante": 160,
                            "ripiani": 4,
                            "misurato": True,
                        }
                    ],
                }
            ],
            False,
        ),
    )

    vano = TestClient(app).get("/api/spaces").json()[0]["vani"][0]
    righe = {r["nome"]: r for r in vano["soluzioni"]}

    piccolo = righe["Box 20x20x10"]
    # 10 cm box + 3 cm of shelf = 13 cm pitch; 160/13 = 12 levels, capped at 4.
    assert piccolo["passo_cm"] == 13.0
    assert piccolo["livelli"] == 4
    assert piccolo["pezzi"] == 2 * 2 * 4

    # 50 cm box + 3 = 53 cm pitch -> only 3 levels fit on a 160 upright.
    assert righe["Box 30x30x50"]["livelli"] == 3


def test_spaces_legacy_italian_alias(client):
    assert client.get("/api/spazi").json() == client.get("/api/spaces").json()


def test_home_down_serves_the_cached_furniture(tmp_path, monkeypatch):
    """Home offline must degrade to the last answer, flagged — not to nothing."""
    from fastapi.testclient import TestClient

    from home_product_finder_backend import spazi as spazi_mod
    from home_product_finder_backend import store
    from home_product_finder_backend.app import app

    scrape_dir = tmp_path / "_scrape"
    scrape_dir.mkdir()
    (scrape_dir / "box.json").write_text(json.dumps(_scrape_rows()), encoding="utf-8")
    monkeypatch.setattr(store, "SCRAPE_DIR", scrape_dir)
    monkeypatch.setattr(spazi_mod, "SPAZI_FILE", tmp_path / "assente.json")

    cache = tmp_path / "_cache" / "home.json"
    cache.parent.mkdir()
    cache.write_text(json.dumps(_arredi_home()), encoding="utf-8")
    monkeypatch.setattr(spazi_mod, "CACHE_FILE", cache)
    # Unroutable address: the fetch fails the way a stopped Home would.
    monkeypatch.setattr(spazi_mod, "HOME_API", "http://127.0.0.1:9")

    spazi = TestClient(app).get("/api/spaces").json()
    assert spazi[0]["fonte"] == "cache-home"
    assert spazi[0]["vani"][0]["n_soluzioni"] > 0
