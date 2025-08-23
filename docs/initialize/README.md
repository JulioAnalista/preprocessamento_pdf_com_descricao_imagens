# Inicialização do Sistema (Modo Dev)

Guia didático para qualquer dev colocar o projeto online rapidamente.

Caminhos citados são relativos à raiz do projeto: `pdf_preproc/`.

---

## 1) Visão geral

- Backend FastAPI: `app.py`
- Extração PDF: `utils/pdf_extractor.py`
- Persistência (PostgreSQL): `db.py`
- Descrição de imagens (Azure OpenAI): `image_caption.py`
- UI estática (opcional): `static/`
- Artefatos públicos: `public/`

---

## 2) Pré‑requisitos

- Python 3.8+
- PostgreSQL acessível (local, Windows host ou remoto)
- (Opcional) Credenciais Azure OpenAI para `POST /api/caption/{file_id}`
- Ferramentas úteis: `psql`, `pg_isready`, `docker` (opcional)

> Em WSL: o Postgres pode estar no Windows. Veja a seção “WSL + Postgres no Windows”.

---

## 3) Variáveis de ambiente (.env)

Crie/edite `pdf_preproc/.env` com suas credenciais. Exemplo mínimo:

```bash
# Postgres
PGHOST=127.0.0.1
PGPORT=5432
PGDATABASE=pdf_preproc
PGUSER=postgres
PGPASSWORD=postgres

# Azure OpenAI (opcional para descrição de imagens)
AZURE_OPENAI_ENDPOINT="https://<seu-endpoint>.openai.azure.com"
AZURE_OPENAI_API_KEY="<sua-chave>"
AZURE_OPENAI_API_VERSION="2025-01-01-preview"
AZURE_OPENAI_CHAT_MODEL="gpt-4.1-nano"
AZURE_OPENAI_EMBEDDING_MODEL="text-embedding-3-large"
```

O app carrega automaticamente `.env` via `python-dotenv`.

---

## 4) Instalação de dependências

```bash
# (opcional) ambiente virtual
python -m venv .venv
source .venv/bin/activate

# backend e pdf
pip install fastapi uvicorn python-multipart python-dotenv
pip install pymupdf pdfplumber python-slugify

# banco
pip install psycopg2-binary

# IA
pip install openai  # SDK v1 usado pelo projeto

# opcionais
pip install easyocr weaviate-client python-arango
```

> `easyocr` é opcional: sem ele o OCR retorna vazio, mas a API funciona.

---

## 5) Inicializar o schema do banco

Cria as tabelas necessárias em PostgreSQL (idempotente):

```bash
python -c "from db import ensure_schema; ensure_schema(); print('Schema OK')"
```

Se falhar por conexão, valide as variáveis PG ou veja a seção WSL abaixo.

---

## 6) Rodar o servidor em modo dev

```bash
uvicorn app:app --reload --port 8099
```

- Docs interativas (Swagger): `http://127.0.0.1:8099/docs`
- Rota `/` usa `static/index.html` (se não existir, exibirá um aviso).

Para rodar em background e salvar logs:

```bash
nohup uvicorn app:app --host 0.0.0.0 --port 8099 --reload > logs/uvicorn_dev.log 2>&1 & echo $! > uvicorn.pid
```

Parar:

```bash
kill $(cat uvicorn.pid)
```

### 6.1) Start rápido com script (`tools/dev_start.sh`)

Para automatizar validação do `.env`, teste de conexão ao Postgres, aplicação do schema e start do servidor com logs:

```bash
tools/dev_start.sh
```

Opções úteis:

- `--host 0.0.0.0` e `--port 8099`
- `--wsl-detect-host` (em WSL, detecta IP do Windows e ajusta `PGHOST` em runtime)

Exemplos:

```bash
tools/dev_start.sh --host 0.0.0.0 --port 8099 --wsl-detect-host
```

Saída e controle:

