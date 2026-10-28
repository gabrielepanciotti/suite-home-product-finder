"""Genera una pagina HTML self-contained per SCEGLIERE le scatole (immagini inline base64).

L'utente apre l'HTML, vede i prodotti con foto, seleziona uno per collocazione e
copia la scelta da rimandare. Immagini incorporate -> funziona offline, file unico.
"""
import base64
import io
from pathlib import Path
import httpx
from PIL import Image

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "it-IT,it;q=0.9"}
AC = "https://asset.action.com/image/upload/t_digital_square/w_512/"

# group, id, nome, negozio, dim, cap, eur, epl, mat, ruote, nota, img, link, preselect
CARDS = [
    ("Sotto il letto", "sl1", "Action contenitore con coperchio 29L", "Action", "59x39x18", "29 L", "5,95", "0,21",
     "Plastica", "No", "Gia' scelto: piu' economico e basso, con coperchio. Negozio + online.",
     AC + "13626189.jpg", "https://www.action.com/it-it/p/2568528/contenitore-con-coperchio/", True),

    ("Armadio / mensola", "ar1", "Action contenitore con ruote 60L", "Action", "59x39x36", "60 L", "8,95", "0,15",
     "Plastica", "Ruote", "Ottimo compromesso prezzo/comodita', con ruote per estrarlo dal ripiano.",
     AC + "2533870_5715079104003-111_01_q1fvo2.jpg", "https://www.action.com/it-it/p/2533870/contenitore-con-ruote/", False),
    ("Armadio / mensola", "ar2", "Action coperchio a clip 80L", "Action", "58x39x43", "80 L", "10,95", "0,14",
     "Plastica", "No", "Piu' capiente, chiusura a clip sicura. Buono se i ripiani sono alti.",
     AC + "17019061.jpg", "https://www.action.com/it-it/p/3000808/contenitore-con-coperchio-a-clip/", False),
    ("Armadio / mensola", "ar3", "Maury's box porta indumenti 74L", "Maury's", "60x41x40", "74 L", "9,90", "0,13",
     "Plastica opaca bianca", "Ruote", "Miglior euro/litro del confronto, con ruote. Solo in negozio.",
     "https://cdn.maurysonline.it/immagini/6075081_0438026-box-porta-indumenti-con-ruote-dimensioni-60x41x40cm-e-coperchio-bianco-main_510.jpeg",
     "https://maurysonline.it/box-contenitore-con-ruote-dimensioni-60x41x40cm-e-coperchio-bianco", False),

    ("Cantina / garage", "ca1", "Action Heidrun 100L", "Action", "59x45x50", "100 L", "9,95", "0,10",
     "Plastica vari colori", "No", "Miglior valore in assoluto del confronto (0,10 euro/L). Negozio + online.",
     AC + "2535483_8010059016510-110_05_y50wtb.jpg", "https://www.action.com/it-it/p/2535483/contenitore-heidrun/", False),
    ("Cantina / garage", "ca2", "IKEA SAMLA 130L", "IKEA", "79x57x43", "130 L", "20,00", "0,15",
     "Trasparente", "No", "Piu' grande, trasparente (vedi il contenuto), disponibile online.",
     "https://www.ikea.com/it/it/images/products/samla-contenitore-con-coperchio-trasparente__0711819_pe728498_s5.jpg",
     "https://www.ikea.com/it/it/p/samla-contenitore-con-coperchio-trasparente-s29440819/", False),
    ("Cantina / garage", "ca3", "Tontarelli Box One 140L", "OrizzonteShop", "79x52x52", "140 L", "29,00", "0,21",
     "Opaco nero, clip", "No", "Robusto industriale con chiusura a clip. Il piu' capiente.",
     "http://www.orizzonteshop.it/cdn/shop/products/immagine-1-tontarelli-boxone-storage-ccoperchio-8035940999-tontarelli-ean-8009404212080.jpg?height=600&width=600",
     "https://www.orizzonteshop.it/products/tontarelli-boxone-storage-ccoperchio-8035940999-tontarelli-ean-8009404212080", False),
]


