import { useMemo, useState } from "react";
import type { Barattolo, RispostaBarattoli } from "../../types";
import { Aiuto } from "../spazi/Aiuto";
import { Chip, Gruppo } from "../spazi/ui";

interface Props {
  dati: RispostaBarattoli | null;
  /** L'id del barattolo attivo, o "" se le misure sono state scritte a mano. */
  preset: string;
  onScegli: (b: Barattolo) => void;
}

const numero = (n: number) => String(n).replace(".", ",");

/**
 * Due passi, nell'ordine in cui uno se lo ricorda: prima la marca, poi il
 * barattolo. Sceglierlo per nome invece che digitandone le misure evita
 * l'errore che conta davvero — fra due Bormioli alti uguale il diametro va da
 * 10,6 a 16,0 cm, e con esso quante scatole servono.
 */
export function Preselezione({ dati, preset, onScegli }: Props) {
  const marche = dati?.marche ?? [];
  // La marca attiva segue il barattolo scelto; altrimenti la prima, che con una
  // marca sola significa "già aperta" e risparmia un clic inutile.
  const [marcaAperta, setMarcaAperta] = useState<string | null>(null);

  const marcaCorrente = useMemo(() => {
    if (marcaAperta) return marcaAperta;
    const scelto = marche.find((m) => m.barattoli.some((b) => b.id === preset));
    return scelto?.marca ?? marche[0]?.marca ?? null;
  }, [marcaAperta, marche, preset]);

  const barattoli =
    marche.find((m) => m.marca === marcaCorrente)?.barattoli ?? [];

  // Le linee dentro una marca (Fido, Quattro Stagioni): sono il modo in cui il
  // produttore stesso divide il catalogo, e chi cerca il proprio barattolo
  // parte da lì.
  const perLinea = useMemo(() => {
    const gruppi = new Map<string, Barattolo[]>();
    for (const b of barattoli) {
      const k = b.linea ?? "Altri";
      gruppi.set(k, [...(gruppi.get(k) ?? []), b]);
    }
    return [...gruppi.entries()];
  }, [barattoli]);

  if (marche.length === 0) return null;

  return (
    <div className="mb-4 flex flex-col gap-3 border-b border-border pb-4">
      <Gruppo
        label="Barattolo noto"
        aiuto="Scorciatoia: scegli il barattolo per nome e le misure si compilano da sole. Sono le misure ufficiali del produttore — esterne, col diametro preso nel punto più largo del vetro. Toccando un campo a mano la scelta si scollega, perché i numeri non descrivono più quel barattolo."
      >
        {marche.map((m) => (
          <Chip
            key={m.marca}
            attivo={m.marca === marcaCorrente}
            onClick={() => setMarcaAperta(m.marca)}
          >
            {m.marca}
            <span className="ml-1 font-normal opacity-70">
              {m.barattoli.length}
            </span>
          </Chip>
        ))}
      </Gruppo>

      {perLinea.map(([linea, lista]) => (
        <div key={linea} className="flex flex-wrap items-center gap-1.5">
          <span className="w-full text-2xs font-bold uppercase tracking-wider text-muted sm:w-auto">
            {linea}
          </span>
          {lista.map((b) => (
            <Chip
              key={b.id}
              attivo={b.id === preset}
              tono="success"
              onClick={() => onScegli(b)}
              aiuto={
                (b.conflitto ? `⚠ ${b.conflitto}. ` : "") +
                `${numero(b.diametro_cm)} cm di diametro, ${numero(b.altezza_cm)} cm di altezza` +
                (b.capacita_cl ? `, ${numero(b.capacita_cl)} cl` : "")
              }
            >
              {b.conflitto && <span className="mr-1">⚠</span>}
              {etichettaCorta(b)}
              <span className="ml-1 font-normal opacity-70 tabular-nums">
                {numero(b.diametro_cm)}×{numero(b.altezza_cm)}
              </span>
            </Chip>
          ))}
        </div>
      ))}

      {preset === "" && (
        <Aiuto testo="Nessun barattolo selezionato: valgono le misure scritte nei campi qui sotto.">
          <span className="text-xs text-muted">Misure a mano</span>
        </Aiuto>
      )}
    </div>
  );
}

/** Sul chip la linea è già il titolo del gruppo: resta il nome del vaso. */
function etichettaCorta(b: Barattolo): string {
  const [, ...resto] = b.etichetta.split(" · ");
  return (resto.join(" · ") || b.etichetta).replace(/^Vaso\s+/i, "");
}
