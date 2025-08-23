import os
import hashlib
import json
import psycopg2
from contextlib import contextmanager
from typing import Optional

PGHOST = os.getenv("PGHOST", os.getenv("POSTGRES_HOST", "127.0.0.1"))
PGPORT = int(os.getenv("PGPORT", os.getenv("POSTGRES_PORT", "5432")))
PGDATABASE = os.getenv("PGDATABASE", os.getenv("POSTGRES_DB", "pdf_preproc"))
PGUSER = os.getenv("PGUSER", os.getenv("POSTGRES_USER", "postgres"))
PGPASSWORD = os.getenv("PGPASSWORD", os.getenv("POSTGRES_PASSWORD", "postgres"))

DSN = f"host={PGHOST} port={PGPORT} dbname={PGDATABASE} user={PGUSER} password={PGPASSWORD}"

@contextmanager
def get_conn():
    conn = psycopg2.connect(DSN)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

SCHEMA_SQL = """
create table if not exists pdfs (
  hash char(64) primary key,
  size_bytes bigint,
  pages int,
  created_at timestamptz default now()
);

create table if not exists pdf_files (
  file_id uuid primary key,
  pdf_hash char(64) references pdfs(hash),
  original_filename text,
  stored_path text not null,
  created_at timestamptz default now()
);

create table if not exists images (
  hash char(64) primary key,
  width int,
  height int,
  mime text,
  size_bytes int,
  storage_path text not null,
  created_at timestamptz default now()
);

create table if not exists tables (
  hash char(64) primary key,
  rows_count int,
  cols_count int,
  storage_path text not null,
  created_at timestamptz default now()
);

create table if not exists pdf_image_refs (
  file_id uuid,
  page int,
  img_index int,
  image_hash char(64) references images(hash),
  created_at timestamptz default now(),
  primary key (file_id, page, img_index)
);

create table if not exists pdf_table_refs (
  file_id uuid,
  page int,
  table_index int,
  table_hash char(64) references tables(hash),
  created_at timestamptz default now(),
  primary key (file_id, page, table_index)
);

create table if not exists extractions (
  file_id uuid primary key,
  output_dir text,
  extraction_json_path text,
  zip_url text,
  extracted_at timestamptz default now()
);

-- Graph KB schema
create table if not exists graphs (
  graph_id char(64) primary key, -- use pdf_hash
  name text,
  source_file_id uuid,
  created_at timestamptz default now()
);

create table if not exists graph_nodes (
  id bigserial primary key,
  graph_id char(64) references graphs(graph_id),
  label text,
  type text,
  properties jsonb default '{}'::jsonb,
  embedding jsonb
);

create table if not exists graph_edges (
  id bigserial primary key,
  graph_id char(64) references graphs(graph_id),
  src bigint references graph_nodes(id),
  dst bigint references graph_nodes(id),
  relation text,
  properties jsonb default '{}'::jsonb
);

create index if not exists idx_graph_nodes_graph on graph_nodes(graph_id);
create index if not exists idx_graph_edges_graph on graph_edges(graph_id);

-- Image descriptions
create table if not exists image_descriptions (
  image_hash char(64) primary key references images(hash),
  model text,
  description text,
  metadata jsonb default '{}'::jsonb,
  ocr_text text,
  created_at timestamptz default now()
);

create index if not exists idx_pdf_files_pdf_hash on pdf_files(pdf_hash);
create index if not exists idx_pdf_image_refs_hash on pdf_image_refs(image_hash);
create index if not exists idx_pdf_table_refs_hash on pdf_table_refs(table_hash);
"""

def ensure_schema():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
            # Migração leve: garantir colunas em image_descriptions
            cur.execute("ALTER TABLE IF EXISTS image_descriptions ADD COLUMN IF NOT EXISTS metadata jsonb DEFAULT '{}'::jsonb")
            cur.execute("ALTER TABLE IF EXISTS image_descriptions ADD COLUMN IF NOT EXISTS ocr_text text")

