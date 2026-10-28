import type { Colonna, Criterio } from "../../hooks/useOrdine";
import { Aiuto } from "../spazi/Aiuto";

/**
 * Intestazione ordinabile: clic = ordina, shift+clic = criterio successivo.
 *
 * L'allineamento della cella segue quello dei numeri sotto — una colonna di
 * importi allineati a destra con il titolo a sinistra si legge male, ed era una
 * delle cose storte della prima tabella.
 */
export function Th<C extends string>({
  campo,
  col,
  criteri,
  ordinaPer,
}: {
  campo: C;
  col: Colonna;
  criteri: Criterio<C>[];
  ordinaPer: (campo: C, aggiungi: boolean) => void;
}) {
  const i = criteri.findIndex((c) => c.campo === campo);
  const attivo = i >= 0 ? criteri[i] : null;
  const allinea =
    col.allinea === "dx"
      ? "text-right"
      : col.allinea === "centro"
        ? "text-center"
        : "text-left";

  return (
    <th className={`px-2.5 py-2 font-bold ${allinea}`}>
      <Aiuto
        focusabile={false}
        testo={`${col.aiuto}\n\nClic per ordinare, shift+clic per aggiungerla come criterio successivo.`}
      >
        <span
          role="button"
          tabIndex={0}
          onClick={(e) => ordinaPer(campo, e.shiftKey)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              ordinaPer(campo, e.shiftKey);
            }
          }}
          className={
            "whitespace-nowrap transition-colors hover:text-text " +
            (attivo ? "text-info" : "")
          }
        >
          {col.label}
          {attivo && (
            <span className="ml-0.5">
              {attivo.dir === "asc" ? "↑" : "↓"}
              {criteri.length > 1 && (
                <sup className="ml-0.5 opacity-70">{i + 1}</sup>
              )}
            </span>
          )}
        </span>
      </Aiuto>
    </th>
  );
}
