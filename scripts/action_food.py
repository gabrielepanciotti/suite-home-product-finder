"""Estrae i contenitori ALIMENTARI da Action (browser reale Playwright).
Cerca per query robuste (ermetico/conservazione/contenitore alimenti)."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

URLS = {
    "ermetico": "https://www.action.com/it-it/search/?q=contenitore%20ermetico",
    "conservazione": "https://www.action.com/it-it/search/?q=conservazione%20alimenti",
    "barattolo": "https://www.action.com/it-it/search/?q=barattolo",
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
    let card = a;
    for (let i = 0; i < 5 && card.parentElement; i++) {
      card = card.parentElement;
      if (card.querySelector('img') && /\d/.test(card.textContent)) break;
    }
    const img = card.querySelector('img');
    const og = card.querySelector('meta[property="og:image"]');
    const txt = (card.textContent || '').replace(/\s+/g, ' ').trim();
    const key = href + '|' + txt.slice(0, 40);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ href, img: img ? (img.getAttribute('src') || '') : '', text: txt.slice(0, 200) });
  }
  return out;
}
"""

results = {}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(user_agent=UA, locale="it-IT", viewport={"width": 1366, "height": 900})
    pg = ctx.new_page()
    for name, url in URLS.items():
        try:
            pg.goto(url, wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print(f"[{name}] goto ERR {type(e).__name__}", file=sys.stderr)
        for sel in ['button#onetrust-accept-btn-handler', 'button:has-text("Accetta")']:
            try:
                pg.click(sel, timeout=2000)
                break
            except Exception:
                pass
        try:
            pg.wait_for_selector('a[href*="/p/"]', timeout=20000)
        except Exception:
            pass
        pg.wait_for_timeout(2500)
        items = pg.evaluate(EXTRACT)
        results[name] = items
        print(f"[{name}] items={len(items)}", file=sys.stderr)
    b.close()
(Path(__file__).resolve().parents[1] / ".firecrawl" / "action-food.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("saved -> .firecrawl/action-food.json")
