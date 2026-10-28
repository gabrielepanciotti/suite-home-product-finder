import type { Colonna, Criterio } from "../../hooks/useOrdine";
import type { Contenitore } from "../../types";

/** I campi su cui si può ordinare la classifica dei contenitori. */
export type CampoBox =
  | "ottimale"
  | "nome"
  | "negozio"
  | "coperchio"
  | "h"
  | "per_scatola"
  | "scatole"
  | "avanzo"
  | "riempimento_pct"
  | "prezzo"
  | "costo"
  | "costo_per_oggetto";

export type CriterioBox = Criterio<CampoBox>;

/** Ordine di partenza: la spesa totale, che è la domanda vera. */
export const ORDINE_INIZIALE: CriterioBox[] = [
  { campo: "costo", dir: "asc" },
  { campo: "scatole", dir: "asc" },
];

export const COLONNE: Record<CampoBox, Colonna> = {
  ottimale: {
    label: "top",
    aiuto:
      "Scelta non dominata: nessun'altra scatola costa meno, ne serve meno numero e sfrutta meglio lo spazio dentro, tutte e tre le cose insieme. Non è «la migliore» in assoluto — è una di quelle fra cui vale la pena scegliere.",
    allinea: "centro",
    naturale: "desc",
  },
  nome: {
    label: "Scatola",
    aiuto:
      "Nome del prodotto sul sito del negozio, con le sue caratteristiche.",
    allinea: "sx",
    naturale: "asc",
  },
  negozio: {
    label: "Negozio",
    aiuto: "Da dove arriva il prezzo (catalogo scaricato dalle CLI negozio).",
    allinea: "sx",
    naturale: "asc",
  },
  coperchio: {
    label: "Cop.",
    aiuto:
      "Coperchio: ✓ sì, ✗ no, ? non dichiarato dal nome del prodotto. Ricavato dal nome, non da una scheda tecnica: «?» vuol dire che non lo sappiamo, non che manca.",
    allinea: "centro",
    naturale: "desc",
  },
  h: {
    label: "L×P×h cm",
    aiuto:
      "Le tre misure ESTERNE della scatola, sempre nello stesso ordine: larghezza × profondità × altezza (l'ultimo numero, quello con la h, è l'altezza). Lo spazio dentro è meno: il margine impostato sopra viene tolto da ogni lato prima del calcolo. Si ordina per altezza.",
    allinea: "dx",
    naturale: "asc",
  },
  per_scatola: {
    label: "Per scatola",
    aiuto:
      "Quanti oggetti entrano in UNA scatola: quanti in larghezza × quanti in profondità × quanti livelli sovrapposti. La colonna «Come stanno» accanto mostra la griglia.",
    allinea: "dx",
    naturale: "desc",
  },
  scatole: {
    label: "Scatole",
    aiuto:
      "Quante scatole comprare per stare dietro alla quantità chiesta. È un numero intero arrotondato per eccesso: se ne restano tre fuori, serve comunque una scatola in più.",
    allinea: "dx",
    naturale: "asc",
  },
  avanzo: {
    label: "Avanzo",
    aiuto:
      "Posti liberi che restano dopo aver messo dentro tutti gli oggetti. Zero = incastro perfetto; un avanzo alto è margine per il futuro, ma anche spazio pagato e non usato.",
    allinea: "dx",
    naturale: "asc",
  },
  riempimento_pct: {
    label: "Sfruttata",
    aiuto:
      "Quanta parte dello spazio utile di una scatola PIENA è davvero occupata dagli oggetti. Il resto è aria: gli spicchi fra un barattolo tondo e l'altro, e l'altezza che avanza sopra. Si misura su una scatola piena, non sul lotto: l'ultima mezza vuota dipende dalla quantità, non dalla scatola.",
    allinea: "sx",
    naturale: "desc",
  },
  prezzo: {
    label: "€/pz",
    aiuto: "Prezzo di una singola scatola.",
    allinea: "dx",
    naturale: "asc",
  },
  costo: {
    label: "Totale",
    aiuto:
      "Quanto costa la soluzione intera: prezzo della scatola × quante ne servono. È il numero da confrontare fra righe.",
    allinea: "dx",
    naturale: "asc",
  },
  costo_per_oggetto: {
    label: "€/oggetto",
    aiuto:
      "Quanto costa mettere via un singolo oggetto: spesa totale diviso la quantità. Rende confrontabili soluzioni con scatole di taglia molto diversa.",
    allinea: "dx",
    naturale: "asc",
  },
};

/** Valore confrontabile di un campo: tutto diventa numero o stringa. */
export function valore(r: Contenitore, campo: CampoBox): number | string {
  switch (campo) {
    case "nome":
      return r.nome;
    case "negozio":
      return r.negozio;
    // Ignoto in mezzo: in cima i sì, in fondo i no dichiarati, e i «non si sa»
    // restano nel mezzo, dove meritano di stare.
    case "coperchio":
      return r.coperchio == null ? 1 : r.coperchio ? 2 : 0;
    case "ottimale":
      return r.ottimale ? 1 : 0;
    default:
      return r[campo];
  }
}
