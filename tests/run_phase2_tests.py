import os
import json
from pathlib import Path
from datetime import datetime

from fastapi.testclient import TestClient

from pdf_preproc.app import app, PUBLIC_DIR
from pdf_preproc import db as pdb

PDFS = [
    "/mnt/e/PDOT/comparacao/Anteprojeto_LC_PDOT_Aprovada_Conplan.pdf",
    "/mnt/e/PDOT/comparacao/Minuta_submetida_a_audiencia_publica.pdf",
]

REPORT_PATH = Path(__file__).resolve().parent / "report.md"


def human(n):
    try:
        return f"{n:,}".replace(",", ".")
    except Exception:
        return str(n)


def db_counts(conn):
    cur = conn.cursor()
    cur.execute("select count(*) from pdfs"); pdfs = cur.fetchone()[0]
    cur.execute("select count(*) from images"); imgs = cur.fetchone()[0]
    cur.execute("select count(*) from tables"); tbls = cur.fetchone()[0]
    return pdfs, imgs, tbls


def run_for_pdf(client: TestClient, pdf_path: str):
    p = Path(pdf_path)
    if not p.exists():
        return {"pdf": pdf_path, "status": "missing"}

    # Upload
    with open(p, 'rb') as f:
        resp = client.post('/api/upload', files={'file': (p.name, f, 'application/pdf')})
    assert resp.status_code == 200, resp.text
    up = resp.json()
    file_id = up['file_id']

    # Extract (first)
    r1 = client.post(f"/api/extract/{file_id}")
    assert r1.status_code == 200, r1.text
    j1 = r1.json()

    # Stats before second run
    with pdb.get_conn() as conn:
        pdfs_b, imgs_b, tbls_b = db_counts(conn)

    # Extract (second) to validate dedup
    r2 = client.post(f"/api/extract/{file_id}")
    assert r2.status_code == 200, r2.text
    j2 = r2.json()

    # Stats after
    with pdb.get_conn() as conn:
        pdfs_a, imgs_a, tbls_a = db_counts(conn)

    # Verify zip
    zip_url = j2.get('download',{}).get('zip_url')
    zip_ok = False
    if zip_url:
        # translate url to path
        if zip_url.startswith('/public/'):
            zpath = PUBLIC_DIR / zip_url.split('/public/',1)[1]
            zip_ok = zpath.exists() and zpath.stat().st_size > 0

    return {
        "pdf": pdf_path,
        "file_id": file_id,
        "pdf_hash": j2.get('pdf_hash'),
        "pages": j2.get('pages_count'),
        "images_reported": sum(len(p.get('images',[])) for p in j2.get('pages',[])),
        "tables_reported": len(j2.get('tables',[])),
        "db_pdfs_before": pdfs_b, "db_images_before": imgs_b, "db_tables_before": tbls_b,
        "db_pdfs_after": pdfs_a, "db_images_after": imgs_a, "db_tables_after": tbls_a,
        "zip_url": zip_url, "zip_ok": zip_ok,
    }


def main():
    pdb.ensure_schema()
    client = TestClient(app)

    rows = []
    for path in PDFS:
        rows.append(run_for_pdf(client, path))

    # Build report
    now = datetime.utcnow().isoformat()
    out = []
    out.append(f"# Relatório Fase 2 - Deduplicação e Persistência ({now}Z)\n")
    for r in rows:
        out.append(f"## PDF: {r['pdf']}")
        if r.get('status') == 'missing':
            out.append("- Status: arquivo não encontrado")
            out.append("")
            continue
        out.append(f"- file_id: {r['file_id']}")
        out.append(f"- pdf_hash: {r['pdf_hash']}")
        out.append(f"- páginas: {r['pages']}")
        out.append(f"- imagens (reportadas): {human(r['images_reported'])}")
        out.append(f"- tabelas (reportadas): {human(r['tables_reported'])}")
        out.append(f"- DB pdfs antes/depois: {r['db_pdfs_before']} → {r['db_pdfs_after']}")
        out.append(f"- DB images antes/depois: {r['db_images_before']} → {r['db_images_after']}")
        out.append(f"- DB tables antes/depois: {r['db_tables_before']} → {r['db_tables_after']}")
        out.append(f"- zip_url: {r['zip_url']}")
        out.append(f"- zip_ok: {r['zip_ok']}")
        out.append("")

    REPORT_PATH.write_text("\n".join(out), encoding='utf-8')
    print(f"Relatório salvo em: {REPORT_PATH}")

if __name__ == '__main__':
    main()