def img_data_uri(url):
    try:
        with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as c:
            raw = c.get(url).content
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        w, h = im.size
        scale = 460 / max(w, h)
        if scale < 1:
            im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=82)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/jpeg;base64,{b64}"
    except Exception as e:
        print("img ERR", url[:50], type(e).__name__)
        return ""


groups = {}
for c in CARDS:
    groups.setdefault(c[0], []).append(c)

cards_html = []
for grp, items in groups.items():
    gid = "g_" + str(abs(hash(grp)) % 10000)
    inner = []
    for (g, cid, nome, neg, dim, cap, eur, epl, mat, ruote, nota, img, link, pre) in items:
        uri = img_data_uri(img)
        sel = " selected" if pre else ""
        badge = '<span class="pre">consigliato</span>' if pre else ''
        inner.append(f"""
      <label class="card{sel}" data-group="{grp}" data-name="{nome}" data-eur="{eur}">
        <input type="radio" name="{grp}" {'checked' if pre else ''} hidden>
        <div class="imgwrap"><img loading="lazy" src="{uri}" alt="{nome}"></div>
        <div class="body">
          <div class="top"><span class="store">{neg}</span>{badge}<span class="check">&#10003;</span></div>
          <h3>{nome}</h3>
          <div class="pill">{epl} &euro;/L</div>
          <table class="specs">
            <tr><td>Prezzo</td><td><b>{eur} &euro;</b></td></tr>
            <tr><td>Capacita'</td><td>{cap}</td></tr>
            <tr><td>Dim (cm)</td><td>{dim}</td></tr>
            <tr><td>Materiale</td><td>{mat}</td></tr>
            <tr><td>Ruote</td><td>{ruote}</td></tr>
          </table>
          <p class="note">{nota}</p>
          <a class="link" href="{link}" target="_blank" rel="noopener">Vedi prodotto &rarr;</a>
        </div>
      </label>""")
    cards_html.append(f"""
    <section>
      <h2>{grp}</h2>
      <div class="grid">{''.join(inner)}</div>
    </section>""")

