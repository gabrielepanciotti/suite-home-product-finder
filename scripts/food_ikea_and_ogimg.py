"""IKEA food search (Playwright) + og:image canonico per i prodotti Action selezionati."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

IKEA_URLS = {
    "ikea-contenitori": "https://www.ikea.com/it/it/search/?q=contenitore%20alimenti",
    "ikea-barattoli": "https://www.ikea.com/it/it/search/?q=barattolo%20vetro%20coperchio",
}
# Action food selezionati -> prendo og:image canonico
ACTION = {
    "Action barattolo ermetico 1,4L": "https://www.action.com/it-it/p/3218514/barattolo-con-chiusura-ermetica/",
    "Action barattolo 0,8L": "https://www.action.com/it-it/p/3218513/barattolo/",
    "Action barattolo vetro conserve 1L": "https://www.action.com/it-it/p/2580021/barattolo-per-conserve/",
    "Action contenitore vetro 1L": "https://www.action.com/it-it/p/3220679/contenitore-in-vetro/",
    "Action contenitori impilabili 3pz": "https://www.action.com/it-it/p/3218110/contenitori-impilabili/",
    "Action Mepal 0,75L": "https://www.action.com/it-it/p/3208100/contenitore-per-alimenti-mepal/",
    "Action Mepal 1,5L": "https://www.action.com/it-it/p/3208098/contenitore-per-alimenti-mepal/",
    "Action Curver 1,4L": "https://www.action.com/it-it/p/3002389/contenitore-per-alimenti-curver/",
    "Action Tefal 1L x2": "https://www.action.com/it-it/p/3208738/contenitori-per-alimenti-tefal/",
    "Action Mepal 0,25L": "https://www.action.com/it-it/p/3208097/contenitore-per-alimenti-mepal/",
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
    for (let i = 0; i < 6 && card.parentElement; i++) {
      card = card.parentElement;
      if (card.querySelector('img') && /\d/.test(card.textContent)) break;
    }
    const img = card.querySelector('img');
    const txt = (card.textContent || '').replace(/\s+/g, ' ').trim();
    const key = href.split('?')[0];
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ href, img: img ? (img.getAttribute('src') || img.getAttribute('data-src') || '') : '', text: txt.slice(0, 160) });
  }
  return out;
}
"""

res = {"ikea": {}, "action_img": {}}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(user_agent=UA, locale="it-IT", viewport={"width": 1366, "height": 900})
    pg = ctx.new_page()
    for name, url in IKEA_URLS.items():
        try:
            pg.goto(url, wait_until="domcontentloaded", timeout=45000)
            for sel in ['button:has-text("Accetta")', 'button#onetrust-accept-btn-handler']:
                try:
                    pg.click(sel, timeout=2000); break
                except Exception:
                    pass
            try:
                pg.wait_for_selector('a[href*="/p/"]', timeout=15000)
            except Exception:
                pass
            pg.wait_for_timeout(2500)
            res["ikea"][name] = pg.evaluate(EXTRACT)
        except Exception as e:
            print(f"[{name}] ERR {type(e).__name__}", file=sys.stderr)
            res["ikea"][name] = []
        print(f"[{name}] {len(res['ikea'][name])} items", file=sys.stderr)
    for name, url in ACTION.items():
        try:
            pg.goto(url, wait_until="domcontentloaded", timeout=45000)
            pg.wait_for_timeout(1000)
            og = pg.evaluate("""() => {
                const m = document.querySelector('meta[property="og:image"]');
                return m ? m.content : null;
            }""")
        except Exception:
            og = None
        res["action_img"][name] = og
        print(f"[og] {name} -> {og}", file=sys.stderr)
    b.close()
(Path(__file__).resolve().parents[1] / ".firecrawl" / "food-extra.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("saved -> .firecrawl/food-extra.json")
