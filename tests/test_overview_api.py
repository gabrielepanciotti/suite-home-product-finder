"""GET /api/overview: scheda-nodo pubblica, 200 + chiavi + degrado graceful.

I test girano su sqlite (``information_schema`` assente): la sezione
``database`` degrada con ``error`` e ``live: false``, ma l'endpoint risponde
comunque 200 con l'intero manifest — esattamente il contratto "graceful".
"""
from __future__ import annotations


def _client():
    from fastapi.testclient import TestClient

    from home_product_finder_backend.app import app

    return TestClient(app)


def test_overview_ok_shape():
    r = _client().get("/api/overview")
    assert r.status_code == 200
    body = r.json()

    identity = body["identity"]
    assert identity["slug"] == "homeProductFinder"
    assert identity["name"] == "HomeProductFinder"

    for key in ("functions", "notifications", "collaborations", "brain"):
        assert key in body, key
    assert isinstance(body["functions"], list)
    assert len(body["functions"]) > 0

    database = body["database"]
    assert "tables" in database
    assert "highlights" in database
    assert "live" in body


def test_overview_public_no_auth():
    """Nessun token/cookie/header: l'endpoint e' pubblico come /api/health."""
    r = _client().get("/api/overview")
    assert r.status_code == 200


def test_overview_degrades_gracefully_without_postgres():
    """DB non-Postgres (niente information_schema) -> 200, error nel payload."""
    r = _client().get("/api/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["live"] is False
    assert body["database"]["error"] == "database query failed"
