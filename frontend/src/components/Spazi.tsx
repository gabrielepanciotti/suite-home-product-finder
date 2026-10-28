import { Button, Callout, cn, PageHeader, Skeleton } from "@suite/design-system";
import { useMemo, useState } from "react";
import { useFiltriSpazi, vocabolario } from "../hooks/useFiltriSpazi";
import { useOrdineVani } from "../hooks/useOrdineVani";
import { chiaveVano, usePreferenze } from "../hooks/usePreferenze";
import { useSpazi } from "../hooks/useSpazi";
import { BarraSpazi } from "./spazi/BarraSpazi";
import { Legenda } from "./spazi/Legenda";
import { preparaRighe } from "./spazi/righe";
import { VanoBlocco } from "./spazi/VanoBlocco";
import { SectionIcon } from "./SectionIcon";

// Spazi: per ogni vano misurato, la classifica di come riempirlo — quante
// scatole entrano, in che griglia, quanta area e quanto volume occupano, quanto
// costa il lotto, com'è fatta la scatola. I vani non ancora misurati restano
// visibili come caselle aperte. Filtri e criteri d'ordine sono di pagina: si
// confrontano vani diversi con lo stesso metro.
export function Spazi() {
  const { data, loading, error, ricarica } = useSpazi();
  const {
    verdetti,
    alterna,
    azzeraVano,
    errore: erroreVerdetti,
  } = usePreferenze();
  const { filtri, patch, alternaIn, attivi, azzera } = useFiltriSpazi();
  const {
    criteri,
    ordinaPer,
    rimuovi,
    azzera: azzeraOrdine,
    ordina,
  } = useOrdineVani();
  const [foto, setFoto] = useState(true);
  const [legenda, setLegenda] = useState(false);

  const voc = useMemo(() => vocabolario(data), [data]);

  // Le righe di ogni vano si calcolano qui, una volta: servono sia alla tabella
  // sia al conteggio "n righe su m" della barra.
  const perVano = useMemo(
    () =>
      data.map((spazio) =>
        spazio.vani.map((vano) => {
          const chiave = chiaveVano(spazio.slug, vano.id);
          return {
            chiave,
            vano,
            righe: preparaRighe(vano, verdetti(chiave), filtri, ordina),
          };
        }),
      ),
    [data, verdetti, filtri, ordina],
  );

  const mostrate = perVano.flat().reduce((n, v) => n + v.righe.length, 0);
  const totali = data.reduce(
    (n, s) => n + s.vani.reduce((m, v) => m + v.soluzioni.length, 0),
    0,
  );

  return (
    <div className="mx-auto w-full max-w-screen-2xl space-y-6 text-text">
      <div>
        <PageHeader
          className={cn(
            "[&>div:first-child]:flex-col [&>div:first-child]:items-stretch",
            "sm:[&>div:first-child]:flex-row",
            "sm:[&>div:first-child]:items-start",
          )}
          icon={<SectionIcon id="spazi" />}
          title="Spazi da riempire"
          subtitle="Per ogni vano, confronta le scatole che entrano, il riempimento e il costo del lotto."
          actions={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setLegenda((v) => !v)}
            >
              {legenda ? "Nascondi legenda" : "Come si legge"}
            </Button>
          }
        />
        {legenda && <Legenda />}
        {erroreVerdetti && (
          <p className="mt-3 text-sm font-semibold text-danger">
            {erroreVerdetti}
          </p>
        )}
      </div>

      <div className="pb-16">
        {loading && (
          <div className="space-y-3" aria-label="Calcolo delle tassellazioni">
            <Skeleton className="h-28 w-full" />
            <Skeleton className="h-56 w-full" />
          </div>
        )}
        {error && (
          <Callout variant="danger" title="Impossibile calcolare gli spazi">
            <p>{error}</p>
            <Button className="mt-3" variant="secondary" onClick={ricarica}>
              Riprova
            </Button>
          </Callout>
        )}

        {!loading && !error && (
          <>
            <BarraSpazi
              filtri={filtri}
              patch={patch}
              alternaIn={alternaIn}
              attivi={attivi}
              azzera={azzera}
              vocabolario={voc}
              criteri={criteri}
              rimuoviCriterio={rimuovi}
              azzeraOrdine={azzeraOrdine}
              foto={foto}
              setFoto={setFoto}
              mostrate={mostrate}
              totali={totali}
            />

            {data.map((spazio, i) => (
              <section key={spazio.slug} className="mb-12">
                <div className="mb-3 flex flex-wrap items-baseline gap-3">
                  <h2 className="text-2xl font-bold tracking-tight">
                    {spazio.nome}
                  </h2>
                  {spazio.stanza && (
                    <span className="text-sm text-muted">
                      {spazio.stanza}
                    </span>
                  )}
                  {spazio.stato === "da-misurare" && (
                    <span className="rounded-full bg-warning/15 px-2.5 py-1 text-xs font-bold text-warning">
                      da misurare
                    </span>
                  )}
                  {spazio.fonte === "cache-home" && (
                    <span
                      className="rounded-full bg-warning/15 px-2.5 py-1 text-xs font-bold text-warning"
                      title="Il nodo Home non risponde: misure dall'ultimo snapshot"
                    >
                      Home offline · dati da snapshot
                    </span>
                  )}
                </div>
                {spazio.nota && (
                  <p className="mb-4 max-w-3xl text-sm text-muted">
                    {spazio.nota}
                  </p>
                )}

                {spazio.vani.length === 0 ? (
                  <p className="rounded-2xl border-2 border-dashed border-border px-5 py-6 text-sm text-muted">
                    Nessuna misura ancora registrata. Appena arrivano larghezza,
                    profondità e altezza (misure utili, ultimo numero = altezza)
                    si scrivono{" "}
                    {spazio.fonte === "locale" ? (
                      <>
                        in <code>vault/spazi.json</code>
                      </>
                    ) : (
                      <>nella scheda del mobile, nel vault del nodo Home</>
                    )}{" "}
                    e questa sezione si popola da sola con la stessa classifica
                    degli altri vani.
                  </p>
                ) : (
                  perVano[i].map(({ chiave, vano, righe }) => (
                    <VanoBlocco
                      key={vano.id}
                      vano={vano}
                      righe={righe}
                      criteri={criteri}
                      ordinaPer={ordinaPer}
                      alterna={(id, verdetto) => alterna(chiave, id, verdetto)}
                      azzeraVerdetti={() => azzeraVano(chiave)}
                      foto={foto}
                    />
                  ))
                )}
              </section>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
