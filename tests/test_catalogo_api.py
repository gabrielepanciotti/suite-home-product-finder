"""Raw box catalogue: GET /api/catalog (+ legacy /api/catalogo).

The catalogue is the flat, deduplicated view over `vault/confronti/_scrape/` —
the dumps produced by the shop CLIs. What matters here: the same product found
under several queries collapses into one row keeping the most informative name,
rows without usable dimensions are dropped (the UI filters by size), and the
value metric of the domain (€/litre) is computed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _rows() -> list[dict]:
    return [
        {
            "shop": "action",
            "nome": "Contenitore",
            "prezzo": 4.49,
            "a": 39.0,
            "b": 29.0,
            "h": 26.0,
            "link": "https://action.example/p/1",
            "img": "",
        },
        {
            "shop": "ikea",
            "nome": "SAMLA Contenitore",
            "prezzo": 10.0,
            "a": 56.0,
            "b": 39.0,
            "h": 42.0,
            "link": "https://ikea.example/p/2",
            "img": "",
        },
        # Unusable: no dimensions -> must not reach the catalogue.
        {
            "shop": "maurys",
            "nome": "SCATOLA SENZA MISURE",
            "prezzo": 3.0,
            "a": 0,
            "b": 0,
            "h": 0,
            "link": "https://maurys.example/p/3",
            "img": "",
        },
    ]


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from fastapi.testclient import TestClient

    from home_product_finder_backend import store
    from home_product_finder_backend.app import app

    scrape_dir = tmp_path / "_scrape"
    scrape_dir.mkdir()
    (scrape_dir / "action-contenitore.json").write_text(
        json.dumps(_rows()), encoding="utf-8"
    )
    # Same Action product under a second query, with a fuller name and an image.
    (scrape_dir / "action-scatola.json").write_text(
        json.dumps(
            [
                {
                    **_rows()[0],
                    "nome": "Contenitore 19 litri | 39x29x26 cm",
                    "img": "https://asset.example/1.webp",
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(store, "SCRAPE_DIR", scrape_dir)

    from home_product_finder_backend import catalog

    classi = tmp_path / "classi.json"
    classi.write_text(
        json.dumps(
            {
                "categorie_scatola": ["action-contenitore", "action-scatola"],
                "nome_esclude": ["stura"],
                "nome_include": ["scatol", "contenitor"],
                "decisioni": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(catalog, "CLASSI_FILE", classi)

    return TestClient(app)


def test_catalogue_dedupes_and_computes_value(client):
    body = client.get("/api/catalog").json()
    items = body["items"]

    # 3 rows in one file + 1 duplicate in another -> 2 usable, deduplicated.
    assert [i["negozio"] for i in items] == ["action", "ikea"]  # cheapest first
    assert body["negozi"] == [{"negozio": "action", "n": 1}, {"negozio": "ikea", "n": 1}]

    action = items[0]
    assert action["nome"] == "Contenitore 19 litri | 39x29x26 cm"  # fullest name wins
    assert action["img"] == "https://asset.example/1.webp"  # image folded in
    assert sorted(action["fonti"]) == ["action-contenitore", "action-scatola"]
    assert action["volume_l"] == pytest.approx(29.4, abs=0.1)
    assert action["eur_per_l"] == pytest.approx(0.153, abs=0.001)


def test_classification_decides_by_category_then_name(tmp_path, monkeypatch):
    """A plunger has three dimensions and a price: only the rules exclude it."""
    from home_product_finder_backend import catalog

    regole = {
        "categorie_scatola": ["action-scatola"],
        "nome_esclude": ["stura"],
        "nome_include": ["scatol"],
        "decisioni": {"https://ex.test/p/9": {"scatola": True, "perche": "controllato"}},
    }

    def classifica(nome, fonti, id_="x"):
        item = {"id": id_, "nome": nome, "fonti": fonti}
        return catalog.classifica_item(item, regole)

    # Name exclusion wins over a trusted category: broad scrapes leak.
    assert classifica("Stura lavandini", ["action-scatola"])[0] == "non-scatola"
    assert classifica("Qualunque cosa", ["action-scatola"])[0] == "scatola"
    assert classifica("Scatolone 50 litri", ["action-rsc-casalinghi"])[0] == "scatola"
    # Broad category + inconclusive name: asks to be decided, does not guess.
    classe, perche = classifica("Sgabello pieghevole", ["action-rsc-casalinghi"])
    assert classe == "da-classificare"
    assert "nome non conclusivo" in perche
    # An explicit decision overrides every rule, including the exclusions.
    assert classifica("Stura lavandini", [], "https://ex.test/p/9") == (
        "scatola",
        "controllato",
    )


def test_catalogue_legacy_italian_alias(client):
    assert client.get("/api/catalogo").json() == client.get("/api/catalog").json()


def test_catalogue_empty_when_no_scrape_dir(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from home_product_finder_backend import store
    from home_product_finder_backend.app import app

    monkeypatch.setattr(store, "SCRAPE_DIR", tmp_path / "assente")
    assert TestClient(app).get("/api/catalog").json() == {"items": [], "negozi": []}
