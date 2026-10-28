import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import type { NodeOverviewData } from "../types";

const REFETCH_MS = 30_000;

/**
 * Live "scheda nodo" — polls `/api/overview` every 30s and refetches on
 * window focus, so the card always reflects current identity/functions/DB
 * counts without a manual refresh.
 */
export function useNodeOverview() {
  const [data, setData] = useState<NodeOverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const payload = await api.getOverview();
      setData(payload);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "errore di rete");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, REFETCH_MS);
    window.addEventListener("focus", load);
    return () => {
      clearInterval(timer);
      window.removeEventListener("focus", load);
    };
  }, [load]);

  return { data, loading, error, refetch: load };
}
