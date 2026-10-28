"""shopcli — ricerca prodotti multi-negozio con calcolo di tassellazione.

CLI riusabile per le ricerche prezzi del vault. Unifica quattro fonti dietro
un'unica interfaccia e sa dire, dato un vano, quali prodotti lo riempiono meglio.

    # cerca su un negozio (o su tutti)
    python scripts/shopcli.py search action "contenitore" --limit 30
    python scripts/shopcli.py search action "cat:casalinghi" --limit 200
    python scripts/shopcli.py search all "scatola" --json out.json

    # quali prodotti riempiono i vani dati (LxPxH in cm, gioco gia' sottratto)
    python scripts/shopcli.py fit --from out.json --vano C1=32x83x18 --vano V3=37x29x43

    # fonti disponibili / categorie Action
    python scripts/shopcli.py shops
    python scripts/shopcli.py categorie

Fonti: ikea (API JSON), amazon (HTTP + UA Chrome), action (flight stream RSC),
maurys (Playwright).

La TASSELLAZIONE (Prodotto, Vano, Fit, classifica) non vive piu' qui: sta in
`backend/home_product_finder_backend/tassellazione.py`, perche' anche l'API la
usa e l'immagine Docker copia solo `backend/`. Questa CLI la importa; il comando
`fit` resta l'interfaccia da riga di comando dello stesso algoritmo.

NB su maurys: il percorso Playwright qui sotto NON e' piu' necessario. Il sito
non e' una SPA: e' nopCommerce renderizzato lato server, e l'HTML sembrava vuoto
solo perche' gli attributi non sono quotati (`data-productid=81378`), quindi un
parser che cerca `data-productid="..."` non trova nulla. Per il catalogo usare
`maurys-pp-cli` (vedi brain/conoscenza/maurys-cli.md); questo resta finche' il
comando `fit` non e' agganciato alla CLI.
Generalizza scripts/action_playwright.py.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from urllib.parse import quote_plus

try:
    import httpx
except ImportError:  # fallback: nessuna dipendenza esterna richiesta
    httpx = None
    import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "vault" / "confronti" / "_scrape"

# Il package backend non e' installato nel venv: e' la sorgente dell'app, e
# questa CLI ne importa la tassellazione. La direzione della dipendenza segue
# quella del packaging (vedi il docstring di tassellazione.py).
_BACKEND = REPO_ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from home_product_finder_backend.tassellazione import (  # noqa: E402
    ORDINAMENTI,
    Prodotto,
    Vano,
    classifica,
    misura,
)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": UA, "Accept-Language": "it-IT,it;q=0.9"}

# 12x8x5 / 12,5 x 8 x 5 cm / 12 X 8 X H5 CM
DIM_RE = re.compile(
    r"(\d{1,3}(?:[.,]\d)?)\s*[xX×]\s*(\d{1,3}(?:[.,]\d)?)\s*[xX×]\s*[Hh]?\s*(\d{1,3}(?:[.,]\d)?)\s*(?:cm)?",
)
# Il simbolo puo' precedere (Maury's: "€12,99") o seguire (Action: "12,99 €").
PRICE_RE = re.compile(r"(?:€\s*(\d{1,4})[.,](\d{2}))|(?:(\d{1,4})[.,](\d{2})\s*€)")


def parse_dims(text: str) -> tuple[float, float, float] | None:
    """Estrae la prima terna di dimensioni plausibile da un testo libero."""
    for m in DIM_RE.finditer(text):
        dims = tuple(misura(m.group(i)) for i in (1, 2, 3))
        if all(1 <= d <= 200 for d in dims):
            return dims  # type: ignore[return-value]
    return None


def _get(url: str, *, as_json: bool = False, extra_headers: dict[str, str] | None = None):
    headers = {**HEADERS, **(extra_headers or {})}
    if httpx is not None:
        r = httpx.get(url, headers=headers, timeout=30, follow_redirects=True)
        r.raise_for_status()
        return r.json() if as_json else r.text
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        raw = resp.read().decode("utf-8", "replace")
    return json.loads(raw) if as_json else raw


# --------------------------------------------------------------------------- #
# Fonti HTTP
# --------------------------------------------------------------------------- #
def search_ikea(query: str, limit: int) -> list[Prodotto]:
    url = (
        "https://sik.search.blue.cdtapps.com/it/it/search-result-page"
        f"?q={quote_plus(query)}&size={max(limit, 40)}"
    )
    data = _get(url, as_json=True)
    items = (
        data.get("searchResultPage", {}).get("products", {}).get("main", {}).get("items", [])
    )
    out: list[Prodotto] = []
    for it in items:
        p = it.get("product") or {}
        misure = p.get("itemMeasureReferenceText") or p.get("measureText") or ""
        dims = parse_dims(misure)
        prezzo = (p.get("salesPrice") or {}).get("numeral")
        if not dims or prezzo is None:
            continue
        out.append(
            Prodotto(
                shop="ikea",
                nome=f"{p.get('name', '')} {p.get('typeName', '')}".strip(),
                prezzo=float(prezzo),
                a=dims[0], b=dims[1], h=dims[2],
                link=p.get("pipUrl", ""),
                img=((p.get("mainImage") or {}).get("url", "")),
            )
        )
    return out[:limit]


def search_amazon(query: str, limit: int) -> list[Prodotto]:
    q = query.replace(" ", "+")
    html = _get(f"https://www.amazon.it/s?k={q}")
    out: list[Prodotto] = []
    seen: set[str] = set()
    for block in html.split('data-asin="')[1:]:
        asin = block[: block.find('"')]
        if not re.fullmatch(r"B[0-9A-Z]{9}", asin) or asin in seen:
            continue
        seen.add(asin)
        chunk = block[:6000]
        t = re.search(r'<h2[^>]*aria-label="([^"]{10,220})"', chunk)
        p = re.search(r'<span class="a-offscreen">([\d.,]+)\s*€</span>', chunk)
        if not (t and p):
            continue
        nome = t.group(1).replace("&amp;", "&")
        dims = parse_dims(nome)
        if not dims:
            continue
        out.append(
            Prodotto(
                shop="amazon",
                nome=nome[:90],
                prezzo=float(p.group(1).replace(".", "").replace(",", ".")),
                a=dims[0], b=dims[1], h=dims[2],
                link=f"https://www.amazon.it/dp/{asin}",
            )
        )
        if len(out) >= limit:
            break
    return out


# --------------------------------------------------------------------------- #
# Action — flight stream RSC (niente browser)
# --------------------------------------------------------------------------- #
# Action e' un Next.js App Router con React Server Components: non espone API
# JSON e l'HTML e' solo il guscio, ma i prodotti viaggiano nel flight stream.
# Con l'header "RSC: 1" il server lo restituisce da solo (text/x-component),
# senza HTML da scartare. Scoperto per browser-sniff il 2026-08-05.
#
# Due vincoli non negoziabili, entrambi verificati:
#   * lo User-Agent di un browser reale e' obbligatorio ovunque (senza -> 403);
#   * sulla scheda prodotto "RSC: 1" e' l'UNICO path che funziona: la stessa
#     URL in HTML da' 403 anche con UA valido, con qualsiasi Accept o Referer.
ACTION_BASE = "https://www.action.com/it-it"
RSC_HEADERS = {"RSC": "1"}
ACTION_HREF = '"href":"https://www.action.com/it-it/p/'


def _match_object(text: str, start: int, limit: int = 20000) -> str | None:
    """Dalla graffa in `start`, ritorna l'oggetto JSON bilanciato.

    Conta le graffe ignorando quelle dentro le stringhe: il flight stream e'
    pieno di testo marketing con parentesi, un conteggio ingenuo sbaglia.
    """
    depth = 0
    in_str = esc = False
    for i in range(start, min(len(text), start + limit)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _flight_products(text: str, lookback: int = 4000) -> list[dict]:
    """Estrae gli oggetti prodotto dal flight stream.

    Cerca ogni href di scheda prodotto e risale alla prima graffa che produce un
    oggetto JSON valido contenente anche titolo e prezzo. Risalire dall'href
    invece di cercare una chiave d'apertura evita di dipendere dall'ordine dei
    campi, che il server puo' cambiare senza preavviso.
    """
    out: list[dict] = []
    visti: set[str] = set()
    pos = 0
    while (m := text.find(ACTION_HREF, pos)) >= 0:
        pos = m + len(ACTION_HREF)
        for j in range(m, max(-1, m - lookback), -1):
            if text[j] != "{":
                continue
            blob = _match_object(text, j)
            if not blob or j + len(blob) <= m:
                continue  # l'oggetto si chiude prima dell'href: non e' il suo
            try:
                obj = json.loads(blob)
            except (ValueError, TypeError):
                continue
            if not isinstance(obj, dict) or not {"title", "price"} <= obj.keys():
                continue
            code = str(obj.get("code") or obj.get("id") or "")
            if code and code not in visti:
                visti.add(code)
                out.append(obj)
            break
    return out


def _action_prodotto(obj: dict) -> Prodotto | None:
    """Converte un oggetto del flight stream in Prodotto, se ha le misure."""
    # `description` nel lister contiene le dimensioni ("53x35x29 cm"): e' un
    # campo dedicato, non testo da indovinare come nello scraping HTML.
    dims = parse_dims(obj.get("description") or "") or parse_dims(obj.get("title") or "")
    amount = ((obj.get("price") or {}).get("current") or {}).get("amount")
    if not dims or amount is None:
        return None
    return Prodotto(
        shop="action",
        nome=(obj.get("title") or "")[:90],
        prezzo=float(amount),  # gia' numerico: nessuna regex sul prezzo
        a=dims[0], b=dims[1], h=dims[2],
        link=obj.get("href", ""),
        img=obj.get("image", ""),
    )


def search_action(query: str, limit: int) -> list[Prodotto]:
    """Cerca su Action via RSC. `cat:<slug>` interroga una categoria.

    Gli slug di categoria validi sono quelli linkati dalla home (`casalinghi`,
    `cucina`, `giardino`, ...): quelli compositi inventati danno 404.
    """
    if query.startswith("cat:"):
        base, sep = f"{ACTION_BASE}/c/{query[4:].strip('/')}/", "?"
    else:
        base, sep = f"{ACTION_BASE}/search/?q={quote_plus(query)}", "&"

    out: list[Prodotto] = []
    visti: set[str] = set()
    pagine = 1
    pagina = 1
    while pagina <= pagine and len(out) < limit:
        url = base if pagina == 1 else f"{base}{sep}page={pagina}"
        testo = _get(url, extra_headers=RSC_HEADERS)
        if pagina == 1:
            # numberOfItems e' il totale reale: la paginazione e' dichiarata,
            # non va indovinata cliccando "carica altro" finche' non finisce.
            if m := re.search(r'"numberOfPages":(\d+)', testo):
                pagine = int(m.group(1))
            if m := re.search(r'"numberOfItems":(\d+)', testo):
                print(f"[action] {m.group(1)} risultati su {pagine} pagine", file=sys.stderr)
        for obj in _flight_products(testo):
            if (p := _action_prodotto(obj)) and p.link not in visti:
                visti.add(p.link)
                out.append(p)
                if len(out) >= limit:
                    break
        pagina += 1
    return out


def action_categorie() -> list[str]:
    """Slug delle categorie di primo livello, dalla home (unica fonte affidabile)."""
    html = _get(f"{ACTION_BASE}/")
    return sorted({m.group(1) for m in re.finditer(r"it-it/c/([a-z0-9-]+)/", html)})


# --------------------------------------------------------------------------- #
# Fonti Playwright (SPA: l'HTML servito e' vuoto, serve un browser reale)
# --------------------------------------------------------------------------- #
SPA_SHOPS = {
    "maurys": "https://maurysonline.it/search?q={q}",
}

# Raccoglie il testo di ogni card prodotto risalendo dall'anchor: funziona su
# entrambi i siti senza dipendere da nomi di classe (che cambiano spesso).
EXTRACT_JS = r"""
(hrefPattern) => {
  const re = new RegExp(hrefPattern);
  const out = [], seen = new Set();
  for (const a of document.querySelectorAll('a[href]')) {
    const href = a.getAttribute('href') || '';
    if (!re.test(href)) continue;
    let card = a;
    for (let i = 0; i < 5 && card.parentElement; i++) {
      card = card.parentElement;
      if (card.querySelector('img') && /\d/.test(card.textContent || '')) break;
    }
    const img = card.querySelector('img');
    // innerText, non textContent: textContent concatena senza separatore e
    // incolla la fine del nome alla misura ("Plast1" + "26x18" -> "126x18").
    const txt = (card.innerText || card.textContent || '').replace(/\s+/g, ' ').trim();
    const key = href + '|' + txt.slice(0, 40);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({
      href: a.href,
      img: img ? (img.getAttribute('src') || img.getAttribute('data-src') || '') : '',
      text: txt.slice(0, 240),
    });
  }
  return out;
}
"""


EXTRACT_TEXT_JS = r"""
() => {
  const hit = [];
  const price = /\d+[.,]\d{2}\s*€|€\s*\d+[.,]\d{2}/;
  const dim = /\d{1,3}\s*[xX×]\s*\d{1,3}/;
  for (const el of document.querySelectorAll('div,li,article,section')) {
    const txt = (el.innerText || '').replace(/\s+/g, ' ').trim();
    if (txt.length < 20 || txt.length > 220) continue;
    if (!price.test(txt) || !dim.test(txt)) continue;
    // tieni il nodo piu' interno: scarta se un figlio soddisfa gia' i criteri
    let inner = false;
    for (const child of el.children) {
      const c = (child.innerText || '').replace(/\s+/g, ' ').trim();
      if (c.length >= 20 && c.length <= 220 && price.test(c) && dim.test(c)) { inner = true; break; }
    }
    if (inner) continue;
    const a = el.querySelector('a[href]');
    const img = el.querySelector('img');
    hit.push({
      href: a ? a.href : '',
      img: img ? (img.getAttribute('src') || img.getAttribute('data-src') || '') : '',
      text: txt.slice(0, 240),
    });
  }
  const seen = new Set();
  return hit.filter(h => !seen.has(h.text) && seen.add(h.text));
}
"""


def search_spa(
    shop: str, query: str, limit: int, *, headless: bool = True, pagine: int = 10
) -> list[Prodotto]:
    from playwright.sync_api import sync_playwright

    # "cat:<path>" e' un path di categoria, non una ricerca: il catalogo online
    # di Maury's non e' esposto dal motore di ricerca, solo dalle pagine di
    # categoria. Il prefisso evita la path-conversion di Git Bash/MSYS, che
    # riscrive un argomento "/foo" in "C:/Program Files/Git/foo".
    if query.startswith("cat:") or query.startswith("/"):
        path = query[4:] if query.startswith("cat:") else query
        base = SPA_SHOPS[shop].split("/search")[0].split("?")[0].rstrip("/")
        url = base + "/" + path.lstrip("/")
    else:
        url = SPA_SHOPS[shop].format(q=query.replace(" ", "+"))
    href_pattern = r"^/[a-z0-9-]{12,}$"
    raw: list[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        ctx = browser.new_context(
            user_agent=UA, locale="it-IT", viewport={"width": 1366, "height": 900}
        )
        page = ctx.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
        except Exception as exc:  # noqa: BLE001
            print(f"[{shop}] goto: {type(exc).__name__}", file=sys.stderr)
        for sel in (
            "button#onetrust-accept-btn-handler",
            'button:has-text("Accetta")',
            'button:has-text("Accept")',
        ):
            try:
                page.click(sel, timeout=2500)
                break
            except Exception:  # noqa: BLE001, PERF203
                pass
        try:
            page.wait_for_selector("a[href]", timeout=20000)
        except Exception:  # noqa: BLE001
            pass
        # scroll + "carica altro": entrambi i cataloghi sono lazy-loaded e
        # paginati, senza i click si ferma alla prima manciata di prodotti.
        for _ in range(pagine):
            page.mouse.wheel(0, 30000)
            page.wait_for_timeout(900)
            for sel in (
                'button:has-text("Carica altro")',
                'button:has-text("Mostra altri")',
                'a:has-text("Carica altro")',
            ):
                try:
                    page.click(sel, timeout=1500)
                    page.wait_for_timeout(1800)
                    break
                except Exception:  # noqa: BLE001, PERF203
                    pass
        raw = page.evaluate(EXTRACT_JS, href_pattern)
        print(f"[{shop}] anchor-mode: {len(raw)} card | url={page.url}", file=sys.stderr)
        if not raw:
            testo = page.evaluate("() => (document.body.innerText||'').length")
            print(f"[{shop}] fallback text-first (body {testo} char)", file=sys.stderr)
            # Fallback text-first: alcuni cataloghi (Maury's) non ancorano la
            # card a un link riconoscibile. Si cercano i nodi il cui testo
            # contiene sia un prezzo sia una misura, prendendo il piu' interno.
            raw = page.evaluate(EXTRACT_TEXT_JS)
            print(f"[{shop}] text-first: {len(raw)} card", file=sys.stderr)
        browser.close()

    out: list[Prodotto] = []
    for item in raw:
        text = item["text"]
        dims = parse_dims(text)
        pm = PRICE_RE.search(text)
        if not dims or not pm:
            continue
        nome = re.sub(
            r"AGGIUNGI ALLA LISTA DEI DESIDERI|ACQUISTA|Sconto del \d+%", "", text, flags=re.I
        )
        nome = re.split(r"€\s*\d|\d+[.,]\d{2}\s*€", nome)[0].strip()
        euro, cent = (pm.group(1), pm.group(2)) if pm.group(1) else (pm.group(3), pm.group(4))
        out.append(
            Prodotto(
                shop=shop,
                nome=nome[:90],
                prezzo=float(f"{euro}.{cent}"),
                a=dims[0], b=dims[1], h=dims[2],
                link=item["href"],
                img=item["img"],
            )
        )
        if len(out) >= limit:
            break
    return out


SHOPS = {
    "ikea": search_ikea,
    "amazon": search_amazon,
    "action": search_action,
    "maurys": lambda q, n: search_spa("maurys", q, n),
}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def cmd_search(args: argparse.Namespace) -> int:
    shops = list(SHOPS) if args.shop == "all" else [args.shop]
    trovati: list[Prodotto] = []
    for shop in shops:
        try:
            res = SHOPS[shop](args.query, args.limit)
        except Exception as exc:  # noqa: BLE001
            print(f"[{shop}] ERRORE {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        print(f"[{shop}] {len(res)} prodotti con dimensioni", file=sys.stderr)
        trovati.extend(res)

    for p in trovati:
        print(f"{p.prezzo:>7.2f} € | {p.a:g}x{p.b:g}x{p.h:g} | {p.shop:7} | {p.nome[:70]}")

    if args.json:
        dest = Path(args.json)
        if not dest.is_absolute():
            dest = DEFAULT_OUT / dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            json.dumps([asdict(p) for p in trovati], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n-> {dest.relative_to(REPO_ROOT)} ({len(trovati)} prodotti)", file=sys.stderr)
    return 0


def prodotti_da_payload(data, etichetta: str) -> list[Prodotto]:
    """Normalizza in Prodotto sia il formato di 'search --json' sia quello
    delle CLI stampate con Printing Press (action-pp-cli, maurys-pp-cli).

    Le due forme si distinguono da sole: 'search --json' produce una LISTA di
    Prodotto gia' completi di misure; le CLI stampate producono l'inviluppo
    {"meta":..., "results":[...]} con i campi del contratto (title/price/slug) e
    NESSUNA misura, perche' nessuno dei due cataloghi espone un campo dimensioni
    affidabile. Le misure si ricavano quindi dal titolo, e i prodotti che non ne
    dichiarano vengono SCARTATI invece che indovinati.
    """
    if isinstance(data, dict):
        righe = (data.get("results") or data.get("products")
                 or data.get("itemSummaries") or [])
    else:
        righe = data  # action-pp-cli --json emette una lista nuda

    out: list[Prodotto] = []
    for d in righe:
        if {"a", "b", "h", "nome"} <= d.keys():
            out.append(Prodotto(**d))  # formato nativo di 'search --json'
            continue

        nome = d.get("title") or d.get("nome") or ""
        # Le misure: Action le ha in un campo dedicato (`description` = "53x35x29
        # cm"), Maury's non le ha affatto e restano nel titolo, eBay a volte le
        # mette in `shortDescription`. Si provano i campi dedicati per primi
        # perche' sono gli unici affidabili.
        dims = (parse_dims(d.get("description") or "")
                or parse_dims(d.get("shortDescription") or "")
                or parse_dims(nome))

        # Il prezzo e' un numero (Maury's) o un oggetto annidato, con due forme
        # diverse: Action {"current": {"amount": 2.99}}, eBay Browse
        # {"value": "24.90", "currency": "EUR"} — dove `value` e' una STRINGA.
        prezzo = d.get("price")
        if isinstance(prezzo, dict):
            prezzo = (prezzo.get("current") or {}).get("amount") or prezzo.get("value")

        if not dims or not prezzo:
            continue

        # Il link e' un URL assoluto (Action `href`, eBay `itemWebUrl`) o uno
        # slug relativo alla radice del sito (Maury's).
        link = d.get("href") or d.get("link") or d.get("itemWebUrl") or ""
        if not link and (slug := d.get("slug")):
            link = slug if slug.startswith("/") else "/" + slug

        # L'immagine e' una stringa (Action, Maury's) o {"imageUrl": ...} (eBay).
        img = d.get("image") or ""
        if isinstance(img, dict):
            img = img.get("imageUrl", "")

        out.append(
            Prodotto(
                shop=etichetta,
                nome=nome[:90],
                prezzo=float(prezzo),
                a=dims[0], b=dims[1], h=dims[2],
                link=link,
                img=img,
            )
        )
    return out


def cmd_fit(args: argparse.Namespace) -> int:
    prodotti: list[Prodotto] = []
    visti: set[tuple] = set()
    for spec in args.source:
        # "-" legge da stdin: consente di incatenare direttamente una CLI
        # stampata senza passare da un file temporaneo.
        if spec == "-":
            sorgenti: list[tuple[str, str]] = [("stdin", sys.stdin.read())]
        else:
            paths = sorted(DEFAULT_OUT.glob(spec)) if not Path(spec).is_absolute() else [Path(spec)]
            sorgenti = [(p.stem, p.read_text(encoding="utf-8")) for p in paths]
        for nome_sorgente, testo in sorgenti:
            # Etichetta del negozio: esplicita se data, altrimenti dedotta dal
            # nome del file ("maurys-baule.json" -> "maurys").
            etichetta = args.shop or nome_sorgente.split("-")[0]
            for p in prodotti_da_payload(json.loads(testo), etichetta):
                # Le MISURE fanno parte dell'identita'. Action riusa lo stesso
                # titolo per taglie diverse ("Contenitore Heidrun" esiste in 7
                # misure) e due di esse costano uguale: senza le misure nella
                # chiave, articoli diversi collidono e spariscono in silenzio.
                chiave = (p.shop, p.nome, p.prezzo, p.a, p.b, p.h)
                if chiave in visti:
                    continue
                visti.add(chiave)
                prodotti.append(p)
    print(f"{len(prodotti)} prodotti unici da {len(args.source)} pattern", file=sys.stderr)
    for spec in args.vano:
        vano = Vano.parse(spec)
        litri_vano = vano.L * vano.P * vano.H / 1000
        print(
            f"\n### {vano.nome} — {vano.L:g}x{vano.P:g}x h{vano.H:g} cm utili "
            f"({litri_vano:.0f} L)"
        )
        top = classifica(
            vano,
            prodotti,
            args.min_vol,
            max_pz=args.max_pz,
            budget=args.budget,
            ordina=args.ordina,
            tutte=args.tutte,
        )[: args.limit]
        if not top:
            print("  nessuna soluzione entro i vincoli dati")
            continue
        etichetta = "tutte le soluzioni" if args.tutte else "frontiera di Pareto"
        print(f"  [{etichetta}, ordinate per {args.ordina}]")
        for f in top:
            p = f.prodotto
            print(
                f"  {f.euro_litro:5.2f} €/L | {f.costo:7.2f} € | "
                f"{f.totale_pezzi:3d} pz ({f.nx}x{f.ny} x{f.livelli} liv) | "
                f"{f.vol * 100:3.0f}% vol | {f.litri:5.0f} L | "
                f"{p.prezzo:6.2f} €/pz | {p.a:g}x{p.b:g}x{p.h:g} | "
                f"{p.shop:7} | {p.nome[:48]}"
            )
    return 0


def cmd_shops(_: argparse.Namespace) -> int:
    print("ikea    API JSON      veloce, misure sempre presenti")
    print("amazon  HTTP + UA     misure solo se nel titolo")
    print("action  RSC + UA      catalogo ampio e economico; misure in un campo dedicato")
    print("        └ cat:<slug>  interroga una categoria (vedi: shopcli categorie)")
    print("maurys  Playwright    catalogo online parziale (molto e' solo in negozio)")
    print()
    print("Per action e maurys conviene la CLI stampata, piu' veloce e completa;")
    print("'fit' ne legge l'output direttamente, anche da stdin:")
    print("  maurys-pp-cli category bauli-e-contenitori --all --json \\")
    print("    | python scripts/shopcli.py fit --from - --shop maurys --vano C1=32x83x18")
    return 0


def cmd_categorie(_: argparse.Namespace) -> int:
    for slug in action_categorie():
        print(f"cat:{slug}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="shopcli", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="cerca prodotti su uno o tutti i negozi")
    s.add_argument("shop", choices=[*SHOPS, "all"])
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=40)
    s.add_argument("--json", help="salva il risultato (default: vault/confronti/_scrape/)")
    s.set_defaults(func=cmd_search)

    f = sub.add_parser(
        "fit",
        help="tassellazione di un vano, con il compromesso riempimento/costo/pezzi",
    )
    f.add_argument(
        "--from", dest="source", required=True, action="append",
        help="JSON da 'search --json'; ammette glob e ripetizioni (es. --from 'action-*.json')",
    )
    f.add_argument("--vano", action="append", required=True, metavar="NOME=LxPxH")
    f.add_argument(
        "--shop", default="",
        help="etichetta del negozio per le sorgenti senza campo 'shop' "
             "(output delle CLI stampate); default: dedotta dal nome del file",
    )
    f.add_argument("--min-vol", type=float, default=0.5)
    f.add_argument("--limit", type=int, default=8)
    f.add_argument(
        "--max-pz", type=int, default=None, metavar="N",
        help="scarta le soluzioni con piu' di N pezzi (riempire un vano grande "
             "con 200 contenitini e' matematicamente ottimo e praticamente inutile)",
    )
    f.add_argument(
        "--budget", type=float, default=None, metavar="EUR",
        help="scarta le soluzioni che costano piu' di EUR in totale",
    )
    f.add_argument(
        "--sort", dest="ordina", default="valore", choices=sorted(ORDINAMENTI),
        help="valore = meno euro per litro (default); costo = spesa totale; "
             "pezzi = meno oggetti; riempimento = massimo volume occupato",
    )
    f.add_argument(
        "--tutte", action="store_true",
        help="mostra anche le soluzioni dominate (peggiori su OGNI criterio); "
             "di default si vede solo la frontiera dei compromessi sensati",
    )
    f.set_defaults(func=cmd_fit)

    sh = sub.add_parser("shops", help="elenca le fonti disponibili")
    sh.set_defaults(func=cmd_shops)

    c = sub.add_parser("categorie", help="elenca gli slug di categoria di Action")
    c.set_defaults(func=cmd_categorie)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
