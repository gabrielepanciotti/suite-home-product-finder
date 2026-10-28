"""Per-compartment verdicts: GET/PUT /api/preferences (+ /api/preferenze).

Starring a box in a 96-row ranking is a decision, and a decision has to survive
a reload. These tests pin the contract: a verdict round-trips through the vault,
one compartment never overwrites another, and emptying one leaves no residue.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from fastapi.testclient import TestClient

    from home_product_finder_backend import preferenze
    from home_product_finder_backend.app import app

    monkeypatch.setattr(preferenze, "PREFERENZE_FILE", tmp_path / "pref.json")
    return TestClient(app)


def test_verdicts_round_trip_through_the_vault(client):
    assert client.get("/api/preferences").json() == {"vani": {}}

    client.put(
        "/api/preferences",
        json={
            "chiave": "scaffale-everest/S1",
            "preferiti": ["PAPPIS"],
            "scartati": ["Stura lavandini"],
        },
    )
    assert client.get("/api/preferences").json() == {
        "vani": {
            "scaffale-everest/S1": {
                "preferiti": ["PAPPIS"],
                "scartati": ["Stura lavandini"],
            }
        }
    }


def test_one_compartment_does_not_overwrite_another(client):
    client.put(
        "/api/preferences",
        json={"chiave": "letto/L1", "preferiti": ["VATTENTRÅG"], "scartati": []},
    )
    client.put(
        "/api/preferences",
        json={"chiave": "scaffale/S1", "preferiti": ["PAPPIS"], "scartati": []},
    )
    vani = client.get("/api/preferences").json()["vani"]
    assert sorted(vani) == ["letto/L1", "scaffale/S1"]


def test_emptying_a_compartment_leaves_no_residue(client, tmp_path):
    """No `{"preferiti": []}` rows piling up for every table ever opened."""
    client.put(
        "/api/preferences",
        json={"chiave": "letto/L1", "preferiti": ["X"], "scartati": []},
    )
    body = client.put(
        "/api/preferences",
        json={"chiave": "letto/L1", "preferiti": [], "scartati": []},
    ).json()
    assert body == {"vani": {}}
    assert json.loads((tmp_path / "pref.json").read_text(encoding="utf-8")) == {
        "vani": {}
    }


def test_corrupt_file_does_not_break_the_page(client, tmp_path):
    """A UI aid must degrade to 'no verdicts', never to a 500."""
    (tmp_path / "pref.json").write_text("{ non json", encoding="utf-8")
    assert client.get("/api/preferenze").json() == {"vani": {}}
