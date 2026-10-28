"""Node health / smoke: the node has its vital pieces and the API responds.

No Postgres required: /api/health does not touch the DB and the routes answer
with their contract's status codes (never 404 on existing routes).
"""
from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _client():
    from fastapi.testclient import TestClient

    from home_product_finder_backend.app import app

    return TestClient(app)


def test_health_endpoint_ok():
    r = _client().get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_routers_mounted():
    """The domain routes exist (non-404); this node has no auth-gated routes."""
    client = _client()
    assert client.get("/api/comparisons").status_code == 200
    assert client.get("/api/purchases").status_code == 200
    assert client.get("/api/overview").status_code == 200
    # Legacy aliases still mounted.
    assert client.get("/api/confronti").status_code == 200
    assert client.get("/api/acquisti").status_code == 200
    # Unknown slug: explicit 404 with detail, not a routing hole.
    r = client.get("/api/comparisons/__does_not_exist__")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"]


def test_functionalities_toml_is_real():
    data = tomllib.loads(
        (ROOT / ".claude" / "functionalities.toml").read_text(encoding="utf-8")
    )
    functionalities = data.get("functionality", [])
    assert len(functionalities) >= 5
    for fn in functionalities:
        assert fn["key"]
        assert fn["label"]
        assert fn["agent"]


def test_overview_manifest_generated():
    manifest = ROOT / "overview.manifest.json"
    assert manifest.exists(), "run suite_core.nodes node-overview to generate it"


def test_node_config_identity():
    cfg = json.loads((ROOT / "node.config").read_text(encoding="utf-8"))
    assert cfg["slug"] == "homeProductFinder"
    assert cfg["type"] == "fastapi-react-app"
