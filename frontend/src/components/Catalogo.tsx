import { Button, Callout, PageHeader, Skeleton } from "@suite/design-system";
import { useCatalogo } from "../hooks/useCatalogo";
import { useCatalogoFiltri } from "../hooks/useCatalogoFiltri";
import { CatalogoGriglia } from "./catalogo/CatalogoGriglia";
import { CatalogoTabella } from "./catalogo/CatalogoTabella";
import { FiltriCatalogo } from "./catalogo/FiltriCatalogo";
import { SectionIcon } from "./SectionIcon";

// Catalogo: TUTTE le scatole trovate dalle CLI negozio, prima di ogni confronto
// curato. Due modalità di lettura sugli stessi dati — griglia (foto, come un
// e-commerce) e tabella (tutte le caratteristiche, colonne ordinabili).
export function Catalogo() {
  const { items, negozi, loading, error, ricarica } = useCatalogo();
  const f = useCatalogoFiltri(items);

  return (
    <div className="mx-auto w-full max-w-7xl space-y-6 text-text">
      <PageHeader
        icon={<SectionIcon id="catalogo" />}
        title="Catalogo scatole"
        subtitle="Tutte le scatole trovate dalle CLI negozio, con dimensioni, volume e costo per litro."
      />
      <div>
        {loading && (
          <div className="space-y-3" aria-label="Caricamento catalogo">
            <Skeleton className="h-28 w-full" />
            <Skeleton className="h-56 w-full" />
          </div>
        )}
        {error && (
          <Callout variant="danger" title="Impossibile caricare il catalogo">
            <p>{error}</p>
            <Button className="mt-3" variant="secondary" onClick={ricarica}>
              Riprova
            </Button>
          </Callout>
        )}

        {!loading && !error && (
          <>
            <FiltriCatalogo
              filtri={f.filtri}
              patch={f.patch}
              toggleNegozio={f.toggleNegozio}
              azzera={f.azzera}
              attivi={f.attivi}
              negozi={negozi}
              ordine={f.ordine}
              direzione={f.direzione}
              ordinaPer={f.ordinaPer}
              vista={f.vista}
              setVista={f.setVista}
              fotoInTabella={f.fotoInTabella}
              setFotoInTabella={f.setFotoInTabella}
              totale={items.length}
              mostrati={f.risultati.length}
            />

            {f.risultati.length === 0 ? (
              <p className="py-12 text-center text-muted">
                Nessuna scatola con questi filtri.
              </p>
            ) : f.vista === "griglia" ? (
              <CatalogoGriglia items={f.risultati} />
            ) : (
              <CatalogoTabella
                items={f.risultati}
                ordine={f.ordine}
                direzione={f.direzione}
                ordinaPer={f.ordinaPer}
                foto={f.fotoInTabella}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
