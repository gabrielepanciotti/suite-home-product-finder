"""Genera l'Excel riepilogativo del confronto scatole stoccaggio/vestiti, CON foto inline.

RICERCA B (scatole stoccaggio grandi: vestiti + ingombranti). Distinta dalla
RICERCA A (contenitori alimentari Ma Maison per armadio/frigo -> schede ma-maison-*).
Fonti: Mycorise (09/06) rielaborato + Action LIVE (browser reale, 14/06, litri e
prezzi REALI dal catalogo) + verifica live IKEA/Maury's/JYSK. Metrica = EUR/Litro.
"""
import io
import re
from pathlib import Path
import httpx
from PIL import Image as PILImage
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      "Accept-Language": "it-IT,it;q=0.9"}

L = {
    "IKEA SAMLA 55L": "https://www.ikea.com/it/it/p/samla-contenitore-trasparente-90102971/",
    "Sottoletto 80x40x18 (vari)": "https://www.amazon.it/s?k=scatola+sottoletto+80x40+coperchio",
    "Bama Stagione 80x60x18": "https://www.eurobrico.com/it/cont-mult-60lt-80x60x18h-C000217933",
    "Maury's sottoletto 80x60x17": "https://maurysonline.it/box-sottoletto-con-ruote-80x60x17cm-in-plastica-trasparente-da--564-lt",
    "Box avio 60x41x14": "https://maurysonline.it/box-contenitore-dimensioni-60x41x14cm-e-coperchio-avio",
    "Maury's porta indumenti 60x41x40": "https://maurysonline.it/box-contenitore-con-ruote-dimensioni-60x41x40cm-e-coperchio-bianco",
    "JYSK Basic Box 80L": "https://jysk.it/organizzazione/contenitori-e-cesti/contenitori-plastica/contenitore-basic-box-80-l-con-coperchio-trasparente",
    "Cetomo 80L (set 6)": "https://www.amazon.it/dp/B0BN1DL6SB",
    "Maury's garage 60x40x36": "https://maurysonline.it/box-contenitore-con-coperchio-e-ruote-garage-60x40x36-cm-grigio",
    "Tontarelli Puzzle Box 60L": "https://www.amazon.it/dp/B06XWDN5QK",
    "PackServices 60x40x36": "https://www.packservices.it/prodotto/cassa-inseribile-e-sovrapponibile-con-coperchio-68-lt-pskm4636/",
    "Stefanplast Vasco 60x40x36": "https://www.amazon.it/dp/B00FF8N7HU",
    "KONZEPT 80L": "https://www.amazon.it/dp/B0FG34FDZ2",
    "IKEA SAMLA 130L": "https://www.ikea.com/it/it/p/samla-contenitore-con-coperchio-trasparente-s29440819/",
    "Tontarelli Box One 140L": "https://www.orizzonteshop.it/products/tontarelli-boxone-storage-ccoperchio-8035940999-tontarelli-ean-8009404212080",
    "Iris Ohyama 80L (set 4)": "https://www.amazon.it/dp/B0CDCP8FB7",
    "Tontarelli Box One 110L": "https://www.livegarden.it/baule-box-one-79x52-h-42-l-110-tontarelli-cod-18071/",
    "Ricomi Athena 80x60x43": "https://www.ricomi.it/cassette-plastica/athena/cassetta-in-plastica-athena-800x600x430h/",
    "Deuba Multibox 100L": "https://www.amazon.it/Deuba-Contenitore-Portaoggetti-80x52x41-Coperchio/dp/B002X7EEY6",
    "Tontarelli Box One 70L": "https://ferramentamassolino.it/product/baule-box-one-79x39-h-35-l-70-tontarelli/",
    # --- Action (catalogo LIVE 14/06, prezzi e litri reali) ---
    "Action coperchio 29L (59x39x18)": "https://www.action.com/it-it/p/2568528/contenitore-con-coperchio/",
    "Action Plast1 60L (75x59x19)": "https://www.action.com/it-it/p/3216516/contenitore-plast1/",
    "Action ruote 60L (59x39x36)": "https://www.action.com/it-it/p/2533870/contenitore-con-ruote/",
    "Action clip 80L (58x39x43)": "https://www.action.com/it-it/p/3000808/contenitore-con-coperchio-a-clip/",
    "Action Plast1 40L (59x39x26)": "https://www.action.com/it-it/p/3205800/scatola-portaoggetti-con-coperchio-plast1/",
    "Action coperchio 32L (39x39x26)": "https://www.action.com/it-it/p/2533849/contenitore-con-coperchio/",
    "Action Iris 40L (55x40x25)": "https://www.action.com/it-it/p/2566818/contenitore-iris/",
    "Action Heidrun 100L (59x45x50)": "https://www.action.com/it-it/p/2535483/contenitore-heidrun/",
    "Action Heidrun 60L (58x36x40)": "https://www.action.com/it-it/p/2535480/contenitore-heidrun/",
    "Action Heidrun 42L (49x36x35)": "https://www.action.com/it-it/p/2535481/contenitore-heidrun/",
    "Temu box plastica": "https://www.temu.com/it/",
    "AliExpress box PP 120L": "https://www.aliexpress.com/w/wholesale-extra-large-plastic-storage-boxes.html",
}
# immagini gia note (evita un fetch)
A = "https://asset.action.com/image/upload/t_digital_square/w_512/"
IMG_DIRECT = {
    "IKEA SAMLA 55L": "https://www.ikea.com/it/it/images/products/samla-contenitore-trasparente__0711155_pe728023_s5.jpg",
    "IKEA SAMLA 130L": "https://www.ikea.com/it/it/images/products/samla-contenitore-con-coperchio-trasparente__0711819_pe728498_s5.jpg",
    "JYSK Basic Box 80L": "https://cdn1.jysk.com/getimage/wd3.large/238798",
    "Iris Ohyama 80L (set 4)": "https://m.media-amazon.com/images/I/71ggSp38aTL._AC_SL1500_.jpg",
    "Tontarelli Box One 140L": "http://www.orizzonteshop.it/cdn/shop/products/immagine-1-tontarelli-boxone-storage-ccoperchio-8035940999-tontarelli-ean-8009404212080.jpg?height=900&width=900",
    "Action coperchio 29L (59x39x18)": A + "13626189.jpg",
    "Action Plast1 60L (75x59x19)": A + "3216516_5715079164151-110_01_guob2h.jpg",
    "Action ruote 60L (59x39x36)": A + "2533870_5715079104003-111_01_q1fvo2.jpg",
    "Action clip 80L (58x39x43)": A + "17019061.jpg",
    "Action Plast1 40L (59x39x26)": A + "27368489.jpg",
    "Action coperchio 32L (39x39x26)": A + "2533849_5715079103006-111_01_xpimq7.jpg",
    "Action Iris 40L (55x40x25)": A + "2566818_8716382216770-110_01_cphwc6.jpg",
    "Action Heidrun 100L (59x45x50)": A + "2535483_8010059016510-110_05_y50wtb.jpg",
    "Action Heidrun 60L (58x36x40)": A + "2535480_8010059016503-110_08_nndk8i.jpg",
    "Action Heidrun 42L (49x36x35)": A + "2535481_8010059016527-110_05_lj4ko1.jpg",
}
# negozi senza catalogo online con foto -> placeholder
NO_IMG = {"Sottoletto 80x40x18 (vari)", "Temu box plastica", "AliExpress box PP 120L"}

