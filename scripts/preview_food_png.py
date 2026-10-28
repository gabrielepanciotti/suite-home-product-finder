"""Anteprima PNG del confronto contenitori alimentari (Maxi vs Action/IKEA)."""
import io
import os
from pathlib import Path
import httpx
from PIL import Image, ImageDraw, ImageFont

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
     "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "it-IT,it;q=0.9"}
AC = "https://asset.action.com/image/upload/t_digital_square/w_512/"
IK = "https://www.ikea.com/it/it/images/products/"
RAW = str(Path(__file__).resolve().parents[1] / "vault" / "raw") + os.sep

ROWS = [
    ("Dispensa", "Action barattolo ermetico 1,4L", "Action", "1,4", "2,72", "1,94",
     AC + "3218514_8712442227854-110_01_goq5xz.jpg"),
    ("Dispensa", "Ma Maison Airtight 1L", "Maxi", "1,0", "4,99", "4,99",
     RAW + "2026-06-14_158_foto.jpg"),
    ("Dispensa", "IKEA KORKEN vetro 1L", "IKEA", "1,0", "2,95", "2,95",
     IK + "korken-barattolo-con-coperchio-vetro-trasparente__1152252_pe885219_s5.jpg"),
    ("Frigo", "IKEA 365+ 2,0L", "IKEA", "2,0", "2,50", "1,25",
     IK + "ikea-365-contenitore-rettangolare-plastica__0711428_pe728244_s5.jpg"),
    ("Frigo", "Action Mepal 1,5L", "Action", "1,5", "3,99", "2,66",
     AC + "25077426.jpg"),
    ("Frigo", "Maison du Monde 1,2L", "Maxi", "1,2", "5,90", "4,92",
     RAW + "2026-06-14-scaffale-contenitori-maxi.jpg"),
    ("Set", "Maison du Monde 4x0,5L", "Maxi", "2,0", "2,99", "1,50",
     RAW + "2026-06-14-scaffale-contenitori-maxi.jpg"),
    ("Set", "IKEA PRUTA 17pz", "IKEA", "set", "4,95", "-",
     IK + "pruta-set-17-contenitori-alim-con-coperch-verde__1383829_pe962689_s5.jpg"),
]
COLS = [("Foto", 95), ("Prodotto", 215), ("Negozio", 75), ("Cap L", 55),
        ("EUR", 60), ("EUR/L", 60), ("Gruppo", 90)]
RH, PAD = 84, 8
W = sum(w for _, w in COLS) + PAD * 2
TITLE_H, HEADER_H = 30, 34
Htot = TITLE_H + HEADER_H + RH * len(ROWS) + PAD * 2


def font(sz, bold=False):
    for n in (["arialbd.ttf", "seguisb.ttf"] if bold else ["arial.ttf", "segoeui.ttf"]):
        try:
            return ImageFont.truetype(n, sz)
        except Exception:
            pass
    return ImageFont.load_default()


img = Image.new("RGB", (W, Htot), "white")
d = ImageDraw.Draw(img)
d.text((PAD, 8), "Contenitori alimentari - Maxi vs Action/IKEA (con foto)  |  verde = miglior EUR/L",
       fill="#1a1a1a", font=font(14, True))
y0 = TITLE_H + PAD
x = PAD
d.rectangle([PAD, y0, W - PAD, y0 + HEADER_H], fill="#305496")
for name, w in COLS:
    d.text((x + 6, y0 + 9), name, fill="white", font=font(13, True))
    x += w
gf = {"Dispensa": "#E8F0FE", "Frigo": "#E6F4EA", "Set": "#FEF7E0"}
best = {"Action barattolo ermetico 1,4L", "IKEA 365+ 2,0L", "Maison du Monde 4x0,5L"}
y = y0 + HEADER_H
for grp, nome, neg, cap, eur, epl, src in ROWS:
    x = PAD
    vals = [None, nome, neg, cap, eur, epl, grp]
    for i, (name, w) in enumerate(COLS):
        cell = [x, y, x + w, y + RH]
        bg = "white"
        if name == "Gruppo":
            bg = gf[grp]
        if name == "EUR/L" and nome in best:
            bg = "#C6EFCE"
        d.rectangle(cell, fill=bg, outline="#D0D0D0")
        if i == 0:
            try:
                if os.path.exists(src):
                    data = open(src, "rb").read()
                else:
                    with httpx.Client(headers=H, timeout=30, follow_redirects=True) as c:
                        data = c.get(src).content
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
            fb = (name == "Prodotto") or (name == "EUR/L" and nome in best)
            d.text((x + 6, y + RH // 2 - 8), str(vals[i]), fill="#1a1a1a", font=font(12, fb))
        x += w
    y += RH
out = Path(__file__).resolve().parents[1] / "vault" / "raw" / "anteprima-alimentari-foto.png"
img.save(out)
print("OK ->", out)
