import {
  Badge,
  Button,
  Callout,
  PageHeader,
  Skeleton,
  cn,
} from "@suite/design-system";
import { useNodeOverview } from "../hooks/useNodeOverview";
import type {
  NodeOverviewData,
  OverviewBrain,
  OverviewCollaborations,
  OverviewDatabase,
  OverviewFunction,
} from "../types";
import { SectionIcon } from "./SectionIcon";

function formatRome(iso?: string): string {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat("it-IT", {
      timeZone: "Europe/Rome",
      dateStyle: "short",
      timeStyle: "medium",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-3 rounded-2xl border-2 border-border bg-surface p-5">
      {children}
    </section>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-xs font-semibold uppercase tracking-wide text-muted">
      {children}
    </h2>
  );
}

function StatTile({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-surface-2 px-3 py-2.5 text-center">
      <div className="text-lg font-semibold text-text">{value ?? "—"}</div>
      <div className="text-xs text-muted">{label}</div>
    </div>
  );
}

function IdentitySection({ data }: { data: NodeOverviewData }) {
  const { identity, live, warning } = data;
  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-text">
              {identity?.name ?? "—"}
            </span>
            {identity?.type && <Badge>{identity.type}</Badge>}
          </div>
          <span className="text-xs text-muted">
            slug <code className="text-text">{identity?.slug}</code>
            {identity?.cluster && identity.cluster.length > 0 && (
              <> · cluster {identity.cluster.join(", ")}</>
            )}
            {identity?.hostBase && <> · {identity.hostBase}</>}
          </span>
        </div>
        <a
          href="/"
          className={cn(
            "inline-flex items-center gap-1.5 rounded-lg border border-border",
            "bg-surface px-3 py-1.5 text-sm font-semibold text-info",
            "transition-colors hover:bg-surface-2",
          )}
        >
          Apri sito ↗
        </a>
      </div>
      <div className="flex items-center gap-2 text-xs text-muted">
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5",
            live
              ? "border-success/30 bg-success/10 text-success"
              : "border-warning/40 bg-warning/10 text-warning",
          )}
        >
          ● {live ? "live" : "degradato"}
        </span>
        <span>aggiornato {formatRome(data.generated_at)}</span>
      </div>
      {warning && (
        <div className="rounded-xl border border-warning/40 bg-warning/10 px-3 py-2 text-xs text-warning">
          {warning}
        </div>
      )}
    </Card>
  );
}

function FunctionsSection({ functions }: { functions?: OverviewFunction[] }) {
  if (!functions?.length) return null;
  return (
    <Card>
      <SectionTitle>Funzioni & comandi</SectionTitle>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {functions.map((fn) => (
          <div
            key={fn.key}
            className="flex flex-col gap-1.5 rounded-xl border border-border bg-surface-2 px-3 py-2.5"
          >
            <span className="text-sm text-text">{fn.label}</span>
            <div className="flex flex-wrap items-center gap-1.5">
              {fn.agent && <Badge>{fn.agent}</Badge>}
              {fn.command && (
                <code className="rounded-xs border border-border bg-surface px-1.5 py-0.5 text-2xs text-muted">
                  {fn.command}
                </code>
              )}
              {(fn.companions ?? []).map((c) => (
                <Badge key={c}>+ {c}</Badge>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function DatabaseSection({ database }: { database?: OverviewDatabase }) {
  if (!database) return null;
  return (
    <Card>
      <SectionTitle>Stato DB (live)</SectionTitle>
      {database.error ? (
        <p className="text-sm text-danger">{database.error}</p>
      ) : (
        <>
          {database.highlights?.length > 0 && (
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {database.highlights.map((h) => (
                <StatTile key={h.label} label={h.label} value={h.value} />
              ))}
            </div>
          )}
          {database.tables?.length > 0 && (
            <div className="flex flex-col divide-y divide-border overflow-hidden rounded-xl border border-border">
              {database.tables.map((t) => (
                <div
                  key={t.name}
                  className="flex items-center justify-between bg-surface-2 px-3 py-1.5 text-xs text-muted"
                >
                  <span>{t.name}</span>
                  <span className="font-medium text-text">{t.rows}</span>
                </div>
              ))}
            </div>
          )}
          {!database.highlights?.length && !database.tables?.length && (
            <p className="text-sm text-muted">Nessuna tabella applicativa.</p>
          )}
        </>
      )}
    </Card>
  );
}

function BrainSection({ brain }: { brain?: OverviewBrain | null }) {
  if (!brain) return null;
  const stats: [string, number | undefined][] = [
    ["Totale", brain.total],
    ["Contenuti", brain.content],
    ["Hub", brain.hubs],
    ["Link", brain.links],
    ["Componenti", brain.components],
  ];
  return (
    <Card>
      <SectionTitle>Brain</SectionTitle>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
        {stats.map(([label, value]) => (
          <StatTile key={label} label={label} value={value} />
        ))}
      </div>
      {brain.per_area && brain.per_area.length > 0 && (
        <div className="flex flex-col divide-y divide-border overflow-hidden rounded-xl border border-border">
          {brain.per_area.map(([area, count]) => (
            <div
              key={area}
              className="flex items-center justify-between bg-surface-2 px-3 py-1.5 text-xs text-muted"
            >
              <span>{area}</span>
              <span className="font-medium text-text">{count}</span>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function CollaborationsSection({
  collaborations,
}: {
  collaborations?: OverviewCollaborations | null;
}) {
  if (!collaborations) return null;
  const { parent, children = [], integrations = [] } = collaborations;
  if (!parent && !children.length && !integrations.length) return null;
  return (
    <Card>
      <SectionTitle>Collaborazioni</SectionTitle>
      <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted">
        {parent && (
          <span>
            padre <Badge>{parent.name ?? parent.slug}</Badge>
          </span>
        )}
        {children.map((c) => (
          <Badge key={c.slug ?? c.name}>figlio: {c.name ?? c.slug}</Badge>
        ))}
      </div>
      {integrations.length > 0 && (
        <ul className="flex flex-col gap-1.5">
          {integrations.map((i) => (
            <li
              key={i.name}
              className="rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs text-muted"
            >
              <span className="font-semibold text-text">{i.name}</span>
              {i.kind && <span className="ml-1.5">({i.kind})</span>}
              {i.detail && <span className="ml-1.5">— {i.detail}</span>}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

// Scheda nodo live: manifest + DB del nodo, aggiornata ogni 30s.
export function NodeOverview() {
  const { data, loading, error, refetch } = useNodeOverview();

  return (
    <div className="mx-auto w-full max-w-3xl space-y-6">
      <PageHeader
        icon={<SectionIcon id="impostazioni" />}
        title="Impostazioni"
        subtitle="Identità, stato operativo e collegamenti del nodo HomeProductFinder."
      />
      <div>
        {loading && !data && (
          <div className="space-y-3" aria-label="Caricamento impostazioni">
            <Skeleton className="h-40 w-full" />
            <Skeleton className="h-56 w-full" />
          </div>
        )}

        {error && !data && (
          <Callout variant="danger" title="Impossibile caricare le impostazioni">
            <p>{error}</p>
            <Button className="mt-3" variant="secondary" onClick={() => void refetch()}>
              Riprova
            </Button>
          </Callout>
        )}

        {data && (
          <div className="flex flex-col gap-3">
            <IdentitySection data={data} />
            <FunctionsSection functions={data.functions} />
            <DatabaseSection database={data.database} />
            <BrainSection brain={data.brain} />
            <CollaborationsSection collaborations={data.collaborations} />
          </div>
        )}
      </div>
    </div>
  );
}
