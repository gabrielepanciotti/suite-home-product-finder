"""Estrae i box Action rilevanti per stoccaggio/vestiti con prezzo CORRETTO,
litri reali, dimensioni, foto, link. Prezzo = numero finale (centesimi)."""
import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / ".firecrawl"
data = json.loads((DATA_DIR / "action-products.json").read_text(encoding="utf-8"))


def parse(t):
    cap = re.search(r'(\d+(?:[.,]\d+)?)\s*litr', t)
    dims = re.search(r'(\d[\d,\.]*\s*[xX]\s*\d[\d,\.]*\s*[xX]\s*\d[\d,\.]*)\s*cm', t)
    # prezzo reale = ultimo gruppo di cifre prima del simbolo valuta finale
    pr = re.findall(r'(\d{2,5})\D*$', t.replace("�", "€"))
    price = None
    if pr:
        v = int(pr[-1])
        price = v / 100.0
    return (float(cap.group(1).replace(",", ".")) if cap else None,
            dims.group(1).replace(" ", "") if dims else None, price)


seen, rows = set(), []
for page, blob in data.items():
    for it in blob["items"]:
        href = it["href"]
        if href in seen:
            continue
        seen.add(href)
        cap, dims, price = parse(it["text"])
        nm = re.sub(r'\d+(?:[.,]\d+)?\s*litr.*$', '', it["text"])
        nm = re.sub(r'\d.*$', '', nm).strip() or it["text"][:30]
        rows.append({"nome": nm, "litri": cap, "dims": dims, "prezzo": price,
                     "img": it["img"], "href": href})

# box grandi rilevanti per stoccaggio/vestiti (cap >= 25 L, con coperchio)
big = [r for r in rows if r["litri"] and r["litri"] >= 25]
big.sort(key=lambda r: r["prezzo"] or 999)
print("=== BOX GRANDI (>=25 L) per stoccaggio/vestiti ===")
for r in big:
    epl = round(r["prezzo"] / r["litri"], 2) if r["prezzo"] and r["litri"] else None
    print(f"{r['nome'][:34]:34} {r['litri']:>5}L  {r['dims'] or '?':16} "
          f"{r['prezzo']!s:>6}EUR  {epl}EUR/L")
    print(f"    img: {r['img'][:90]}")
    print(f"    {r['href']}")

# salva il sottoinsieme per integrazione
out = [r for r in big]
((DATA_DIR / "action-big.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
))
print(f"\nsalvati {len(out)} box grandi -> .firecrawl/action-big.json")
