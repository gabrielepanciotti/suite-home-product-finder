import type {
  Acquisto,
  CatalogoResponse,
  Confronto,
  ConfrontoSummary,
  NodeOverviewData,
  Preferenze,
  RispostaBarattoli,
  RispostaContenere,
  Spazio,
} from "../types";

/** Le misure di UN oggetto e quanti ne vanno conservati. */
export interface ParamsContenere {
  a: number;
  b: number;
  h: number;
  n: number;
  in_piedi: boolean;
  impilabili: boolean;
  margine: number;
  max_scatole: number | null;
  // Materiale: il filtro sta nel backend perché il cartone è la roba più
  // economica del catalogo e altrimenti riempirebbe la classifica prima che
  // qualcosa di plastica arrivi al browser.
  materiali: string[];
  escludi: string[];
  ignoti: boolean;
}

// Tutte le chiamate passano dal proxy Vite (/api -> backend 10008).
async function get<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

export const api = {
  listConfronti: () => get<ConfrontoSummary[]>("/api/confronti"),

  getPurchases: () => get<Acquisto[]>("/api/purchases"),

  // Scheda nodo live (pubblica, come /api/health).
  getOverview: () => get<NodeOverviewData>("/api/overview"),

  getConfronto: (slug: string) => get<Confronto>(`/api/confronti/${slug}`),

  // Catalogo grezzo: tutte le scatole trovate dalle CLI negozio.
  getCatalogo: () => get<CatalogoResponse>("/api/catalogo"),

  // Spazi da riempire + tassellazione classificata per ogni vano misurato.
  getSpazi: () => get<Spazio[]>("/api/spazi"),

  // Barattoli noti per marca: la preselezione del modulo.
  getBarattoli: () => get<RispostaBarattoli>("/api/barattoli"),

  // Quale scatola contiene N oggetti di una certa misura. Il calcolo sta nel
  // backend (stessa geometria della tassellazione), qui passano solo i numeri.
  cercaContenitori: (p: ParamsContenere) => {
    const q = new URLSearchParams({
      a: String(p.a),
      b: String(p.b),
      h: String(p.h),
      n: String(p.n),
      in_piedi: String(p.in_piedi),
      impilabili: String(p.impilabili),
      margine: String(p.margine),
      ignoti: String(p.ignoti),
    });
    if (p.max_scatole != null) q.set("max_scatole", String(p.max_scatole));
    // Ripetuti, non separati da virgola: è la forma che FastAPI legge come lista.
    for (const m of p.materiali) q.append("materiali", m);
    for (const m of p.escludi) q.append("escludi", m);
    return get<RispostaContenere>(`/api/contenere?${q}`);
  },

  // Verdetti per vano: preferiti in cima, scartati in fondo. Stanno nel vault,
  // non nel browser: la decisione vale per il nodo, non per questa scheda.
  getPreferenze: () => get<Preferenze>("/api/preferenze"),

  salvaPreferenze: async (
    chiave: string,
    preferiti: string[],
    scartati: string[],
  ): Promise<Preferenze> => {
    const r = await fetch("/api/preferenze", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chiave, preferiti, scartati }),
    });
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json();
  },

  salvaScelta: async (
    slug: string,
    selezioni: Record<string, number>,
  ): Promise<Confronto> => {
    const r = await fetch(`/api/confronti/${slug}/scelta`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ selezioni }),
    });
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json();
  },

  // URL immagine prodotto (servita dal backend, dentro vault/confronti/images)
  imgUrl: (slug: string, filename: string | null) =>
    filename ? `/api/images/${slug}/${filename}` : null,
};
