import { useCallback, useMemo, useState } from "react";

export type Direzione = "asc" | "desc";

/** Cosa serve sapere di una colonna per ordinarla e per spiegarla. */
export interface Colonna {
  label: string;
  /** Cosa dice davvero il numero: appare al passaggio del mouse. */
  aiuto: string;
  allinea: "sx" | "dx" | "centro";
  /** Il verso in cui "meglio" sta in cima, usato al primo clic. */
  naturale: Direzione;
}

export interface Criterio<C extends string> {
  campo: C;
  dir: Direzione;
}

/**
 * Ordinamento a più criteri in sequenza, per qualunque tabella.
 *
 * Un clic ordina per quella colonna sola — è il caso normale, e accumulare
 * criteri a ogni clic renderebbe la tabella imprevedibile. Shift+clic aggiunge
 * la colonna come criterio successivo (a parità del primo, decide il secondo);
 * ri-cliccare una colonna già in uso ne inverte il verso.
 *
 * La tabella resta ignara del tipo delle sue righe: le passa solo il dizionario
 * delle colonne e una funzione che dà il valore confrontabile di un campo.
 */
export function useOrdine<T, C extends string>(
  colonne: Record<C, Colonna>,
  valore: (riga: T, campo: C) => number | string,
  iniziale: Criterio<C>[],
) {
  const [criteri, setCriteri] = useState<Criterio<C>[]>(iniziale);

  const ordinaPer = useCallback(
    (campo: C, aggiungi: boolean) => {
      setCriteri((attuali) => {
        const i = attuali.findIndex((c) => c.campo === campo);
        if (i >= 0) {
          const invertito: Criterio<C> = {
            campo,
            dir: attuali[i].dir === "asc" ? "desc" : "asc",
          };
          if (!aggiungi && attuali.length === 1) return [invertito];
          const copia = [...attuali];
          copia[i] = invertito;
          return copia;
        }
        const nuovo: Criterio<C> = { campo, dir: colonne[campo].naturale };
        return aggiungi ? [...attuali, nuovo] : [nuovo];
      });
    },
    [colonne],
  );

  const rimuovi = useCallback(
    (campo: C) => {
      setCriteri((attuali) => {
        const rimasti = attuali.filter((c) => c.campo !== campo);
        return rimasti.length ? rimasti : iniziale;
      });
    },
    [iniziale],
  );

  const ordina = useCallback(
    (righe: T[]): T[] =>
      [...righe].sort((a, b) => {
        for (const c of criteri) {
          const va = valore(a, c.campo);
          const vb = valore(b, c.campo);
          const segno = c.dir === "asc" ? 1 : -1;
          const d =
            typeof va === "string" || typeof vb === "string"
              ? segno * String(va).localeCompare(String(vb), "it")
              : segno * (va - vb);
          if (d !== 0) return d;
        }
        return 0;
      }),
    [criteri, valore],
  );

  const azzera = useCallback(() => setCriteri(iniziale), [iniziale]);

  return useMemo(
    () => ({ criteri, ordinaPer, rimuovi, azzera, ordina }),
    [criteri, ordinaPer, rimuovi, azzera, ordina],
  );
}
