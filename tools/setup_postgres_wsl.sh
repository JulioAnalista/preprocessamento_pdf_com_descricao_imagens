#!/usr/bin/env bash
# Instala e configura PostgreSQL no WSL (Ubuntu/Debian) para uso local pelo projeto.
# - Instala pacotes
# - Ajusta listen_addresses/port
# - Configura pg_hba para md5 local
# - Define senha do usuário postgres
# - Cria o banco pdf_preproc
# - Testa conectividade
# Atenção: requer sudo e reinicia o serviço PostgreSQL.

set -euo pipefail

# Parâmetros padrão do projeto
PGHOST_DEFAULT="127.0.0.1"
PGPORT_DEFAULT="5432"
PGDATABASE_DEFAULT="pdf_preproc"
PGUSER_DEFAULT="postgres"
PGPASSWORD_DEFAULT="postgres"

info() { echo -e "\033[1;34m[INFO]\033[0m $*"; }
warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; }
err()  { echo -e "\033[1;31m[ERRO]\033[0m $*"; }
need_cmd() { command -v "$1" >/dev/null 2>&1 || { err "Comando '$1' não encontrado"; exit 1; }; }

need_cmd sudo

info "Atualizando índices de pacotes..."
sudo apt update -y

info "Instalando PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib

# Detectar diretório de configuração; se não houver cluster, criar um padrão (17 main)
CONF_DIR=""
for d in /etc/postgresql/*/main; do
  if [[ -d "$d" ]]; then CONF_DIR="$d"; break; fi
done
if [[ -z "$CONF_DIR" ]]; then
  warn "Nenhum cluster padrão encontrado. Criando cluster 17/main..."
  if command -v pg_createcluster >/dev/null 2>&1; then
    sudo pg_createcluster 17 main --start
  else
    err "pg_createcluster não encontrado. Certifique-se de que postgresql-common está instalado."
    exit 2
  fi
  for d in /etc/postgresql/*/main; do
    if [[ -d "$d" ]]; then CONF_DIR="$d"; break; fi
  done
fi
if [[ -z "$CONF_DIR" ]]; then
  err "Não foi possível localizar diretório de configuração do PostgreSQL (esperado /etc/postgresql/*/main)"
  exit 2
fi
POSTGRESQL_CONF="$CONF_DIR/postgresql.conf"
PG_HBA_CONF="$CONF_DIR/pg_hba.conf"

info "Ajustando $POSTGRESQL_CONF (listen_addresses, port)"
sudo sed -i "s/^#*\s*listen_addresses\s*=.*/listen_addresses = '${PGHOST_DEFAULT}'/" "$POSTGRESQL_CONF" || true
sudo sed -i "s/^#*\s*port\s*=.*/port = ${PGPORT_DEFAULT}/" "$POSTGRESQL_CONF" || true

info "Configurando $PG_HBA_CONF (md5 para 127.0.0.1 e ::1)"
if ! grep -qE "^host\s+all\s+all\s+127.0.0.1/32\s+md5" "$PG_HBA_CONF"; then
  echo "host    all             all             127.0.0.1/32            md5" | sudo tee -a "$PG_HBA_CONF" >/dev/null
fi
if ! grep -qE "^host\s+all\s+all\s+::1/128\s+md5" "$PG_HBA_CONF"; then
  echo "host    all             all             ::1/128                 md5" | sudo tee -a "$PG_HBA_CONF" >/dev/null
fi

info "Reiniciando serviço PostgreSQL..."
if systemctl is-system-running >/dev/null 2>&1; then
  sudo systemctl restart postgresql
  sleep 1
  sudo systemctl status postgresql --no-pager -l | sed -n '1,10p' || true
else
  # Fallback em ambientes sem systemd completamente funcional
  VERSION_DIR=$(basename "$(dirname "$CONF_DIR")")
  warn "Systemd indisponível; usando pg_ctlcluster ${VERSION_DIR} main restart"
  sudo pg_ctlcluster "$VERSION_DIR" main restart
fi

info "Definindo senha do usuário postgres..."
sudo -u postgres psql -tAc "ALTER USER ${PGUSER_DEFAULT} WITH PASSWORD '${PGPASSWORD_DEFAULT}';"

info "Criando banco ${PGDATABASE_DEFAULT} (se não existir)..."
sudo -u postgres psql -tAc "DO \$\$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname='${PGDATABASE_DEFAULT}') THEN CREATE DATABASE ${PGDATABASE_DEFAULT}; END IF; END \$\$;"

info "Testando conectividade como cliente normal..."
need_cmd pg_isready
pg_isready -h "$PGHOST_DEFAULT" -p "$PGPORT_DEFAULT" -d "$PGDATABASE_DEFAULT" -U "$PGUSER_DEFAULT" || true
PGPASSWORD="$PGPASSWORD_DEFAULT" psql -h "$PGHOST_DEFAULT" -p "$PGPORT_DEFAULT" -U "$PGUSER_DEFAULT" -d "$PGDATABASE_DEFAULT" -c "select version();" -tA | sed -n '1p'

info "Tudo pronto. Ajuste/valide seu .env se necessário e aplique o schema:"
echo "python -c \"from db import ensure_schema; ensure_schema(); print('Schema OK')\""
