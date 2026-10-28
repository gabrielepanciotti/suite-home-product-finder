"""Sonda le pagine Action per capire come estrarre i prodotti (JSON embedded / API)."""
import re
import httpx

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      "Accept-Language": "it-IT,it;q=0.9"}
URLS = [
    "https://www.action.com/it-it/search/?sortBy=PRICE_DESC&filter=categories%3ACasalinghi&q=scatola",
    "https://www.action.com/it-it/c/casalinghi/stoccaggio/",
]
with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as c:
    for u in URLS:
        try:
            r = c.get(u)
            h = r.text
        except Exception as e:
            print(u, "ERR", type(e).__name__, str(e)[:60])
            continue
        print("\n###", u, "->", r.status_code, "len", len(h))
        for key in ["__NEXT_DATA__", "algolia", "apiKey", "x-algolia", "application/ld+json",
                    "productData", "window.__", "/api/", "data-product", "price",
                    "ProductCard", "indexName", "appId"]:
            print(f"  {key:24} {'YES' if key.lower() in h.lower() else '-'}")
        # snippet di eventuale ld+json
        m = re.search(r'application/ld\+json[^>]*>(.{0,300})', h, re.S)
        if m:
            print("  ld+json snippet:", m.group(1).replace("\n", " ")[:200])
