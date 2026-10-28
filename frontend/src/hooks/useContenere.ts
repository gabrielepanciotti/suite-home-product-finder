import { useEffect, useMemo, useRef, useState } from "react";
import type { ParamsContenere } from "../lib/api";
import { api } from "../lib/api";
import type { Barattolo, RispostaBarattoli, RispostaContenere } from "../types";

/** Lo stato del modulo è testo, non numeri: "22,5" è un'altezza legittima. */
export interface Modulo {
  forma: "squadrato" | "tondo";
  larghezza: string;
  profondita: string;
  diametro: string;
  altezza: string;
  quantita: string;
  in_piedi: boolean;
  impilabili: boolean;
  margine: string;
  max_scatole: string;
  /** Materiali richiesti (vuoto = qualunque) e materiali rifiutati. */
  materiali: string[];
  escludi: string[];
  /** Se tenere le scatole che non dichiarano di che materiale sono. */
  ignoti: boolean;
  /**
   * Il barattolo scelto dalla preselezione, o "" se le misure sono a mano.
   * Si conserva l'id, non solo le misure: serve a tenere acceso il chip giusto
   * e a spegnerlo appena qualcuno ritocca una misura a mano.
   */
  preset: string;
}

export const MODULO_INIZIALE: Modulo = {
  forma: "tondo",
  larghezza: "",
  profondita: "",
  diametro: "",
  altezza: "",
  quantita: "12",
  // I due divieti sono accesi di default perché il caso da cui nasce questa
  // pagina sono i barattoli: coricati si svuotano, impilati non stanno su.
  in_piedi: true,
  impilabili: false,
  margine: "1",
  max_scatole: "",
  materiali: [],
  // Il cartone parte escluso: è la roba più economica del catalogo, quindi
  // vince sempre l'asse del costo e riempiva la classifica di scatoloni da
  // trasloco. Non è una scelta nascosta — il chip resta acceso e visibile, e
  // basta un clic per rimetterlo dentro.
  escludi: ["cartone"],
  ignoti: true,
  preset: "",
};

const CHIAVE = "hpf.contenere.modulo";

function numero(s: string): number | null {
  const v = parseFloat(s.replace(",", "."));
  return Number.isFinite(v) && v > 0 ? v : null;
}

/** I parametri da mandare al backend, o null finché le misure non ci sono. */
export function parametri(m: Modulo): ParamsContenere | null {
  const h = numero(m.altezza);
  const n = numero(m.quantita);
  const margine = parseFloat(m.margine.replace(",", "."));
  // Un oggetto tondo occupa comunque il quadrato che lo contiene: due barattoli
  // vicini lasciano gli spicchi vuoti, e quello spazio non è riutilizzabile.
  const [a, b] =
    m.forma === "tondo"
      ? [numero(m.diametro), numero(m.diametro)]
      : [numero(m.larghezza), numero(m.profondita)];
  if (a == null || b == null || h == null || n == null) return null;

  return {
    a,
    b,
    h,
    n: Math.round(n),
    in_piedi: m.in_piedi,
    impilabili: m.impilabili,
    margine: Number.isFinite(margine) && margine >= 0 ? margine : 0,
    max_scatole: numero(m.max_scatole),
    // Ordinati: la chiave di cache della ricerca è il JSON dei parametri, e due
    // insiemi uguali in ordine diverso non devono valere come due ricerche.
    materiali: [...m.materiali].sort(),
    escludi: [...m.escludi].sort(),
    ignoti: m.ignoti,
  };
}

/** Modulo persistente: riaprendo la pagina l'oggetto è ancora quello di prima. */
export function useModulo() {
  const [modulo, setModulo] = useState<Modulo>(() => {
    try {
      const salvato = localStorage.getItem(CHIAVE);
      return salvato
        ? { ...MODULO_INIZIALE, ...JSON.parse(salvato) }
        : MODULO_INIZIALE;
    } catch {
      return MODULO_INIZIALE;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(CHIAVE, JSON.stringify(modulo));
    } catch {
      // localStorage pieno o negato: il modulo funziona lo stesso, non si ricorda.
    }
  }, [modulo]);

  // Ritoccare una misura a mano scollega la preselezione: il chip resterebbe
  // acceso su un barattolo che non è più quello descritto dai campi.
  const MISURE = [
    "forma",
    "larghezza",
    "profondita",
    "diametro",
    "altezza",
  ] as const;
  const patch = (p: Partial<Modulo>) =>
    setModulo((m) => {
      const aMano = MISURE.some((k) => k in p) && !("preset" in p);
      return { ...m, ...p, ...(aMano ? { preset: "" } : {}) };
    });

  return { modulo, patch, azzera: () => setModulo(MODULO_INIZIALE) };
}

/** L'elenco dei barattoli noti. Non cambia durante la sessione: si carica una volta. */
export function useBarattoli() {
  const [data, setData] = useState<RispostaBarattoli | null>(null);

  useEffect(() => {
    let vivo = true;
    api
      .getBarattoli()
      .then((r) => vivo && setData(r))
      // La preselezione è una comodità: se non arriva, il modulo a mano basta.
      .catch(() => vivo && setData(null));
    return () => {
      vivo = false;
    };
  }, []);

  return data;
}

/** Le misure del barattolo scelto, pronte per il modulo. */
export function daBarattolo(b: Barattolo): Partial<Modulo> {
  return {
    preset: b.id,
    // Un barattolo è tondo: basta il diametro, e il calcolo userà comunque il
    // quadrato che lo contiene (gli spicchi fra due barattoli sono persi).
    forma: "tondo",
    diametro: String(b.diametro_cm).replace(".", ","),
    altezza: String(b.altezza_cm).replace(".", ","),
  };
}

/**
 * La ricerca vera e propria.
 *
 * Attesa di 300 ms prima di chiamare: le misure si digitano una cifra alla
 * volta, e "2" seguito da "22" farebbe partire due ricerche di cui la prima
 * inutile. I risultati precedenti restano a schermo mentre arriva la risposta
 * nuova, così la tabella non sfarfalla a ogni tasto.
 */
export function useContenere(params: ParamsContenere | null) {
  const [data, setData] = useState<RispostaContenere | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chiave = useMemo(
    () => (params ? JSON.stringify(params) : null),
    [params],
  );
  const ultima = useRef(0);

  useEffect(() => {
    if (chiave == null) {
      setData(null);
      setError(null);
      return;
    }
    const richiesta = ++ultima.current;
    setLoading(true);
    const t = setTimeout(() => {
      api
        .cercaContenitori(JSON.parse(chiave) as ParamsContenere)
        .then((r) => {
          // Una risposta lenta di una ricerca vecchia non deve sovrascrivere
          // quella nuova già arrivata.
          if (richiesta !== ultima.current) return;
          setData(r);
          setError(null);
        })
        .catch((e: Error) => {
          if (richiesta === ultima.current) setError(e.message);
        })
        .finally(() => {
          if (richiesta === ultima.current) setLoading(false);
        });
    }, 300);
    return () => clearTimeout(t);
  }, [chiave]);

  return { data, loading, error };
}
