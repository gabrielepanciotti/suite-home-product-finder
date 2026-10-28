import {
  Button,
  Callout,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  DataOra,
  EmptyState,
  PageHeader,
  Skeleton,
} from "@suite/design-system";
import { useAcquisti } from "../hooks/useAcquisti";
import { SectionIcon } from "../components/SectionIcon";

const euro = new Intl.NumberFormat("it-IT", {
  style: "currency",
  currency: "EUR",
});

export function Salvati() {
  const { data, loading, error, ricarica } = useAcquisti();

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6">
      <PageHeader
        icon={<SectionIcon id="salvati" />}
        title="Salvati"
        subtitle="Le scelte da comprare registrate nei confronti prodotto."
      />

      {loading && (
        <div className="space-y-3" aria-label="Caricamento elementi salvati">
          {Array.from({ length: 4 }, (_, index) => (
            <Skeleton key={index} className="h-28 w-full" />
          ))}
        </div>
      )}

      {!loading && error && (
        <Callout variant="danger" title="Impossibile caricare gli elementi salvati">
          <p>{error}</p>
          <Button className="mt-3" variant="secondary" onClick={ricarica}>
            Riprova
          </Button>
        </Callout>
      )}

      {!loading && !error && data.length === 0 && (
        <EmptyState
          icon={<SectionIcon id="salvati" />}
          title="Nessun elemento salvato"
          description="Salva i risultati migliori durante una ricerca per ritrovarli qui"
          action={
            <Button onClick={() => { window.location.hash = "cerca"; }}>
              Nuova ricerca
            </Button>
          }
        />
      )}

      {!loading && !error && data.length > 0 && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {data.map((item) => (
            <Card key={`${item.slug}-${item.gruppo}-${item.nome}`}>
              <CardHeader>
                <CardTitle>{item.nome}</CardTitle>
                <p className="text-sm text-muted">
                  {item.negozio} · {item.confronto}
                </p>
              </CardHeader>
              <CardBody className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <p className="font-semibold text-text">
                    {item.quantita} × {euro.format(item.prezzo)}
                  </p>
                  <p className="text-xs text-muted">Registrato</p>
                  <DataOra value={item.created_at ?? item.updated_at} />
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button asChild variant="secondary" size="sm">
                    <a href={`#risultati/${encodeURIComponent(item.slug)}`}>Apri confronto</a>
                  </Button>
                  {item.link && (
                    <Button asChild variant="link" size="sm">
                      <a href={item.link} target="_blank" rel="noreferrer">Apri negozio</a>
                    </Button>
                  )}
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
