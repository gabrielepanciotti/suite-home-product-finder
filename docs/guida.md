# Guida d'uso — Casa — Prodotti (HomeProductFinder)

Per chi lo usa, non per chi lo sviluppa.

## Cosa fa
Ti aiuta a scegliere e comprare oggetti per la casa (contenitori, mobili, organizer,
elettrodomestici): li cataloga dalle foto, confronta i prezzi al **totale** (prodotto +
spedizione + dogana) e calcola quali scatole entrano in un vano o contengono i tuoi oggetti.
Non ordina e non paga mai niente da solo.

## Come si apre
| Dove | Indirizzo |
|---|---|
| Docker example | http://localhost:3342 · API http://localhost:10008 |
| Local development | http://localhost:3342 · API http://localhost:10008 |
| Telegram | gruppo «🏠 Casa — Prodotti» |

## Casi d'uso
1. **Catalogare un prodotto visto in giro** — manda la foto nel gruppo Telegram. L'agente lo
   riconosce e crea una scheda in `vault/prodotti/<categoria>/` con stato `visto`.
2. **Trovare il prezzo migliore** — nel gruppo scrivi `/prodotto <nome>`. Ricevi il ventaglio dei
   negozi IT/UE con il totale, e un avviso dogana per quelli extra-UE.
3. **Vedere il catalogo** — `/catalogo [categoria]` nel gruppo: elenco schede con stato e prezzo.
4. **Scegliere da un confronto** — apri l'app, clicca la card del confronto (es. «3 prodotti»),
   segna cosa comprare: il contatore «N da comprare» compare sulla card e la scelta resta nel vault.
5. **Riempire un vano** — pulsante **Spazi da riempire**: per ogni vano la classifica delle scatole
   che ci stanno, quante ne entrano e quanto costano. Puoi tenere o scartare le proposte.
6. **In cosa lo metto** — pulsante omonimo: inserisci le misure di un oggetto (cm), quanti sono e se
   stanno in piedi o si impilano; ottieni le scatole del catalogo che li contengono, filtrabili per
   materiale. Per i barattoli c'è la preselezione per marca (es. Bormioli).
7. **Catalogo scatole** — tutte le scatole note dai negozi (IKEA, Action, Maury's, Amazon), con misure e prezzo.
8. **Scheda nodo** — stato del nodo e dei suoi collegamenti.

## Servizi LLM
Il nodo **non chiama modelli dal proprio codice**: foto, `/prodotto` e `/catalogo` sono gestiti dalla
sessione del Coordinator, che segue i playbook in `.claude/commands/`. Il modello di quella sessione
si cambia nella configurazione del Coordinator / Life (`<istanza>/config/llm-routing.json`), non qui.

## Problemi comuni
- **La pagina resta su «Carico…» o dà «Errore»** — il backend non risponde: controlla
  http://localhost:10008/api/health (deve dire `ok`) e che i container siano in esecuzione.
- **«In cosa lo metto» mostra solo scatoloni di cartone** — clicca sul materiale «cartone» finché
  diventa arancione (non lo voglio). Se invece non trova nulla, lascia acceso «anche materiale
  ignoto»: molti nomi di prodotto non dicono il materiale.
- **La foto nel gruppo non produce una scheda** — il Coordinator dev'essere attivo e il bot admin del gruppo.
- **Prezzi Amazon assenti** — Amazon a volte blocca le richieste; riprova più tardi.
