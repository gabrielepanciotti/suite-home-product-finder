# HomeProductFinder - launcher (backend FastAPI :10008 + frontend Vite :3342)
# Uso:  .\menu.ps1            # dev: avvia backend + frontend (no Docker)
#       .\menu.ps1 -Build     # rigenera i JSON confronto (immagini incluse)
#       .\menu.ps1 -Docker    # prod: pre-build @suite + docker compose up -d
param([switch]$Build, [switch]$Docker)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"

if ($Docker) {
    # deploy/docker-compose.yml è suite-managed; l'override (DATABASE_URL + rete del
    # DB del nodo) è locale e va passato esplicitamente con un secondo -f.
    $compose = Join-Path $root "deploy/docker-compose.yml"
    $override = Join-Path $root "deploy/docker-compose.override.yml"
    # --env-file: i compose stanno in deploy/, quindi Compose cercherebbe le
    # variabili in deploy/.env, che non esiste — e il base file pretende
    # DB_PASSWORD con ${DB_PASSWORD:?}, quindi si ferma prima di partire. Il .env
    # del nodo sta nella root: glielo si indica a mano. (`env_file: ../.env` nel
    # compose riguarda solo le variabili DENTRO al container, non queste.)
    $envFile = Join-Path $root ".env"
    Write-Host "Avvio DB del nodo (docker compose -f docker-compose.db.yml up -d)..." -ForegroundColor Cyan
    docker compose --env-file $envFile -f (Join-Path $root "deploy/docker-compose.db.yml") up -d | Out-Null
    Write-Host "Pre-build tarball @suite/design-system + vendor backend-core..." -ForegroundColor Cyan
    bash (Join-Path $root "deploy/prebuild.sh")
    if ($LASTEXITCODE -ne 0) { throw "deploy/prebuild fallito" }
    Write-Host "docker compose build + up -d..." -ForegroundColor Cyan
    docker compose --env-file $envFile -f $compose -f $override build
    docker compose --env-file $envFile -f $compose -f $override up -d
    Write-Host "Backend  -> http://localhost:10008" -ForegroundColor Green
    Write-Host "Frontend -> http://localhost:3342" -ForegroundColor Green
    return
}

if (-not (Test-Path $py)) {
    Write-Host "Creo il venv (.venv, Python 3.13)..." -ForegroundColor Yellow
    py -3.13 -m venv (Join-Path $root ".venv")
    & $py -m pip install -r (Join-Path $root "backend\requirements.txt") -q
    # suite_backend_core: shared Life package, linked editable from the sibling repo (issue #2).
    & $py -m pip install -e (Join-Path $root "..\Life\packages\backend-core") -q
}

if ($Build) {
    Write-Host "Rigenero i confronti JSON + immagini..." -ForegroundColor Cyan
    & $py (Join-Path $root "scripts\build_confronti_json.py")
    return
}

# Dev: solo il DB del nodo gira su Docker (Postgres 16, porta registry 11120).
# Additivo: se .env non ha DATABASE_URL il backend resta in modalita' solo-JSON.
$dbCompose = Join-Path $root "deploy/docker-compose.db.yml"
Write-Host "Avvio DB del nodo (docker compose -f docker-compose.db.yml up -d)..." -ForegroundColor Cyan
docker compose -f $dbCompose up -d | Out-Null
Write-Host "DB       -> postgres://localhost:11120/homeproductfinder" -ForegroundColor Green

Write-Host "Backend  -> http://localhost:10008  (API)" -ForegroundColor Green
Write-Host "Frontend -> http://localhost:3342  (app)" -ForegroundColor Green

# Backend in una nuova finestra (package in backend/, lanciato con python -m)
$backendDir = Join-Path $root "backend"
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "`$env:UVICORN_RELOAD='1'; `$env:PORT='10008'; & '$py' -m home_product_finder_backend"
) -WorkingDirectory $backendDir

# Frontend nella finestra corrente
Set-Location (Join-Path $root "frontend")
if (-not (Test-Path "node_modules")) { npm install }
npm run dev
