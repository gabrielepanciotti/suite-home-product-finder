import { useMemo, useState } from "react";
import type { CatalogoItem } from "../types";

export type Vista = "griglia" | "tabella";
export type ChiaveOrdine = "prezzo" | "eur_per_l" | "volume_l" | "h" | "nome";
export type Direzione = "asc" | "desc";

export interface Filtri {
  q: string;
  negozi: string[]; // vuoto = tutti
  hMin: number | null;
  prezzoMax: number | null;
  // Di default il catalogo nasconde ciò che scatola non è: senza questo, in
  // cima alla classifica per €/litro finiscono buste salvaspazio e simili.
  soloScatole: boolean;
}

const FILTRI_VUOTI: Filtri = {
  q: "",
  negozi: [],
  hMin: null,
  prezzoMax: null,
  soloScatole: true,
};

function confronta(
  a: CatalogoItem,
  b: CatalogoItem,
  chiave: ChiaveOrdine,
): number {
  if (chiave === "nome") return a.nome.localeCompare(b.nome, "it");
  const va = a[chiave];
  const vb = b[chiave];
  // Le righe senza metrica (es. €/L nullo) finiscono sempre in fondo.
  if (va == null) return 1;
  if (vb == null) return -1;
  return va - vb;
}

/** Stato di filtro/ordinamento/vista del catalogo. Puro client-side. */
export function useCatalogoFiltri(items: CatalogoItem[]) {
  const [filtri, setFiltri] = useState<Filtri>(FILTRI_VUOTI);
  const [ordine, setOrdine] = useState<ChiaveOrdine>("eur_per_l");
  const [direzione, setDirezione] = useState<Direzione>("asc");
  const [vista, setVista] = useState<Vista>("griglia");
  // Le miniature in tabella sono opzionali: a colonne strette la riga si legge
  // meglio senza. In griglia la foto è il punto, quindi lì non si tocca.
  const [fotoInTabella, setFotoInTabella] = useState(true);

  const patch = (p: Partial<Filtri>) => setFiltri((f) => ({ ...f, ...p }));

  const toggleNegozio = (negozio: string) =>
    setFiltri((f) => ({
      ...f,
      negozi: f.negozi.includes(negozio)
        ? f.negozi.filter((n) => n !== negozio)
        : [...f.negozi, negozio],
    }));

  /** Cliccare la colonna già attiva inverte la direzione, come in un'app tabellare. */
  const ordinaPer = (chiave: ChiaveOrdine) => {
    if (chiave === ordine) {
      setDirezione((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setOrdine(chiave);
      setDirezione(chiave === "volume_l" || chiave === "h" ? "desc" : "asc");
    }
  };

  const risultati = useMemo(() => {
    const q = filtri.q.trim().toLowerCase();
    const filtrati = items.filter((i) => {
      if (q && !i.nome.toLowerCase().includes(q)) return false;
      if (filtri.negozi.length && !filtri.negozi.includes(i.negozio))
        return false;
      if (filtri.hMin != null && i.h < filtri.hMin) return false;
      if (filtri.prezzoMax != null && i.prezzo > filtri.prezzoMax) return false;
      if (filtri.soloScatole && i.classe === "non-scatola") return false;
      return true;
    });
    const segno = direzione === "asc" ? 1 : -1;
    return [...filtrati].sort((a, b) => segno * confronta(a, b, ordine));
  }, [items, filtri, ordine, direzione]);

  // `soloScatole` è il default, non un filtro che l'utente ha messo: non entra
  // nel conteggio di "azzera filtri (n)".
  const attivi =
    (filtri.q ? 1 : 0) +
    (filtri.negozi.length ? 1 : 0) +
    (filtri.hMin != null ? 1 : 0) +
    (filtri.prezzoMax != null ? 1 : 0);

  return {
    filtri,
    patch,
    toggleNegozio,
    azzera: () => setFiltri(FILTRI_VUOTI),
    attivi,
    ordine,
    direzione,
    ordinaPer,
    vista,
    setVista,
    fotoInTabella,
    setFotoInTabella,
    risultati,
  };
}