# Upserts / inserts

def upsert_pdf(pdf_hash: str, size_bytes: int, pages: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into pdfs(hash, size_bytes, pages)
                values (%s, %s, %s)
                on conflict (hash) do update set size_bytes = excluded.size_bytes, pages = excluded.pages
                """,
                (pdf_hash, size_bytes, pages),
            )

def upsert_pdf_file(file_id: str, pdf_hash: str, original_filename: str, stored_path: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into pdf_files(file_id, pdf_hash, original_filename, stored_path)
                values (%s, %s, %s, %s)
                on conflict (file_id) do update set pdf_hash=excluded.pdf_hash, original_filename=excluded.original_filename, stored_path=excluded.stored_path
                """,
                (file_id, pdf_hash, original_filename, stored_path),
            )

def upsert_image(image_hash: str, width: int, height: int, mime: str, size_bytes: int, storage_path: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into images(hash, width, height, mime, size_bytes, storage_path)
                values (%s, %s, %s, %s, %s, %s)
                on conflict (hash) do nothing
                """,
                (image_hash, width, height, mime, size_bytes, storage_path),
            )

def upsert_table(table_hash: str, rows_count: int, cols_count: int, storage_path: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into tables(hash, rows_count, cols_count, storage_path)
                values (%s, %s, %s, %s)
                on conflict (hash) do nothing
                """,
                (table_hash, rows_count, cols_count, storage_path),
            )

def insert_pdf_image_ref(file_id: str, page: int, img_index: int, image_hash: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into pdf_image_refs(file_id, page, img_index, image_hash)
                values (%s, %s, %s, %s)
                on conflict do nothing
                """,
                (file_id, page, img_index, image_hash),
            )

def insert_pdf_table_ref(file_id: str, page: int, table_index: int, table_hash: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into pdf_table_refs(file_id, page, table_index, table_hash)
                values (%s, %s, %s, %s)
                on conflict do nothing
                """,
                (file_id, page, table_index, table_hash),
            )

def insert_extraction(file_id: str, output_dir: str, extraction_json_path: str, zip_url: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into extractions(file_id, output_dir, extraction_json_path, zip_url)
                values (%s, %s, %s, %s)
                on conflict (file_id) do update set output_dir=excluded.output_dir, extraction_json_path=excluded.extraction_json_path, zip_url=excluded.zip_url
                """,
                (file_id, output_dir, extraction_json_path, zip_url),
            )

def upsert_image_description(image_hash: str, model: str, description: str, metadata: dict | None = None, ocr_text: str | None = None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into image_descriptions(image_hash, model, description, metadata, ocr_text)
                values (%s, %s, %s, %s, %s)
                on conflict (image_hash) do update set model=excluded.model, description=excluded.description, metadata=excluded.metadata, ocr_text=excluded.ocr_text
                """,
                (image_hash, model, description, json.dumps(metadata or {}), ocr_text),
            )



