import { Button } from "@suite/design-system";
import { Aiuto } from "./Aiuto";

/** Chip filtro/azione. Nessun controllo nativo: solo bottoni con i token. */
export function Chip({
  attivo,
  onClick,
  children,
  aiuto,
  tono = "info",
}: {
  attivo: boolean;
  onClick: () => void;
  children: React.ReactNode;
  aiuto?: string;
  tono?: "info" | "warning" | "success";
}) {
  const acceso = {
    info: "border-info bg-info text-bg hover:bg-info",
    warning: "border-warning bg-warning text-bg hover:bg-warning",
    success: "border-success bg-success text-bg hover:bg-success",
  }[tono];

  const bottone = (
    <Button
      variant="ghost"
      size="sm"
      onClick={onClick}
      aria-pressed={attivo}
      className={
        "rounded-full border px-2.5 py-1 text-sm font-semibold transition-all active:scale-95 " +
        (attivo
          ? `${acceso} shadow-card`
          : "border-border bg-surface text-muted hover:border-info hover:text-text")
      }
    >
      {children}
    </Button>
  );

  return aiuto ? (
    <Aiuto testo={aiuto} focusabile={false}>
      {bottone}
    </Aiuto>
  ) : (
    bottone
  );
}

/** Gruppo di chip con la sua etichetta. */
export function Gruppo({
  label,
  aiuto,
  children,
}: {
  label: string;
  aiuto?: string;
  children: React.ReactNode;
}) {
  const testo = (
    <span className="text-2xs font-bold uppercase tracking-wider text-muted">
      {label}
    </span>
  );
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {aiuto ? <Aiuto testo={aiuto}>{testo}</Aiuto> : testo}
      {children}
    </div>
  );
}

/** Etichetta ferma (non cliccabile): materiale, tratto, stato. */
export function Etichetta({
  children,
  tono = "neutro",
  aiuto,
}: {
  children: React.ReactNode;
  tono?: "neutro" | "info" | "success" | "warning";
  aiuto?: string;
}) {
  const stile = {
    neutro: "bg-surface-2 text-muted",
    info: "bg-info/15 text-info",
    success: "bg-success/15 text-success",
    warning: "bg-warning/15 text-warning",
  }[tono];
  const el = (
    <span
      className={`inline-block rounded-md px-1.5 py-0.5 text-2xs font-bold uppercase tracking-wide ${stile}`}
    >
      {children}
    </span>
  );
  return aiuto ? <Aiuto testo={aiuto}>{el}</Aiuto> : el;
}
