import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import type { CatalogoItem } from "../types";

// Catalogo grezzo delle scatole (una sola fetch: ~300 righe, poi tutto client-side).
export function useCatalogo() {
  const [items, setItems] = useState<CatalogoItem[]>([]);
  const [negozi, setNegozi] = useState<{ negozio: string; n: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const carica = useCallback(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    api
      .getCatalogo()
      .then((d) => {
        if (!alive) return;
        setItems(d.items);
        setNegozi(d.negozi);
      })
      .catch((e) => alive && setError(String(e.message ?? e)))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => carica(), [carica]);

  return { items, negozi, loading, error, ricarica: carica };
}
