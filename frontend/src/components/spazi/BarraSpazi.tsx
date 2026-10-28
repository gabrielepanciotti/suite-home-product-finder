import { Button, Input } from "@suite/design-system";
import type { Criterio } from "../../hooks/useOrdineVani";
import type { FiltriSpazi } from "../../hooks/useFiltriSpazi";
import { COLONNE } from "./colonne";
import { Chip, Gruppo } from "./ui";

interface Props {
  filtri: FiltriSpazi;
  patch: (p: Partial<FiltriSpazi>) => void;
  alternaIn: (chiave: "negozi" | "materiali" | "tratti", v: string) => void;
  attivi: number;
  azzera: () => void;
  vocabolario: { negozi: string[]; materiali: string[]; tratti: string[] };
  criteri: Criterio[];
  rimuoviCriterio: (campo: Criterio["campo"]) => void;
  azzeraOrdine: () => void;
  foto: boolean;
  setFoto: (v: boolean) => void;
  mostrate: number;
  totali: number;
}

const ALTEZZE = [18, 23, 30];
const PREZZI = [3, 5, 10, 20];
const RIEMPIMENTI = [50, 70, 85];

/** Filtri e criteri d'ordine, condivisi da tutti i vani della pagina. */
export function BarraSpazi(p: Props) {
  return (
    <div className="sticky top-0 z-30 -mx-5 mb-8 border-b border-border bg-bg/95 px-5 py-3.5 backdrop-blur">
      <div className="flex flex-wrap items-center gap-2">
        <Input
          name="cerca-soluzione"
          aria-label="Cerca fra le scatole della classifica"
          value={p.filtri.q}
          onChange={(e) => p.patch({ q: e.target.value })}
          placeholder="Cerca una scatola…"
          className="min-w-48 flex-1 rounded-xl border-2 border-border bg-surface px-3.5 py-1.5 text-sm text-text outline-none transition-colors placeholder:text-muted focus:border-info"
        />
        <span className="text-sm text-muted">
          <strong className="text-text">{p.mostrate}</strong> righe su{" "}
          {p.totali}
        </span>
        {p.attivi > 0 && (
          <Button
            variant="secondary"
            size="sm"
            onClick={p.azzera}
          >
            azzera filtri ({p.attivi})
          </Button>
        )}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2.5">
        <Gruppo
          label="Ordina"
          aiuto="Clic sull'intestazione di una colonna per ordinare; shift+clic per aggiungerla come criterio successivo, a parità del primo. Vale per tutti i vani della pagina."
        >
          {p.criteri.map((c, i) => (
            <Button
              variant="secondary"
              size="sm"
              key={c.campo}
              onClick={() => p.rimuoviCriterio(c.campo)}
              title="togli questo criterio"
              className="gap-1"
            >
              {p.criteri.length > 1 && (
                <span className="opacity-60">{i + 1}.</span>
              )}
              {COLONNE[c.campo].label}
              <span>{c.dir === "asc" ? "↑" : "↓"}</span>
              <span className="opacity-50">✕</span>
            </Button>
          ))}
          {(p.criteri.length > 1 || p.criteri[0]?.campo !== "vol_pct") && (
            <Button
              variant="secondary"
              size="sm"
              onClick={p.azzeraOrdine}
            >
              ripristina
            </Button>
          )}
        </Gruppo>

        <Gruppo label="Vedi">
          <Chip
            attivo={p.filtri.soloOttimali}
            onClick={() => p.patch({ soloOttimali: !p.filtri.soloOttimali })}
            tono="success"
            aiuto={COLONNE.ottimale.aiuto}
          >
            solo top
          </Chip>
          <Chip
            attivo={p.filtri.soloPreferiti}
            onClick={() => p.patch({ soloPreferiti: !p.filtri.soloPreferiti })}
            tono="warning"
            aiuto="Solo le scatole che hai messo fra i preferiti con la ★."
          >
            ★ preferiti
          </Chip>
          <Chip
            attivo={p.filtri.nascondiScartati}
            onClick={() =>
              p.patch({ nascondiScartati: !p.filtri.nascondiScartati })
            }
            aiuto="Le scatole scartate restano in fondo alla tabella, sbiadite. Con questo chip spariscono del tutto."
          >
            nascondi scartate
          </Chip>
          <Chip attivo={p.foto} onClick={() => p.setFoto(!p.foto)}>
            foto
          </Chip>
        </Gruppo>

        <Gruppo label="Coperchio" aiuto={COLONNE.coperchio.aiuto}>
          <Chip
            attivo={p.filtri.coperchio === "si"}
            onClick={() =>
              p.patch({ coperchio: p.filtri.coperchio === "si" ? null : "si" })
            }
          >
            ✓ con
          </Chip>
          <Chip
            attivo={p.filtri.coperchio === "no"}
            onClick={() =>
              p.patch({ coperchio: p.filtri.coperchio === "no" ? null : "no" })
            }
          >
            ✗ senza / ignoto
          </Chip>
        </Gruppo>

        <Gruppo
          label="Altezza min"
          aiuto="Altezza esterna della scatola. I barattoli Bormioli alti 22 cm vogliono almeno 23."
        >
          {ALTEZZE.map((cm) => (
            <Chip
              key={cm}
              attivo={p.filtri.hMin === cm}
              onClick={() =>
                p.patch({ hMin: p.filtri.hMin === cm ? null : cm })
              }
            >
              ≥ {cm}
              {cm === 23 && " · barattoli"}
            </Chip>
          ))}
        </Gruppo>

        <Gruppo label="Riempimento" aiuto={COLONNE.vol_pct.aiuto}>
          {RIEMPIMENTI.map((pct) => (
            <Chip
              key={pct}
              attivo={p.filtri.riempMin === pct}
              onClick={() =>
                p.patch({ riempMin: p.filtri.riempMin === pct ? null : pct })
              }
            >
              ≥ {pct}%
            </Chip>
          ))}
        </Gruppo>

        <Gruppo label="€/pz max">
          {PREZZI.map((v) => (
            <Chip
              key={v}
              attivo={p.filtri.prezzoMax === v}
              onClick={() =>
                p.patch({ prezzoMax: p.filtri.prezzoMax === v ? null : v })
              }
            >
              ≤ {v} €
            </Chip>
          ))}
        </Gruppo>

        <Gruppo label="Negozio">
          {p.vocabolario.negozi.map((n) => (
            <Chip
              key={n}
              attivo={p.filtri.negozi.includes(n)}
              onClick={() => p.alternaIn("negozi", n)}
            >
              {n}
            </Chip>
          ))}
        </Gruppo>

        {p.vocabolario.materiali.length > 0 && (
          <Gruppo label="Materiale" aiuto={COLONNE.materiale.aiuto}>
            {p.vocabolario.materiali.map((m) => (
              <Chip
                key={m}
                attivo={p.filtri.materiali.includes(m)}
                onClick={() => p.alternaIn("materiali", m)}
              >
                {m}
              </Chip>
            ))}
          </Gruppo>
        )}

        {p.vocabolario.tratti.length > 0 && (
          <Gruppo
            label="Caratteristiche"
            aiuto="Ricavate dal nome del prodotto. Scegliendone più d'una devono esserci tutte."
          >
            {p.vocabolario.tratti.map((t) => (
              <Chip
                key={t}
                attivo={p.filtri.tratti.includes(t)}
                onClick={() => p.alternaIn("tratti", t)}
              >
                {t}
              </Chip>
            ))}
          </Gruppo>
        )}
      </div>
    </div>
  );
}
