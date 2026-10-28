import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import type { Spazio } from "../types";

// Spazi da riempire + tassellazione per vano (calcolata dal backend).
export function useSpazi() {
  const [data, setData] = useState<Spazio[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const carica = useCallback(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    api
      .getSpazi()
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
