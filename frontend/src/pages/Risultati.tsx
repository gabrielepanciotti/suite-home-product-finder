import { Button, EmptyState, PageHeader } from "@suite/design-system";
import { ConfrontoView } from "../components/ConfrontoView";
import { SectionIcon } from "../components/SectionIcon";

export function Risultati({ slug }: { slug?: string }) {
  if (slug) return <ConfrontoView slug={slug} />;

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6">
      <PageHeader
        icon={<SectionIcon id="risultati" />}
        title="Risultati"
        subtitle="Confronta prodotti, prezzi e caratteristiche della ricerca aperta."
      />
      <EmptyState
        icon={<SectionIcon id="risultati" />}
        title="Nessun risultato trovato"
        description="Allarga l'intervallo di prezzo o modifica le date"
        action={
          <Button onClick={() => { window.location.hash = "cerca"; }}>
            Modifica criteri
          </Button>
        }
      />
    </div>
  );
}
