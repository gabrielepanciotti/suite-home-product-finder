import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import type { ConfrontoSummary } from "../types";

// Elenco confronti per la home.
export function useConfronti() {
  const [data, setData] = useState<ConfrontoSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const carica = useCallback(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    api
      .listConfronti()
      .then((d) => alive && setData(d))
      .catch((e) => alive && setError(String(e.message ?? e)))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => carica(), [carica]);

  return { data, loading, error, ricarica: carica };
}
