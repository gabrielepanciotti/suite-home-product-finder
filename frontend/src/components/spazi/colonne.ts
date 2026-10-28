import type { Colonna } from "../../hooks/useOrdine";
import type { Soluzione } from "../../types";

/** I campi su cui si può ordinare la classifica di un vano. */
export type CampoVano =
  | "nome"
  | "negozio"
  | "h"
  | "passo_cm"
  | "pezzi"
  | "area_pct"
  | "vol_pct"
  | "litri"
  | "prezzo"
  | "costo"
  | "eur_per_l"
  | "coperchio"
  | "materiale"
  | "ottimale";

export const COLONNE: Record<CampoVano, Colonna> = {
  ottimale: {
    label: "top",
    aiuto:
      "Soluzione non dominata: nessun'altra scatola di questa classifica riempie di più, costa meno e usa meno pezzi tutte e tre le cose insieme. Non è «la migliore» in assoluto — è una di quelle fra cui vale la pena scegliere.",
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
  materiale: {
    label: "Materiale",
    aiuto: "Materiali citati nel nome del prodotto. Vuoto = non dichiarato.",
    allinea: "sx",
    naturale: "asc",
  },
  h: {
    label: "L×P×h cm",
    aiuto:
      "Le tre misure ESTERNE della scatola, sempre nello stesso ordine: larghezza × profondità × altezza (l'ultimo numero, quello con la h, è l'altezza). Per i barattoli Bormioli alti 22 serve h ≥ 23. Si ordina per altezza.",
    allinea: "dx",
    naturale: "desc",
  },
  passo_cm: {
    label: "Passo",
    aiuto:
      "Solo per gli scaffali a ripiani regolabili: a che distanza fissare un ripiano dall'altro per far stare questa scatola. Altezza della scatola + 3 cm fra spessore del ripiano e gioco per infilarla.",
    allinea: "dx",
    naturale: "asc",
  },
  pezzi: {
    label: "Pz",
    aiuto:
      "Quante scatole entrano in tutto nel vano: colonne × righe × livelli. È il numero da comprare.",
    allinea: "dx",
    naturale: "desc",
  },
  area_pct: {
    label: "Area",
    aiuto:
      "Quanta parte del PAVIMENTO del vano è coperta dalle scatole. 100% = niente corridoi sprecati fra una scatola e l'altra.",
    allinea: "dx",
    naturale: "desc",
  },
  vol_pct: {
    label: "Volume riempito",
    aiuto:
      "Quanta parte dello SPAZIO del vano è occupata. Tiene conto anche dell'altezza: scatole basse che coprono tutto il pavimento fanno area 100% ma volume molto meno, perché sopra resta aria.",
    allinea: "sx",
    naturale: "desc",
  },
  litri: {
    label: "Litri",
    aiuto:
      "Capienza totale di tutte le scatole insieme, in litri (misura esterna: quella interna è un po' meno).",
    allinea: "dx",
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
    aiuto: "Quanto costa riempire il vano: prezzo × numero di pezzi.",
    allinea: "dx",
    naturale: "asc",
  },
  eur_per_l: {
    label: "€/L",
    aiuto:
      "Euro per litro di capienza: quanto si paga lo spazio. È la misura di convenienza vera, indipendente dalla taglia della scatola.",
    allinea: "dx",
    naturale: "asc",
  },
};

/** Valore confrontabile di un campo: tutto diventa numero o stringa. */
export function valore(s: Soluzione, campo: CampoVano): number | string {
  switch (campo) {
    case "nome":
      return s.nome;
    case "negozio":
      return s.negozio;
    case "materiale":
      return (s.materiali ?? []).join(" ");
    // Ignoto in mezzo: ordinando per coperchio in cima vanno i sì, in fondo i
    // no dichiarati, e i «non si sa» restano nel mezzo dove meritano di stare.
    case "coperchio":
      return s.coperchio == null ? 1 : s.coperchio ? 2 : 0;
    case "ottimale":
      return s.ottimale ? 1 : 0;
    case "passo_cm":
      return s.passo_cm ?? Number.POSITIVE_INFINITY;
    default:
      return s[campo];
  }
}