html = f"""<!DOCTYPE html>
<html lang="it"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Scegli le scatole da stoccaggio</title>
<style>
  :root{{--bg:#0f172a;--card:#fff;--ink:#0f172a;--mut:#64748b;--line:#e2e8f0;--accent:#16a34a;--accent2:#2563eb}}
  *{{box-sizing:border-box}}
  body{{margin:0;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#f1f5f9;color:var(--ink);padding-bottom:96px}}
  header{{background:linear-gradient(135deg,#1e293b,#0f172a);color:#fff;padding:28px 20px}}
  header h1{{margin:0 0 6px;font-size:24px}}
  header p{{margin:0;color:#cbd5e1;font-size:14px}}
  main{{max-width:1100px;margin:0 auto;padding:20px}}
  section{{margin:28px 0}}
  section h2{{font-size:18px;margin:0 0 14px;padding-left:10px;border-left:4px solid var(--accent2)}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px}}
  .card{{background:var(--card);border:2px solid var(--line);border-radius:16px;overflow:hidden;cursor:pointer;
    transition:.2s ease;display:flex;flex-direction:column;position:relative}}
  .card:hover{{transform:translateY(-3px);box-shadow:0 12px 28px rgba(15,23,42,.12)}}
  .card.selected{{border-color:var(--accent);box-shadow:0 0 0 3px rgba(22,163,74,.18)}}
  .imgwrap{{aspect-ratio:1/1;background:#fff;display:flex;align-items:center;justify-content:center;padding:14px;border-bottom:1px solid var(--line)}}
  .imgwrap img{{max-width:100%;max-height:100%;object-fit:contain}}
  .body{{padding:14px;display:flex;flex-direction:column;gap:8px;flex:1}}
  .top{{display:flex;align-items:center;gap:8px}}
  .store{{font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--mut);background:#f1f5f9;padding:3px 8px;border-radius:999px}}
  .pre{{font-size:11px;font-weight:700;color:#fff;background:var(--accent2);padding:3px 8px;border-radius:999px}}
  .check{{margin-left:auto;width:24px;height:24px;border-radius:999px;background:var(--accent);color:#fff;
    display:flex;align-items:center;justify-content:center;font-size:14px;opacity:0;transform:scale(.5);transition:.2s}}
  .card.selected .check{{opacity:1;transform:scale(1)}}
  .body h3{{margin:0;font-size:15px;line-height:1.25}}
  .pill{{align-self:flex-start;font-weight:800;font-size:13px;color:#065f46;background:#d1fae5;padding:4px 10px;border-radius:999px}}
  .specs{{width:100%;border-collapse:collapse;font-size:13px}}
  .specs td{{padding:3px 0;border-bottom:1px dashed var(--line)}}
  .specs td:first-child{{color:var(--mut)}}
  .specs td:last-child{{text-align:right}}
  .note{{font-size:12.5px;color:#475569;margin:2px 0 0;line-height:1.4}}
  .link{{font-size:13px;color:var(--accent2);text-decoration:none;font-weight:600;margin-top:auto}}
  .link:hover{{text-decoration:underline}}
  footer{{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid var(--line);
    box-shadow:0 -6px 20px rgba(15,23,42,.08);padding:12px 20px}}
  .fbar{{max-width:1100px;margin:0 auto;display:flex;align-items:center;gap:16px;flex-wrap:wrap}}
  .summary{{font-size:13px;color:#334155;flex:1;min-width:200px}}
  .summary b{{color:var(--ink)}}
  .total{{font-size:18px;font-weight:800}}
  button{{border:0;background:var(--accent);color:#fff;font-weight:700;font-size:14px;padding:11px 18px;
    border-radius:12px;cursor:pointer;transition:.15s}}
  button:hover{{filter:brightness(1.06)}}
  button:active{{transform:scale(.97)}}
  .ok{{color:var(--accent);font-weight:700;font-size:13px;opacity:0;transition:.3s}}
  .ok.show{{opacity:1}}
</style></head>
<body>
<header>
  <h1>Scegli le scatole da stoccaggio</h1>
  <p>Clicca la scatola che preferisci per ogni collocazione. In fondo copi la tua scelta e me la incolli in chat.</p>
</header>
<main>{''.join(cards_html)}</main>
<footer><div class="fbar">
  <div class="summary" id="summary">Nessuna scelta ancora.</div>
  <div class="total" id="total"></div>
  <span class="ok" id="ok">Copiato! Incollalo in chat.</span>
  <button onclick="copia()">Copia la mia scelta</button>
</div></footer>
<script>
  const cards = document.querySelectorAll('.card');
  cards.forEach(c => c.addEventListener('click', () => {{
    document.querySelectorAll('.card[data-group="'+c.dataset.group+'"]').forEach(x=>x.classList.remove('selected'));
    c.classList.add('selected'); c.querySelector('input').checked = true; update();
  }}));
  function getSel(){{
    const out = {{}};
    document.querySelectorAll('.card.selected').forEach(c => out[c.dataset.group] = {{n:c.dataset.name, e:parseFloat(c.dataset.eur.replace(',','.'))}});
    return out;
  }}
  function update(){{
    const s = getSel(); const groups = Object.keys(s);
    document.getElementById('summary').innerHTML = groups.length
      ? groups.map(g => g+': <b>'+s[g].n+'</b>').join('  &nbsp;|&nbsp;  ')
      : 'Nessuna scelta ancora.';
    const tot = groups.reduce((a,g)=>a+s[g].e,0);
    document.getElementById('total').textContent = tot ? tot.toFixed(2).replace('.',',')+' €' : '';
  }}
  function copia(){{
    const s = getSel();
    const txt = 'Scelta scatole stoccaggio:\\n' + Object.keys(s).map(g => '- '+g+': '+s[g].n+' ('+s[g].e.toFixed(2).replace('.',',')+' EUR)').join('\\n');
    navigator.clipboard.writeText(txt).then(()=>{{
      const ok=document.getElementById('ok'); ok.classList.add('show'); setTimeout(()=>ok.classList.remove('show'),2500);
    }});
  }}
  update();
</script>
</body></html>"""

out = Path(__file__).resolve().parents[1] / "vault" / "prodotti" / "contenitori" / "scelta-scatole-stoccaggio.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("OK ->", out, "|", round(len(html)/1024), "KB")
