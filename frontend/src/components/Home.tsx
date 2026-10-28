import { useEffect } from "react";
import {
  Button,
  Callout,
  cn,
  EmptyState,
  PageHeader,
  Skeleton,
} from "@suite/design-system";
import { useAnnounce } from "../lib/announcer";
import { useConfronti } from "../hooks/useConfronti";
import { SectionIcon } from "./SectionIcon";

// La navigazione di sezione vive nella Sidebar comune: qui resta soltanto
// l'elenco dei confronti prodotto, punto di partenza del nodo.
export function Home() {
  const { data, loading, error, ricarica } = useConfronti();
  const announce = useAnnounce();

  useEffect(() => {
    if (!loading && !error) announce(`${data.length} risultati trovati`);
  }, [announce, data.length, error, loading]);

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6">
      <PageHeader
        icon={<SectionIcon id="cerca" />}
        title="Cerca"
        subtitle="Apri un confronto prodotto, scegli cosa comprare e salva la selezione nel vault."
      />

      {loading && (
        <div
          className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3"
          aria-label="Caricamento confronti"
        >
          {Array.from({ length: 6 }, (_, index) => (
            <Skeleton key={index} className="h-44 w-full rounded-2xl" />
          ))}
        </div>
      )}

      {!loading && error && (
        <Callout variant="danger" title="Impossibile caricare i confronti">
          <p>{error}</p>
          <Button className="mt-3" variant="secondary" onClick={ricarica}>
            Riprova
          </Button>
        </Callout>
      )}

      {!loading && !error && data.length === 0 && (
        <EmptyState
          icon={<SectionIcon id="cerca" />}
          title="Nessuna ricerca recente"
          description="Imposta i parametri qui sopra per interrogare le fonti disponibili"
          action={<Button onClick={ricarica}>Avvia ricerca</Button>}
        />
      )}

      {!loading && !error && data.length > 0 && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((confronto) => (
            <Button
              variant="ghost"
              key={confronto.slug}
              onClick={() => {
                window.location.hash = `risultati/${encodeURIComponent(confronto.slug)}`;
              }}
              className={cn(
                "group flex h-auto min-h-44 flex-col items-stretch justify-start",
                "whitespace-normal rounded-2xl! border-2 border-border",
                "bg-surface p-5 text-left text-text transition",
                "hover:-translate-y-0.5 hover:border-accent hover:bg-surface-2",
                "hover:shadow-card",
              )}
            >
              <h2 className="text-lg font-bold leading-tight group-hover:text-accent">
                {confronto.titolo}
              </h2>
              <p className="mt-1.5 flex-1 text-sm text-muted">
                {confronto.sottotitolo}
              </p>
              <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
                <span className="rounded-full bg-surface-2 px-2.5 py-1 font-semibold text-muted">
                  {confronto.n_prodotti} prodotti
                </span>
                {confronto.n_da_comprare > 0 && (
                  <span className="rounded-full bg-success/15 px-2.5 py-1 font-bold text-success">
                    {confronto.n_da_comprare} da comprare
                  </span>
                )}
                <span className="ml-auto font-semibold text-accent">Apri →</span>
              </div>
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
