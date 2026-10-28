import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import type { Confronto, Gruppo } from "../types";

// Carica un confronto e gestisce la selezione (id -> quantità).
// "per-gruppo": al massimo un prodotto per gruppo. "multipla": quanti vuoi.
export function useConfronto(slug: string) {
  const [data, setData] = useState<Confronto | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sel, setSel] = useState<Record<string, number>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const carica = useCallback(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    api
      .getConfronto(slug)
      .then((c) => {
        if (!alive) return;
        setData(c);
        // pre-seleziona ciò che è già da-comprare
        const init: Record<string, number> = {};
        for (const g of c.gruppi)
          for (const p of g.prodotti)
            if (p.stato === "da-comprare") init[p.id] = p.quantita || 1;
        setSel(init);
      })
      .catch((e) => alive && setError(String(e.message ?? e)))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [slug]);

  useEffect(() => carica(), [carica]);

  const groupOf = useMemo(() => {
    const m: Record<string, Gruppo> = {};
    if (data)
      for (const g of data.gruppi) for (const p of g.prodotti) m[p.id] = g;
    return m;
  }, [data]);

  const toggle = useCallback(
    (id: string) => {
      if (!data) return;
      setSaved(false);
      setSel((prev) => {
        const next = { ...prev };
        if (next[id]) {
          delete next[id];
          return next;
        }
        if (data.selezione === "per-gruppo") {
          // togli gli altri dello stesso gruppo
          const g = groupOf[id];
          for (const p of g.prodotti) delete next[p.id];
        }
        next[id] = 1;
        return next;
      });
    },
    [data, groupOf],
  );

  const setQty = useCallback((id: string, qty: number) => {
    setSaved(false);
    setSel((prev) => {
      if (!prev[id]) return prev;
      const q = Math.max(1, qty);
      return { ...prev, [id]: q };
    });
  }, []);

  const salva = useCallback(async () => {
    setSaving(true);
    try {
      const updated = await api.salvaScelta(slug, sel);
      setData(updated);
      setSaved(true);
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setSaving(false);
    }
  }, [slug, sel]);

  return {
    data,
    loading,
    error,
    sel,
    toggle,
    setQty,
    salva,
    saving,
    saved,
    ricarica: carica,
  };
}
