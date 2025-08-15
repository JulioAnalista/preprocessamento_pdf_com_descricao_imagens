import os
import json
from pathlib import Path
from datetime import datetime

from fastapi.testclient import TestClient

from pdf_preproc.app import app
from pdf_preproc.graph_kb import build_graph_for_extraction

PDFS = [
    "/mnt/e/PDOT/comparacao/Anteprojeto_LC_PDOT_Aprovada_Conplan.pdf",
    "/mnt/e/PDOT/comparacao/Minuta_submetida_a_audiencia_publica.pdf",
]

REPORT_PATH = Path(__file__).resolve().parent / "report_graph_kb.md"


def run_for_pdf(client: TestClient, pdf_path: str):
    p = Path(pdf_path)
    if not p.exists():
        return {"pdf": pdf_path, "status": "missing"}
    # Upload
    with open(p, 'rb') as f:
        r = client.post('/api/upload', files={'file': (p.name, f, 'application/pdf')})
    assert r.status_code == 200, r.text
    fid = r.json()['file_id']
    # Extract
    e = client.post(f"/api/extract/{fid}")
    assert e.status_code == 200, e.text
    ex = e.json()
    # Build graph KB
    g = build_graph_for_extraction(ex)
    return {"pdf": pdf_path, "file_id": fid, "pdf_hash": ex.get('pdf_hash'), "graph": g}


def main():
    client = TestClient(app)
    rows = []
    for path in PDFS:
        rows.append(run_for_pdf(client, path))

    now = datetime.utcnow().isoformat()
    out = []
    out.append(f"# Relatório Graph KB (Azure OpenAI) ({now}Z)\n")
    for r in rows:
        out.append(f"## PDF: {r['pdf']}")
        if r.get('status') == 'missing':
            out.append("- Status: arquivo não encontrado\n"); continue
        g = r['graph']
        out.append(f"- file_id: {r['file_id']}")
        out.append(f"- pdf_hash: {r['pdf_hash']}")
        out.append(f"- graph_id: {g['graph_id']}")
        out.append(f"- nodes: {g['nodes']} | edges: {g['edges']}\n")

    REPORT_PATH.write_text("\n".join(out), encoding='utf-8')
    print(f"Relatório salvo em: {REPORT_PATH}")

if __name__ == '__main__':
    main()

