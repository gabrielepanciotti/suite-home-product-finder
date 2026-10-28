"""Node view declaration, available both locally and in the Docker image."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from suite_backend_core.vista import VistaSpec


DEFAULT_VISTA: dict[str, Any] = {
    "sezioni": [
        {"id": "cerca", "titolo": "Cerca", "min": "player"},
        {"id": "risultati", "titolo": "Risultati", "min": "player"},
        {"id": "salvati", "titolo": "Salvati", "min": "player"},
        {"id": "spazi", "titolo": "Spazi da riempire", "min": "player"},
        {"id": "contenere", "titolo": "In cosa lo metto", "min": "player"},
        {"id": "catalogo", "titolo": "Catalogo scatole", "min": "player"},
        {"id": "impostazioni", "titolo": "Impostazioni", "min": "admin"},
    ],
    "azioni": {
        "ricerca.crea": "creator",
        "ricerca.elimina": "admin",
        "salvato.crea": "creator",
        "salvato.modifica": "creator",
        "salvato.elimina": "creator",
        "impostazioni.modifica": "admin",
    },
}


def load_vista_spec() -> VistaSpec:
    """Load the checked-in declaration, with a Docker-safe default."""
    config_path = Path(__file__).resolve().parents[2] / "node.config"
    vista = DEFAULT_VISTA
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        vista = config.get("vista", DEFAULT_VISTA)
    return VistaSpec.model_validate(vista)
