import type { FiltriSpazi } from "../../hooks/useFiltriSpazi";
import { passa } from "../../hooks/useFiltriSpazi";
import type { Soluzione, VerdettiVano, Vano } from "../../types";

export interface RigaVano extends Soluzione {
  preferito: boolean;
  scartato: boolean;
}

/**
 * Le righe da mostrare per un vano: filtrate, ordinate, e poi divise in tre
 * fasce — preferite in cima, normali, scartate in fondo.
 *
 * Le fasce vengono DOPO l'ordinamento, non al posto suo: dentro ogni fascia
 * valgono i criteri scelti (il sort di JS è stabile, quindi non si perdono).
 * Così scartare una scatola non la cancella, la mette da parte.
 */
export function preparaRighe(
  vano: Vano,
  verdetti: VerdettiVano,
  filtri: FiltriSpazi,
  ordina: (s: Soluzione[]) => Soluzione[],
): RigaVano[] {
  const decorate: RigaVano[] = vano.soluzioni.map((s) => ({
    ...s,
    preferito: verdetti.preferiti.includes(s.id),
    scartato: verdetti.scartati.includes(s.id),
  }));
  const filtrate = decorate.filter((r) => passa(r, filtri, r));
  const fascia = (r: RigaVano) => (r.preferito ? 0 : r.scartato ? 2 : 1);
  return (ordina(filtrate) as RigaVano[]).sort((a, b) => fascia(a) - fascia(b));
}
