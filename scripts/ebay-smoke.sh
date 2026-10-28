#!/usr/bin/env bash
# Collaudo dal vivo di ebay-browse-pp-cli contro api.ebay.com.
#
# Finche' questo script non passa, la CLI e' STAMPATA ma non VERIFICATA:
# compilare e passare i test unitari non dice nulla sul fatto che il contratto
# regga contro il bersaglio vero.
#
#   bash scripts/ebay-smoke.sh
#
# Richiede EBAY_BROWSE_CLIENT_ID / EBAY_BROWSE_CLIENT_SECRET nel .env del nodo.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLI="${EBAY_CLI:-$HOME/go/bin/ebay-browse-pp-cli}"
MKT="EBAY_IT"
ok=0
ko=0

# Le credenziali vivono nel .env del nodo, che e' gitignored.
if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$ROOT/.env"
  set +a
fi

if [ -z "${EBAY_BROWSE_CLIENT_ID:-}" ] || [ -z "${EBAY_BROWSE_CLIENT_SECRET:-}" ]; then
  echo "MANCANO le credenziali: metti EBAY_BROWSE_CLIENT_ID e"
  echo "EBAY_BROWSE_CLIENT_SECRET in $ROOT/.env (vedi .env.example)."
  exit 2
fi

if [ ! -x "$CLI" ] && ! command -v "$CLI" >/dev/null 2>&1; then
  echo "CLI non trovata: $CLI"
  echo "Ricompilala: cd ~/printing-press/library/ebay-browse && go build -o \"$CLI\" ./cmd/ebay-browse-pp-cli"
  exit 2
fi

# Ogni caso e' (nome, attesa, comando). L'esito si legge SEMPRE da $? del
# comando, mai attraverso una pipe: dopo una pipe $? e' quello dell'ultimo
# elemento, non della CLI.
check() {
  local nome="$1"; shift
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  if [ $rc -eq 0 ]; then
    printf '  OK   %-42s %s\n' "$nome" "$(printf '%s' "$out" | head -c 90 | tr -d '\n')"
    ok=$((ok + 1))
  else
    printf '  FAIL %-42s exit=%d\n' "$nome" "$rc"
    printf '%s\n' "$out" | head -4 | sed 's/^/         /'
    ko=$((ko + 1))
  fi
  LAST_OUT="$out"
}

echo "== 1. Autenticazione =="
check "auth login (client_credentials)" "$CLI" auth login --agent
check "auth status" "$CLI" auth status --agent
check "doctor" "$CLI" doctor --agent

echo
echo "== 2. Ricerca (il caso d'uso del nodo) =="
check "search q=contenitore, marketplace IT" \
  "$CLI" item-summary search --q contenitore --x-ebay-c-marketplace-id "$MKT" --limit 5 --json

# Il conteggio e' la verifica vera: un comando che esce 0 con zero risultati
# non prova nulla. Sul caso Maury's fu esattamente cosi' che `--all` tronco'
# in silenzio.
n=$(printf '%s' "${LAST_OUT:-}" | python -c "
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(-1); raise SystemExit
r = d.get('results') or d.get('itemSummaries') or (d if isinstance(d, list) else [])
print(len(r))
" 2>/dev/null || echo -1)
if [ "${n:-0}" -ge 1 ] 2>/dev/null; then
  echo "  OK   risultati ricevuti: $n"; ok=$((ok + 1))
else
  echo "  FAIL nessun risultato (n=$n) — comando riuscito ma vuoto"; ko=$((ko + 1))
fi

echo
echo "== 3. Paginazione: --all deve superare una pagina =="
tot=$("$CLI" item-summary search --q scatola --x-ebay-c-marketplace-id "$MKT" --all --json 2>/dev/null | python -c "
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(0); raise SystemExit
r = d.get('results') or d.get('itemSummaries') or (d if isinstance(d, list) else [])
print(len(r))
" 2>/dev/null || echo 0)
if [ "${tot:-0}" -gt 100 ] 2>/dev/null; then
  echo "  OK   --all ha superato la prima pagina: $tot risultati"; ok=$((ok + 1))
else
  echo "  ATTENZIONE  --all ha reso $tot risultati (<=100): possibile troncamento"
  echo "              e' il difetto upstream #3989 — verificare defaultPageSize"
  ko=$((ko + 1))
fi

echo
echo "== 4. Ricerca per EAN (l'aggancio con il gtin di Maury's) =="
check "search --gtin" \
  "$CLI" item-summary search --gtin 8004399322349 --x-ebay-c-marketplace-id "$MKT" --json

echo
echo "== 5. Aggancio a fit =="
if "$CLI" item-summary search --q "scatola contenitore" --x-ebay-c-marketplace-id "$MKT" --limit 50 --json 2>/dev/null \
     | python "$ROOT/scripts/shopcli.py" fit --from - --shop ebay --vano C2=38x84x18 > /tmp/ebay-fit.out 2>&1; then
  head -3 /tmp/ebay-fit.out | sed 's/^/  /'
  ok=$((ok + 1))
else
  echo "  FAIL fit non ha prodotto output"; sed 's/^/         /' /tmp/ebay-fit.out | head -4; ko=$((ko + 1))
fi

echo
echo "=============================="
echo " passati: $ok    falliti: $ko"
[ "$ko" -eq 0 ] && echo " COLLAUDO OK — la CLI e' verificata dal vivo." \
               || echo " Collaudo NON superato: la CLI resta 'stampata', non verificata."
exit $([ "$ko" -eq 0 ] && echo 0 || echo 1)
