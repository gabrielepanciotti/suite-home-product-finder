"""Pulisce i contenitori alimentari Action: nome, prezzo reale, capacita, dims, foto."""
import json
import re
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / ".firecrawl" / "action-food.json"
data = json.loads(DATA_FILE.read_text(encoding="utf-8"))


def parse(t):
    # capacita: litri o ml
    cap_l = re.search(r'(\d+(?:[.,]\d+)?)\s*litr', t)
    cap_ml = re.search(r'(\d+)\s*ml', t)
    if cap_l:
        cap = float(cap_l.group(1).replace(",", "."))
    elif cap_ml:
        cap = int(cap_ml.group(1)) / 1000.0
    else:
        cap = None
    dims = re.search(r'(\d[\d,\.]*\s*[xX]\s*\d[\d,\.]*(?:\s*[xX]\s*\d[\d,\.]*)?)\s*cm', t)
    pz = re.search(r'(\d+)\s*pezzi', t)
    pr = re.findall(r'(\d{2,5})\D*$', t.replace("�", "€").replace("�", "€"))
    price = int(pr[-1]) / 100.0 if pr else None
    return cap, dims.group(1).replace(" ", "") if dims else None, price, int(pz.group(1)) if pz else 1


seen, rows = set(), []
for q, items in data.items():
    for it in items:
        href = it["href"]
        if href in seen:
            continue
        seen.add(href)
        cap, dims, price, pz = parse(it["text"])
        nm = re.sub(r'(\d+(?:[.,]\d+)?\s*(?:litri|ml)).*$', '', it["text"])
        nm = re.sub(r'\d.*$', '', nm).strip() or it["text"][:30]
        rows.append({"nome": nm, "cap": cap, "pz": pz, "dims": dims, "prezzo": price,
                     "img": it["img"], "href": href, "raw": it["text"][:110]})

# food-relevant: ermetico/contenitore/barattolo/conserv + capacita piccola (<=3L)
KW = re.compile(r'ermetic|conservazion|contenitor|barattol|alim>|fresh|frigo|dispens', re.I)
food = [r for r in rows if KW.search(r["nome"] + " " + r["raw"]) and (r["cap"] is None or r["cap"] <= 5)]
food.sort(key=lambda r: r["prezzo"] or 999)
print(f"Totale unici: {len(rows)} | food-relevant: {len(food)}\n")
for r in food:
    cap = f"{r['cap']}L" if r['cap'] else "?"
    print(f"- {r['nome'][:40]:40} {cap:>7} x{r['pz']}  {r['dims'] or '?':14} {r['prezzo']!s:>6}EUR")
    print(f"    {r['href']}")
    print(f"    raw: {r['raw']}")
