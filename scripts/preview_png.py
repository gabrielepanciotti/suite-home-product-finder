"""Render PNG di anteprima della tabella confronto con foto inline (top picks, Action incluso)."""
import io
from pathlib import Path
import httpx
from PIL import Image, ImageDraw, ImageFont

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
     "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "it-IT,it;q=0.9"}
AC = "https://asset.action.com/image/upload/t_digital_square/w_512/"

ROWS = [
    ("Sotto il letto", "Action coperchio 29L", "59x39x18", "29", "5,95", "0,21", "No",
     AC + "13626189.jpg"),
    ("Sotto il letto", "IKEA SAMLA 55L", "78x56x18", "55", "13,00", "0,24", "No",
     "https://www.ikea.com/it/it/images/products/samla-contenitore-trasparente__0711155_pe728023_s5.jpg"),
    ("Armadio", "Action ruote 60L", "59x39x36", "60", "8,95", "0,15", "Ruote",
     AC + "2533870_5715079104003-111_01_q1fvo2.jpg"),
    ("Armadio", "Maury's porta indumenti", "60x41x40", "74", "9,90", "0,13", "Ruote",
     "https://cdn.maurysonline.it/immagini/6075081_0438026-box-porta-indumenti-con-ruote-dimensioni-60x41x40cm-e-coperchio-bianco-main_510.jpeg"),
    ("Cantina", "Action Heidrun 100L", "59x45x50", "100", "9,95", "0,10", "No",
     AC + "2535483_8010059016510-110_05_y50wtb.jpg"),
    ("Cantina", "IKEA SAMLA 130L", "79x57x43", "130", "20,00", "0,15", "No",
     "https://www.ikea.com/it/it/images/products/samla-contenitore-con-coperchio-trasparente__0711819_pe728498_s5.jpg"),
]
COLS = [("Foto", 95), ("Box", 200), ("Dim", 95), ("Cap L", 55),
        ("EUR", 60), ("EUR/L", 60), ("Ruote", 60), ("Collocaz.", 105)]
RH = 84
PAD = 8
W = sum(w for _, w in COLS) + PAD * 2
HEADER_H = 34
TITLE_H = 30
Htot = TITLE_H + HEADER_H + RH * len(ROWS) + PAD * 2


def font(sz, bold=False):
    names = (["arialbd.ttf", "seguisb.ttf"] if bold else ["arial.ttf", "segoeui.ttf"])
    for n in names:
        try:
            return ImageFont.truetype(n, sz)
        except Exception:
            pass
    return ImageFont.load_default()


img = Image.new("RGB", (W, Htot), "white")
d = ImageDraw.Draw(img)
d.text((PAD, 8), "Scatole stoccaggio - top picks con foto inline (Action LIVE incluso)  |  verde = miglior EUR/L",
       fill="#1a1a1a", font=font(14, True))
y0 = TITLE_H + PAD
x = PAD
d.rectangle([PAD, y0, W - PAD, y0 + HEADER_H], fill="#305496")
for name, w in COLS:
    d.text((x + 6, y0 + 9), name, fill="white", font=font(13, True))
    x += w
collfill = {"Sotto il letto": "#E8F0FE", "Armadio": "#E6F4EA", "Cantina": "#FEF7E0"}
best = {"Action ruote 60L", "Action Heidrun 100L", "Maury's porta indumenti"}
y = y0 + HEADER_H
for coll, box, dim, cap, eur, epl, ruote, url in ROWS:
    x = PAD
    vals = [None, box, dim, cap, eur, epl, ruote, coll]
    for i, (name, w) in enumerate(COLS):
        cell = [x, y, x + w, y + RH]
        bg = "white"
        if name == "Collocaz.":
            bg = collfill[coll]
        if name == "EUR/L" and box in best:
            bg = "#C6EFCE"
        d.rectangle(cell, fill=bg, outline="#D0D0D0")
        if i == 0:
            try:
                with httpx.Client(headers=H, timeout=30, follow_redirects=True) as c:
                    data = c.get(url).content
                im = Image.open(io.BytesIO(data)).convert("RGB")
                ww, hh = im.size
                th = RH - 8
                tw = int(ww * th / hh)
                if tw > w - 8:
                    tw = w - 8
                    th = int(hh * tw / ww)
                im = im.resize((tw, th), Image.LANCZOS)
                img.paste(im, (x + (w - tw) // 2, y + (RH - th) // 2))
            except Exception:
                d.text((x + 6, y + 30), "(no img)", fill="#999", font=font(11))
        else:
            v = vals[i]
            fb = (name == "Box") or (name == "EUR/L" and box in best)
            d.text((x + 6, y + RH // 2 - 8), str(v), fill="#1a1a1a", font=font(13, fb))
        x += w
    y += RH
out = Path(__file__).resolve().parents[1] / "vault" / "raw" / "anteprima-confronto-foto.png"
img.save(out)
print("OK ->", out)
