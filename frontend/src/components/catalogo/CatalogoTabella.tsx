import { Button } from "@suite/design-system";
import type { ChiaveOrdine, Direzione } from "../../hooks/useCatalogoFiltri";
import type { CatalogoItem } from "../../types";
import { eur, eurPerLitro, num } from "./fmt";

interface Props {
  items: CatalogoItem[];
  ordine: ChiaveOrdine;
  direzione: Direzione;
  ordinaPer: (chiave: ChiaveOrdine) => void;
  foto: boolean;
}

/** Vista tabellare: tutte le caratteristiche a confronto, colonne ordinabili. */
export function CatalogoTabella({
  items,
  ordine,
  direzione,
  ordinaPer,
  foto,
}: Props) {
  return (
    <div className="overflow-x-auto rounded-2xl border-2 border-border bg-surface">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b-2 border-border bg-surface-2 text-left">
            {foto && <th className="w-10 px-3 py-2.5" />}
            <Th chiave="nome" {...{ ordine, direzione, ordinaPer }}>
              Prodotto
            </Th>
            <th className="px-3 py-2.5 font-bold text-muted">Negozio</th>
            <th className="px-3 py-2.5 text-right font-bold text-muted">
              L×P cm
            </th>
            <Th chiave="h" allineaDx {...{ ordine, direzione, ordinaPer }}>
              H cm
            </Th>
            <Th
              chiave="volume_l"
              allineaDx
              {...{ ordine, direzione, ordinaPer }}
            >
              Volume
            </Th>
            <Th chiave="prezzo" allineaDx {...{ ordine, direzione, ordinaPer }}>
              Prezzo
            </Th>
            <Th
              chiave="eur_per_l"
              allineaDx
              {...{ ordine, direzione, ordinaPer }}
            >
              €/litro
            </Th>
            <th className="px-3 py-2.5" />
          </tr>
        </thead>
        <tbody>
          {items.map((i) => (
            <tr
              key={i.id}
              className="border-b border-border transition-colors last:border-0 hover:bg-surface-2"
            >
              {foto && (
                <td className="px-3 py-1.5">
                  {i.img && (
                    <img
                      src={i.img}
                      alt=""
                      loading="lazy"
                      className="h-7 w-7 rounded-xs object-contain"
                    />
                  )}
                </td>
              )}
              <td className="max-w-md px-3 py-1.5 font-semibold">
                {i.nome}
                {i.classe !== "scatola" && (
                  <span
                    className="ml-2 rounded-full bg-warning/15 px-2 py-0.5 text-xs font-bold text-warning"
                    title={i.classe_perche}
                  >
                    {i.classe}
                  </span>
                )}
              </td>
              <td className="px-3 py-1.5 text-muted">{i.negozio}</td>
              <td className="whitespace-nowrap px-3 py-1.5 text-right tabular-nums">
                {num(i.a)}×{num(i.b)}
              </td>
              <td className="px-3 py-1.5 text-right font-bold tabular-nums">
                {num(i.h)}
              </td>
              <td className="px-3 py-1.5 text-right tabular-nums">
                {num(i.volume_l)} L
              </td>
              <td className="px-3 py-1.5 text-right font-bold tabular-nums">
                {eur(i.prezzo)} €
              </td>
              <td className="px-3 py-1.5 text-right tabular-nums text-success">
                {eurPerLitro(i.eur_per_l)}
              </td>
              <td className="px-3 py-1.5">
                {i.link && (
                  <a
                    href={i.link}
                    target="_blank"
                    rel="noopener"
                    className="font-semibold text-info hover:underline"
                  >
                    apri →
                  </a>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({
  chiave,
  children,
  ordine,
  direzione,
  ordinaPer,
  allineaDx,
}: {
  chiave: ChiaveOrdine;
  children: React.ReactNode;
  ordine: ChiaveOrdine;
  direzione: Direzione;
  ordinaPer: (chiave: ChiaveOrdine) => void;
  allineaDx?: boolean;
}) {
  const attiva = ordine === chiave;
  return (
    <th className={"px-3 py-2.5 " + (allineaDx ? "text-right" : "")}>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => ordinaPer(chiave)}
        className={
          "h-auto px-0 py-0 font-bold transition-colors hover:text-text " +
          (attiva ? "text-info" : "text-muted")
        }
      >
        {children}
        {attiva && (
          <span className="ml-1">{direzione === "asc" ? "↑" : "↓"}</span>
        )}
      </Button>
    </th>
  );
}
