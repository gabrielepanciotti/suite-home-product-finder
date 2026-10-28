"""Tenta di leggere i prodotti Action: priming cookie homepage -> categoria/ricerca.
Cerca JSON embedded, endpoint Algolia/API, o blocchi prodotto."""
import re
import httpx

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
HEAD = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}
URLS = [
    "https://www.action.com/it-it/c/casalinghi/stoccaggio/",
    "https://www.action.com/it-it/search/?sortBy=PRICE_DESC&filter=categories%3ACasalinghi&q=scatola",
]
with httpx.Client(headers=HEAD, timeout=30, follow_redirects=True, http2=True) as c:
    # priming
    try:
        r0 = c.get("https://www.action.com/it-it/")
        print("home:", r0.status_code, "cookies:", len(c.cookies))
    except Exception as e:
        print("home ERR", type(e).__name__, str(e)[:60])
    for u in URLS:
        c.headers["Referer"] = "https://www.action.com/it-it/"
        try:
            r = c.get(u)
        except Exception as e:
            print(u, "ERR", type(e).__name__, str(e)[:60])
            continue
        h = r.text
        print("\n###", u[-40:], "->", r.status_code, "len", len(h))
        for key in ["algolia", "appId", "apiKey", "indexName", "__NEXT_DATA__",
                    "product", "price", "ld+json"]:
            if key.lower() in h.lower():
                print("  has", key)
        m = re.search(r'(appId|applicationId)["\']?\s*[:=]\s*["\']([A-Z0-9]{8,})', h)
        if m:
            print("  APP_ID:", m.group(2))
        m = re.search(r'(searchApiKey|apiKey|searchKey)["\']?\s*[:=]\s*["\']([a-f0-9]{20,})', h)
        if m:
            print("  API_KEY:", m.group(2)[:12], "...")
