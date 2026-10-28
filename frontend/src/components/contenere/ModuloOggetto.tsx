import { Button, Input } from "@suite/design-system";
import type { Modulo } from "../../hooks/useContenere";
import { daBarattolo } from "../../hooks/useContenere";
import type { RispostaBarattoli } from "../../types";
import { Aiuto } from "../spazi/Aiuto";
import { Chip, Gruppo } from "../spazi/ui";
import { Preselezione } from "./Preselezione";

interface Props {
  modulo: Modulo;
  patch: (p: Partial<Modulo>) => void;
  azzera: () => void;
  /** Cosa il catalogo dichiara davvero, dal backend: qui niente elenco fisso. */
  materialiCatalogo: { nome: string; n: number }[];
  /** I barattoli noti per la preselezione; null se non sono arrivati. */
  barattoli: RispostaBarattoli | null;
}

/**
 * Cosa va conservato: misure di UN oggetto, quantità, e i vincoli di come può
 * stare. Niente controlli nativi — le misure sono campi di testo perché "22,5"
 * con la virgola è una misura legittima, e le scelte sono chip.
 */
export function ModuloOggetto({
  modulo,
  patch,
  azzera,
  materialiCatalogo,
  barattoli,
}: Props) {
  const tondo = modulo.forma === "tondo";

  /** Il ciclo dei tre stati: indifferente → lo voglio → non lo voglio. */
  const ruota = (nome: string) => {
    const voluto = modulo.materiali.includes(nome);
    const rifiutato = modulo.escludi.includes(nome);
    const senza = {
      materiali: modulo.materiali.filter((m) => m !== nome),
      escludi: modulo.escludi.filter((m) => m !== nome),
    };
    if (voluto) patch({ ...senza, escludi: [...senza.escludi, nome] });
    else if (rifiutato) patch(senza);
    else patch({ ...senza, materiali: [...senza.materiali, nome] });
  };

  return (
    <section className="mb-6 rounded-2xl border border-border bg-surface p-4 shadow-card">
      <Preselezione
        dati={barattoli}
        preset={modulo.preset}
        onScegli={(b) => patch(daBarattolo(b))}
      />

      <div className="flex flex-wrap items-end gap-x-5 gap-y-4">
        <Gruppo
          label="Forma"
          aiuto="Un oggetto tondo occupa comunque il quadrato che lo contiene: due barattoli accostati lasciano vuoti gli spicchi fra l'uno e l'altro, e quello spazio non è riutilizzabile. Per questo al tondo basta il diametro."
        >
          <Chip attivo={tondo} onClick={() => patch({ forma: "tondo" })}>
            tondo
          </Chip>
          <Chip attivo={!tondo} onClick={() => patch({ forma: "squadrato" })}>
            squadrato
          </Chip>
        </Gruppo>

        {tondo ? (
          <Campo
            label="Diametro"
            unita="cm"
            valore={modulo.diametro}
            onChange={(v) => patch({ diametro: v })}
            aiuto="Il punto più largo dell'oggetto, coperchio o manico compresi: è quello che decide se ce ne stanno due affiancati."
          />
        ) : (
          <>
            <Campo
              label="Larghezza"
              unita="cm"
              valore={modulo.larghezza}
              onChange={(v) => patch({ larghezza: v })}
              aiuto="Il primo dei due lati di base. Quale sia dei due non conta: il calcolo prova comunque a girare l'oggetto di 90°."
            />
            <Campo
              label="Profondità"
              unita="cm"
              valore={modulo.profondita}
              onChange={(v) => patch({ profondita: v })}
              aiuto="L'altro lato di base."
            />
          </>
        )}

        <Campo
          label="Altezza"
          unita="cm"
          valore={modulo.altezza}
          onChange={(v) => patch({ altezza: v })}
          aiuto="Da terra al punto più alto, coperchio compreso. Per i barattoli Bormioli è 22 cm."
        />

        <Campo
          label="Quantità"
          unita="pz"
          valore={modulo.quantita}
          onChange={(v) => patch({ quantita: v })}
          aiuto="Quanti oggetti vanno conservati in tutto. Da qui esce quante scatole servono: il numero si arrotonda sempre per eccesso."
          largo
        />

        <Button
          variant="secondary"
          size="sm"
          onClick={azzera}
          className="ml-auto"
        >
          azzera
        </Button>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-3 border-t border-border pt-3">
        <Gruppo label="Come può stare">
          <Chip
            attivo={modulo.in_piedi}
            onClick={() => patch({ in_piedi: !modulo.in_piedi })}
            aiuto="Acceso: l'oggetto deve restare dritto, e l'altezza che hai scritto va sempre in verticale. Spento: può anche essere coricato, e allora il calcolo prova a mettere ogni lato verso l'alto — giusto per i libri e le scatole, sbagliato per un barattolo, che coricato si svuota."
          >
            solo in piedi
          </Chip>
          <Chip
            attivo={modulo.impilabili}
            onClick={() => patch({ impilabili: !modulo.impilabili })}
            aiuto="Acceso: gli oggetti si possono sovrapporre, quindi una scatola alta vale più livelli. Spento (predefinito): un solo livello, per quanto alta sia la scatola — su un coperchio di vetro non ci si appoggia niente."
          >
            impilabili
          </Chip>
        </Gruppo>

        <Campo
          label="Margine pareti"
          unita="cm"
          valore={modulo.margine}
          onChange={(v) => patch({ margine: v })}
          aiuto="I negozi pubblicano solo le misure ESTERNE: nessuno dichiara lo spessore delle pareti. Questo numero viene tolto da ogni lato prima del calcolo, per stimare lo spazio vero dentro. 1 cm è una stima prudente per una cassetta di plastica; alzalo per i cesti di vimini, che rubano molto di più. Attenzione anche alle pareti svasate: molte scatole in basso sono più strette che in cima."
        />

        <Campo
          label="Max scatole"
          unita=""
          valore={modulo.max_scatole}
          onChange={(v) => patch({ max_scatole: v })}
          aiuto="Filtro facoltativo: nasconde le soluzioni che richiedono più scatole di così. Serve a togliere di mezzo le scatoline che ne vorrebbero trenta. Vuoto = nessun limite."
        />
      </div>

      {materialiCatalogo.length > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-3 border-t border-border pt-3">
          <Gruppo
            label="Materiale"
            aiuto="Ogni clic gira il materiale fra tre stati: indifferente (grigio), lo voglio (verde), non lo voglio (arancione). Il filtro non è cosmetico — agisce prima della classifica, perché il cartone è la roba più economica del catalogo e senza filtro occupa tutti i primi posti con scatoloni da trasloco. Il numero fra parentesi è quante scatole del catalogo dichiarano quel materiale."
          >
            {materialiCatalogo.map(({ nome, n }) => {
              const voluto = modulo.materiali.includes(nome);
              const rifiutato = modulo.escludi.includes(nome);
              return (
                <Chip
                  key={nome}
                  attivo={voluto || rifiutato}
                  tono={voluto ? "success" : "warning"}
                  onClick={() => ruota(nome)}
                >
                  {rifiutato && "✕ "}
                  {nome}
                  <span className="ml-1 font-normal opacity-70">{n}</span>
                </Chip>
              );
            })}
          </Gruppo>

          {modulo.materiali.length > 0 && (
            <Gruppo label="">
              <Chip
                attivo={modulo.ignoti}
                onClick={() => patch({ ignoti: !modulo.ignoti })}
                aiuto="Il materiale si ricava dal nome del prodotto, e moltissimi nomi non lo dicono: un IKEA KUGGIS è solo «KUGGIS». Acceso (predefinito): quelle scatole restano, perché non sapere non vuol dire materiale sbagliato. Spento: restano solo quelle che dichiarano esplicitamente il materiale che hai chiesto — elenco molto più corto, e qualche buona scatola di plastica ci rimette."
              >
                anche materiale ignoto
              </Chip>
            </Gruppo>
          )}
        </div>
      )}
    </section>
  );
}

function Campo({
  label,
  unita,
  valore,
  onChange,
  aiuto,
  largo,
}: {
  label: string;
  unita: string;
  valore: string;
  onChange: (v: string) => void;
  aiuto: string;
  largo?: boolean;
}) {
  return (
    <label className="flex flex-col gap-1">
      <Aiuto testo={aiuto} focusabile={false}>
        <span className="text-2xs font-bold uppercase tracking-wider text-muted">
          {label}
        </span>
      </Aiuto>
      <span className="flex items-center gap-1.5">
        <Input
          value={valore}
          onChange={(e) => onChange(e.target.value)}
          inputMode="decimal"
          placeholder="—"
          className={
            "rounded-lg border border-border bg-bg px-2.5 py-1.5 text-sm font-semibold tabular-nums text-text outline-none transition focus:border-info " +
            (largo ? "w-24" : "w-20")
          }
        />
        {unita && <span className="text-xs text-muted">{unita}</span>}
      </span>
    </label>
  );
}
