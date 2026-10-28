const VOCI: { simbolo: string; titolo: string; testo: string }[] = [
  {
    simbolo: "★ / ✕",
    titolo: "Preferite e scartate",
    testo:
      "La stella tiene una scatola in cima alla tabella (e la salva dai filtri); la ✕ la manda in fondo, sbiadita, senza cancellarla. I due verdetti si salvano nel vault del nodo, quindi restano al prossimo giro e valgono anche dall'altro PC.",
  },
  {
    simbolo: "top",
    titolo: "Soluzione non dominata",
    testo:
      "Nessun'altra riga di quella classifica riempie di più, costa meno e usa meno pezzi tutte e tre le cose insieme. Non è «la migliore»: è una di quelle fra cui la scelta è un compromesso vero.",
  },
  {
    simbolo: "40×30×h22",
    titolo: "Misure della scatola",
    testo:
      "Sempre nello stesso ordine: larghezza × profondità × altezza, in centimetri, misure esterne. L'ultimo numero porta la h proprio per non confonderlo con gli altri.",
  },
  {
    simbolo: "8×13 × 2 liv",
    titolo: "Disposizione nel vano",
    testo:
      "Numeri di scatole, non centimetri: 8 affiancate in larghezza, 13 in profondità, su 2 livelli sovrapposti — in tutto 8×13×2 = 208 pezzi, il numero della colonna Pz.",
  },
  {
    simbolo: "Area vs Volume",
    titolo: "Due riempimenti diversi",
    testo:
      "Area = quanto pavimento del vano è coperto. Volume = quanto spazio è occupato davvero, altezza compresa. Scatole basse che coprono tutto il fondo fanno 100% di area e magari 50% di volume: sopra resta aria.",
  },
  {
    simbolo: "Passo",
    titolo: "Solo scaffali regolabili",
    testo:
      "Dove fissare i ripiani: altezza della scatola più 3 cm fra spessore del ripiano e gioco per infilarla. Sullo scaffale l'altezza del livello non è un vincolo, è una scelta.",
  },
  {
    simbolo: "✓ ✗ ?",
    titolo: "Coperchio e materiali",
    testo:
      "Ricavati dal nome commerciale del prodotto, l'unica scheda tecnica che i negozi espongono. «?» vuol dire che il nome non lo dice — non che il coperchio manca.",
  },
  {
    simbolo: "↑ ↓ ¹ ²",
    titolo: "Ordinamento",
    testo:
      "Clic su un'intestazione ordina per quella colonna; shift+clic la aggiunge come criterio successivo (a parità del primo decide il secondo, e così via). L'ordine vale per tutti i vani, così si confrontano con lo stesso metro.",
  },
];

/** Come si legge la tabella: tutto ciò che un simbolo da solo non dice. */
export function Legenda() {
  return (
    <div className="mt-4 grid gap-x-6 gap-y-3.5 rounded-2xl border border-border bg-surface p-5 sm:grid-cols-2 xl:grid-cols-4">
      {VOCI.map((v) => (
        <div key={v.titolo}>
          <div className="mb-0.5 flex items-baseline gap-2">
            <span className="rounded-md bg-surface-2 px-1.5 py-0.5 font-mono text-xs font-bold text-info">
              {v.simbolo}
            </span>
            <span className="text-sm font-bold">{v.titolo}</span>
          </div>
          <p className="text-sm leading-relaxed text-muted">{v.testo}</p>
        </div>
      ))}
    </div>
  );
}
