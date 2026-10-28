"""I barattoli noti: GET /api/jars (+ /api/barattoli).

Sono la preselezione del modulo "In cosa lo metto". Cosa conta: che si leggano
tutti i file `barattoli-*.json` del vault, che una riga senza diametro non arrivi
al frontend, che un file rotto non porti giù l'endpoint, e che il campanello
d'allarme del produttore incoerente sopravviva fino alla pagina.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _bormioli() -> list[dict]:
    return [
        {
            "id": "262",
            "marca": "Bormioli Rocco",
            "nome": "Vaso ermetico 150 cl  Fido",
            "capacita_cl": 150.0,
            "altezza_cm": 22.0,
            "diametro_cm": 10.6,
            "linea": "Fido",
            "url": "https://ex.test/262",
        },
        {
            "id": "1003",
            "marca": "Bormioli Rocco",
            "nome": "Vaso 300 cl - Imboccatura larga Quattro Stagioni",
            "capacita_cl": 317.5,
            "altezza_cm": 21.8,
            "diametro_cm": 16.0,
            "linea": "Quattro Stagioni",
            "url": "https://ex.test/1003",
            "conflitto": "il sito dichiara misure diverse",
        },
        # Senza diametro non serve a niente: non deve arrivare al frontend.
        {
            "id": "999",
            "marca": "Bormioli Rocco",
            "nome": "Vaso misterioso",
            "altezza_cm": 12.0,
            "linea": "Fido",
        },
    ]


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from fastapi.testclient import TestClient
    from home_product_finder_backend import barattoli
    from home_product_finder_backend.app import app

    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "barattoli-bormioli.json").write_text(
        json.dumps(_bormioli()), encoding="utf-8"
    )
    monkeypatch.setattr(barattoli, "VAULT", vault)
    return TestClient(app)


def test_grouped_by_brand_and_sorted_by_height(client):
    r = client.get("/api/jars")
    assert r.status_code == 200, r.text
    dati = r.json()

    assert [m["marca"] for m in dati["marche"]] == ["Bormioli Rocco"]
    vasi = dati["marche"][0]["barattoli"]
    # Il vaso senza diametro è stato scartato, gli altri sono in ordine di altezza.
    assert [v["altezza_cm"] for v in vasi] == [21.8, 22.0]
    assert dati["n"] == 2


def test_the_label_names_the_line_once(client):
    """Il sito ripete la linea in coda al nome; sul chip basta una volta."""
    vasi = client.get("/api/jars").json()["marche"][0]["barattoli"]
    fido = next(v for v in vasi if v["altezza_cm"] == 22.0)
    assert fido["etichetta"] == "Fido · Vaso ermetico 150 cl"


def test_identity_is_brand_plus_name(client):
    """Due produttori possono chiamare uguale la loro serie."""
    vasi = client.get("/api/jars").json()["marche"][0]["barattoli"]
    assert all(v["id"].startswith("Bormioli Rocco|") for v in vasi)
    assert len({v["id"] for v in vasi}) == len(vasi)


def test_the_conflict_warning_survives_to_the_page(client):
    """Se il produttore si contraddice, la pagina deve poterlo dire."""
    vasi = client.get("/api/jars").json()["marche"][0]["barattoli"]
    qs = next(v for v in vasi if v["altezza_cm"] == 21.8)
    assert qs["conflitto"] == "il sito dichiara misure diverse"
    fido = next(v for v in vasi if v["altezza_cm"] == 22.0)
    assert fido["conflitto"] is None


def test_a_broken_file_does_not_take_the_endpoint_down(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Un file illeggibile costa il suo contenuto, non l'intera preselezione."""
    from fastapi.testclient import TestClient
    from home_product_finder_backend import barattoli
    from home_product_finder_backend.app import app

    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "barattoli-rotto.json").write_text("{ non json", encoding="utf-8")
    (vault / "barattoli-bormioli.json").write_text(
        json.dumps(_bormioli()[:1]), encoding="utf-8"
    )
    monkeypatch.setattr(barattoli, "VAULT", vault)

    dati = TestClient(app).get("/api/jars").json()
    assert dati["n"] == 1


def test_italian_alias(client):
    assert client.get("/api/barattoli").json() == client.get("/api/jars").json()
