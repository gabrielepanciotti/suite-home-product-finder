// Modello dati riusabile (specchia i JSON in vault/confronti/). La struttura è fissa:
// per ogni prodotto cambiano solo immagine, specs e valori — non il codice.

export interface Spec {
  label: string;
  value: string;
}

export interface Prodotto {
  id: string;
  nome: string;
  negozio: string;
  immagine: string | null;
  link: string | null;
  prezzo: number;
  valore: number | null;
  valore_label: string;
  nota: string;
  consigliato: boolean;
  stato: string | null; // "da-comprare" | null
  quantita: number;
  specs: Spec[];
}

export interface Gruppo {
  nome: string;
  prodotti: Prodotto[];
}

export type Selezione = "per-gruppo" | "multipla";

export interface Confronto {
  slug: string;
  titolo: string;
  sottotitolo: string;
  metrica: string;
  selezione: Selezione;
  gruppi: Gruppo[];
}

// ---- Scheda nodo (GET /api/overview) -------------------------------------

export interface OverviewFunction {
  key: string;
  label: string;
  agent?: string;
  command?: string;
  companions?: string[];
}

export interface OverviewIntegration {
  name: string;
  kind?: string;
  detail?: string;
}

export interface OverviewCollaborations {
  parent?: { slug?: string; name?: string } | null;
  children?: { slug?: string; name?: string }[];
  integrations?: OverviewIntegration[];
}

export interface OverviewDatabase {
  tables: { name: string; rows: number }[];
  highlights: { label: string; value: number }[];
  error?: string;
}

export interface OverviewBrain {
  total?: number;
  content?: number;
  hubs?: number;
  links?: number;
  components?: number;
  per_area?: [string, number][];
}

export interface NodeOverviewData {
  identity: {
    slug: string;
    name: string;
    type?: string;
    cluster?: string[];
    hostBase?: string;
    ports?: { backend?: number; frontend?: number; db?: number };
  };
  functions?: OverviewFunction[];
  collaborations?: OverviewCollaborations | null;
  database: OverviewDatabase;
  brain?: OverviewBrain | null;
  live: boolean;
  warning?: string;
  generated_at?: string;
}

// ---- Catalogo scatole (GET /api/catalogo) --------------------------------
// Specchia vault/confronti/_scrape/: il catalogo grezzo di tutte le scatole
// trovate dalle CLI negozio, prima di qualsiasi confronto curato.

// Caratteristiche lette dal nome commerciale (backend `attributi.py`). Il
// coperchio è `null` quando il nome non lo dice: ignoto, non "senza".
export interface Caratteristiche {
  coperchio?: boolean | null;
  materiali?: string[];
  tratti?: string[];
}

export interface CatalogoItem extends Caratteristiche {
  id: string;
  nome: string;
  negozio: string;
  prezzo: number;
  a: number;
  b: number;
  h: number;
  volume_l: number;
  eur_per_l: number | null;
  link: string | null;
  img: string | null;
  fonti: string[];
  // Le categorie larghe delle CLI pescano anche non-scatole (stura lavandini,
  // appendiabiti): la classe dice cosa tenere, e perché è stato deciso così.
  classe: "scatola" | "non-scatola" | "da-classificare";
  classe_perche: string;
}

export interface CatalogoResponse {
  items: CatalogoItem[];
  negozi: { negozio: string; n: number }[];
}

// ---- Spazi da riempire (GET /api/spazi) ----------------------------------
// Specchia vault/spazi.json + la tassellazione calcolata dal backend: per ogni
// vano misurato, quante scatole entrano, come sono disposte, quanto riempiono.

export interface Soluzione extends Caratteristiche {
  // "nome|LxPxH": il nome da solo non identifica niente — Action vende sette
  // contenitori diversi tutti chiamati "Contenitore Heidrun".
  id: string;
  nome: string;
  negozio: string;
  prezzo: number;
  dim: string;
  a: number;
  b: number;
  h: number;
  nx: number;
  ny: number;
  livelli: number;
  pezzi: number;
  costo: number;
  area_pct: number;
  vol_pct: number;
  litri: number;
  eur_per_l: number;
  ottimale: boolean;
  link: string | null;
  img: string | null;
  // Solo per gli scaffali a ripiani regolabili: a che passo fissarli.
  passo_cm?: number;
}

