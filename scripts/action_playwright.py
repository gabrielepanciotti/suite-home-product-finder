"""Estrae i prodotti 'scatole/stoccaggio' da Action con browser reale (Playwright).

Naviga le pagine, accetta i cookie, aspetta la griglia, estrae per ogni prodotto:
nome, prezzo, link, immagine. Salva JSON + screenshot per ispezione.
"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

URLS = {
    "stoccaggio": "https://www.action.com/it-it/c/casalinghi/stoccaggio/",
    "search-scatola": "https://www.action.com/it-it/search/?sortBy=PRICE_DESC&filter=categories%3ACasalinghi&q=scatola",
}
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

EXTRACT = r"""
() => {
  const out = [];
  const anchors = Array.from(document.querySelectorAll('a[href]'))
    .filter(a => /\/p\//.test(a.getAttribute('href') || ''));
  const seen = new Set();
  for (const a of anchors) {
    const href = a.href;
    // risali al 'card' contenitore
    let card = a;
    for (let i = 0; i < 5 && card.parentElement; i++) {
      card = card.parentElement;
      if (card.querySelector('img') && /\d/.test(card.textContent)) break;
    }
    const img = card.querySelector('img');
    const imgSrc = img ? (img.getAttribute('src') || img.getAttribute('data-src') || '') : '';
    const txt = (card.textContent || '').replace(/\s+/g, ' ').trim();
    const key = href + '|' + txt.slice(0, 40);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ href, img: imgSrc, text: txt.slice(0, 200) });
  }
  return out;
}
"""

results = {}
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent=UA, locale="it-IT",
                              viewport={"width": 1366, "height": 900})
    page = ctx.new_page()
    for name, url in URLS.items():
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print(f"[{name}] goto ERR {type(e).__name__}: {str(e)[:60]}", file=sys.stderr)
        # cookie banner
        for sel in ['button#onetrust-accept-btn-handler',
                    'button:has-text("Accetta")',
                    'button:has-text("Accept")']:
            try:
                page.click(sel, timeout=2500)
                break
            except Exception:
                pass
        try:
            page.wait_for_selector('a[href*="/p/"]', timeout=20000)
        except Exception:
            pass
        page.wait_for_timeout(2500)
        title = page.title()
        items = page.evaluate(EXTRACT)
        results[name] = {"title": title, "n": len(items), "items": items}
        page.screenshot(
            path=str(Path(__file__).resolve().parents[1] / ".firecrawl" / f"action-{name}.png"),
            full_page=False,
        )
        print(f"[{name}] title={title!r} items={len(items)}", file=sys.stderr)
    browser.close()

(Path(__file__).resolve().parents[1] / ".firecrawl" / "action-products.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("saved -> .firecrawl/action-products.json")
