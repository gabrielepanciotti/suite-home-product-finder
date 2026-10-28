import { Button, cn, Input, PageHeader } from "@suite/design-system";
import { useMemo, useState } from "react";
import { COLONNE, ORDINE_INIZIALE, valore } from "./contenere/colonne";
import type { CampoBox } from "./contenere/colonne";
import { ModuloOggetto } from "./contenere/ModuloOggetto";
import { TabellaBox } from "./contenere/TabellaBox";
import {
  parametri,
  useBarattoli,
  useContenere,
  useModulo,
} from "../hooks/useContenere";
import { useOrdine } from "../hooks/useOrdine";
import type { Contenitore } from "../types";
import { eur } from "./catalogo/fmt";
import { Aiuto } from "./spazi/Aiuto";
import { Chip, Gruppo } from "./spazi/ui";
import { SectionIcon } from "./SectionIcon";

/**
 * La domanda inversa degli spazi: non «cosa metto in questo vano» ma «in cosa
 * metto queste cose». Si danno le misure di un oggetto e quanti sono, e il
 * catalogo risponde con le scatole che li reggono, quante ne servono e quanto
 * costano.
 */
export function Contenere() {
  const { modulo, patch, azzera } = useModulo();
  const params = useMemo(() => parametri(modulo), [modulo]);
  const { data, loading, error } = useContenere(params);
  const barattoli = useBarattoli();

  const {
    criteri,
    ordinaPer,
    rimuovi,
    azzera: azzeraOrdine,
    ordina,
  } = useOrdine<Contenitore, CampoBox>(COLONNE, valore, ORDINE_INIZIALE);

  const [testo, setTesto] = useState("");
  const [negozi, setNegozi] = useState<string[]>([]);
  const [soloCoperchio, setSoloCoperchio] = useState(false);
  const [soloTop, setSoloTop] = useState(false);
  const [foto, setFoto] = useState(true);

  const tutte = data?.risultati ?? [];
  const listaNegozi = useMemo(
    () => [...new Set(tutte.map((r) => r.negozio))].sort(),
    [tutte],
  );

  const righe = useMemo(() => {
    const q = testo.trim().toLowerCase();
    return ordina(
      tutte.filter(
        (r) =>
          (!q || r.nome.toLowerCase().includes(q)) &&
          (negozi.length === 0 || negozi.includes(r.negozio)) &&
          (!soloCoperchio || r.coperchio === true) &&
          (!soloTop || r.ottimale),
      ),
    );
  }, [tutte, testo, negozi, soloCoperchio, soloTop, ordina]);

  const alterna = (n: string) =>
    setNegozi((v) => (v.includes(n) ? v.filter((x) => x !== n) : [...v, n]));

  return (
    <div className="mx-auto w-full max-w-screen-2xl space-y-6 text-text">
      <PageHeader
        icon={<SectionIcon id="contenere" />}
        title="In cosa lo metto"
        subtitle="Inserisci misure e quantità: il catalogo trova le scatole adatte, quante ne servono e il costo del lotto."
      />

      <div className="pb-16">
        <ModuloOggetto
          modulo={modulo}
          patch={patch}
          azzera={azzera}
          materialiCatalogo={data?.materiali_catalogo ?? []}
          barattoli={barattoli}
        />

        {params == null ? (
          <p className="rounded-2xl border-2 border-dashed border-border px-5 py-6 text-sm text-muted">
            Mancano le misure. Servono{" "}
            {modulo.forma === "tondo"
              ? "diametro e altezza"
              : "larghezza, profondità e altezza"}{" "}
            dell'oggetto, e quanti ne devi conservare.
          </p>
        ) : error ? (
          <p className="py-8 text-danger">Errore: {error}</p>
        ) : data == null ? (
          <p className="py-8 text-muted">Cerco fra le scatole…</p>
        ) : data.risultati.length === 0 ? (
          <p className="rounded-2xl border-2 border-dashed border-warning/50 px-5 py-6 text-sm text-muted">
            Nessuna delle {data.n_catalogo} scatole del catalogo contiene un
            oggetto di {data.oggetto.a}×{data.oggetto.b}×h{data.oggetto.h} cm
            con questi vincoli. Da provare: allargare il filtro sui materiali,
            abbassare il margine pareti, permettere di coricarlo, o cercare la
            scatola nei negozi con una nuova ricerca (
            <code>scripts/shopcli.py</code>).
          </p>
        ) : (
          <>
            <Verdetto righe={data.risultati} n={data.n} />

            <div
              className={cn(
                "mb-4 mt-5 flex flex-wrap items-center gap-x-5 gap-y-3",
                "rounded-2xl border border-border bg-surface px-4 py-3",
              )}
            >
              <Input
                value={testo}
                onChange={(e) => setTesto(e.target.value)}
                placeholder="cerca nel nome…"
                className={cn(
                  "w-52 rounded-lg border border-border bg-bg px-3 py-1.5",
                  "text-sm outline-none transition focus:border-info",
                )}
              />
              <span className="text-xs text-muted">
                {righe.length} su {data.n_valide} scatole buone
                {loading && " · aggiorno…"}
              </span>

              {/* Il materiale si deduce dal nome, e molti nomi tacciono: se il
                  filtro è acceso, la pagina deve dire quante ne sta tenendo
                  per beneficio del dubbio, invece di spacciarle per plastica. */}
              {modulo.materiali.length > 0 && data.n_ignoti > 0 && (
                <Aiuto testo="Il materiale si ricava dal nome del prodotto: queste scatole non lo dichiarano, quindi restano nell'elenco — non sapere non vuol dire materiale sbagliato. Il chip «anche materiale ignoto» le toglie.">
                  <span className="rounded-md bg-warning/15 px-2 py-0.5 text-xs font-semibold text-warning">
                    {data.n_ignoti} di materiale ignoto
                  </span>
                </Aiuto>
              )}

              <Gruppo label="Vedi">
                <Chip
                  attivo={soloTop}
                  onClick={() => setSoloTop((v) => !v)}
                  tono="success"
                  aiuto={COLONNE.ottimale.aiuto}
                >
                  solo top
                </Chip>
                <Chip
                  attivo={soloCoperchio}
                  onClick={() => setSoloCoperchio((v) => !v)}
                  aiuto="Solo le scatole il cui nome dichiara un coperchio. Le altre non sono senza: di quelle non lo sappiamo."
                >
                  con coperchio
                </Chip>
                <Chip attivo={foto} onClick={() => setFoto((v) => !v)}>
                  foto
                </Chip>
              </Gruppo>

              {listaNegozi.length > 1 && (
                <Gruppo label="Negozio">
                  {listaNegozi.map((n) => (
                    <Chip
                      key={n}
                      attivo={negozi.includes(n)}
                      onClick={() => alterna(n)}
                    >
                      {n}
                    </Chip>
                  ))}
                </Gruppo>
              )}

              <div className="ml-auto flex flex-wrap items-center gap-1.5">
                <span className="text-2xs font-bold uppercase tracking-wider text-muted">
                  Ordine
                </span>
                {criteri.map((c, i) => (
                  <Button
                    variant="secondary"
                    size="sm"
                    key={c.campo}
                    onClick={() => rimuovi(c.campo)}
                    title="togli questo criterio"
                  >
                    {i + 1}. {COLONNE[c.campo].label}{" "}
                    {c.dir === "asc" ? "↑" : "↓"} ✕
                  </Button>
                ))}
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={azzeraOrdine}
                >
                  ripristina
                </Button>
              </div>
            </div>

            {righe.length === 0 ? (
              <p className="rounded-2xl border-2 border-dashed border-border px-5 py-6 text-sm text-muted">
                Con i filtri attivi non resta nessuna scatola (ce ne sarebbero{" "}
                {data.n_valide}).
              </p>
            ) : (
              <TabellaBox
                righe={righe}
                n={data.n}
                criteri={criteri}
                ordinaPer={ordinaPer}
                foto={foto}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}

/**
 * Le due risposte che si cercano davvero, prima della tabella: la più
 * economica e quella che spreca meno spazio. Spesso non sono la stessa, ed è
 * esattamente quello che vale la pena vedere subito.
 */
function Verdetto({ righe, n }: { righe: Contenitore[]; n: number }) {
  const economica = righe.reduce((a, b) => (b.costo < a.costo ? b : a));
  const compatta = righe.reduce((a, b) =>
    b.riempimento_pct > a.riempimento_pct ? b : a,
  );
  const stessa = economica.id === compatta.id;

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <Scheda
        titolo={stessa ? "La scelta" : "Costa meno"}
        r={economica}
        n={n}
        accento="success"
      />
      {!stessa && (
        <Scheda titolo="Spreca meno spazio" r={compatta} n={n} accento="info" />
      )}
    </div>
  );
}

function Scheda({
  titolo,
  r,
  n,
  accento,
}: {
  titolo: string;
  r: Contenitore;
  n: number;
  accento: "success" | "info";
}) {
  const bordo = accento === "success" ? "border-success/50" : "border-info/50";
  const testo = accento === "success" ? "text-success" : "text-info";

  return (
    <div className={`rounded-2xl border-2 ${bordo} bg-surface p-4`}>
      <div
        className={`text-2xs font-bold uppercase tracking-wider ${testo}`}
      >
        {titolo}
      </div>
      <div className="mt-1 flex items-start gap-3">
        {r.img && (
          <img
            src={r.img}
            alt=""
            loading="lazy"
            className="h-12 w-12 shrink-0 rounded-lg object-contain"
          />
        )}
        <div>
          <div className="text-md font-bold leading-tight">{r.nome}</div>
          <p className="mt-1 text-sm text-muted">
            <strong className="text-text">{r.scatole}</strong>{" "}
            {r.scatole === 1 ? "scatola" : "scatole"} da {r.per_scatola} posti
            per {n} oggetti ={" "}
            <strong className="text-text">{eur(r.costo)} €</strong> ·{" "}
            <Aiuto testo="Quanta parte dello spazio utile di una scatola piena è occupata dagli oggetti. Il resto è aria.">
              {r.riempimento_pct.toFixed(0)}% sfruttata
            </Aiuto>
            {r.avanzo > 0 && ` · ${r.avanzo} posti liberi`}
          </p>
        </div>
      </div>
    </div>
  );
}
