import { useEffect, useMemo } from "react";
import { Button, Callout, cn, PageHeader, Skeleton } from "@suite/design-system";
import { useConfronto } from "../hooks/useConfronto";
import type { Prodotto } from "../types";
import { ProductCard } from "./ProductCard";
import { useAnnounce } from "../lib/announcer";
import { SectionIcon } from "./SectionIcon";

interface Props {
  slug: string;
}

// Vista RIUSABILE di un confronto: vale per qualunque categoria di prodotto.
// Rende i gruppi con le card e una barra fissa per confermare la scelta (da-comprare).
export function ConfrontoView({ slug }: Props) {
  const {
    data,
    loading,
    error,
    sel,
    toggle,
    setQty,
    salva,
    saving,
    saved,
    ricarica,
  } = useConfronto(slug);
  const announce = useAnnounce();

  useEffect(() => {
    if (saved) announce("Elemento salvato");
  }, [announce, saved]);

  const tutti = useMemo<Prodotto[]>(
    () => (data ? data.gruppi.flatMap((g) => g.prodotti) : []),
    [data],
  );

  const scelti = useMemo(
    () => tutti.filter((p) => sel[p.id]).map((p) => ({ p, qty: sel[p.id] })),
    [tutti, sel],
  );
  const totale = scelti.reduce((a, { p, qty }) => a + p.prezzo * qty, 0);

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl space-y-4" aria-label="Caricamento risultati">
        <Skeleton className="h-24 w-full" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }, (_, index) => (
            <Skeleton key={index} className="h-72 w-full" />
          ))}
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <Callout variant="danger" title="Impossibile completare la ricerca sulle fonti selezionate">
        <p>{error}</p>
        <Button className="mt-3" variant="secondary" onClick={ricarica}>
          Riprova
        </Button>
      </Callout>
    );
  }
  if (!data) return null;

  return (
    <div className="mx-auto max-w-6xl space-y-6 pb-4">
      <PageHeader
        className={cn(
          "[&>div:nth-child(2)]:flex-col [&>div:nth-child(2)]:items-stretch",
          "sm:[&>div:nth-child(2)]:flex-row",
          "sm:[&>div:nth-child(2)]:items-start",
        )}
        icon={<SectionIcon id="risultati" />}
        title={data.titolo}
        subtitle={data.sottotitolo}
        breadcrumb={
          <Button asChild variant="link" size="sm" className="px-0">
            <a href="#cerca">← Tutti i confronti</a>
          </Button>
        }
        actions={
          <Button asChild variant="secondary" size="sm">
            <a href="#cerca">Nuova ricerca</a>
          </Button>
        }
      />

      <div>
        {data.gruppi.map((g) => (
          <section key={g.nome} className="my-7">
            <h2 className="mb-3.5 border-l-4 border-info pl-2.5 text-lg font-semibold">
              {g.nome}
            </h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {g.prodotti.map((p) => (
                <ProductCard
                  key={p.id}
                  slug={slug}
                  prodotto={p}
                  selected={!!sel[p.id]}
                  qty={sel[p.id] ?? 1}
                  onToggle={() => toggle(p.id)}
                  onQty={(q) => setQty(p.id, q)}
                />
              ))}
            </div>
          </section>
        ))}
      </div>

      <footer
        className={cn(
          "sticky bottom-0 z-10 rounded-xl border border-border",
          "bg-surface/95 px-4 py-3 shadow-card backdrop-blur",
        )}
      >
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-4">
          <div className="min-w-48 flex-1 text-sm text-text">
            {scelti.length ? (
              <span>
                Scelti <b>{scelti.length}</b>:{" "}
                {scelti
                  .map(({ p, qty }) => `${p.nome}${qty > 1 ? ` ×${qty}` : ""}`)
                  .join("  ·  ")}
              </span>
            ) : (
              <span className="text-muted">
                Nessuna scelta ancora — clicca i prodotti che vuoi comprare.
              </span>
            )}
          </div>
          {totale > 0 && (
            <div className="text-lg font-bold">{eur(totale)}</div>
          )}
          {saved && (
            <span className="text-sm font-bold text-success">
              Salvato nel vault ✓
            </span>
          )}
          <Button
            variant="primary"
            size="sm"
            onClick={salva}
            loading={saving}
            disabled={saving}
          >
            {saving ? "Salvo…" : "Conferma scelta → da-comprare"}
          </Button>
        </div>
      </footer>
    </div>
  );
}

function eur(x: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(x);
}