# coll, box, fonte, dim, cap, coperchio, mat, ruote, eur, disp
R = [
    ("Sotto il letto", "IKEA SAMLA 55L", "IKEA", "78x56x18", 55, "Si (set)", "Trasparente", "No", 13.00, "Disponibile (verif. 14/06)"),
    ("Sotto il letto", "Action coperchio 29L (59x39x18)", "Action", "59x39x18", 29, "Si", "Plastica", "No", 5.95, "Negozio + online (14/06)"),
    ("Sotto il letto", "Action Plast1 60L (75x59x19)", "Action", "75x59x19", 60, "Si", "Plastica", "No", 16.95, "Negozio + online (14/06)"),
    ("Sotto il letto", "Sottoletto 80x40x18 (vari)", "Amazon", "80x40x18", 55, "Si", "Trasparente", "No", 12.00, "Da verificare"),
    ("Sotto il letto", "Bama Stagione 80x60x18", "Eurobrico", "80x60x18", 60, "Si", "Opaco", "No", 20.90, "Disponibile"),
    ("Sotto il letto", "Maury's sottoletto 80x60x17", "Maury's", "80x60x17", 56.4, "Si", "Trasparente", "Ruote", 16.99, "Esaurito online / in negozio si"),
    ("Sotto il letto", "Box avio 60x41x14", "Maury's", "60x41x14", 25, "Si", "Opaco", "No", 5.00, "Disponibile (H14 basso)"),
    ("Armadio/mensola", "Maury's porta indumenti 60x41x40", "Maury's", "60x41x40", 74, "Si", "Opaco bianco", "Ruote", 9.90, "Disponibile (verif. 14/06)"),
    ("Armadio/mensola", "Action ruote 60L (59x39x36)", "Action", "59x39x36", 60, "Si", "Plastica", "Ruote", 8.95, "Negozio + online (14/06)"),
    ("Armadio/mensola", "Action clip 80L (58x39x43)", "Action", "58x39x43", 80, "Si clip", "Plastica", "No", 10.95, "Negozio + online (14/06)"),
    ("Armadio/mensola", "Action Plast1 40L (59x39x26)", "Action", "59x39x26", 40, "Si", "Plastica", "No", 7.95, "Negozio + online (14/06)"),
    ("Armadio/mensola", "Action coperchio 32L (39x39x26)", "Action", "39x39x26", 32, "Si", "Plastica", "No", 5.95, "Negozio + online (14/06)"),
    ("Armadio/mensola", "Action Iris 40L (55x40x25)", "Action", "55x40x25", 40, "Si", "Plastica vari colori", "No", 6.49, "Negozio + online (14/06)"),
    ("Armadio/mensola", "JYSK Basic Box 80L", "JYSK", "60x40x43", 80, "Si", "Trasparente", "No", 12.50, "Disponibile (verif. 14/06)"),
    ("Armadio/mensola", "Cetomo 80L (set 6)", "Amazon", "62x45.5x39.5", 80, "Si", "Opaco", "No", 13.99, "Disponibile (set 6 = 83,96)"),
    ("Armadio/mensola", "Maury's garage 60x40x36", "Maury's", "60x40x36", 55, "Si", "Opaco grigio", "Ruote", 12.99, "Disponibile (verif. 14/06)"),
    ("Armadio/mensola", "Tontarelli Puzzle Box 60L", "Amazon", "60.5x40x38.5", 60, "Si clip", "Trasp.+colore", "Ruote", 14.50, "Disponibile"),
    ("Armadio/mensola", "PackServices 60x40x36", "PackServices", "60x40x36", 68, "Si integrato", "Opaco blu", "No", 19.13, "Disponibile"),
    ("Armadio/mensola", "Stefanplast Vasco 60x40x36", "Amazon", "60x40x36", 55, "Si", "Opaco", "Ruote", 18.67, "Disponibile"),
    ("Armadio/mensola", "KONZEPT 80L", "Amazon", "71.9x38.5x37.2", 80, "Si", "Trasparente", "No", 30.10, "Disponibile (caro)"),
    ("Cantina/garage", "Action Heidrun 100L (59x45x50)", "Action", "59x45x50.5", 100, "Si", "Plastica vari colori", "No", 9.95, "Negozio + online (14/06)"),
    ("Cantina/garage", "Action Heidrun 60L (58x36x40)", "Action", "58.5x36x40", 60, "Si", "Plastica vari colori", "No", 7.98, "Negozio + online (14/06)"),
    ("Cantina/garage", "Action Heidrun 42L (49x36x35)", "Action", "49x36x35", 42, "Si", "Plastica vari colori", "No", 5.95, "Negozio + online (14/06)"),
    ("Cantina/garage", "IKEA SAMLA 130L", "IKEA", "79x57x43", 130, "Si (set)", "Trasparente", "No", 20.00, "Disponibile (verif. 14/06)"),
    ("Cantina/garage", "Tontarelli Box One 140L", "OrizzonteShop", "79x52x52", 140, "Si clip", "Opaco nero", "No", 29.00, "Disponibile"),
    ("Cantina/garage", "Iris Ohyama 80L (set 4)", "Amazon", "84x42.5x33", 80, "Si clip", "Trasparente", "No", 23.51, "Disponibile (set 4 = 94,04)"),
    ("Cantina/garage", "Tontarelli Box One 110L", "LiveGarden", "79x52x42", 110, "Si clip", "Opaco nero", "No", 38.80, "Su ordine"),
    ("Cantina/garage", "Ricomi Athena 80x60x43", "Ricomi", "80x60x43", 150, "Cop. separato", "Opaco", "No", 60.00, "Disponibile (industriale)"),
    ("Cantina/garage", "Deuba Multibox 100L", "Amazon", "80x52x41", 100, "Si clip", "Opaco", "Ruote", 47.95, "Disponibile (caro)"),
    ("Cantina/garage", "Tontarelli Box One 70L", "Ferr. Massolino", "79x39x35", 70, "Si clip", "Opaco nero", "No", 37.00, "Disponibile (caro)"),
    ("Extra-UE (dogana)", "Temu box plastica", "Temu (CN)", "60x40x35", 60, "Si", "Varie", "No", 18.00, "5-14 gg, IVA IOSS incl."),
    ("Extra-UE (dogana)", "AliExpress box PP 120L", "AliExpress (CN)", "80x50x37", 120, "Si snap", "Opaco", "No", 35.00, "20-40 gg + sped/dogana"),
]

