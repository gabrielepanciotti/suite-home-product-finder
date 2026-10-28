import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import type { Preferenze, VerdettiVano } from "../types";

const VUOTO: VerdettiVano = { preferiti: [], scartati: [] };

export type Verdetto = "preferiti" | "scartati";

/** Chiave stabile di un vano dentro le preferenze del vault. */
export function chiaveVano(spazio: string, vano: string): string {
  return `${spazio}/${vano}`;
}

/**
 * Preferiti e scartati per vano, persistiti nel vault via API.
 *
 * L'aggiornamento è ottimistico: cliccare una stella deve spostare la riga
 * subito: il salvataggio è una conseguenza, non un'attesa. Se il PUT fallisce
 * si mostra l'errore e si tiene lo stato del server come verità.
 */
export function usePreferenze() {
  const [preferenze, setPreferenze] = useState<Preferenze>({ vani: {} });
  const [errore, setErrore] = useState<string | null>(null);

  useEffect(() => {
    let vivo = true;
    api
      .getPreferenze()
      .then((p) => vivo && setPreferenze(p))
      .catch(() => vivo && setErrore("preferenze non caricate"));
    return () => {
      vivo = false;
    };
  }, []);

  const verdetti = useCallback(
    (chiave: string): VerdettiVano => preferenze.vani[chiave] ?? VUOTO,
    [preferenze],
  );

  const alterna = useCallback(
    (chiave: string, nome: string, verdetto: Verdetto) => {
      const attuali = preferenze.vani[chiave] ?? VUOTO;
      const acceso = attuali[verdetto].includes(nome);
      const elenco = acceso
        ? attuali[verdetto].filter((n) => n !== nome)
        : [...attuali[verdetto], nome];
      // Preferito e scartato sono opposti: accendere l'uno spegne l'altro,
      // altrimenti una scatola finirebbe insieme in cima e in fondo.
      const opposto =
        verdetto === "preferiti" ? "scartati" : ("preferiti" as Verdetto);
      const altri = attuali[opposto].filter((n) => n !== nome);

      const nuovi: VerdettiVano =
        verdetto === "preferiti"
          ? { preferiti: elenco, scartati: altri }
          : { preferiti: altri, scartati: elenco };

      setPreferenze((p) => ({ vani: { ...p.vani, [chiave]: nuovi } }));
      setErrore(null);
      api
        .salvaPreferenze(chiave, nuovi.preferiti, nuovi.scartati)
        .then(setPreferenze)
        .catch(() => setErrore("verdetto non salvato nel vault"));
    },
    [preferenze],
  );

  const azzeraVano = useCallback((chiave: string) => {
    setPreferenze((p) => ({ vani: { ...p.vani, [chiave]: VUOTO } }));
    api
      .salvaPreferenze(chiave, [], [])
      .then(setPreferenze)
      .catch(() => {});
  }, []);

  return { verdetti, alterna, azzeraVano, errore };
}
