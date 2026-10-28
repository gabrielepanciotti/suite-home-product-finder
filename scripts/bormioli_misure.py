"""Misure dei vasi Bormioli Rocco dal sito ufficiale -> vault/barattoli-bormioli.json.

    python scripts/bormioli_misure.py            # riscrive il file nel vault
    python scripts/bormioli_misure.py --stdout   # stampa e basta

Perche' serve: la pagina "In cosa lo metto" (`/api/packing`) chiede altezza e
diametro dell'oggetto, e per i barattoli di casa la fonte giusta e' il produttore,
non un metro appoggiato a occhio. Le misure pubblicate sono ESTERNE — il diametro
e' il punto piu' largo del vetro — che e' esattamente cio' che decide quanti ne
stanno affiancati in una scatola.

Attenzione a due trappole della pagina, entrambe viste sul campo:

* in fondo a ogni scheda c'e' un blocco "Potrebbero interessarti" con ALTRI
  prodotti e le loro misure, nello stesso identico formato. Senza tagliare li',
  un accessorio (tappi, guarnizioni, imbuti) si porta a casa le misure del vaso
  che gli sta accanto, e lo fa in silenzio;
* la capacita' dichiarata nella terna e' quella a raso, non il nome commerciale:
  il "Vaso 300 cl" dichiara 317,5 cl.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://www.bormiolirocco.com"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0"}

# Ogni riga porta la marca: il vault tiene un file per produttore
# (`vault/barattoli-*.json`) e l'API li unisce in un elenco solo.
MARCA = "Bormioli Rocco"

# Gli id di collezione del sito. Le due linee da conserva di casa.
COLLEZIONI = {"Fido": 50, "Quattro Stagioni": 124}

# Dove finisce la scheda e cominciano i prodotti suggeriti.
FINE_SCHEDA = "Potrebbero interessarti"

# Si tiene cio' che E' un contenitore, non cio' che non nomina un accessorio:
# la collezione contiene anche tappi, guarnizioni, imbuti ed etichette, ma
# scartare per parole citate buttava via il "Vaso 300 cl ... senza capsula" —
# un vaso vero, e per giunta uno dei candidati alti 22 cm.
CONTENITORI = ("vaso", "bottiglia", "bottiglietta", "barattolo", "damigiana")

REPO_ROOT = Path(__file__).resolve().parents[1]
DESTINAZIONE = REPO_ROOT / "vault" / "barattoli-bormioli.json"


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:  # noqa: S310
        return r.read().decode("utf-8", "replace")


def _righe(pagina: str) -> list[str]:
    """Il testo della sola scheda, tagliato prima dei prodotti suggeriti."""
    p = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", pagina, flags=re.S | re.I)
    p = html.unescape(re.sub(r"<[^>]+>", "\n", p))
    righe = [r.strip() for r in p.split("\n") if r.strip()]
    for i, r in enumerate(righe):
        if r.startswith(FINE_SCHEDA):
            return righe[:i]
    return righe


def _terna(righe: list[str]) -> tuple[float, float, float] | None:
    """`(capacita_cl, altezza_mm, diametro_mm)` dalle tre righe consecutive."""
    cap = h = d = None
    for r in righe:
        if cap is None and (m := re.match(r"^([\d.,]+)\s*cl\b", r)):
            cap = float(m.group(1).replace(",", "."))
        elif cap is not None and h is None and (m := re.match(r"^h\s*([\d.,]+)\s*mm", r)):
            h = float(m.group(1).replace(",", "."))
        elif h is not None and d is None and (m := re.match(r"^.\s*([\d.,]+)\s*mm", r)):
            d = float(m.group(1).replace(",", "."))
            return cap, h, d
    return None


def scheda(pid: str, slug: str) -> dict | None:
    righe = _righe(_get(f"{BASE}/it/product/{pid}/{slug}"))
    if not righe:
        return None
    nome = righe[0]
    if not nome.lower().startswith(CONTENITORI):
        return None
    terna = _terna(righe)
    if terna is None:
        return None
    cap, h, d = terna
    return {
        "id": pid,
        "marca": MARCA,
        "nome": nome,
        "capacita_cl": cap,
        "altezza_cm": round(h / 10, 1),
        "diametro_cm": round(d / 10, 1),
        "url": f"{BASE}/it/product/{pid}/{slug}",
    }


def raccogli() -> list[dict]:
    fuori: list[dict] = []
    for linea, cid in COLLEZIONI.items():
        pagina = _get(f"{BASE}/it/products?collection={cid}")
        prodotti = sorted(set(re.findall(r"/it/product/(\d+)/([a-z0-9\-]+)", pagina)))
        print(f"{linea}: {len(prodotti)} pagine", file=sys.stderr)
        for pid, slug in prodotti:
            try:
                s = scheda(pid, slug)
            except Exception as e:  # una scheda rotta non ferma la raccolta
                print(f"  ! {slug}: {type(e).__name__}", file=sys.stderr)
                continue
            if s is None:
                continue
            s["linea"] = linea
            fuori.append(s)
            time.sleep(0.2)
    return _segnala_conflitti(_unici(fuori))


def _nudo(nome: str) -> str:
    """Il nome senza confezione e senza linea: `Vaso 70 cl`.

    Serve a riconoscere che due schede parlano dello STESSO vetro pur avendo
    titoli diversi ("con tappo", "senza capsula").
    """
    n = nome.lower()
    for pezzo in (" con tappo", " senza tappo", " senza capsula", " con capsula"):
        n = n.replace(pezzo, "")
    for linea in COLLEZIONI:
        n = n.replace(linea.lower(), "")
    return " ".join(n.split())


def _segnala_conflitti(vasi: list[dict]) -> list[dict]:
    """Marca i vasi per cui il sito dichiara misure diverse di se stesso.

    Trovato sul campo: la scheda "Vaso 70 cl con tappo" dichiara h 290 mm, quella
    del "Vaso 70 cl" h 129 mm — stesso vetro, un refuso da qualche parte. Non si
    puo' sapere quale delle due sia giusta, quindi non si sceglie: si segna il
    dubbio e chi legge misura col metro prima di comprare le scatole.

    Il confronto e' fra schede con lo stesso nome nudo, non fra stesse capacita':
    il Fido cilindrico e l'ermetico da 50 cl hanno forme legittimamente diverse.
    """
    gruppi: dict[str, list[dict]] = {}
    for v in vasi:
        gruppi.setdefault(_nudo(v["nome"]), []).append(v)

    for simili in gruppi.values():
        if len(simili) < 2:
            continue
        for campo in ("altezza_cm", "diametro_cm"):
            valori = [v[campo] for v in simili]
            if max(valori) > min(valori) * 1.05:
                for v in simili:
                    v["conflitto"] = (
                        "il sito dichiara misure diverse per lo stesso vaso "
                        f"({campo}: {sorted(valori)}) — verificare col metro"
                    )
                break
    return vasi


def _unici(vasi: list[dict]) -> list[dict]:
    """Un vetro, una riga.

    Lo stesso vaso ha due schede, "con tappo" e "senza capsula"/"senza tappo":
    e' lo stesso vetro venduto in due confezioni, e in una lista di misure
    comparirebbe due volte identico. La chiave e' la geometria, non il nome —
    e si tiene il nome piu' corto, che e' quello del vaso e basta.
    """
    per_chiave: dict[tuple, dict] = {}
    for v in vasi:
        chiave = (v["linea"], v["capacita_cl"], v["altezza_cm"], v["diametro_cm"])
        tenuto = per_chiave.get(chiave)
        if tenuto is None or len(v["nome"]) < len(tenuto["nome"]):
            per_chiave[chiave] = v
    return sorted(
        per_chiave.values(),
        key=lambda x: (x["linea"], x["altezza_cm"], x["capacita_cl"]),
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stdout", action="store_true", help="stampa invece di salvare")
    args = ap.parse_args(argv)

    dati = raccogli()
    testo = json.dumps(dati, ensure_ascii=False, indent=2) + "\n"
    if args.stdout:
        print(testo)
    else:
        DESTINAZIONE.write_text(testo, encoding="utf-8")
        print(f"{len(dati)} contenitori -> {DESTINAZIONE.name}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
