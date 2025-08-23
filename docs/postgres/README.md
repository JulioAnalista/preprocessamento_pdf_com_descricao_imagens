# PostgreSQL no WSL (Ubuntu/Debian) – Instalação e Configuração

Este guia coloca um servidor PostgreSQL local no WSL com as credenciais usadas pelo projeto.

Valores padrão esperados pelo `.env` em `pdf_preproc/`:

```bash
PGHOST=127.0.0.1
PGPORT=5432
PGDATABASE=pdf_preproc
PGUSER=postgres
PGPASSWORD=postgres
```

---

## 1) Requisitos

- WSL2 com Ubuntu/Debian
- Acesso sudo
- Porta 5432 livre no WSL

---

## 2) Instalação rápida (automática)

Use o script preparado no repositório. Ele:
- Instala PostgreSQL
- Ajusta `listen_addresses` para `127.0.0.1`
- Configura autenticação `md5` local
- Define a senha do usuário `postgres`
- Cria o banco `pdf_preproc` (se não existir)
- Faz testes de conexão

```bash
# a partir da raiz do projeto
bash tools/setup_postgres_wsl.sh
```

> O script usa `sudo` e reinicia o serviço PostgreSQL.

---

## 3) Instalação manual (passo a passo)

Caso prefira executar manualmente:

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
```

Descubra o diretório da instância (Ubuntu usa `/etc/postgresql/<versão>/main`):

```bash
echo /etc/postgresql/*/main
```

Edite `postgresql.conf` e garanta:

```conf
listen_addresses = '127.0.0.1'
port = 5432
```

Edite `pg_hba.conf` e garanta autenticação `md5` local:

```conf
# Local IPv4
host    all             all             127.0.0.1/32            md5
# Local IPv6 (opcional)
host    all             all             ::1/128                 md5
```

Reinicie o serviço:

```bash
sudo systemctl restart postgresql
sudo systemctl status postgresql --no-pager -l
```

Defina a senha do superusuário `postgres` e crie o banco:

```bash
sudo -u postgres psql -tAc "ALTER USER postgres WITH PASSWORD 'postgres';"
sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='pdf_preproc'\gset" && \
  if [[ "${?}" -eq 0 ]]; then echo "db check feito"; fi
sudo -u postgres psql -tAc "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname='pdf_preproc') THEN CREATE DATABASE pdf_preproc; END IF; END $$;"
```

Teste a conexão como cliente normal:

```bash
PGPASSWORD=postgres psql -h 127.0.0.1 -p 5432 -U postgres -d pdf_preproc -c "select version();"
```

---

## 4) Ajustar `.env`

Em `pdf_preproc/.env` (ou crie se não existe):

```bash
PGHOST=127.0.0.1
PGPORT=5432
PGDATABASE=pdf_preproc
PGUSER=postgres
PGPASSWORD=postgres
```

---

## 5) Aplicar schema e rodar o app

Aplicar o schema do projeto (idempotente):

```bash
python -c "from db import ensure_schema; ensure_schema(); print('Schema OK')"
```

Subir o servidor de desenvolvimento:

```bash
tools/dev_start.sh --host 0.0.0.0 --port 8099
# ou simplesmente
# uvicorn app:app --reload --port 8099
```

Docs da API: `http://127.0.0.1:8099/docs`

---

## 6) Testes rápidos

- Conectividade:
  ```bash
  pg_isready -h 127.0.0.1 -p 5432 -d pdf_preproc -U postgres
  PGPASSWORD=postgres psql -h 127.0.0.1 -U postgres -d pdf_preproc -c "select current_database(), current_user;"
  ```
- Fluxo do app:
  - `POST /api/upload` → obter `file_id`
  - `POST /api/extract/{file_id}` → gerar artefatos
  - `POST /api/caption/{file_id}` → requer Azure para descrever imagens

---

## 7) Troubleshooting

- Porta 5432 ocupada: altere `port` em `postgresql.conf` e atualize o `.env`.
- `psql: FATAL: password authentication failed`: confirme senha do usuário `postgres`.
- `could not connect to server`: verifique se o serviço está ativo (`systemctl status postgresql`) e `listen_addresses`.
- Logs do servidor PostgreSQL (Ubuntu): `/var/log/postgresql/postgresql-*.log`.

---

## 8) Remoção (opcional)

```bash
sudo systemctl stop postgresql
sudo apt purge -y postgresql*
sudo rm -rf /etc/postgresql /var/lib/postgresql /var/log/postgresql
sudo apt autoremove -y
```