# top per collocazione (verde su EUR/Litro)
best = {"IKEA SAMLA 55L", "Maury's porta indumenti 60x41x40",
        "Action Heidrun 100L (59x45x50)", "Action ruote 60L (59x39x36)"}

THUMB_H = 72  # px


def resolve_img_url(box, client):
    """Risolve l'URL immagine del prodotto con strategie multiple."""
    if box in IMG_DIRECT:
        return IMG_DIRECT[box]
    if box in NO_IMG:
        return None
    url = L.get(box)
    if not url:
        return None
    try:
        h = client.get(url).text
    except Exception:
        return None
    if "amazon.it" in url:
        m = (re.search(r'"hiRes":"(https://[^"]+)"', h)
             or re.search(r'data-old-hires="(https://[^"]+)"', h)
             or re.search(r'"large":"(https://m\.media-amazon[^"]+)"', h))
        return m.group(1) if m else None
    if "maurysonline.it" in url:
        m = re.search(r'(https://cdn\.maurysonline\.it/immagini/[^"\'\s]+?_510\.jpe?g)', h)
        if m:
            return m.group(1)
        m = re.search(r'(https://cdn\.maurysonline\.it/immagini/[^"\'\s]+?\.jpe?g)', h)
        return m.group(1) if m else None
    m = (re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', h)
         or re.search(r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"', h)
         or re.search(r'<meta[^>]+name="twitter:image"[^>]+content="([^"]+)"', h))
    return m.group(1) if m else None


def fetch_thumb(img_url, client):
    data = client.get(img_url).content
    im = PILImage.open(io.BytesIO(data)).convert("RGB")
    w, h = im.size
    nw = max(1, int(w * THUMB_H / h))
    im = im.resize((nw, THUMB_H), PILImage.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    buf.seek(0)
    return buf, nw


wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Confronto"
HDR = ["Collocazione", "Foto", "Box", "Fonte", "Dim LxPxH (cm)", "Cap (L)", "Coperchio",
       "Materiale", "Ruote", "Prezzo (EUR)", "EUR/Litro", "Disponibilita", "Link"]
thin = Side(style="thin", color="D0D0D0")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
title = ws.cell(1, 1, "RICERCA B - scatole stoccaggio (vestiti + ingombranti). Action = "
                      "catalogo LIVE 14/06 (litri/prezzi reali). EUR/Litro = valore "
                      "(verde = top per collocazione). NB: contenitori ALIMENTARI Ma Maison "
                      "= ricerca separata (schede ma-maison-*).")
title.font = Font(bold=True, size=11)
ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=13)
title.alignment = Alignment(wrap_text=True, vertical="center")
ws.row_dimensions[1].height = 44
for j, h in enumerate(HDR, 1):
    c = ws.cell(3, j, h)
    c.font = Font(bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="305496")
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = border
collfill = {"Sotto il letto": "E8F0FE", "Armadio/mensola": "E6F4EA",
            "Cantina/garage": "FEF7E0", "Extra-UE (dogana)": "FCE8E6"}
imgcol_w = 12.0
r = 4
with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as client:
    for coll, box, fonte, dim, cap, cop, mat, ruote, eur, disp in R:
        epl = round(eur / cap, 2)
        ws.cell(r, 1, coll).fill = PatternFill("solid", fgColor=collfill[coll])
        ws.cell(r, 3, box).font = Font(bold=(box in best))
        ws.cell(r, 4, fonte)
        ws.cell(r, 5, dim)
        ws.cell(r, 6, cap)
        ws.cell(r, 7, cop)
        ws.cell(r, 8, mat)
        ws.cell(r, 9, ruote)
        ws.cell(r, 10, eur).number_format = "0.00"
        epl_c = ws.cell(r, 11, epl)
        epl_c.number_format = "0.00"
        ws.cell(r, 12, disp)
        lk = ws.cell(r, 13, "apri")
        if box in L:
            lk.hyperlink = L[box]
            lk.font = Font(color="0563C1", underline="single")
        if box in best:
            epl_c.fill = PatternFill("solid", fgColor="C6EFCE")
        for j in range(1, 14):
            ws.cell(r, j).border = border
            ws.cell(r, j).alignment = Alignment(vertical="center", wrap_text=(j in (1, 12)))
        placed = False
        try:
            iu = resolve_img_url(box, client)
            if iu:
                buf, nw = fetch_thumb(iu, client)
                xi = XLImage(buf)
                xi.height = THUMB_H
                xi.width = nw
                ws.add_image(xi, f"B{r}")
                imgcol_w = max(imgcol_w, nw / 7 + 2)
                placed = True
                print("img OK ", box)
        except Exception as e:
            print("img ERR", box, type(e).__name__, str(e)[:40])
        if not placed:
            ws.cell(r, 2, "(no img)").alignment = Alignment(horizontal="center", vertical="center")
            print("no img ", box)
        ws.row_dimensions[r].height = THUMB_H * 0.78
        r += 1
ws.freeze_panes = "A4"
ws.auto_filter.ref = f"A3:M{r - 1}"
W = [16, None, 30, 14, 16, 7, 13, 15, 8, 11, 9, 26, 7]
for j, w in enumerate(W, 1):
    col = get_column_letter(j)
    ws.column_dimensions[col].width = imgcol_w if col == "B" else w

ws2 = wb.create_sheet("Sintesi")
rows = [
    ("RACCOMANDAZIONE - scatole stoccaggio (vestiti + ingombranti)", ""),
    ("", ""),
    ("Sotto il letto", "Action contenitore con coperchio 29L 59x39x18 - 5,95 EUR (0,21 EUR/L) "
     "o IKEA SAMLA 55L 13 EUR (trasparente). Action Plast1 60L 75x59x19 (16,95) se vuoi footprint max."),
    ("Armadio / mensola", "Action contenitore con RUOTE 60L 59x39x36 - 8,95 EUR (0,15 EUR/L) o "
     "Action clip 80L 58x39x43 - 10,95 EUR (0,14 EUR/L). Maury's porta indumenti 74L ruote 9,90 EUR (0,13)."),
    ("Cantina / garage", "Action Heidrun 100L 59x45x50 - 9,95 EUR (0,10 EUR/L) = miglior valore in assoluto. "
     "IKEA SAMLA 130L 20 EUR (0,15); Tontarelli 140L 29 EUR se vuoi clip robusto."),
    ("Extra-UE", "Temu/AliExpress sconsigliati: spedizione volumetrica CN + dogana azzerano il risparmio."),
    ("", ""),
    ("Action (novita)", "Catalogo Action LIVE verificato 14/06: litri e prezzi REALI (prima erano stime "
     "Mycorise sbagliate, es. 75x59x19 e 60L non 75). Action e' il miglior EUR/L su quasi ogni taglia."),
    ("Nota 2 ricerche", "Questa = scatole stoccaggio grandi (vestiti, alcune utili anche per cibo ingombrante). "
     "I contenitori ALIMENTARI piccoli (Ma Maison, armadio/frigo) sono una ricerca separata: schede ma-maison-*."),
]
ws2.cell(1, 1).font = Font(bold=True, size=12)
for i, (a, b) in enumerate(rows, 1):
    ws2.cell(i, 1, a).font = Font(bold=True)
    ws2.cell(i, 2, b).alignment = Alignment(wrap_text=True, vertical="top")
ws2.column_dimensions["A"].width = 22
ws2.column_dimensions["B"].width = 100

out = Path(__file__).resolve().parents[1] / "vault" / "prodotti" / "contenitori" / "scatole-vestiti-confronto.xlsx"
wb.save(out)
print("OK ->", out, "|", len(R), "box")
