#!/usr/bin/env bash
# Dev starter: valida .env, testa Postgres, aplica schema e inicia Uvicorn com logs.
# Uso:
#   tools/dev_start.sh [--port 8099] [--host 0.0.0.0] [--wsl-detect-host]
# Exemplos:
#   tools/dev_start.sh
#   tools/dev_start.sh --port 8099 --host 0.0.0.0 --wsl-detect-host

set -euo pipefail

PORT=8099
HOST="0.0.0.0"
WSL_DETECT_HOST=false
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$PROJECT_ROOT/uvicorn.pid"
ENV_FILE="$PROJECT_ROOT/.env"
APP_IMPORT="app:app"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      PORT="$2"; shift 2 ;;
    --host)
      HOST="$2"; shift 2 ;;
    --wsl-detect-host)
      WSL_DETECT_HOST=true; shift ;;
    *) echo "[WARN] Argumento desconhecido: $1"; shift ;;
  esac
done

info() { echo -e "\033[1;34m[INFO]\033[0m $*"; }
warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; }
err()  { echo -e "\033[1;31m[ERRO]\033[0m $*"; }

need_cmd() { command -v "$1" >/dev/null 2>&1 || { err "Comando '$1' não encontrado"; exit 1; }; }

# 1) Validar .env
if [[ ! -f "$ENV_FILE" ]]; then
  err "Arquivo .env não encontrado em $ENV_FILE"
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${PGHOST:=127.0.0.1}" ; : "${PGPORT:=5432}" ; : "${PGDATABASE:=pdf_preproc}" ; : "${PGUSER:=postgres}" ; : "${PGPASSWORD:=postgres}"

info "PGHOST=$PGHOST PGPORT=$PGPORT PGDATABASE=$PGDATABASE PGUSER=$PGUSER"

# 2) WSL: detectar host Windows (opcional)
if [[ "$WSL_DETECT_HOST" == true ]]; then
  if grep -qiE 'microsoft|WSL' /proc/version 2>/dev/null; then
    HOST_IP=$(awk '/^nameserver /{print $2; exit}' /etc/resolv.conf || true)
    if [[ -n "${HOST_IP:-}" ]]; then
      warn "WSL detectado. Ajustando PGHOST -> $HOST_IP (antes: $PGHOST)"
      export PGHOST="$HOST_IP"
    else
      warn "Não foi possível detectar IP do host Windows automaticamente."
    fi
  else
    info "Não parece ser WSL; ignorando --wsl-detect-host."
  fi
fi

# 3) Testar conexão ao Postgres
need_cmd pg_isready
info "Testando Postgres em $PGHOST:$PGPORT ..."
if ! pg_isready -h "$PGHOST" -p "$PGPORT" -d "$PGDATABASE" -U "$PGUSER" >/dev/null 2>&1; then
  warn "pg_isready falhou; tentando psql..."
  if ! PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "select 1;" >/dev/null 2>&1; then
    err "Não foi possível conectar ao Postgres ($PGHOST:$PGPORT / db=$PGDATABASE user=$PGUSER)."
    err "Dicas: verifique listen_addresses/pg_hba.conf/firewall ou use --wsl-detect-host."
    exit 2
  fi
fi
info "Conexão com Postgres OK."

# 4) Aplicar schema (idempotente)
need_cmd python
info "Aplicando schema do banco..."
python - <<'PY'
from db import ensure_schema
ensure_schema()
print('Schema OK')
PY

# 5) Iniciar uvicorn com logs
need_cmd uvicorn
mkdir -p "$LOG_DIR"
if [[ -f "$PID_FILE" ]] && ps -p "$(cat "$PID_FILE" 2>/dev/null)" >/dev/null 2>&1; then
  warn "Uvicorn já parece rodando (PID $(cat "$PID_FILE")), tentando parar..."
  kill "$(cat "$PID_FILE")" || true
  sleep 1
fi

LOG_FILE="$LOG_DIR/uvicorn_dev.log"
info "Iniciando servidor: uvicorn $APP_IMPORT --host $HOST --port $PORT --reload"
nohup uvicorn "$APP_IMPORT" --host "$HOST" --port "$PORT" --reload > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

sleep 1
if ps -p "$(cat "$PID_FILE")" >/dev/null 2>&1; then
  info "Servidor iniciado (PID $(cat "$PID_FILE")). Logs em: $LOG_FILE"
  info "Docs: http://127.0.0.1:$PORT/docs"
else
  err "Falha ao iniciar o servidor. Consulte logs em $LOG_FILE"
  exit 3
fi
