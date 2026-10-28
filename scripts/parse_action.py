"""Pulisce i prodotti Action estratti: nome, prezzo, litri, foto, link."""
import json
import re
from pathlib import Path

data_file = Path(__file__).resolve().parents[1] / ".firecrawl" / "action-products.json"
data = json.loads(data_file.read_text(encoding="utf-8"))


def price(t):
    m = re.search(r'(\d+[.,]\d{2})\s*(?:€|EUR)', t) or re.search(r'€\s*(\d+[.,]\d{2})', t)
    return m.group(1).replace(".", ",") if m else None


def litri(t):
    m = re.findall(r'(\d+(?:[.,]\d+)?)\s*[lL](?![a-z])', t)
    return m[0].replace(",", ".") if m else None


def name(t):
    # togli prezzo e rumore finale, prendi la parte iniziale significativa
    t = re.sub(r'\s*\d+[.,]\d{2}\s*€.*$', '', t)
    t = re.sub(r'(Aggiungi|Confronta|Online|In negozio|Nuovo).*$', '', t, flags=re.I)
    return t.strip()[:80]


seen = set()
rows = []
for page, blob in data.items():
    for it in blob["items"]:
        t = it["text"]
        href = it["href"]
        if href in seen:
            continue
        seen.add(href)
        nm = name(t)
        if not nm or len(nm) < 4:
            continue
        rows.append({
            "nome": nm, "prezzo": price(t), "litri": litri(t),
            "img": it["img"], "href": href, "raw": t[:120],
        })

# filtra a contenitori/scatole/box plausibili
KW = re.compile(r'scatola|contenitor|box|cassa|baule|organizer|stoccagg|coperchio', re.I)
boxes = [r for r in rows if KW.search(r["nome"] + " " + r["raw"])]
print(f"Totale prodotti unici: {len(rows)} | filtrati box: {len(boxes)}\n")
for r in sorted(boxes, key=lambda x: float(x["prezzo"].replace(",", ".")) if x["prezzo"] else 999):
    print(f"- {r['nome']!r}")
    print(f"    prezzo={r['prezzo']}  litri={r['litri']}  img={'Y' if r['img'] else 'N'}")
    print(f"    {r['href']}")
    print(f"    raw: {r['raw']}")
print("\n--- TUTTI (anche non-box) per controllo ---")
for r in rows:
    print(f"  {r['prezzo']!s:>8}  {r['litri']!s:>5}L  {r['nome'][:55]}")
