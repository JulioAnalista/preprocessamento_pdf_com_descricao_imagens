import os
import json
import hashlib
from typing import List, Dict, Any

import psycopg2
from contextlib import contextmanager

from .db import get_conn, ensure_schema

AZ_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZ_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZ_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2025-01-01-preview')
AZ_EMBEDDING_MODEL = os.getenv('AZURE_OPENAI_EMBEDDING_MODEL', 'text-embedding-3-large')
AZ_CHAT_MODEL = os.getenv('AZURE_OPENAI_CHAT_MODEL', 'gpt-4.1-nano')

# Minimal Azure OpenAI embedding client using OpenAI SDK v1
from openai import AzureOpenAI
client = AzureOpenAI(
    api_key=AZ_KEY,
    api_version=AZ_API_VERSION,
    azure_endpoint=AZ_ENDPOINT,
)


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    resp = client.embeddings.create(model=AZ_EMBEDDING_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def build_graph_for_extraction(extraction: Dict[str, Any]):
    ensure_schema()
    pdf_hash = extraction.get('pdf_hash')
    if not pdf_hash:
        raise ValueError('pdf_hash ausente na extração')

    name = extraction.get('upload', {}).get('original_filename', pdf_hash)

    # Aggregate content: texts and tables
    texts: List[str] = []
    for p in extraction.get('pages', []):
        t = (p.get('text') or '').strip()
        if t:
            texts.append(t)
    # tables as JSON strings
    for p in extraction.get('pages', []):
        for tbl in p.get('tables', []):
            rows = tbl.get('rows') or []
            if rows:
                texts.append(json.dumps(rows, ensure_ascii=False))

    # Chunking naive (could be improved):
    chunks: List[str] = []
    for t in texts:
        if len(t) <= 4000:
            chunks.append(t)
        else:
            # split by paragraph size
            s = t
            while len(s) > 0:
                chunks.append(s[:4000])
                s = s[4000:]

    # Embed chunks
    embeddings = embed_texts(chunks)

    # Insert graph metadata
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "insert into graphs(graph_id, name, source_file_id) values(%s,%s,%s) on conflict do nothing",
                (pdf_hash, name, extraction.get('upload',{}).get('file_id')),
            )
            node_ids: List[int] = []
            for i, (ck, emb) in enumerate(zip(chunks, embeddings)):
                cur.execute(
                    "insert into graph_nodes(graph_id, label, type, properties, embedding) values(%s,%s,%s,%s,%s) returning id",
                    (pdf_hash, f"chunk_{i+1}", "chunk", json.dumps({"len": len(ck)}), json.dumps(emb)),
                )
                nid = cur.fetchone()[0]
                node_ids.append(nid)
            # simple linear edges chunk_i -> chunk_{i+1}
    # optional: incorporate image descriptions as nodes
    img_desc_nodes = 0
    for p in extraction.get('pages', []):
        for img in p.get('images', []):
            desc = img.get('description')
            if not desc:
                continue
            emb = embed_texts([desc])[0]
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "insert into graph_nodes(graph_id, label, type, properties, embedding) values(%s,%s,%s,%s,%s)",
                        (pdf_hash, f"img_{img.get('hash','')[:8]}", "image_desc", json.dumps({"hash": img.get('hash')}), json.dumps(emb)),
                    )
                    img_desc_nodes += 1

            for i in range(len(node_ids)-1):
                cur.execute(
                    "insert into graph_edges(graph_id, src, dst, relation) values(%s,%s,%s,%s)",
                    (pdf_hash, node_ids[i], node_ids[i+1], "NEXT"),
                )

    return {"graph_id": pdf_hash, "nodes": len(embeddings), "edges": max(0, len(embeddings)-1)}

