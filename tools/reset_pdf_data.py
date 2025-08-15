import argparse
from pdf_preproc import db as pdb

SQL = """
BEGIN;
-- limpar grafos primeiro (dependem de pdfs opcionalmente)
DELETE FROM graph_edges;
DELETE FROM graph_nodes;
DELETE FROM graphs;
-- descrições de imagens independentes (ligadas a images.hash)
DELETE FROM image_descriptions;
-- refs e extrações dependem de pdf_files
DELETE FROM pdf_image_refs;
DELETE FROM pdf_table_refs;
DELETE FROM extractions;
-- arquivos de pdf e índices por hash
DELETE FROM pdf_files;
-- artefatos únicos
DELETE FROM images;
DELETE FROM tables;
DELETE FROM pdfs;
COMMIT;
"""

def main(confirm: bool):
    if not confirm:
        print("Proteção: use --yes para confirmar a limpeza total das tabelas relacionadas a PDFs.")
        return 1
    pdb.ensure_schema()
    with pdb.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(SQL)
    print("OK: dados de PDFs limpos com sucesso.")
    return 0

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Zera tabelas relacionadas a PDFs (irrecuperável)")
    ap.add_argument("--yes", action="store_true", help="Confirmar limpeza total")
    args = ap.parse_args()
    raise SystemExit(main(args.yes))

