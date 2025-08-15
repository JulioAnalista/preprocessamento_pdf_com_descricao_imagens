import os
import json
from pathlib import Path
from typing import List, Dict

# Weaviate
import weaviate

# Arango
from arango import ArangoClient

# Azure OpenAI embeddings
from openai import AzureOpenAI

AZ_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZ_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZ_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2025-01-01-preview')
AZ_EMBED_MODEL = os.getenv('AZURE_OPENAI_EMBEDDING_MODEL', 'text-embedding-3-large')

WEAVIATE_URL = os.getenv('WEAVIATE_URL', 'http://localhost:8080')
WEAVIATE_API_KEY = os.getenv('WEAVIATE_API_KEY')

ARANGO_URL = os.getenv('ARANGO_URL', 'http://localhost:8529')
ARANGO_USER = os.getenv('ARANGO_USER', 'root')
ARANGO_PASSWORD = os.getenv('ARANGO_PASSWORD', '')
ARANGO_DB = os.getenv('ARANGO_DB', 'mpnormas')

_embed_client = AzureOpenAI(api_key=AZ_KEY, api_version=AZ_API_VERSION, azure_endpoint=AZ_ENDPOINT)

def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    resp = _embed_client.embeddings.create(model=AZ_EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def load_image_descriptions(conn) -> List[Dict]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.image_hash,
               '/public/images/' || r.image_hash || '.png' as url,
               i.width, i.height,
               COALESCE(d.description, '') as description,
               COALESCE(d.metadata, '{}'::jsonb) as metadata,
               COALESCE(d.ocr_text, '') as ocr_text,
               pf.pdf_hash,
               r.file_id,
               r.page as pagina
        FROM pdf_image_refs r
        JOIN images i ON i.hash = r.image_hash
        LEFT JOIN image_descriptions d ON d.image_hash = r.image_hash
        JOIN pdf_files pf ON pf.file_id = r.file_id
        ORDER BY pf.pdf_hash, r.page, r.image_hash
        """
    )
    cols = [c[0] for c in cur.description]
    rows = cur.fetchall()
    out = [dict(zip(cols, row)) for row in rows]
    return out


def index_weaviate(conn):
    # Connect Weaviate (legacy client)
    client = weaviate.Client(WEAVIATE_URL)

    class_name = 'ImageDescription'
    schema = client.schema.get()
    exists = any(c.get('class') == class_name for c in schema.get('classes', []))
    if not exists:
        client.schema.create_class(
            {
                'class': class_name,
                'vectorizer': 'none',
                'properties': [
                    {'name':'image_hash','dataType':['text']},
                    {'name':'url','dataType':['text']},
                    {'name':'description','dataType':['text']},
                    {'name':'metadata','dataType':['text']},
                    {'name':'pdf_hash','dataType':['text']},
                    {'name':'file_id','dataType':['text']},
                    {'name':'pagina','dataType':['int']},
                    {'name':'embedding','dataType':['number[]']},
                ]
            }
        )

    items = load_image_descriptions(conn)
    with client.batch as batch:
        batch.batch_size = 50
        for it in items:
            const_text = ((it['description'] or '') + '\n' + (it.get('ocr_text') or '')).strip()
            props = {
                'image_hash': it['image_hash'],
                'url': it['url'],
                'description': it['description'],
                'metadata': json.dumps(it['metadata']),
                'pdf_hash': it['pdf_hash'],
                'file_id': it['file_id'],
                'pagina': int(it['pagina']),
                'embedding': embed_texts([ const_text ])[0] if const_text else None,
            }
            client.batch.add_data_object(props, class_name)


def index_arango(conn):
    client = ArangoClient(hosts=ARANGO_URL)
    sys_db = client.db('_system', username=ARANGO_USER, password=ARANGO_PASSWORD)
    if not sys_db.has_database(ARANGO_DB):
        sys_db.create_database(ARANGO_DB)
    db = client.db(ARANGO_DB, username=ARANGO_USER, password=ARANGO_PASSWORD)
    col = db.collection('imagens_descritas') if db.has_collection('imagens_descritas') else db.create_collection('imagens_descritas')

    items = load_image_descriptions(conn)
    for it in items:
        key = it['image_hash']
        doc = {
            '_key': key,
            'image_hash': it['image_hash'],
            'url': it['url'],
            'width': it['width'],
            'height': it['height'],
            'description': it['description'],
            'metadata': it['metadata'],
            'ocr_text': it.get('ocr_text') or '',
            'pdf_hash': it['pdf_hash'],
            'file_id': it['file_id'],
            'pagina': int(it['pagina']),
        }
        if col.has(key):
            col.update(doc)
        else:
            col.insert(doc)


if __name__ == '__main__':
    from pdf_preproc import db as pdb
    pdb.ensure_schema()
    with pdb.get_conn() as conn:
        index_weaviate(conn)
        index_arango(conn)
    print('Indexação concluída (Weaviate + Arango).')

