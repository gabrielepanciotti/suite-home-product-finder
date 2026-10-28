import { useMemo, useState } from "react";
import type { Soluzione, Spazio } from "../types";

export interface FiltriSpazi {
  q: string;
  negozi: string[]; // vuoto = tutti
  materiali: string[]; // vuoto = tutti
  tratti: string[]; // tutti quelli scelti devono esserci
  coperchio: "si" | "no" | null;
  hMin: number | null;
  prezzoMax: number | null;
  riempMin: number | null; // % di volume riempito
  soloOttimali: boolean;
  soloPreferiti: boolean;
  nascondiScartati: boolean;
}

export const FILTRI_VUOTI: FiltriSpazi = {
  q: "",
  negozi: [],
  materiali: [],
  tratti: [],
  coperchio: null,
  hMin: null,
  prezzoMax: null,
  riempMin: null,
  soloOttimali: false,
  soloPreferiti: false,
  // Gli scartati restano visibili in fondo: scartare è una decisione, e una
  // decisione vuole poter essere riletta. Il chip la nasconde su richiesta.
  nascondiScartati: false,
};

/** Il vocabolario dei chip nasce dai dati, non da una lista scritta a mano. */
export function vocabolario(spazi: Spazio[]) {
  const negozi = new Set<string>();
  const materiali = new Set<string>();
  const tratti = new Set<string>();
  for (const s of spazi) {
    for (const v of s.vani) {
      for (const sol of v.soluzioni) {
        negozi.add(sol.negozio);
        (sol.materiali ?? []).forEach((m) => materiali.add(m));
        (sol.tratti ?? []).forEach((t) => tratti.add(t));
      }
    }
  }
  const ord = (s: Set<string>) =>
    [...s].sort((a, b) => a.localeCompare(b, "it"));
  return {
    negozi: ord(negozi),
    materiali: ord(materiali),
    tratti: ord(tratti),
  };
}

export function passa(
  s: Soluzione,
  f: FiltriSpazi,
  stato: { preferito: boolean; scartato: boolean },
): boolean {
  // Un preferito è una decisione già presa: non lo nasconde nessun filtro,
  // altrimenti sparirebbe proprio ciò che si è messo da parte per ricordarlo.
  if (stato.preferito) return true;
  if (f.soloPreferiti) return false;
  if (f.nascondiScartati && stato.scartato) return false;
  if (f.q && !s.nome.toLowerCase().includes(f.q.trim().toLowerCase()))
    return false;
  if (f.negozi.length && !f.negozi.includes(s.negozio)) return false;
  if (
    f.materiali.length &&
    !(s.materiali ?? []).some((m) => f.materiali.includes(m))
  )
    return false;
  if (f.tratti.length && !f.tratti.every((t) => (s.tratti ?? []).includes(t)))
    return false;
  if (f.coperchio === "si" && s.coperchio !== true) return false;
  if (f.coperchio === "no" && s.coperchio === true) return false;
  if (f.hMin != null && s.h < f.hMin) return false;
  if (f.prezzoMax != null && s.prezzo > f.prezzoMax) return false;
  if (f.riempMin != null && s.vol_pct < f.riempMin) return false;
  if (f.soloOttimali && !s.ottimale) return false;
  return true;
}

export function useFiltriSpazi() {
  const [filtri, setFiltri] = useState<FiltriSpazi>(FILTRI_VUOTI);

  const patch = (p: Partial<FiltriSpazi>) => setFiltri((f) => ({ ...f, ...p }));

  const alternaIn = (chiave: "negozi" | "materiali" | "tratti", v: string) =>
    setFiltri((f) => ({
      ...f,
      [chiave]: f[chiave].includes(v)
        ? f[chiave].filter((x) => x !== v)
        : [...f[chiave], v],
    }));

  const attivi = useMemo(
    () =>
      (Object.keys(FILTRI_VUOTI) as (keyof FiltriSpazi)[]).filter((k) => {
        const a = filtri[k];
        const b = FILTRI_VUOTI[k];
        return Array.isArray(a) ? a.length !== (b as string[]).length : a !== b;
      }).length,
    [filtri],
  );

  return {
    filtri,
    patch,
    alternaIn,
    attivi,
    azzera: () => setFiltri(FILTRI_VUOTI),
  };
}