- Logs: `logs/uvicorn_dev.log`
- PID do servidor: `uvicorn.pid`
- Parar servidor manualmente:
  ```bash
  kill $(cat uvicorn.pid)
  ```

---

## 7) Fluxo de teste rápido

1. `POST /api/upload` → envie um PDF, receba `file_id`
2. `POST /api/extract/{file_id}` → cria `uploads/<slug>/extraction.json` e popula `public/images/` e `public/tables/`
3. (Opcional) `POST /api/caption/{file_id}` → gera descrições (requer Azure OpenAI)
4. `GET /api/files` e `GET /api/file/{file_id}` → inspecionar no DB

Artefatos canônicos:
- Imagens únicas: `public/images/<hash>.png`
- Tabelas únicas: `public/tables/<hash>.json`
- ZIP por upload: `public/<slug>-<file_id>.zip`

---

## 8) WSL + Postgres no Windows

Quando o backend roda no WSL e o Postgres está no Windows:

1) Descobrir IP do host Windows a partir do WSL:
```bash
echo $(awk '/^nameserver /{print $2; exit}' /etc/resolv.conf)
```
2) Testar conectividade:
```bash
pg_isready -h <IP_HOST_WINDOWS> -p 5432 -d pdf_preproc -U postgres
```
3) Ajustar `.env` (`PGHOST=<IP_HOST_WINDOWS>`), se necessário.

No Windows (PostgreSQL):
- `postgresql.conf`: `listen_addresses = '*'` (ou `localhost` + IP desejado) e confirme `port`.
- `pg_hba.conf`: inclua regras `host all all 127.0.0.1/32 md5`, `host all all ::1/128 md5` e, se usar IP da rede/WSL, a sub-rede correspondente (ex.: `10.0.0.0/8`).
- Reinicie o serviço PostgreSQL (Services.msc) e libere a porta no Firewall do Windows (TCP 5432).

Se preferir, suba um Postgres temporário via Docker (preserva seu banco “oficial”):
```bash
docker run --name pdfpg -e POSTGRES_DB=pdf_preproc -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -p 5433:5432 -d postgres:16
# use PGHOST=127.0.0.1 e PGPORT=5433 no .env
```

---

## 9) Solução de problemas comuns

- **Conexão recusada no Postgres**: verifique `PGHOST/PORT`, permissões em `pg_hba.conf`, `listen_addresses`, firewall e se o serviço está ativo.
- **`pdfplumber` sem tabelas**: se não instalado, as tabelas vêm vazias (comportamento esperado).
- **Azure OpenAI**: confirme `AZURE_OPENAI_*` e cota. Endpoints `caption` falham sem credenciais válidas.
- **UI não carrega**: crie `static/index.html` ou use `/docs` para testar a API.

---

## 10) Componentes opcionais

- **Weaviate/Arango** (`indexers.py`):
  - Weaviate URL: `WEAVIATE_URL` (padrão `http://localhost:8080`)
  - Arango URL/DB: `ARANGO_URL`, `ARANGO_DB`, `ARANGO_USER`, `ARANGO_PASSWORD`
  - Rodar indexação:
    ```bash
    python indexers.py
    ```

- **Grafo de conhecimento** (`graph_kb.py`):
  - Usa embeddings Azure para criar nós/arestas no Postgres.
  - Exemplo de uso (dentro de um script):
    ```python
    from graph_kb import build_graph_for_extraction
    import json
    extraction = json.load(open('uploads/<slug>/extraction.json', 'r', encoding='utf-8'))
    build_graph_for_extraction(extraction)
    ```

---

## 11) Referências rápidas

- Servidor: `app.py`
- Banco/Schema: `db.py` (`ensure_schema()`)
- Extração: `utils/pdf_extractor.py`
- Descrição de imagens: `image_caption.py`
- Indexadores: `indexers.py`
- Documentação da API: `http://127.0.0.1:8099/docs`
