"""Core domain E2E: list -> detail -> choice -> shopping list -> history.

The flow runs on a temporary vault (the comparison JSON files are the source
of truth) and on a real sqlite DB: the choice is persisted in ``choice_log``
(additive relational replica) and read back from
``/api/comparisons/{slug}/history``.

Also covers the legacy Italian route aliases (``/api/confronti[...]``,
``/api/acquisti``) that external consumers — e.g. the Home cluster widget —
still call.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest


def _sample_confronto() -> dict:
    return {
        "slug": "scatole-test",
        "titolo": "Scatole sottoletto",
        "sottotitolo": "50L trasparenti con ruote",
        "metrica": "€/litro",
        "gruppi": [
            {
                "nome": "Trasparenti",
                "prodotti": [
                    {
                        "id": "p1",
                        "nome": "Scatola A 50L",
                        "negozio": "Ikea",
                        "prezzo": 12.5,
                        "stato": None,
                        "quantita": 1,
                        "link": "https://example.com/a",
                        "immagine": None,
                    },
                    {
                        "id": "p2",
                        "nome": "Scatola B 55L",
                        "negozio": "Amazon",
                        "prezzo": 15.0,
                        "stato": None,
                        "quantita": 1,
                        "link": "https://example.com/b",
                        "immagine": None,
                    },
                ],
            }
        ],
    }


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from fastapi.testclient import TestClient

    from home_product_finder_backend import db, store
    from home_product_finder_backend.app import app
    from suite_backend_core import Base

    # Temporary vault: the domain's data source.
    confronti_dir = tmp_path / "confronti"
    confronti_dir.mkdir()
    (confronti_dir / "scatole-test.json").write_text(
        json.dumps(_sample_confronto(), ensure_ascii=False), encoding="utf-8"
    )
    monkeypatch.setattr(store, "CONFRONTI_DIR", confronti_dir)
    monkeypatch.setattr(store, "LOG_FILE", tmp_path / "log.md")

    # Node DB schema (choice_log) on the test sqlite.
    db.session_factory()  # initializes the lazy engine

    async def _create_all() -> None:
        async with db._engine.begin() as conn:  # noqa: SLF001 — test setup
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create_all())
    return TestClient(app)


def test_e2e_comparison_choice_purchases_history(client):
    # 1) Comparison list: the temporary vault exposes the test comparison.
    r = client.get("/api/comparisons")
    assert r.status_code == 200
    summaries = r.json()
    assert [c["slug"] for c in summaries] == ["scatole-test"]
    assert summaries[0]["n_prodotti"] == 2
    assert summaries[0]["n_da_comprare"] == 0

    # 2) Comparison detail.
    r = client.get("/api/comparisons/scatole-test")
    assert r.status_code == 200
    assert r.json()["titolo"] == "Scatole sottoletto"

    # 3) Choice: p1 x2 to buy, p2 not.
    r = client.post(
        "/api/comparisons/scatole-test/choice", json={"selezioni": {"p1": 2}}
    )
    assert r.status_code == 200
    data = r.json()
    prodotti = {p["id"]: p for g in data["gruppi"] for p in g["prodotti"]}
    assert prodotti["p1"]["stato"] == "da-comprare"
    assert prodotti["p1"]["quantita"] == 2
    assert prodotti["p2"]["stato"] is None

    # 4) Aggregated shopping list.
    r = client.get("/api/purchases")
    assert r.status_code == 200
    acquisti = r.json()
    assert len(acquisti) == 1
    assert acquisti[0]["nome"] == "Scatola A 50L"
    assert acquisti[0]["quantita"] == 2

    # 5) Relational history: the choice was persisted in choice_log.
    r = client.get("/api/comparisons/scatole-test/history")
    assert r.status_code == 200
    storico = r.json()
    assert len(storico) >= 1
    assert storico[0]["slug"] == "scatole-test"
    assert "Scatola A 50L x2" in storico[0]["scelti"]


def test_legacy_italian_routes_still_work(client):
    """Compat aliases: old Italian routes answer identically to the new ones."""
    assert client.get("/api/confronti").status_code == 200
    assert client.get("/api/confronti/scatole-test").status_code == 200
    assert client.get("/api/acquisti").status_code == 200
    assert client.get("/api/confronti/scatole-test/storico").status_code == 200
    r = client.post(
        "/api/confronti/scatole-test/scelta", json={"selezioni": {"p2": 1}}
    )
    assert r.status_code == 200
    prodotti = {p["id"]: p for g in r.json()["gruppi"] for p in g["prodotti"]}
    assert prodotti["p2"]["stato"] == "da-comprare"
