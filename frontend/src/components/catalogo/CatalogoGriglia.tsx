import type { CatalogoItem } from "../../types";
import { dim, eur, eurPerLitro, num } from "./fmt";

interface Props {
  items: CatalogoItem[];
}

/** Vista e-commerce: una card per scatola, foto in evidenza. */
export function CatalogoGriglia({ items }: Props) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
      {items.map((i) => (
        <Card key={i.id} item={i} />
      ))}
    </div>
  );
}

function Card({ item: i }: { item: CatalogoItem }) {
  return (
    <article className="flex flex-col overflow-hidden rounded-2xl border-2 border-border bg-surface transition duration-200 hover:-translate-y-0.5 hover:border-info hover:shadow-card">
      <div className="flex aspect-square items-center justify-center border-b border-border bg-surface p-3">
        {i.img ? (
          <img
            src={i.img}
            alt={i.nome}
            loading="lazy"
            className="max-h-full max-w-full object-contain"
          />
        ) : (
          // IKEA non espone la foto nel dump: la scatola resta leggibile lo stesso.
          <span className="text-center text-sm font-semibold text-muted">
            {dim(i.a, i.b, i.h)} cm
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-2 p-3.5">
        <div className="flex items-center justify-between gap-2">
          <span className="rounded-full bg-surface-2 px-2 py-0.5 text-xs font-bold uppercase tracking-wide text-muted">
            {i.negozio}
          </span>
          <span className="text-md font-bold">{eur(i.prezzo)} €</span>
        </div>

        <h3 className="line-clamp-3 text-sm font-semibold leading-tight">
          {i.nome}
        </h3>

        <dl className="mt-auto grid grid-cols-2 gap-x-2 gap-y-0.5 text-sm">
          <Riga label="Dim. cm" value={dim(i.a, i.b, i.h)} />
          <Riga label="Altezza" value={`${num(i.h)} cm`} />
          <Riga label="Volume" value={`${num(i.volume_l)} L`} />
          <Riga label="Valore" value={eurPerLitro(i.eur_per_l)} />
        </dl>

        {i.link && (
          <a
            href={i.link}
            target="_blank"
            rel="noopener"
            className="pt-1 text-sm font-semibold text-info hover:underline"
          >
            Vedi prodotto →
          </a>
        )}
      </div>
    </article>
  );
}

function Riga({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt className="text-muted">{label}</dt>
      <dd className="text-right font-semibold">{value}</dd>
    </>
  );
}
