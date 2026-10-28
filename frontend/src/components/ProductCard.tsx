import { api } from "../lib/api";
import type { Prodotto } from "../types";
import { QtyStepper } from "./QtyStepper";

interface Props {
  slug: string;
  prodotto: Prodotto;
  selected: boolean;
  qty: number;
  onToggle: () => void;
  onQty: (qty: number) => void;
}

// Card prodotto RIUSABILE: stessa struttura per ogni confronto, cambiano solo
// immagine / specs / valori. Cliccando si seleziona (bordo verde + check).
export function ProductCard({
  slug,
  prodotto: p,
  selected,
  qty,
  onToggle,
  onQty,
}: Props) {
  const img = api.imgUrl(slug, p.immagine);
  return (
    <div
      onClick={onToggle}
      className={
        "group relative flex cursor-pointer flex-col overflow-hidden rounded-2xl border-2 bg-surface " +
        "transition duration-200 hover:-translate-y-0.5 hover:shadow-card " +
        (selected ? "border-success ring-4 ring-success/15" : "border-border")
      }
    >
      <span
        className={
          "absolute right-3 top-3 z-10 grid h-7 w-7 place-items-center rounded-full bg-success text-sm " +
          "text-bg transition " +
          (selected ? "scale-100 opacity-100" : "scale-50 opacity-0")
        }
      >
        ✓
      </span>

      <div className="flex aspect-square items-center justify-center border-b border-border bg-surface p-3.5">
        {img ? (
          <img
            src={img}
            alt={p.nome}
            loading="lazy"
            className="max-h-full max-w-full object-contain"
          />
        ) : (
          <span className="text-xs text-muted">nessuna foto</span>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-2 p-3.5">
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-surface-2 px-2 py-0.5 text-xs font-bold uppercase tracking-wide text-muted">
            {p.negozio}
          </span>
          {p.consigliato && (
            <span className="rounded-full bg-info px-2 py-0.5 text-xs font-bold text-bg">
              consigliato
            </span>
          )}
        </div>

        <h3 className="text-md font-semibold leading-tight">{p.nome}</h3>

        {p.valore !== null && (
          <span className="self-start rounded-full bg-success/15 px-2.5 py-1 text-sm font-bold text-success">
            {p.valore_label}
          </span>
        )}

        <table className="w-full border-collapse text-sm">
          <tbody>
            <tr className="border-b border-dashed border-border">
              <td className="py-0.5 text-muted">Prezzo</td>
              <td className="py-0.5 text-right font-bold">{eur(p.prezzo)} €</td>
            </tr>
            {p.specs.map((s) => (
              <tr key={s.label} className="border-b border-dashed border-border">
                <td className="py-0.5 text-muted">{s.label}</td>
                <td className="py-0.5 text-right">{s.value}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {p.nota && (
          <p className="mt-0.5 text-sm leading-snug text-muted">
            {p.nota}
          </p>
        )}

        <div className="mt-auto flex items-center justify-between pt-1">
          {p.link ? (
            <a
              href={p.link}
              target="_blank"
              rel="noopener"
              onClick={(e) => e.stopPropagation()}
              className="text-sm font-semibold text-info hover:underline"
            >
              Vedi prodotto →
            </a>
          ) : (
            <span className="text-xs text-muted">solo in negozio</span>
          )}
          {selected && <QtyStepper value={qty} onChange={onQty} />}
        </div>
      </div>
    </div>
  );
}

function eur(x: number): string {
  return x.toFixed(2).replace(".", ",");
}
