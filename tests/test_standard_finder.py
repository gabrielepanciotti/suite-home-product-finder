"""Finder-family API additions keep the legacy surface compatible."""
from __future__ import annotations

import importlib
import json
from pathlib import Path

import httpx
import pytest

from home_product_finder_backend.vista import DEFAULT_VISTA

ROOT = Path(__file__).resolve().parents[1]


def _transport() -> httpx.ASGITransport:
    from home_product_finder_backend.app import app

    return httpx.ASGITransport(app=app)


async def _get(path: str) -> httpx.Response:
    async with httpx.AsyncClient(
        transport=_transport(), base_url="http://testserver",
    ) as client:
        return await client.get(path)


@pytest.mark.asyncio
async def test_not_found_uses_standard_error_envelope() -> None:
    response = await _get("/api/comparisons/__not_found__")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Risorsa non trovata.",
            "field": None,
        },
        "detail": "Comparison '__not_found__' not found",
    }


@pytest.mark.asyncio
async def test_validation_error_uses_standard_error_envelope() -> None:
    response = await _get("/api/packing?a=zero&b=2&h=3")

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == {
        "code": "validation_error",
        "message": "I dati inviati non sono validi.",
        "field": "a",
    }
    assert isinstance(body["detail"], list)


@pytest.mark.asyncio
async def test_vista_is_available_with_explicit_local_claims(monkeypatch) -> None:
    import home_product_finder_backend.app as app_module

    with monkeypatch.context() as local_environment:
        local_environment.setenv("ALLOW_DEV_OWNER", "1")
        local_environment.setenv("LIFE_VISTA_DEFAULT_ROLE", "admin")
        app_module = importlib.reload(app_module)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app_module.app),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/api/vista")

    importlib.reload(app_module)
    assert response.status_code == 200
    assert response.json()["ruolo"] == "admin"


def test_default_vista_matches_node_config() -> None:
    config = json.loads((ROOT / "node.config").read_text(encoding="utf-8"))

    assert DEFAULT_VISTA == config["vista"]
