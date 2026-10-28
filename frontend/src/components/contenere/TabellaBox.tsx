import type { Contenitore } from "../../types";
import { eur, num } from "../catalogo/fmt";
import { Aiuto } from "../spazi/Aiuto";
import { Etichetta } from "../spazi/ui";
import { Th } from "../tabella/Th";
import type { CampoBox, CriterioBox } from "./colonne";
import { COLONNE } from "./colonne";

interface Props {
  righe: Contenitore[];
  n: number;
  criteri: CriterioBox[];
  ordinaPer: (campo: CampoBox, aggiungi: boolean) => void;
  foto: boolean;
}

/** La classifica dei contenitori per l'oggetto e la quantità chiesti. */
export function TabellaBox({ righe, n, criteri, ordinaPer, foto }: Props) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-border bg-surface shadow-card">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border bg-surface-2 text-muted">
            <th className="px-2 py-2.5 text-right font-bold">#</th>
            {foto && <th className="w-8 px-2 py-2.5" />}
            <Colonna campo="ottimale" {...{ criteri, ordinaPer }} />
            <Colonna campo="nome" {...{ criteri, ordinaPer }} />
            <Colonna campo="negozio" {...{ criteri, ordinaPer }} />
            <Colonna campo="coperchio" {...{ criteri, ordinaPer }} />
            <Colonna campo="h" {...{ criteri, ordinaPer }} />
            <th className="px-2.5 py-2.5 text-center font-bold">
              <Aiuto testo="Come si dispongono gli oggetti dentro UNA scatola: quanti in larghezza per quanti in profondità, e su quanti livelli sovrapposti. Sono numeri di OGGETTI, non centimetri.">
                Come stanno
              </Aiuto>
            </th>
            <Colonna campo="per_scatola" {...{ criteri, ordinaPer }} />
            <Colonna campo="scatole" {...{ criteri, ordinaPer }} />
            <Colonna campo="avanzo" {...{ criteri, ordinaPer }} />
            <Colonna campo="riempimento_pct" {...{ criteri, ordinaPer }} />
            <Colonna campo="prezzo" {...{ criteri, ordinaPer }} />
            <Colonna campo="costo" {...{ criteri, ordinaPer }} />
            <Colonna campo="costo_per_oggetto" {...{ criteri, ordinaPer }} />
            <th className="px-2.5 py-2.5" />
          </tr>
        </thead>
        <tbody>
          {righe.map((r, i) => (
            <Riga key={r.id} r={r} n={n} posizione={i + 1} foto={foto} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Riga({
  r,
  n,
  posizione,
  foto,
}: {
  r: Contenitore;
  n: number;
  posizione: number;
  foto: boolean;
}) {
  return (
    <tr className="border-b border-border/60 align-top transition-colors last:border-0 odd:bg-surface-2/30 hover:bg-info/5">
      <td className="px-2 py-2 text-right tabular-nums text-muted">
        {posizione}
      </td>
      {foto && (
        <td className="px-2 py-2">
          {r.img && (
            <img
              src={r.img}
              alt=""
              loading="lazy"
              className="h-7 w-7 rounded-xs object-contain"
            />
          )}
        </td>
      )}
      <td className="px-2.5 py-2 text-center">
        {r.ottimale && (
          <Etichetta tono="success" aiuto={COLONNE.ottimale.aiuto}>
            top
          </Etichetta>
        )}
      </td>
      <td className="max-w-sm px-2.5 py-2">
        <div className="font-semibold">{r.nome}</div>
        {((r.materiali?.length ?? 0) > 0 || (r.tratti?.length ?? 0) > 0) && (
          <div className="mt-1 flex flex-wrap gap-1">
            {(r.materiali ?? []).map((m) => (
              <Etichetta key={m} tono="info">
                {m}
              </Etichetta>
            ))}
            {(r.tratti ?? []).map((t) => (
              <Etichetta key={t}>{t}</Etichetta>
            ))}
          </div>
        )}
      </td>
      <td className="px-2.5 py-2 text-muted">{r.negozio}</td>
      <td className="px-2.5 py-2 text-center">
        <Aiuto
          testo={
            r.coperchio === true
              ? "Il nome del prodotto dichiara un coperchio."
              : r.coperchio === false
                ? "Il nome dichiara esplicitamente che il coperchio non c'è."
                : "Il nome non dice niente sul coperchio: non lo sappiamo. Va guardata la scheda sul sito."
          }
        >
          <span
            className={
              "font-bold " +
              (r.coperchio === true
                ? "text-success"
                : r.coperchio === false
                  ? "text-danger"
                  : "text-muted/60")
            }
          >
            {r.coperchio === true ? "✓" : r.coperchio === false ? "✗" : "?"}
          </span>
        </Aiuto>
      </td>
      <td className="whitespace-nowrap px-2.5 py-2 text-right tabular-nums">
        <Aiuto
          testo={`Larghezza ${num(r.a)} · profondità ${num(r.b)} · altezza ${num(r.h)} cm, misure esterne.`}
        >
          {num(r.a)}×{num(r.b)}×<span className="font-bold">h{num(r.h)}</span>
        </Aiuto>
      </td>
      <td className="whitespace-nowrap px-2.5 py-2 text-center tabular-nums text-muted">
        <Aiuto
          testo={`${r.nx} oggetti in larghezza × ${r.ny} in profondità = ${r.nx * r.ny} per livello${r.livelli > 1 ? `, su ${r.livelli} livelli sovrapposti` : " (un solo livello)"} → ${r.per_scatola} per scatola. ${r.in_piedi ? "In piedi." : "Coricati: l'altezza dell'oggetto non è verticale."}`}
        >
          {r.nx}×{r.ny}
          {r.livelli > 1 && (
            <span className="text-text"> × {r.livelli} liv</span>
          )}
          {!r.in_piedi && <span className="ml-1 text-warning">coricati</span>}
        </Aiuto>
      </td>
      <td className="px-2.5 py-2 text-right tabular-nums">{r.per_scatola}</td>
      <td className="px-2.5 py-2 text-right text-sm font-bold tabular-nums text-info">
        {r.scatole}
      </td>
      <td className="px-2.5 py-2 text-right tabular-nums">
        <Aiuto
          testo={`${r.scatole} scatole × ${r.per_scatola} posti = ${r.capienza} posti per ${n} oggetti: ne restano ${r.avanzo} liberi.`}
        >
          <span className={r.avanzo === 0 ? "font-bold text-success" : ""}>
            {r.avanzo}
          </span>
        </Aiuto>
      </td>
      <td className="px-2.5 py-2">
        <Barra pct={r.riempimento_pct} />
      </td>
      <td className="px-2.5 py-2 text-right tabular-nums text-muted">
        {eur(r.prezzo)}
      </td>
      <td className="px-2.5 py-2 text-right text-sm font-bold tabular-nums">
        {eur(r.costo)} €
      </td>
      <td className="px-2.5 py-2 text-right tabular-nums text-success">
        {eur(r.costo_per_oggetto)}
      </td>
      <td className="px-2.5 py-2">
        {r.link && (
          <a
            href={r.link}
            target="_blank"
            rel="noopener"
            className="font-semibold text-info hover:underline"
          >
            apri →
          </a>
        )}
      </td>
    </tr>
  );
}

/** Intestazione ordinabile con le colonne di questa tabella. */
function Colonna({
  campo,
  criteri,
  ordinaPer,
}: {
  campo: CampoBox;
  criteri: CriterioBox[];
  ordinaPer: (campo: CampoBox, aggiungi: boolean) => void;
}) {
  return (
    <Th
      campo={campo}
      col={COLONNE[campo]}
      criteri={criteri}
      ordinaPer={ordinaPer}
    />
  );
}

/** Quanto dello spazio utile di una scatola piena è davvero occupato. */
function Barra({ pct }: { pct: number }) {
  return (
    <div className="flex min-w-28 items-center gap-2">
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-bg">
        <div
          className={
            "h-full rounded-full transition-all " +
            (pct >= 60 ? "bg-success" : pct >= 35 ? "bg-info" : "bg-warning")
          }
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
      <span className="w-9 text-right font-bold tabular-nums">
        {pct.toFixed(0)}%
      </span>
    </div>
  );
}
