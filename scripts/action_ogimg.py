"""Raccoglie l'og:image canonico di ogni prodotto Action (browser reale)."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

PROD = {
    "Action coperchio 29L (59x39x18)": "https://www.action.com/it-it/p/2568528/contenitore-con-coperchio/",
    "Action Plast1 60L (75x59x19)": "https://www.action.com/it-it/p/3216516/contenitore-plast1/",
    "Action ruote 60L (59x39x36)": "https://www.action.com/it-it/p/2533870/contenitore-con-ruote/",
    "Action clip 80L (58x39x43)": "https://www.action.com/it-it/p/3000808/contenitore-con-coperchio-a-clip/",
    "Action Plast1 40L (59x39x26)": "https://www.action.com/it-it/p/3205800/scatola-portaoggetti-con-coperchio-plast1/",
    "Action coperchio 32L (39x39x26)": "https://www.action.com/it-it/p/2533849/contenitore-con-coperchio/",
    "Action Iris 40L (55x40x25)": "https://www.action.com/it-it/p/2566818/contenitore-iris/",
    "Action Heidrun 100L (59x45x50)": "https://www.action.com/it-it/p/2535483/contenitore-heidrun/",
    "Action Heidrun 60L (58x36x40)": "https://www.action.com/it-it/p/2535480/contenitore-heidrun/",
    "Action Heidrun 42L (49x36x35)": "https://www.action.com/it-it/p/2535481/contenitore-heidrun/",
}
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
out = {}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(user_agent=UA, locale="it-IT")
    pg = ctx.new_page()
    for name, url in PROD.items():
        try:
            pg.goto(url, wait_until="domcontentloaded", timeout=45000)
            pg.wait_for_timeout(1200)
            og = pg.evaluate("""() => {
                const m = document.querySelector('meta[property="og:image"]');
                if (m) return m.content;
                const im = document.querySelector('img[src*="asset.action.com"]');
                return im ? im.src : null;
            }""")
        except Exception as e:
            og = None
            print("ERR", name, type(e).__name__)
        out[name] = og
        print(name, "->", og)
    b.close()
(Path(__file__).resolve().parents[1] / ".firecrawl" / "action-ogimg.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
