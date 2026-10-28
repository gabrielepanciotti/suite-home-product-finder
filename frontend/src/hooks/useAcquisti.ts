import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import type { Acquisto } from "../types";

export function useAcquisti() {
  const [data, setData] = useState<Acquisto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const carica = useCallback(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    api
      .getPurchases()
      .then((items) => alive && setData(items))
      .catch((reason) => alive && setError(String(reason?.message ?? reason)))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => carica(), [carica]);

  return { data, loading, error, ricarica: carica };
}
