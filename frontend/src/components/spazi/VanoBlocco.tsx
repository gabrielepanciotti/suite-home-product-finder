import { Button } from "@suite/design-system";
import type { Criterio } from "../../hooks/useOrdineVani";
import type { Vano } from "../../types";
import { eur, num } from "../catalogo/fmt";
import { Th as ThGenerica } from "../tabella/Th";
import { Aiuto } from "./Aiuto";
import type { CampoVano } from "./colonne";
import { COLONNE } from "./colonne";
import type { RigaVano } from "./righe";
import { Etichetta } from "./ui";

interface Props {
  vano: Vano;
  righe: RigaVano[];
  criteri: Criterio[];
  ordinaPer: (campo: CampoVano, aggiungi: boolean) => void;
  alterna: (id: string, verdetto: "preferiti" | "scartati") => void;
  azzeraVerdetti: () => void;
  foto: boolean;
}

/** Un vano: le sue misure e la classifica completa di come riempirlo. */
export function VanoBlocco({
  vano,
  righe,
  criteri,
  ordinaPer,
  alterna,
  azzeraVerdetti,
  foto,
}: Props) {
  const misurabile = vano.regolabile || vano.H != null;
  const conVerdetti = righe.some((r) => r.preferito || r.scartato);

  return (
    <section className="mb-6 overflow-hidden rounded-2xl border border-border bg-surface shadow-card">
      <header className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-border bg-surface-2 px-4 py-3">
        <h3 className="text-md font-bold tracking-tight">{vano.nome}</h3>

        <Aiuto
          testo={
            vano.regolabile
              ? "Pianta del ripiano (larghezza × profondità) e altezza totale del montante su cui i ripiani si possono fissare dove si vuole."
              : "Misure UTILI del vano, cioè lo spazio davvero libero dentro: larghezza × profondità × altezza."
          }
        >
          <span className="rounded-lg bg-bg px-2 py-1 font-mono text-xs font-semibold text-muted">
            {vano.regolabile ? (
              <>
                {vano.L != null ? num(vano.L) : "?"}×
                {vano.P != null ? num(vano.P) : "?"} cm · montante{" "}
                {vano.montante != null ? num(vano.montante) : "?"} ·{" "}
                {vano.ripiani ?? "?"} ripiani
              </>
            ) : (
              <>
                {vano.L != null ? num(vano.L) : "?"}×
                {vano.P != null ? num(vano.P) : "?"}×h
                {vano.H != null ? num(vano.H) : "?"} cm
              </>
            )}
          </span>
        </Aiuto>

        {vano.regolabile && (
          <Etichetta
            tono="info"
            aiuto="I ripiani si fissano dove si vuole sul montante: qui l'altezza per livello non è un vincolo ma un risultato. La colonna Passo dice a che distanza metterli."
          >
            passo libero
          </Etichetta>
        )}
        {!vano.regolabile && vano.H == null && (
          <Etichetta tono="warning">altezza da misurare</Etichetta>
        )}
        {vano.nominale && (
          <span className="text-xs text-muted">
            nominale {vano.nominale}
          </span>
        )}
        {vano.accesso && (
          <span className="text-xs text-muted">· {vano.accesso}</span>
        )}

        <span className="ml-auto text-xs text-muted">
          {righe.length} su {vano.n_soluzioni} soluzioni
        </span>
        {conVerdetti && (
          <Button
            variant="secondary"
            size="sm"
            onClick={azzeraVerdetti}
          >
            azzera ★/✕
          </Button>
        )}
      </header>

      {!misurabile ? (
        <p className="px-4 py-4 text-sm text-muted">
          Pianta nota, altezza no: senza quella la classifica sarebbe inventata.
          {vano.note && ` ${vano.note}`}
        </p>
      ) : righe.length === 0 ? (
        <p className="px-4 py-4 text-sm text-muted">
          Con i filtri attivi non resta nessuna scatola
          {vano.n_soluzioni > 0 && ` (ce ne sarebbero ${vano.n_soluzioni})`}.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-muted">
                <th className="px-2 py-2 text-right font-bold">#</th>
                <th className="px-1 py-2 text-center font-bold">
                  <Aiuto testo="Preferita: la scatola resta in cima alla tabella, e nessun filtro la nasconde. Il verdetto si salva nel vault, quindi lo ritrovi al prossimo giro.">
                    ★
                  </Aiuto>
                </th>
                <th className="px-1 py-2 text-center font-bold">
                  <Aiuto testo="Scartata: la scatola scende in fondo, sbiadita. Non sparisce — resta lì a ricordarti che l'avevi già guardata e detto no.">
                    ✕
                  </Aiuto>
                </th>
                {foto && <th className="w-8 px-2 py-2" />}
                <Th campo="ottimale" {...{ criteri, ordinaPer }} />
                <Th campo="nome" {...{ criteri, ordinaPer }} />
                <Th campo="negozio" {...{ criteri, ordinaPer }} />
                <Th campo="coperchio" {...{ criteri, ordinaPer }} />
                <Th campo="h" {...{ criteri, ordinaPer }} />
                <th className="px-2.5 py-2 text-center font-bold">
                  <Aiuto testo="Come si dispongono nel vano: quante in larghezza per quante in profondità, e su quanti livelli sovrapposti. Sono numeri di SCATOLE, non centimetri.">
                    Disposizione
                  </Aiuto>
                </th>
                {vano.regolabile && (
                  <Th campo="passo_cm" {...{ criteri, ordinaPer }} />
                )}
                <Th campo="pezzi" {...{ criteri, ordinaPer }} />
                <Th campo="area_pct" {...{ criteri, ordinaPer }} />
                <Th campo="vol_pct" {...{ criteri, ordinaPer }} />
                <Th campo="litri" {...{ criteri, ordinaPer }} />
                <Th campo="prezzo" {...{ criteri, ordinaPer }} />
                <Th campo="costo" {...{ criteri, ordinaPer }} />
                <Th campo="eur_per_l" {...{ criteri, ordinaPer }} />
                <th className="px-2.5 py-2" />
              </tr>
            </thead>
            <tbody>
              {righe.map((s, idx) => (
                <Riga
                  key={s.id}
                  s={s}
                  posizione={idx + 1}
                  regolabile={!!vano.regolabile}
                  foto={foto}
                  alterna={alterna}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function Riga({
  s,
  posizione,
  regolabile,
  foto,
  alterna,
}: {
  s: RigaVano;
  posizione: number;
  regolabile: boolean;
  foto: boolean;
  alterna: (id: string, verdetto: "preferiti" | "scartati") => void;
}) {
  const sfondo = s.preferito
    ? "bg-warning/10"
    : s.scartato
      ? "opacity-45"
      : "odd:bg-surface-2/30";

  return (
    <tr
      className={`border-b border-border/60 align-top transition-colors last:border-0 hover:bg-info/5 ${sfondo}`}
    >
      <td className="px-2 py-2 text-right tabular-nums text-muted">
        {posizione}
      </td>
      <td
        className={
          "px-1 py-2 text-center " +
          (s.preferito ? "border-l-2 border-warning" : "")
        }
      >
        <Button
          variant="ghost"
          size="sm"
          onClick={() => alterna(s.id, "preferiti")}
          title={s.preferito ? "togli dai preferiti" : "metti fra i preferiti"}
          aria-pressed={s.preferito}
          className={
            "h-auto px-0 py-0 text-md leading-none transition-transform hover:scale-125 " +
            (s.preferito ? "text-warning" : "text-muted/40 hover:text-warning")
          }
        >
          {s.preferito ? "★" : "☆"}
        </Button>
      </td>
      <td className="px-1 py-2 text-center">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => alterna(s.id, "scartati")}
          title={s.scartato ? "rimetti in gioco" : "scarta"}
          aria-pressed={s.scartato}
          className={
            "h-auto px-0 py-0 text-sm leading-none transition-transform hover:scale-125 " +
            (s.scartato ? "text-danger" : "text-muted/40 hover:text-danger")
          }
        >
          ✕
        </Button>
      </td>
      {foto && (
        <td className="px-2 py-2">
          {s.img && (
            <img
              src={s.img}
              alt=""
              loading="lazy"
              className="h-7 w-7 rounded-xs object-contain"
            />
          )}
        </td>
      )}
      <td className="px-2.5 py-2 text-center">
        {s.ottimale && (
          <Etichetta tono="success" aiuto={COLONNE.ottimale.aiuto}>
            top
          </Etichetta>
        )}
      </td>
      <td className="max-w-sm px-2.5 py-2">
        <div className={"font-semibold " + (s.scartato ? "line-through" : "")}>
          {s.nome}
        </div>
        {((s.materiali?.length ?? 0) > 0 || (s.tratti?.length ?? 0) > 0) && (
          <div className="mt-1 flex flex-wrap gap-1">
            {(s.materiali ?? []).map((m) => (
              <Etichetta key={m} tono="info">
                {m}
              </Etichetta>
            ))}
            {(s.tratti ?? []).map((t) => (
              <Etichetta key={t}>{t}</Etichetta>
            ))}
          </div>
        )}
      </td>
      <td className="px-2.5 py-2 text-muted">{s.negozio}</td>
      <td className="px-2.5 py-2 text-center">
        <Aiuto
          testo={
            s.coperchio === true
              ? "Il nome del prodotto dichiara un coperchio."
              : s.coperchio === false
                ? "Il nome dichiara esplicitamente che il coperchio non c'è."
                : "Il nome non dice niente sul coperchio: non lo sappiamo. Va guardata la scheda sul sito."
          }
        >
          <span
            className={
              "font-bold " +
              (s.coperchio === true
                ? "text-success"
                : s.coperchio === false
                  ? "text-danger"
                  : "text-muted/60")
            }
          >
            {s.coperchio === true ? "✓" : s.coperchio === false ? "✗" : "?"}
          </span>
        </Aiuto>
      </td>
      <td className="whitespace-nowrap px-2.5 py-2 text-right tabular-nums">
        <Aiuto
          testo={`Larghezza ${num(s.a)} · profondità ${num(s.b)} · altezza ${num(s.h)} cm (misure esterne).`}
        >
          {num(s.a)}×{num(s.b)}×<span className="font-bold">h{num(s.h)}</span>
        </Aiuto>
      </td>
      <td className="whitespace-nowrap px-2.5 py-2 text-center tabular-nums text-muted">
        <Aiuto
          testo={`${s.nx} scatole in larghezza × ${s.ny} in profondità = ${s.nx * s.ny} per livello${s.livelli > 1 ? `, su ${s.livelli} livelli sovrapposti` : " (un solo livello)"} → ${s.pezzi} pezzi in tutto.`}
        >
          {s.nx}×{s.ny}
          {s.livelli > 1 && (
            <span className="text-text"> × {s.livelli} liv</span>
          )}
        </Aiuto>
      </td>
      {regolabile && (
        <td className="whitespace-nowrap px-2.5 py-2 text-right font-bold tabular-nums text-info">
          {s.passo_cm != null ? `${num(s.passo_cm)} cm` : "—"}
        </td>
      )}
      <td className="px-2.5 py-2 text-right font-bold tabular-nums">
        {s.pezzi}
      </td>
      <td className="px-2.5 py-2 text-right tabular-nums">
        {s.area_pct.toFixed(0)}%
      </td>
      <td className="px-2.5 py-2">
        <Barra pct={s.vol_pct} />
      </td>
      <td className="px-2.5 py-2 text-right tabular-nums">{num(s.litri)}</td>
      <td className="px-2.5 py-2 text-right tabular-nums text-muted">
        {eur(s.prezzo)}
      </td>
      <td className="px-2.5 py-2 text-right font-bold tabular-nums">
        {eur(s.costo)} €
      </td>
      <td className="px-2.5 py-2 text-right tabular-nums text-success">
        {s.eur_per_l.toFixed(2).replace(".", ",")}
      </td>
      <td className="px-2.5 py-2">
        {s.link && (
          <a
            href={s.link}
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

/** Intestazione ordinabile della classifica: la generica, con le sue colonne. */
function Th({
  campo,
  criteri,
  ordinaPer,
}: {
  campo: CampoVano;
  criteri: Criterio[];
  ordinaPer: (campo: CampoVano, aggiungi: boolean) => void;
}) {
  return (
    <ThGenerica
      campo={campo}
      col={COLONNE[campo]}
      criteri={criteri}
      ordinaPer={ordinaPer}
    />
  );
}

/** Percentuale di volume riempito, leggibile a colpo d'occhio. */
function Barra({ pct }: { pct: number }) {
  return (
    <div className="flex min-w-30 items-center gap-2">
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-bg">
        <div
          className={
            "h-full rounded-full transition-all " +
            (pct >= 85 ? "bg-success" : pct >= 60 ? "bg-info" : "bg-warning")
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