def get_image_description(image_hash: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("select model, description, metadata, ocr_text from image_descriptions where image_hash=%s", (image_hash,))
            row = cur.fetchone()
            if not row:
                return None
            return {"model": row[0], "description": row[1], "metadata": row[2] or {}, "ocr_text": row[3]}


def get_image_descriptions_for_file(file_id: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.image_hash,
                       '/public/images/' || r.image_hash || '.png' as url,
                       i.width, i.height,
                       COALESCE(d.description, '') as description,
                       COALESCE(d.metadata, '{}'::jsonb) as metadata,
                       COALESCE(d.ocr_text, '') as ocr_text,
                       r.page as pagina
                FROM pdf_image_refs r
                JOIN images i ON i.hash = r.image_hash
                LEFT JOIN image_descriptions d ON d.image_hash = r.image_hash
                WHERE r.file_id = %s
                ORDER BY r.page, r.image_hash
                """,
                (file_id,),
            )
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


# Maintenance / cache management
def delete_image_descriptions_for_file(file_id: str):
    """Delete image_descriptions rows for all images linked to a given file_id.
    Useful to force regeneration of captions for a specific file's images.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                delete from image_descriptions d
                using pdf_image_refs r
                where r.image_hash = d.image_hash
                  and r.file_id = %s
                """,
                (file_id,),
            )
            return cur.rowcount or 0

# Listing and loading

def list_files():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT pf.file_id, pf.pdf_hash, pf.original_filename, pf.stored_path,
                       (SELECT count(*) FROM pdf_image_refs r WHERE r.file_id = pf.file_id) AS images,
                       (SELECT count(*) FROM pdf_table_refs t WHERE t.file_id = pf.file_id) AS tables,
                       (SELECT COUNT(*) FROM image_descriptions d JOIN pdf_image_refs r ON r.image_hash=d.image_hash AND r.file_id=pf.file_id) AS images_described
                FROM pdf_files pf
                ORDER BY pf.created_at DESC
                """
            )
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]



def list_files_grouped_by_pdf():
    """Return one row per pdf_hash (latest file_id for that hash)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (pf.pdf_hash)
                       pf.file_id, pf.pdf_hash, pf.original_filename, pf.stored_path,
                       (SELECT count(*) FROM pdf_image_refs r WHERE r.file_id = pf.file_id) AS images,
                       (SELECT count(*) FROM pdf_table_refs t WHERE t.file_id = pf.file_id) AS tables,
                       (SELECT COUNT(*) FROM image_descriptions d JOIN pdf_image_refs r ON r.image_hash=d.image_hash AND r.file_id=pf.file_id) AS images_described
                FROM pdf_files pf
                ORDER BY pf.pdf_hash, pf.created_at DESC
                """
            )
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def load_extraction_from_db(file_id: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("select pdf_hash, original_filename, stored_path from pdf_files where file_id=%s", (file_id,))
            row = cur.fetchone()
            if not row:
                return None
            pdf_hash, original_filename, stored_path = row
            # Try existing extraction.json path
            import json as _json
            from pathlib import Path as _Path
            pdf_path = _Path(stored_path)
            sanitized = __import__('slugify').slugify(_Path(original_filename).stem)
            out_dir = pdf_path.parent / sanitized
            extraction_json = out_dir / 'extraction.json'
            if extraction_json.exists():
                try:
                    return _json.loads(extraction_json.read_text(encoding='utf-8'))
                except Exception:
                    pass
            # Synthesize JSON from DB minimal
            # Pages text not stored; we will return pages with images/tables from refs
            cur.execute(
                "select page, img_index, image_hash from pdf_image_refs where file_id=%s order by page, img_index",
                (file_id,),
            )
            img_rows = cur.fetchall()
            cur.execute(
                "select page, table_index, table_hash from pdf_table_refs where file_id=%s order by page, table_index",
                (file_id,),
            )
            tbl_rows = cur.fetchall()
            # Group by page
            pages = {}
            for (pg, idx, ih) in img_rows:
                pages.setdefault(pg, {"page": pg, "images": [], "tables": []})
                pages[pg]["images"].append({"hash": ih, "url": f"/public/images/{ih}.png"})
            for (pg, idx, th) in tbl_rows:
                pages.setdefault(pg, {"page": pg, "images": [], "tables": []})
                pages[pg]["tables"].append({"hash": th, "url": f"/public/tables/{th}.json"})
            result = {
                "pdf_hash": pdf_hash,
                "pages": sorted(pages.values(), key=lambda x: x["page"]),
                "tables": [
                    {"hash": th, "url": f"/public/tables/{th}.json"}
                    for (_, _, th) in tbl_rows
                ],
                "upload": {
                    "file_id": file_id,
                    "original_filename": original_filename,
                    "stored_path": stored_path,
                    "output_dir": str(out_dir),
                },
            }
            return result
