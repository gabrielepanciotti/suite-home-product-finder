"""Standard ASGI entrypoint for the deploy/ stack.

The suite deploy convention launches the app as ``<backendPkg>.main:app``
(see deploy/backend.Dockerfile). This node defines the FastAPI instance in
``app.py``; this module re-exports it so the standard Dockerfile works without
duplicating the application code. Native dev keeps using
``python -m home_product_finder_backend`` (see ``__main__.py``).
"""
from __future__ import annotations

from home_product_finder_backend.app import app

__all__ = ["app"]
