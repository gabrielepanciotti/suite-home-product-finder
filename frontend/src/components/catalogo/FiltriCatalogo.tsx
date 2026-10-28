import { Button, Input } from "@suite/design-system";
import type {
  ChiaveOrdine,
  Direzione,
  Filtri,
  Vista,
} from "../../hooks/useCatalogoFiltri";

interface Props {
  filtri: Filtri;
  patch: (p: Partial<Filtri>) => void;
  toggleNegozio: (negozio: string) => void;
  azzera: () => void;
  attivi: number;
  negozi: { negozio: string; n: number }[];
  ordine: ChiaveOrdine;
  direzione: Direzione;
  ordinaPer: (chiave: ChiaveOrdine) => void;
  vista: Vista;
  setVista: (v: Vista) => void;
  fotoInTabella: boolean;
  setFotoInTabella: (v: boolean) => void;
  totale: number;
  mostrati: number;
}

const ORDINI: { chiave: ChiaveOrdine; label: string }[] = [
  { chiave: "eur_per_l", label: "€/litro" },
  { chiave: "prezzo", label: "Prezzo" },
  { chiave: "volume_l", label: "Volume" },
  { chiave: "h", label: "Altezza" },
  { chiave: "nome", label: "Nome" },
];

// Altezze notevoli: il barattolo Bormioli h22 richiede 23 cm esterni (1 cm di
// gioco per coperchio e manovra); gli altri due sono i tagli tipici dei vani.
const ALTEZZE: { cm: number; label: string }[] = [
  { cm: 18, label: "≥ 18" },
  { cm: 23, label: "≥ 23 · barattoli h22" },
  { cm: 35, label: "≥ 35" },
];

/** Barra filtri del catalogo. Nessun controllo nativo: solo bottoni-token. */
export function FiltriCatalogo(p: Props) {
  return (
    <div className="sticky top-0 z-20 -mx-5 mb-6 border-b border-border bg-bg/95 px-5 py-4 backdrop-blur">
      <div className="flex flex-wrap items-center gap-2">
        <Input
          name="cerca-scatola"
          aria-label="Cerca fra le scatole"
          value={p.filtri.q}
          onChange={(e) => p.patch({ q: e.target.value })}
          placeholder="Cerca fra le scatole…"
          className="min-w-56 flex-1 rounded-xl border-2 border-border bg-surface px-3.5 py-2 text-sm text-text outline-none transition-colors placeholder:text-muted focus:border-info"
        />

        {p.vista === "tabella" && (
          <Chip
            attivo={p.fotoInTabella}
            onClick={() => p.setFotoInTabella(!p.fotoInTabella)}
          >
            miniature
          </Chip>
        )}

        <Segmento
          opzioni={[
            { value: "griglia", label: "▦ Griglia" },
            { value: "tabella", label: "☰ Tabella" },
          ]}
          value={p.vista}
          onChange={(v) => p.setVista(v as Vista)}
        />
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2.5">
        <Gruppo label="Negozio">
          {p.negozi.map((n) => (
            <Chip
              key={n.negozio}
              attivo={p.filtri.negozi.includes(n.negozio)}
              onClick={() => p.toggleNegozio(n.negozio)}
            >
              {n.negozio} <span className="opacity-60">{n.n}</span>
            </Chip>
          ))}
        </Gruppo>

        <Gruppo label="Altezza min">
          {ALTEZZE.map((a) => (
            <Chip
              key={a.cm}
              attivo={p.filtri.hMin === a.cm}
              onClick={() =>
                p.patch({ hMin: p.filtri.hMin === a.cm ? null : a.cm })
              }
            >
              {a.label}
            </Chip>
          ))}
        </Gruppo>

        <Gruppo label="Tipo">
          <Chip
            attivo={p.filtri.soloScatole}
            onClick={() => p.patch({ soloScatole: !p.filtri.soloScatole })}
          >
            solo scatole
          </Chip>
        </Gruppo>

        <Gruppo label="Prezzo max">
          {[5, 10, 20].map((v) => (
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

        <Gruppo label="Ordina">
          {ORDINI.map((o) => (
            <Chip
              key={o.chiave}
              attivo={p.ordine === o.chiave}
              onClick={() => p.ordinaPer(o.chiave)}
            >
              {o.label}
              {p.ordine === o.chiave && (
                <span className="ml-1">
                  {p.direzione === "asc" ? "↑" : "↓"}
                </span>
              )}
            </Chip>
          ))}
        </Gruppo>
      </div>

      <div className="mt-3 flex items-center gap-3 text-sm text-muted">
        <span>
          <strong className="text-text">{p.mostrati}</strong> scatole
          {p.mostrati !== p.totale && ` su ${p.totale}`}
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
    </div>
  );
}

function Gruppo({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-xs font-bold uppercase tracking-wide text-muted">
        {label}
      </span>
      {children}
    </div>
  );
}

function Chip({
  attivo,
  onClick,
  children,
}: {
  attivo: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={onClick}
      className={
        "rounded-full border px-2.5 py-1 text-sm font-semibold transition " +
        (attivo
          ? "border-info bg-info text-bg hover:bg-info"
          : "border-border bg-surface text-muted hover:border-info hover:text-text")
      }
    >
      {children}
    </Button>
  );
}

function Segmento({
  opzioni,
  value,
  onChange,
}: {
  opzioni: { value: string; label: string }[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex shrink-0 gap-1 rounded-xl border-2 border-border bg-surface p-1">
      {opzioni.map((o) => (
        <Button
          variant="ghost"
          size="sm"
          key={o.value}
          onClick={() => onChange(o.value)}
          className={
            "rounded-lg px-3 py-1.5 text-sm font-semibold transition " +
            (value === o.value
              ? "bg-info text-bg hover:bg-info"
              : "text-muted hover:bg-surface-2 hover:text-text")
          }
        >
          {o.label}
        </Button>
      ))}
    </div>
  );
}
