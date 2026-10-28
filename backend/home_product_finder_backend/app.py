"""HomeProductFinder API (FastAPI, port 10008).

Exposes product comparisons as reusable data: the structure is fixed, only the
values in the JSON files change. Endpoints:
  GET  /api/comparisons               list of comparisons (home)
  GET  /api/comparisons/{slug}        comparison detail (groups + products)
  POST /api/comparisons/{slug}/choice mark the chosen products as `da-comprare`
  GET  /api/comparisons/{slug}/history relational choice history (node DB)
  GET  /api/catalog                   raw box catalogue (every scraped product)
  GET  /api/spaces                    spaces to fill, ranked per compartment
  GET  /api/packing                   which box holds N objects (inverse of /spaces)
  GET  /api/preferences               per-compartment verdicts (pinned / ruled out)
  PUT  /api/preferences               replace one compartment's verdicts
  GET  /api/purchases                 shopping list (all `da-comprare` items)
  /api/images/...                     product images (static)

Compatibility aliases (legacy Italian routes, kept working for existing
consumers — e.g. the Home cluster widget still calls /api/confronti):
  /api/confronti[...]  ->  /api/comparisons[...]
  /api/acquisti        ->  /api/purchases
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from suite_backend_core.vista import MemoryPreferenceStore, make_vista_router
from suite_backend_core.vista_claims import make_claims_dependency

from . import barattoli, catalog, contenere, db, preferenze, store
from .errors import install_error_handlers
from .overview import router as overview_router
from .vista import load_vista_spec

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="HomeProductFinder API", version="1.0")
install_error_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3342", "http://127.0.0.1:3342"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Live node card (public, like /api/health).
app.include_router(overview_router)
app.include_router(
    make_vista_router(
        load_vista_spec(),
        MemoryPreferenceStore(),
        make_claims_dependency("homeProductFinder"),
        "homeProductFinder",
    )
)

if store.IMAGES_DIR.exists():
    app.mount("/api/images", StaticFiles(directory=str(store.IMAGES_DIR)), name="images")


class SceltaIn(BaseModel):
    selezioni: dict[str, int]  # {product_id: quantity}


class PreferenzeIn(BaseModel):
    chiave: str  # "<spazio>/<vano>"
    preferiti: list[str] = []
    scartati: list[str] = []


@app.get("/api/comparisons")
@app.get("/api/confronti", include_in_schema=False)  # legacy alias
def get_comparisons() -> list[dict]:
    return store.list_confronti()


@app.get("/api/comparisons/{slug}")
@app.get("/api/confronti/{slug}", include_in_schema=False)  # legacy alias
async def get_comparison(slug: str) -> dict:
    try:
        return store.get_confronto(slug)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Comparison '{slug}' not found")


@app.post("/api/comparisons/{slug}/choice")
@app.post("/api/confronti/{slug}/scelta", include_in_schema=False)  # legacy alias
async def post_choice(slug: str, payload: SceltaIn) -> dict:
    try:
        data = store.set_scelta(slug, payload.selezioni)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Comparison '{slug}' not found")
    # Additive: persist the choice to the node DB too (best-effort, never blocks
    # the response — the source of truth remains the JSON in the vault).
    await _persist_choice(data)
    return data


async def _persist_choice(data: dict) -> None:
    factory = db.session_factory()
    if factory is None:
        return
    scelti = [
        f"{pr['nome']} x{int(pr.get('quantita', 1))}"
        for g in data["gruppi"]
        for pr in g["prodotti"]
        if pr.get("stato") == "da-comprare"
    ]
    try:
        async with factory() as session:
            session.add(
                db.ChoiceLog(
                    slug=data["slug"],
                    titolo=data["titolo"],
                    scelti="; ".join(scelti),
                )
            )
            await session.commit()
    except Exception:  # noqa: BLE001 — the DB is additive, it must never break the choice
        logger.warning("choice_log persist failed for %s", data.get("slug"), exc_info=True)


@app.get("/api/comparisons/{slug}/history")
@app.get("/api/confronti/{slug}/storico", include_in_schema=False)  # legacy alias
async def get_history(slug: str, limit: int = 20) -> list[dict]:
    """Relational history of a comparison's choices (from the node DB).

    Empty when the DB is not configured (JSON-only mode).
    """
    from sqlalchemy import select

    factory = db.session_factory()
    if factory is None:
        return []
    async with factory() as session:
        rows = (
            await session.execute(
                select(db.ChoiceLog)
                .where(db.ChoiceLog.slug == slug)
                .order_by(db.ChoiceLog.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
    return [
        {"id": r.id, "slug": r.slug, "titolo": r.titolo,
         "scelti": r.scelti, "created_at": r.created_at.isoformat()}
        for r in rows
    ]


@app.get("/api/catalog")
@app.get("/api/catalogo", include_in_schema=False)  # legacy alias
def get_catalog() -> dict:
    """Raw box catalogue (every scraped product), with per-shop counts.

    Unfiltered on purpose: it is a few hundred rows, so the UI filters and
    sorts client-side and stays responsive without a round trip per keystroke.
    """
    return {"items": catalog.list_catalogo(), "negozi": catalog.catalogo_negozi()}


@app.get("/api/spaces")
@app.get("/api/spazi", include_in_schema=False)  # legacy alias
def get_spaces() -> list[dict]:
    """Spaces to fill, each measured compartment with its ranked tessellations."""
    from . import spazi

    return spazi.list_spazi()


@app.get("/api/packing")
@app.get("/api/contenere", include_in_schema=False)  # italian alias
def get_packing(
    a: float = Query(gt=0, description="object width in cm"),
    b: float = Query(gt=0, description="object depth in cm"),
    h: float = Query(gt=0, description="object height in cm"),
    n: int = Query(1, gt=0, le=10_000, description="how many to store"),
    in_piedi: bool = Query(True, description="the object may not lie down"),
    impilabili: bool = Query(False, description="the object may be stacked"),
    margine: float = Query(
        contenere.MARGINE_DEFAULT, ge=0, le=10,
        description="cm subtracted per side: external size -> usable inside",
    ),
    max_scatole: int | None = Query(None, gt=0, description="cap on containers"),
    # Annotated, unlike the scalars above: a repeated query parameter needs a
    # list annotation, and only this form keeps the default out of the signature.
    materiali: Annotated[
        list[str] | None, Query(description="keep only these materials")
    ] = None,
    escludi: Annotated[
        list[str] | None, Query(description="drop these materials")
    ] = None,
    ignoti: bool = Query(True, description="keep boxes that declare no material"),
) -> dict:
    """Which box holds N objects of the given size, and how many are needed.

    The inverse of /api/spaces: there the container is fixed and the catalogue
    fills it, here the content is fixed and the catalogue contains it.

    The material filter runs server-side on purpose: cardboard boxes are the
    cheapest in the catalogue, so they win the cost axis and would occupy the
    whole page before anything made of plastic reached the browser.
    """
    return contenere.cerca(
        contenere.Oggetto(a=a, b=b, h=h),
        n,
        contenere.Opzioni(
            in_piedi=in_piedi,
            impilabili=impilabili,
            margine=margine,
            max_scatole=max_scatole,
            materiali=frozenset(materiali or ()),
            escludi=frozenset(escludi or ()),
            ignoti=ignoti,
        ),
    )


@app.get("/api/jars")
@app.get("/api/barattoli", include_in_schema=False)  # italian alias
def get_jars() -> dict:
    """Barattoli noti per marca: la preselezione di /api/packing.

    Sceglierli per nome invece che a misure digitate evita l'errore che conta —
    fra due Bormioli alti uguale il diametro cambia da 10,6 a 16,0 cm, e con esso
    quante scatole servono.
    """
    return barattoli.elenco()


@app.get("/api/preferences")
@app.get("/api/preferenze", include_in_schema=False)  # legacy alias
def get_preferences() -> dict:
    """Per-compartment verdicts: boxes pinned to the top, boxes ruled out."""
    return preferenze.leggi()


@app.put("/api/preferences")
@app.put("/api/preferenze", include_in_schema=False)  # legacy alias
def put_preferences(payload: PreferenzeIn) -> dict:
    """Replace one compartment's verdicts; returns the whole updated set."""
    try:
        return preferenze.scrivi_vano(
            payload.chiave, payload.preferiti, payload.scartati
        )
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"vault not writable: {exc}")


@app.get("/api/purchases")
@app.get("/api/acquisti", include_in_schema=False)  # legacy alias
def get_purchases() -> list[dict]:
    return store.lista_acquisti()


@app.get("/api/export-contribution")
async def export_contribution() -> list[dict]:
    """Life standard: contribution bundle — only rows with visibility='public'.

    Always an empty list for this node (personal data, all private).
    """
    from sqlalchemy import select

    factory = db.session_factory()
    if factory is None:
        return []
    async with factory() as session:
        rows = (
            await session.execute(
                select(db.ChoiceLog).where(db.ChoiceLog.visibility == "public")
            )
        ).scalars().all()
    return [
        {"id": r.id, "slug": r.slug, "titolo": r.titolo,
         "scelti": r.scelti, "created_at": r.created_at.isoformat(),
         "visibility": r.visibility}
        for r in rows
    ]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/health")
def api_health() -> dict:
    return {"status": "ok"}
