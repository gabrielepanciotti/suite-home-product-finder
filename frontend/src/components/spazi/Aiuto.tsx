import { useState } from "react";

interface Props {
  testo: string;
  children: React.ReactNode;
  className?: string;
  /** false quando dentro c'è già qualcosa di focalizzabile (bottone, link):
   *  due tab-stop sullo stesso elemento sono solo un intralcio. */
  focusabile?: boolean;
}

/**
 * Spiegazione al passaggio del mouse.
 *
 * Il pannello è `position: fixed` e non figlio del flusso della tabella: dentro
 * un contenitore con `overflow-x-auto` un tooltip in posizione assoluta verrebbe
 * tagliato dal bordo della tabella proprio quando serve, sull'ultima colonna.
 * La x si ancora al centro dell'elemento e si tiene lontana dai bordi finestra.
 */
export function Aiuto({
  testo,
  children,
  className,
  focusabile = true,
}: Props) {
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null);

  const mostra = (e: React.SyntheticEvent) => {
    const r = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const meta = 150; // metà larghezza del pannello, per non uscire dallo schermo
    setPos({
      x: Math.min(
        Math.max(r.left + r.width / 2, meta + 8),
        window.innerWidth - meta - 8,
      ),
      y: r.bottom + 8,
    });
  };

  return (
    <span
      className={"relative cursor-help " + (className ?? "")}
      onMouseEnter={mostra}
      onMouseLeave={() => setPos(null)}
      onFocus={mostra}
      onBlur={() => setPos(null)}
      tabIndex={focusabile ? 0 : undefined}
    >
      {children}
      {pos && (
        <span
          role="tooltip"
          style={{ left: pos.x, top: pos.y, width: 300 }}
          className="pointer-events-none fixed z-50 -translate-x-1/2 whitespace-pre-line rounded-xl border border-border bg-surface-2 px-3.5 py-2.5 text-left text-sm font-normal normal-case leading-relaxed tracking-normal text-text shadow-dialog"
        >
          {testo}
        </span>
      )}
    </span>
  );
}
