"""Costruisce la FONTE DATI UNICA dell'app Casa-Prodotti: un JSON per confronto.

Per ogni confronto genera `vault/confronti/<slug>.json` e scarica le immagini in
`vault/confronti/images/<slug>/<id>.jpg` (ridimensionate -> app veloce e offline).

Modello dati riusabile per OGNI prodotto (la struttura non cambia mai, cambiano solo
immagine/caratteristiche/valori):
  { id, nome, negozio, immagine, link, prezzo, valore, valore_label, nota,
    consigliato, stato, quantita, specs: [{label, value}, ...] }

Confronto:
  { slug, titolo, sottotitolo, metrica, selezione ("per-gruppo"|"multipla"),
    gruppi: [{ nome, prodotti: [...] }] }
"""
from __future__ import annotations

import io
import json
import os
import shutil
from pathlib import Path

import httpx
from PIL import Image

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "it-IT,it;q=0.9"}
AC = "https://asset.action.com/image/upload/t_digital_square/w_512/"
IK = "https://www.ikea.com/it/it/images/products/"
VAULT = Path(__file__).resolve().parents[1] / "vault"
RAW = str(VAULT / "raw") + os.sep
ROOT = VAULT / "confronti"
MAXPX = 600


def eur(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def epl_label(valore: float | None) -> str:
    return f"{eur(valore)} €/L" if valore is not None else "—"


# ──────────────────────────────────────────────────────────────────────────
# CONFRONTO 1 — Scatole da stoccaggio (vestiti / ingombranti). Selezione: 1 per gruppo.
# Fonte: scripts/gen_chooser_html.py (dati live Action/Maury's/IKEA/Tontarelli).
# ──────────────────────────────────────────────────────────────────────────
SCATOLE = {
    "slug": "scatole-stoccaggio",
    "titolo": "Scatole da stoccaggio (vestiti / ingombranti)",
    "sottotitolo": "Scegli una scatola per ogni collocazione. Metrica di valore: €/Litro (più basso = meglio).",
    "metrica": "€/Litro",
    "selezione": "per-gruppo",
    "gruppi": [
        {"nome": "Sotto il letto", "prodotti": [
            {"id": "sl1", "nome": "Maury's box sottoletto 60x40x14", "negozio": "Maury's",
             "prezzo": 4.99, "valore": 0.20, "consigliato": True,
             "nota": "Il più basso (h 14 cm): entra anche sotto letti bassi. Coperchio + ruote. "
                     "Capacità ~25 L (stimata). Sempre disponibile in negozio.",
             "link": "https://maurysonline.it/box-scatola-sotto-letto-da-60x40xh14cm-in-plastica-con-coperchio-verde",
             "_img": "https://cdn.maurysonline.it/immagini/6075085_0450471-box-scatola-sotto-letto-da-60x40xh14cm-in-plastica-con-coperchio-verde-main.jpeg",
             "specs": [("Capacità", "~25 L"), ("Dim (cm)", "60x40x14"), ("Materiale", "Plastica"), ("Ruote", "Sì")]},
            {"id": "sl2", "nome": "IKEA SAMLA 55L (basso)", "negozio": "IKEA",
             "prezzo": 13.00, "valore": 0.24, "consigliato": True,
             "nota": "55 L reali, dati certi, coperchio a scatto robusto. Senza ruote ma capiente. "
                     "Consegna anche senza IKEA a Udine.",
             "link": "https://www.ikea.com/it/it/p/samla-contenitore-con-coperchio-trasparente-s39440814/",
             "_img": "https://www.ikea.com/it/it/images/products/samla-contenitore-con-coperchio-trasparente__0711818_pe728497_s5.jpg",
             "specs": [("Capacità", "55 L"), ("Dim (cm)", "79x57x18"), ("Materiale", "Trasparente"), ("Ruote", "No")]},
            {"id": "sl3", "nome": "Action contenitore con coperchio 29L", "negozio": "Action",
             "prezzo": 5.95, "valore": 0.21, "consigliato": False,
             "nota": "Economico e basso, con coperchio. Solo in negozio (Action non vende online).",
             "link": "https://www.action.com/it-it/p/2568528/contenitore-con-coperchio/",
             "_img": AC + "13626189.jpg",
             "specs": [("Capacità", "29 L"), ("Dim (cm)", "59x39x18"), ("Materiale", "Plastica"), ("Ruote", "No")]},
            {"id": "sl4", "nome": "Maury's box sottoletto 80x60x17 (Oceano)", "negozio": "Maury's",
             "prezzo": 16.99, "valore": 0.30, "consigliato": False,
             "nota": "Il più capiente da sottoletto (~56 L), con ruote. Coperchio non dichiarato online. "
                     "Disponibile anche online.",
             "link": "https://maurysonline.it/box-sotto-letto-con-ruote-80x60x17cm-in-colore-oceano",
             "_img": "https://cdn.maurysonline.it/immagini/6164229_0444387-box-sotto-letto-con-ruote-80x60x17cm-in-colore-oceano-main.jpeg",
             "specs": [("Capacità", "~56 L"), ("Dim (cm)", "80x60x17"), ("Materiale", "Plastica"), ("Ruote", "Sì")]},
            {"id": "sl5", "nome": "Stefanplast Storage 13054 30L", "negozio": "Leroy Merlin",
             "prezzo": 9.15, "valore": 0.31, "consigliato": False,
             "nota": "Ruote + coperchio, ordinabile online (Leroy Merlin / rivenditori). Consegna ~pochi giorni.",
             "link": "https://www.prezzoforte.it/stefanplast-scatola-multiuso-contenitore-sottoletto-con-ruote-capacit-lt-30-cm-59x39x185-colore-trasparente-linea-storage-13054-p-102880.html",
             "_img": "https://www.prezzoforte.it/images/webp/STEFANPLAST_13054_102880_0.webp",
             "specs": [("Capacità", "30 L"), ("Dim (cm)", "59x39x18,5"), ("Materiale", "Trasparente"), ("Ruote", "Sì")]},
            {"id": "sl6", "nome": "Tontarelli Stock Box 25L", "negozio": "Tontarelli",
             "prezzo": 8.90, "valore": 0.36, "consigliato": False,
             "nota": "Compatto 60x40, ruote + coperchio. Disponibilità secondo punto vendita.",
             "link": "https://www.sme.it/sp/260124700398",
             "_img": "https://rep.sme.it/RepAP?code=D1875147&skey=01cc32a87f4ff57615ddeb15779d96b6&resize=500",
             "specs": [("Capacità", "25 L"), ("Dim (cm)", "60x40x17"), ("Materiale", "PP"), ("Ruote", "Sì")]},
        ]},
        {"nome": "Armadio / mensola", "prodotti": [
            {"id": "ar1", "nome": "Action contenitore con ruote 60L", "negozio": "Action",
             "prezzo": 8.95, "valore": 0.15, "consigliato": False,
             "nota": "Ottimo compromesso prezzo/comodità, con ruote per estrarlo dal ripiano.",
             "link": "https://www.action.com/it-it/p/2533870/contenitore-con-ruote/",
             "_img": AC + "2533870_5715079104003-111_01_q1fvo2.jpg",
             "specs": [("Capacità", "60 L"), ("Dim (cm)", "59x39x36"), ("Materiale", "Plastica"), ("Ruote", "Sì")]},
            {"id": "ar2", "nome": "Action coperchio a clip 80L", "negozio": "Action",
             "prezzo": 10.95, "valore": 0.14, "consigliato": False,
             "nota": "Più capiente, chiusura a clip sicura. Buono se i ripiani sono alti.",
             "link": "https://www.action.com/it-it/p/3000808/contenitore-con-coperchio-a-clip/",
             "_img": AC + "17019061.jpg",
             "specs": [("Capacità", "80 L"), ("Dim (cm)", "58x39x43"), ("Materiale", "Plastica"), ("Ruote", "No")]},
            {"id": "ar3", "nome": "Maury's box porta indumenti 74L", "negozio": "Maury's",
             "prezzo": 9.90, "valore": 0.13, "consigliato": True,
             "nota": "Miglior €/L del confronto, con ruote. Solo in negozio.",
             "link": "https://maurysonline.it/box-contenitore-con-ruote-dimensioni-60x41x40cm-e-coperchio-bianco",
             "_img": "https://cdn.maurysonline.it/immagini/6075081_0438026-box-porta-indumenti-con-ruote-dimensioni-60x41x40cm-e-coperchio-bianco-main_510.jpeg",
             "specs": [("Capacità", "74 L"), ("Dim (cm)", "60x41x40"), ("Materiale", "Plastica opaca bianca"), ("Ruote", "Sì")]},
        ]},
        {"nome": "Cantina / garage", "prodotti": [
            {"id": "ca1", "nome": "Action Heidrun 100L", "negozio": "Action",
             "prezzo": 9.95, "valore": 0.10, "consigliato": True,
             "nota": "Miglior valore in assoluto (0,10 €/L). Negozio + online.",
             "link": "https://www.action.com/it-it/p/2535483/contenitore-heidrun/",
             "_img": AC + "2535483_8010059016510-110_05_y50wtb.jpg",
             "specs": [("Capacità", "100 L"), ("Dim (cm)", "59x45x50"), ("Materiale", "Plastica"), ("Ruote", "No")]},
            {"id": "ca2", "nome": "IKEA SAMLA 130L", "negozio": "IKEA",
             "prezzo": 20.00, "valore": 0.15, "consigliato": False,
             "nota": "Più grande, trasparente (vedi il contenuto), disponibile online.",
             "link": "https://www.ikea.com/it/it/p/samla-contenitore-con-coperchio-trasparente-s29440819/",
             "_img": "https://www.ikea.com/it/it/images/products/samla-contenitore-con-coperchio-trasparente__0711819_pe728498_s5.jpg",
             "specs": [("Capacità", "130 L"), ("Dim (cm)", "79x57x43"), ("Materiale", "Trasparente"), ("Ruote", "No")]},
            {"id": "ca3", "nome": "Tontarelli Box One 140L", "negozio": "OrizzonteShop",
             "prezzo": 29.00, "valore": 0.21, "consigliato": False,
             "nota": "Robusto industriale con chiusura a clip. Il più capiente.",
             "link": "https://www.orizzonteshop.it/products/tontarelli-boxone-storage-ccoperchio-8035940999-tontarelli-ean-8009404212080",
             "_img": "http://www.orizzonteshop.it/cdn/shop/products/immagine-1-tontarelli-boxone-storage-ccoperchio-8035940999-tontarelli-ean-8009404212080.jpg?height=600&width=600",
             "specs": [("Capacità", "140 L"), ("Dim (cm)", "79x52x52"), ("Materiale", "Opaco nero, clip"), ("Ruote", "No")]},
        ]},
    ],
}

# ──────────────────────────────────────────────────────────────────────────
# CONFRONTO 2 — Contenitori alimentari (dispensa / frigo). Selezione: multipla.
# Fonte: scripts/gen_food_xlsx.py. Metrica €/Litro. Foto Maxi = locali in vault/raw.
# ──────────────────────────────────────────────────────────────────────────
# (gruppo, id, nome, negozio, cap_L, materiale, ermetico, prezzo, nota, img, link, consigliato)
FOOD_ROWS = [
    ("Dispensa / ermetici", "d1", "Action barattolo ermetico 1,4L", "Action", 1.4, "Plastica", "Sì", 2.72,
     "Alternativa economica al Ma Maison.", AC + "3218514_8712442227854-110_01_goq5xz.jpg",
     "https://www.action.com/it-it/p/3218514/barattolo-con-chiusura-ermetica/", True),
    ("Dispensa / ermetici", "d2", "Action barattolo 0,8L", "Action", 0.8, "Plastica", "Sì", 1.99,
     "", AC + "3218513_8712442227823-110_02_ev4jgi.jpg", "https://www.action.com/it-it/p/3218513/barattolo/", False),
    ("Dispensa / ermetici", "d3", "Action contenitore vetro 1L", "Action", 1.0, "Vetro", "Sì", 2.59,
     "Vetro.", AC + "3220679_3560231067373-110_05_iy2adl.jpg", "https://www.action.com/it-it/p/3220679/contenitore-in-vetro/", False),
    ("Dispensa / ermetici", "d4", "Action barattolo vetro conserve 1L", "Action", 1.0, "Vetro", "Sì", 2.99,
     "Vetro, per conserve.", AC + "13792752.jpg", "https://www.action.com/it-it/p/2580021/barattolo-per-conserve/", False),
    ("Dispensa / ermetici", "d5", "IKEA 365+ cibi secchi 1,3L", "IKEA", 1.3, "Plastica", "Sì", 3.95,
     "Il più venduto IKEA.", IK + "ikea-365-contenitore-coperchio-cibi-secchi-trasparente-bianco__0711434_pe728250_s5.jpg",
     "https://www.ikea.com/it/it/p/ikea-365-contenitore-coperchio-cibi-secchi-trasparente-bianco-80066723/", False),
    ("Dispensa / ermetici", "d6", "IKEA KORKEN barattolo vetro 1L", "IKEA", 1.0, "Vetro", "Sì", 2.95,
     "Vetro con guarnizione.", IK + "korken-barattolo-con-coperchio-vetro-trasparente__1152252_pe885219_s5.jpg",
     "https://www.ikea.com/it/it/p/korken-barattolo-con-coperchio-vetro-trasparente-10541366/", False),
    ("Dispensa / ermetici", "d7", "Ma Maison Airtight tondo 1L", "Maxi", 1.0, "Plastica", "Sì", 4.99,
     "Fotografato a Maxi.", RAW + "2026-06-14_158_foto.jpg", "", False),
    ("Dispensa / ermetici", "d8", "Ma Maison Airtight 660ml", "Maxi", 0.66, "Plastica", "Sì", 3.99,
     "Fotografato a Maxi.", RAW + "2026-06-14_158_foto.jpg", "", False),
    ("Dispensa / ermetici", "d9", "Ma Maison Clear&Fresh rett. 1L", "Maxi", 1.0, "Plastica", "Sì", 3.99,
     "Fotografato a Maxi.", RAW + "2026-06-14-ma-maison-clear-and-fresh-rettangolare-1l.jpg", "", False),
    ("Dispensa / ermetici", "d10", "Ma Maison Clear&Fresh tondo 1L", "Maxi", 1.0, "Plastica", "Sì", 3.99,
     "Fotografato a Maxi.", RAW + "2026-06-14_159_foto.jpg", "", False),
    ("Dispensa / ermetici", "d11", "Ma Maison Ying Yang 700ml", "Maxi", 0.7, "Plastica", "Sì", 1.99,
     "Fotografato a Maxi.", RAW + "2026-06-14_158_foto.jpg", "", False),
    ("Frigo / avanzi", "f1", "IKEA 365+ contenitore 2,0L", "IKEA", 2.0, "Plastica", "Sì", 2.50,
     "Miglior €/L.", IK + "ikea-365-contenitore-rettangolare-plastica__0711428_pe728244_s5.jpg",
     "https://www.ikea.com/it/it/p/ikea-365-contenitore-rettangolare-plastica-60359152/", True),
    ("Frigo / avanzi", "f2", "Frigochef 1,25L", "Maxi", 1.25, "Plastica", "Coperchio", 2.59,
     "Fotografato a Maxi.", RAW + "2026-06-14-scaffale-contenitori-maxi.jpg", "", False),
    ("Frigo / avanzi", "f3", "Maison du Monde 1,6L clip", "Maxi", 1.6, "Plastica", "Sì clip", 3.50,
     "Fotografato a Maxi.", RAW + "2026-06-14-scaffale-contenitori-maxi.jpg", "", False),
    ("Frigo / avanzi", "f4", "Action Mepal 1,5L", "Action", 1.5, "Plastica", "Sì", 3.99,
     "Brand premium.", AC + "25077426.jpg", "https://www.action.com/it-it/p/3208098/contenitore-per-alimenti-mepal/", False),
    ("Frigo / avanzi", "f5", "Action Curver 1,4L", "Action", 1.4, "Plastica", "Sì", 3.79,
     "", AC + "17623549.jpg", "https://www.action.com/it-it/p/3002389/contenitore-per-alimenti-curver/", False),
    ("Frigo / avanzi", "f6", "Action Mepal 0,75L", "Action", 0.75, "Plastica", "Sì", 2.99,
     "Brand premium.", AC + "25077875.jpg", "https://www.action.com/it-it/p/3208100/contenitore-per-alimenti-mepal/", False),
    ("Frigo / avanzi", "f7", "Maison du Monde 900ml", "Maxi", 0.9, "Plastica", "Coperchio", 4.90,
     "Fotografato a Maxi.", RAW + "2026-06-14-scaffale-contenitori-maxi.jpg", "", False),
    ("Frigo / avanzi", "f8", "Maison du Monde 1,2L", "Maxi", 1.2, "Plastica", "Coperchio", 5.90,
     "Fotografato a Maxi.", RAW + "2026-06-14-scaffale-contenitori-maxi.jpg", "", False),
    ("Frigo / avanzi", "f9", "Action Mepal 0,25L", "Action", 0.25, "Plastica", "Sì", 1.88,
     "Brand premium.", AC + "25077236.jpg", "https://www.action.com/it-it/p/3208097/contenitore-per-alimenti-mepal/", False),
    ("Frigo / avanzi", "f10", "Maison du Monde 400ml", "Maxi", 0.4, "Plastica", "Coperchio", 2.99,
     "Fotografato a Maxi.", RAW + "2026-06-14-scaffale-contenitori-maxi.jpg", "", False),
    ("Set / multipack", "s1", "Maison du Monde set 4x0,5L", "Maxi", 2.0, "Plastica", "Coperchio", 2.99,
     "4 pz = 2L totali.", RAW + "2026-06-14-scaffale-contenitori-maxi.jpg", "", True),
    ("Set / multipack", "s2", "Action Tefal 1L x2", "Action", 2.0, "Plastica", "Sì", 6.95,
     "2 pz = 2L totali.", AC + "28018846.jpg", "https://www.action.com/it-it/p/3208738/contenitori-per-alimenti-tefal/", False),
    ("Set / multipack", "s3", "IKEA PRUTA set 17pz", "IKEA", None, "Plastica", "Sì", 4.95,
     "17 pz misti, frigo/freezer.", IK + "pruta-set-17-contenitori-alim-con-coperch-verde__1383829_pe962689_s5.jpg",
     "https://www.ikea.com/it/it/p/pruta-set-17-contenitori-alim-con-coperch-verde-10597099/", False),
    ("Set / multipack", "s4", "Action contenitori impilabili 3pz", "Action", None, "Plastica", "Coperchio", 5.95,
     "3 pz.", AC + "3218110_8721037720373-110_01_nujg9n.jpg", "https://www.action.com/it-it/p/3218110/contenitori-impilabili/", False),
    ("Set / multipack", "s5", "IKEA 365+ set 6 contenitori", "IKEA", None, "Plastica", "Sì", 17.00,
     "6 pz misti.", IK + "ikea-365-set-6-contenit-alim-con-coperchio-plastica__1109095_pe869821_s5.jpg",
     "https://www.ikea.com/it/it/p/ikea-365-set-6-contenit-alim-con-coperchio-plastica-80526452/", False),
]


def build_food() -> dict:
    gruppi: dict[str, list] = {}
    for grp, pid, nome, neg, cap, mat, erm, prezzo, nota, img, link, cons in FOOD_ROWS:
        valore = round(prezzo / cap, 2) if cap else None
        specs = [("Capacità", f"{eur(cap)} L" if cap else "—"), ("Materiale", mat), ("Ermetico", erm)]
        gruppi.setdefault(grp, []).append({
            "id": pid, "nome": nome, "negozio": neg, "prezzo": prezzo, "valore": valore,
            "consigliato": cons, "nota": nota, "link": link, "_img": img, "specs": specs,
        })
    return {
        "slug": "contenitori-alimentari",
        "titolo": "Contenitori alimentari (dispensa / frigo)",
        "sottotitolo": "Seleziona quelli che vuoi comprare. Metrica di valore: €/Litro (più basso = meglio).",
        "metrica": "€/Litro",
        "selezione": "multipla",
        "gruppi": [{"nome": g, "prodotti": p} for g, p in gruppi.items()],
    }


def fetch_image(src: str, dest: str, client: httpx.Client) -> bool:
    try:
        data = open(src, "rb").read() if os.path.exists(src) else client.get(src).content
        im = Image.open(io.BytesIO(data)).convert("RGB")
        w, h = im.size
        scale = MAXPX / max(w, h)
        if scale < 1:
            im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        im.save(dest, format="JPEG", quality=85)
        return True
    except Exception as e:  # noqa: BLE001 — best effort, segnalo e continuo
        print("  img ERR", os.path.basename(dest), type(e).__name__, str(e)[:50])
        return False


def normalize(prod: dict, slug: str, client: httpx.Client) -> dict:
    src = prod.pop("_img", "")
    fname = f"{prod['id']}.jpg"
    dest = os.path.join(ROOT, "images", slug, fname)
    has_img = bool(src) and fetch_image(src, dest, client)
    valore = prod.get("valore")
    return {
        "id": prod["id"], "nome": prod["nome"], "negozio": prod["negozio"],
        "immagine": fname if has_img else None,
        "link": prod.get("link") or None,
        "prezzo": prod["prezzo"],
        "valore": valore,
        "valore_label": epl_label(valore),
        "nota": prod.get("nota") or "",
        "consigliato": bool(prod.get("consigliato")),
        "stato": None,
        "quantita": 1,
        "specs": [{"label": lbl, "value": val} for lbl, val in prod.get("specs", [])],
    }


def build(confronto: dict, client: httpx.Client) -> None:
    slug = confronto["slug"]
    os.makedirs(os.path.join(ROOT, "images", slug), exist_ok=True)
    print(f"\n=== {slug} ===")
    for gruppo in confronto["gruppi"]:
        gruppo["prodotti"] = [normalize(p, slug, client) for p in gruppo["prodotti"]]
    out = os.path.join(ROOT, f"{slug}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(confronto, f, ensure_ascii=False, indent=2)
    n = sum(len(g["prodotti"]) for g in confronto["gruppi"])
    print(f"  OK -> {out}  ({n} prodotti)")


def main() -> None:
    os.makedirs(ROOT, exist_ok=True)
    with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as client:
        build(SCATOLE, client)
        build(build_food(), client)


if __name__ == "__main__":
    main()
