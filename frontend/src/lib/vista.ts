import type { VistaBody, VistaFetcher } from "@suite/design-system";

const SEZIONI = [
  ["cerca", "Cerca"],
  ["risultati", "Risultati"],
  ["salvati", "Salvati"],
  ["spazi", "Spazi da riempire"],
  ["contenere", "In cosa lo metto"],
  ["catalogo", "Catalogo scatole"],
  ["impostazioni", "Impostazioni"],
] as const;

const FALLBACK: VistaBody = {
  ruolo: "admin",
  etichetta: "Amministratore",
  sezioni: SEZIONI.map(([id, titolo]) => ({
    id,
    titolo,
    nascosta: false,
    preferita: false,
  })),
  azioni: {
    "ricerca.crea": true,
    "ricerca.elimina": true,
    "salvato.crea": true,
    "salvato.modifica": true,
    "salvato.elimina": true,
    "impostazioni.modifica": true,
  },
  preferenze: {
    nascoste: [],
    ordine: SEZIONI.map(([id]) => id),
    preferiti: [],
  },
};

function pathname(input: RequestInfo | URL): string {
  if (input instanceof URL) return input.pathname;
  if (input instanceof Request) return new URL(input.url).pathname;
  return new URL(input, window.location.origin).pathname;
}

export const vistaFetcher: VistaFetcher = async (input, init) => {
  const isVistaGet =
    pathname(input) === "/api/vista" &&
    (!init?.method || init.method.toUpperCase() === "GET");

  if (!isVistaGet) return fetch(input, init);

  try {
    const response = await fetch(input, init);
    if (!response.ok) return FALLBACK;
    return (await response.json()) as VistaBody;
  } catch {
    return FALLBACK;
  }
};