export interface Vano {
  id: string;
  nome: string;
  nominale?: string | null;
  utile?: string | null;
  // L/P noti ma H nulla = pianta misurata, altezza no (scaffale a ripiani
  // regolabili): il vano si mostra, ma non si classifica.
  L: number | null;
  P: number | null;
  H: number | null;
  misurato?: boolean;
  // Scaffale: i ripiani si fissano dove si vuole sul montante, quindi
  // l'altezza per livello e' un risultato (il passo), non un vincolo.
  regolabile?: boolean;
  montante?: number | null;
  ripiani?: number | null;
  tipo?: string | null;
  accesso?: string | null;
  note?: string | null;
  n_soluzioni: number;
  soluzioni: Soluzione[];
}

export interface Spazio {
  slug: string;
  nome: string;
  stanza?: string | null;
  stato: "misurato" | "da-misurare";
  nota?: string | null;
  // Da dove arriva: l'API del nodo Home, il suo snapshot, o questo nodo.
  fonte?: "home" | "cache-home" | "locale";
  vani: Vano[];
}

// ---- Contenere oggetti (GET /api/contenere) ------------------------------
// La domanda inversa degli spazi: lì il contenitore è dato e il catalogo lo
// riempie, qui il contenuto è dato e il catalogo deve contenerlo.

export interface Contenitore extends Caratteristiche {
  // "nome|LxPxH", come nelle soluzioni: il nome da solo non identifica niente.
  id: string;
  nome: string;
  negozio: string;
  prezzo: number;
  a: number;
  b: number;
  h: number;
  dim: string;
  // Come si dispongono gli oggetti DENTRO una scatola.
  nx: number;
  ny: number;
  livelli: number;
  in_piedi: boolean;
  per_scatola: number;
  // Quante scatole servono per la quantità chiesta, e cosa comporta.
  scatole: number;
  capienza: number;
  avanzo: number;
  costo: number;
  costo_per_oggetto: number;
  // Quanto dello spazio utile di una scatola piena è davvero occupato.
  riempimento_pct: number;
  litri: number;
  eur_per_l: number | null;
  ottimale: boolean;
  link: string | null;
  img: string | null;
  classe?: string;
}

export interface RispostaContenere {
  oggetto: { a: number; b: number; h: number; volume_l: number };
  n: number;
  opzioni: {
    in_piedi: boolean;
    impilabili: boolean;
    margine: number;
    max_scatole: number | null;
    materiali: string[];
    escludi: string[];
    ignoti: boolean;
  };
  n_valide: number;
  n_catalogo: number;
  // Quante fra le scatole valide non dichiarano di che materiale sono: il
  // filtro le tiene, quindi la pagina deve poterlo ammettere.
  n_ignoti: number;
  // Il vocabolario dei materiali sta nel vault, non nel frontend: qui arriva
  // ciò che il catalogo dichiara davvero, con quante scatole per materiale.
  materiali_catalogo: { nome: string; n: number }[];
  risultati: Contenitore[];
}

// ---- Barattoli noti (GET /api/barattoli) ---------------------------------
// Preselezione del modulo "In cosa lo metto": si sceglie il barattolo per nome
// invece di digitarne le misure, perché è lì che si sbaglia — fra due Bormioli
// alti uguale il diametro va da 10,6 a 16,0 cm.

export interface Barattolo {
  id: string;
  marca: string;
  linea: string | null;
  nome: string;
  /** Come appare sul chip: "Fido · Vaso ermetico 150 cl". */
  etichetta: string;
  altezza_cm: number;
  diametro_cm: number;
  capacita_cl: number | null;
  url: string | null;
  /** Valorizzato solo quando il produttore dichiara misure discordi. */
  conflitto: string | null;
}

export interface RispostaBarattoli {
  marche: { marca: string; barattoli: Barattolo[] }[];
  n: number;
}

// Verdetti per vano (GET/PUT /api/preferenze): quali scatole tenere in cima e
// quali sono state scartate. Chiave = "<slug spazio>/<id vano>".
export interface VerdettiVano {
  preferiti: string[];
  scartati: string[];
}

export interface Preferenze {
  vani: Record<string, VerdettiVano>;
}

export interface ConfrontoSummary {
  slug: string;
  titolo: string;
  sottotitolo: string;
  metrica: string;
  n_prodotti: number;
  n_da_comprare: number;
}

export interface Acquisto {
  confronto: string;
  slug: string;
  gruppo: string;
  nome: string;
  negozio: string;
  prezzo: number;
  quantita: number;
  link: string | null;
  immagine: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}
