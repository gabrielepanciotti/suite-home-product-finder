import type { CampoVano } from "../components/spazi/colonne";
import { COLONNE, valore } from "../components/spazi/colonne";
import type { Criterio as CriterioGenerico } from "./useOrdine";
import { useOrdine } from "./useOrdine";
import type { Soluzione } from "../types";

export type Criterio = CriterioGenerico<CampoVano>;

const INIZIALE: Criterio[] = [{ campo: "vol_pct", dir: "desc" }];

/** L'ordinamento a più criteri, legato alle colonne della classifica di un vano. */
export function useOrdineVani() {
  return useOrdine<Soluzione, CampoVano>(COLONNE, valore, INIZIALE);
}
